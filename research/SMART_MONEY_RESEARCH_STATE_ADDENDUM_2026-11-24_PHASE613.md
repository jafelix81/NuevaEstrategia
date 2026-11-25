# Smart Money Research state addendum — Phase 613

**Audit cutoff:** 2026-11-25 04:12 UTC  
**Branch:** `phase613-sec-13f-legal-dissemination-floor`  
**Base:** Phase 612 branch; no production merge.

## Completed
- Added a legal Filing Date 06:00 ET floor to the observed 13F knowledge clock.
- Added a fail-closed guard for same-day first-seen observations after 17:30 ET acceptance.
- Preserved the end-of-Filing-Date fallback when no prospective first-seen exists.
- Kept the guard specific to 13F; Form 4/144 clocks are not changed.
- Added offline regression coverage for after-hours, exact-cutoff, legal-floor, and weekend cases.

## Current source state
- SEC 13F: historical accession/holdings joins are structurally viable, but effective-dated security identity and F80 historical coverage remain insufficient. No prospective 13F collector is present on main.
- SEC Form 4: latest persisted poll 45533818624 completed successfully; current data remain descriptive only and first-seen intervals are bounded poll intervals, not exact public availability.
- SEC Form 144: latest persisted poll 45523407949 completed successfully; proposal notices and compensation/tax context remain non-signal evidence.
- FINRA Reg SHO: fail-closed; no accepted market rows.
- CFTC TFF: no incremental stock-level signal; context-only.
- Options: no purchases or quote requests; authorized initial budget remains USD 0.

## Decision
Phase 613 is a point-in-time control improvement only. It does not create a signal, run a backtest, or justify a strategy change. `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen.
