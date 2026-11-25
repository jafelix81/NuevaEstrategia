# Smart Money Research state addendum — Phase 615

**Date:** 2026-11-25 UTC  
**Phase:** 615 — SEC 13F full-snapshot and late-index safety

- Phase 614's prior accession watermark is now diagnostic only; scheduled capture scans the complete current feed snapshot to a proven short/empty page and compares all accessions against the local append-only ledger.
- The first scheduled baseline also enumerates the complete available snapshot before setting a watermark; baseline rows have no historical lower bound.
- Recognized neighboring form types are counted separately from exact target-form entries. Unclassifiable entries and unparseable exact target-form entries fail closed.
- Atom `updated` is diagnostic only. It does not terminate pagination or establish an observation interval. A bounded collector interval is between two complete-snapshot poll receipts, not an exact public-release timestamp.
- Scheduled scans are capped at 50 pages / 5,000 raw entries per form feed. A cap, repeated page, parsing failure or incomplete pagination suppresses candidates and does not advance that feed's successful state.
- Manual mode remains one-page diagnostic-only and non-persistent. PR validation remains offline-only; scheduled capture starts only after merge to main.
- Offline tests added for late-indexed accessions after the old watermark, full baseline enumeration, form-prefix neighbors, timestamp non-monotonicity, and fail-closed pagination. CI result pending at the time this addendum was written.

Source status at preflight:
- FINRA Reg SHO: 7/7 HTTP-200 daily files rejected for overlapping duplicate BCPC/TPC rows; 14 duplicate extra rows; zero accepted files or eligible first-seen events.
- CFTC TFF: 3,043 rows unchanged; no new reports/revisions; latest report date 2026-11-17; zero signal-eligible rows.
- SEC Form 4/Form 144 remain descriptive structured ledgers; no signal admitted by this phase.
- Cboe public monthly symbol-volume archive remains killed for F80 due coverage and PIT/contract-level limitations. OPRA-wide/Open-Close remains separately budget-gated.

No live SEC request, holdings download, alpha test, OOS test, bootstrap or LOO was performed. No production or baseline change. `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen. No paid data, vendor contact or quote request.
