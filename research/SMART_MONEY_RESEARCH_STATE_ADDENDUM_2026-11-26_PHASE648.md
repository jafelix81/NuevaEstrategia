# Smart Money Research State Addendum — Phase 648

**Audit cutoff:** 2026-11-26 19:23 UTC  
**Base main HEAD:** `fd3c3e6c190e329a5f2ad69941edbe83bb2ca1a8`  
**Branch:** `phase648-cftc-russell-reproducible-feature-pipeline`  
**Disposition:** implement a reproducible offline Russell CFTC feature pipeline. CI status is pending until the PR workflow completes.

## Current state

- Phase 646 preregistration remains fixed.
- Phase 647's two prospective Russell observations remain reproduced at 40.625% and 45.4167% of the frozen 480-row reference distribution; neither reaches the fixed 80th-percentile high-crowding state.
- Phase 648 adds frozen Git-blob checks, raw-event hash/OI validation, strict UTC first-seen checks, duplicate/chronology guards, deterministic mid-rank construction, offline regression tests, and a PR-only JSON artifact.
- Historical CFTC archive rows remain unverified for historical availability and are used only as a fixed pre-sample reference. They are not signals, training labels, or return observations.
- No Russell price or outcome data have been accessed. The permitted adjusted-OHLC/VIX source gate remains open.

## Actions / operational preflight

- 8,350 total Actions runs; latest 100 inspected; none active or queued.
- Latest scheduled SEC runs: Form 4 [45848689364], 13F [45839454376], Form 144 [45827105431]. Their jobs completed successfully and artifacts remain unexpired.
- Latest CFTC scheduled run [45753716471]: no new reports/revisions.
- Latest FINRA Reg SHO scheduled run [45754121648]: eight files rejected by the BCPC/TPC integrity gate; zero rows admitted.
- No manual dispatch, rerun, or duplicate poll.
- No existing Phase 648 branch/PR was present at preflight.

## Next gates

1. Require Phase 648 offline PR workflow to pass before merge.
2. Preserve the fixed reference Git blob identities and Phase 646 threshold.
3. Continue natural CFTC first-receipt capture; do not backdate report dates.
4. Freeze a permitted, reproducible adjusted Russell proxy OHLC and VIX source before inspecting any forward outcome.
5. Continue collecting until the preregistered matured-training and evaluation sample gates are met; do not relax them.

## Strategy controls

- Signals admitted: **0**.
- Incremental alpha versus LTM/F80: **none demonstrated**.
- New OOS / bootstrap / LOO: **0**.
- Holdout remains sealed.
- `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen.
- No universe, parameters, exposure, costs, capital, holding-period or production changes.
- Options-data budget remains **USD 0**.
