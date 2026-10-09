# Messages and status

How to write PR descriptions, commit messages, final reports, status updates, emails, chat messages and async requests, and when to use a live conversation instead. Sources: Communication Patterns (Read 2023) ch. 7, 8, 11, 13, 14, 15; Pragmatic Programmer ch. 1 and 8; Mythical Man-Month ch. 10. Items marked (inferred) are readings added in the notes; "Agent" lines and the templates are adaptation.

## Contents

1. Principles
2. Message anatomy
3. Symmetrical Email and its use in PRs and chat
4. Time, deadlines and time zones
5. Async or sync
6. Setting and handling expectations: Who, What, When, Wah-wah, Why
7. Status updates and final reports
8. PR descriptions and commit messages (adaptation)
9. Meetings, presentations and screen shares
10. Respecting working patterns and energy
11. Templates
12. Checks

## 1. Principles

- Success is shared understanding judged at the receiver. If the reader has to ask what you want, the message failed.
- Put the point, the ask and the deadline first (structured writing, ch. 7).
- Message the right people only, one topic at a time, with a link rather than a copy.
- Channel follows purpose, direction, urgency and the need to find it later. Tool names date; these four do not.
- Always respond, even if only "I will get back to you later", and then do. (Pragmatic Programmer ch. 1) Never go silent on a long task; report back status.
- Email checklist (Pragmatic Programmer ch. 1): proofread, keep formatting simple, minimise quoting and attribute what you quote, do not flame, check the recipient list, keep a record. Messages are permanent and can be evidence. The checklist carries over to chat, PRs and commit messages.

## 2. Message anatomy

1. Tag and ask in the first line: `FYI`, `Action needed by <time, zone, date>`, `Decision needed`.
2. The point or conclusion in one or two sentences.
3. Per-person asks if several people are addressed.
4. Reasons and evidence, most important first.
5. Links to everything referenced.
6. What happens if no reply (default action).
7. Time cost of what you ask ("about 15 minutes to review").

Writing quality: you and I rather than robotic passive ("Can you please give me feedback on the context diagram by 4 p.m. IST?" rather than "Feedback is requested"); write as you speak and read aloud before sending; assume good intent when reading; no idioms, sarcasm or unexplained acronyms for international readers (ch. 7). Text loses tone and body language and is easy to misread; emojis are interpreted differently, so a team may keep a small emoji dictionary (ch. 14).

## 3. Symmetrical Email (pattern, ch. 15)

- Problem: people handle email differently; it is unclear when email beats another channel; messages lack expectations and clarity.
- Solution: structure around reasons, expectations and clarity, and write them into a communication agreement for the team or company (it can be shared with partners or become an SLA).
- Reasons: list the typical kinds of communication in the team, decide sync or async for each, then pick the channel.
- Expectations go in the subject line: urgency and the response required. Examples from the notes: `[URGENT, response required by 1 p.m. CET today, 24th July] Request for telemetry data`; `[FYI] Minor update to project budget`; `[Response required - Libby] Architecture meeting update`. Do not overuse URGENT. Review the agreement 2 to 4 weeks after creating it, when problems arise, and every 6 to 12 months. Applies to automated notifications too.
- Clarity: repeat the subject-line specifics (deadline) in the body; with several recipients state each person's expected action rather than relying on To/Cc/Bcc (and this decides who belongs on the email at all); give time costs; consider non-email channels for customers.
- Tips: main point first; one topic per email; hyperlink everything; link to documents rather than attach; default to Reply, not Reply All; enable Undo Send; concise; proofread.
- Agent: use the same structure for PR descriptions, status updates and chat messages.

## 4. Time, deadlines and time zones (ch. 13)

- Synchronize Time. State the time zone every time, even when everyone seems to share one. Prefer the recipient's zone, or both, or one company reference zone (UTC is a good choice, with others as offsets). Use a.m./p.m. with 1 to 12 where the 24-hour clock is uncommon. Dates in ISO 8601 (2023-11-10) or with a month word (10-Nov-2023), because 10-11-2023 reads two ways. Store timestamps with zone, because daylight saving rules change.
- Do not assume availability from your own idea of reasonable hours; check theirs (calendar secondary zones, working hours in signature, chat status). Say you do not expect a reply outside their hours.
- Daylight saving shifts offsets between zones for several weeks a year and the dates differ by region (US and EU switch on different days; some places do not observe it), so recheck meeting times near the switch.
- If you need a fast answer across zones, contact the person early in their day and mark urgency in the subject or first line.
- Schedule-send messages rather than logging in off-hours yourself, which models boundaries. Scheduled alerts can go to a shared mailbox unless urgent.
- Verify: every time or deadline carries a zone and an unambiguous date.

## 5. Async or sync (ch. 14)

Async or sync depends on the expectation, not the tool: rapid back-and-forth in a chat is sync. Remote sync costs more energy than in person, hard to schedule across zones (10 people times 1 hour is 10 hours of work), interrupts, and unrecorded speech is heard once. Async leaves a reference and gives time to think, but the cost of bad async is harder to see than that of a bad meeting.

| Prefer sync to | Prefer async to |
|---|---|
| Build rapport (kickoff, team-building) | Report progress (stand-up, project status) |
| Generate ideas | Gather feedback (a draft ADR or document) |
| Make a final decision | Disseminate information (announcements; sync gives no time to digest) |
| Quick back-and-forth that is ballooning | Answer questions across zones |

- It is not either/or. Use the asynchronous sandwich: async before (brief context, brainstorm, vote to narrow), sync to decide, async after (document and communicate the decision).
- Direction matters. Unidirectional (updates, announcements) works well async. Bidirectional varies: feedback on documents async via comments with access, rights and deadlines that respect working hours; discussions get out of hand async, so gather ideas async and then meet; kickoffs sync with async prework.
- Pure async can let the same loud voices dominate; give everyone time and chase non-contributors before the deadline.
- Switching rule: a team rule such as "if a thread goes back and forth four or more times, switch to a call".
- Reducing meetings: give async access to status (so the uninformed need no meeting), convert stand-ups to written updates and keep sync for bidirectional help, trial no-meeting blocks, shorten necessary meetings on purpose. Content still matters; only the format changes.
- Async channel catalogue (dated names): email for external parties and long text; instant messaging for short items (manage channel proliferation); recorded video or audio for tone; forums and Q&A for knowledge that stays searchable; project tools for status and assignment; wikis for policies and status with comments; surveys with anonymity for quiet voices; whiteboards for collecting ideas and diagram feedback.
- Enhance async: automate access, pre-populate status updates from the previous one, connect tools.

## 6. Setting and handling expectations: Who, What, When, Wah-wah, Why (ch. 14)

The four Ws come from Greene and Sanderson (Remote Works, 2023); "Why" is the book's addition.

- Who: who is included and excluded (never omit the decision authority); who must respond and what exactly you need from each. Do not let the discussion proceed until required responders have responded.
- What: the form of response wanted and the tool or workflow.
- When: date, time and time zone every time. "End of day tomorrow" and "ASAP" mean nothing. The deadline respects recipients' hours. Hold people accountable so it does not stall.
- Wah-wah (what happens on silence): state the consequence of a missed deadline. Example: "If I don't hear back by the date and time above, I will assume no changes are needed and send the document to the client as is."
- Why: the goal; it derives the other four.

Verify: the message names people and the ask per person, the response format, an absolute deadline with zone, the default on silence and the purpose.

## 7. Status updates and final reports

Use these when reporting to the user, a lead agent, a reviewer or a team.

1. Lead with the state: done, blocked, or needs a decision. Newspaper headline length. (Headline statement, ch. 8.)
2. Evidence: what you ran or checked and the result. State what you did not verify. "Sign your work": stand behind it, report as done only when tested and documented, leave an auditable trail (Pragmatic Programmer ch. 8, inferred application).
3. Assumptions with IDs, marked confirmed or unconfirmed, and what changes if each is wrong (ch. 11).
4. Open decisions and the ask, with owner and date; deferred items as "not yet decided; revisit when X".
5. Next steps.

Rules:
- Use real hours or real remaining effort, not wishful figures; the notes advise using genuinely productive hours rather than 8 per day when estimating capacity in hours (ch. 13). Estimation method is in `craft-planning-and-estimation`.
- Say real uncertainty out loud. Avoid hedging words when you are confident ("The plan is ...") and avoid confident phrasing when you are not.
- Status that is stale is worse than none: date it (Pragmatic Programmer: date or version on documents).
- Brooks (ch. 10): the status of a project is read from a few current documents (objectives, specification, schedule, budget, organisation) that are consistent with each other; report against them.
- Meetings exist for bidirectional help; a progress report is async-able, so put progress in the tracker or a written update.

Brooks's reminder applies to work done by many agents or people: the manager's chief daily task is communication; documents lighten it.

## 8. PR descriptions and commit messages (adaptation)

The notes do not contain a PR template; the following applies the pyramid, Symmetrical Email and feedback patterns.

PR description:
1. First line: what changes and why, in one sentence, with the ask: "Review needed by <date, zone>" or "FYI, no action".
2. Motivation and context (the big picture first), including links to the issue or ADR.
3. What changed, summarised by behaviour, not file by file; a diagram only if the structure changed (context or container level, one message).
4. How it was verified: commands run, tests added, what was not tested.
5. Assumptions with IDs, open questions, risks, rollback.
6. Feedback wanted: which parts, and what the author is unsure about.
7. Details last (file-level notes).

Commit message: a short subject saying what changed, a body saying why (the reason is the thing the diff cannot show; comments and messages record why, not how), links instead of pasted copies, no idioms or undefined acronyms.

Verify: the first sentence of the PR makes sense alone; truncation test; the ask and deadline are present; links resolve.

## 9. Meetings, presentations and screen shares

Enhance Meetings (before; ch. 14):
1. State the goal (a stand-up's goals are removing roadblocks, getting help and knowing whether the team is on track, not only reporting progress).
2. Every activity connects to the goal.
3. Agenda with timings and a parking lot for off-goal topics.
4. Expectations and a safe space (cameras, no interruptions, confidentiality).
5. Invite only the right people (someone with authority if a decision is needed; no "just in case" invites; ask others to be on call by message).
6. Brief presenters on their exact time.
7. Plan async before and after (pre-reading marked required or not, access confirmed).
8. Document decisions and actions and send them to attendees and stakeholders.
9. Breaks every 45 to 60 minutes; energy-heavy items early or after a break.

During a remote or hybrid meeting: draw out quiet people with open questions, have someone watch chat, breakout rooms for larger groups, polls and whiteboards, keep to time, and everyone in a hybrid meeting joins as an individual virtual attendee (inferred from the remote-first section).

Online presentations (ch. 15):
- Engagement: say how to ask questions; have a helper watch chat; camera on; use reaction emojis and polls.
- Attention: more slides than in person (slides are free, bigger text and more whitespace), short segments with visual breaks, attention span about 20 minutes at most, breaks every 45 to 60 minutes, maximise discussion and push reading to async.
- Content: an agenda slide is not the same as tell-them-tell-them-tell-them. Open with the challenge or pain point, a bold statement, a statistic or a story; frame the main takeaway and end with it; finish with next steps; follow up async.
- Slideument (antipattern): a deck holding everything the presenter says, so the audience reads rather than listens. Infodeck (pattern): a stand-alone deck built for reading, distributed as PDF or web page.
- Screen shares: present finished work full-screen; share in edit mode to signal openness to change; move the cursor slowly and rest on the target for at least five seconds.

Handling unexpected questions: pause, thank them, repeat the question, ask a clarifying question, answer concisely without defensiveness, and if you do not know promise to find out and follow through. In writing this becomes an FAQ and an "alternatives considered" section. Listening (active listening: do not assume what they will say, summarise back, ask clarifying questions) transfers to reading a user's request carefully and restating it before acting when it is ambiguous.

Body language, gestures and eye contact are for humans in a room; they do not transfer to an agent.

## 10. Respecting working patterns and energy

- Communicate availability; do not assume it. Patterns change with school runs, leave and holidays. Holidays differ by country and region and may be fixed date, fixed day or lunar; keep a shared calendar.
- Work with others' rhythms: the notes say people are most productive late morning and least around 3 p.m.; ask for high-effort responses before someone's productive time. Schedule thinking and decisions early in the day.
- Empathy and compromise for unavoidable sync meetings: rotate inconvenient times, compensate, record the meeting and let non-attendees influence the decision, use async before and after.
- Control notifications and automate routine replies. Keep focus blocks.
- Part-time colleagues: schedule important meetings within their hours or say attendance is not expected, and write up decisions.
- Be explicit across cultures about practices, laws and standards, and how literally to follow designs and prototype code.
- Remote-first versus remote-friendly: remote-first designs processes so remote and local people have the same chance, makes key decisions async and values outcomes over hours.

## 11. Templates

Request for review:

```text
[Action needed by Fri 2026-03-13 16:00 CET] Review of order-retry design (15 min)
Please read docs/adr/0012-order-retry.md and comment on the retry limit (section 3).
Libby: confirm the queue limits in section 4 still hold.  Sander: FYI only.
Why: we start implementation Monday and the retry limit changes the schema.
If I hear nothing by the deadline I will proceed with the limit of 3.
```

Status:

```text
Status: blocked on one decision.
Done: parser rewrite merged; tests pass (214 run, 0 failed); not tested: Windows paths.
Assumptions: A1 inputs are UTF-8 (confirmed); A2 files under 50 MB (unconfirmed, owner: Gino).
Decision needed by Tue 2026-03-10 12:00 UTC: stream or buffer large files. Recommendation: stream.
Next: implement the streaming reader once decided.
```

## 12. Checks

- Tag, ask and deadline in the first line; zone and ISO date present.
- Each recipient has an action or "FYI".
- Time cost stated; default on silence stated; links not attachments.
- One topic; reads correctly if cut after any paragraph.
- Status states what was and was not verified; assumptions numbered.
- Channel matches purpose; thread of four or more exchanges moved to a call.
