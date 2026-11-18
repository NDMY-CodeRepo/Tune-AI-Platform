# Product-agnostic customer opportunities — 18 November 2026

The React customer workspace now displays the existing `NEXT_BEST_PRODUCT`, rather than assuming Travel. The selected customer drawer shows recorded Motor/Travel holdings, the source candidate, grounded rationale, suggested engagement action, preferred channel and the existing AI-assisted brief. Product and holding filters derive their choices from full Snowflake aggregates, with each choice constrained by the other product filter. KPI totals cover the full candidate segment; the worklist explicitly reports its filtered count and first 200 rows.

No products are inferred. Only consented, nonempty source recommendations are candidates. Recorded Motor/Travel candidates already held (or with unknown holding status) are excluded. Personal Accident, Fire or other source candidate names are presented with an explicit warning that their holdings are unavailable in these attributes; eligibility, suitability and propensity remain unestablished. No Motor/Travel holdings does not imply the customer holds no other products.

The original NBO SQL ordering and retention action SQL are reused. `shared/business_logic.py` is unchanged. The legacy NBO API and Streamlit segment remain Motor-to-Travel. The generalized React segment includes additional recorded candidates; this intentionally broadens its count. Retention-first actions, consent checks, human review, evidence-ID-only Cortex responses and deterministic fallback remain in place. No Snowflake writes, schema changes, new dependency, infrastructure, financial or Desk change.

## Live checks

Read-only source aggregation and in-process API checks passed against Snowflake:

| Recorded Motor/Travel holding | Candidate product | Consented candidates |
|---|---|---:|
| Motor | Travel | 10,566 |
| Motor + Travel | Fire | 67 |
| Motor + Travel | Personal Accident | 644 |
| No Motor / Travel recorded | Motor | 5,202 |
| No Motor / Travel recorded | Personal Accident | 3,309 |
| Travel | Motor | 299 |
| Travel | Personal Accident | 7,052 |
| **Total** | | **27,139** |

These are the observed source snapshot results, not hardcoded UI values. The Motor-to-Travel subset reconciles exactly with legacy counts and ordering, including High risk / Top value filters. Retention order, counts and evidence agree with the existing NBA source. Each recorded combination's filtered count and product/holding options reconciles; unsupported/injected filter values return no customers. Live Cortex returned a validated evidence selection for one engagement brief. Unit coverage checks rejected Cortex evidence and deterministic fallback, absent products, denied consent and already-held/unknown Motor/Travel flags.

Evidence: `product_opportunities_live.json`; repeat with `python -m tests.live_product_opportunities` using the configured Snowflake profile. `tests.live_customer_consolidation` delegates to the expanded check.

## Verification boundary

Frontend build, automated regression and presentation tests are run separately. Browser rendering, drawer interactions and hosted startup are **not verified** in this pass. No application server was started or stopped.
