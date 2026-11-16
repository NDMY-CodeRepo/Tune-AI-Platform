# Executive Intelligence final polish — 16 November 2026

## Targeted UI changes

AI Performance Insights is immediately below the unchanged KPI cards, before Monthly Performance and the detailed analytics. The default card shows one calculated key finding, at most two business-line/channel contribution sentences, one investigation, Explain Performance and collapsed exact supporting evidence. Cortex still selects approved evidence IDs; selected facts are highlighted inside supporting evidence. Ask Tune AI remains accessible in a separate collapsed disclosure so the default summary stays compact.

Monthly Performance is reduced from 285px to 245px on desktop and from 255px to 225px on small screens, with slightly tighter heading/chart spacing. Executive section gaps are modestly reduced using scoped CSS. The existing typography, palette, sidebar, KPI contents, financial calculations and customer/desk workflows are preserved.

## Current financial reconciliation

Independent source SQL and the live API agree for **January–October 2026, Motor + Travel, all channels**:

| Measure | Current source / API | Earlier saved snapshot | Difference |
|---|---:|---:|---:|
| GWP actual | RM 18,825,419.86 | RM 18,926,262.09 | −RM 100,842.23 |
| GWP plan | RM 19,974,803.65 | RM 20,084,123.92 | −RM 109,320.27 |
| GWP variance | −RM 1,149,383.79 | −RM 1,157,861.83 | +RM 8,478.04 |

Current actual and plan match the recent RM18.83M reconciliation in `gwp_investigation.json`. The older `data_inspection.json` month/line aggregates differ for ten Motor months on both actual and plan; Travel is unchanged. Row counts in the differing groups are unchanged. These saved aggregate differences are not display rounding, and no formulas or values were changed to reproduce a screenshot. This comparison cannot identify the upstream cause, actor or physical data-change history.

Filtered checks also reconcile independently: Motor/Agency GWP RM 4,834,084.23 vs plan RM 5,742,966.22; Travel/Direct Online GWP RM 1,616,623.82 vs plan RM 1,651,320.77. Explain Performance uses the same facts as the filtered financial response. A live Motor/Agency Cortex explanation returned valid evidence IDs; AI-off deterministic explanations also passed. Plan claims and planned loss-ratio comparisons remain withheld.

## Verification and boundaries

- **PASS:** 149 pytest tests, React production build, Python compilation and `git diff --check`. The existing non-blocking Starlette test-client and bundle notices remain.
- **PASS:** 21 preservation comparisons covering the sidebar and KPI markup, Customer Intelligence component bodies, financial/backend source files, Executive chat and existing Data Service Desk files. No GOLD, business-rule or financial-query changes were made.
- **PASS:** live independent actual/plan SQL sums, variance and filtered explanation fact equality. Evidence: `executive_final_reconciliation.json` and `executive-final-live.log`.
- **PASS:** source preservation evidence in `executive_final_preservation.json`, captured against `executive_final_baseline.json` before this polish pass.
- **BLOCKED:** requested **1920×1080 browser verification**, screenshots, chart hover/resize, custom selector interaction, and the visual Explain Performance/loading/evidence interaction. Computer-use inventory returned no apps/browsers; native pipe and browser host were unavailable. Build/API checks do not prove those browser behaviors, and they are not claimed as verified.
- **NOT PERFORMED:** any customer/desk workflow changes, ticket writes, database changes, container deployment or hosted update. The local app continues at http://127.0.0.1:8000; refresh to load the new bundle.

Remaining manual rehearsal: at 1920×1080 confirm KPIs → compact AI summary → monthly chart; switch the four trend modes, date/line/channel selectors and GWP/NEP switches; run Explain Performance with Cortex on/off, expand supporting evidence, and reopen Ask Tune AI. Verify no horizontal overflow or clipped labels.
