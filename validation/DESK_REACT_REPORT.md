# Data Service Desk React frontend — 16 November 2026

Implemented the separate Service Desk React frontend using the repository's existing React/Vite dependencies and local Python API. No replacement database, schema migration, container, access grant or financial change. Streamlit remains available as the working fallback.

- UI: business overview with recent requests, awaiting-response highlights and latest visible updates; guided request/review form; selectable request queues and filters; team workload bars; prominent conversation and separate management/resolution sections; searchable catalogue.
- API: isolated `/api/desk` router delegates all mutations to the existing `create_ticket` / `change_ticket` methods. UUID retry tokens, sequence references, version checks and atomic activity writes are retained. The client keeps its loaded version until save/refresh, shows stale responses explicitly, and disables pending action buttons.
- Presentation: white/neutrals, red accents, navy text, regular/medium weights, compact controls and responsive layouts. Existing AI frontend files and their pending work were retained.
- Boundaries: `/desk` is a separate HTML entry and navigation. It shares the existing server and dependency/build setup with `/`. Typed role/identity switching is a demo workflow control, **not authentication or production authorization**. No attachments, notifications or new AI behavior.

## Verification

| Check | Result |
|---|---|
| Existing + new Python suite | PASS — 149 tests |
| Vite production build | PASS — both intelligence and desk HTML/assets generated |
| API role/requester guards | PASS — requester mutation fields and other-requester history rejected |
| Submit → triage/assign → clarification → BU response → resolve → BU resolution visibility | PASS against live Snowflake through HTTP adapter |
| Request fields / retry token | PASS — all new request fields and idempotent retry verified |
| Internal note filtering | PASS — internal text absent from BU response payload |
| Stale version | PASS — HTTP 409; no mutation |
| Competing HTTP writes | PASS — one success, one 409 |
| History failure | PASS — API returns sanitized 503 and ticket version rolls back |
| Reopen / closure | PASS |
| APP_STATE and GOLD definitions | PASS — before/after recursive schema hashes identical |
| Running server / desk HTML / JS / CSS / metadata / overview | PASS — HTTP 200 on port 8002 |
| Actual browser appearance / keyboard / clicks | BLOCKED — browser access host unavailable |
| Hosted deployment | NOT EXECUTED — local server only |

Live acceptance evidence: `desk_react_acceptance.json`, retained CLOSED request `TDS-000106`. Serving evidence: `desk_react_serving.json`. This is an HTTP/Snowflake workflow verification, not a claim that browser clicks were executed. The existing icon package emitted Vite's `use client` directive warning; the build completed. The existing Starlette/httpx test-client deprecation warning remains; no dependency changes were introduced for it.

Port 8000 was already serving an older API instance, so it was retained. The new local server is available at **http://127.0.0.1:8002/desk**. Port 8502 was not restarted. To relaunch after stopping the current local process, run `./launch-react.ps1 -Port 8002`.

Reproduce with the existing Snowflake connection environment:

```powershell
npm.cmd --prefix apps/ai-intelligence-react run build
.\.venv\Scripts\python -m pytest -q
.\.venv\Scripts\python -m tests.live_desk_react
```

The live acceptance adds one explicitly labelled `[Validation]` ticket per run and retains it closed. It never runs migrations or seed scripts. No live report links are invented.


## Demo sidebar and requesting functions

Identity and record scope controls are retained under collapsed **Demo settings**. A short demo/no-authentication notice remains visible; the technical Snowflake/history explanation is removed from the main sidebar.

The React form now offers Finance, Claims, Underwriting, Actuarial, Sales & Distribution, Partnerships, Customer Experience, Technology, People & Culture, Risk & Compliance, Corporate Strategy and Other. This is a demo shortlist informed by [Tune Protect's published functions](https://www.tuneprotect.com/my/corporate/group/about-us/), not an approved internal business-unit directory. Motor and Travel remain data domains. Historical BU values remain unchanged and available in queue filters. The existing Streamlit fallback and core workflow rules are unchanged.

Verification: frontend production build PASS; 149 tests PASS; running metadata/assets on port 8002 checked. No migration or ticket writes were required. Browser appearance remains unverified. Evidence: `desk_business_units.json`.
