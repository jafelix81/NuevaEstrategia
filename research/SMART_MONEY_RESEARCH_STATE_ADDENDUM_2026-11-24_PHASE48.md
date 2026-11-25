# Smart Money Research state addendum — Phase 48 (2026-11-24 UTC)

- Added a pure, deterministic SEC 13F manager-period as-of amendment state machine with explicit RESTATEMENT replacement, NEW HOLDINGS supplement, and 13F-NT notice-only semantics.
- Daily availability is conservative: first supplied regular session strictly after date-only FILING_DATE; report period is never treated as availability.
- Chain gaps, missing originals, unknown amendment types, overlapping supplement rows, missing holding payloads and duplicate line keys fail closed. Notices never become zero portfolios.
- Offline synthetic tests cover the critical paths. Awaiting Phase 48 GitHub Actions result at time of writing.
- No SEC request or data backfill was made. Phase 47 pull-request workflow was hardened: PR checks are offline-only; live SEC retrieval requires explicit workflow_dispatch input run_live_sec_audit=true.
- This is code-contract validation only; no actual 13F manager state panel, CUSIP-to-F80 historical mapping, exact acceptance timestamp, signal, alpha, OOS, bootstrap or LOO result is claimed.
- Historical coverage remains the blocker: Phase 22C 13F mapping reported 212/335 in 2016Q1, 246/335 in 2020Q1, 280/335 in 2024Q1. Phase 604's 328/335 is current registered-fund ticker/registrant discovery, not an effective-dated security master.
- Next: parse OTHERMANAGER relationships and validate complete amendment chains against original EDGAR filings, then revisit the historical CUSIP/F80 coverage gate.
- `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen. Options budget remains USD 0; no sample, purchase or quote request.
