# Compatibility rules for encoded data and APIs

Contents: 1. Definitions and direction rules; 2. The unknown-field hazard; 3. Format rules (JSON, protobuf/gRPC, Avro); 4. Format comparison; 5. Schema registries and where the writer schema comes from; 6. Compatibility checklist before shipping; 7. Test matrix; 8. Dataflow modes

Sources: DDIA 2e ch. 5 (figures were missing from the notes; some items are marked inferred there); Mastering API Architecture (MAA) ch. 1.

## 1. Definitions and direction rules

- Backward compatibility: newer code can read data written by older code. Usually easy, because the old format is known.
- Forward compatibility: older code can read data written by newer code. Harder: old code must ignore what it does not understand.
- Code cannot change instantly. Servers do rolling upgrades; clients update when users decide. Old and new code, and old and new data formats, therefore coexist.

Direction for calls:
- Old client to new service: backward compatibility on the request, forward compatibility on the response.
- New client to old service: forward compatibility on the request, backward compatibility on the response.
- Simplifying assumption for service evolution: servers upgrade first, clients second. This fails for mobile apps and third-party clients.
- Data in a database or event log persists, so both directions are needed there.

## 2. The unknown-field hazard

A new version writes a record with a new field. An old version reads it into a model object that drops unknown fields, modifies another field, and writes it back. The new field is silently lost. The same applies to a consumer that republishes messages to another topic, and to read-modify-write through an ORM.

Rule: preserve unknown fields on round trips. Test (the notes mark this as inferred): encode with schema v2, decode with v1 code, re-encode, decode with v2; the new field must still be present.

## 3. Format rules

### JSON / REST (plain)
- Add only optional request parameters and new response fields; both are considered compatible, so clients must ignore unknown response fields.
- Do not change the meaning or type of an existing field.
- Integers above 2^53 lose precision as doubles; send them as strings.
- JSON Schema: the default open content model allows undefined fields; a closed model (additionalProperties false) breaks forward compatibility for old validators. Choose deliberately. Conditionals, remote references and open content make schemas hard to evolve; keep them simple.
- Binary JSON variants (MessagePack and others) keep the schemaless JSON model and embed field names, saving little (66 against 81 bytes for the sample record). Usually not worth losing readability.

### Protocol Buffers / Thrift / gRPC
The tag number is the field's identity.

| Change | Safe? |
|---|---|
| Rename a field | Yes, names are not on the wire |
| Change a tag number | Never; invalidates existing data |
| Add a field with a new tag | Yes. Old code skips the unknown tag (forward compatible); new code reading old data uses the default (backward compatible) |
| Remove a field | Yes, but never reuse its tag; mark it `reserved` |
| Change datatype | Only some conversions, with truncation risk: int32 to int64 lets new code read old data, but old code reading new data into 32 bits truncates large values |
| Make a field mandatory | Breaks compatibility (MAA ch. 1) |
| Add a service or method | Compatible |
| Single-valued to repeated | Treated as a type change; check the documentation (inferred in notes) |

Position and numbering are critical. gRPC is much stricter than JSON/OpenAPI, which tolerates extra fields and ordering unless runtime validation is on. Never let a generator auto-number proto fields (openapi2proto orders alphabetically, so a new field renumbers old ones).

### Avro
No tag numbers; values are concatenated in schema order, so decoding needs the exact writer's schema. The reader supplies its own schema and Avro resolves differences:
- Fields match by name; order may differ.
- In the writer but not the reader: ignored.
- In the reader but not the writer: filled with the reader's default.

| Change | Compatibility |
|---|---|
| Add or remove a field | Only if it has a default. Adding without a default breaks backward compatibility; removing without a default breaks forward compatibility |
| Nullable field | Needs a union including null; null can be the default only if null is the first branch |
| Rename | Use aliases in the reader schema; backward compatible, not forward compatible |
| Add a union branch | Backward compatible, not forward compatible |
| Change type | Only where Avro can convert |

## 4. Format comparison

| | JSON/XML/CSV | Binary JSON | Protobuf/Thrift | Avro |
|---|---|---|---|---|
| Schema | optional (JSON Schema, XSD) | none | required, IDL with tags | required, no tags; writer plus reader schema |
| Field identity on the wire | name | name | tag number | position under the writer's schema |
| Sample record size | 81 B | 66 B | 33 B | 32 B (one record; use only as a relative comparison) |
| Evolution safety | convention | none enforced | strong rules via tags | strong rules via name and default |
| Human readable | yes | no | no | no |
| Best for | inter-organisation interchange, public REST, config | niche | RPC (gRPC), services with hand-managed IDL | Hadoop/data pipelines, big files, Kafka with a registry, DB dumps |

Language-specific serialisation (Java Serializable, pickle, Marshal, Kryo) is for very transient use only. It locks you to one language, decoding instantiates arbitrary classes (remote code execution, CWE-502), versioning is an afterthought, and efficiency is poor. Never use it for storage or inter-service data. ASN.1 is complex and badly documented; not for new applications. Keep the number of concurrent schema formats small.

## 5. Schema registries and where the writer schema comes from (Avro)

| Context | Mechanism |
|---|---|
| Large file, many records, one schema | Embed the schema once at the file start (object container file) |
| Database with records written over time | Prefix each record with a schema version number and keep a registry (incrementing integer or schema hash) |
| Network connection between two processes | Negotiate versions at connection setup, valid for the connection's life |

A schema-version store doubles as documentation and lets CI check compatibility before deploy. A registry for message brokers should store all valid versions and check compatibility; AsyncAPI is the messaging analogue of OpenAPI. Common registry modes (backward, forward, full) are named in the notes only as inferred practice.

## 6. Compatibility checklist before shipping a schema or API change

1. Which direction is exercised? Database or event log: both. RPC/REST during rollout: servers first, so request backward and response forward. Public cross-organisation API: assume indefinite old clients.
2. Protobuf: no renumbering, no reuse of removed tags (reserve them), new fields get new tags and tolerate absence, widening ints is unsafe for old readers, old code preserves unknown fields.
3. Avro: every added or removed field has a default; nullable means a union with null first when the default is null; renames via aliases (backward only); union branch additions are backward only; the writer's schema is obtainable.
4. JSON/REST: only optional additions; clients ignore unknown fields; no type or meaning changes; large ints as strings; deliberate open or closed content model.
5. Read-modify-write paths (ORMs, republishing consumers) preserve unknown fields.
6. Schemas live in a registry or the repo, and an automated compatibility check runs in CI.
7. Test matrix (inferred): {old writer, new writer} x {old reader, new reader}, with golden fixtures captured from each released version.
8. Workflow code is versioned rather than edited, deterministic, and keeps call order stable (durable execution engines replay it).
9. No language-native serialisation for persistent or inter-service data.

## 7. Test matrix in practice

A minimal automated version for any format: keep a directory of fixtures written by each released version. In CI, decode every fixture with the current reader, re-encode with the current writer, and decode that output with each previously released reader. A failure names the pair that broke. Add the unknown-field round trip from section 2 as one explicit test.

## 8. Dataflow modes (DDIA 2e ch. 5)

- Through databases: data outlives code. Rows written years ago keep their encoding unless rewritten; LSM engines rewrite during compaction, relational databases allow cheap changes such as adding a nullable column. Complex changes (single-valued to multi-valued, moving data to another table) need a rewrite, often at application level. Archival dumps use the latest schema (Avro container files, Parquet).
- Through services: REST and RPC, evolution as above.
- Through workflows and brokers: see `choosing-an-api-style.md` section 9.
