# Phase 473 — FINRA Phase 20C price-provider response classification audit

**Audit cutoff:** 2026-11-18 07:16 UTC  
**Base main:** \`cdb6f13ab4fab8929c211430f90d86af9dad869b\`  
**Disposition:** one of the seven missing Phase 20C symbols (ROKU) now returns 2,280 valid close/adjusted-close observations from both Yahoo chart hosts, enough to exceed the frozen 220-row minimum. This is a candidate to resolve the 328/329 price-history blocker, but the exact Phase 11/yfinance pipeline has not yet been revalidated and no fallback is admitted. Stooq and Nasdaq results are now correctly classified by control behavior and API response metadata.

## 1. Repository and Actions preflight

- Main HEAD: \`cdb6f13ab4fab8929c211430f90d86af9dad869b\` (Phase 472 / PR #133 merged).
- Actions total at preflight: 7,771. Latest 100: 79 success, 15 failure, 6 cancelled; 0 active/queued.
- Branches: 304 (100 + 100 + 100 + 4 across four REST pages).
- Open PRs: 56; workflow files: 78.
- Latest mainline CI runs [44248336010](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44248336010) and [44248336008](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44248336008) completed successfully for PR #133, which merged at 06:02 UTC.
- No workflow was dispatched, rerun or duplicated before Phase 473. The new Phase 473 branch push created its own single diagnostic workflow; the later second push triggered a queued duplicate because the script and test files were committed separately. Both are sequential under the same concurrency group; no overlapping live probe is permitted.

### Relevant live captures

- SEC Form 144 run [44228413864](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44228413864), job 134547264687, succeeded; artifact [14393319006](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44228413864/artifacts/14393319006), SHA-256 \`dd3cae9e7e224491fa32ffaee34b56f3ab6211f57a3bf0384165d5cda1e96775\`. Its inspected summary contains 90 new Form 144 accessions and 109 feed-observation rows, but both feeds still have \`INITIAL_BASELINE_NO_LOWER_BOUND\`, null lower bound, zero research-eligible and zero signal-eligible observations. Pagination watermark is found and no feed-window gap is reported. The 90 records are not PIT-admissible.
- CFTC TFF run [44232546204](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44232546204), job 134560838218, succeeded; artifact [14395926632](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44232546204/artifacts/14395926632), SHA-256 \`e4d9a147e920e3333b1d684a477ac77ef68a1364e9b028c2e3381a34ece795e7\`. It records four first-receipt report events for positions dated 2026-11-10, observed at 2026-11-18 03:44:57 UTC. No derived signal or forward return is attached. The scheduled run was delayed materially.
- FINRA Phase 469's first post-merge scheduled slots (22:30 and 23:30 UTC weekdays) were still ahead at this audit cutoff. No live FINRA capture is claimed.
- SEC Phase 403 has an hourly :47 cron. The only post-upgrade scheduled run visible at cutoff is 44228413864 at 03:09 UTC. No subsequent scheduled SEC run was visible through 07:16 UTC; treat this as a delivery gap to monitor, not proof the workflow is disabled.

## 2. Phase 381 artifact re-adjudication

Inspected Phase 381 PR #57 and downloaded its metadata-only artifact [14073108228](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43500356535/artifacts/14073108228), ZIP SHA-256 \`c88e350c188e513e9ac7995aad859ec1b02040e7a2f9586ce1f063bf7f6537ef\`.

For 2016-10-24 through 2026-10-23:

| Provider | Four controls (AAPL/MSFT/NVDA/SPY) | Seven missing names (AVB/EA/EQR/LPRO/ROKU/WBD/WBS) | Adjudication |
|---|---:|---:|---|
| Yahoo query1/query2 (13 Nov) | 2,514 rows each | 0 each | Controls validated; seven empty chart results on that capture date |
| Stooq | 0 each; parser raised \`ValueError\` | 0 each; same failure | Method unvalidated; old artifact omitted HTTP status/content type |
| Nasdaq US-slash date format | 0 for all | 0 for all | Method unvalidated; old artifact omitted API error details |

The Phase 381 report must not be read as proving Stooq/Nasdaq lacked historical data. Their controls failed too, so those were provider-method/access/schema failures rather than negative coverage evidence.

## 3. Phase 473 live metadata-only probe

Workflow [44256736433](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44256736433) completed successfully. The first pass exposed a diagnostic issue: it counted timestamps without requiring a valid close. That output was superseded and not used to claim price history.

The corrected script was run in [44256975655](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44256975655), with offline regression successful and live metadata probe successful. Artifact [14405593899](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44256975655/artifacts/14405593899), SHA-256 \`1ea4cab0e7af7d146a300a5d438fcea2e80919fd934cf8aa46ec32d38c4ba645\`.

### 3.1 Yahoo — ROKU recovered as a candidate

Both query1 and query2 returned:
- 4/4 positive controls with valid close observations;
- ROKU: 2,280 positive finite Close values and 2,280 adjusted-close values;
- ROKU dates: 2017-09-28 through 2026-10-23;
- Yahoo metadata identifies ROKU as \`NMS\` / \`EQUITY\`, with first-trade date 2017-09-28;
- the other six target symbols (AVB, EA, EQR, LPRO, WBD, WBS) still returned no chart timestamps/close rows on both hosts.

ROKU is in the frozen 335-symbol universe and 2,280 rows exceed Phase 11's 220-row minimum. This is a meaningful candidate to restore the single missing valid history (328/329 → potentially 329/329), but that count is **not yet certified**. The exact \`yfinance.download(period="10y", interval="1d", auto_adjust=False)\` path used by Phase 11 must be re-run for ROKU, with the same feature builder and no prices persisted. The two Yahoo hosts are mirrors, not independent providers; they do not constitute independent-source return concordance.

The six other symbols have Yahoo metadata identifying the expected ticker/exchange/instrument type, but the API returned empty result arrays. Some returned a suspicious generic \`firstTradeDate\` of 2026-07-17; do not treat that metadata as a reliable listing date.

### 3.2 Stooq — HTML, not CSV

The endpoint returned HTTP 200 but \`text/html; charset=utf-8\`, 796 bytes, for both controls and missing names. No \`Date,Close\` CSV schema was present. This is an access/response-format failure; Stooq remains unvalidated, not a negative history result.

### 3.3 Nasdaq historical API — date format fixed, target coverage still absent

The original US-slash parameters (\`10/24/2016\`) returned HTTP 200 with embedded API \`rCode=400\`, error code 1011: \`Bad or No parameter fromdate\`.

Using ISO dates (\`2016-10-24\` / \`2026-10-24\`) returned \`rCode=200\` and 2,496 rows for AAPL, MSFT and NVDA (3/4 controls; SPY is rejected as \`Symbol not exists\`, consistent with an equity-only endpoint). All seven target symbols were rejected with embedded error code 1001, \`Symbol not exists.\`, including ROKU. Thus the corrected Nasdaq method works for three controls but supplies none of the seven missing histories.

The current metadata script lexicographically sorts Nasdaq's \`MM/DD/YYYY\` date strings and reads \`totalRecords\` from the wrong object level. Therefore it does **not** certify the true Nasdaq first/last date or total-record metadata. Do not infer a complete 10-year date range from the 2,496 count. A future parser correction must normalize dates chronologically and read \`data.totalRecords\`.

## 4. Phase 20C status and branch hygiene

- PR [#57](https://github.com/jafelix81/NuevaEstrategia/pull/57) remains Draft/open, based on \`phase380-cftc-tff-full-postlaunch-archive-census\`, not main.
- Its head \`phase381-finra-price-provider-fallback-audit\` is 211 commits ahead and 205 behind current main. Do not merge it directly or rebase its entire stacked history blindly.
- Legacy \`phase20c-finra-walkforward\` is 12 commits ahead and 314 behind current main. Its original helper uses signal-date close as entry, not executable for FINRA data received after close. The later next-session-open retest is the relevant line.
- ROKU is explicitly present in the frozen 335-symbol Phase 11 universe. The exact Phase 11/yfinance pipeline remains the required next check before updating the 328/329 count.
- No tickers may be dropped, imputed or mixed across providers without effective-dated identity, corporate-action reconciliation and independent-source price concordance.

## 5. Next gates

1. Re-run the exact Phase 11/yfinance download and feature builder for ROKU only; require at least 220 usable Close observations and the same date/adjustment conventions. Do not persist raw prices.
2. If ROKU passes, re-run the full Phase 20C price-coverage census from a clean main-based branch and verify whether the denominator becomes 329/329. Do not yet run returns or alpha.
3. Correct Nasdaq date normalization and \`data.totalRecords\` extraction before using it for coverage claims. It currently offers no target-symbol history.
4. Do not spend more effort on the current Stooq request path unless its HTML response can be explained and a valid CSV method is demonstrated on controls.
5. Continue SEC Form 144 only after a second successful poll establishes a non-null lower bound; the first post-upgrade baseline remains ineligible.
6. Continue CFTC first-receipt collection under the preregistered ES/NQ scope and weekly-cadence guard.
7. Inspect FINRA Phase 469's first scheduled capture after its 22:30/23:30 UTC slots.
8. Keep Cboe sample artifact 13291147097 quarantined pending sample-specific written redistribution permission or manual deletion (Issue #132). No deletion endpoint is available to this connection.

No return, alpha, OOS, bootstrap, LOO or holdout test was performed. No provider fallback, signal or production change is admitted.

\`F80_TOP20_PARTIAL50_BASELINE_C20\` remains frozen: universe, parameters, holding period, capital, exposure, costs, holdout and production are unchanged.
