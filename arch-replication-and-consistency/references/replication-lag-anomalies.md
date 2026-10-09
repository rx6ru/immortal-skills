# Replication-lag anomalies and their remedies

Sources: DDIA 2e ch. 6 "Problems with replication lag"; ch. 10 (linearizability, cross-channel
timing). Items marked (inferred) are extrapolations in the study notes.

## Contents
1. The premise
2. Anomaly table
3. Remedies in detail
4. How to decide what the product needs
5. Testing for each anomaly
6. Related: linearizability races between channels

## 1. The premise

With asynchronous followers serving reads, a follower that fell behind returns different results than
the leader. If the lag is temporary this is "eventual consistency". "Eventually" has no bound: lag may
be sub-second or minutes under load or recovery. This is true of async relational followers too, not
only NoSQL.

Design question to ask every time: what happens to the user experience if the lag grows to minutes
or hours? If the answer is bad, a stronger guarantee is needed. Treating an async replica as if it
were synchronous causes trouble.

## 2. Anomaly table

| Anomaly | Example | Guarantee that prevents it | Remedies |
|---|---|---|---|
| Reading your own writes | User posts a comment, reloads, hits a stale follower, comment seems lost | Read-after-write (read-your-writes): a user always sees their own submitted updates; no promise about other users | See 3.1 |
| Cross-device read-after-write | Enter on desktop, view on phone | Same guarantee across a user's devices | See 3.2 |
| Monotonic reads | Refresh shows a comment, refresh again hits a staler replica and it disappears | Successive reads by one user never go back in time (weaker than strong consistency, stronger than eventual) | See 3.3 |
| Consistent prefix reads | Observer sees an answer before the question, because causally ordered writes landed on different shards with different lag | Writes that happened in an order are seen in that order | See 3.4 |

## 3. Remedies in detail

### 3.1 Read-your-writes
Pick the option that fits how much data a user can modify.
1. Read from the leader (or a sync follower) anything the user may have modified; read other things
   from followers. Example: own profile from the leader, others' profiles from followers. Needs a way
   to know what is "theirs" without querying first.
2. If most data is user-editable, option 1 defeats read scaling. Instead read from the leader for N
   minutes after the user's last update (e.g. N = 1), and/or refuse to serve from followers more than
   N minutes behind.
3. The client remembers the timestamp of its latest write. Prefer a logical timestamp such as a log
   sequence number; a wall-clock timestamp then needs clock synchronisation. Serve the read only from
   a replica that has reached it; otherwise wait or use another replica.
4. Multi-region: route requests that need the leader to the leader's region.

### 3.2 Cross-device
The "time of last write" metadata must be centralised, not per device. Devices on different networks
may reach different regions; if reads must come from the leader, route all of a user's devices to the
same region.

### 3.3 Monotonic reads
Pin each user to one replica, e.g. choose the replica by hashing the user ID. If that replica fails,
reroute; the guarantee may be briefly lost.

### 3.4 Consistent prefix
- Put causally related writes on the same shard (not always possible).
- Track causal dependencies (happens-before, version vectors). A single global order avoids the issue.
- Mostly a problem in sharded databases with independent shards.

Application-level workarounds are complex and error-prone. Prefer a store that offers the guarantee.

## 4. Deciding what the product needs

| Question about the feature | If yes |
|---|---|
| Does a user act on data they just wrote and expect to see it (post, save settings, checkout)? | Read-your-writes, at least |
| Can the user refresh and compare (feeds, comment threads, dashboards)? | Monotonic reads |
| Do items reference each other causally (replies to posts, messages in a thread) and live on different shards? | Consistent prefix (co-locate or track dependencies) |
| Do two people coordinate out of band (one tells the other to look)? | Needs more than per-user guarantees; see section 6 |
| Is the data safe if stale for minutes (view counts, recommendations)? | Plain async followers are fine |

## 5. Testing for each anomaly (inferred)
Inject artificial replica lag in tests (delay follower apply by 5 to 60 seconds) and assert:
1. A user sees their own write immediately after submit (also from a second device).
2. Repeated reads by one user never move backward.
3. Causal pairs appear in order (reply never visible without its post).
Also monitor lag (leader position minus follower position) and alert on it in production.

## 6. Related: races between channels
A second channel can outrun replication: a web server stores a video, enqueues a transcode job, and
the transcoder reads a replica that does not yet have the file; or a push notification arrives before
the replica has the data. Fixes: pass a version or timestamp in the message and read from a replica
that has reached it (or from the leader); or use a linearizable store, which is simplest but costs
latency and availability (`linearizability-and-consensus.md`). The warning sign is a bug that appears
only when two systems race: queue plus store, notification plus fetch, upload plus permission change.
