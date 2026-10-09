# Configuration design and safe configuration change

Sources: SRE Workbook ch. 14 (Configuration Design and Best Practices), ch. 15 (Configuration Specifics), App. C. Jsonnet, ksonnet, Helm and Spinnaker are 2018-era examples; ksonnet is archived, and Helm, Kustomize, CUE, Dhall, Pulumi and Starlark now compete. The principles (hermetic evaluation, separating config from data, tooling, validation, sandboxing) are stable.

## Contents

1. What configuration is and why it matters for reliability
2. Philosophy: ask fewer questions
3. Mechanics: separating config from data
4. Tooling, ownership, change tracking
5. Safe application of a config change
6. Config-induced toil and the strategy ladder
7. Critical properties of a config system
8. The five language pitfalls
9. Integrating a config language
10. Designing an in-house app to coexist with a config language
11. Validation
12. Operating a config system
13. When to evaluate: decision table
14. Guarding against abusive config
15. Worked example: templates with an escape hatch
16. Review checklist and warning signs

## 1. What configuration is and why it matters

Configuration is a human-computer interface for changing system behaviour without a rebuild or redeploy. A system has three parts (software, data set, configuration) and the boundaries blur (a Lua-configured server is code; stored procedures are data). A good interface allows quick, confident, testable change; a poor one raises cognitive load and mistakes.

Configuration differs from code: one option can change functionality drastically (one bad firewall rule locks you out), it often lives in an environment you cannot test, and changes happen under pressure in incidents. Config interface quality affects an organisation's ability to run the system reliably, as code quality affects maintainability. Outage data supports putting effort here: configuration push is 31% of outage triggers and, with binary push, 68% (App. C), and config changes dominate root causes over time (ch. 15).

Separate two questions. Philosophy (language independent): how to structure config, the right abstraction level, diverging use cases. Mechanics: language design, deployment strategy, interaction with other systems. Language choice (XML versus Lua) does not rescue an interface that demands lots of hard-to-understand input; simple inputs also fail if the interface is cumbersome (a configuration that must be re-entered from scratch after any fix).

## 2. Philosophy: ask fewer questions

- Ideal: no configuration. The system infers settings from deployment, workload and existing config. Fewer knobs mean a smaller error surface and lower cognitive load. If you can remove configuration altogether, that is always the best option (ch. 15).
- Every config option asks the user a question. Infrastructure-centric view: more knobs, better tuning. User-centric view (the book's preference): every question is a chore between the user and their goal. This requires designing for a specific key audience (needs user research). Limited options can drive better adoption than versatile software because it works out of the box.
- Questions near user goals: "hot green tea" versus water volume, temperature, steeping time and cup. Goal-level inputs let the system improve how it implements the goal; step-level inputs bind the system to follow them (example: run an analysis job without choosing physical machines).
- Mandatory versus optional: mandatory questions are needed for any function (who to charge); optional ones improve quality (number of worker processes). Minimise mandatory questions by turning them into optional ones with safe defaults (dry-run by default). Defaults can be dynamic: thread count from core count, JVM heap from container memory, with an override. If a significant share of users report problems with a dynamic default, the decision logic no longer matches the user base: improve it broadly rather than adding knobs. If only a few are unhappy, let them set the option manually.
- Defaults are powerful because most users keep them; choose them carefully. Remove optional questions with no clear use case; add a knob only for a real need. With inheritance, allow leaf configs to revert to the default for any optional question.
- Escaping simplicity: do not set the default at the lowest common denominator of regular and power users. Model power use as optional overrides of defaults ("green tea" plus "steep five minutes"), like an advanced-options screen. Optimise the sum of hours the whole organisation spends configuring, including decision paralysis and correction time. If more than a small subset need complex config, you misidentified the common use cases; redo user research.
- Case in the book: a team spent a month cutting mandatory questions and finding good defaults; the result was adopted widely, users changed config with confidence and needed little support. Misconfiguration and support were never eliminated.

## 3. Mechanics: separating config from data

Best of both worlds: infrastructure operates on plain static data (protobuf, YAML, JSON), and users interact with a higher-level interface that generates it (a DSL, Lua, a purpose-built language, or a web UI), "compiled" like C++. Benefits:

- Different cultures and languages can coexist after migrations or acquisitions.
- Compilation can be automatic (post-commit hook) or periodic at the cost of delay.
- Static output is queryable: load the JSON into a database to see which parameters are used by whom, find removable features, or measure the impact of a buggy option. Store ingestion metadata (source file, language) to find authors.
- Avoid tight coupling between the interface data format and the internal data structure (internal may carry implementation-only data).

## 4. Tooling, ownership, change tracking

- Semantic validation, not just syntax: a nonexistent directory typo; 1000x RAM from wrong units. For each misconfiguration ask whether it could be rejected at commit time.
- Syntax tooling: editor highlighting, a linter, an automatic formatter (removes formatting debates, prevents indentation mistakes in whitespace-sensitive formats). Large organisations benefit from deprecation annotations and automatic rewrite tools for central migrations.
- Each snippet has one clear owner (for example a directory owned by one production group).
- Version configuration (VCS, and equivalent history for UI- or API-ingested config); couple the config version to the software version to avoid configuring features the binary lacks.
- Log both config changes and their application. Committing is not always applying. During an incident this tells you the full set of edits in a change, lets you roll back confidently, and lets you notify affected parties.

## 5. Safe application of a config change

Three properties (ch. 14):
1. Deploy gradually; no all-or-nothing. Avoid the global all-at-once push (Kubernetes rolling updates; the canary approach in `canarying-and-rollouts.md`).
2. Be able to roll back. Rolling back is faster and higher-confidence than patching. To roll forward or back, config must be hermetic: no dependence on external mutable resources (config in VCS that references data on a network filesystem is not hermetic).
3. Automatic rollback, or at least halt, if the change causes loss of operator control. Examples: the desktop resolution-change confirmation countdown; auto-revert timers on firewall changes that could lock the admin out.

These principles apply equally to binary upgrades and data pushes.

## 6. Config-induced toil and the strategy ladder (ch. 15)

- Replication toil: config replicated across a system (INI/JSON/YAML/XML files multiply; one logical change needs edits in many files; real differences hide among duplicates). Common with microservices.
- Complexity toil: appears after you fix replication with automation or a language; the corpus grows with renewed energy and you fight emergent behaviour. It bites organisations with 10 or more engineers and compounds, so tackle it early.

Ladder:
1. Remove the config if the app is yours (pick defaults from machine info, vary values with load).
2. For replication toil, use automation or a configuration language to remove duplication. Automatic conversion from the old language only works if the old source is standard and non-broken.
3. For any system, apply operating practices (versioning, source control, tooling, testing, when-to-evaluate, abuse guards).

## 7. Critical properties of a config system

Beyond being lightweight, easy to learn, simple and expressive:
1. Tooling for config health and engineer confidence: linters, debuggers, formatters, IDE integration.
2. Hermetic evaluation: the same inputs give the same config data regardless of where or when evaluated. This gives reliable rollback and replay. Corollary: the source is interchangeable with the data it expands to.
3. Separation of config from data: evaluate config, get inspectable data, then consume it. This enables analysis and several interfaces (UIs, tools, scripts) over the same data.

## 8. The five language pitfalls

1. Not recognising config as a programming-language problem. If you do not design a language intentionally, the accidental one is bad. Data formats sprout language features: a `count` attribute on a VM schema (a loop smuggled into data; the proper approach is a loop outside the artifact); string interpolation hiding real code (checksums, base64, data-structure operations); YAML plus a text-templating language (each is fine alone, but combined they are hard for humans and tools to analyse).
2. Accidental, ad hoc language features: no IDE support or linters, undocumented semantics, feature-interaction gotchas. Decide at initial design whether simple programming constructs will be needed.
3. Too much domain-specific optimisation: a small user base means tooling and learning resources arrive late, and engineers will not invest in a language with no use outside the domain.
4. Interleaving evaluation with side effects: changing external systems or consulting out-of-band data (DNS, VM IDs, the latest build version) during config runs. This breaks hermeticity and separation; in the extreme you cannot debug config without spending money reserving cloud resources. Rule: evaluate config first, expose the resulting data for inspection, only then allow side effects.
5. A general-purpose scripting language (Python, Ruby, Lua): heavyweight or needs intrusive sandboxing for hermeticity and security; maintainers may not know it. A Python-like hermetic language such as Starlark (adaptation, from the notes' dated-section remark) is a middle path.

Recommendation: use an existing configuration DSL (HOCON, Flabbergast, Dhall, Jsonnet in the book; CUE or Starlark are current alternatives). Restrict its power with an in-house style guide if it seems too powerful; you may need it later.

Jsonnet in brief: a hermetic DSL, superset of JSON (any JSON file is a valid program that outputs itself), Python-like syntax with object-oriented and functional constructs and comments.

## 9. Integrating a config language

- If the language outputs your target natively (Jsonnet to JSON for JSON-superset consumers such as YAML, HCL), done.
- Otherwise: represent the config data in the language (maps, lists, strings are universal); use its abstractions to remove duplication; write or reuse a serializer for the output format; use plain string templating only as a last resort (for example Bash scripts).
- Drive several applications from one config: one evaluation can yield an Nginx config and a firewall config with the port defined once, plus dashboards, retention policies and alert pipelines.
- Configs can nest (a database config inside a Kubernetes ConfigMap); a good language handles the quoting. Multi-file mode: evaluation yields one object mapping filenames to contents; emulate elsewhere with a string-to-string map and a wrapper that writes files.

## 10. Designing an in-house app to coexist with a config language

Let the language do the language job; the app does everything else.

- The app consumes one pure data file; imports combine inputs in the language so the combination logic is explicit.
- Named entities are objects keyed by name, not arrays of `{name: ...}` elements. Keyed objects allow direct references and easy extension and avoid brittle indexes.
- Group by function, not by type, at the top level (`pot_assembly1: {pot, lid}` rather than separate `pots` and `lids` maps), so language abstractions can follow functional boundaries.
- Keep the data representation simple: no embedded language features, do not worry about verbosity (fix that in the language), and do not interpret custom string interpolation (conditionals, placeholders) in the app. Exceptions exist for post-generation actions such as alerts and handlers.
- Do not use the language to paper over inconsistent naming or model mistakes; fix the model. If you cannot, live with the inconsistency at the language level rather than adding more. Generated data is not fully hidden (tools, people and config databases see it).

## 11. Validation

- Validate generated data immediately after evaluation. Syntax (parsable JSON) alone finds few bugs.
- Do generic schema validation (JSON Schema, or protobuf canonical JSON validated on deserialisation), then domain checks: required fields present, referenced filenames exist, values in allowed ranges.
- Never ignore unrecognised field names (they may be a typo at the language level); hide non-output fields in the language (Jsonnet `::`).
- Run the same validation in a precommit hook and in CI.

## 12. Operating a config system

- Versioning of template and utility libraries: for a breaking change either update all consumers globally (often organisationally impossible) or version the library so consumers migrate independently (laggards accrue debt). Jsonnet has no built-in support, so use directories, with the version as the first path component of the import.
- Source control: history including who changed what, easy reliable rollback, code review of config.
- Tooling: style and lint, editor plug-ins, post-write and precommit hooks, aiming at consistency, readability and error detection.
- Testing: unit tests for template and function libraries. Instantiate them in various ways and assert the concrete output. Prefer a framework that reports all failing tests rather than stopping at the first.

## 13. When to evaluate: decision table

Because evaluation is hermetic, the data can be generated at any time between source change and use.

| Option | Pros | Cons |
|---|---|---|
| Very early: check in generated JSON beside the source (edit source, regenerate, precommit hook enforces consistency, PR) | Reviewer sees the concrete change (a pure refactor leaves the JSON unchanged); blame and audit at both levels; no language runtime in production | JSON may be unreadable, too large, or hold secrets; merge conflicts when many sources feed one JSON |
| Build time: embed the JSON in the release artifact | Controls runtime complexity, size and risk without regenerating in each PR; no desync risk | More complex build; harder to see the concrete change in review |
| Runtime: link the library, app evaluates | Simplest; can evaluate user-supplied code | Footprint and risk exposure; config bugs found at runtime are found too late; untrusted code needs care |

Examples: a client CLI evaluates in-process on the author's machine (safe); one company used Git hooks pushing generated JSON kept in the repo so the server never runs the language; daemons such as Helm or Spinnaker must evaluate on the server at runtime.

## 14. Guarding against abusive config

Evaluation should terminate quickly, but bugs or attacks can use unbounded CPU or memory: infinite recursion, unbounded list growth, and even in a non-Turing-complete language an exponential blow-up (a function calling itself twice per level 100 deep). XML and YAML have similar issues (billion-laughs style). Risk depends on trust: a trusted local CLI is fine (Ctrl-C suffices), but a service evaluating end-user config in request handlers risks denial of service. Mitigation for untrusted code: evaluate in a separate process with ulimit or an equivalent resource limit, fork the CLI binary rather than link the library, and let runaway evaluations fail safely and report to the user.

## 15. Worked example: templates with an escape hatch

Problem: the same Kubernetes Service replicated four times with differing namespace and labels, differences obscured (YAML anchors give no real abstraction and Kubernetes does not support them). Pattern in the book's language: an abstract template object with a required hidden field set to an error (instantiating without overriding it fails at evaluation, like a pure virtual method); derived values (labels, name) computed from that field; each instance overrides what differs. Functions only parameterise, whereas templates let the user override any parent field, which is the escape hatch (for example merging a session-affinity setting into the spec). Benefit grows as differences become subtle, structural, or "same change applied to all array elements". Conversion workflow: convert one YAML variant to JSON, run the formatter, add abstraction and instantiation by hand.

Use cases: one team's near-identical variants across prod, stage, dev and test, architectures and regions; an infrastructure team publishes templates for reusable components that app teams instantiate.

## 16. Review checklist and warning signs

Checklist:
1. Can the system run with zero config? Which questions are mandatory, and can each get a safe static or dynamic default?
2. Are questions in user-goal terms? Are expert overrides optional layers?
3. Interface separated from internal static data, and the internal format not coupled to the interface format?
4. Semantic validation at commit, linter and formatter, one owner per snippet, versioned, changes and applications logged?
5. Rollout gradual, rollback-able (hermetic), auto-stop when operator control is lost, tested in a canary?
6. Evaluation free of network, clock and file side effects before data is emitted? (Inferred test: evaluate twice in different environments and compare output byte for byte.)
7. Generated data schema- and domain-validated in precommit and CI; unknown fields rejected?
8. Template library unit tested; breaking changes versioned by path; refactor PRs show an empty diff in generated output when generated config is checked in?
9. Untrusted evaluation in a resource-limited subprocess?
10. Rollback means re-applying an earlier generated artifact, not re-evaluating against today's world.

Warning signs: count, loop or conditional keys in data schemas; string values containing mini-languages; YAML plus text templates; config evaluation that calls APIs; arrays of named objects; top-level grouping by type; app code interpreting placeholders; silently ignored unknown keys; many near-identical files diverging subtly.
