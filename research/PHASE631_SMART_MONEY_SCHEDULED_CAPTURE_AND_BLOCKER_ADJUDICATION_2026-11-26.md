# Phase 631 — Smart Money scheduled-capture and blocker adjudication

**Audit cutoff:** 2026-11-26 04:20 UTC  
**Main HEAD at preflight:** `8507184eaa47dd9cfa7b2d0f93cff6a6054c2505`  
**Disposition:** FINRA/CFTC scheduled jobs are operational, but no FINRA rows were admitted; SEC 13F live capture is blocked because the scheduled job receives an empty `SEC_USER_AGENT`. No new signal, return test or strategy change.

## 1. Preflight

- Actions inventory: 8,311 total runs; latest 100 = 71 success / 18 failure / 11 cancelled; zero queued, waiting or in-progress.
- Latest runs inspected with jobs, logs and artifacts. No workflow was dispatched, rerun, cancelled or duplicated.
- Open PRs relevant to this line: #241 (13D/G, Draft), #240 (Form 4 entity duplicate semantics, Draft), #235 (Form 144/Form 4 acceptance clock, Draft), and stacked 13F audit PRs #230–#227. PR #242 / Phase 629 is merged.
- Main is at `8507184`, the scheduled Phase 469 metadata-diagnostic commit. The next Phase 614 cron slot is 04:41 UTC; no manual run was started.

## 2. SEC 13F — material credential blocker

Scheduled run [45751086501](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45751086501) on main (2026-11-26 03:46:56 UTC):

- `offline-regression`: 36/36 passed.
- `live-capture`: failed before any SEC request.
- The job log shows the injected `SEC_USER_AGENT` environment value is empty; the collector raised `SEC_USER_AGENT is missing or invalid; no SEC request was made.`
- No state/ledger write occurred and no artifact was produced.

PR [#242](https://github.com/jafelix81/NuevaEstrategia/pull/242) is merged (commit `d81c2c65`); it correctly maps `secrets.SEC_USER_AGENT` into the job and fails closed. The remaining issue is secret availability/configuration, not parser code. A maintainer must verify that the repository Actions secret is named exactly `SEC_USER_AGENT` and is available to scheduled workflows. If the value was stored as an Actions variable or environment-scoped secret instead, it is not exposed by the current workflow's `secrets.SEC_USER_AGENT` mapping. Do not put the contact value in logs or commit it.

## 3. FINRA Reg SHO — latest live diagnostic still quarantined

Run [45754121648](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45754121648), artifact [15086513251](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45754121648/artifacts/15086513251):

- Both offline regression and live capture completed successfully.
- Eight requested trade-date files returned HTTP 200; all eight were rejected by the duplicate-symbol / overlapping-facility guard.
- Two repeated symbols per file: BCPC and TPC; 16 duplicate-symbol occurrences / 16 extra rows across the eight files.
- No exact duplicate raw rows were found. Facility token sets overlap, including rows with `B,N,Q` versus `N,Q` or `Q`; TPC also has same-token-set rows with different raw hashes.
- Zero valid files, zero first-seen events, zero research-eligible observations and zero signal-eligible observations. Raw rows and volume values were not persisted; the FINRA file-state map remains unchanged.

This is consistent with the unresolved Phase 539/590/594 issue. Keep the parser fail-closed. Do not sum, drop, max-select or deduplicate BCPC/TPC from ticker/facility overlap alone. The bounded FINRA Query API `regShoDaily` cross-check remains the preferred next adjudication, but Phase 590 requires authorized credentials and a use-right check before querying. No credentials were used or requested here.

## 4. CFTC TFF — stable, but still only a broad positioning panel

Run [45753716471](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45753716471), artifact [15086462804](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45753716471/artifacts/15086462804):

- 3,043 rows, no new reports or revisions; latest report date 2026-11-17.
- Coverage: DJIA, E-mini S&P 500 and Nasdaq Mini from 2010-07-20 (853 observations each); Russell E-mini from 2017-08-15 (484).
- Natural report cadence is semiweekly/irregular in parts of the history. Weekly 4/52-report features remain suppressed unless a separately preregistered cadence specification is adopted.
- Zero historical signal-eligible rows; no event or trade signal generated.

Treat TFF as a possible market-regime/crowding covariate, not security-level institutional flow. Do not infer stock-specific smart money from index-futures positioning.

## 5. SEC Form 144 / Form 4

- Form 144 run [45747356670](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45747356670): 82 new canonical events from 84 feed observations, 82 XML resolutions; cumulative ledger 815 accessions / 5,443 detail rows. The poll intervals are bounded, but exact public-availability certification remains 0 and signal eligibility remains 0. The Phase 549 10b5-1 classification is descriptive only; proposed sales are not executions.
- Form 4 run [45714679017](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45714679017): 415 new accession events / 912 entity observations; structured transaction/footnote enrichment remains descriptive, with zero signal-eligible rows.
- PR #240 remains Draft despite passing its offline regression suite. Its entity-key correction is not yet in main; do not reinterpret the legacy accession-repeat count as entity duplicates.

## 6. SEC 13D/G

PR [#241](https://github.com/jafelix81/NuevaEstrategia/pull/241) remains open/Draft. The latest run [45733913256](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45733913256) passed 30/30 offline tests; `live-sample` was skipped because no manual dispatch with `run_live_sample=true` occurred. The 44-header identity sample is still pending. The same `SEC_USER_AGENT` availability gate applies. No broad crawl or return test is authorized.

## 7. Phase 20C and model controls

- Phase 593 remains authoritative: current same-day-close Phase 20C is NO-GO because FINRA daily short-volume is published after the regular session; same-day-close entry is look-ahead.
- The next-open successor remains untested. Phase 594 identifies missing live first-receipt-to-Phase-468 wiring and incomplete 335-name adjusted-price/terminal-return coverage (seven inactive/renamed/acquired names remain unresolved).
- Earlier Phase 20C pseudo-OOS results are small and unstable; the final six-date holdout remains sealed.
- Options, OPRA/Open-Close, IvyDB, ThetaData and MIDAS remain feasibility-only; no sample or license was obtained. Options-data budget remains USD 0.

## 8. Final disposition

- New signals admitted: **0**.
- Incremental alpha / valid OOS / bootstrap / LOO result: **0**.
- No universe, exposure, cost, parameter, holding-period, holdout or production change.
- `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen.

**Next gates:** restore the exact repository Actions secret `SEC_USER_AGENT`; then complete the bounded 13D/G sample. Separately, resolve FINRA BCPC/TPC with the authorized `regShoDaily` facility-grain cross-check before enabling any Phase 468 labels. Keep all source interpretations as hypotheses.
