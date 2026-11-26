# Smart Money Research State Addendum — Phase 641

**Date:** 2026-11-26  
**Main checkpoint:** `a0e82e350337df0d9c12032a659f683292e3f162`  
**Disposition:** infrastructure/data-quality progress only; no new investment signal or alpha evidence.

## Current operational state

- Latest 100 Actions runs: 71 success, 17 failure, 12 cancelled; zero queued/in-progress.
- Latest scheduled Form 4 run [45759597509](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45759597509) succeeded with 90 new canonical events and 192 entity observations, but predates PR #240's 06:40 UTC merge. The Phase 626 duplicate-audit sidecar has not yet been validated by a natural post-merge capture.
- Latest scheduled Form 144 run [45747356670](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45747356670) succeeded with 82 new accessions and 534 structured detail rows, but predates Phase 638/639. Post-merge live validation remains pending.
- Latest scheduled 13F run [45751086501](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45751086501) failed before any SEC request because the old run commit received an empty `SEC_USER_AGENT`. Phase 635's fallback is now merged; post-merge natural validation remains pending.
- CFTC TFF [45753716471](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45753716471) found no new report or revision; the ledger remains 3,043 rows (3,035 unverified archive proxies + 8 prospective observations).
- FINRA Reg SHO [45754121648](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45754121648) received eight HTTP-200 files, rejected all eight for BCPC/TPC duplicate-symbol ambiguity, and admitted zero observations.

## Priority order

1. Obtain a maintainer check of GitHub Actions workflow enablement/scheduled-workflow permission. The connected read interface cannot inspect that administrative setting. Do not dispatch, rerun or change cron until confirmed.
2. Validate the next natural post-merge Form 4 capture, including `entity_duplicate_audit.csv`.
3. Validate the next natural post-merge Form 144 capture against the Phase 638/639 interval and timezone guards.
4. Validate the first natural post-Phase 635 SEC 13F poll; no secret change is currently requested.
5. Keep FINRA Reg SHO and Phase 20C quarantined until authoritative row-grain/security identity and next-session executable inputs exist.
6. Continue CFTC prospective collection; do not use unverified historical archive timestamps as PIT.
7. Keep SEC MIDAS and options work at feasibility/rights gates; no purchase, vendor contact or quote request. Options-data budget remains USD 0.

## Quantitative controls

- New signals admitted: **0**.
- Incremental alpha versus frozen LTM/F80: **none demonstrated**.
- New valid OOS / bootstrap / LOO: **0**.
- Final holdout: sealed.
- `F80_TOP20_PARTIAL50_BASELINE_C20`: **frozen**.
- Universe, parameters, exposure, costs, holding-period policy and production: unchanged.

See [Phase 641](PHASE641_SMART_MONEY_POSTMERGE_CAPTURE_AND_OPERATIONAL_ADJUDICATION_2026-11-26.md) for the full run, job, artifact, branch and source adjudication.
