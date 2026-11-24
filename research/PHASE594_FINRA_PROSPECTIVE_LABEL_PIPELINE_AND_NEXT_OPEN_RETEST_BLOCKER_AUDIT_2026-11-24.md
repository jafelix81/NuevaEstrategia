# Phase 594 — FINRA prospective label-pipeline and next-open retest blocker audit

**Audit cutoff:** 2026-11-24 11:28 UTC  
**Main HEAD at preflight:** `3b9faa75b1412ceea4cbe7c8033ec29ffad5d9d1`  
**Disposition:** no executable FINRA signal or next-open OOS result is currently available. The same-day-close Phase 20C implementation remains NO-GO; the next-session-open hypothesis remains untested, not rejected.

## 1. Repository and Actions preflight

- Actions runs: **8,109** total; latest 100 = **90 success / 10 failure**.
- Explicit status queries: **0 in-progress / 0 queued**.
- Branches: **380** across four pages; open PRs: **72**; workflow files: **96**; research files: **504**.
- Main HEAD: `3b9faa75b1412ceea4cbe7c8033ec29ffad5d9d1`.
- No workflow was dispatched, rerun, cancelled or duplicated.

Latest relevant completed runs, jobs and artifacts:

| Line | Run | Jobs | Artifacts |
|---|---:|---|---|
| FINRA Reg SHO | [45339067236](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45339067236) | offline-regression success; live-capture success | [14895571787](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45339067236/artifacts/14895571787), 1,774 bytes |
| CFTC TFF | [45338400329](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45338400329) | prospective-capture success | [14895036288](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45338400329/artifacts/14895036288), 1,110 bytes |
| SEC Form 4 | [45332760566](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45332760566) | offline-regression success; live-capture success | [14892950135](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45332760566/artifacts/14892950135), 3,649 bytes |
| SEC Form 144 | [45330252226](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45330252226) | offline-regression success; live-capture success | [14891955642](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45330252226/artifacts/14891955642), [14891416912](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45330252226/artifacts/14891416912), [14890729923](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45330252226/artifacts/14890729923) |

A successful workflow conclusion is not equivalent to accepted market data. In particular, Phase 469 deliberately completes after recording invalid-file diagnostics.

## 2. FINRA Phase 469 live-poll adjudication

The live job returned HTTP 200 for six daily files (trade dates 2026-11-16, 17, 18, 19, 20 and 23), but every file was rejected as `duplicate_symbol_in_consolidated_file`.

- Each file contains repeated symbols **BCPC** and **TPC**: two repeated symbols / two extra rows per file.
- Across six files: **12 duplicate-symbol occurrences and 12 extra rows**.
- No repeated raw row was an exact byte-level duplicate.
- Facility token sets overlap. For BCPC, examples include `[B,N,Q]` versus `[N,Q]` or `[Q]`. For TPC, most repeated rows have the same `[B,N,Q]` facility set but different raw-row hashes; one date has `[B,N,Q]` versus `[N,Q]`.
- The diagnostic ledger stores line numbers, facility-set fingerprints, response hashes and byte counts. It does **not** store raw rows or volume values.
- The 2026-11-24 file returned HTTP 403 / not_available during this poll.
- `research/data/finra_regsho_daily_first_seen/state.json` still has an empty `files` map; there is no accepted `events.csv` first-seen event. First-seen, research-observation-eligible and signal-eligible counts are all zero.

The parser must remain fail-closed. Do not sum, drop or deduplicate BCPC/TPC rows from ticker/facility overlap alone. Issue [#214](https://github.com/jafelix81/NuevaEstrategia/issues/214) retains the raw-grain adjudication.

## 3. Missing production bridge: Phase 469 to Phase 468

Code inspection confirms a separate pipeline gap:

- Phase 469 hashes and parses the HTTP response, then discards the raw bytes. Its summary explicitly sets `raw_market_data_persisted=false`.
- The current capture writes poll metadata, hashes, schema and duplicate diagnostics; it does not persist a per-symbol flow panel that can be joined to returns.
- Phase 468 is a reusable executable-label constructor. It requires a validated per-symbol first-seen/late-first-seen observation, actual timezone-aware poll/receipt timestamps, source hash/schema, a verified XNYS session calendar, and consistent adjusted OHLC bars. It enters at the first session open strictly after actual first receipt and rejects historical observations without first-seen timestamps.
- Phase 468 is covered by synthetic tests, but there is no live workflow step that supplies validated Phase 469 rows and a price/security-master panel to it.

Do not solve this by committing raw market data to the public repository. Before any raw-payload or derived-row archive is added, review applicable data-use/storage/redistribution terms and choose an appropriately controlled, immutable storage design. If raw retention is not permitted, specify a permitted reproducible per-symbol feature/observation output without misrepresenting it as raw data.

## 4. Phase 372 next-session-open retest: failed before performance output

The branch `phase372-finra-shortflow-next-session-open-retest` is **20 commits ahead / 598 behind main** and has five historical runs, all failed. Latest run [43481200906](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43481200906) has one failed `next-open-pseudo-oos` job and **no artifact**.

The run stopped at the pinned-universe price gate:

- Expected valid histories: 329.
- Obtained: 328.
- Unresolved names: AVB, EA, EQR, LPRO, ROKU, WBD and WBS.
- No return table, portfolio result, bootstrap, LOO or OOS statistic was produced.

Phase 372 uses next-common-session-open entry after the signal date and had frozen the 2016-10-24 to 2026-10-24 price window. It does not consume the actual Phase 469 first-seen ledger. Phase 468's stricter actual-receipt labeler is the preferred successor contract once a valid first-seen data stream and price panel exist.

The earlier price-source audit remains conditional only: Phase 475 ranked Massive Advanced as the most practical full-history OHLC candidate, Sharadar SEP as a possible second source and CRSP as the preferred terminal-return benchmark if accessible. No sample, license, price source or terminal-return panel has been admitted. The seven legacy names have merger/acquisition/renaming events; they cannot be dropped, imputed or replaced by current successor tickers without effective-dated identity and consideration reconciliation.

## 5. Other research-line status

- **Form 4:** the latest live capture recovered both feed watermarks. The current structured ledger remains discovery-only: 61 owner-sidecar rows, 20 owner accessions pending, four multi-owner accessions quarantined, five descriptive Form 144/Form 4 crosswalk rows and zero signal-eligible matches. UPST remains a candidate issuer cluster, not an admitted signal; HOS/PICS remain out-of-universe observations.
- **Form 144:** 477 accessions / 3,360 structured detail rows, 238 bounded backfills pending, five acceptance reconciliations unresolved and zero signal-eligible filings. Mechanical sell-to-cover and plan-driven sales remain separate negative controls.
- **CFTC TFF:** 3,043 historical rows; the latest prospective capture found no new report or revision. Continue accumulation only; no predictive claim.
- **Options / MIDAS:** Cboe OPRA/Open-Close remains conditional on written strategy-use rights, PIT delivery/correction history and exact 335-name coverage. MIDAS remains exchange-market-structure/liquidity context, not dark-pool participant identity. No new sample or license was obtained.

## 6. Next gates

1. Resolve BCPC/TPC row identity and CNMS row grain from an authoritative source or controlled raw sample; no heuristic aggregation.
2. Decide whether raw payload or derived per-symbol observations can be retained under applicable terms; preserve immutable hashes and actual receipt timestamps.
3. Wire only validated first-seen observations into Phase 468; keep revisions and bootstrap observations out of executable labels.
4. Obtain a complete, immutable, effective-dated 335-name price/security panel, including inactive names, merger consideration, dividends, delisting/terminal returns and a verified XNYS calendar.
5. Freeze inputs, universe, execution, costs and chronological splits before a successor test. Compare against frozen LTM/F80 at identical exposure; use block bootstrap and event/time-block LOO. Keep the final six holdout dates sealed.

## 7. Research disposition

- Current same-day-close Phase 20C: **NO-GO** due to look-ahead.
- Phase 372 next-session-open retest: **incomplete / no performance result**, blocked by price-history coverage.
- Phase 468 actual-first-receipt labeler: synthetic contract passes; production integration and data inputs absent.
- New signals admitted: **0**.
- Incremental alpha demonstrated: **none**.
- New valid OOS / bootstrap / LOO results: **0**.
- No universe, model, exposure, costs, holding-period policy, holdout or production changes.
- `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen.

Tracking issue: [#216](https://github.com/jafelix81/NuevaEstrategia/issues/216).
