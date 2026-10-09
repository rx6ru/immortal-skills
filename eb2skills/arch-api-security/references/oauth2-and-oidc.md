# Authentication, API keys, OAuth2, tokens and OIDC

Contents: authN versus authZ; choosing a mechanism; API keys; OAuth2 roles; grant chooser; flow mechanics (authorization code, PKCE, client credentials); refresh tokens; JWT anatomy; scopes; OIDC; SAML; do-nots; ADR guideline tables; verification.

Source: Mastering API Architecture ch. 7 (2022). Where the note is marked "(inferred)" or adaptation, the label is kept. Passages labelled "Update" correct or extend the book with later guidance (mainly the OAuth 2.0 Security Best Current Practice, RFC 9700, January 2025); where an Update and the book differ, follow the Update. Validation rules are in `token-validation-checklist.md`; enforcement of what a caller may do is in `authorization-enforcement.md`.

## Definitions

- Authentication (authN): verifying identity. Humans: username and password, increasingly with multi-factor authentication (higher assurance). Machines: keys or certificates.
- Authorization (authZ): what the authenticated caller may do; checking entitlements.
- Order matters: identify the caller first, then check entitlements. An API holding PII (name, email) needs both.
- Identify the caller types before choosing anything. The case study has three: an end user on a mobile app, an end user acting through a third-party system (conference speakers using the CFP system), and the third-party system acting on its own (system to system).

## Choosing a mechanism

| Situation | Use | Notes |
|---|---|---|
| APIs only inside one control plane, no external parties, no integrator demand | Simplest thing that meets requirements; mTLS inside a mesh (`edge-and-zero-trust.md`) | OAuth2 is optional here; weigh the cost |
| Third parties or external clients, or you may need several auth models while migrating | OAuth2 (maximum compatibility, standard, client libraries, covers end-user and system-to-system) | Table 7-1 below |
| End user using a third-party app, no password sharing | OAuth2 authorization code (with PKCE for public clients) | The user's consent is the authorisation |
| One system calling another on its own behalf | Client credentials, or an API key if OAuth2 is not available | Client credentials is often the easiest first step into OAuth2 |
| Need to know who the user is in the client | OIDC on top of OAuth2 | Not a replacement for access tokens |
| Plain HTTP Basic for third-party access | Do not | The third party would need the user's password |

## API keys

- For system-to-system calls; there is no standard.
- Generate with a cryptographically secure random number generator; unguessable length, typically 32 characters (256 bits). Short or deterministic keys are a vulnerability. Adaptation: the 256 bits hold only if you draw 32 random bytes (then encode them); 32 characters from a 62-symbol alphabet carry about 190 bits.
- Send in a header: custom `X-API-KEY` or the Authorization header. Never in a URL (inferred: URLs end up in logs; Adaptation).
- A key identifies an application or project and behaves like a password: store it hashed or in a secret store, rotate it, scope it per application, and revoke it per application.
- Do not mix keys and users. A key authenticates the third-party system but does not entitle it to assert who the end user is; allowing that makes your whole trust depend on the third party. Passing the user's password via Basic alongside the key makes the user hand credentials to the third party. The ideal is that the third party acts for the user only with explicit approval and no credential sharing, which is OAuth2.

## Token basics

- Token-based auth: exchange credentials for a token, send it as `Authorization: Bearer ...` over HTTPS only (tokens are sensitive).
- Looking an opaque token up in a database on each request is a performance concern; self-contained, integrity-protected tokens (JWT) can be validated in-process.
- Tokens have a limited lifetime (example: 1 hour) so that long-lived passwords are not sent per request.

## OAuth2 roles

| Role | Meaning |
|---|---|
| Resource owner | The person (end user) |
| Authorization server | Authenticates the owner, obtains authorisation, issues tokens (examples: Google, Auth0). Has an authorization endpoint (owner authorises) and a token endpoint (client gets tokens) |
| Client | The application acting for the owner |
| Resource server | Hosts the protected resources and accepts access tokens. A whole system can be the resource server; a popular pattern is the API gateway as resource server with many services behind |

Abstract flow: client requests authorisation; owner grants or denies; client presents the grant to the authorization server; server issues an access token; client calls the resource server with it; the resource server returns the resource if the token is valid. The steps are isolated, so the resource server does not care how the client obtained the token, which is why different grants exist for different client environments.

## Grant chooser

| Grant | Client type | Use when | Do not use when / notes |
|---|---|---|---|
| Authorization code | Confidential client (server-side web app that can keep a secret) acting for an end user | Server-backed website, user consent | Public clients cannot keep a secret; use PKCE |
| Authorization code with PKCE | Public clients (SPA, mobile); also optional extra protection for confidential clients | Any end-user scenario where the client cannot protect a secret. PKCE must be used for public clients. Update: use it for confidential clients too (see "Updates since the book") | Same journey as plain code grant |
| Client credentials | Confidential client, machine to machine | No resource owner; pre-arranged access (example: the CFP system's quarterly report on its own behalf) | No refresh tokens (request a new access token). `sub` is the client, not a user. A client can be registered for several grants and `sub` differs per grant. RFC 8705 allows mTLS in place of secret strings for client authentication |
| Device authorization | Devices with limited input or no browser (IoT, smart fridge, Raspberry Pi) | Only if you must support such devices | Not explored in depth in the source |
| Implicit | SPAs, historical | Legacy only | Replaced by code plus PKCE; support only if old SPA clients cannot move. Update: RFC 9700 advises against it (tokens travel in the URL fragment and can leak or be injected); disable it |
| Resource owner password credentials | Historical step up from HTTP Basic | Never recommended | Client sees the user's password; forbid it. Update: RFC 9700 says it must not be used |

Case study mapping: the external CFP system is a confidential client, so authorization code for speakers' actions and client credentials for its own reporting; the mobile app is a public client, so authorization code with PKCE.

Decision order for an agent: (1) is there a human resource owner? No: client credentials. (2) Yes: can the client keep a secret? Yes: authorization code, and add PKCE (the book says "if you can"; Update: current guidance is to always). No: authorization code with PKCE. (3) No browser at all: device authorization. (4) Implicit and password grants: only to document why they are disabled.

## Authorization code mechanics

A. The client redirects the user agent to the authorization server with its client id and `response_type=code`.
B. The server authenticates the resource owner and obtains consent.
C. The server returns an authorization code through the user agent.
D. The client calls the token endpoint with the code and authenticates itself with its secret (the server must not accept codes from anyone).
E. The server issues the access token.

## PKCE mechanics

The client generates a random `code_verifier`, sends its hash as `code_challenge` (plus the transformation method) in the authorization request, and later presents the `code_verifier` with the code at the token endpoint. The server hashes it and compares. No client secret is sent. It defeats a stolen authorization code, because only the original client holds the verifier.

Update: use the `S256` method; `plain` exists only for clients that cannot hash. The verifier is a high-entropy random string of 43 to 128 characters (RFC 7636), a new one per authorization request. The authorization server must refuse the token request when the authorization request carried a challenge and the verifier is missing or wrong, and should refuse a verifier when no challenge was sent (otherwise an attacker strips PKCE from the request).

Adaptation (verifier and challenge in TypeScript on Node; use the platform's crypto library, never `Math.random`):

```ts
import { randomBytes, createHash } from "node:crypto";
const verifier = randomBytes(32).toString("base64url");
const challenge = createHash("sha256").update(verifier).digest("base64url");
// send challenge with code_challenge_method=S256; keep verifier for the token request
```

Checked by running it: the verifier is 43 characters and the challenge 43 characters, and the same SHA-256 and base64url steps reproduce the RFC 7636 appendix B test vector (verifier `dBjftJeZ4CVP-mB92K27uhbUJU1p1r_wW1gFWFOEjXk` gives challenge `E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstw-cM`). Use that vector as a unit test for your own implementation.

Update: also send a `state` value (or rely on PKCE) and check it on return, so a forged redirect cannot complete a login. The authorization server must compare registered redirect URIs by exact string match, with no wildcards or prefix matching; a loose redirect check lets an attacker steal the code.

## Client credentials mechanics

The client authenticates to the authorization server with `grant_type=client_credentials` and gets an access token. The client is registered, and the resource server holds a list of allowed clients with pre-arranged permissions (example: the CFP system may read attendees and query which users submitted talks).

## Refresh tokens

- A long-lived credential that lets the client obtain new short-lived access tokens without bothering the user.
- Treat as an extra secret. Latest best practice in the source: if a refresh token is used twice, immediately revoke the active refresh token (rotation with reuse detection).
- Revoking the refresh token cuts a client off when the owner withdraws consent. A window remains until the current access token expires, so keep access tokens short.
- Update: for public clients RFC 9700 requires that refresh tokens are either sender-constrained (DPoP, mutual TLS) or rotated with reuse detection, which is the practice above. Never accept refresh tokens or access tokens in a URL query string.

## JWT

- Structured claims, standardised, the de facto OAuth2 access token format, suited to header size limits.
- Reserved claims worth including as a minimum set:

| Claim | Meaning | Rule |
|---|---|---|
| `iss` | Issuer (identity provider) | Check it is the issuer you expect |
| `sub` | Subject: unique principal id (the user, or the application for server-to-server) | Use a stable id, not an email or username, since those change; decide system-unique or globally unique (UUID) |
| `aud` | Audience: who the token is for | Check it names this service |
| `exp` | Expiry | Reject after |
| `nbf` | Not before | Reject before |
| `iat` | Issued at | Informational / age checks |
| `jti` | Unique token id | Useful for revocation lists and replay detection (Adaptation) |

- Extra claims are allowed: name, email, which app requested, the authentication method used (high-security APIs use it to check MFA happened).
- JWS (signed): integrity, content readable by anyone holding the token. JWE (signed and encrypted): content hidden. "JWT" usually means JWT with JWS. The issuer signs with its private key; receivers verify with the public key. Never put confidential data in JWS claims; use JWE if content must be hidden.
- Lifetimes: keep as short as possible. Short-lived typically 1 to 60 minutes; long-lived 1 to 10 years (refresh or long assertions). NIST: long-lived assertions are riskier (theft and replay).

## Scopes

- Limit what a client may do on behalf of a user. Shown on a consent screen, so they must make sense to the end user. No standard naming; typically coarse grained. Optional in OAuth2 but recommended. In a JWT they appear as a `scope` claim (space-separated string or array).
- Case-study design: one scope per API (`Attendee`, `Conference`) so the CFP can be authorised for attendees only; refine to a read and write split (GET attendees needs `AttendeeRead`; POST and PUT need `AttendeeAccount`).
- The gateway can enforce scopes per route. Scope is not the user's entitlement; see `authorization-enforcement.md` for the intersection rule.

## OpenID Connect (OIDC)

- OAuth2 does not tell the client who the user is. OIDC adds an identity layer: the authorization server also acts as an OpenID provider; the client requests the scope `openid` alongside API scopes and receives an ID token (a JWT with claims about the user).
- With only `openid`, the sole identifying claim is `sub` (unique, never changes, usually a UUID). More scopes add claims: `profile` (name, family_name, given_name, nickname, preferred_username, picture, website, gender, birthdate, zoneinfo, locale, updated_at), `email` (email, email_verified), `address`, `phone` (phone_number, phone_number_verified). These scopes shape ID tokens, not access tokens.
- OIDC flows: authorization code, implicit, hybrid. Recommended: authorization code.
- OAuth2 and OIDC are distinct: OIDC tells the client who the user is, it does not grant API access.
- Use an identity provider that supports OIDC. Do not build your own identity layer.
- Never use an ID token as an access token.

## SAML 2.0

An enterprise single sign-on assertion standard, not designed for API use directly. The OAuth2 extension "SAML 2.0 Profile for OAuth 2.0 Client Authentication and Authorization Grants" lets a client trade a SAML assertion for an access token if the authorization server supports it; relevant when migrating an SSO estate to OAuth2.

## ADR guideline tables

### Table 7-1: Do I need OAuth2?
- Decision: OAuth2 or another preferred standard for the environment?
- Discuss: current and future security requirements (inside a control plane only, or external and third parties?); what model you are expected to support (have external integrators asked for one?); whether you must support multiple authN and authZ models (important when migrating).
- Recommendation: OAuth2 offers maximum compatibility, is an industry standard with documentation and client libraries, and covers end-user and system-to-system cases.

### Table 7-2: Which grants to support?
- Discuss: which clients call your APIs; whether IoT or device grant is needed; whether old SPA clients force Implicit; whether to forbid password credentials outright; if an existing security model works, whether to move to OAuth2, which grant represents each interaction, whether clients can migrate (easier with few or controlled clients), whether all newly onboarded clients should use OAuth2.
- Recommendation: use OAuth2, support only the grants you need, add later. If many paying customers depend on an existing model you may not be able to force migration, but third parties may ask for OAuth2 (no custom integration). Starting with client credentials is often the easiest way to introduce OAuth2.

## Do-nots

- Do not accept HTTP Basic for third-party access.
- Do not enable the resource owner password grant; do not enable implicit (book: unless legacy clients force it; Update: RFC 9700 advises against it outright, so record any exception and a retirement date).
- Do not use an API key to assert end-user identity.
- Do not accept an ID token at a resource server.
- Do not put secrets or PII in JWS claims; do not use email or username as `sub`.
- Do not send tokens over plain HTTP.
- Do not build your own identity provider or token format.
- Do not hand long-lived access tokens to clients; keep access tokens short and use refresh tokens with rotation.

## Verification

- Public clients: the code exchange without a valid verifier is rejected. Update: the same holds for confidential clients, and a code-exchange request carrying a verifier for an authorization request that had no challenge is rejected.
- A redirect URI that differs from the registered one by a path suffix, port or query string is refused.
- Implicit and password grants return an error from the token endpoint unless a recorded exception exists.
- A second use of a refresh token revokes the active one; revoking a refresh token stops new access tokens.
- An access token is rejected after its `exp`; an ID token is rejected at the resource server.
- Client credentials tokens carry the client as `sub` and only the scopes that were pre-arranged.
- Full list of per-request checks: `token-validation-checklist.md`.

## Updates since the book (2022)

These are not in the notes; they come from later standards and are marked so the agent can tell them from the book's claims. Check the RFC text before quoting a requirement level to a user.

| Topic | Book (2022) | Current guidance |
|---|---|---|
| PKCE | Required for public clients; optional for confidential | Use for every client that uses the authorization code grant, confidential ones included (RFC 9700; OAuth 2.1 draft). It also stops code injection when a client secret leaks |
| Implicit grant | Legacy only, replaced by code plus PKCE | Do not use (RFC 9700) |
| Password grant | Forbid | Must not be used (RFC 9700); OAuth 2.1 removes it |
| Redirect URIs | Not covered | Exact string matching on a pre-registered list; no wildcards |
| Browser apps (SPA) | Code with PKCE | Still code with PKCE, but keeping tokens in the browser is the weak point. A backend-for-frontend (the server holds tokens and the browser holds a session cookie) is the pattern the IETF browser-based-apps guidance prefers |
| Client authentication | Shared secret; mTLS mentioned for client credentials | Prefer asymmetric client authentication (`private_key_jwt`) or mTLS (RFC 8705) over shared secrets where the authorization server supports it |
| Token theft | Short lifetimes, rotation | Add sender-constrained tokens (DPoP, RFC 9449) for high-value APIs |
| Device grant | Named, not explored | Standardised as RFC 8628; use it for input-limited devices |
| ID token checks (OIDC) | Do not use as access token | The client also validates the ID token's `iss`, `aud` (its own client id), `exp` and the `nonce` it sent |

## Caveats

The book defers to the OAuth2 best-current-practice and the notes remark that later OAuth 2.1 guidance consolidates it (PKCE for all code flows, removal of implicit and password grants). The 2022 table above is therefore mostly right on the grants but behind on PKCE for confidential clients and on redirect-URI and token-theft guidance; the table in "Updates since the book" supersedes it. OAuth 2.1 was an Internet-Draft when this skill was reviewed; RFC 9700 is the published reference. Token exchange for propagating identity to downstream services is not covered in the source notes.
