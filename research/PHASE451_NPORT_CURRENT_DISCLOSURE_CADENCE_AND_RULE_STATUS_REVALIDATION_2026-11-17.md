# Phase 451 — N-PORT current disclosure cadence and rule-status revalidation

**Audit time:** 2026-11-17 09:30 UTC  
**Disposition:** The 2024 N-PORT monthly-reporting amendments remain delayed; the February 2026 N-PORT proposal remains proposed as of this audit. Continue treating the current public N-PORT holdings panel as quarterly and accession/acceptance-clocked. No cadence change, signal admission, or return test.

## 1. Operational preflight

- Main HEAD: `fda2bd347fbce0eb3dbdce301f08fe533af3961a` (Phase 450).
- Actions total: 7,691. Explicit `in_progress` and `queued` queries returned zero.
- Latest overall run [44009082677](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44009082677): Phase 448 PR CI. `offline-regression` passed 18/18 synthetic tests; `live-capture` was skipped by design. No artifact. The job log contains synthetic partial/failure fixtures only; it is not a live SEC poll.
- Latest main push run [44007937167](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44007937167): Phase 447 client compilation and 14/14 synthetic contract tests passed. No artifact.
- Latest scheduled SEC Form 144 run remains [43970444015](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43970444015). Offline regression passed; live capture failed after four retries on the Form 144/A endpoint with a read timeout. Ledger commit was skipped and no artifact was produced. The Phase 444 partial-feed persistence correction is still not validated by a post-merge live capture.
- Latest CFTC capture remains bootstrap [43525140200](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43525140200): `BASELINE_ALREADY_EXISTS_NO_OVERWRITE`, zero signal-eligible historical rows, artifact [14084802705](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43525140200/artifacts/14084802705). The next configured scheduled capture slot, 2026-11-17 22:25 UTC, had not yet occurred.
- Branches: 285 across three pages (100/100/85); open PRs: 56; workflow files: 69. No workflow was dispatched, rerun, or duplicated.

## 2. Official SEC rule status

### 2.1 The 2024 amendments are not yet in force

The SEC's April 16, 2025 final rule, Release IC-35538 / File S7-26-22, delayed the Form N-PORT amendments adopted August 28, 2024:

- The effective date for the Form N-PORT amendments and amendatory instruction 2 was moved to **November 17, 2027**.
- The effective date for amendatory instruction 3 was moved to **May 18, 2028**.
- Compliance dates were moved to November 17, 2027 for fund groups with at least USD 1 billion in net assets, and May 18, 2028 for smaller fund groups.

The delay is a final rule, not a proposal. The separate N-CEN effective date is not a Form N-PORT holdings-cadence change.

Official source: https://www.sec.gov/rules-regulations/2025/04/s7-26-22

### 2.2 The February 2026 proposal remains proposed

The SEC's February 18, 2026 proposal, Release IC-35962 / File S7-2026-05, would provide an additional 15 days to file monthly portfolio reports and restore quarterly public publication. The SEC's current Rulemaking Activity index, reviewed November 17, 2026, still lists S7-2026-05 as **Proposed Rule**, not Final Rule.

Official sources:
- https://www.sec.gov/rules-regulations/2026/02/s7-2026-05
- https://www.sec.gov/rules-regulations/rulemaking-activity

A proposal does not change the operative reporting or public-availability clock. Do not implement its proposed 15-day extension, monthly filing cadence, or quarterly-publication language as if adopted.

## 3. Consequences for the research panel

1. Keep the existing N-PORT research panel at quarterly public-observation grain for the current regime; do not create monthly observations by interpolation or assume a monthly public tape.
2. Continue to timestamp each accession/amendment by its own EDGAR acceptance/first-public timestamp. Never backdate a position to the report period end.
3. Treat the 60- and 64-calendar-day report-to-filing lags observed in the two Phase 313 short-position filings as case-specific diagnostics, not a population estimate.
4. Keep amendments as separate vintages. A later amendment cannot rewrite the information set available at the original filing date.
5. Before any future cadence transition, re-check the SEC rulemaking status and actual filing/publication behavior; if a final rule changes the cadence, create a new regime boundary rather than stitching monthly and quarterly observations.
6. The Phase 450 finding remains unchanged: the 56-filing sample is deterministic and non-representative; N-PORT amendment-delta-as-flow is killed for the observed Otter Creek pair; quarterly short-position levels remain low-priority delayed context only.

## 4. Research disposition

- No N-PORT source or signal admitted.
- No new raw SEC data acquired.
- No return, alpha, OOS, bootstrap, LOO, or holdout test run.
- No new sample, cadence conversion, or monthly backfill created.
- `F80_TOP20_PARTIAL50_BASELINE_C20`, universe, parameters, capital, exposure, holdout, and production remain frozen.

## 5. References

- SEC 2025 final rule IC-35538: https://www.sec.gov/rules-regulations/2025/04/s7-26-22
- SEC 2026 proposed rule IC-35962: https://www.sec.gov/rules-regulations/2026/02/s7-2026-05
- SEC Rulemaking Activity index: https://www.sec.gov/rules-regulations/rulemaking-activity
- Phase 450 N-PORT amendment-delta disposition: https://github.com/jafelix81/NuevaEstrategia/blob/main/research/PHASE450_NPORT_SHORT_POSITION_AMENDMENT_DELTA_DISPOSITION_2026-11-17.md
