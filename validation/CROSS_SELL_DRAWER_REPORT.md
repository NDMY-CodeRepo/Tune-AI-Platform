# Cross-sell recommendation drawer — 18 November 2026

Cross-Sell Opportunities now gives the ranked candidate list the full content width. No customer is automatically selected on that tab. Clicking a customer ID or row opens a right-hand drawer containing the existing Travel recommendation, eligibility-review notice, supporting product/customer evidence, engagement approach and AI-assisted engagement brief.

The drawer uses the browser’s native modal dialog: a persistent close button and Back to candidates action, Escape handling, backdrop-click closing, background scroll locking and focus handling tied to the selected customer button. On small screens it uses the full viewport width. Product details and brief scroll within the drawer, avoiding the prior tall sidebar and blank page area. Closing clears the cross-sell selection while keeping the underlying list/filter/search context.

The existing `CrossSellProfile` and `UnifiedBrief` components are reused without changing their content, API calls, facts, actions or fallback behavior. Retention Actions retains its existing default selection and side-by-side profile. Customer Priorities and Executive Intelligence are unchanged.

Verification:

- **PASS:** production frontend build with existing dependencies.
- **PASS:** 222 Python tests and 12 Node presentation tests. Existing non-blocking Starlette test-client and build notices remain.
- **PASS:** 37 preservation checks for backend/shared/SQL/Desk source files and the reused profile/brief, retention, overview and Executive components.
- **PASS:** `git diff --check`.
- **NOT VERIFIED:** browser rendering, focus restoration, backdrop/keyboard interaction and responsive screenshots. The build/regression checks do not establish these browser behaviors.
- No app-server process was started or stopped. No backend, database, recommendation, ranking, consent, eligibility or financial logic was changed; no new dependency or infrastructure was added.

Evidence: `cross_sell_drawer_baseline.json`, `cross_sell_drawer_preservation.json`, `cross-sell-drawer-build.log`, `cross-sell-drawer-presentation-tests.log`.
