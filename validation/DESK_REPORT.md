# Data Service Desk enhancement validation — 16 November 2026

The existing Streamlit desk was enhanced in place. The APP_STATE upgrade and demo seed have run against the configured Snowflake account under `AGENT_ROLE` / `POC_WH`. The enhanced hosted Streamlit app has **not** been deployed. Browser visual and row-click review remains **BLOCKED**.

| Requirement | Result | Evidence |
|---|---|---|
| Existing ticket preservation | PASS | Additive migration run twice; original field values and assigned references unchanged. Seven historical resolved tickets were present at initial inspection. Final rerun preserves all 19 current records. |
| New request fields | PASS | Live three-step Streamlit form persists business impact, required-by date, domain, existing reference, period, fields and output format. |
| Unique short references | PASS | Existing UUIDs retained; `DATA_REQUEST_NUMBER.NEXTVAL` allocates numeric references. No MAX+1. Independent-session allocations are unique; no duplicate/null references in current tickets. Gaps are expected. |
| Triage and assignment | PASS | Live UI saves owner, confirmed priority, target date, effort and TRIAGED → IN_PROGRESS. |
| Clarification visible to BU | PASS | Team question and WAITING_FOR_BU persisted and rendered in BU history. |
| BU response visible to team | PASS | Response persists and renders to team; explicit resume option returns to IN_PROGRESS. |
| Allowed transitions | PASS | All 36 status pairs tested against the defined transition contract, with ownership/resolution checks. Live primary, clarification and reopening paths exercised. |
| Invalid/stale transitions | PASS | Direct API uses stored state, role workflow guards and version predicates. Stale saves and requester field tampering rejected. Two independent sessions competing on one version produce one winner and one stale rejection. |
| Persistent activity | PASS | Accepted workflow retains 17 entries with author, role, timestamp, entry type, message and joined ticket reference. Application history writes are append-only. |
| Atomic ticket/history writes | PASS | Simulated activity-insert failure rolls back the ticket version in live Snowflake. |
| Internal notes | PASS | Stored separately by visibility flag; BU activity SQL excludes internal text. Internal entries cannot mutate BU-visible fields. |
| Resolution, reopen and closure | PASS | Resolution and delivered reference visible to requester; reasoned reopen and final closure exercised through Streamlit. |
| Existing tests | PASS | 94 tests pass, including the original 31 tests. Existing AI acceptance checks remain; their obsolete desk block now delegates to the focused desk acceptance helper. The combined AI/live script was not rerun in this enhancement. |
| GOLD definitions | PASS | Recursive schema DDL SHA-256 before/after migration and workflow is identical: `fc6cf6b416a38490ff314dc25355de89ee4c5cf36889a23d6d24fc288c60a701`. Upgrade/application writes target APP_STATE only. This is a definition check, not a full GOLD data snapshot. |
| Demo seed idempotency | PASS | Five deterministic `[Demo]` tickets; repeated seed retains five. Three clearly illustrative catalogue entries, no invented report URLs. |
| Local package preparation | PASS | Desk-only deployment bundle prepared with existing script; no deployment command executed. |
| Browser rendering/usability | BLOCKED | Browser tool reports `The browser access host is unavailable`; Computer Use native helper reports `Computer Use native pipe is unavailable ... (os error 2)`. |
| Hosted Snowflake startup | NOT EXECUTED | New app bundle has not been deployed or interactively opened in the hosted runtime. |

Evidence: `desk_upgrade_migration.json`, `desk_upgrade_acceptance.json`, `desk_upgrade_bundle.json`. The live acceptance ticket is `TDS-000103` (UUID `1d1911dc-db86-49d3-9092-6bfae4ee2bf7`), retained CLOSED. Earlier rehearsal attempts are also retained with `[Validation]` titles, alongside the seven original validation records; the default view excludes validation records. All records remain accessible through the explicit record selector.

## Workflow and implementation boundaries

- Separate business portal navigation: Overview, New Data Request, Find Existing Reports, My Requests. The team has Operations Dashboard and Request Queue. Row selection opens a focused detail workspace with separate Request details, Conversation & history, Resolution and Manage request sections.
- Request priorities and required-by dates remain business inputs. Confirmed priority, owner, target date, effort, progress and delivery fields belong to the team workflow. BU can comment, respond to clarification, confirm closure or explain a resolved-ticket reopening.
- Status edges: NEW → TRIAGED; TRIAGED → IN_PROGRESS; IN_PROGRESS → WAITING_FOR_BU or RESOLVED; WAITING_FOR_BU → IN_PROGRESS; RESOLVED → IN_PROGRESS or CLOSED. Same-status saves are supported; CLOSED accepts comments only. Owner is required for non-new state changes; confirmed priority is required for triage/work; resolution notes are required for resolution/closure. Clarification requests must contain a visible question and use the explicit action.
- The editor retains the version it loaded. Refresh request reloads the current row. Comments also advance the version, so competing comments cannot silently bypass the concurrency protocol.
- Workload counts and distributions are SQL aggregates over all matching records. Queues are limited to 200 with a matching count, catalogue results to 100. Priority sorting/filtering uses confirmed priority when available, otherwise requested priority. Age is elapsed calendar days; overdue uses the team target date.
- Historical progress/resolution notes remain visible. No invented historical events or resolution dates are backfilled. “Resolved this month” counts current resolved/closed tickets with a known recorded resolution timestamp; older unknown dates are explicitly excluded.
- The migration creates only a sequence, activity table and catalogue table, and adds ticket columns. No records, schemas or objects are dropped/truncated/recreated. The original setup script is unchanged. Stop old desk writes during migration/replacement; rerun the migration if an old client inserted tickets without short references before replacement.
- The original shared connection utilities are reused. New desk logic lives in `shared/desk_rules.py`, `shared/desk_service.py` and `shared/desk_demo.py`; public ticket APIs remain available through the existing service. AI financial/customer functions and AI app files were not changed by this enhancement. Pre-existing unrelated working-tree changes were retained.
- Demo workspace/typed identity guards are **not authentication or production authorization**. No access grants or production access-control claims. No files, notifications, AI features, new framework or new database.

## Remaining presenter checks

1. Run `./launch.ps1 -App desk` and inspect 1920×1080 and 1366×768 browser layouts, keyboard navigation, queue row selection and back navigation. AppTest sets selected-ticket state directly; it does not establish actual dataframe click behavior.
2. Rehearse the README's ten-step portal/team journey with Record view = Exclude validation. Use Synthetic demo only to inspect the five labelled scenario examples.
3. After visual review, deploy only the desk with the existing deployment script and verify hosted Python 3.11 startup under the presenter's role. Local tests use the repository's Python 3.10 / Streamlit 1.42 environment.


## Targeted rehearsal refinement — 16 November 2026

Kept the existing Streamlit/Snowflake stack, workflow and dependencies. No migration or schema change was executed. Changes are limited to desk presentation and one allowlisted read sort (`UPDATED_AT DESC`).

- BU homepage: compact Recent Requests with directly clickable short references, awaiting-response highlights and the latest BU-visible ticket activity. New Data Request remains prominent.
- Queue: status, owner, confirmed priority and age appear first; secondary filters sit in an expander. Waiting-for-BU rows are highlighted. Table height follows the number of rows. Existing selection and filters are retained.
- Workload: a compact horizontal count chart is used for 2–10 groups; the table remains for a single group or longer lists, preserving all values.
- Details: conversation is the default section, with bounded chronological history beside the reply form. Assignment/status/resolution stay in Manage request; progress and resolution fields share a row. Compact medium-weight header and status treatment reduce vertical space.

Validation: **100 tests passed**. Focused live acceptance **PASS**, ticket **TDS-000020** retained CLOSED: submit → assign/triage → clarification → BU response → resolve → BU resolution visibility, plus reopening/closure, internal-note filtering, rollback and stale/concurrent-update rejection. GOLD definition hash remains unchanged. Extra Streamlit interaction checks pass for homepage highlights/latest updates, reference-button navigation, chart rendering, queue column order and status filtering. AST comparison against the prior staged source confirms ticket creation, updates, transactions and activity write/read methods are unchanged.

Evidence: `desk_rehearsal_acceptance.json`, `desk_rehearsal_checks.json`. AppTest injects selected-ticket state for the main dataframe workflow; the homepage reference buttons are clicked through AppTest. Actual browser rendering and dataframe row clicks remain **BLOCKED**: browser access host unavailable. No hosted deployment was performed. Port **8502 remains stopped** following the user's earlier instruction.
