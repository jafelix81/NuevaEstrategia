# Phase 515 — FINRA CNMS Market-field schema repair (2026-11-20)

## Executive disposition

The Phase 469 scheduled workflow is operational at the GitHub Actions level but its live parser is not accepting the current CNMS payloads. Run 44669121290 completed successfully, yet all eight HTTP-200 responses were classified as invalid files. The failure is a parser/schema incompatibility, not a transport outage and not evidence that the daily files were unavailable.

The observed failure was `market_code_invalid` on all eight requested dates. The current parser required a single alphabetic character in the Market field. FINRA's Developer Center describes Reg SHO daily short-sale volume as aggregated by security across trades reported to FINRA facilities. A recent reproducible description of the consolidated CNMS file documents one row per symbol and a comma-separated Market list such as `B,Q,N`. The older FINRA file-layout PDF describes a one-character facility identifier; that older convention does not fully describe the current consolidated CNMS representation. Because the live response body was not persisted, the exact offending field values from run 44669121290 cannot be independently re-read; the root-cause diagnosis is consistent with the published current CNMS format and must be confirmed by the next scheduled live poll.

Sources:
- FINRA Developer Center, Reg SHO Daily Short Sale Volume: https://developer.finra.org/docs/api-explorer/query_api-equity_reg_sho_daily_short_sale_volume
- FINRA Regulation SHO Daily Short Sale Volume File Layout (older layout): https://www.finra.org/sites/default/files/DailyShortSaleVolumeFileLayout.pdf
- Current CNMS field-format walkthrough, updated 2026-10-03: https://www.strasmore.com/blog/lang/es/how-to-download-finra-short-volume-data

## Preflight and latest Actions state

Reviewed the latest 100 Actions runs, their run metadata, jobs, job steps, artifacts, recent branches, open PRs, current research files, and the relevant data ledgers before making changes.

- Main HEAD before this PR: `1fa5e7c427caba657c74b4e4268f57e47cc82b00`.
- Active Actions runs: 0.
- Queued Actions runs: 0.
- No workflow was manually dispatched or rerun.
- Relevant open draft PRs at preflight: #166 (Phase 513 Form 4), #167 (Phase 514 Form 4/Form 144), #165 (CFTC PIT), #164 (OptionMetrics PIT), and #159 (FINRA Consolidated Short Interest).

### Latest relevant runs

| Run | Result | What it establishes |
|---|---|---|
| [44669121290](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44669121290) Phase 469 FINRA Reg SHO | Workflow success; offline 56/56; live job success | 8 HTTP 200, 8 invalid, 0 valid, 0 first-seen, 0 research-eligible; `raw_market_data_persisted=false` |
| [44668300202](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44668300202) Phase 384 CFTC TFF | Success | 3,039 rows unchanged; no new report or revision; zero historical rows signal-eligible; alpha test not authorized |
| [44662324343](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44662324343) Phase 403 Form 144 | Success | Both feeds complete; 103 feed-observation rows; 70 new accession XML blocks parsed into 542 detail rows; separate bounded backfill processed 10 accessions and appended 54 rows; final ledger 80 accessions / 596 detail rows / 61 issuer CIKs; 596/596 source hashes match; 368 backfill accessions remain |
| [44656159115](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44656159115) Phase 476 Form 4 | Success | 457 new canonical Form 4 accessions; 10 bounded structured documents parsed; 22 detail rows; 1,190 backfill accessions remain; public availability and signal eligibility remain false |

### FINRA Reg SHO failure detail

Run 44669121290 requested eight trade dates (2026-11-19, 18, 17, 16, 13, 12, 11 and 10). All returned HTTP 200 and response sizes between 542,484 and 552,360 bytes. All eight were rejected with `market_code_invalid`. The append-only polls ledger retains each response hash and byte count. The state file has an empty `files` map; no date was accepted as a valid first-seen file.

The prior run 44453548570 also had eight HTTP-200 invalid files, but under the earlier parser it reported `duplicate_symbol`. This reinforces that the CNMS row-grain assumptions have not been correctly reconciled. Neither run produced eligible observations.

## Parser correction

The parser now supports both representations without double-counting:

1. **Consolidated security rows:** when any Market field contains a comma-separated list of one-letter facility codes, the file is treated as security-grain. Each symbol must be unique. Volume values are retained as already consolidated; they are never summed again. Market codes are normalized, sorted and retained as a comma-joined list.
2. **Single-code rows:** when all rows carry one facility code, the parser preserves the legacy facility-row path. Repeated symbols across distinct facility codes are aggregated; duplicate (symbol, facility) pairs remain invalid.
3. A consolidated file with duplicate symbols, malformed tokens, repeated codes within a list, bad dates, invalid volumes, row-width errors or a trailer mismatch remains rejected.
4. The schema signature now includes the inferred row grain, so a transition between facility rows and consolidated security rows is visible in the ledger.

The repair does not whitelist a fixed set of facility letters. It validates the published one-letter token shape while leaving room for future facility codes; the CNMS file identity supplies the consolidated-NMS scope.

Four new offline tests cover comma-separated market lists, no double aggregation, duplicate symbols in consolidated files, invalid multi-character tokens and duplicate facility codes. Existing facility-row aggregation tests remain in place.

## Point-in-time consequences

The invalid 2026-11-19 through 2026-11-10 files were not accepted into state. After the repair, any older file first accepted for the first time will be bootstrap-only unless the existing ledger contains a prior scheduled `not_available` poll satisfying the strict late-first-seen rule. An earlier `invalid_file` response is not proof that FINRA had not published the file. Therefore the repair must not backdate eligibility for these dates.

The next existing scheduled Phase 469 poll is the live validation gate. Do not manually dispatch or rerun while a scheduled attempt is active or pending. The PR CI run will exercise offline tests only; its live-capture job is skipped for pull requests.

## Strategy controls

- No raw FINRA volume rows were persisted by the failed capture.
- No FINRA signal or research observation is admitted by this phase.
- No return test, event study, backtest, chronological OOS, bootstrap, LOO or holdout test was run.
- CFTC remains prospective-only for PIT; the archive Updated-date clock remains rejected.
- SEC Form 4/Form 144 structured ledgers remain ingestion-valid but public-availability uncertified and non-signal.
- `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen. No universe, parameter, exposure, cost, holding-period, holdout or production changes.

## Next gate

Wait for the next existing scheduled Phase 469 run. It must show valid CNMS files, correct row/trailer reconciliation, stable hashes, a non-empty valid-file count, and correct security/facility grain. Historical dates that lack prior scheduled unavailability evidence must remain bootstrap-only. Only after live parser validation and separate PIT/universe gates can any FINRA feature be considered for incremental testing against frozen LTM/F80.
