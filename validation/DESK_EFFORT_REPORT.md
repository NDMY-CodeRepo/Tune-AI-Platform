# Business Effort Approval — 18 November 2026

Implemented the approval gate in the existing React desk, Python API, shared ticket service and APP_STATE persistence. No financial/AI logic, runtime dependencies, framework, service or separate approval platform was added. Existing pending AI presentation changes were retained.

## Behavior

- NEW → TRIAGED → AWAITING_BU_APPROVAL → APPROVED → IN_PROGRESS → RESOLVED → CLOSED. REJECTED cannot progress into engineering; explicit reassessment returns it to TRIAGED for a new submission. Existing clarification and approved-effort reopening paths remain.
- Data Team submits S/M/L and assessment notes. Server records assessor, timestamp and assessment revision. BU sees a prominent review card and must check the decision confirmation. Rejection requires a reason; approval comments are optional.
- Every decision is bound to `EFFORT_ASSESSMENT_VERSION` and the loaded ticket `VERSION`. The server checks both, the requesting profile, recorded assessment, owner and confirmed priority. Raw status changes cannot create approvals or skip effort submission. Direct API calls are subject to the same rules as the UI.
- Any effort size or notes change creates a new assessment revision, clears previous decision fields, and returns previously assessed work to TRIAGED. This includes changes during engineering. Unchanged values and non-assessment fields preserve approval. Reassessment/resubmission cannot reuse an earlier decision.
- Assessed/revised/submitted, approval-requested, approved/rejected and decision comments are append-only events in the existing activity table. All ticket/assessment/decision changes and their events share the existing transaction and version predicate. Failure to write history rolls back the decision and ticket.

## Migration and compatibility

`sql/desk_effort_approval.sql` adds nine nullable columns; no extra table, status rewrite or historical backfill. The new 20-character AWAITING_BU_APPROVAL value fits the inspected existing STATUS column. Migration ran twice successfully and preserved all 22 preexisting tickets and 112 activity entries exactly. GOLD schema definitions are unchanged. Existing UUIDs and sequence references are retained.

Legacy records have no fabricated assessment/approval. They remain readable; already in-progress legacy work can still receive comments or be resolved. Any future transition into IN_PROGRESS, including resume or reopening, needs a valid approval. The Data Team must reassess legacy requests when further engineering is required. Streamlit stays available as a compatibility view; the new assessment/decision controls live in React.

## Validation

| Check | Result |
|---|---|
| Python suite | PASS — 222 tests, including all status pairs and stateful service/API approval tests |
| Existing JavaScript customer-view tests | PASS — 5 tests |
| React production build | PASS — desk and AI HTML/assets generated |
| Additive migration rerun | PASS — existing ticket/activity data unchanged |
| Assessment fields and actor/timestamp persist | PASS — live Snowflake |
| Approve with confirmation / reject with mandatory reason | PASS — live API/Snowflake |
| Direct unapproved start/resume/reopen | PASS — rejected, including legacy reopening |
| Exact assessment revision binding | PASS — stale revision rejected even with current ticket version |
| Changed size / changed notes | PASS — approval withdrawn, status TRIAGED, reapproval required |
| Decision concurrency | PASS — contradictory decisions from the same ticket version yield one success and one HTTP 409 |
| Decision + history atomicity | PASS — injected history failure leaves ticket and activity unchanged |
| Full submit → assess → approve → start → clarification → BU response → resolve/close | PASS — API/Snowflake acceptance |
| Historical ticket access | PASS — legacy record read and failed-start test leave it unchanged |
| Live HTTP routes, metadata, pending demo and built assets | PASS — isolated local test server |
| Actual React browser clicks / visual review | NOT EXECUTED — automatic approval review rejected the headless Edge/Playwright run as blocked by policy; no more specific reason was returned |

The build/API checks do not establish browser interaction or visual correctness. A temporary QA-only browser tool was isolated under ignored output; it was never added to application dependencies. No browser action ran after the policy rejection.

Evidence: `desk_effort_migration.json`, `desk_effort_happy_path.json`, `desk_effort_acceptance.json`, `desk_effort_serving.json`. The happy-path request `TDS-000301` and rejection/revision request `TDS-000203` are retained CLOSED validation records.

## Demo

Use the existing launcher and `/desk`. Requester `motor.demo` (Motor business user) sees **TDS-000202**, the clearly illustrative Motor claims dashboard enhancement awaiting effort approval. Assessment: **M**; “Data mapping, development and validation are required.” Its assessment version is 1 at validation. The deterministic seed does not duplicate the ticket or reset subsequent decisions.

For a fresh full journey, submit a new request, triage/assign it in Manage request, enter M and notes, and Submit for BU Approval. BU reviews the card, explicitly confirms and approves. Data Team then selects Start Work. To demonstrate rejection, reject a fresh assessment with a reason, then use Reassess Effort and resubmit.

The existing typed workspace/profile switch is a demo mechanism, not real authentication, authorization or verified employee identity. No production access-control claim is made. No hosted deployment was performed.


The existing local API on port 8000 was restarted to load the new rules. `/desk`, approval metadata and the illustrative pending record were checked through the running server. A direct unapproved IN_PROGRESS POST was rejected with HTTP 422 and left the ticket version unchanged. The isolated 8012 test server was stopped; ports 8002 and 8502 were not started. Current local desk: http://127.0.0.1:8000/desk.
