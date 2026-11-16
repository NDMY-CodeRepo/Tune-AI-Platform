# Customer Intelligence consolidation — 16 November 2026

## Delivered scope

The active local React app has two sidebar entries: **Executive Intelligence** and **Customer Growth & Retention Intelligence**. Customer Intelligence contains **Customer Priorities**, **Retention Actions** and **Cross-Sell Opportunities**. Legacy React `#NBA`/`#NBO` bookmarks open the matching tabs. The Streamlit fallback retains its legacy screens; its code was not changed.

Customer Priorities and Retention Actions use the existing NBA query/order, while Cross-Sell Opportunities uses the existing NBO query/order. The consolidated table adds the already-calculated retention action and a supported Travel candidate, without combining two overlapping ranked lists. Each table contains unique customer IDs. Portfolio and cross-sell counts retain their original full-scope meaning; overlapping categories are explicitly labelled and never added.

One shared profile now displays customer risk/value, the existing retention action, a candidate Travel offer only when supported, renewal/channel/consent/holdings, and separate expandable retention/offer evidence. A combined engagement brief preserves the retention action first, reuses existing evidence, and retains Cortex fact-ID validation and deterministic fallback. An unsupported offer is shown explicitly rather than inferred from `NEXT_BEST_PRODUCT` alone.

## Backend boundary

Existing `customer_query`, `ACTION_SQL`, `RENEWAL_SQL`, `CANDIDATE_WHERE`, `customer_evidence`, Snowflake connection/cache utilities and original API routes remain unchanged. A thin presentation adapter (`/api/customer-intelligence` and `/api/customer-intelligence/brief`) reuses those existing queries/evidence. It checks the displayed IDs against the unchanged consent-based candidate SQL predicate using bound parameters. This is needed because intersecting two top-200 lists would miss qualified retention customers. No recommendation engine, schema, table, model or pipeline was introduced or modified.

Customer detail is validated against membership in the selected bounded worklist before generating a brief. Cortex can select only server-built, validated fact IDs; no model-generated customer claims, prices, propensity or eligibility are displayed. No messages or ticket operations are performed.

## Verified

- **PASS:** React production build, Python compilation and `git diff --check`.
- **PASS:** 137 pytest tests, including nine focused consolidation checks. They cover supported/unsupported offers, retained evidence, retention-first action, bound membership lookup, tab-to-existing-query mapping, protected brief selection, rejected-AI fallback and source preservation.
- **PASS:** live HTTP checks for all three tabs and High/Top filters. Row IDs/order/attributes and counts match the original NBA/NBO APIs exactly, with only a candidate-offer display annotation added.
- **PASS:** every displayed customer’s offer membership matches the four validated source attributes, and retention/offer facts match the existing `customer_evidence` function. No duplicate IDs appear in a worklist.
- **PASS:** unique portfolio **179,725**; independent NBO count **10,566**. These are source observations, not UI constants or added category totals.
- **PASS:** the first 200 priorities include **66** qualified customers absent from NBO’s first 200; membership lookup preserves those supported offers.
- **PASS:** a customer with no supported offer gets a retention-only deterministic brief; a qualified customer gets a live Cortex combined brief with the original retention action first. Unknown worklist IDs are rejected.
- **PASS:** existing `tests.live_nbo` gate: live unique count, filters, source attributes, Cortex brief, Streamlit fallback and AI-off behavior.
- **PASS:** all eight existing NBA rule/window SQL fixtures from `tests.live_workflows.py` ran independently; its ticket-mutating steps were not executed.
- **PASS:** existing `tests.live_react_api` checks for NBA/NBO source equality, filters, original briefs and financial API regression.
- **PASS:** baseline hashes for business logic, Snowflake service, Executive chat and Data Service Desk match. Existing Executive frontend function bodies match byte-for-byte. The required sidebar navigation change is limited to presentation/routing.

Evidence: `customer_consolidation_live.json`, `customer_consolidation_baseline.json`, `customer-consolidation-live.log`, `customer-existing-nbo.log`, `customer-existing-nba-rules.log`, `customer-existing-api.log`, `customer-consolidation-build.log`.

## Remaining boundary

Browser inventory was retried and returned no apps/browsers, with the native pipe and browser host unavailable. Visual geometry, tab/keyboard interactions and screenshots are **not verified** by the build/API checks. The main local app remains at http://127.0.0.1:8000; refresh to load the new bundle. No hosted/container deployment, GOLD changes or ticket writes were performed. Existing non-blocking bundle-size/Lucide notices and the Starlette test-client deprecation warning remain as documented in `REACT_REPORT.md`.
