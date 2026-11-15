# Validation report — 16 November 2026

Maintenance update: renamed the shared local Snowflake profile to `snowflake-DINHEAO-HN84194`, preserving its connection parameters. Updated the launcher and README. Added the supplied Tune Protect logo to the sidebar and tab icon, and to deployed artifacts. The renamed profile connected successfully; Streamlit AppTest rendered the logo and reconciled the NBO KPI to 10,566. Local HTTP health returned `ok` after restart. Updated source and logo were downloaded from the Snowflake live version and matched local SHA-256 hashes. Browser visual QA remains unverified.

Implemented all four workspaces and created the Snowflake app object. **Local application and live SQL checks pass. Browser presentation and interactive hosted startup remain unverified.** Do not treat this report as a completed presenter-role rehearsal.

## Acceptance evidence

| Criterion | Status | Evidence / boundary |
|---|---|---|
| Application launches | PASS locally; hosted startup NOT EXECUTED | Streamlit AppTest on 1.42.0; local HTTP health `ok`. Snowflake app object/package settings verified separately. |
| NBO count reconciles | PASS | 10,566 distinct source customers = grouped overview count = application KPI; `nbo_gate.json`. |
| Real customer attributes support recommendations | PASS | Live source predicate checks, High-value filter, recommendation evidence and live Cortex evidence selection. |
| NBA transparent rules | PASS | Eight live SQL rule/window fixtures, filters, missing-renewal wording, deterministic explanation; `acceptance.json`, `final_checks.json`. |
| Executive metrics reconcile | PASS for supported definitions | Independent GWP, NEP, net incurred and loss-ratio source queries; monthly/line/channel totals reconcile. Claims plan gross/net basis remains unconfirmed. |
| Business user creates a ticket | PASS | Real Snowflake INSERT through Streamlit AppTest; labelled validation request. |
| Data team assigns and resolves | PASS | Owner/progress/status/resolution persisted; stale version update rejected. |
| Business user sees resolution | PASS | Role switching and resolution visibility tested through AppTest against persisted state. |
| AI unavailable | PASS | Toggle-off brief, simulated Cortex outage, and simulated connection-outage screen without substituted figures. |
| GOLD remains unchanged | PASS for code scope and checked invariants | No GOLD DDL/DML. GOLD column metadata and DERIVED_METRIC/FIELD_DISPLAY/MART_REGISTRY content hashes unchanged from preimplementation inspection. No claim of a full before/after hash of every mart row. |

## Executed checks

- `pytest`: **15 passed**. Parameter binding, evidence-ID validation, ticket transition restrictions and unknown-renewal wording.
- `tests.live_nbo`: PASS on Streamlit 1.42.0. Executed first as the NBO implementation gate, then repeated after runtime alignment.
- `tests.live_workflows`: PASS on Streamlit 1.42.0. Includes live financial reconciliation, SQL retention rules, ticket create/assign/resolve/business view and simulated Cortex outage.
- `tests.live_financial_edges`: PASS. Inline read-only Snowflake fixtures verify missing actual/plan keys, zero denominators and null source amounts.
- `tests.final_checks`: PASS on existing `AGENT_ROLE` / `POC_WH`. Final screens, missing renewal dates, connection failure, semantic fingerprints and GOLD column metadata.
- Python compilation: PASS. Dependency check: no broken requirements. The interrupted dependency downgrade left an ignored stale protobuf metadata directory; the active runtime imports and tests pass.
- Live Cortex: `AI_COMPLETE` with `llama3.3-70b` and structured evidence identifiers passed. Legacy `CORTEX.COMPLETE` is unavailable on this account.

The broader customer source has 179,725 unique customers, all at snapshot 31 October 2026. Of these, 146,948 have no next renewal month; the app does not infer one. All 10,566 NBO candidates have the required attributes.

Financial actual and plan periods: January 2024–October 2026. Actual policy/month keys and plan month/entity/line/channel keys had no duplicates at inspection. For Motor + Travel, January–October 2026, source GWP is **MYR 18,926,262.09** and plan GWP **MYR 20,084,123.92**. These are captured verification observations, not app constants.

## Deployment evidence

- App: `TUNE_BI_DB.APP_STATE.TUNE_AI_INTELLIGENCE`, owner `AGENT_ROLE`.
- Runtime: `SYSTEM$WAREHOUSE_RUNTIME`; query warehouse: existing `POC_WH`.
- Package declaration: Python 3.11, Streamlit 1.42.0, Snowpark, pandas, Plotly and toml.
- No external access integrations or secrets attached. No new compute pool was created. The initial account default selected a system container runtime; deployment was corrected to explicit warehouse runtime.
- The final live-version copies of `app.py`, `business_logic.py`, `snowflake_service.py` and `environment.yml` were downloaded through Snowflake SQL GET and match local SHA-256 hashes exactly; `deployed_source_match.json`.
- CLI 3.33.0 reports a nonzero exit after uploading when it cannot construct a browser URL from the working organization/account hostname. SQL DESCRIBE, LIST and downloaded-file hashes establish the remote object and file state; they do not establish interactive runtime startup.
- A trial regional hostname failed certificate validation. It was not retained; no TLS checks were disabled and no connection profile was modified.
- Local server remains available at `http://localhost:8501`, using the existing named profile with session-only overrides for `AGENT_ROLE` / `POC_WH`.

## Remaining rehearsal checks

Computer use stopped because it could not confidently determine the current browser URL. No browser workaround was attempted. Consequently these checks remain NOT EXECUTED:

1. Visual inspection at the presentation resolution, chart appearance and customer table row clicks.
2. Interactive Snowflake app startup, package resolution and execution under its Python 3.11 runtime.
3. Presenter-role access and full hosted create/assign/resolve workflow.

Confirm the plan incurred-claims definition before enabling claims actual/plan variance or planned loss ratio. Demo role switching is not real authentication/authorization. Validation tickets are retained as labelled synthetic rehearsal records. No report, customer communication or external notification was sent.
