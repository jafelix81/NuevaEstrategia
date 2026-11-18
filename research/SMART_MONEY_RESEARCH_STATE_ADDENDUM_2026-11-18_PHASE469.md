## Phase 469 — FINRA Reg SHO daily first-seen capture (2026-11-18)

- Added a new public-file capture workflow for consolidated `CNMSshvolYYYYMMDD.txt`; no existing mainline workflow covered this daily flow source (Phase 447 is short-interest OAuth).
- Schedule: 22:30 and 23:30 UTC weekdays. Each poll rechecks ten calendar days of weekday candidates to catch late files without backdating.
- File parser validates header/schema, trade date, unique symbols, finite non-negative Decimal volumes, `ShortExempt <= Short <= Total`, and trailer count. Fractional shares are supported.
- Ledger is file-level only: first-seen UTC, poll bounds, HTTP status, raw SHA-256, bytes, row/symbol counts, schema signature and revision lineage. Raw market data are held in memory only; no raw files or per-symbol volumes are committed.
- Only a non-empty file first observed by a scheduled poll on the same New York trade date after 16:00 ET can be research-observation eligible. Prior-date first captures are bootstrap; manual polls are diagnostic and do not persist; revisions preserve the original first-seen time/hash and are not new signals. All signal eligibility remains false.
- File manifests can be expanded in memory into Phase 468 per-symbol labeler inputs only after a re-download matches the original hash. Unrecoverable revised first-seen bytes must be excluded from primary feature tests.
- Phase 469 tests and CI are pending at the time this addendum was authored. No live FINRA request, return test, OOS, bootstrap, LOO or strategy change was performed.
- Report: [Phase 469](PHASE469_FINRA_REGSHO_DAILY_FIRST_SEEN_CAPTURE_AUDIT_2026-11-18.md) · [summary](PHASE469_FINRA_REGSHO_DAILY_FIRST_SEEN_CAPTURE_SUMMARY_2026-11-18.json).
- `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen.
