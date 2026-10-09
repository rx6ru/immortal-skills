# Authorization enforcement

Contents: the rule; where each check lives; the scope and entitlement intersection; object-level (BOLA) and function-level (BFLA) checks; code patterns; how to find gaps in a repository; test matrix.

Source: Mastering API Architecture ch. 7 (scopes, enforcement, BOLA and BFLA) and ch. 6 (elevation of privilege). Code patterns, grep targets and the test matrix are adaptation built on the book's verification list.

## The rule

Authorization must be enforced at every endpoint, before the request is fulfilled. The exact model (role-based access control or another entitlement model) is a detail; the existence of the check on every route is not. A valid token proves who is calling and what the user consented to; it does not prove the caller may touch this object.

## Two threats

| Threat | Question | Typical failure |
|---|---|---|
| Broken Object Level Authorization (BOLA) | Can user A read or change object B by altering an identifier in the request? | Handler loads `/attendees/{id}` by id alone and never compares the owner with the caller |
| Broken Function Level Authorization (BFLA) | Can an ordinary user call an administrative function? | Admin routes exist on the same service and are hidden only by being unlinked or by client-side UI |

Both are elevation of privilege in STRIDE.

## Scope is not entitlement

Effective permission is the intersection of two sets: what the user is entitled to do, and what the user consented to let this client do. A client may request a "manage attendees" scope and the user may approve it; if the user lacks admin rights the call must still fail. The reverse also holds: an entitled user whose token lacks the scope cannot do it through that client.

| Layer | Check | Granularity | Where |
|---|---|---|---|
| Token validity | Signature, expiry, audience, issuer | Per request | Gateway (and services) |
| Scopes | Token carries the scope for this route and verb | Coarse, per API or per read and write | Gateway can enforce per route |
| Entitlement | Role, ownership, tenant, state of the object | Fine, per object and function | Service, where the data and rules are |

Do not collapse the third row into the second. Scopes are designed for consent screens and are coarse; if you encode per-object rights as scopes you get thousands of scopes and still miss ownership.

Case-study scope design: one scope per API (`Attendee`, `Conference`); then refine to read and write (`AttendeeRead` for GET, `AttendeeAccount` for POST and PUT).

## Procedure: adding or reviewing an endpoint

1. Identify the caller kind from the token: end user (client acting for a user, `sub` is the user) or client itself (client credentials, `sub` is the client). The rules differ.
2. Require the scope for the route and verb. Enforce at the gateway where possible, and do not rely on it alone (a service reachable around the gateway must still check).
3. Resolve the object server-side from the identifier. Compare ownership or tenancy with the authenticated `sub` (or an organisation claim). Take the identity from the validated token, never from a request field, header or body the client controls.
4. Check the function: is the caller's role allowed to perform this operation on this object in this state (for example approve, delete, export)?
5. Return 403 (or the policy's 404) on denial, with no data. Log the denial with the correlation id.
6. Filter the response with a DTO so a permitted caller sees only permitted fields (excessive data exposure is the sibling failure).

## Patterns (Adaptation)

Prefer scoping the query to the caller so an unauthorised row can never be returned, rather than load-then-check where a forgotten check leaks data:

```ts
// scoped query: ownership is part of the lookup
const row = await db.oneOrNone(
  "SELECT id, name FROM attendee WHERE id = $1 AND owner_id = $2",
  [req.params.id, auth.sub]);
if (!row) return res.sendStatus(404);
```
```python
# function-level: central decorator, deny by default
@require_scope("AttendeeAccount")
@require_role("organiser")
def delete_attendee(attendee_id): ...
```

Deny by default: a route with no declared policy should fail closed in tests, not serve everyone. Centralise the policy (middleware, decorator, policy engine) so a new route cannot silently skip it.

## Finding gaps in a repository

- List every route from the router, OpenAPI file and gateway config. For each, record: authenticated? scope required? object ownership check? role check? A column of blanks is the finding list.
- Search for handlers that take an id from the path, query or body and call a repository `findById`, `get`, `delete` or `update` without an owner or tenant argument.
- Search for role checks done only in client code or in a UI layer.
- Search for admin or internal routes (`/admin`, `/internal`, `/debug`, `/beta`) and confirm they are protected and inventoried (improper assets management).
- Check that identity is not read from a client-supplied header such as an asserted role or impersonation header; the gateway should strip such headers (`stride-and-owasp-api.md`, misconfiguration).

## Test matrix

For each protected route run these, as automated tests:

| Test | Setup | Expect |
|---|---|---|
| Object-level, cross user | User A's token requests user B's object id (read, update, delete) | 403 or 404; nothing changed |
| Object-level, enumeration | Sequential or guessed ids with A's token | Same response for "not yours" and "does not exist" if policy hides existence |
| Function-level | Ordinary user token calls admin route | 403 |
| Scope present, not entitled | Token with manage scope for a user without admin rights | 403 |
| Entitled, scope missing | Admin user's token without the scope | 403 |
| Client credentials | Client token without pre-arranged permission for the route | 403 |
| Positive control | Correct user, scope and ownership | 200 with only permitted fields |
| Header spoofing | Request with `X-Impersonate: Admin` or similar from outside | Ignored |

Evidence for the user: the route table with the four columns filled, and the test names and results for the matrix above.
