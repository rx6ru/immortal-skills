# Token validation checklist

Contents: what to check on every request and in what order; a code sketch; what to test; failure responses; common mistakes.

Source: Mastering API Architecture ch. 7 (JWT validation, lifetimes, verification checklist). The book states four checks: signature and integrity, expiry, not-before, and other claims. Explicit audience and issuer verification is implied by the claim definitions (marked inferred in the notes). Ordering, algorithm pinning and the code are adaptation.

## Where validation runs

In-process at whichever component acts as the resource server: usually the API gateway, and also each service that makes its own authorisation decisions (see `edge-and-zero-trust.md`: do not trust a request merely because it came from inside). No database lookup is needed for a self-contained token, which is why it scales.

## Checks, in order

| # | Check | Reject when | Why |
|---|---|---|---|
| 0 | Transport | Request arrived over plain HTTP | Tokens are sensitive; TLS only |
| 1 | Format | Not three well-formed segments, or header names an algorithm you did not configure (Adaptation: pin accepted algorithms; never accept `none`) | Prevents downgrade tricks |
| 2 | Signature | Not verifiable with the public key of the expected issuer (fetch and cache the issuer's key set; handle key rotation) | Proves the issuer signed it and nothing changed |
| 3 | `exp` | Current time is after expiry | Limits theft and replay window |
| 4 | `nbf` | Current time is before not-before | Token not yet valid |
| 5 | `iss` (inferred explicit check) | Issuer is not the one you trust | A token from another issuer may be validly signed but meaningless to you |
| 6 | `aud` (inferred explicit check) | Audience does not name this service or API | Stops a token minted for service A being replayed against service B |
| 7 | Token type | It is an ID token, not an access token (Update: when the issuer follows RFC 9068, require the JOSE header `typ` to be `at+jwt`; otherwise rely on `aud` naming your API and on the issuer's documented access-token claims) | ID tokens inform the client about the user; they are not for resource access |
| 8 | Scope | Required scope for this route absent in `scope` claim | Coarse authorisation, gateway-enforceable |
| 9 | Authentication context, if the route needs it | Required authentication method (for example MFA) is not in the claims | High-security APIs use this claim |
| 10 | Fine-grained entitlement | Subject not allowed to touch this object or function | Done in the service, not by the token: `authorization-enforcement.md` |

Allow a small clock skew for 3 and 4 only if your environment needs it (Adaptation), and record the value.

## Sketch (Adaptation; TypeScript with the `jose` library)

```ts
import { jwtVerify, createRemoteJWKSet } from "jose";
const jwks = createRemoteJWKSet(new URL("https://idp.example/.well-known/jwks.json"));

export async function authenticate(bearer: string) {
  const { payload } = await jwtVerify(bearer, jwks, {
    issuer: "https://idp.example/",      // check 5
    audience: "attendee-api",             // check 6
    algorithms: ["RS256"],                // check 1: pinned
    requiredClaims: ["exp", "sub"],       // without this a token with no exp is accepted
    typ: "at+jwt",                        // check 7, only if your issuer sets it (RFC 9068)
    clockTolerance: 5,                    // seconds, deliberate and small
  }); // signature, exp and nbf are verified here (checks 2 to 4) when present
  const scopes = String(payload.scope ?? "").split(" ");
  return { sub: payload.sub!, scopes };
}
```

Tested behaviour (jose 5, locally generated keys): Wrong `aud`, wrong `iss`, expired, `alg` HS256 and `alg: none` were all rejected. A validly signed token with no `exp` was accepted until `requiredClaims` was added, so list the claims that must exist; a library check only runs on claims that are present.

Python equivalent: `jwt.decode(token, key, algorithms=["RS256"], audience="attendee-api", issuer="https://idp.example/", options={"require": ["exp", "iss", "aud", "sub"]})` with PyJWT. Run on PyJWT, the same call without `options["require"]` accepted a token with no `exp`. In both libraries pass `algorithms`, `audience` and `issuer` explicitly and name the required claims; libraries differ in which checks they run by default, so read the library's documentation (not stated in the book).

Update (current practice, not in the 2022 book): take the verification key only from the issuer's configured key-set URL, selected by `kid`. Do not follow `jku`, `jwk` or `x5u` headers that arrive inside the token. This is the key-confusion class of attacks in the JWT best-practice RFC 8725.

## Lifetimes and revocation

- Access tokens: as short as possible; typical 1 to 60 minutes. Long-lived (1 to 10 years) belongs to refresh credentials or special assertions and is riskier.
- Refresh tokens: rotate on use; a second use of the same refresh token revokes the active one.
- Update: bearer tokens work for whoever holds them. Where theft of a token is a realistic threat (browser or mobile clients, high-value APIs), current OAuth guidance (RFC 9700) prefers sender-constrained tokens: DPoP (RFC 9449) or mutual-TLS-bound tokens (RFC 8705). The resource server then also checks the proof that accompanies the token. The book does not cover this.
- Revocation window: self-contained tokens stay valid until `exp` even after consent is withdrawn; shorten the lifetime rather than add a lookup on every request (inferred from the notes' advice). If you must support immediate revocation, add a deny-list keyed on `jti` and accept the lookup cost (Adaptation).

## Content rules

- No secrets or PII in JWS claims (readable by anyone holding the token). Use JWE if content must be hidden.
- `sub` is a stable identifier, not an email or username.
- API keys: at least 256 bits from a secure random source, rotated, scoped per application, never used to assert end-user identity.

## Tests to write

Generate each of these negative cases in a test fixture and assert 401 (or 403 for scope):

1. No token; malformed token; token with altered payload (signature mismatch).
2. Expired token; token whose `nbf` is in the future; validly signed token with no `exp` claim.
3. Token signed by a different key or issuer; token with the wrong `iss`.
4. Token with `aud` of a different service.
5. ID token presented as an access token.
6. Token with `alg: none` or a different algorithm than configured.
7. Token lacking the required scope but otherwise valid.
8. Token over plain HTTP (expect refusal; a redirect means the token has already been sent in the clear, so treat a redirect as a finding for API hosts unless policy says otherwise).
9. Positive control: a correct token passes. Without it the negative tests may pass for the wrong reason.

## Response behaviour

- Invalid or missing credential: 401 with a `WWW-Authenticate: Bearer` header (Adaptation, RFC 6750; add `error="invalid_token"` when a token was presented). Valid identity but not allowed (scope missing, not entitled): 403 (RFC 6750 names this `insufficient_scope`). For object-level denials some teams return 404 to avoid confirming an object exists (Adaptation; choose one policy and apply it consistently).
- Error bodies carry no stack traces, key identifiers or library names.
- Log the failure with correlation id and reason code, but not the token itself.
