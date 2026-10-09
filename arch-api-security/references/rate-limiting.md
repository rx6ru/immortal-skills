# Rate limiting and load shedding

Contents: the two controls; why and where; choosing an algorithm (table and chooser); the five algorithms in detail; bucket counts and keys; architecture; response contract; distributed pitfalls; failure mode; client-side contract; hard versus soft limits; verification; sketches.

Sources: Mastering API Architecture ch. 6 (DoS, rate limiting vs load shedding) and ch. 3 (gateway protection); System Design Interview ch. 4 (rate limiter). Sketches are adaptation.

## Two controls, often confused

| | Rate limiting | Load shedding |
|---|---|---|
| Rejects based on | Properties of the individual request source: per user, client app, location or IP, client id, or all callers equally | Overall system state: database at capacity, no worker threads free |
| Protects against | One caller consuming more than its share; abuse; runaway clients; cost from paid third-party calls | Total overload regardless of who is calling |
| Answer to "who gets turned away?" | The offender | Whoever arrives while the system is saturated (choose a priority policy) |

You usually need both. Many servers and gateways have neither by default, so failure behaviour under load is undefined. Load test to find the limits first, then set the numbers.

## Why limit

Prevent resource starvation and denial of service, intentional or accidental; reduce cost (fewer servers, and essential when each call to a third party is billed); stop overload from bots and misbehaving users. Real limits mentioned: Twitter 300 tweets per 3 hours; Google Docs API 300 read requests per user per 60 seconds.

## Where to put it

- Not on the client: requests can be forged and you do not control the client.
- Server side, either inside the API server code or as middleware or in the API gateway in front of the APIs. The gateway also does TLS termination, authentication and IP allow-listing, so it is the natural home.
- Also limit internal service-to-service calls, to catch circular-dependency call loops and to surface error signals.
- Decision guidance from the chapter: check that your stack is efficient enough to do it; pick the algorithm you need (a third-party gateway may restrict your choice); if you already have microservices plus a gateway, add it there; if you lack engineering capacity, prefer a commercial gateway to building your own.
- Layer: this chapter works at layer 7 (HTTP). Lower layers can limit too, for example iptables by IP at layer 3.

## Choosing an algorithm

| Need | Choose | Why |
|---|---|---|
| Allow short bursts, simple, low memory (the default for most APIs; used by Amazon and Stripe) | Token bucket | Bursts allowed up to bucket size; two parameters |
| Bursty flash-sale style traffic that a strict scheme would punish | Token bucket | The source says to switch to it for bursty traffic |
| Stable, smooth outflow to a downstream that cannot take bursts (used by Shopify) | Leaking bucket | Fixed processing rate from a FIFO queue |
| Quota that resets on a boundary and is easy to explain ("2,400 per day") | Fixed window counter | Simple, tiny memory; accept the edge-spike flaw |
| Exactness over any rolling window and memory is not a concern | Sliding window log | Exact |
| Smooth, cheap, and a small approximation is acceptable | Sliding window counter | Weighted blend of two windows; Cloudflare measured about 0.003% of 400 million requests misjudged |

## The five algorithms

### Token bucket
- Mechanics: a bucket of fixed capacity; a refiller adds tokens at a fixed rate and discards overflow; each request takes one token; no token means the request is dropped.
- Parameters: bucket size, refill rate.
- Pros: simple; memory efficient; allows bursts.
- Cons: the two parameters are hard to tune.
- Use when: you want bursts tolerated but a long-run average enforced.
- Do not use when: the downstream needs a perfectly flat rate.

### Leaking bucket
- Mechanics: a FIFO queue of fixed size; a request is enqueued if there is room, otherwise dropped; requests are processed at a fixed outflow rate.
- Parameters: queue size, outflow rate.
- Pros: memory efficient; stable outflow.
- Cons: a burst fills the queue with old requests so recent ones get limited; two parameters hard to tune.
- Use when: smoothing traffic into a fragile backend. Do not use when: latency of recent requests matters more than smoothness.

### Fixed window counter
- Mechanics: a counter per fixed time window; when it hits the threshold, drop until the next window.
- Pros: memory efficient, easy to understand, a quota reset fits some uses.
- Cons: spikes at window edges can let through up to twice the quota. Example: with a limit of 5 per minute, 5 requests at 2:00:30 to 2:01:00 plus 5 at 2:01:00 to 2:01:30 gives 10 within a 60-second span.
- Use when: quota semantics matter more than short-term precision.

### Sliding window log
- Mechanics: keep timestamps (a Redis sorted set). On each request remove timestamps older than the window start, add the new one, accept if the log size is within the limit.
- Pros: exact in any rolling window.
- Cons: high memory, because timestamps of rejected requests are also stored.

### Sliding window counter (hybrid)
- Mechanics: rolling count = current window count + previous window count multiplied by the share of the rolling window that overlaps the previous window.
- Example: limit 7 per minute, previous window 5, current 3, 30% into the minute: 3 + 5 x 0.7 = 6.5, round down to 6, so the request is allowed.
- Pros: smooths spikes, memory efficient.
- Cons: an approximation that assumes requests were evenly spread in the previous window.

## Buckets and keys

- One bucket per endpoint per user when limits differ per action. Example: 1 post per second, 150 friend-adds per day, 5 likes per second gives 3 buckets per user.
- One bucket per IP when throttling by IP.
- One global bucket when there is a global cap (example 10,000 requests per second).
- Choose the key to match the threat. IP alone punishes shared networks and does nothing against distributed callers; client id or user id needs authentication to run first, so unauthenticated routes (login, token endpoint) still need an IP-level limit (Adaptation).

## Architecture

- Counters live in an in-memory store such as Redis, not a disk database (too slow). Redis gives `INCR` (add one) and `EXPIRE` (time-to-live, auto delete).
- Flow: client, then rate-limit middleware; the middleware reads the counter from the right bucket; over the limit: reject; otherwise forward to API servers and increment.
- Rules are config, not code. In the Lyft open-source format a rule has a domain, descriptors with key and value, and a rate limit with a unit and requests per unit (examples: marketing messages 5 per day, login 5 per minute). Workers pull rules from disk into a cache; the middleware reads rules from the cache.
- On rejection: return 429 and either drop the request or forward it to a queue (for example keep rate-limited orders for later processing).

## Response contract

| Item | Value |
|---|---|
| Status when over limit | 429 Too Many Requests |
| `X-Ratelimit-Limit` | Calls allowed per window |
| `X-Ratelimit-Remaining` | Calls left in the window |
| `X-Ratelimit-Retry-After` | Seconds to wait before retrying |

Users must be told they were throttled. Note (Adaptation): the standard `Retry-After` response header is widely understood by HTTP clients; sending it alongside the `X-` headers costs nothing.

## Distributed pitfalls

1. Race condition. Read counter, compare, write plus one is not atomic: two concurrent requests both read 3 and both write 4 when the right answer is 5. Locks fix it but slow the system. Use a Redis Lua script (atomic) or sorted sets.
2. Synchronisation across several limiter servers. Sticky sessions are neither scalable nor flexible. Preferred: a centralised shared store (Redis) used by all limiters.
3. Latency for distant users. Use multiple data centres or edge servers (Cloudflare had 194 edge locations in 2020) and synchronise counters with eventual consistency.
4. Tuning. Monitor throttle rates per rule. Too strict: valid requests are dropped, relax the rule. Ineffective under sudden spikes: change the algorithm, for example to token bucket.

## Failure mode of the limiter itself

The limiter must not take the system down when its store fails (a stated non-functional requirement: high fault tolerance). That leaves a real choice: fail open (let traffic through, risk overload) or fail closed (reject, risk outage). The book gives no universal answer: financial APIs fail closed, a public weather API may fail open, an emergency medical history service might prefer open. Decide per route class, write it down, and test it.

## Client-side contract (document this for API consumers)

Use client-side caching; understand the limits and avoid bursts; catch the 429 and recover; retry with exponential and sufficiently long back-off, honouring Retry-After.

## Hard versus soft limits

Hard: the threshold cannot be exceeded. Soft: may be exceeded briefly. Choose per rule; soft limits suit user-experience-driven quotas, hard limits suit cost or capacity protection.

## Verification

| Check | How | Pass condition |
|---|---|---|
| Boundary behaviour | Fixed window: send the full quota at the end of a window and again at the start of the next | Expected result matches the chosen algorithm (fixed window will pass up to 2x; if that is unacceptable, change algorithm) |
| Concurrency | Fire N parallel requests at a limit of N-1 | Exactly N-1 pass; no over-admission from races |
| Over-limit response | Exceed the limit | 429 with the three rate-limit headers present and correct |
| Store failure | Stop Redis (or the limiter's store) | Behaviour equals the documented fail-open or fail-closed choice; the API itself stays up |
| Per-key isolation | Exhaust one user's bucket | Another user is unaffected |
| Internal calls | Simulate a call loop between two services | The loop is cut by the internal limit and an alert fires |
| Load shedding | Saturate a dependency (slow the database) | The system sheds with a defined response, not a pile-up of timeouts |
| Observability | Check dashboards | Throttle rate per rule is visible |

## Sketches (Adaptation, not from the book)

Atomic fixed-window counter in Redis through a Lua script, so increment, expiry set and check cannot interleave (the script also guarantees the key always gets a TTL; a client that crashed between a bare `INCR` and `EXPIRE` would leave a counter that never resets). Rejected requests still increment, which is acceptable for a fixed window. Run against a mock of `redis.call` with limit 4: results 1,1,1,1,0,0 and TTL 60; not run against a live Redis. A sliding-window log or counter needs a different script (sorted set or two counters):

```lua
-- KEYS[1] = counter key, ARGV[1] = limit, ARGV[2] = window seconds
local n = redis.call('INCR', KEYS[1])
if n == 1 then redis.call('EXPIRE', KEYS[1], ARGV[2]) end
if n > tonumber(ARGV[1]) then return 0 end
return 1
```

Token bucket state in application memory (single process only; shared deployments need the central store). Run as written below: capacity 3, rate 1 per second gives True, True, True, False, False for five simultaneous requests, one more allowed after one second, and the token count is capped at capacity after a long idle gap.

```python
from dataclasses import dataclass

@dataclass
class Bucket:
    tokens: float
    last: float

def allow(bucket, now, rate, capacity):
    bucket.tokens = min(capacity, bucket.tokens + (now - bucket.last) * rate)
    bucket.last = now
    if bucket.tokens >= 1:
        bucket.tokens -= 1
        return True
    return False

b = Bucket(tokens=3, last=0.0)   # start full; use time.monotonic() for `now` in real code
```

Two cautions: use a monotonic clock so a wall-clock step cannot refill or drain the bucket, and in a multi-threaded process guard the function with a lock (the same read-modify-write race as in the Redis case).
