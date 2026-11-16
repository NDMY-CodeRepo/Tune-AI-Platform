# Local React migration — 16 November 2026

## Delivered

All three AI modules now have a React frontend under `apps/ai-intelligence-react`, backed by a small FastAPI adapter under `apps/api`. Vite produces static files served by the same Python process on **http://127.0.0.1:8000**. There is no separate frontend server needed for the demo, no cloud deployment, no containers and no database/schema migration.

Executive Intelligence includes the four KPIs, four selectable trends, both variance dimensions, separate GWP/NEP premium mixes, Motor/Travel metric cards, sortable channel table, exact financial detail, expandable source evidence and final AI Insights section. NBA and NBO retain source-driven overview counts, three filters, a bounded ranked worklist, customer selection/profile, existing actions, generated briefs and methodology. The sidebar has three navigation actions with icons and bottom-aligned Cortex/refresh controls. Hash navigation supports direct module links and browser back/forward. Layouts have desktop/tablet/mobile CSS and an accessible mobile menu; actual visual behavior remains unverified below.

## Backend preservation

- Existing Snowflake connection profile, `SnowflakeService`, read cache, financial aggregate-before-join SQL, semantic guard and business rules are reused.
- Financial narrative functions moved unchanged from the Streamlit entry point to `shared/insight_facts.py`, imported by both frontends. The preservation check compares their AST against the earlier baseline.
- Customer facts/actions still come from `customer_evidence`. The API verifies customer grain and only permits explanations for IDs in the current bounded worklist. It reconstructs financial/customer evidence server-side; clients cannot submit SQL or fabricated facts.
- Cortex still selects only validated fact IDs, checked again at the API boundary. Disabled/unavailable/rejected AI returns deterministic verified evidence. No messages are sent, no propensity/eligibility scores added and no customer export is exposed.
- The API binds to loopback only, serves UI/API on the same origin, rejects untrusted hosts and cross-origin writes, and returns sanitized errors without credentials. This is a local internal demo with no authentication, not a production security implementation.
- The Streamlit AI and separate Data Service Desk remain available. `deploy.ps1` still targets Streamlit only.

## Verified

- **PASS:** React production build; locally bundled JS/CSS/logo served over HTTP. npm installation audit: zero vulnerabilities at installation. The build emits a non-blocking bundle-size advisory (about 667 kB JS / 196 kB gzip) and Lucide `use client` directive notices; this is a client-only application.
- **PASS:** 107 pytest tests, including seven new API grounding/filter/origin/error tests. A non-blocking Starlette test-client deprecation warning remains for `httpx`; `pip check` reports no broken requirements.
- **PASS:** live HTTP responses for the default and Motor/Agency financial scopes equal all values/nulls/dates from the existing validated Python financial query.
- **PASS:** read-only management SQL/AppTest regression: default, filtered, single-month and empty scopes; independent source aggregates, ratios and shares; missing/null/negative/zero-denominator SQL fixtures; Streamlit navigation, AI fallback and source preservation.
- **PASS:** live NBA/NBO API worklists match the existing query, filters return the requested risk/value bands, and profiles/facts/actions match the existing evidence function. NBA priority count matches the existing retention-priority query.
- **PASS:** NBO total and independent `COUNT(DISTINCT CUSTOMER_ID)` both equal **10,566**. NBA portfolio total is **179,725**. These are observed source results, never frontend constants.
- **PASS:** one live NBO Cortex engagement brief returns verified fact IDs; executive/NBA deterministic briefs work. Refresh invalidates the existing read cache.
- **PASS:** launcher `-SkipBuild` starts an independent local server, health endpoint returns 200, and the temporary smoke-test process is stopped. The main demo server remains on 8000.
- **PASS:** Python compilation and `git diff --check`.

Evidence: `react_live_acceptance.json`, `react-live-run.log`, `react-streamlit-regression.log`, `react-build.log`, `react-launch-smoke.log`. The earlier GOLD schema-snapshot difference remains documented in `schema_snapshot_difference.json`; this migration does not change that baseline.

## Not verified / not performed

- **BLOCKED:** browser execution, desktop/mobile screenshots, chart hover/resize, keyboard selection and pixel-level UX. Computer-use inventory returned no apps/browsers; native pipe and browser host were unavailable. HTTP/build/AppTest checks do not prove React rendering.
- **NOT PERFORMED:** Snowflake/container deployment, public access, authentication rollout or Data Service Desk migration. No database writes, GOLD changes or new pipelines were performed.

## Demo operation

1. Run `./launch.ps1 -App react` or `./launch-react.ps1`, then open http://127.0.0.1:8000. `-SkipBuild` reuses the prepared build. Stop with Ctrl+C in that terminal.
2. Review Executive Intelligence filters/trends and final AI Insights. Switch to NBO, show the live candidate count, filter customer value, select a customer and generate the engagement brief. Show NBA’s rule-based action and renewal-window methodology.
3. For today’s fallback, run `./launch.ps1 -App intelligence` and open http://localhost:8501. The desk remains `-App desk` on 8502. The React server uses a separate port and does not start either Streamlit app.
4. Before presenting, manually open all three React modules and check chart tooltips, scorecard/table labels, customer selection and the brief spinner. Browser validation is the remaining rehearsal boundary.

## Dropdown and financial chat refinement

Added a shared styled combobox with 11px/13px option padding, selected-state ticks, scroll-to-selection, type-ahead, outside-click closing and keyboard controls. Executive Intelligence now includes an in-memory Ask Tune AI transcript, suggested questions, follow-up context, current-filter scope, loading/error states and expandable numbered source evidence. The existing performance brief and customer workflows remain available.

`POST /api/chat` accepts a question, reporting filters, AI preference and at most four prior question strings. It obtains the existing validated financial aggregates, narrows evidence to supported measures/dimensions and uses the existing Cortex structured fact-ID validation. Only server-written facts based on returned SQL results are rendered; no model prose, financial numbers or SQL is executed. Unsupported periods, business lines/channels, missing comparisons, forecasts and out-of-scope requests return a clear limit. Claims and planned loss-ratio comparisons remain withheld. No schema, database or recommendation changes were made.

Validation: the React build passes; the full pytest suite passes (128 tests). Live HTTP checks pass for a GWP channel question, NEP follow-up, causal-boundary question, loss-ratio methodology, out-of-period scope, forecast refusal, prompt injection and Motor-only scope. Both channel questions completed through live Cortex with verified fact IDs. Source evidence is recorded in `executive_chat_live.json` and `chat-live-run.log`. Browser access was retried and remains blocked, so dropdown geometry, keyboard interaction, chat rendering and screenshots are not claimed as verified. The local API was restarted to expose the new endpoint.

## Unified customer navigation

The active React customer screens are now consolidated into Customer Growth & Retention Intelligence with Customer Priorities, Retention Actions and Cross-Sell Opportunities. Existing NBA/NBO queries and evidence remain unchanged; Executive Intelligence and Data Service Desk were preserved. See [CUSTOMER_CONSOLIDATION_REPORT.md](CUSTOMER_CONSOLIDATION_REPORT.md) for the latest 137-test suite and live workflow/count checks. Earlier sections above describe the prior navigation.

## Final Executive polish

AI Performance Insights now sits directly below the unchanged KPI cards, with compact line/channel contributions, investigation and collapsed evidence/chat. Monthly Performance is 40px shorter. The 149-test suite and current live GWP/plan reconciliation pass; the requested 1920×1080 browser review remains blocked by unavailable browser access. See [EXECUTIVE_FINAL_REPORT.md](EXECUTIVE_FINAL_REPORT.md) for exact amounts, earlier-snapshot investigation and preservation evidence. Earlier sections describe prior layouts.

## Floating financial assistant

Following the latest UI request, AI Performance Insights returns to the end of Executive Intelligence. Ask Tune AI now uses a bottom-right launcher and a non-modal, responsive floating chat window. Conversation state persists while minimized and resets with financial scope/evidence changes. Escape and close/minimize controls restore launcher focus; hidden responses do not take focus or scroll the page. Backend questions, grounding and calculations are unchanged. The production build and 149 tests pass; browser interactions are not verified in this pass. Applications remain stopped as requested.
