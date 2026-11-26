# Phase 650 — FINRA CNMS partial symbol quarantine

**Audit cutoff:** 2026-11-26 20:56:40 UTC  
**Base main:** `a218c79922628d34a87ee3fd59ea3d9c0576ac4c`  
**Disposition:** retain the unambiguous symbol rows from a syntactically valid CNMS file while quarantining every row for any repeated symbol. Do not aggregate overlapping composite-market rows. This is a data-integrity improvement only; it does not admit a signal.

## 1. Required preflight

Before editing the collector, inspected the latest Actions runs, jobs, logs and artifacts; current branches; all 85 open PRs; and the relevant FINRA, CFTC, SEC and Phase 648 research files.

- Actions inventory: 8,354 total runs.
- Latest 100: 70 success, 18 failure, 12 cancelled.
- Queued: 0. In progress: 0.
- Latest main commit: `a218c79922628d34a87ee3fd59ea3d9c0576ac4c`.
- Phase 648 PR #246 is merged; its final offline run [45883866597](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45883866597) passed 10/10 tests and uploaded artifact [15148442172](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45883866597/artifacts/15148442172).
- Latest SEC scheduled captures remain Form 4 [45848689364](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45848689364), 13F [45839454376](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45839454376), and Form 144 [45827105431](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45827105431). Their jobs completed successfully and artifacts remain unexpired. At the audit cutoff no later scheduled run was visible; this does not prove that any workflow is disabled.
- Latest inspected CFTC and FINRA captures remain [45753716471](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45753716471) and [45754121648](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45754121648), respectively.

No workflow was dispatched, rerun, cancelled or duplicated.

## 2. What the FINRA artifact actually showed

Downloaded and inspected the exact Phase 469 artifact [15086513251](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45754121648/artifacts/15086513251), ZIP SHA-256:

`e7f8c2922c83cb9d2c24f1b08a8e6eacf78b99d4c8e4b5d356bc9f7e339fbdba`.

The scheduled poll covered eight trade dates: 16, 17, 18, 19, 20, 23, 24 and 25 November 2026. All eight URLs returned HTTP 200 and all eight files passed the header/trailer and numeric parsing up to the duplicate-symbol gate.

The old parser rejected every entire file because two symbols repeated in each file:

- **BCPC:** two rows with overlapping facility sets. The sets were either `B,N,Q` plus `N,Q`, or `B,N,Q` plus `Q`.
- **TPC:** two rows with overlapping facility sets, generally `B,N,Q` in both rows; on 17 November the second set was `N,Q`.

Across eight dates:
- 16 duplicate symbol/date groups.
- 16 extra rows beyond one row per repeated symbol.
- 32 total source rows belong to the repeated-symbol groups and must be excluded under a fail-closed symbol rule.
- Zero byte-identical duplicate rows. The repeated rows have different row hashes, so they must not be summed or silently deduplicated.
- All observed facility sets overlap; the data do not establish whether each pair is a duplicate aggregate or separate security classes sharing a ticker.

The artifact stores only row hashes, line numbers, market-code sets and duplicate counts. It does not store raw rows or volume values.

## 3. Frozen-universe overlap check

Recovered the exact frozen 335-symbol snapshot from commit `1aa1b91f383ce9cef375a43e775c736a27356a5f`, blob SHA-1 `7edbd62b4fb34a6123276e4ce45cb3c1c62479c7`.

- 335 unique tickers.
- BCPC absent.
- TPC absent.

This is a descriptive overlap check against the frozen snapshot only. That snapshot has no effective dates and is not a historical security master. It does, however, show that the two currently ambiguous symbols are outside the reference universe used by the prior 335-symbol audit.

## 4. Parser change

The previous rule rejected a complete consolidated file if any symbol repeated. The revised rule is deliberately narrower and fail-closed at the security-symbol level:

1. Validate every source row, date, market code, volume relationship, file trailer and raw-file hash as before.
2. For composite-market CNMS files, identify all symbols with more than one row.
3. Exclude **every** row for each repeated symbol; do not select a preferred row, sum volumes, or infer a CUSIP/class.
4. Retain rows for symbols that occur exactly once.
5. Mark the schema version `security_rows_with_market_lists_partial_symbol_quarantine` and poll status `valid_file_partial_symbol_quarantine`.
6. Persist metadata-only duplicate diagnostics, including the number of quarantined symbols and rows. Raw rows and volume values remain unpersisted.
7. A research observation is eligible only if at least one unambiguous symbol remains. If all rows are quarantined, the file is recorded but produces no research-eligible symbol observations.
8. Existing first-seen rules remain unchanged. A prior `invalid_file` is not converted retrospectively into a first-seen event; old files remain bootstrap/ineligible unless their original capture history independently satisfies the existing rule.

This recovers the unambiguous portion of the daily cross-section without contaminating it with potentially overlapping short-volume totals. Downstream Phase 468 labels receive only retained symbols and carry the partial schema version.

## 5. Interpretation and limits

FINRA Reg SHO daily short volume measures reported executed short-sale volume in FINRA trade-reporting facilities; it is not short interest, not total-market short selling, and not a direct measure of informed institutional intent. The official FINRA file layout describes the volume fields and reporting-facility field; the current consolidated multi-facility notation is also documented in contemporary file-format references. Sources: [FINRA file layout](https://www.finra.org/sites/default/files/DailyShortSaleVolumeFileLayout.pdf), [FINRA Developer Center — Reg SHO Daily Short Sale Volume](https://developer.finra.org/docs/api-explorer/query_api-equity-reg_sho_daily_short_sale_volume), [current CNMS format notes](https://www.strasmore.com/blog/how-to-download-finra-short-volume-data).

The two repeated symbols are excluded even though they are outside the frozen 335 snapshot. The collector remains generic: any future repeated symbol is quarantined the same way. No assertion is made that all remaining symbols have correct historical identity or F80 membership.

No prices were downloaded and no forward returns, alpha, OOS, bootstrap, LOO or portfolio tests were run. The Phase 649 price-rights gate remains unresolved. No paid data, quote requests, vendor contact or options-data acquisition occurred; the authorized data budget remains USD 0.

## 6. Validation and next gate

The PR workflow runs offline regression only; the live-capture job is schedule/dispatch-only and will not run on this PR. New tests cover:
- partial parsing with unique symbols retained;
- all rows for duplicate symbols quarantined;
- no duplicate-volume aggregation;
- metadata-only diagnostics;
- no research eligibility when no unique symbols remain;
- research observations containing only unique symbols when partial data remain.

After CI passes, the next natural FINRA capture may use the new parser. Historical files rejected by the old parser will not be retroactively promoted to first-seen observations.

`F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen. No universe, parameters, costs, exposure, capital or holding-period policy changed.
