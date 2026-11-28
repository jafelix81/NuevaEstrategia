# Smart Money Research — state addendum (Phase 680)

**Updated:** 2026-11-28 UTC  
**Main HEAD before Phase 680 documentation:** `32f993f6a2846e4022e10de4059ccf7f032d9c43`.

## Phase 680 — AMS Capital full 13F value-unit reconciliation

- Revisited SEC accession `0001717977-26-000005` (AMS Capital Ltda), filed 2026-11-27 and accepted 14:32:31 ET for 2026-09-30.
- The SEC-rendered cover reports 15 entries and a nearest-dollar total of 289,276; all 15 rendered information-table rows sum to the same amount.
- Expanded the Phase 677 seven-row retrospective screen to all 15 positions using same-report-date secondary close references. Under a factor of 1,000, 15/15 rows are within 0.5%; median absolute relative error 0.001040%, maximum 0.005509%.
- The 15 shares × same-date close values total $289,275,024.30 versus $289,276,000 implied by the filed values × 1,000; aggregate difference $975.70 (0.000337%).
- Factor 1 has 0/15 rows within tolerance; median absolute relative error is approximately 99.9000%.
- This is a stronger retrospective `LEGACY_THOUSANDS_CANDIDATE` classification for this filing, not a general rule. Phase 671's existing detector remains unchanged and its `COM`/`COMMON STOCK` scope still admits only seven rows; the other eight were manually reconciled but not admitted to that detector.
- SEC filing detail, cover and rendered information table were inspected. The SEC filing index lists raw information-table XML at 8,610 bytes, but raw XML was not downloaded and no raw XML hash was computed.
- No normalization, parser change, production feature, signal, return/alpha test, OOS, bootstrap, LOO or holdout use. F80 remains frozen; spend remains USD 0.

Full report: [Phase 680](PHASE680_AMS_CAPITAL_13F_FULL_15_ROW_VALUE_SCALE_RECONCILIATION_2026-11-28.md). Machine-readable result: [Phase 680 JSON](phase680_ams_capital_13f_full_15_row_value_scale_reconciliation_2026-11-28.json).

## Cross-source state retained from Phase 679

- **Form 144:** natural post-Phase 673 run [46110032075](https://github.com/jafelix81/NuevaEstrategia/actions/runs/46110032075) passed 103/103 tests and both jobs. No new notices; 52 feed observations are poll rows, not economic events. Ledger: 1,104 accessions, 976 structured-detail accessions, 6,360 detail rows, 128 without details; 0 public-availability-certified and 0 signal-eligible.
- **FINRA Reg SHO:** run [46105917821](https://github.com/jafelix81/NuevaEstrategia/actions/runs/46105917821) passed; one prospective date, 327/335 symbols, raw payload not retained, no approved PIT security-master/price panel, 0 signal-eligible rows.
- **CFTC TFF:** run [46105422375](https://github.com/jafelix81/NuevaEstrategia/actions/runs/46105422375) passed; no new report/revision and 3,043 historical rows remain.
- **Form 4:** run [46099559273](https://github.com/jafelix81/NuevaEstrategia/actions/runs/46099559273) passed; 156 new accession observations, 0 signal-eligible.
- **SEC 13D/G:** bounded global-index sample still requires the existing Phase 616 manual dispatch with `run_live_sample=true`; do not create another crawler.
- **13F selector:** PR #262 remains a draft stacked on PR #230 and the Phase 612/613 dependency chain; do not merge out of order.
- **Options/OPRA/Cboe:** no rights-cleared, reproducible historical options source admitted; no vendor contact or purchase.

## Strategy controls

- Signals promoted: **0**.
- Incremental alpha demonstrated: **none**.
- New valid OOS / bootstrap / LOO result: **0**.
- `F80_TOP20_PARTIAL50_BASELINE_C20`: **frozen**.
- No production, universe, parameter, capital, exposure, cost or holding-period changes.
- Data spend: **USD 0**.

## Next priorities

1. Retrieve and hash AMS Capital's raw XML through the authorized SEC User-Agent path, then reconcile all 15 raw rows.
2. Expand the 13F value-unit control sample to at least 20 independent managers, retaining positive and negative controls.
3. Continue the existing Phase 616 manual 13D/G sample when the maintainer performs the required dispatch.
4. Accumulate prospective FINRA observations and resolve raw payload reproducibility plus PIT prices/security identity before any return test.
5. Continue Form 144 detail backfill and Form 4 identity/transaction enrichment without treating filings or poll observations as executable signals.
