# Tune Protect demo applications

Two independent Streamlit applications for **19 November 2026**:

| Application | Entry point | Local URL | Snowflake object |
|---|---|---|---|
| Tune AI Intelligence | `apps/ai-intelligence/app.py` | http://localhost:8501 | `TUNE_BI_DB.APP_STATE.TUNE_AI_INTELLIGENCE` |
| Tune Data Service Desk | `apps/data-service-desk/app.py` | http://localhost:8502 | `TUNE_BI_DB.APP_STATE.TUNE_DATA_SERVICE_DESK` |

Tune AI Intelligence contains **Executive Intelligence, Next Best Action and Next Best Offer**. The separate service desk contains **Business User Portal and Data Team Workspace**. They share connection utilities, presentation helpers and the existing business rules from `shared/`, but have separate navigation, entry points, processes and deployments.

Both read live Snowflake data. The database describes its records as **synthetic demo data**; no business figures are fabricated locally. Existing GOLD definitions and financial calculations are preserved. The service desk reuses `APP_STATE.DATA_REQUEST_TICKET` with the additive `sql/desk_upgrade.sql` migration; existing UUIDs and ticket values are retained.

## Local React demo — all three AI modules

The React version runs **Executive Intelligence, Next Best Action and Next Best Offer** against the same Python/Snowflake services. Start it with:

```powershell
.\launch.ps1 -App react
# Or directly, with optional -Port, -ConnectionName, -ConfigPath, -Role, -Warehouse:
.\launch-react.ps1
```

Open **http://127.0.0.1:8000**. The script builds React, then serves the built UI and API from one loopback-only Python process. Press Ctrl+C in the launch terminal to stop it. Node.js 22.12+ (or 20.19+) and npm are required for the Vite build. Existing Python environment/Snowflake profile setup below still applies. No credentials are bundled into JavaScript.

The first launch installs missing API dependencies from `apps/api/requirements.txt` and frontend packages using the committed npm lockfile. If preparing dependencies manually:

```powershell
.\.venv\Scripts\python -m pip install -r apps/api/requirements.txt
npm --prefix apps/ai-intelligence-react ci
npm --prefix apps/ai-intelligence-react run build
.\launch-react.ps1 -SkipBuild
```

React source: `apps/ai-intelligence-react/`; API: `apps/api/main.py`. The shared financial narrative moved unchanged into `shared/insight_facts.py` for both frontends. Financial SQL, customer rules, semantic checks and Cortex fact-ID validation remain unchanged. The API rebuilds evidence server-side and accepts only structured filters/customer IDs. Read cache refresh, source-grain checks, no-data/error states and deterministic AI fallback remain available. No database migration or GOLD changes were needed. The separate Data Service Desk remains Streamlit; `-App intelligence`, `-App desk` and `-App both` retain their previous behavior. Streamlit is the fallback for today’s demo.

For frontend editing only, `npm --prefix apps/ai-intelligence-react run dev` starts Vite on 5173 and proxies the API to the Python process on 8000. The normal demo launcher needs only port 8000. Run API tests after installing test tooling (`pip install pytest httpx`): `python -m pytest -q`. The live HTTP/Snowflake check is `python -m tests.live_react_api`, with the same connection environment as the launcher. See [React validation report](validation/REACT_REPORT.md).

This is a local internal demo with no authentication, intended to remain loopback-only. Container/Snowflake deployment and browser visual verification have not been completed. Do not use `deploy.ps1` for React; it still deploys the existing Streamlit apps.

## Executive management analytics

Executive Intelligence retains the white/navy/Tune red design and four reconciled KPIs. Monthly performance switches between GWP and NEP actual/plan, actual net incurred claims and actual net loss ratio. A dedicated AI Insights section closes the page, showing one finding, up to three verified contributors, one investigation/action and collapsed exact evidence. Cortex selects verified evidence; its loading state, filter-specific results and deterministic fallback stay inside the same section.

Management views include separate ranked line/channel variance charts (GWP or NEP), line/channel portfolio mix with separate SQL-calculated denominators, Motor/Travel metric cards with GWP, plan variance and supporting financial highlights, a numerically sortable channel scorecard, and retained exact financial detail/methodology. All use the active date, line and channel filters. Variance charts exclude incomplete groups; unavailable comparisons are not zero. Premium mix is withheld for missing/negative group amounts or a zero denominator. Loss ratios are ratios of summed claims to summed NEP. Claims-plan and planned loss-ratio comparisons remain withheld until their basis is confirmed.

For **January–October 2026, Motor + Travel, all channels**, current direct SQL and the app reconcile to **RM 18,825,419.86 (RM 18.83M)**, against plan **RM 19,974,803.65**. The earlier saved GWP result was RM 18,926,262.09. Source Motor aggregates changed by net −RM 100,842.23; values were not adjusted to match an image. See `validation/gwp_investigation.json`.

The 100-test suite and read-only management SQL/AppTest checks pass. Run `.\.venv\Scripts\python -m tests.live_management_analytics` with the Snowflake environment set. See [management validation](validation/MANAGEMENT_REPORT.md) for results and boundaries. The historical schema check still flags the added `VW_AS_AT.FIRST_YEAR_ON_YEAR_MONTH` column; its baseline remains intact. Browser screenshots and responsive visual review remain blocked by unavailable browser/native hosts. The AI bundle is prepared locally; no hosted update was made in this iteration. NBA/NBO recommendation functions and financial definitions are preserved.

## Visual direction

The AI application follows the supplied Tune Protect Executive Intelligence dashboard reference: compact logo/navigation, a single title/filter row, coordinated financial cards and a monthly trend, management scorecards and a final full-width AI insights section. Reporting-period controls are in the calendar popover; chart options include premium, claims and loss-ratio trends, with separate GWP/NEP variance and mix controls. Planned loss-ratio and claims comparisons remain unavailable until their source basis is established.

Customer Growth and Retention Intelligence use the same light theme, with filters in the header and the worklist/profile directly beneath the portfolio KPIs. Source definitions and ranking methodology sit after the main workflow. Engagement briefs use verified evidence and retain deterministic fallback. The service desk inherits the common branding and typography and now has a separate guided-request, conversation and triage workflow.

This visual pass has live data/AppTest validation. Browser rendering, responsive layout and hosted startup still require a presenter rehearsal; automated browser access was unavailable.

## Repository layout

```text
apps/
  ai-intelligence/
    app.py
    snowflake.yml
  data-service-desk/
    app.py
    snowflake.yml
shared/
  __init__.py
  business_logic.py
  snowflake_service.py
  ui.py
  assets/tune-protect-group-logo.png
  environment.yml
sql/
tests/
launch.ps1
deploy.ps1
requirements.txt
.streamlit/
```

This is one Git repository with its existing history. There are no nested repositories, package installs for local modules, monorepo tools or additional build frameworks. Business logic and connection utilities have a single source under `shared/`; both entry points import that package. `requirements.txt` is the common local dependency list and `shared/environment.yml` is the common Snowflake environment.

## Launch locally

Python 3.10+ and an existing Snowflake connection are required. From this directory in PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
# Terminal 1 — Tune AI Intelligence
.\launch.ps1 -App intelligence

# Terminal 2 — Tune Data Service Desk
.\launch.ps1 -App desk

# Or start both in one terminal; Ctrl+C stops both
.\launch.ps1 -App both
```

With `-App both`, intelligence uses 8501 and the desk uses 8502. `-Port 9000` changes these to 9000 and 9001. Keep the launching terminal open; Ctrl+C stops both child process trees. Server logs are saved under `validation/*-launch*.log`.

Open <http://localhost:8501> for intelligence and <http://localhost:8502> for requests. Running `launch.ps1` without arguments still launches intelligence. Use `-Port` to override either default. The launch script reuses the existing `snowflake-DINHEAO-HN84194` Snowflake CLI profile in `%LOCALAPPDATA%\snowflake\config.toml`, overrides only the session's database/schema, role and warehouse, and leaves the profile unchanged. This profile was renamed from `pos-ai-platform`; connection parameters are preserved. It defaults to existing `AGENT_ROLE` / `POC_WH`. Override for another environment:

```powershell
.\launch.ps1 -ConnectionName YOUR_PROFILE -ConfigPath C:\secure\config.toml -Role YOUR_ROLE -Warehouse YOUR_WAREHOUSE
```

For the Python connector's standard `connections.toml`, set `TUNE_SNOWFLAKE_CONNECTION` to its profile name and leave `TUNE_SNOWFLAKE_CONFIG` unset, then run `.\.venv\Scripts\python -m streamlit run apps/ai-intelligence/app.py --server.port 8501` or `.\.venv\Scripts\python -m streamlit run apps/data-service-desk/app.py --server.port 8502`. Alternatively copy `.streamlit/secrets.toml.example` to `.streamlit/secrets.toml` and supply your own identity. Credentials stay outside source control. Never paste credentials into the app. A connection error produces an empty error state, never substituted figures.

## Streamlit in Snowflake

Both deployments use warehouse-runtime apps, explicitly selected in each application's own `snowflake.yml`, using the existing `POC_WH`. `get_active_session()` uses Snowflake's native session. No external service, pipeline, compute pool, external access integration or model training is required.

The separately addressable objects are listed above. Open either app in Snowsight → Projects → Streamlit, using a role authorized to view the app. Its object, package configuration and uploaded files were inspected through SQL; **interactive startup and browser rendering in Snowflake have not been verified**.

To deploy/update either app independently from the repository root:

```powershell
.\deploy.ps1 -App intelligence
.\deploy.ps1 -App desk
```

Each command reads only the selected app's deployment configuration:

- `apps/ai-intelligence/snowflake.yml` → `TUNE_AI_INTELLIGENCE`.
- `apps/data-service-desk/snowflake.yml` → `TUNE_DATA_SERVICE_DESK`.

The script defaults to the same existing Snowflake connection, role and warehouse as the launcher. Override with `-ConnectionName`, `-Role` or `-Warehouse`. It does not run ticket setup SQL, modify GOLD or grant access. The existing ticket table and the desk upgrade migration are required for the enhanced desk.

Snowflake CLI requires deployment sources to be inside its project directory. `deploy.ps1` therefore copies the selected entry point/config, shared Python package, logo, environment and theme into ignored `output/deploy/intelligence/` or `output/deploy/desk/`, then calls the CLI against that self-contained bundle. These are generated deployment copies, not additional maintained business logic. No credentials, secrets files, tests or validation exports are staged.

To inspect a bundle without deploying:

```powershell
.\deploy.ps1 -App intelligence -PrepareOnly
.\deploy.ps1 -App desk -PrepareOnly
```

For a manual CLI invocation after staging, use `snow streamlit deploy tune_ai --project output/deploy/intelligence ... --replace` or the corresponding `tune_desk` / `output/deploy/desk`. Do not run the CLI directly against a source app folder; shared dependencies are assembled by the staging script.

Change `query_warehouse` in the chosen app's `snowflake.yml` if needed. `shared/environment.yml` selects Python 3.11 and Streamlit 1.42.0 and is copied to the bundle root as `environment.yml`. Local tests use Streamlit 1.42.0 on Python 3.10. The logo and all shared helper imports resolve relative to their source files.

On the inspected account, CLI 3.33.0 creates/updates the app but exits nonzero when constructing its browser URL from an organization/account hostname. Verify `DESCRIBE STREAMLIT TUNE_BI_DB.APP_STATE.TUNE_AI_INTELLIGENCE` and `LIST 'snow://streamlit/TUNE_BI_DB.APP_STATE.TUNE_AI_INTELLIGENCE/versions/live/'` before retrying a reported deployment failure. For the desk, substitute `TUNE_DATA_SERVICE_DESK` in those checks. Do not weaken TLS or change a working connection hostname to work around this display error.

## Snowflake requirements

- Database/schema usage and SELECT on `TUNE_BI_DB.GOLD.CUSTOMER_360_WIDE_MART`, `GI_ENTERPRISE_WIDE_MART`, `GI_PLAN_MONTHLY` and `DERIVED_METRIC`.
- USAGE on an existing running/resumable warehouse. `AGENT_ROLE` owns the inspected marts and APP_STATE; a narrower demo role can be provisioned by your administrator before sharing beyond the demonstrator.
- The existing `APP_STATE.DATA_REQUEST_TICKET` must be present. Apply `sql/desk_upgrade.sql` explicitly before using the enhanced desk. No migration or seeding runs during launch or deployment. `sql/setup.sql` remains the original initial-install script.
- For desk use: SELECT, INSERT, UPDATE on `APP_STATE.DATA_REQUEST_TICKET`; SELECT, INSERT on `DATA_REQUEST_ACTIVITY`; SELECT on `REPORT_CATALOGUE`; USAGE on `DATA_REQUEST_NUMBER`. Migration and explicit seeding additionally require suitable APP_STATE DDL/DML privileges. No grants are applied by this change.
- For deployment: CREATE STREAMLIT and privileges to upload its artifacts in APP_STATE. No access grants are applied automatically.
- Optional AI: permission to call `AI_COMPLETE` and access to `llama3.3-70b`. Both were exercised on this account. Legacy `SNOWFLAKE.CORTEX.COMPLETE` is blocked here. `TUNE_CORTEX_MODEL` can override the model locally; revalidate before changing it.

No GOLD DDL or DML is issued by setup, the application or validation scripts. Read-only inspection SQL and aggregate evidence are under `sql/` and `validation/`.

## Business definitions

**NBO:** Motor held, Travel not held, existing next-best-product Travel, marketing consent Yes. The inspected source has **10,566 unique candidates**, with required attributes populated. The UI always displays queried counts. This is not confirmed eligibility, suitability or a newly trained propensity model.

Ranking is SQL-based: Low risk → Medium → High, then lifetime value descending, renewal-window flag first, renewal month ascending and customer ID. High-risk candidates receive a retention-first next step. The first 200 matching customers are displayed, with the full filtered count shown separately. The expandable opportunity segmentation describes the entire candidate segment; list filters apply to the ranked list and detail panel. The priority-opportunity count means Low retention risk + High/Top source value; it is not a conversion forecast. The selected customer and engagement brief sit beside the ranked list.

**NBA:** The Retention Intelligence screen uses existing risk/value bands. Its priority-retention KPI counts the unchanged Priority retention review rule across the portfolio. Renewal window is the next three full calendar months after the customer snapshot. At the inspected 31 October 2026 snapshot, this is 1 November 2026–31 January 2027. High value means High or Top band.

1. High risk + High/Top value + renewal window: Priority retention review.
2. Other High risk: Retention review.
3. Medium risk + renewal window: Proactive renewal engagement.
4. Other Medium risk: Monitor retention needs.
5. Low risk: Standard relationship maintenance.

Ties use lifetime value descending, risk score descending and customer ID. A missing renewal month never qualifies for the renewal window and is explicitly labelled unavailable. The source contains 146,948 such records across the broader Customer 360 population. Recommendations do not authorize customer contact; marketing consent is displayed and any permitted engagement route must be reviewed.

**Executive Intelligence:** Actual grain is one policy per accounting month, confirmed by metadata and a duplicate-key query. Plan keys are unique at accounting month/entity/business line/distribution channel. Both sides are aggregated independently at those four keys before a full outer join. Source periods are January 2024–October 2026; default view is 2026 YTD. No future months or absent history are inferred.

- Large financial KPIs use compact RM notation (for example RM 18.93M); exact amounts remain in financial detail, KPI help and chart hover. This is display rounding only.
- GWP and NEP sum source monthly movements. Variance = actual − plan; variance % = variance / plan.
- Net incurred claims = gross paid + outstanding reserve movement + IBNR movement − reinsurance recoveries.
- Net loss ratio = net incurred / net earned premium. The expression is checked against `DERIVED_METRIC.LOSS_RATIO` at runtime; a changed definition blocks the financial screen pending review. Ratios use summed amounts, never an average of row ratios.
- Missing keys are exposed; affected variances are unavailable. Null source amounts are not silently omitted. Zero denominators return unavailable.
- `PLAN_INCURRED_CLAIMS` has no documented gross/net basis. Its source amount is shown separately; claims variance and planned loss ratio are withheld until that basis is confirmed.
- Line/channel variances describe accounting contributions, not proven business causes. There is no invented causal explanation.

**AI:** The engine receives only approved fact sentences, without customer identity. `AI_COMPLETE` selects evidence identifiers in priority order using structured output. The app validates those identifiers and renders only approved facts, together with the deterministic recommendation, next action and human-review requirement. This deliberately constrained AI-curated brief cannot introduce pricing, travel plans, eligibility or unsupported findings. AI is explicitly labelled and never executes SQL. Turning AI off, a Cortex error or an invalid response yields a deterministic brief.

**Service desk:** Internal UUIDs remain the ticket identifiers; Snowflake sequence values display as `TDS-000123` (gaps are expected). Requests move NEW → TRIAGED → IN_PROGRESS → RESOLVED → CLOSED, with IN_PROGRESS ↔ WAITING_FOR_BU and RESOLVED → IN_PROGRESS. Same-status saves are supported; CLOSED only accepts comments. Owner and confirmed priority are required for triage/work; resolution notes are required to resolve or close. Requester comments, clarification responses and closure cannot overwrite Data Team fields. Every ticket mutation and append-only activity record commits in one transaction. Version predicates reject stale saves; the editor retains its loaded version until **Refresh request** or a successful update. Role and identity switching preserve the requester identity for the demo.

The demo role selector and typed requester identity are **not authentication or authorization**. Do not expose this service desk as a production request portal. No messages or notifications are sent.

## Tune AI Intelligence demo walkthrough

1. Open the intelligence app (port 8501), defaulting to Executive Intelligence. Select 2026 YTD, All business lines and All channels. Review GWP/NEP versus plan, the actual/plan trend and variance contribution. Use Financial detail for exact amounts and Definitions for the calculation basis. The plan-claims basis remains unconfirmed.
2. Open Next Best Offer, presented as Customer Growth Intelligence. Refresh Snowflake data, show the live candidate headline and snapshot date, and explain the synthetic source records.
3. Filter value to High or Top. Select a customer row and inspect the profile beside the table. Explain holdings, consent, risk, value and renewal month. Travel remains a candidate recommendation.
4. Generate Engagement Brief. Explain its grounded evidence, rule-based action and human review. Disable Cortex and regenerate to show continuity.
5. Open Next Best Action, presented as Retention Intelligence. Filter High risk and Top value. Explain the renewal window, priority-review count and selected customer action. Missing renewal dates remain explicitly unavailable.

## Tune Data Service Desk enhancement

The enhanced desk is implemented locally; its additive migration and synthetic examples have been exercised in Snowflake. Hosted application deployment and browser visual review remain outstanding. See `validation/DESK_REPORT.md` for evidence and boundaries.

Apply the upgrade using the same connection environment variables described above (the command does not deploy an application):

```powershell
$env:TUNE_SNOWFLAKE_CONNECTION = 'snowflake-DINHEAO-HN84194'
$env:TUNE_SNOWFLAKE_CONFIG = "$env:LOCALAPPDATA\snowflake\config.toml"
$env:TUNE_SNOWFLAKE_ROLE = 'AGENT_ROLE'
$env:TUNE_SNOWFLAKE_WAREHOUSE = 'POC_WH'
.\.venv\Scripts\python -m tests.migrate_desk --seed-demo
.\.venv\Scripts\python -m tests.live_desk
.\deploy.ps1 -App desk -PrepareOnly
```

The migration is idempotent and performs only additive APP_STATE DDL and missing-reference backfill. The sequence is never reset. Pause writes from the old desk during migration and replacement: older application code does not allocate the new reference or write history. If an old client created more tickets before replacement, rerun the migration to backfill their references. Five deterministic `[Demo]` tickets are seeded explicitly; seeding again does not duplicate them. Three illustrative catalogue entries are added only when real catalogue records are absent. They have no fabricated report links. Activity history begins with the upgrade; existing progress and resolution notes remain visible without invented historical events. Legacy resolved dates are unknown and are excluded from “Resolved this month”.

The default record view excludes `[Validation]` tickets, while **All records** retains access to them. **Synthetic demo only** shows only the five seeded examples. Switch to **Exclude validation** for the full new-submission walkthrough, since newly submitted requests are ordinary request records. Request queues show at most 200 matches, with the matching count; overview counts and workload distributions use all matching records.

1. Launch `./launch.ps1 -App desk` and use Business User Portal, requester `motor.demo`.
2. Open **Find Existing Reports**, search a keyword/domain, and explain that `[Demo]` catalogue entries are illustrative.
3. Choose **New Data Request**. Complete request information, conditional data requirements, then review and submit. Note the short reference.
4. In **My Requests**, select the row to open request details, conversation/history and resolution.
5. Switch to **Data Team Workspace**. Review the operations dashboard, then select the request in **Request Queue**.
6. In **Manage request**, assign `demo.engineer`, confirm priority, set target/effort and save **Triaged**. Then save **In Progress**.
7. In **Conversation & history**, choose **Request clarification**, enter a BU-visible question and send. The ticket becomes **Waiting for BU**.
8. Switch back to the portal, select the request and respond. Leave the explicit **Return to In Progress with this response** option checked.
9. As Data Team, record resolution notes and a delivered output link/reference, then resolve. Internal notes are separate from BU-visible history.
10. As BU, view the resolution/reference and **Confirm closure**, or give a reason to reopen a resolved request.

The workspace selector and typed identities are workflow demonstration controls, not production authentication or authorization. No attachments, AI search, notifications or external integrations are included.

Before 19 November: open **both** deployed apps under the presenter's actual role, rehearse these journeys in a browser, check that POC_WH resumes and regenerate an AI brief. Keep both local launches available as fallbacks. These browser checks remain required.

## Validation

Install test tooling with `.\.venv\Scripts\python -m pip install pytest`, set the connection environment variables as in `launch.ps1`, then:

```powershell
.\.venv\Scripts\python -m pytest -q
.\.venv\Scripts\python -m tests.live_nbo
.\.venv\Scripts\python -m tests.live_financial_edges
.\.venv\Scripts\python -m tests.live_management_analytics
.\.venv\Scripts\python -m tests.live_workflows
.\.venv\Scripts\python -m tests.final_checks
```

`live_nbo` is the first workflow gate and ran before later modules were completed. `live_workflows` creates a labelled `[Validation]` request and resolves it through Streamlit AppTest; it leaves that synthetic request as evidence. Repeating it creates another labelled request. It does not deliver a report. Validation records from development are retained in the ticket table and appear only under their `validation.motor` requester in the business view.

Evidence: `validation/nbo_gate.json`, `acceptance.json`, `financial_edges.json`, `requirements-tested.txt` and `REPORT.md`. Live financial checks reconcile GWP, NEP, incurred claims and loss ratio to independent source SQL, and reconcile monthly/line/channel totals. SQL fixtures exercise missing coverage, zero denominators and null amounts. Ticket tests verify persistence, owner/status updates, business-user resolution visibility and stale-update rejection. Cortex is tested live; failure behavior is also simulated.

## Known limitations

- Browser visual QA, dataframe row-click behavior in a real browser and interactive Snowflake startup remain unverified because the browser access host and native computer-use connection were unavailable during the refactor. AppTest exercises screens, filters, briefs and ticket forms, but cannot establish visual quality or hosted startup.
- Local Python 3.10 validation does not establish Python 3.11 Snowflake runtime behavior. The hosted runtime and package settings were inspected, not interactively executed.
- Claims actual/plan comparisons await a confirmed plan-claims definition.
- This is a single-role demo. No user provisioning, RBAC implementation, SLA engine, notifications or customer contact integration. The enhanced desk has append-only ticket activity history.
- Read-only results cache for up to five minutes. Use Refresh Snowflake data before presenting; tickets always read current state.
- Customer tables and ticket queues are bounded to 200 rows, with counts/limits displayed. No bulk customer export or PII is exposed.
- No performance/concurrency benchmark or production security certification is claimed.
