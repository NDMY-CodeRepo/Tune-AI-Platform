# Customer tab presentation refinement — 18 November 2026

## Three distinct business questions

- **Customer Priorities — Where should we focus?** Portfolio KPIs, a retention summary, a Motor-to-Travel opportunity summary, compact portfolio risk/value distributions, and clear links to the two worklists. The individual customer table, profile and brief are not rendered in this management view.
- **Retention Actions — Who should we retain?** Existing NBA order/filtering/selection, with risk, customer value, renewal month, the SQL-calculated upcoming-renewal flag and recommended action. The profile leads with the retention action and supporting renewal/risk/value context; additional cross-sell context is secondary.
- **Cross-Sell Opportunities — What should we offer?** Existing NBO ranking and customer selection, with a product-led Travel Insurance profile, eligibility-review notice, customer value, preferred channel, product evidence and an engagement brief. Retention action is not a primary table column or profile headline. The original engagement action remains visible, including retention-first guidance for high-risk candidates; full retention context remains accessible.

## Preserved contracts

No backend, API, Snowflake SQL, model, marketing-consent rule, recommendation rule, schema, dependency or infrastructure was modified. Executive Intelligence and Data Service Desk source files were preserved. Existing customer API requests and the engagement-brief request/response/AI fallback behavior remain in use.

Overview distributions sum the existing `CUSTOMERS` cells from the API’s `segments` aggregate, grouped by risk or value. They do not count the bounded `rows` worklist or derive new opportunity definitions. Bar lengths compare counts, without inventing conversion, revenue, propensity or eligibility measures. Invalid/missing aggregate counts withhold the breakdown. Full-portfolio and cross-sell counts remain separate and overlapping; they are not added.

Renewal timing displays the existing `UPCOMING` SQL flag. Null/unknown timing remains “Timing unavailable” rather than “Outside renewal window”. Product display remains conditional on the existing supported offer. Existing ranking, facts, recommended engagement actions and human-review requirements remain intact.

## Verification

- **PASS:** React production build with existing dependencies.
- **PASS:** 149 Python tests. The existing non-blocking Starlette test-client deprecation warning remains.
- **PASS:** 12 Node presentation tests, including five new aggregate/renewal checks. They cover full aggregate-cell grouping, protection against using bounded customer rows, missing/invalid counts, unknown bands, source zero counts and SQL-derived renewal timing.
- **PASS:** 29 source-preservation comparisons for backend/shared logic/SQL, Desk files and Executive frontend components. Evidence: `customer_tab_distinction_baseline.json` and `customer_tab_distinction_preservation.json`.
- **PASS:** `git diff --check`; no package or dependency changes.
- A historical UI preservation test compared mixed CR/CRLF endings literally; its comparison now normalizes line endings while retaining exact source-text checks. Financial/business-rule guards were not relaxed.
- **NOT EXECUTED:** browser visual/interaction review or screenshots, a new live Snowflake reconciliation, live Cortex calls, ticket mutations or deployment. Current figures remain API-driven; historical counts are not used as application constants. Build/unit checks do not establish browser rendering.

Evidence: `customer-tabs-build.log`, `customer-tabs-presentation-tests.log`, `tests/customer_views.test.mjs` and the preservation files above. The refinement does not start or stop local application servers.
