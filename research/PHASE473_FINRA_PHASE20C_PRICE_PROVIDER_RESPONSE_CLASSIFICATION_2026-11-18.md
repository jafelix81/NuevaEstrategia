# Phase 473 — FINRA Phase 20C price-provider response classification audit

**Audit cutoff:** 2026-11-18 07:03 UTC  
**Base main:** \`cdb6f13ab4fab8929c211430f90d86af9dad869b\`  
**Disposition:** Phase 381 correctly admitted no fallback, but its Stooq and Nasdaq outcomes are provider-method failures/unknowns, not evidence of missing ticker history. Yahoo's seven empty chart responses are symbol-level endpoint observations, not proof of no historical data across providers. Phase 20C remains blocked; no price source or signal is admitted.

## 1. Repository and Actions preflight

- Main HEAD: \`cdb6f13ab4fab8929c211430f90d86af9dad869b\` (Phase 472 / PR #133 merged).
- Actions total: 7,771. Latest 100: 79 success, 15 failure, 6 cancelled; 0 active/queued.
- Branches: 304 (100 + 100 + 100 + 4 across four REST pages).
- Open PRs: 56; workflow files: 78.
- Latest runs [44248336010](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44248336010) and [44248336008](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44248336008) are completed successful Form 4 compatibility jobs for PR #133; PR #133 merged at 06:02:16 UTC as \`cdb6f13...\`.
- No active/queued run was observed. No workflow was dispatched, rerun or duplicated.

### Relevant live captures

- SEC Form 144 run [44228413864](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44228413864), job 134547264687, succeeded; artifact [14393319006](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44228413864/artifacts/14393319006), SHA-256 \`dd3cae9e7e224491fa32ffaee34b56f3ab6211f57a3bf0384165d5cda1e96775\`. I downloaded and inspected its summary. It contains 90 new Form 144 accessions and 109 feed-observation rows, but both feeds still have \`INITIAL_BASELINE_NO_LOWER_BOUND\`, null lower bound, zero research-eligible and zero signal-eligible observations. The pagination watermark is found and no feed-window gap is reported. The 90 records are not PIT-admissible.
- CFTC TFF run [44232546204](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44232546204), job 134560838218, succeeded; artifact [14395926632](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44232546204/artifacts/14395926632), SHA-256 \`e4d9a147e920e3333b1d684a477ac77ef68a1364e9b028c2e3381a34ece795e7\`. Its metadata-only summary confirms four first-receipt report events for 2026-11-10 at 2026-11-18 03:44:57 UTC; no signal or forward-return feature is attached. The run was materially delayed relative to its configured prior-day schedule.
- FINRA Phase 469's first post-merge scheduled slots (22:30 and 23:30 UTC on weekdays) were still ahead at this audit cutoff. No live FINRA capture is claimed.
- SEC Phase 403 has a 47-minute hourly cron. The only post-upgrade scheduled run visible at cutoff is 44228413864 at 03:09 UTC. No subsequent scheduled SEC run was visible through 07:03 UTC; treat this as a delivery gap to monitor, not proof the workflow is disabled.

## 2. Phase 381 artifact re-adjudication

Inspected Phase 381 PR #57 and downloaded its metadata-only artifact [14073108228](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43500356535/artifacts/14073108228), ZIP SHA-256 \`c88e350c188e513e9ac7995aad859ec1b02040e7a2f9586ce1f063bf7f6537ef\`.

Exact provider counts for 2016-10-24 through 2026-10-23:

| Provider | Four controls (AAPL/MSFT/NVDA/SPY) | Seven Phase 20C missing names (AVB/EA/EQR/LPRO/ROKU/WBD/WBS) | Adjudication |
|---|---:|---:|---|
| Yahoo query1 | 2,514 each | 0 each | Controls validate endpoint; seven chart responses are empty at this endpoint/window |
| Yahoo query2 | 2,514 each | 0 each | Same result, independent host |
| Stooq | 0 each; parser raises \`ValueError\` | 0 each; same parser failure | **Provider method unvalidated**: HTTP status/content type/body signature were not retained |
| Nasdaq historical API | 0 rows for all four controls | 0 rows for all seven | **Provider method/schema unvalidated**: HTTP 200 with empty \`tradesTable.rows\` even for controls; response status/message/schema keys were not retained |

### Critical interpretation correction

The Phase 381 report's broad statement that the alternatives returned no parseable history must not be read as a negative coverage result for Stooq or Nasdaq. Their control tickers failed too. This is evidence that those request/parser methods were not validated, not that those providers lack historical data.

For Yahoo, Phase 381 records HTTP 200 and a chart result with zero timestamps for the seven missing tickers, while all four controls returned 2,514 rows. That is a reproducible endpoint-level empty result, but the old artifact does not preserve Yahoo chart metadata (symbol, first-trade date, exchange, chart error) needed to distinguish a symbol mapping issue from a genuine history gap. It is not sufficient to certify that no usable historical source exists.

The Phase 381 code also:
- stores only \`error_class\` for Stooq exceptions, omitting HTTP status and response content type;
- parses only \`data.tradesTable.rows\` for Nasdaq, omitting API \`status\`, \`message\`, root/data keys and total-record metadata;
- records Yahoo status/row count but omits chart metadata and error details.

No raw prices are retained in this re-audit.

## 3. Phase 20C status and branch hygiene

- PR [#57](https://github.com/jafelix81/NuevaEstrategia/pull/57) remains Draft/open, based on \`phase380-cftc-tff-full-postlaunch-archive-census\`, not main.
- Its head \`phase381-finra-price-provider-fallback-audit\` is 211 commits ahead and 205 behind current main in the comparison endpoint. Do not merge it directly or rebase its entire stacked history blindly.
- Legacy \`phase20c-finra-walkforward\` is 12 commits ahead and 314 behind current main. Its original code's forward-return helper uses the signal-date close as entry, which is not a valid executable entry for a FINRA file received after the close. The later next-session-open retest is the relevant line; the price-provider blocker remains 328/329 histories.
- No tickers may be dropped, imputed or mixed across providers without an effective-dated security master, adjustment/corporate-action reconciliation and independent return-concordance checks.

## 4. Phase 473 response-metadata probe

This phase adds a metadata-only hosted diagnostic for the same 11 symbols and exact window. It records HTTP status, content type, response/schema signatures, provider error metadata, row counts and first/last dates only. It never writes OHLCV values or raw response bodies.

Provider method validity is assessed using the four positive controls. A provider with fewer than three nonempty control histories is classified \`PROVIDER_METHOD_UNVALIDATED\`; zero rows for the seven missing names must not be interpreted as missing market history under an unvalidated method.

The probe is not a price fallback and cannot authorize mixing providers. It is intended to distinguish:
- transport/access failure;
- unexpected content type or schema;
- valid but empty symbol-level response;
- validated control response with ticker-specific history gap.

## 5. Binding controls and next gates

1. Run the metadata-only probe once on the dedicated branch; inspect the artifact and logs.
2. Only if a provider method passes controls, investigate the seven names' symbol mapping and listing dates, then require at least 220 usable daily observations where appropriate and independent return concordance before any fallback is considered.
3. Preserve the 335-symbol universe and exact Phase 20C sample window; no imputation or mixed source.
4. Continue SEC Form 144 only after a second successful poll establishes a non-null lower bound; the first post-upgrade baseline remains ineligible.
5. Continue CFTC first-receipt collection under the preregistered ES/NQ scope and weekly-cadence guard.
6. Inspect FINRA Phase 469's first scheduled capture after its configured 22:30/23:30 UTC slots; CI is not a data capture.
7. Keep Cboe sample artifact 13291147097 quarantined from further use pending sample-specific written redistribution permission or manual deletion (Issue #132). No deletion endpoint is available to this connection.

No return, alpha, OOS, bootstrap, LOO or holdout test was performed. No provider fallback, signal or production change is admitted.

\`F80_TOP20_PARTIAL50_BASELINE_C20\` remains frozen: universe, parameters, holding period, capital, exposure, costs, holdout and production are unchanged.
