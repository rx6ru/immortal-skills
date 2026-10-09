# Pragmatic Programmer tips index

Contents: 1 How to use; 2 Tips 1 to 22; 3 Tips 23 to 46; 4 Tips 47 to 70; 5 Checklists; 6 Planning decisions by tip

Source: The Pragmatic Programmer, 1st edition (Hunt and Thomas, 1999), tip and checklist card (appX), with section detail from ch. 1, 2, 7, 8. Numbering follows the card. Page numbers are omitted. The 1999 edition is dated in tooling; the tips are principles.

Where a tip belongs mainly to another skill, the line names it. Tips marked (here) are covered in this skill's references; tips marked (card only) were read from the card's one-line gloss without chapter detail, so apply them as stated and do not add detail from memory.

## 1. How to use

- Looking for a rule you remember by number: scan the lists below.
- Planning decisions: section 6 maps a situation to the tips and reference files.
- For tips outside planning, follow the sibling pointers: `craft-module-design` (DRY, orthogonality, decoupling, metadata), `craft-error-handling` (contracts, assertions, exceptions, resources), `craft-debugging` (debugging tips), `craft-refactoring`, `craft-testing`, `craft-concurrency`, `craft-technical-communication`.

## 2. Tips 1 to 22

1. Care About Your Craft: why spend your life on software unless you care about doing it well. (card only)
2. Think! About Your Work: turn off autopilot; constantly critique and appraise what you do. (card only)
3. Provide Options, Don't Make Lame Excuses: never just "can't be done"; explain what can be done. (here: `milestones-and-status.md`)
4. Don't Live with Broken Windows: fix bad designs, wrong decisions and poor code when you see them; board them up if you cannot. (here: `scope-and-second-system.md`)
5. Be a Catalyst for Change: show people the possible future and let them take part. Ask whether it is stone soup or frog soup. (here, below)
6. Remember the Big Picture: watch what is happening around you; overruns happen a day at a time. (here: `milestones-and-status.md`)
7. Make Quality a Requirements Issue: involve users in deciding the real quality requirements. (here: `requirements-and-specs.md`)
8. Invest Regularly in Your Knowledge Portfolio: make learning a habit. For an agent, check a current source rather than answering from possibly stale memory. (card; adaptation in notes)
9. Critically Analyze What You Read and Hear: do not be swayed by vendors, hype or dogma; rank is not evidence. (here: `tools-and-build-vs-buy.md`)
10. It's Both What You Say and the Way You Say It: great ideas are worthless if not communicated. WISDOM: what do you want them to learn; what is their interest; how sophisticated are they; how much detail do they want; whom do you want to own the information; how can you motivate them to listen. (`craft-technical-communication`)
11. DRY: every piece of knowledge has a single authoritative representation. (`craft-module-design`; also `requirements-and-specs.md` for documents)
12. Make It Easy to Reuse: build an environment where reuse is easier than rewriting. (here: `tools-and-build-vs-buy.md`)
13. Eliminate Effects Between Unrelated Things: orthogonality. (`craft-module-design`; team form in `staffing-and-partitioning.md`)
14. There Are No Final Decisions: write decisions in sand. (here: `delivery-strategy.md` section 10)
15. Use Tracer Bullets to Find the Target. (here: `delivery-strategy.md`)
16. Prototype to Learn. (here: `delivery-strategy.md`)
17. Program Close to the Problem Domain. (here: `requirements-and-specs.md`)
18. Estimate to Avoid Surprises. (here: `estimating.md`)
19. Iterate the Schedule with the Code. (here: `estimating.md`)
20. Keep Knowledge in Plain Text: plain text does not go obsolete, leverages your work, simplifies debugging and testing. (card only)
21. Use the Power of Command Shells. (card only)
22. Use a Single Editor Well. (card only)

Tip 5 detail (ch. 1): when you know what is needed but asking permission for the whole thing causes delay, work out what you can reasonably ask for, build it well, show it, then mention it would be better with X and let people ask. People find it easier to join an ongoing success. The authors' ethical test: is it stone soup or frog soup, serving the others involved or not?

## 3. Tips 23 to 46

23. Always Use Source Code Control: a time machine for your work. (card only; automation context in `done-and-verification.md`)
24. Fix the Problem, Not the Blame. (`craft-debugging`)
25. Don't Panic When Debugging. (`craft-debugging`)
26. "select" Isn't Broken: suspect your application before the OS, compiler or library. (`craft-debugging`)
27. Don't Assume It, Prove It: prove assumptions in the real environment with real data and boundary conditions. (`craft-debugging`)
28. Learn a Text Manipulation Language. (card only)
29. Write Code That Writes Code. (card only; see DRY by generation in `done-and-verification.md`)
30. You Can't Write Perfect Software. (`craft-error-handling`)
31. Design with Contracts. (`craft-error-handling`)
32. Crash Early. (`craft-error-handling`)
33. Use Assertions to Prevent the Impossible. (`craft-error-handling`)
34. Use Exceptions for Exceptional Problems. (`craft-error-handling`)
35. Finish What You Start: the routine that allocates a resource should deallocate it. (`craft-error-handling`)
36. Minimize Coupling Between Modules: write shy code; Law of Demeter. (`craft-module-design`)
37. Configure, Don't Integrate. (`craft-module-design`)
38. Put Abstractions in Code, Details in Metadata. (`craft-module-design`)
39. Analyze Workflow to Improve Concurrency. (`craft-concurrency`)
40. Design Using Services. (`craft-concurrency`, `craft-module-design`)
41. Always Design for Concurrency. (`craft-concurrency`)
42. Separate Views from Models. (`craft-module-design`)
43. Use Blackboards to Coordinate Workflow. (`craft-concurrency`)
44. Don't Program by Coincidence: rely only on reliable things; a happy coincidence is not a plan. (`craft-debugging`, `craft-clean-code`)
45. Estimate the Order of Your Algorithms. (card only; performance in `craft-module-design`)
46. Test Your Estimates: math is not everything; time the code in its target environment. (card only; relates to `estimating.md`)

## 4. Tips 47 to 70

47. Refactor Early, Refactor Often. (`craft-refactoring`)
48. Design to Test. (`craft-testing`)
49. Test Your Software, or Your Users Will. (`craft-testing`)
50. Don't Use Wizard Code You Don't Understand: understand all generated code before adopting. (card; adaptation to generated code in `tools-and-build-vs-buy.md`)
51. Don't Gather Requirements, Dig for Them. (here: `requirements-and-specs.md`)
52. Work with a User to Think Like a User. (here)
53. Abstractions Live Longer than Details. (here)
54. Use a Project Glossary. (here)
55. Don't Think Outside the Box, Find the Box. (here)
56. Start When You're Ready: heed niggling doubts; prototype to test whether it is procrastination. (here)
57. Some Things Are Better Done than Described: avoid the specification spiral. (here)
58. Don't Be a Slave to Formal Methods. (here: `tools-and-build-vs-buy.md`)
59. Costly Tools Don't Produce Better Designs. (here: `tools-and-build-vs-buy.md`)
60. Organize Teams Around Functionality. (here: `staffing-and-partitioning.md`)
61. Don't Use Manual Procedures. (here: `done-and-verification.md`)
62. Test Early. Test Often. Test Automatically. (here: `done-and-verification.md`; depth in `craft-testing`)
63. Coding Ain't Done 'Til All the Tests Run. (here)
64. Use Saboteurs to Test Your Testing. (here)
65. Test State Coverage, Not Code Coverage. (here)
66. Find Bugs Once. (here)
67. English Is Just a Programming Language. (here)
68. Build Documentation In, Don't Bolt It On. (here)
69. Gently Exceed Your Users' Expectations. (here: `requirements-and-specs.md`)
70. Sign Your Work. (here: `milestones-and-status.md`)

## 5. Checklists on the card

- Languages to learn (dated list; principle: learn languages of different paradigms and try a small home project).
- WISDOM acrostic (Tip 10; section 2).
- How to maintain orthogonality: design independent, well-defined components; keep code decoupled; avoid global data; refactor similar functions.
- Things to prototype: architecture; new functionality in an existing system; structure or contents of external data; third-party tools or components; performance issues; user interface design.
- Architectural questions: are responsibilities well defined; are collaborations well defined; is coupling minimised; can you identify potential duplication; are interface definitions and constraints acceptable; can modules access needed data when needed.
- Debugging checklist: is the reported problem a direct result of the underlying bug or a symptom; is the bug in the compiler or OS, or in your code; if you explained it in detail to a coworker, what would you say; if the suspect code passes its unit tests, are the tests complete enough; do the conditions that caused this bug exist anywhere else in the system. (`craft-debugging`)
- Law of Demeter for functions: a method should call only methods of itself, parameters passed in, objects it creates, and component objects. (`craft-module-design`)
- How to program deliberately: stay aware of what you are doing; do not code blindfolded; proceed from a plan; rely only on reliable things; document assumptions; test assumptions as well as code; prioritise effort; do not be a slave to history.
- When to refactor: you find a DRY violation; things could be more orthogonal; your knowledge improves; requirements evolve; you need to improve performance.
- Cutting the Gordian knot: is there an easier way; am I solving the right problem; why is this a problem; what makes it hard; do I have to do it this way; does it have to be done at all.
- Aspects of testing: unit; integration; validation and verification; resource exhaustion, errors and recovery; performance; usability; testing the tests.

## 6. Planning decisions by tip

| Situation | Tips | File |
|---|---|---|
| Asked for an estimate | 18, 19, 46 | `estimating.md` |
| Unknown target, new kind of system | 15, 16, 56 | `delivery-strategy.md` |
| Unclear request | 51, 52, 53, 54, 55 | `requirements-and-specs.md` |
| Spec growing without code | 57, 58, 59 | `requirements-and-specs.md`, `tools-and-build-vs-buy.md` |
| Splitting work among people or agents | 13, 60 | `staffing-and-partitioning.md`, `orchestrating-subagents.md` |
| Reporting trouble or slippage | 3, 6, 69, 70 | `milestones-and-status.md` |
| Scope or quality bar | 4, 7, 69 | `scope-and-second-system.md` |
| Before saying done | 61 to 68 | `done-and-verification.md` |
| Reversible versus fixed decisions | 14, 37, 38 | `delivery-strategy.md` section 10 |
