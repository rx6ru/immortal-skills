# Saga state machines and error handling

Read this when you are implementing or reviewing how a saga recovers from failure: designing the
state machine, deciding between compensating updates and retry-with-state, writing the tests, or
making saga membership visible to the team.

Contents: two ways to handle errors; why compensation is weaker than it looks; state management
with a finite state machine; the worked state table; implementation sketch; making sagas
discoverable; verification.

## Two ways to handle errors (Hard Parts ch. 12)

### A. Compensating updates (atomic distributed transactions, as in Epic)

Walkthrough (ticket completion): the expert marks a ticket complete; the Ticket Orchestrator makes a
synchronous call to Ticket Service (commit status complete); Ticket Service asynchronously queues
analytics data for the Analytics service and acknowledges; the orchestrator synchronously calls
Survey Service (inserts a survey row, emails the customer); the orchestrator replies to the expert.

Problems when the survey step fails and the orchestrator tries to undo:

1. No isolation, so side effects escape. If the orchestrator compensates Ticket Service back to
   "in progress", Analytics has already consumed the data. Undoing that needs another message and
   more logic, and further downstream actions may exist ("turtles all the way down").
2. Compensation can fail. The ticket may stay "complete", the expert retries and is told "already
   complete", and nobody knows why. The assumption that compensations always work is false.
   Developer confusion is a sign the architecture is incomplete.
3. The user waits for all corrective actions before seeing the error. Compensating asynchronously
   (Parallel, Anthology) helps.
4. A service cannot roll back. Locking participants between calls destroys performance and scale;
   not locking lets other requests interleave, worse with asynchrony. The real world is mostly
   non-transactional, and the broader the transaction scope, the worse it gets.
5. The end user is needlessly coupled to a business process they should not care about.

| Advantages | Disadvantages |
|---|---|
| All data restored to its prior state | No transaction isolation |
| Allows retries and restart | Side effects may occur on compensation |
| | Compensation may fail |
| | Poor responsiveness for the end user |

### B. State management plus eventual consistency (Fairy Tale and Parallel style)

Use a finite state machine so the saga's state is always known, then fix errors by retry or by
automated or manual repair. Example: Survey Service is unavailable; the saga moves to NO_SURVEY, the
expert gets a success response, the orchestrator retries behind the scenes and, if still failing,
escalates to an administrator. The user is unaffected.

| Advantages | Disadvantages |
|---|---|
| Good responsiveness | Data may be out of step when errors occur |
| Less impact to the end user on errors | Eventual consistency may take some time |

Whichever you choose, the state of the distributed transaction must be known and managed. The
choice is responsiveness versus consistency.

Rule of thumb that follows: prefer B when the failed step is not something the user needs to act on
(survey, notification, analytics); reserve A for steps that truly must be undone, and then design
the undo as a first-class, tested feature with its own failure handling.

## The state machine

A saga's state machine lists all possible paths: a START state, transition states each with an
action, and an end state (CLOSED). Table for the new-problem-ticket saga:

| Initiating state | Transition state | Transaction action |
|---|---|---|
| START | CREATED | Assign ticket to expert |
| CREATED | ASSIGNED | Route ticket to assigned expert |
| ASSIGNED | ACCEPTED | Expert fixes problem |
| ACCEPTED | COMPLETED | Send customer survey |
| ACCEPTED | REASSIGN | Reassign to a different expert |
| REASSIGN | ASSIGNED | Route ticket to assigned expert |
| COMPLETED | CLOSED | Ticket saga done |
| COMPLETED | NO_SURVEY | Send customer survey |
| NO_SURVEY | CLOSED | Ticket saga done |

Semantics:

- START validates the plan and ticket and inserts the ticket, then moves to CREATED. Errors at this
  point prevent the saga from starting.
- CREATED waits until an expert is available. ASSIGNED stays until the ticket is routed and
  acknowledged.
- ACCEPTED can go to COMPLETED or REASSIGN (wrong assignment, or the expert cannot finish). REASSIGN
  loops back to ASSIGNED.
- COMPLETED goes to CLOSED once the survey is sent, or to NO_SURVEY (an error state retried until
  the survey is sent), then to CLOSED.

Practice: tabulate all states, transitions and actions, then implement them as triggers and error
handling in the orchestrator (or in the services, if choreographed).

## Implementation sketch (adaptation, not from the notes)

Persist the saga's current state and the ids of the events already applied with the workflow
identifier, in the same transaction as the local change that caused the transition, so a crash
cannot leave state and effect disagreeing. The sketch runs as written under Python 3 (the
persistence is represented by plain attributes).

```python
class IllegalTransition(Exception):
    pass

TRANSITIONS = {
  ("START", "ticket_saved"): "CREATED",
  ("CREATED", "expert_found"): "ASSIGNED",
  ("ASSIGNED", "accepted"): "ACCEPTED",
  ("ACCEPTED", "fixed"): "COMPLETED",
  ("ACCEPTED", "declined"): "REASSIGN",
  ("REASSIGN", "expert_found"): "ASSIGNED",
  ("COMPLETED", "survey_sent"): "CLOSED",
  ("COMPLETED", "survey_failed"): "NO_SURVEY",
  ("NO_SURVEY", "survey_sent"): "CLOSED",
}

class Saga:
    def __init__(self):
        self.state = "START"
        self.seen = set()              # ids of events already applied

def step(saga, event_id, event):
    if event_id in saga.seen:
        return saga.state              # duplicate delivery: no-op
    nxt = TRANSITIONS.get((saga.state, event))
    if nxt is None:
        raise IllegalTransition(saga.state, event)   # never silently ignore
    saga.state = nxt                   # persist state and event_id atomically with the effect
    saga.seen.add(event_id)
    return saga.state
```

Design notes: an event arriving twice must be a no-op (idempotence, see
`end-to-end-correctness.md`), which is why the sketch records event ids; error states such as NO_SURVEY need a retry policy and a maximum
duration after which they alert a person; do not let any state lack an exit.

## Making sagas discoverable

Sagas cannot be bought like an ACID transaction manager; they have to be designed, coded and
maintained, so make them visible.

- Annotation technique from the notes: define a single `Saga` marker (a Java annotation or C#
  attribute) carrying an enum of saga names (NEW_TICKET, CANCEL_TICKET, NEW_CUSTOMER, UNSUBSCRIBE,
  NEW_SUPPORT_CONTRACT). Tag each service entry-point class with the sagas it takes part in (for
  example the survey API in NEW_TICKET, the ticket API in NEW_TICKET and CANCEL_TICKET).
- A small code-walking command (for example `sagatool.sh NEW_TICKET -services`) lists membership
  in real time for developers, architects and analysts, supporting test scoping and impact
  analysis.
- Language-neutral version: any marker or metadata mechanism (a decorator, a manifest field, a
  registry file) plus a scanner that fails CI when a service calls into a saga it has not declared.

## Verify

- State machine completeness: every state defines transitions for success, failure and timeout;
  there are no dead states; every error state has a retry policy, an escalation path and a
  maximum-duration alarm.
- Write tests that drive each row of the transition table, plus illegal events (must be rejected
  and logged), duplicate events (must be no-ops) and out-of-order events.
- Test compensation failure and downstream side effects explicitly (the analytics example).
- Test that an operator can list all sagas stuck in an error state and their age.
- Saga registry check: the set of services found by scanning annotations equals the set in the
  architecture document.
