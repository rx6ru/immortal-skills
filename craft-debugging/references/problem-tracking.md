# Problem tracking: reports, classification, linking to fixes

Source: WPF ch. 2 (tracking problems). The tools named there (BugZilla, Trac, CVS) are dated; the capabilities are any issue tracker plus git tags, branches and commit-to-issue links. Read this when you write or triage a problem report, set priorities, or decide how a fix reaches users. For what a report should contain to be reproducible, see `reproduce.md` section 2.

## Contents
1. The life of a user problem
2. Classification: severity and priority
3. States and resolutions
4. Duplicates and obsolete reports
5. Linking problems, versions, fixes and tests
6. Decision rules
7. Verify

## 1. The life of a user problem

User informs the vendor; the vendor reproduces it; isolates the circumstances; locates and fixes the defect; delivers the fix. Solving a user's problem is more than debugging: first establish whether anything can be done (it may be a misunderstanding, or caused by an external component), and at the end the fix must be deployed, not just committed. A tracker must answer: what is open, what is most severe, did similar problems occur before (a fix may exist and only need delivering), and what is the status.

Keep tracking simple; if it gets in the way, people stop using it. A single list file is easy but does not scale (one editor at a time, no history unless versioned). A tracker scales but is meant for developers: distil and classify end-user input before entering it. A tracker nobody files into is useless; one where nobody marks resolutions fills with stale data.

## 2. Classification: severity and priority

Severity is the impact on development or release: blocker, critical (crash, data loss, severe leak), major (major loss of function), normal, minor (minor loss or an easy workaround), trivial (cosmetic), enhancement (a desired feature, not a failure). An unmet requirement is a major problem, not an enhancement.

Priority is how soon it is addressed, set by management, and depends on severity together with likelihood, number of users affected and potential damage. Priority need not follow severity: a blocker in an alpha can rank below a major problem in a widely deployed product. Weigh all of these together, not severity alone; the book gives no formula.

Other fields: a unique identifier (used in commits, change logs, status reports), comments (circumstances, speculation, first findings), notification to subscribers on every change. Requirements can be tracked as problems with hierarchical decomposition (fixed when all sub-problems are).

## 3. States and resolutions

Model (adapt to your process): UNCONFIRMED (nobody has tried to reproduce), NEW (valid, not an obvious duplicate), ASSIGNED, RESOLVED with a resolution, VERIFIED (fix confirmed by independent review or test), CLOSED (a release containing the fix has shipped), REOPENED (recurred or new information; must be assigned again).

Resolutions: FIXED, INVALID (not a problem, or lacking the relevant facts), DUPLICATE, WONTFIX (includes "it's a feature"), WORKSFORME (all reproduction attempts failed; may be reopened).

Cannot reproduce: document every attempt in the report, resolve as WORKSFORME, and ask a specific question about a configuration difference that could explain it. Do not close silently. Adaptation rules: skip VERIFIED without independent verification; if fixes are applied at the user's site, RESOLVED and CLOSED coincide.

## 4. Duplicates and obsolete reports

Many users hitting one defect write differently worded reports. A report should contain as many facts as possible (any may matter for reproduction), yet spotting duplicates needs as few as possible. The resolution is simplification: reduce each report to the relevant facts (`simplify-and-isolate.md`). A simplified report both reproduces and reveals similarity. Mark duplicates; when the original is fixed close the duplicates that share the cause.

Unresolved reports accumulate. Periodically mark as obsolete those that will never be fixed (unsupported product) or are old and occurred only once or only internally. Obsolete reports remain searchable and can be revived.

## 5. Linking problems, versions, fixes and tests

- Report the exact version and be able to recreate that configuration: every source file and every tool version. Use version control, not manual copies.
- Tag the source at every release shipped. Put fixes (and only fixes) for stable releases on a maintenance branch; risky new features go on the trunk; merge fixes back so the next release has them.
- Link both ways: the tracker records the change that fixed the problem; the commit message records the problem identifier.
- Keep test outcomes out of the tracker unless the two are integrated: outcomes are far more frequent than user reports and, with automated tests, can be recomputed for any version on demand. Rule: test cases make problem reports obsolete. A problem found in development becomes a failing test; use the tracker for ideas and feature requests that cannot yet be a test.

## 6. Decision rules

- Vague report: ask for steps and input files, then logs or stack trace, then observed behaviour, then expected behaviour, then version, then environment.
- Found a problem while developing: write a failing test.
- Writing a report for someone else (an upstream library): simplify the trigger to the minimum, generalise (other versions, environments?), neutral tone, one-line summary naming component, symptom and trigger.
- Fix must reach a released version: branch from the release tag, commit only the fix, reference the problem identifier, merge back to trunk.
- Only a workaround exists: leave the problem open.

## 7. Verify

- A second person can reproduce the problem from the report without asking anything.
- Every fix commit names its problem identifier, and every resolved problem names its fixing change.
- A released version can be rebuilt from its tag (check it out and build).
- FIXED is not the end: the original reproduction was rerun, and the fix was delivered.
