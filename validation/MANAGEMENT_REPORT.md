# Executive management analytics — 16 November 2026

## Delivered scope

Executive Intelligence only: retained four KPI cards; four monthly trend options; compact full-width AI Insights at the end of the page; paired line/channel GWP or NEP variance charts; paired premium composition charts; Motor/Travel scorecards; sortable channel scorecard; retained financial detail, methodology and exact grouped evidence. Existing light design, shared sidebar and customer workflows are retained. No heatmap or additional framework was introduced.

The financial query and definitions in `shared/business_logic.py` are byte-identical to this iteration's baseline. The service's optional analytics projection wraps that unchanged query to calculate GWP and NEP shares separately, after aggregation. Date/line/channel values remain bound parameters. No DDL, DML, grants or GOLD modifications were performed by this work. Runtime `DERIVED_METRIC.LOSS_RATIO` validation remains active.

Loss ratios reuse SQL ratios of summed net incurred claims to summed NEP. Claims and loss-ratio trends have no plan trace. Whole variance groups with incomplete actual/plan coverage are excluded with a count; missing values are never filled with zero. Portfolio composition is unavailable when a group has missing/negative actual premium or the denominator is zero. The channel scorecard retains numeric values for sorting, with display-only formatting and variance text colors. Exact grouped amounts remain available under source evidence.

AI evidence IDs, grounding validation and fallback remain unchanged. Results are keyed by the filtered financial evidence, so changing scope does not show an old explanation. Observed accounting contributions are not presented as causes.

## Verification

- **PASS:** 100 pytest tests, including six focused management projection/presentation checks.
- **PASS:** read-only live reconciliation of unchanged base outputs and independent source SQL by total, month, business line and channel, including GWP/NEP plans, variances, net incurred claims, ratios and separate portfolio shares. Cases: full Jan–Oct portfolio; Motor/Agency; Travel/Direct Online over Mar–May; October only; empty selection.
- **PASS:** inline Snowflake SELECT fixtures for missing actual/plan keys, null/negative premiums, zero earned premium and zero-denominator shares. No fixture objects were created.
- **PASS:** Streamlit AppTest with live reads: all four trends; both variance and mix bases; Travel filter; single-month display; AI success and unavailable fallback (AI responses mocked in this run); NBA/NBO navigation. Customer/recommendation/narrative function ASTs match the baseline.
- **PASS:** Python compilation, `git diff --check`, and local AI deployment bundle preparation.
- **KNOWN FAILURE:** `tests.final_checks` reaches the historical GOLD-column snapshot assertion and fails on the previously observed added `VW_AS_AT.FIRST_YEAR_ON_YEAR_MONTH` column. Its earlier semantic-definition fingerprint check passes. The baseline was not changed to suppress the failure.
- **BLOCKED:** browser screenshots at desktop resolutions and visual/responsive review. Computer-use inventory returned no apps or browsers, with native pipe and browser host unavailable. AppTest does not establish pixel rendering, hover interactions or responsive visual quality.
- **NOT EXECUTED:** hosted Snowflake startup/deployment, live Cortex generation in this iteration, or ticket mutations. The separately edited service desk is outside this task.

Evidence: `management_analytics.json`, `management_analytics_run.log`, `management_final_checks.log`, `management_dashboard_baseline.json`. Live values are observations, not application constants. For Jan–Oct Motor + Travel all channels, GWP is RM 18,825,419.86 versus plan RM 19,974,803.65. Earlier source-snapshot changes are documented in `gwp_investigation.json`.

Run locally using `./launch.ps1 -App intelligence`. The prepared bundle is under `output/deploy/intelligence`; the hosted app was not updated. Remaining visual rehearsal: open the dashboard at 1920×1080 and 1366×768, review long channel labels/tooltips/table sorting, switch trend and premium bases, and confirm cards stack without page overflow.

## Internal-demo presentation refinement

AI Insights now follows Financial detail and Reporting basis as the final page section. Added a 16px margin above Monthly performance. Motor/Travel tables are replaced with native metric cards: prominent actual GWP and variance, plan GWP caption, plus NEP, net incurred claims and loss ratio; exact currency values remain in tooltips/source evidence. Cortex and refresh use a bottom-aligned flex utility section in the existing scrollable sidebar, with no fixed overlay. These changes preserve all data queries and AI controls. The 100-test suite and live management SQL/AppTest run pass again; see `demo_refinement_run.log`. Browser visual checks remain blocked by the unavailable host. The AI deployment bundle is refreshed locally only.
