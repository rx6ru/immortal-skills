# Distributed locks, leases and fencing tokens

Sources: DDIA 2e ch. 9 "Distributed Locks and Leases", ch. 10 (coordination services, epochs). Items
marked (inferred) are extrapolations in the study notes.

## Contents
1. What leases are for
2. Why a lease alone is unsafe: two failure scenarios
3. Fencing tokens
4. Making the resource check the token
5. Fencing with replicas
6. Vendor equivalents
7. Procedure for adding fencing to code
8. Verification

## 1. What leases are for
A lease is a lock with a timeout. It implements "only one of X": a shard leader (avoids split brain), a
single updater of a resource, a single processor of an input file. In the first two a duplicate holder
corrupts data; in the last it only wastes work. That difference decides how much machinery you need.

## 2. Two failure scenarios
1. Pause (HBase had this bug): client 1 holds the lease, pauses (garbage collection) past expiry,
   client 2 acquires the lease and writes, client 1 wakes believing it still holds the lease and
   writes. The file is corrupted.
2. Delayed packet: no pause; client 1 sends a write and crashes or stalls; the packet sits in the
   network and arrives after the lease has been reassigned.

A zombie is a former leaseholder unaware it lost the lease. You cannot rule zombies out, so fence them.
STONITH (kill the node, cut its power or network) is not effective: it does not cover delayed packets,
nodes may kill each other, and it may be too late.

## 3. Fencing tokens
The lock service returns a monotonically increasing number with every grant (client 1 gets 33, its
lease expires, client 2 gets 34). Clients attach the token to every write; the storage service remembers
the highest token it has seen and rejects lower ones (33 is rejected after 34). A new leaseholder should
write immediately so that zombies are fenced. Fencing differs from optimistic concurrency control:
fencing is permanent for a given token, while an OCC failure is retried.

Takeaway: never assume exactly one node believes it holds the lease; make the resource reject stale
holders.

Sketch of the resource-side check (adaptation, Python-style pseudocode):

```python
def write(resource, token, payload):
    with resource.lock:                      # or one atomic conditional update in the store
        if token < resource.max_token:
            raise StaleToken(token, resource.max_token)
        resource.max_token = token           # persist together with the write
        resource.apply(payload)
```

The comparison and the write must be atomic, and `max_token` must be stored durably with the data.

## 4. Making the resource check the token
Either the storage service checks tokens, or it supports conditional writes / compare-and-set (S3
conditional writes, Azure Blob conditional headers, GCS request preconditions). If a single storage
service supports conditional writes, a separate lock service is somewhat redundant; tokens shine when
fencing across multiple services or replicas.

## 5. Fencing with replicas
In a leaderless last-write-wins store, put the token in the most significant digits of the write
timestamp, so writes from token 34 always beat 33. A zombie's write may land on one replica (replica 3
missed client 2's write), but quorum reads choose the higher timestamp and read repair or anti-entropy
fix it.

## 6. Vendor equivalents
The same idea appears under many names: Chubby "sequencer", Kafka "epoch number", Paxos ballot number,
Raft term, ZooKeeper `zxid` or `cversion`, etcd revision plus lease ID; Hazelcast FencedLock generates
tokens explicitly. A consensus log entry's sequence number is a valid token.

## 7. Procedure for adding fencing to code
1. List every place code acts on "I am the leader" or "I hold the lock" (cron leaders, singleton
   workers, shard owners, migration runners).
2. For each, find what it writes to. If the target is idempotent and duplicate work is harmless, a
   lease with a modest TTL is enough; stop here.
3. Otherwise get the token from the lock service at acquisition (ZooKeeper `zxid`/`cversion`, etcd
   revision; as an adaptation not in the notes, a database sequence incremented in the same
   transaction that grants the lease).
4. Pass the token on every write to the protected resource. Carry it in the request, not in a
   shared variable that a paused thread might read late.
5. Make the resource enforce it: a `WHERE token >= stored` conditional update, an `If-Match` style
   precondition, or a check inside the storage layer.
6. Make the new holder write once immediately so older tokens are fenced.
7. Never compare a remote expiry time with the local wall clock; measure local elapsed time with a
   monotonic clock, and still fence.
8. Use the coordination service for the lock rather than rolling your own
   (`linearizability-and-consensus.md`).

## 8. Verification
- Pause test: acquire the lease, `SIGSTOP` the holder until the lease expires, let a second holder
  write, `SIGCONT` the first, and assert its write is rejected.
- Delay test: hold a write in a proxy past the lease expiry and release it; assert rejection.
- Assert at the storage layer that accepted tokens are monotonic non-decreasing (inferred).
- Review warning signs: comparing local `now()` with a remote-supplied expiry; assuming the code
  between "check lease" and "act" is fast; "exactly one leader" assumed without fencing; a returning
  old leader that is not demoted.
