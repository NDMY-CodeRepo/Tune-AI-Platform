# Executive Intelligence and sidebar refinement — 16 November 2026

**Current status: implementation and data checks complete; browser/screenshot acceptance BLOCKED.** This section supersedes the older iteration results retained below. No claim is made that visual quality, sidebar collapse, tooltips or responsive rendering have been verified in a browser.

## White-surface and section-spacing follow-up

The latest follow-up removes the warm/peach page, KPI and finding fills from Executive Intelligence. Header, filters, KPI row, charts, financial detail and AI insights use a consistent section rhythm. Filters now use three equal-width columns aligned across the page. The former right-hand insight rail was moved below the chart pair and financial table into a full-width AI performance insights section. It presents finding, contributors and action across three desktop columns, with Explain performance in its header and exact evidence collapsed below. No calculation, data query, customer view or sidebar change was required for this follow-up.

Validation: **31 pytest cases pass**. A live Executive AppTest loads the expanded layout, verifies collapsed evidence and a single in-place Cortex selection on click (mocked for this layout check). Browser geometry/appearance remains unverified because browser access is unavailable. This is a local follow-up; no hosted deployment was performed.

## Current scope

Only the AI app sidebar and Executive Intelligence were changed. The new `shared/executive_ui.py` is explicitly called by the AI sidebar/executive view. Styles are scoped to owned container keys; sidebar sizing uses its native `aria-expanded` state. The native collapse control remains in normal document flow. No new framework, dependency, service, database object or model training was introduced.

- Sidebar: 252px expanded desktop target, native icon navigation, pale-red active item with red left border, compact branding, scrollable native content and a small Cortex/refresh utility row.
- Executive: regular/medium weights, uniform white page/card surfaces, no card gradients/shadows, a consistent date/line/channel filter grid with nonbreaking date labels, equal KPI cards, and a full-width chart pair, financial detail, then a dedicated AI performance insights section. Charts have equal heights, muted grids, red actuals and blue plans.
- Insights: one highlighted finding, at most three compact evidence sentences, one short action, Explain performance and a collapsed Supporting evidence section. Exact values stay in the financial table and evidence. Cortex generation uses an in-panel spinner and disabled submit control, retains the existing summary during the request, then reruns with the result in the same panel. Error and toggle-off paths retain deterministic results.
- Existing `customer_page`, general `explanation` and `financial_narrative` functions have unchanged ASTs relative to the start-of-task snapshot. Backend/recommendation files and the desk entry point are byte-identical. This pass issued no DDL, application-table DML or customer messages.

## GWP investigation

For 1 January–1 October accounting months in 2026 (January–October inclusive), Motor + Travel and all channels:

| Observation | Amount |
|---|---:|
| Current direct source GWP | RM 18,825,419.86 |
| Current application-service GWP | RM 18,825,419.86 |
| Earlier saved GWP | RM 18,926,262.09 |
| Change in saved/current Motor aggregates | −RM 100,842.23 |
| Current plan GWP | RM 19,974,803.65 |
| Current GWP variance | −RM 1,149,383.79 |

The current display of **RM 18.83M** is correct rounding of the current source. All ten Motor month aggregates differ from the saved inspection; Travel aggregates and row counts match. Plan GWP has also changed from its saved RM 20,084,123.92. Current direct SQL and the existing service reconcile under the same explicit filters. This establishes changed source-query results, not a display-rounding problem. The writer/refresh operation responsible was not audited, and no causal explanation of that source change is asserted. No values or formulas were adjusted to reproduce the design image.

## Acceptance and validation

| Check | Status / boundary |
|---|---|
| Compact sidebar, readable cards, 1920×1080 / 1366×768 layout | IMPLEMENTED; browser verification BLOCKED |
| Compact insights / max three displayed facts | PASS in unit/AppTest checks; browser height/readability unverified |
| Cortex loading/result placement | IMPLEMENTED with native spinner, disabled button and same-panel replacement; actual loading appearance unverified |
| Cortex and fallback | PASS: live executive Cortex result; one call per click in mocked test; failure fallback and AI-off/no-call pass |
| Exact financial reconciliation | PASS: independent actual GWP/NEP/net incurred/loss-ratio and plan GWP/NEP SQL match the service |
| Filters and source availability | PASS: business-line, NEP view, channel breakdown and single-month AppTest interaction |
| NBA/NBO unchanged | PASS: preserved function ASTs and navigation/portfolio counts; live NBO remains 10,566 |
| Backend / separate desk unchanged | PASS: file hashes match the task-start snapshot; no desk redesign or ticket writes executed |
| Unit / existing pytest suite | **31 passed** |
| Existing NBO live test | PASS including live Cortex and toggle-off fallback |
| Existing financial edge fixtures | PASS (read-only inline SQL) |
| Existing historical schema check | **FAIL:** current GOLD metadata has one extra column, `VW_AS_AT.FIRST_YEAR_ON_YEAR_MONTH` (DATE), compared with saved inspection. No columns were removed. Its baseline/assertion was not weakened. Semantic fingerprints passed before the metadata assertion. |
| App execution | PASS in AppTest; both existing local HTTP health endpoints responded `ok` |
| Desktop browser screenshots captured and reviewed | **BLOCKED:** browser access host and native computer-use pipe unavailable; no screenshots captured |

No full ticket-write rehearsal was rerun in this focused iteration. Previous ticket results below are historical. Current evidence: `executive_refinement_baseline.json`, `executive_refinement_checks.json`, `gwp_investigation.json`, `schema_snapshot_difference.json`, plus current test logs. Existing source-reconciliation tests were retained; only navigation selectors were adapted to the native icon buttons, and five compact-evidence edge cases were added.

## Delivery boundary

Changes are local. An intelligence-only deployment bundle was prepared, but no new hosted deployment was performed while the required visual review remains blocked. Both independent apps and deployment commands remain intact. To finish visual acceptance, browser access must become available for screenshots at 1920×1080 and 1366×768, including collapsed sidebar, filters, the loading/result state and the small-screen stack.

---

# Earlier iteration records (historical)

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


## Data Service Desk enhancement — 16 November 2026

The desk now has guided requests, short sequence-backed references, triage/clarification, append-only conversations, internal notes, requester closure/reopening, SQL workload views and an illustrative report catalogue. The APP_STATE migration and five labelled synthetic scenarios have been applied and rerun safely. Existing tickets and UUIDs are retained; GOLD definition hashes match. All 94 tests and the focused live desk acceptance pass, including independent-session concurrency and transaction rollback. The desk deployment bundle is prepared; no hosted update was made. Browser rendering/row-click QA is blocked by unavailable browser/native helpers. See [DESK_REPORT.md](DESK_REPORT.md) and the `desk_upgrade_*.json` evidence for the current desk results; earlier workflow/source-preservation statements above describe the prior iterations.

## Executive management analytics — 16 November 2026

The expanded management view and its verification boundaries are documented in [MANAGEMENT_REPORT.md](MANAGEMENT_REPORT.md). This iteration changes Executive Intelligence only; no hosted update was made. Historical results above describe earlier source snapshots and application iterations.


### Data Service Desk rehearsal refinement

Targeted Streamlit-only layout improvements completed for the BU homepage, queue, workload comparison and ticket conversation/manage sections. No new dependency, schema migration, financial change or workflow rewrite. All 100 existing tests and the full live desk acceptance pass. Browser rendering remains blocked by unavailable browser access. Port 8502 is left stopped; no hosted update was made. Latest evidence and limits are in [DESK_REPORT.md](DESK_REPORT.md), `desk_rehearsal_acceptance.json` and `desk_rehearsal_checks.json`.
