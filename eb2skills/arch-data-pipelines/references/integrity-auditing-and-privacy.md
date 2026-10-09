# Integrity, auditing and privacy in derived data

Read this when a pipeline carries personal data, produces decisions about people, retains data indefinitely, needs deletion to work through logs and derived stores, or when someone asks how you would know the data is still correct.

Contents: 1 Trust but verify; 2 Designing for auditability; 3 Audit tools and their reach; 4 Deletion in immutable and derived data; 5 Data handling rules; 6 Automated decisions about people; 7 Privacy and consent; 8 Review questions; 9 Caveats; 10 Verify.

Sources: DDIA 2e ch. 13 (trust but verify, auditing), ch. 12 (immutability limits, crypto-shredding), ch. 14 (ethics, privacy, GDPR). Items marked (inferred) are labelled so in the notes.

## 1. Trust but verify

The system model assumptions (a crash is the failure; fsynced data is safe; memory is not corrupted; the CPU computes correctly) are really probabilities, and at scale unlikely things happen. Corruption is observed in memory, disk and network. Software has bugs: past MySQL versions failed to maintain uniqueness constraints; PostgreSQL's serializable mode has shown write-skew anomalies. Application code is reviewed far less, and many applications do not use foreign keys or uniqueness constraints correctly. ACID consistency presumes bug-free transactions; misuse such as unsafe weak isolation voids it.

Auditing means checking data integrity. HDFS, S3 and Ceph continually read back files, compare replicas and move data to mitigate silent disk corruption. "If you want to be sure that your data is still there, you have to read it and check." Test restoring backups periodically. Few systems audit themselves, so build it.

Continuous auditing lets you change things with confidence, like automated tests, which enables evolution.

## 2. Designing for auditability

With plain database transactions the why of a mutation is lost, because the application invocation was transient. With event sourcing, user input is one immutable event and state updates are derived deterministically; the same log and the same code version give the same state. Consequences:
- Use hashes to verify event storage.
- Re-run batch or stream derivations to compare with the live derived state, or run a redundant derivation in parallel.
- Deterministic dataflow enables debugging by replay (time-travel debugging) and provenance tracing.
- Logging reads as events (see `stream-processing-correctness.md`) records what the user saw.

Include as many stages as possible in each integrity check, so the disks, networks, services and algorithms along the path are covered implicitly. Per-stage health checks alone miss end-to-end corruption (see the dropped-field example in `pipeline-reliability.md`).

## 3. Audit tools and their reach

| Tool | What it gives | Limit |
|---|---|---|
| Audit table | record of changes | integrity of the audit log versus state is hard to guarantee |
| Tamper-proof log signed periodically (hardware security module) | evidence the log was not altered | does not prove the right transactions were entered |
| Blockchain | shared append-only log with cryptographic checks; smart contracts resemble stream processors; Byzantine fault tolerant | too heavy for most applications |
| Merkle trees | hash trees proving a record belongs to a dataset | need scalability work to spread |
| Certificate transparency style logs | append-only verified logs, single leader per log, no consensus needed | lightweight but not mainstream |
| Reconciliation job (inferred) | compare derived store with source: counts, checksums, sampled rows | catches divergence, not intent errors |

Practical default: reconciliation jobs plus periodic restore tests plus checksums at endpoints. Reach for cryptographic tooling only when parties do not trust each other.

## 4. Deletion in immutable and derived data

Immutability has limits: high-churn small datasets make history huge and fragmented, so compaction and garbage collection performance is critical. Legal deletion (GDPR) needs real removal: Datomic's excision and Fossil's shunning exist. True deletion is hard: SSD and file-system copy-on-write keep copies, backups are immutable. Net: deletion often means "make harder to retrieve", not "impossible".

Crypto-shredding: store the deletable data encrypted and forget the key. You must choose the key granularity up front: deletion is all-or-nothing per key, and a key per item makes the key store as big as the data. Puncturable encryption exists but is not widely used.

Tension: immutable append-only logs and long retention aid auditing and reprocessing but conflict with deletion and minimisation duties (inferred; the ethics chapter itself says purge data when no longer needed). Resolution options (inferred, not in the text): retention limits on the log, per-subject encryption keys with crypto-shredding, and a plan that includes backups. Derived data of a deleted user must also be deletable (inferred), which means a deletion event must propagate through every derived store and the next reprocessing must not resurrect the data from an archive.

Adaptation checklist for a deletion request:
1. Inventory every store holding the subject's data: primary, log topics (including compacted ones), derived indexes and caches, warehouse tables, object-store archives, backups, ML training sets.
2. For each, name the deletion mechanism (row delete and tombstone for compacted topics, key destruction for crypto-shredded stores, excision, expiry on retention) and its latency.
3. Make reprocessing jobs apply the deletion list so a rebuild does not bring data back.
4. Record that the deletion happened without recording the deleted data.

## 5. Data handling rules

| Situation | Do |
|---|---|
| Adding tracking, telemetry or behaviour logging | State the purpose; collect the minimum; separate what directly benefits the user (ranking, A/B tests) from profiling; set retention and a purge job; do not collect what you cannot justify (data minimisation, purpose limitation) |
| Storing sensitive or derived data | Treat it as hazardous material: threat-model breach, insiders, compelled disclosure and acquisition; delete rather than keep "just in case". Data you do not hold cannot be leaked, stolen or compelled |
| Pipelines and derived datasets | Combining datasets creates information users never consented to; make deletion of a subject propagate (inferred) |
| Temporary storage in pipelines | No PII in temporary storage, or encrypt it; TTL on logs and PII; least privilege per stage (SRE Workbook ch. 13) |
| Design reviews | Include an explicit "consequences and misuse" section; consider future owners and governments |

Industrial analogy from the chapter: safeguards cost business money but society benefited; data is the pollution problem of the information age, so how data is contained and disposed of is central.

## 6. Automated decisions about people

For credit, hiring, insurance, moderation or risk scores, the chapter's issues and their engineering consequences:

| Issue | Mechanism | Consequence for design |
|---|---|---|
| Asymmetric caution | a missed opportunity costs little, a bad decision costs a lot, so "if in doubt, say no"; a person labelled risky collects "no" across many domains | provide an appeal or human review path; weigh false-positive cost to the individual, not only to the business |
| Bias | rules are inferred from data, patterns are opaque; proxies for protected traits (postal code, IP address) exist; models extrapolate the past | audit features for correlation with protected traits (inferred); do not assume data-driven means fair |
| Accountability | blurred responsibility | keep decisions explainable and traceable; name an accountable owner (inferred) |
| Statistical vs individual | probabilistic output wrong for individuals; scoring asks "who is similar to you" | provide error correction; surface uncertainty |
| Dual use | analytics that direct aid can find vulnerable people to exploit | consider misuse of the capability when building it |
| Feedback loops | predictions change what they predict (echo chambers; credit scores used for hiring) | model the whole socio-technical system; watch for amplification |

Measure error rates per group (inferred) and monitor feedback loops. People should not be able to evade responsibility by blaming an algorithm.

## 7. Privacy and consent

- Data a user enters deliberately means the service works for the user. Behaviour tracked as a side effect gives the service interests that may conflict with the user's. Legitimate tracking benefits users: ranking from clicks, recommendations, A/B tests, UI flow analysis.
- Consent is weak when: it is not necessary for the user's benefit; users are not informed (derived datasets combine many users and external sources); there is no reciprocity (terms set by the service); the service is effectively essential (network effects) so refusing has a social cost.
- GDPR consent must be freely given, specific, informed and unambiguous; the user can refuse or withdraw without detriment; plain language; silence, pre-ticked boxes and inactivity are not consent. Other lawful bases exist (legal obligation, protecting life, legitimate interest such as fraud prevention). Principles: purpose limitation and data minimisation. These are EU-centric; other jurisdictions differ, so check current law.
- Privacy is a decision right, the freedom to choose what to reveal to whom; it is not the same as secrecy. Surveillance moves that decision to the collector. Expect data to be wrong, undesirable or inappropriate and build mechanisms for those failures.
- User-facing privacy settings restrict other users only; the service keeps internal access.
- Concrete first step: do not retain data forever; purge when no longer needed; minimise collection.

## 8. Review questions

For any pipeline touching people's data (the first five are implied by the chapter and marked inferred there):
1. Who is affected by a wrong output? Can they find out why and appeal?
2. Does any input proxy for a protected trait?
3. Does the output feed back into future inputs?
4. Who is accountable?
5. What is the purpose of each field, and when is it purged?
6. Where does a deletion propagate, and how is it proved?
7. How would we notice silent corruption, and when did we last restore from backup?

## 9. Caveats

The ethics chapter is argumentative rather than empirical and takes strong positions (including a deliberately polemic "surveillance" framing). Legal references are EU and GDPR centred; enforcement and rulings change. The book gives no technical mechanism for appeals, bias testing or deletion in derived stores; those parts above are extensions. Treat it as a checklist of risk areas to raise, not a compliance procedure; real compliance needs legal input. Cryptographic audit tooling is not mainstream.

## 10. Verify

- Restore test: restore the latest backup of the system of record into a scratch environment and run the integrity checks; record the date and result. Never having restored a backup is a warning sign.
- Reconciliation: show a job comparing a derived store against its source (counts and checksums, or sampled rows) with its schedule, alert and last result.
- Rederivation: rerun the derivation from the log with the same code version and compare with live derived data; show the diff is empty or explained.
- Deletion test: delete a test subject, wait for the stated propagation latency, then query every store in the inventory (including a rebuilt derived store) and show the subject is absent.
- Retention: show the purge job and its configured retention for each store holding personal data.
- For decision systems: show the appeal path, the owner, and the per-group error-rate report if the system affects individuals.
