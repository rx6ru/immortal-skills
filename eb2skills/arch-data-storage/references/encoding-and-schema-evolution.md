# Encoding formats and schema evolution

Use this file whenever a change touches a stored or transmitted data shape: adding, removing, renaming or retyping a field in a protobuf, Avro, JSON, database column, event, message or API payload; choosing a serialisation format; or reviewing a change for rolling-deploy safety.

Contents
1. Why compatibility matters
2. Compatibility vocabulary and direction rules
3. Choosing a format
4. Language-specific formats (avoid)
5. JSON, XML, CSV, JSON Schema, binary JSON
6. Protocol Buffers and Thrift
7. Avro
8. Format comparison table
9. The compatibility checklist
10. Tests that prove compatibility
11. Worked change examples

Sources: DDIA 2e ch. 5, ch. 3 (schema-on-read migrations). Where a statement is marked "inferred" it is an extension of the notes, not a claim by the book.

---

## 1. Why compatibility matters

Applications change, so data formats change. A relational database has exactly one schema in force at a time; a schema-on-read database holds a mix of old and new shapes. Code cannot change instantly: servers are upgraded by rolling upgrade (a few nodes at a time, monitor, continue; zero downtime, encourages small frequent releases) and client code updates when the user decides. Therefore old and new code, and old and new data formats, coexist at all times. Every format change must be judged for what runs against what.

Data outlives code: application code is replaced in minutes, but five-year-old rows stay in their original encoding unless rewritten. Rewriting is costly, so databases defer: LSM engines rewrite into the latest format during compaction; relational databases allow cheap changes such as adding a nullable column (readers fill null for missing columns) without rewriting rows. Complex changes (single-valued to multi-valued, moving data to another table) still need a rewrite, usually in the application, and cross-version compatibility during such migrations is described as an open research problem (Project Cambria lenses and Stripe online migrations are named).

## 2. Compatibility vocabulary and direction rules

- **Backward compatibility**: newer code can read data written by older code. Usually easy, since you know the old format.
- **Forward compatibility**: older code can read data written by newer code. Harder: old code must ignore additions it does not understand.
- Direction rules for an API: old client to new service needs backward compatibility on the request and forward compatibility on the response. New client to old service needs forward compatibility on the request and backward compatibility on the response.

**The unknown-field loss hazard.** New code writes a record with a new field. Old code reads it into a model object that has no such field, modifies something else, and writes it back; the new field is silently lost. The same happens in a consumer that republishes messages. Required behaviour: preserve unknown fields on a read-modify-write round trip. ORMs and model mappers are the usual culprit.

## 3. Choosing a format

| Context | Pick | Reason |
|---|---|---|
| Public REST API, interchange between organisations, config | JSON (with JSON Schema or OpenAPI) | Ubiquitous, human-readable; agreeing across organisations outweighs elegance |
| Service-to-service RPC with managed IDL | Protocol Buffers (gRPC) or Thrift | Compact, tag-numbered evolution rules, code generation |
| Data pipelines, big files, Kafka with a schema registry, database dumps | Avro | Most compact, name-based resolution, generated schemas |
| Analytical files | Parquet or ORC (columnar), Avro container files for row-oriented archives | See `analytical-storage.md` |
| Anything persistent or inter-service | Never language-native serialisation | See section 4 |
| Binary JSON (MessagePack, CBOR, BSON) | Rarely | Small gain, no schema, loses readability |

Zero-copy formats (Cap'n Proto, FlatBuffers) can be used in memory and on the wire without a conversion step; databases that work directly on compressed column data also skip decoding. Keep the number of concurrent schema formats small. Merits of schema-based binary formats: compact (no field names), the schema is documentation guaranteed to be current (it is needed to decode), a schema registry allows compatibility checks before deployment, and code generation gives compile-time type checking.

## 4. Language-specific formats (Java Serializable, Python pickle, Ruby Marshal, Kryo)

Problems: tied to one language (long-term lock-in, blocks integration); decoding must instantiate arbitrary classes, which is a deserialisation-of-untrusted-data hole and often remote code execution (CWE-502); versioning is an afterthought; efficiency is an afterthought. Rule: use only for very transient purposes, never for storage or inter-service data.

Review check: grep for `pickle.load`, `ObjectInputStream`, `Marshal.load` and similar on any data that crosses a trust or time boundary (adaptation).

## 5. Textual formats

- Numbers: XML and CSV cannot tell numbers from digit strings without a schema. JSON separates strings from numbers but not integers from floats and sets no precision. Integers above 2^53 lose precision when parsed as IEEE-754 doubles (JavaScript). Example in the book: X/Twitter returns 64-bit post IDs twice, as a number and as a decimal string. Send large IDs as strings.
- No binary strings: use Base64 (about 33% bigger; the schema must say to decode it).
- CSV has no schema, ambiguous escaping, inconsistent parsers, and manual handling when columns are added. XML is verbose and complicated.
- **JSON Schema** (draft-07 in the example): primitive types plus validation constraints (port minimum 1, maximum 65535). Used in OpenAPI, schema registries (Confluent Schema Registry, Apicurio) and databases (PostgreSQL pg_jsonschema, MongoDB `$jsonSchema`).
  - Open content model (additionalProperties true, the default) accepts undefined fields of any type; closed model accepts only defined fields. Schemas therefore usually say what is not permitted. Object keys are always strings, so an integer-key map uses `patternProperties` such as `"^[0-9]+$"` with additionalProperties false.
  - Hazard: conditionals, remote references and open content make schemas hard to reason about and to evolve compatibly. A closed content model breaks forward compatibility for older validators.
- **Binary JSON** (MessagePack, CBOR, BSON and others) adds types but keeps the schema-less JSON model, so field names are embedded in every record. The book's sample record is 66 bytes versus 81 textual: not worth the lost readability for most uses. Sizes are for one specific record; use only as a relative comparison.

## 6. Protocol Buffers (Thrift is very similar)

Needs a schema in an IDL; a code generator produces classes.

```proto
message Person {
  string user_name       = 1;
  int64  favorite_number = 2;
  repeated string interests = 3;
}
```

Wire format: each field is a tag number plus type and then the value; no field names; unset fields omitted; integers are varints (7 data bits per byte, top bit as continuation); `repeated` is the same tag appearing multiple times. The sample record is 33 bytes. **The tag number is the field's identity.**

| Change | Safe? | Notes |
|---|---|---|
| Rename a field | Yes | Names are not on the wire |
| Change a tag number | Never | Invalidates all existing data |
| Add a field | Yes, with a new tag | Old code ignores the unknown tag (the type annotation says how many bytes to skip): forward compatible. New code reading old data fills a default: backward compatible |
| Remove a field | Yes, but never reuse its tag | Mark the tag `reserved`; old data may still contain it |
| Change type | Only some conversions, risk of truncation | int32 to int64: new code reads old data (padded); old code reading new data into a 32-bit variable truncates large values |
| Single value to repeated list | Treat as a type change; check the docs (inferred) | |

Rename caveat (adaptation, not in the notes): "rename is safe" holds for the binary wire format. If the same messages are also rendered as proto-JSON or text format, or other code refers to the generated field name, a rename breaks those.

Adapted practice: use `reserved 4; reserved "old_name";` in the message; run a breaking-change detector in CI (for example `buf breaking`, a modern tool, adaptation).

## 7. Avro

Two schema languages: Avro IDL (human) and JSON (machine). No tag numbers; the encoded record (32 bytes, the most compact in the sample) is values concatenated with no field identifiers or type info. So decoding must follow the schema's field order, and the reader must know the exact writer's schema.

```
record Person {
  string userName;
  union { null, long } favoriteNumber = null;
  array<string> interests;
}
```

**Writer's schema vs reader's schema.** The writer encodes with its schema; the reader supplies its own, possibly different, schema and obtains the writer's. Avro resolves them: fields match by name (order may differ); a field in the writer's schema but not the reader's is ignored; a field in the reader's but not the writer's takes the reader's declared default.

Rules:
- Forward compatible means the writer is newer than the reader; backward compatible means the writer is older.
- You may add or remove only fields that have a default. Adding a field without a default breaks backward compatibility (new reader, old data). Removing a field without a default breaks forward compatibility (old reader, new data).
- null is not a universal default. A nullable field is a union that includes null, and null can be the default only if it is the first branch of the union.
- Type changes are fine where Avro can convert.
- Renaming uses aliases in the reader's schema: backward compatible, not forward compatible.
- Adding a union branch: backward compatible, not forward compatible.

How the reader gets the writer's schema:

| Context | Mechanism |
|---|---|
| Large file of many records with one schema | Embed the schema once at the start (object container file) |
| Database with individually written records over time | Prefix each record with a schema version number and keep a table of versions (Confluent Schema Registry for Kafka, LinkedIn Espresso); version = incrementing integer or schema hash |
| Network connection between two processes | Negotiate versions at connection setup (Avro RPC) |

Dynamically generated schemas are Avro's selling point: generate a schema from a relational schema (table to record, column to field by name) and dump the database to a container file; when the database schema changes, regenerate, and name matching handles old writers and new readers. With protobuf, tag numbers would need manual mapping and care never to reuse tags.

## 8. Format comparison table

| | JSON/XML/CSV | Binary JSON | Protobuf/Thrift | Avro |
|---|---|---|---|---|
| Schema | optional (JSON Schema, XSD) | none | required, IDL, tag numbers | required, no tags, writer + reader schema |
| Field identity on the wire | name | name | tag number | position under the writer's schema |
| Sample record size | 81 B | 66 B | 33 B | 32 B |
| Evolution safety | convention-based | none enforced | strong rules via tags | strong rules via name + default resolution |
| Human readable | yes | no | no | no |
| Generated schemas | n/a | n/a | awkward | good |
| Best for | interchange, public REST, config | niche | RPC (gRPC) | Hadoop/pipelines, large files, Kafka with registry, DB dumps |

ASN.1 (1984; DER encodes X.509 certificates) is similar to protobuf but complex and poorly documented: not for new applications. Database vendors also have proprietary wire protocols with drivers (ODBC, JDBC).

## 9. The compatibility checklist

Run through every applicable item before shipping a schema or API change.

1. Which direction is exercised? Database or event log: old and new data both persist, so both directions are needed. RPC/REST during a rollout: servers first, so requests need backward compatibility and responses forward compatibility. Cross-organisation public API: assume old clients exist indefinitely. The "servers first, clients second" assumption fails for mobile apps and third-party clients.
2. Protobuf/Thrift: never renumber; never reuse a removed tag (reserve it); new fields get new tags and tolerate absence via defaults; renames are fine; widening integer types is backward compatible but unsafe for old readers (truncation); old code preserves unknown fields on re-serialisation.
3. Avro: every added or removed field has a default; a nullable field is a union with null first if the default is null; renames through aliases (backward only); adding a union branch (backward only); type changes only where Avro can promote; the writer's schema must be obtainable (file header, version prefix plus registry, or connection handshake).
4. JSON/REST: add only optional request parameters and new response fields; clients must ignore unknown fields; never change the meaning or type of an existing field; send integers above 2^53 as strings; choose the open vs closed content model deliberately.
5. Read-modify-write paths (ORM, republishing consumers) preserve unknown fields.
6. Store schemas in a registry and run automated compatibility checks in CI before deploy. Backward, forward and full modes are common practice in registries (inferred; the notes do not name the modes).
7. Test matrix (inferred): {old writer, new writer} x {old reader, new reader}, with golden binary fixtures from every released version.
8. Workflow code: version workflows rather than editing in place; keep them deterministic; keep call order stable (see `dataflow-modes.md`).
9. No language-native serialisation for persistent or inter-service data.

## 10. Tests that prove compatibility

Implement these as automated tests, not review comments (the matrix and round trip are inferred from the notes' hazards):

1. **Round trip with unknown field**: encode with schema v2, decode with v1 code, change an unrelated field, re-encode, decode with v2. The v2-only field must still be present.
2. **Cross-version matrix**: for each released version keep a captured encoded sample. New code must decode all of them; the previous release's code must decode samples produced by the new code (forward direction).
3. **Registry or linter gate**: CI fails when a change violates the format's rules (reused tag number, new Avro field without default).
4. **Large-number test**: a JSON payload with an ID above 2^53 survives a round trip through every language involved.
5. **Rolling-upgrade rehearsal** (adaptation): run old and new service versions side by side against the same database or topic and exercise reads and writes in both directions.

Sketch (Python, protobuf; adaptation). It needs two generated modules, one per schema version. Define them in separate packages so the names do not clash:

```proto
// person_v1.proto: package v1; message Person { string user_name = 1; int64 favorite_number = 2; repeated string interests = 3; }
// person_v2.proto: same message in package v2, plus: string nickname = 4;
// generate with: protoc --python_out=gen person_v1.proto person_v2.proto
```

```python
import person_v1_pb2 as p1, person_v2_pb2 as p2     # generated modules
PersonV1, PersonV2 = p1.Person, p2.Person

def test_unknown_field_survives_old_reader():
    v2 = PersonV2(user_name="a", favorite_number=1, nickname="x")   # nickname: new field
    raw = v2.SerializeToString()
    old = PersonV1(); old.ParseFromString(raw)       # old code ignores nickname
    old.favorite_number = 2
    again = PersonV2(); again.ParseFromString(old.SerializeToString())
    assert again.nickname == "x"                     # relies on unknown-field retention
    assert again.favorite_number == 2
```
Run during review with protobuf 7.36 and protoc 36.1: passes. Some runtimes (older protobuf, some model mappers) drop unknown fields by default; the test exists to catch exactly that.

This test is format-specific. Avro cannot pass it by design: the reader's schema resolution ignores writer-only fields, so an old-schema read-modify-write loses the new field (checked with fastavro: the field came back as its default, null). For Avro, keep republishing consumers on a passthrough path (forward the original bytes, or decode with the writer's schema and re-encode with it) or upgrade them before producers start writing the new field (adaptation, derived from the resolution rule). For JSON, the test passes only if the code keeps the parsed map instead of binding to a fixed class.

## 11. Worked change examples

| Change | Protobuf | Avro | JSON/REST |
|---|---|---|---|
| Add an optional field | New tag, default on absence: safe both ways | Add with a default: safe both ways | New response field: safe if clients ignore unknowns; new optional request param: safe |
| Remove a field | Stop using, reserve tag | Only if it had a default | Stop returning only after confirming no client reads it (inferred) |
| Rename | Safe | Alias: backward only | Breaking for anyone reading it; add the new name, keep the old, retire later (inferred) |
| Widen int32 to int64 | Backward ok; old readers may truncate | Promotion allowed by Avro | Not an issue in JSON text, but the 2^53 limit applies |
| Make a field nullable | Absence already means default (inferred from the default-fill rule) | Union with null; mind default order | Clients must tolerate null |
| Split `name` into `first`, `last` | Add two fields, dual-write, backfill, then retire | Same with defaults | Same; document-store reader handles both shapes during transition |

For databases, the add-column / backfill / switch-readers / drop sequence and online schema-change tools are in `data-models.md` section 4.
