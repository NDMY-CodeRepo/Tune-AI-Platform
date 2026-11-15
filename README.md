# Tune AI Intelligence

Tune Protect executive demo for **19 November 2026**. Four Streamlit workspaces use live queries against existing Snowflake marts: Next Best Offer, Next Best Action, Executive Intelligence and Data Service Desk. The Snowflake database describes its records as **synthetic demo data**; the application queries those records, with no fabricated local business results.

## Launch locally

Python 3.10+ and an existing Snowflake connection are required. From this directory in PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
.\launch.ps1
```

Open <http://localhost:8501>. The launch script reuses the existing `snowflake-DINHEAO-HN84194` Snowflake CLI profile in `%LOCALAPPDATA%\snowflake\config.toml`, overrides only the session's database/schema, role and warehouse, and leaves the profile unchanged. This profile was renamed from `pos-ai-platform`; connection parameters are preserved. It defaults to existing `AGENT_ROLE` / `POC_WH`. Override for another environment:

```powershell
.\launch.ps1 -ConnectionName YOUR_PROFILE -ConfigPath C:\secure\config.toml -Role YOUR_ROLE -Warehouse YOUR_WAREHOUSE
```

For the Python connector's standard `connections.toml`, set `TUNE_SNOWFLAKE_CONNECTION` to its profile name and leave `TUNE_SNOWFLAKE_CONFIG` unset, then run `.\.venv\Scripts\python -m streamlit run app.py`. Alternatively copy `.streamlit/secrets.toml.example` to `.streamlit/secrets.toml` and supply your own identity. Credentials stay outside source control. Never paste credentials into the app. A connection error produces an empty error state, never substituted figures.

## Streamlit in Snowflake

The preferred deployment is a warehouse-runtime app, explicitly selected in `snowflake.yml`, using the existing `POC_WH`. `get_active_session()` uses Snowflake's native session. No external service, pipeline, compute pool, external access integration or model training is required.

The app object is `TUNE_BI_DB.APP_STATE.TUNE_AI_INTELLIGENCE`. Open it in Snowsight → Projects → Streamlit, using a role authorized to view the app. Its object, package configuration and uploaded files were inspected through SQL; **interactive startup and browser rendering in Snowflake have not been verified**.

To deploy/update from this directory:

```powershell
snow sql -c YOUR_PROFILE --role YOUR_ROLE -f sql/setup.sql
snow streamlit deploy tune_ai -c YOUR_PROFILE --role YOUR_ROLE --database TUNE_BI_DB --schema APP_STATE --warehouse POC_WH --replace
```

Change `query_warehouse` in `snowflake.yml` if your existing warehouse differs. `environment.yml` selects Python 3.11 and Streamlit 1.42.0. Local application tests also run on Streamlit 1.42.0 (local Python 3.10). No secrets, validation exports or tests are uploaded: deployment artifacts are listed explicitly.

On the inspected account, CLI 3.33.0 creates/updates the app but exits nonzero when constructing its browser URL from an organization/account hostname. Verify `DESCRIBE STREAMLIT TUNE_BI_DB.APP_STATE.TUNE_AI_INTELLIGENCE` and `LIST 'snow://streamlit/TUNE_BI_DB.APP_STATE.TUNE_AI_INTELLIGENCE/versions/live/'` before retrying a reported deployment failure. Do not weaken TLS or change a working connection hostname to work around this display error.

## Snowflake requirements

- Database/schema usage and SELECT on `TUNE_BI_DB.GOLD.CUSTOMER_360_WIDE_MART`, `GI_ENTERPRISE_WIDE_MART`, `GI_PLAN_MONTHLY` and `DERIVED_METRIC`.
- USAGE on an existing running/resumable warehouse. `AGENT_ROLE` owns the inspected marts and APP_STATE; a narrower demo role can be provisioned by your administrator before sharing beyond the demonstrator.
- For setup only: CREATE TABLE on `TUNE_BI_DB.APP_STATE`. `sql/setup.sql` creates only `DATA_REQUEST_TICKET` if absent; it does not migrate or replace existing objects. APP_STATE was inspected first and contained no matching ticket workflow.
- For ticket use: SELECT, INSERT, UPDATE on `APP_STATE.DATA_REQUEST_TICKET`.
- For deployment: CREATE STREAMLIT and privileges to upload its artifacts in APP_STATE. No access grants are applied automatically.
- Optional AI: permission to call `AI_COMPLETE` and access to `llama3.3-70b`. Both were exercised on this account. Legacy `SNOWFLAKE.CORTEX.COMPLETE` is blocked here. `TUNE_CORTEX_MODEL` can override the model locally; revalidate before changing it.

No GOLD DDL or DML is issued by setup, the application or validation scripts. Read-only inspection SQL and aggregate evidence are under `sql/` and `validation/`.

## Business definitions

**NBO:** Motor held, Travel not held, existing next-best-product Travel, marketing consent Yes. The inspected source has **10,566 unique candidates**, with required attributes populated. The UI always displays queried counts. This is not confirmed eligibility, suitability or a newly trained propensity model.

Ranking is SQL-based: Low risk → Medium → High, then lifetime value descending, renewal-window flag first, renewal month ascending and customer ID. High-risk candidates receive a retention-first next step. The first 200 matching customers are displayed, with the full filtered count shown separately. Overview charts describe the entire candidate segment; list filters apply to the list and detail panel.

**NBA:** Uses existing risk/value bands. Renewal window is the next three full calendar months after the customer snapshot. At the inspected 31 October 2026 snapshot, this is 1 November 2026–31 January 2027. High value means High or Top band.

1. High risk + High/Top value + renewal window: Priority retention review.
2. Other High risk: Retention review.
3. Medium risk + renewal window: Proactive renewal engagement.
4. Other Medium risk: Monitor retention needs.
5. Low risk: Standard relationship maintenance.

Ties use lifetime value descending, risk score descending and customer ID. A missing renewal month never qualifies for the renewal window and is explicitly labelled unavailable. The source contains 146,948 such records across the broader Customer 360 population. Recommendations do not authorize customer contact; marketing consent is displayed and any permitted engagement route must be reviewed.

**Executive Intelligence:** Actual grain is one policy per accounting month, confirmed by metadata and a duplicate-key query. Plan keys are unique at accounting month/entity/business line/distribution channel. Both sides are aggregated independently at those four keys before a full outer join. Source periods are January 2024–October 2026; default view is 2026 YTD. No future months or absent history are inferred.

- GWP and NEP sum source monthly movements. Variance = actual − plan; variance % = variance / plan.
- Net incurred claims = gross paid + outstanding reserve movement + IBNR movement − reinsurance recoveries.
- Net loss ratio = net incurred / net earned premium. The expression is checked against `DERIVED_METRIC.LOSS_RATIO` at runtime; a changed definition blocks the financial screen pending review. Ratios use summed amounts, never an average of row ratios.
- Missing keys are exposed; affected variances are unavailable. Null source amounts are not silently omitted. Zero denominators return unavailable.
- `PLAN_INCURRED_CLAIMS` has no documented gross/net basis. Its source amount is shown separately; claims variance and planned loss ratio are withheld until that basis is confirmed.
- Line/channel variances describe accounting contributions, not proven business causes. There is no invented causal explanation.

**AI:** The engine receives only approved fact sentences, without customer identity. `AI_COMPLETE` selects evidence identifiers in priority order using structured output. The app validates those identifiers and renders only approved facts, together with the deterministic recommendation, next action and human-review requirement. This deliberately constrained AI-curated brief cannot introduce pricing, travel plans, eligibility or unsupported findings. AI is explicitly labelled and never executes SQL. Turning AI off, a Cortex error or an invalid response yields a deterministic brief.

**Service desk:** UUID ticket reference, business justification, owner, progress notes, resolution notes and version are persisted in Snowflake. Writes are parameterized and uncached. Status moves NEW → IN_PROGRESS → RESOLVED → CLOSED; resolved requests can return to IN_PROGRESS. Owner is required for work to start, notes for resolution/closure. A version check rejects stale updates. Requester identity persists through demo-role switching. A submission token supports retry after an uncertain insert response.

The demo role selector and typed requester identity are **not authentication or authorization**. Do not expose this app as a production request portal. No messages or notifications are sent.

## Demo walkthrough

1. Open Next Best Offer and refresh Snowflake data. Show the live candidate count and the 31 October snapshot label. Describe the synthetic source data honestly.
2. Filter Customer value to High or Top. Select a customer row. Explain the existing holdings, consent, risk, value and renewal month. Show Travel as a candidate recommendation.
3. Generate Engagement Brief. Point out AI-curated supporting evidence, rule-based next action and human review. Disable Cortex and regenerate to demonstrate continuity.
4. Open Next Best Action. Filter High risk and Top value. Explain the displayed renewal window and priority-review rule. Contrast with a customer whose renewal date is unavailable.
5. Open Executive Intelligence. Use 2026 YTD, All business lines and All channels. Review GWP/NEP versus plan, monthly chart, line/channel contributions and the financial definitions. Explain the unconfirmed plan-claims basis if asked.
6. Open Data Service Desk as Business User (`motor.demo`). Submit a Motor report request with title `Motor claims breakdown by channel`, a description and business justification. Note its ticket reference.
7. Switch to Data Team. Open that reference, assign `demo.engineer`, save IN_PROGRESS with progress notes. Add resolution notes, save RESOLVED.
8. Switch back to Business User. Open the same reference and show its saved resolution. For this demonstration the role selector only changes the view.

Before 19 November: open the deployed Snowflake app under the presenter's actual role, rehearse the above sequence in a browser, verify that POC_WH resumes, regenerate an AI brief, and keep the local launch as fallback. These browser checks remain required.

## Validation

Install test tooling with `.\.venv\Scripts\python -m pip install pytest`, set the connection environment variables as in `launch.ps1`, then:

```powershell
.\.venv\Scripts\python -m pytest -q
.\.venv\Scripts\python -m tests.live_nbo
.\.venv\Scripts\python -m tests.live_financial_edges
.\.venv\Scripts\python -m tests.live_workflows
```

`live_nbo` is the first workflow gate and ran before later modules were completed. `live_workflows` creates a labelled `[Validation]` request and resolves it through Streamlit AppTest; it leaves that synthetic request as evidence. Repeating it creates another labelled request. It does not deliver a report. Validation records from development are retained in the ticket table and appear only under their `validation.motor` requester in the business view.

Evidence: `validation/nbo_gate.json`, `acceptance.json`, `financial_edges.json`, `requirements-tested.txt` and `REPORT.md`. Live financial checks reconcile GWP, NEP, incurred claims and loss ratio to independent source SQL, and reconcile monthly/line/channel totals. SQL fixtures exercise missing coverage, zero denominators and null amounts. Ticket tests verify persistence, owner/status updates, business-user resolution visibility and stale-update rejection. Cortex is tested live; failure behavior is also simulated.

## Known limitations

- Browser visual QA, dataframe row-click behavior in a real browser and interactive Snowflake startup remain unverified because computer use stopped at its browser-URL policy check. AppTest exercises screens, filters, briefs and ticket forms, but cannot establish visual quality or hosted startup.
- Local Python 3.10 validation does not establish Python 3.11 Snowflake runtime behavior. The hosted runtime and package settings were inspected, not interactively executed.
- Claims actual/plan comparisons await a confirmed plan-claims definition.
- This is a single-role demo. No user provisioning, RBAC implementation, SLA engine, notifications, ticket event history or customer contact integration.
- Read-only results cache for up to five minutes. Use Refresh Snowflake data before presenting; tickets always read current state.
- Customer tables and ticket queues are bounded to 200 rows, with counts/limits displayed. No bulk customer export or PII is exposed.
- No performance/concurrency benchmark or production security certification is claimed.
