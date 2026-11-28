# Phase 678 — FINRA Reg SHO first prospective symbol-panel observation

**Audit date:** 2026-11-28 UTC  
**Repository HEAD after capture:** `bc4d02d9fd9d60cf726c2bdefd822fbaece35d2d`  
**Disposition:** first prospective symbol-level observation persisted; research-only, no signal or alpha claim.

## 1. Actions preflight and execution

- Checked the latest 20 repository Actions runs before proceeding: **0 active or queued**. No duplicate run was dispatched.
- Scheduled run [46105917821](https://github.com/jafelix81/NuevaEstrategia/actions/runs/46105917821) completed successfully. Both jobs passed: offline regression and live capture.
- Offline regression ran **65 tests**, all passing.
- The poll requested trade dates 2026-11-27, 11-26, 11-25, 11-24, 11-23, 11-20, 11-19 and 11-18. Only the 2026-11-27 file generated a new first-seen event in this run; historical observations were not backdated or promoted.
- The run committed the append-only panel to `main`. The resulting HEAD is the commit above.

## 2. First-seen symbol panel

The persisted `research/data/finra_regsho_daily_first_seen/symbol_observations.csv` contains **327 unique ticker observations for 2026-11-27**, each tied to the frozen 335-ticker snapshot.

- Universe coverage: **327 / 335 = 97.61%**.
- Every persisted row is marked `research_observation_eligible=true`; every row remains `signal_eligible=false`.
- The capture summary records one eligible first-seen date-level event and 327 appended symbol rows.
- Eight snapshot tickers had no row in the source file: AVB, EA, EQR, LPRO, ROKU, TELFY, WBD and WBS. This is an absence-of-row observation only; it does not establish zero trading, delisting or a parser defect.
- The conservative first-seen interval for the new file was 2026-11-28 04:05:56.775438–04:05:57.090923 UTC (about 315 ms). The stored first-seen time is the interval's upper bound, **not** the exact public-release timestamp.
- The panel retains source-file hash, per-row hashes, the frozen-universe commit/hash and the market-list field. It does **not** retain the raw source payload: `raw_market_data_persisted=false` and `raw_source_payload_persisted=false`.

### Row-grain control

The poll summary reports 14 duplicate symbols and 28 quarantined row occurrences across seven diagnostic files (14 extra rows). The parser excludes all rows for an ambiguous duplicate symbol and retains only unique symbols. The persisted security row's market field is a comma-separated facility list (for example, `B,N,Q`), not separate facility-level observations; it must not be re-summed as though it were a per-market breakdown.

## 3. Descriptive-only snapshot

Across the 327 symbols:

- Median short-volume ratio: **49.21%**.
- 25th–75th percentile: **39.02%–58.28%**.
- 90th percentile: **67.09%**; maximum: **87.56%**.
- Sum of the observed universe rows: approximately 878.1 million total-volume units and 389.7 million short-volume units (volume-weighted ratio **44.38%**).

These are one-date descriptive statistics, not evidence of informed buying/selling or predictive pressure. FINRA daily short-sale volume is not short interest, does not identify the beneficial buyer/seller, and can reflect market-making, hedging and intraday inventory mechanics.

## 4. Point-in-time and strategy disposition

- The 2026-11-27 file was first observed after that session's close. A daily-bar-based event test must not enter on 2026-11-27; the next XNYS session is **2026-11-30**.
- There is only one prospective eligible trade date in the symbol panel. No approved price/security-master join, event return, incremental comparison versus frozen LTM/F80, chronological OOS, bootstrap or LOO result exists.
- No signal is admitted. `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen.
- No production change, exposure change, parameter change, vendor contact or data purchase occurred; data spend remains USD 0.

## 5. Next gates

1. Continue the existing scheduled capture; preserve first-seen intervals and never turn bootstrap/backfill rows into prospective observations.
2. Obtain a reviewed, reproducible price panel and point-in-time security master before labeling returns or mapping delisted names.
3. Preserve raw source bytes (or an approved immutable source artifact) if terms and storage controls permit; hashes alone do not make the parsed values independently reproducible.
4. Accumulate a materially longer prospective sample before any hypothesis test. Pre-register the feature, next-session execution rule, costs, universe, benchmark and OOS schedule before looking at returns.
5. Keep duplicate-symbol rows quarantined until the source's row-grain semantics are independently resolved.

**Conclusion:** Phase 678 closes the operational gap between a metadata-only FINRA poll and a persisted prospective symbol panel. It does not establish a trading edge.