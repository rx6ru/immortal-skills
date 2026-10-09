# Fitness functions

How to turn an architecture decision or characteristic into a check that runs without anyone
remembering to run it. Sources: Hard Parts ch. 1, ch. 2, ch. 3, ch. 15; Fundamentals ch. 1;
Communication Patterns ch. 12. Tool mappings beyond the three the sources name are adaptations and
are marked.

## Contents

1. Definition
2. Why automate governance
3. Classification
4. Fitness function or ordinary test
5. Procedure: from ADR to check
6. Catalogue
7. Wiring into CI and monitoring
8. Limits and cautions
9. Verify

## 1. Definition

Any mechanism that performs an objective integrity assessment of some architecture characteristic or
combination of characteristics (Hard Parts ch. 1, taken from the evolutionary architecture
literature; Fundamentals ch. 1 gives the same definition).

- **Any mechanism.** Structural test libraries, metrics, unit-style tests, monitors for performance
  and scalability, chaos experiments for resilience, code hygiene scanners.
- **Objective.** A measurable value or a true/false result. "High performance" cannot be asserted.
  If a characteristic cannot be measured, its definition is too vague or it is composite and has to
  be decomposed (agility into deployability, testability, cycle time).
- **Some characteristic or combination.** See atomic and holistic below.

The term comes from evolutionary computing, where a fitness function scores how close a candidate is
to the goal.

## 2. Why automate governance

- Documenting a decision does not govern it (Hard Parts ch. 1). Ensuring compliance is a standing
  duty: a developer who bypasses the layers to reach the database for speed undoes the reason the
  layers were closed (Fundamentals ch. 1).
- Fitness functions are an executable checklist for things that are important but not urgent. They
  hold under schedule pressure, when "we will fix it later" otherwise wins.
- Code review is too late for structural rules. With editor auto-imports, the damage from an
  unwanted dependency is done within days.
- The more often a fitness function runs, the faster the feedback.

## 3. Classification

| Axis | Kinds | Example |
|---|---|---|
| Scope | **Atomic**: one characteristic in isolation. **Holistic**: a combination of interacting characteristics | Atomic: cycle detection. Holistic: security together with performance; scalability together with elasticity |
| Result | **Static**: fixed true/false or numeric threshold. **Dynamic**: the acceptable result depends on context | Dynamic: per-user response time may degrade gently as concurrent users rise, but must not fall off a cliff |
| Execution | **Automated**: in the build or pipeline (most). **Manual**: a human step, run as a manual pipeline stage | Manual: legal review of legally sensitive code |
| Cadence | Triggered by change (build-time) or continuous (monitor) | Dynamic coupling needs continuous checks, typically monitors (Hard Parts ch. 2) |

A validation that does not run cannot validate anything: prefer continuous execution over on-demand.

## 4. Fitness function or ordinary test

Ask: is domain knowledge required to execute this test?

- Yes: it is a unit, functional or acceptance test. Example: validating a mailing address.
- No: it is a fitness function. Example: elasticity under a burst of load, or absence of package
  cycles.

The line is not strictly binary. The practical use of the question is to decide where a check lives
and who owns it: fitness functions belong with the architecture rules and usually apply across the
codebase.

## 5. Procedure: from ADR to check

1. Take one rule or consequence from the ADR's decision or consequences.
2. State the observable fact that would show the rule broken ("a module under `ui/` imports a module
   under `db/`"; "p95 page load above the budget"; "a dependency with a known critical advisory is
   present").
3. Classify it using section 3. That tells you where it runs: build, pipeline stage, scheduled job
   or production monitor.
4. Pick the mechanism from the catalogue. Prefer an existing tool already in the repository over a
   new dependency; a twenty-line script that parses imports is acceptable when no tool fits.
5. Set the pass condition as a number or boolean. For an existing codebase that already violates the
   rule, record the current violations as a baseline and fail only on new ones, then reduce the
   baseline (adaptation; the sources do not discuss baselining).
6. Put the ADR identifier in the test name or failure message.
7. Wire it into the pipeline so it runs on every change.
8. Prove it: break the rule deliberately once and confirm the check fails.

## 6. Catalogue

Uniform entry: governs; mechanism; implement; notes.

### 6.1 No dependency cycles between components

- **Governs:** maintainability, modularity. Cyclic components cannot be reused or extracted one
  without the others, and the end state is a big ball of mud.
- **Mechanism (source):** analyse package dependencies and assert that no cycles exist, as a test in
  the build (Hard Parts ch. 1, using JDepend).
- **Implement (adaptation):** Java/Kotlin: ArchUnit slice rules. .NET: NetArchTest or an analyser.
  TypeScript/JavaScript: `madge --circular` or a dependency-cruiser `no-circular` rule. Python:
  import-linter contracts, or a small script over the import graph. Go: the compiler already
  rejects import cycles between packages, so check at the level of higher groupings if needed.
  Rust: cycles between crates are rejected by Cargo; module-level cycles inside a crate need a
  custom check.
- **Notes:** atomic, static, automated. Cheapest check with the highest return on a growing codebase.

### 6.2 Layer and module access rules

- **Governs:** the decision that layers are closed, or that one module may not reach another; keeps
  change in the database from reaching the presentation layer.
- **Mechanism (source):** declare layers by package pattern and assert access: controllers may not
  be accessed by any layer, services only by controllers, persistence only by services (Hard Parts
  ch. 1, ArchUnit). The .NET equivalent asserts that types in the presentation namespace have no
  dependency on the data namespace (NetArchTest).
- **Implement (adaptation):** sketch in Python with only the standard library, for a repository with
  no architecture-test tool:

  ```python
  # test_layers.py  (guards ADR-0004: UI may not import persistence)
  import ast, pathlib

  FORBIDDEN = {"app/ui": ("app.persistence",)}

  def imports(path):
      tree = ast.parse(path.read_text())
      for node in ast.walk(tree):
          if isinstance(node, ast.Import):
              yield from (a.name for a in node.names)
          elif isinstance(node, ast.ImportFrom) and node.module and not node.level:
              # "from app import persistence" imports app.persistence too
              yield node.module
              yield from (f"{node.module}.{a.name}" for a in node.names)

  def banned_by(module, banned):
      return any(module == b or module.startswith(b + ".") for b in banned)

  def test_ui_does_not_import_persistence():
      bad = [(str(p), m)
             for root, banned in FORBIDDEN.items()
             for p in pathlib.Path(root).rglob("*.py")
             for m in imports(p) if banned_by(m, banned)]
      assert not bad, f"ADR-0004 violated: {bad}"
  ```

  Limits of the sketch: it ignores relative imports (`from . import x`) and dynamic imports, and
  `FORBIDDEN` paths are relative to the directory the test runs from. Run from the repository root.
  Tool equivalents: import-linter layers contract (Python), dependency-cruiser forbidden rules or
  lint import-restriction rules (TypeScript), depguard-style linters or internal packages (Go),
  crate boundaries and visibility (Rust), ArchUnit (JVM), NetArchTest (.NET).
- **Notes:** atomic, static, automated. Pair each rule with the ADR that explains why the layer is
  closed, and with a variance path for exceptions.

### 6.3 Vulnerable or banned dependency gate

- **Governs:** security across every team; enterprise-wide governance.
- **Mechanism (source):** the security team owns a slot in every team's deployment pipeline. When a
  zero-day is announced, it inserts a test that fails the build if the vulnerable library version is
  present and notifies security. The motivating case is a breach in which a published patch was not
  applied to all systems, scans missed the unpatched ones, and the breach was found months later
  (Hard Parts ch. 1).
- **Implement (adaptation):** a pipeline stage running the ecosystem's advisory scanner
  (`npm audit`, `pip-audit`, `cargo audit`, `govulncheck`, or a cross-ecosystem scanner) with a
  fail threshold; plus a deny-list file the security owner can edit without touching each
  repository's pipeline.
- **Notes:** the general lesson is that pipelines should wake on any change: code, database schema,
  deployment configuration, and the fitness functions themselves.

### 6.4 Page or endpoint response-time budget

- **Governs:** performance.
- **Mechanism (source):** a test of page load time for each page, run in continuous integration
  (Fundamentals ch. 1).
- **Implement (adaptation):** a browser-automation or HTTP timing test against a deployed preview
  with a budget per route; fail on regression beyond the budget. Use a percentile over several runs,
  not a single sample, to keep the check from flaking.
- **Notes:** atomic, static. Needs a stable environment to be meaningful.

### 6.5 Elasticity under burst and graceful degradation

- **Governs:** elasticity, scalability.
- **Mechanism (source):** a load test that applies a burst and checks responsiveness; needs no domain
  knowledge, which is what marks it as a fitness function. As a dynamic function, the allowed
  response time rises with concurrent users but must not collapse (Hard Parts ch. 1). Mean time to
  startup is the underlying property for elasticity (Hard Parts ch. 3).
- **Implement (adaptation):** scheduled load test with stepped and spiked profiles; assertion on the
  shape of the latency curve (bounded slope) and on error rate; a separate measurement of container
  or process start-to-ready time with a ceiling.
- **Notes:** often holistic, since scalability and elasticity interact. Runs on a schedule or before
  release, not on every commit.

### 6.6 Resilience experiments

- **Governs:** fault tolerance, availability.
- **Mechanism (source):** chaos engineering is listed among fitness-function mechanisms (Hard Parts
  ch. 1; Fundamentals ch. 1). The property to demonstrate is that parts of the system stay
  responsive when another part fails, which holds only where the dependency is asynchronous (Hard
  Parts ch. 3).
- **Implement (adaptation):** in a test environment, stop or delay one dependency and assert that
  named workflows still complete or degrade as specified.
- **Notes:** holistic, usually scheduled.

### 6.7 Static coupling inventory

- **Governs:** independence of deployable units; blast radius of change.
- **Mechanism (source):** derive each service's static coupling from container manifests and
  dependency files during the build and publish it; the case study's platform team did this to
  answer "what must be tested if this changes" (Hard Parts ch. 2, ch. 15).
- **Implement (adaptation):** a build step that emits, per deployable, its runtime, libraries, data
  stores and brokers into a machine-readable file; a check that fails when two deployables declared
  independent share a data store, or when a new shared dependency appears without an ADR reference.
- **Notes:** atomic, static.

### 6.8 Dynamic coupling monitor

- **Governs:** communication dependencies between quanta; the decision that a given path is
  asynchronous, or that a service is not called synchronously by more than an agreed set.
- **Mechanism (source):** fitness functions for dynamic coupling have to be continuous, typically
  monitors; a call graph built from observability logs (Hard Parts ch. 2).
- **Implement (adaptation):** derive service-to-service edges from traces; alert when a synchronous
  edge appears that is not on the allowed list; monitor queue depth per consumer where independent
  operational profiles were the reason for a decision.
- **Notes:** continuous, automated.

### 6.9 Accidental coupling through repository proximity

- **Governs:** independence of projects that share a repository.
- **Mechanism (source):** when agreeing to trial a single repository for several projects, the trial
  was accompanied by metrics and fitness functions to stop projects becoming coupled just because
  their code sits side by side (Hard Parts ch. 15).
- **Implement (adaptation):** import rules between top-level project directories (as in 6.2), plus
  workspace or build-graph visibility rules where the build tool supports them.
- **Notes:** an example of using a fitness function to make a contested option safe to try.

### 6.10 Modularity metrics with thresholds

- **Governs:** maintainability, testability, deployability.
- **Mechanism (source):** the practical metrics named for maintainability are component coupling,
  component cohesion, cyclomatic complexity, component size in statements, and technical versus
  domain partitioning; testability is judged by the test scope of a change; deployability by ease,
  frequency and risk (Hard Parts ch. 3). Code hygiene scanners are listed as a mechanism (Hard Parts
  ch. 1).
- **Implement (adaptation):** complexity and size thresholds through the language's linter or a
  quality scanner; incoming-dependency counts per component from the import graph; test-suite
  duration and number of services a typical change touches tracked as trend metrics.
- **Notes:** thresholds are local choices; the sources give none. Start from the current values and
  ratchet.

### 6.11 Decomposition pattern checks

Component size, component namespace ownership, shared-component and dependency checks used during a
monolith migration each come with their own fitness functions. Those are catalogued in
`arch-decomposition`.

### 6.12 Documentation coverage and health

- **Governs:** the reliability of generated documentation and of the decision records themselves.
- **Mechanism (source):** documentation generators that depend on annotations silently omit
  un-annotated code; guard with review checks or automated fitness functions. Broken-link and
  readability checks are worth running in most projects alongside code tests (Communication
  Patterns ch. 12).
- **Implement (adaptation):** a link checker over `docs/` including `docs/adr/`; a check that every
  public endpoint or exported module appears in the generated reference; a check that ADR files
  have the required headings and an allowed status value.
- **Notes:** generated documentation never explains why; it complements ADRs and does not replace
  them.

### 6.13 Manual stage

- **Governs:** anything that needs human judgement, such as legal review.
- **Mechanism (source):** run it as a manual stage in the pipeline so it is still part of the flow
  and cannot be skipped unnoticed (Hard Parts ch. 1).
- **Implement (adaptation):** a required approval on changes to named paths, through the pipeline's
  manual-approval step or a code-owners rule.

## 7. Wiring into CI and monitoring

| Kind of check | Where it runs | Failure means |
|---|---|---|
| Structural (6.1, 6.2, 6.9, parts of 6.10, 6.12) | Unit-test stage on every push | Build fails |
| Dependency gate (6.3) | Pipeline stage on every push and on a schedule, since advisories appear without code changes | Build fails, owner notified |
| Performance budget (6.4) | After deploy to a preview or test environment | Pipeline fails or warns |
| Load, elasticity, resilience (6.5, 6.6) | Scheduled or pre-release | Release blocked or issue raised |
| Coupling inventory (6.7) | Build step | Build fails on undeclared shared dependency |
| Dynamic coupling (6.8) | Production or staging monitoring | Alert |
| Manual (6.13) | Approval stage | Pipeline waits |

Practices:

- Keep structural fitness functions in the ordinary test suite so developers run them locally.
- Name tests after the rule and the ADR (`test_adr_0004_ui_does_not_import_persistence`).
- Treat changes to fitness functions as changes that trigger the pipeline.
- Record in each ADR which check guards it; record in each check which ADR it guards.

## 8. Limits and cautions

- Do not overuse. A small group designing many interlocking functions that frustrate teams is a
  failure mode the source warns about (Hard Parts ch. 1). Add a function for a rule that matters and
  is at risk.
- A check with a vague or subjective pass condition is not a fitness function; fix the definition
  first.
- Performance and load checks need a controlled environment; without one, they flake, and a flaky
  gate gets disabled.
- A fitness function governs what it measures. Passing structural checks says nothing about whether
  the decision was the right one; that is what the ADR's revisit trigger is for.
- Tools named in the sources date from roughly 2020 to 2022. Check that a tool is maintained before
  adding it; a small custom check is a reasonable fallback.
- A side benefit noted in the source: writing these keeps architects in the code.

## 9. Verify

- For each rule in each ADR touched by the task: a check exists, or a written reason why not. Present
  this as a rule-to-check table.
- The check has been seen to fail on a deliberate violation and pass after reverting. Include the
  failing output in the report.
- The check is invoked by the pipeline configuration on every change (show the line), or by a
  schedule or monitor where that is the right cadence.
- The pass condition is numeric or boolean.
- The failure message names the ADR.
- The check needs no domain knowledge to run. If it does, it belongs in the functional test suite.
- No check was weakened to make the build pass: thresholds and baselines only move in the stricter
  direction without a superseding ADR.
