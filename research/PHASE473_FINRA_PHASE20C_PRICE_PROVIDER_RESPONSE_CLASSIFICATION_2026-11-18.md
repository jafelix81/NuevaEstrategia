# Phase 473 — FINRA Phase 20C price-provider response classification audit

**Audit cutoff:** 2026-11-18 07:19 UTC  
**Base main:** \`cdb6f13ab4fab8929c211430f90d86af9dad869b\`  
**Disposition:** the 328/329 Phase 20C price-history blocker remains. A transient Yahoo chart response once returned 2,280 ROKU rows, but this was not reproducible on the final run. The Phase 11-equivalent yfinance download returned only 1–2 rows for each of the seven missing symbols (zero passed the 220-row threshold). Nasdaq's corrected ISO-date API works on three controls but returns none of the target symbols. No fallback is admitted.

## 1. Repository and Actions preflight

- Main HEAD: \`cdb6f13ab4fab8929c211430f90d86af9dad869b\` (Phase 472 / PR #133 merged).
- Actions at preflight: 7,771 total; latest 100: 79 success, 15 failure, 6 cancelled; 0 active/queued.
- Branches at preflight: 304; open PRs: 56; workflow files: 78.
- Mainline CI runs [44248336010](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44248336010) and [44248336008](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44248336008) completed successfully for PR #133, which merged at 06:02 UTC.
- No pre-existing active/queued run was duplicated. Phase 473 used a branch-specific workflow with a concurrency group. Two sequential commits caused one queued repeat of the same metadata-only probe; it did not overlap the first. Two intermediate code iterations failed (missing pandas in the live job, then an optional yfinance version NameError); both were corrected before the final successful run.

### Relevant live captures

- SEC Form 144 run [44228413864](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44228413864), job 134547264687, succeeded; artifact [14393319006](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44228413864/artifacts/14393319006), SHA-256 \`dd3cae9e7e224491fa32ffaee34b56f3ab6211f57a3bf0384165d5cda1e96775\`. Its inspected summary contains 90 new Form 144 accessions and 109 feed-observation rows, but both feeds still have \`INITIAL_BASELINE_NO_LOWER_BOUND\`, null lower bound, zero research-eligible and zero signal-eligible observations. Pagination watermark is found and no feed-window gap is reported. The 90 records are not PIT-admissible.
- CFTC TFF run [44232546204](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44232546204), job 134560838218, succeeded; artifact [14395926632](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44232546204/artifacts/14395926632), SHA-256 \`e4d9a147e920e3333b1d684a477ac77ef68a1364e9b028c2e3381a34ece795e7\`. It records four first-receipt report events for positions dated 2026-11-10, observed at 2026-11-18 03:44:57 UTC. No derived signal or forward return is attached. The scheduled run was materially delayed.
- FINRA Phase 469's first post-merge scheduled slots (22:30 and 23:30 UTC weekdays) were still ahead at this audit cutoff. No live FINRA capture is claimed.
- SEC Phase 403 has an hourly :47 cron. The only post-upgrade scheduled run visible at cutoff is 44228413864 at 03:09 UTC. No subsequent scheduled SEC run was visible through 07:19 UTC; treat this as a delivery gap to monitor, not proof the workflow is disabled.

## 2. Phase 381 artifact re-adjudication

Inspected Phase 381 PR #57 and downloaded its metadata-only artifact [14073108228](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43500356535/artifacts/14073108228), ZIP SHA-256 \`c88e350c188e513e9ac7995aad859ec1b02040e7a2f9586ce1f063bf7f6537ef\`.

For 2016-10-24 through 2026-10-23:

| Provider | Four controls (AAPL/MSFT/NVDA/SPY) | Seven missing names (AVB/EA/EQR/LPRO/ROKU/WBD/WBS) | Adjudication |
|---|---:|---:|---|
| Yahoo query1/query2 (13 Nov) | 2,514 rows each | 0 each | Controls validated; seven empty chart results on that capture date |
| Stooq | 0 each; parser raised \`ValueError\` | 0 each; same failure | Method unvalidated; old artifact omitted HTTP status/content type |
| Nasdaq US-slash date format | 0 for all | 0 for all | Method unvalidated; old artifact omitted API error details |

The Phase 381 report must not be read as proving Stooq/Nasdaq lacked historical data. Their controls failed too, so those were provider-method/access/schema failures rather than negative coverage evidence.

## 3. Phase 473 live provider audit

### 3.1 Corrected Yahoo chart probes — ROKU result not reproducible

- Runs [44256975655](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44256975655) and [44256978857](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44256978857) each returned 2,280 positive finite Close and adjusted-Close rows for ROKU on both Yahoo query hosts (2017-09-28 through 2026-10-23).
- The later final run [44257792682](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44257792682) returned **zero** rows for ROKU on both hosts, and zero rows for the other six missing names. All four controls still returned 2,514 rows.
- Therefore the ROKU result is transient/non-reproducible. Do not count it as recovered history. Query1/query2 are mirrors, not independent providers.

### 3.2 Exact Phase 11-style yfinance download probe

The final Phase 473 run [44257792682](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44257792682) ran the same yfinance download arguments used by Phase 11 (\`period="10y"\`, \`interval="1d"\`, \`auto_adjust=False\`, \`progress=False\`, \`threads=False\`) and mirrored the Open/Close feature-column and 220-row gates. Installed package version: **yfinance 1.8.0**.

| Symbol | Rows returned | Positive Close | Positive Open+Close | First–last usable OHLC | 220 usable rows? |
|---|---:|---:|---:|---|---|
| AVB | 1 | 1 | 1 | 2026-08-14 | No |
| EA | 1 | 1 | 1 | 2026-08-04 | No |
| EQR | 1 | 1 | 1 | 2026-08-17 | No |
| LPRO | 1 | 1 | 1 | 2026-07-29 | No |
| ROKU | 2 | 2 | 2 | 2026-11-06–2026-11-09 | No |
| WBD | 1 | 1 | 0 | None | No |
| WBS | 1 | 1 | 1 | 2026-08-19 | No |

All four controls (AAPL, MSFT, NVDA, SPY) returned 2,512 rows each, from 2016-11-18 through 2026-11-17. The method therefore works on controls but does not deliver the missing symbols' histories. None of the seven passes the 220-row threshold. This does **not** resolve 328/329.

The yfinance version is not pinned in the legacy Phase 11 workflow. Before any full-universe rerun, identify and record the exact package version used by the prior 328/329 run; do not assume the current 1.8.0 behavior is identical to the earlier run.

### 3.3 Stooq — HTML, not CSV

The endpoint returned HTTP 200 but \`text/html; charset=utf-8\`, 796 bytes, for controls and missing names. No \`Date,Close\` CSV schema was present. Stooq remains unvalidated, not a negative history result.

### 3.4 Nasdaq historical API — corrected date format, no target coverage

- US-slash dates (\`10/24/2016\`) returned embedded API \`rCode=400\`, error 1011: \`Bad or No parameter fromdate\`.
- ISO dates (\`2016-10-24\` / \`2026-10-24\`) returned \`rCode=200\`, 2,496 rows and \`totalRecords=2496\` for AAPL, MSFT and NVDA, with true chronological coverage 2016-11-17 through 2026-10-23.
- SPY and all seven target symbols were rejected with embedded error 1001, \`Symbol not exists.\`.

The Nasdaq date parser and \`data.totalRecords\` extraction are now corrected and unit-tested. The endpoint is usable for the three positive equity controls, but it does not cover the missing target symbols.

## 4. Phase 20C status and branch hygiene

- PR [#57](https://github.com/jafelix81/NuevaEstrategia/pull/57) remains Draft/open, based on \`phase380-cftc-tff-full-postlaunch-archive-census\`, not main.
- Its head \`phase381-finra-price-provider-fallback-audit\` is 211 commits ahead and 205 behind current main. Do not merge it directly or rebase its entire stacked history blindly.
- Legacy \`phase20c-finra-walkforward\` is 12 commits ahead and 314 behind current main. Its original helper uses signal-date close as entry, not executable for FINRA data received after close. The later next-session-open retest is the relevant line.
- ROKU is explicitly present in the frozen 335-symbol Phase 11 universe, but the apparent direct-chart recovery was not reproducible and the yfinance path returned only two rows.
- No tickers may be dropped, imputed or mixed across providers without effective-dated identity, corporate-action reconciliation and independent-source price concordance.

## 5. Next gates

1. Inspect the dependency/version record for the prior Phase 20C 328/329 run and determine why the current yfinance 1.8.0 call returns only 1–2 rows for the seven names while controls pass.
2. Reproduce the exact 328/329 download with a pinned, recorded environment; no full-universe run until the provider behavior is understood.
3. Do not treat ROKU as recovered from the transient Yahoo chart response.
4. Do not spend more effort on the current Stooq request path unless its HTML response can be explained and a valid CSV method is demonstrated on controls.
5. Keep Nasdaq as a validated control-only method; it does not supply any of the seven missing tickers.
6. Continue SEC Form 144 only after a second successful poll establishes a non-null lower bound; the first post-upgrade baseline remains ineligible.
7. Continue CFTC first-receipt collection under the preregistered ES/NQ scope and weekly-cadence guard.
8. Inspect FINRA Phase 469's first scheduled capture after its 22:30/23:30 UTC slots.
9. Keep Cboe sample artifact 13291147097 quarantined pending sample-specific written redistribution permission or manual deletion (Issue #132). No deletion endpoint is available to this connection.

No return, alpha, OOS, bootstrap, LOO or holdout test was performed. No provider fallback, signal or production change is admitted.

\`F80_TOP20_PARTIAL50_BASELINE_C20\` remains frozen: universe, parameters, holding period, capital, exposure, costs, holdout and production are unchanged.
