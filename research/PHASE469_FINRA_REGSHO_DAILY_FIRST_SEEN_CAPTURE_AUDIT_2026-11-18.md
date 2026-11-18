# Phase 469 — FINRA Reg SHO daily first-seen metadata capture

**Audit date:** 2026-11-18 UTC  
**Disposition:** **PROSPECTIVE FILE-LEVEL CAPTURE IMPLEMENTED; NO RAW DATA COMMITTED; NO SIGNAL OR ALPHA ADMISSION.**

## 1. Preflight

- Main HEAD: `bc4a2ccecd32962340831eea54563743dadfe6c6`.
- PR #129 remains open/draft on `phase467-finra-regsho-flow-pit-label-audit`; its Phase 468 and Form 4 compatibility checks passed.
- Latest Actions inventory: 7,743 runs; latest 100 all completed; no active or queued runs.
- No existing workflow in main captures the daily consolidated `CNMSshvolYYYYMMDD.txt` file. Existing Phase 447 workflows concern FINRA short-interest OAuth, not the public daily Reg SHO short-volume file.
- SEC Form 144 latest scheduled run remains 44179257367. CFTC TFF has no scheduled run in the Actions schedule-event inventory; its latest verified run remains bootstrap 43525140200.
- No live workflow was dispatched and no duplicate job was started.

## 2. Capture design

The new workflow polls the public consolidated FINRA file at:

`https://cdn.finra.org/equity/regsho/daily/CNMSshvolYYYYMMDD.txt`

It runs at 22:30 and 23:30 UTC on weekdays. The two polls are designed to observe the file after the regular session and around FINRA's documented same-day publication window. They do not assume an exact public release timestamp: the recorded first-seen time is the local receipt time after the complete response body is received.

Each scheduled run rechecks the latest ten calendar days, restricted to weekdays. This allows late files to be observed without backdating them. A file first observed for an earlier trade date is classified as bootstrap and is never research-observation eligible. Only a non-empty file first observed by a scheduled poll on the same New York calendar date, after 16:00 ET, can be research-observation eligible. All records remain `signal_eligible=false`.

Manual runs are diagnostic only and do not persist the ledger.

## 3. File validation

The parser:
- supports UTF-8 with optional BOM and pipe-delimited headers;
- resolves required Date, Symbol, ShortVolume, Short Exempt Volume and TotalVolume fields by normalized names;
- accepts an optional Market field and preserves a header-derived schema signature;
- parses volumes as finite non-negative Decimal values, including fractional shares;
- checks every row's trade date, unique symbol, field count and `ShortExempt <= Short <= Total`;
- validates the trailer record count against parsed data rows;
- records SHA-256, response bytes, row count and symbol count;
- treats 403/404 as `not_available`, not proof of a holiday or permanent absence;
- rejects invalid files without updating state.

The raw file is held in memory only and is not committed or uploaded. The repository stores only file-level hashes, timestamps, counts, schema signatures and poll outcomes. A later research replay must re-download the public file and verify that its hash still matches the first-seen manifest. If FINRA has revised the file and the original bytes are no longer retrievable, the original first-seen version is not reconstructable and must be excluded from primary feature tests.

## 4. Revision and bootstrap policy

- First observation of a prior date during initial activation: `bootstrap`, not eligible.
- First observation of the current New York trade date during a scheduled poll after 16:00 ET: `first_seen`, eligible for research only.
- Same hash on a later poll: `unchanged`, no duplicate event.
- Changed hash: append a `revision` event, preserve original first-seen time/hash, and never relabel the revision as a new first-seen signal.
- Manual run: `manual_diagnostic`, no persistent state.
- No state or event ever sets `signal_eligible=true`.

The file-level manifest can be expanded in memory into per-symbol Phase 468 labeler inputs only after the raw file is re-downloaded and its SHA-256 and trade date match the manifest. No raw volume values are stored in Git.

## 5. Validation

The offline suite covers fractional volumes, empty-but-valid files, header/trailer validation, duplicate symbols, volume subset constraints, negative/non-finite values, trade-date mismatch, row-width errors, weekend filtering, same-day eligibility, historical bootstrap, manual-mode isolation, revisions, unchanged hashes, and hash-verified per-symbol expansion.

No live FINRA request, raw file persistence, price download, label generation, return test, OOS, bootstrap, LOO or strategy change is part of this PR. The scheduled workflow becomes active only after merge to the default branch and only if enabled in GitHub Actions.

## 6. Research gates

Before a flow-only economic test:
1. Accumulate prospective first-seen observations and verify schedule delivery.
2. Re-download each historical file and require exact SHA-256 match to the first-seen manifest; exclude unrecoverable revisions.
3. Reconcile effective-dated security identity and the complete 335-name universe, including inactive/delisted securities.
4. Obtain total-return prices, delisting/terminal returns, corporate actions and executable-cost estimates.
5. Build flow-only features separately from short-interest and ATS venue concentration.
6. Compare against frozen LTM/F80 at identical exposure and costs, with chronological OOS, bootstrap and leave-one-date/event-block-out controls. Control for prior returns, volatility, liquidity, market regime and off-exchange volume.

No claim is made that FINRA short-volume represents net short positioning, beneficial ownership, institutional identity or informed trading.

## 7. Frozen strategy

`F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen. No universe, parameter, holding-period, capital, exposure, cost, holdout or production changes were made.
