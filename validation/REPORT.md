# Separation and redesign validation — 16 November 2026

The existing MVP was refactored into two independent Streamlit apps. Existing financial SQL, ranking/retention rules, Cortex grounding, ticket persistence, transition validation and concurrency checks were preserved. **Local AppTest and live SQL checks pass. Browser appearance and interactive hosted startup remain unverified.**

## Reference-led visual refinement

The latest visual pass uses the supplied Tune Protect Executive Intelligence image as a composition reference. The 246px desktop sidebar has compact branding and icon navigation. Executive Intelligence has a single title/filter row, a calendar reporting-range popover, icon/tint financial cards and a three-part overview: trend, signed variance contribution and an insight rail. Financial detail stays directly under the charts. The unconfirmed planned loss ratio shown in the reference is deliberately not reproduced.

Customer Growth / Retention Intelligence now place their filters in the header and the worklist/profile directly after the KPI row. Repeated recommendation blocks, large information banners and pre-worklist methodology sections were removed. Full supporting evidence and source definitions remain available on demand. User-controlled widgets remain native Streamlit controls; no frontend framework or dependency was added. Native navigation inputs remain focusable, dynamic HTML text is escaped, and the common stylesheet no longer paints every layout wrapper as one large white canvas.

Live financial UI checks pass for the initial cards, NEP view, channel breakdown, Travel filtering, multi-year selection and a single-month period. Live NBO still reconciles to 10,566 and both Cortex/fallback paths pass. Retention, financial reconciliation and separate ticket workflows pass. Business logic, Snowflake service and dependency environment hashes match the start-of-visual-pass snapshot; data/calculation changes were not required. Evidence: `visual_baseline.json`, `visual_checks.json`, and the current workflow logs. Both app entry points and the shared visual helper were downloaded from the updated Snowflake live versions and matched local SHA-256 hashes (`visual_source_match.json`). The CLI still reports its known post-upload URL-format error; artifact verification does not establish hosted startup.

Browser rendering is **NOT EXECUTED**: both browser host and native computer-use connection were unavailable. AppTest assertions establish execution and data behavior, not pixel alignment, contrast measurements, responsive layout or browser row-click behavior. The supplied screenshots informed the changes; they are not verification screenshots of this revision.

## Monorepo structure update

Both applications remain in the existing Git repository, with entry points and individual Snowflake configs under `apps/ai-intelligence/` and `apps/data-service-desk/`. Reusable modules, branding and the Snowflake environment are maintained once under `shared/`. `sql/` and `tests/` remain at the repository root. No Git repository was initialized, no commits were rewritten and no nested repositories were created; Git HEAD matches the pre-move snapshot.

`launch.ps1` selects either relocated entry point. `deploy.ps1` stages the chosen app/config and shared files under ignored `output/deploy/`, because Snowflake CLI rejects artifact sources outside a project root. This is a small copy-and-deploy script, with no added dependency or build framework. `-PrepareOnly` creates a reviewable bundle without deployment. The CLI exit code is preserved.

The relocation leaves business rules, dependency environment and logo bytes unchanged. Shared service imports are package-relative; each entry point resolves the repository package locally or the adjacent shared package in a deployed bundle. An isolated-bundle test caught a working-directory dependency during the move; that was fixed and is covered for both apps.

The relocated apps passed the live NBO, retention, financial and ticket workflows. NBO remains 10,566. Final GOLD metadata/semantic fingerprint checks pass. Both local servers report `ok` on their existing ports. Both updated Snowflake objects use `app.py` as the staged entry point, and remote shared package paths, logo and source hashes match local files (`monorepo_checks.json`, `monorepo_deployments.json`). No ticket setup or migration was executed. Browser rendering and interactive hosted startup remain unverified.

## Applications

| Application | Entry point / local address | Snowflake object |
|---|---|---|
| Tune AI Intelligence | `apps/ai-intelligence/app.py` · http://localhost:8501 | `TUNE_BI_DB.APP_STATE.TUNE_AI_INTELLIGENCE` |
| Tune Data Service Desk | `apps/data-service-desk/app.py` · http://localhost:8502 | `TUNE_BI_DB.APP_STATE.TUNE_DATA_SERVICE_DESK` |

Intelligence navigation contains only Executive Intelligence, Next Best Action and Next Best Offer. Its default page is Executive Intelligence. The service desk has its own Business User Portal / Data Team Workspace navigation and branding. Neither imports the other entry point. `shared/ui.py` and the existing connection/business modules are shared.

## Design changes implemented

- Used the supplied dashboard and customer-segmentation references as inspiration for compact branding, light surfaces, navy type, subtle borders, Tune red accents and a clear customer-table/profile hierarchy. No additional frontend framework or dependency.
- Financial KPIs use compact RM notation, with exact values in details, help and chart hovers. Actual/plan trends and signed variance contributions sit side by side; red indicates unfavorable premium variance and green favorable variance.
- NBO is presented as Customer Growth Intelligence. The prominent candidate headline is sourced from the queried count. Segmentation is expandable, and the ranked table sits beside the selected profile and grounded engagement brief. Priority-opportunity segment means Low risk + High/Top value; no revenue forecast or conversion prediction.
- NBA is presented as Retention Intelligence. KPI hierarchy is portfolio, High risk, High-value at risk and Priority retention opportunities. The priority count uses the existing action CASE expression. Customer actions and supporting evidence sit beside the worklist.
- The standalone service desk provides a prominent New Data Request action, My Requests, a status journey and resolution details. The data team sees all-request workload counts, pending priority breakdown, ownership and the existing assignment/progress/resolution workflow.

These are implemented layout changes, not a claim of browser-verified visual quality.

## Acceptance evidence

| Check | Status | Evidence |
|---|---|---|
| Both app entry points launch | PASS locally | Both execute in Streamlit AppTest; HTTP health returns `ok` on 8501 and 8502. |
| Independent navigation | PASS | Offline AppTest asserts exactly three AI modules and two desk workspaces; no Cortex toggle in the desk. |
| NBO reconciliation | PASS | 10,566 unique source candidates = overview total = app KPI; live filters, source attributes and Cortex brief pass. |
| NBA retention rules | PASS | Eight live SQL boundary/rule cases, risk/value filters, deterministic explanation and missing-renewal wording. |
| Executive financial calculations | PASS for supported definitions | Independent GWP, NEP, net incurred and loss-ratio source queries; month/line/channel totals reconcile. |
| Ticket creation / assignment / resolution | PASS | AppTest creates a labelled validation request through the separate desk app, assigns owner, saves IN_PROGRESS then RESOLVED. |
| Business-user resolution visibility | PASS | Return to Business User Portal shows the saved resolution. |
| Concurrency protection | PASS | A stale ticket version update is rejected. |
| Cortex and fallback | PASS | Live grounded NBO explanation; toggle-off and simulated Cortex-outage fallback. |
| Connection outage | PASS | Friendly error state with no substituted business figures. |
| Financial edge cases | PASS | Read-only SQL fixtures for missing actual/plan keys, zero denominators and null source amounts. |
| GOLD and existing calculations | PASS for checked invariants | No GOLD DDL/DML; column metadata and semantic-table content fingerprints unchanged. `business_logic.py` byte-identical to pre-refactor Git HEAD. |
| Ticket table reuse | PASS | Existing APP_STATE.DATA_REQUEST_TICKET reused. No setup, recreation or migration executed. Existing CRUD methods unchanged. |
| Two hosted objects and artifacts | PASS for object/file state | SQL DESCRIBE shows independent entry points and warehouse runtimes; downloaded source/branding files match local SHA-256 hashes. |
| Browser visuals / row selection / hosted runtime startup | NOT EXECUTED | Browser host and native computer-use connection unavailable. Local Python 3.10 tests do not establish Snowflake Python 3.11 startup. |

## Executed checks

- `pytest`: **26 passed** (15 original cases, seven navigation/currency cases, and four independent-directory / standalone-bundle import cases).
- `tests.live_nbo`: PASS, including live Cortex selection and AI-off fallback on Streamlit 1.42.0.
- `tests.live_workflows`: PASS after adapting navigation to the separated apps. Validation ticket: `TP-9452C7D7-1297-437F-9ABB-5ACFED0B6D23`. This labelled synthetic rehearsal record remains in the existing table; no report or external message was sent.
- `tests.live_financial_edges`: PASS; inline SELECT fixtures only.
- `tests.final_checks`: PASS on `AGENT_ROLE` / `POC_WH`; final AI screens, missing renewal, connection failure, GOLD column metadata and semantic fingerprints.
- Source-preservation checks: existing service methods `finance`, `create_ticket`, `update_ticket`, `tickets`, `explain`, `customers`, `overview` and `health` have identical Python ASTs to pre-refactor Git HEAD. `business_logic.py` is byte-identical. Only two read-only summary methods were added to the service.
- Python compilation and `git diff --check`: PASS.

Source snapshot remains 31 October 2026. For Motor + Travel, January–October 2026, GWP actual **RM 18,926,262.09** and plan **RM 20,084,123.92** reconcile. These are verification observations, not UI constants. Plan incurred claims still lack a documented gross/net basis, so claims variance and planned loss ratio remain withheld.

## Deployment boundary

Both objects use `SYSTEM$WAREHOUSE_RUNTIME` and existing `POC_WH`. No compute pool, external service, pipeline, database, model training, access grant or dependency was added. The new object is only the separately required desk app. Its data table already existed.

CLI 3.33.0 still exits nonzero when constructing a browser URL from the working organization/account hostname, after it uploads/updates the apps. SQL DESCRIBE and downloaded-file hash comparisons establish the object and artifact state independently; they do not prove runtime startup. No hostname override or TLS relaxation was used during this refactor.

Additional relocation evidence: `monorepo_baseline.json`, `monorepo_checks.json`, `monorepo_deployments.json`.

Earlier separation evidence files: `nbo_gate.json`, `acceptance.json`, `financial_edges.json`, `final_checks.json`, `refactor_preservation.json`, `separate_deployments.json`, `separate_source_match.json`.

## Remaining rehearsal

1. Visually inspect both apps at the intended presentation resolution; confirm KPI/card alignment, responsive behavior, chart legends and customer-row selection.
2. Open each Snowflake app under the presenter's actual role; verify Python 3.11 package/runtime startup and access.
3. Rehearse the complete hosted customer brief and request/assignment/resolution journeys. Workspace switching is a demo convenience, not real authorization.
4. Confirm the plan-claims basis before enabling any further claims comparisons.
