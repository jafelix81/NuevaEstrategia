# Smart Money Research — state addendum, Phase 496 (2026-11-19)

## Completed
- Phase 496 live Form 4 payload audit completed successfully in run 44474285899; 637/637 SGML acceptance clocks matched independent SEC filing-index clocks, and 637/637 ownership XML payloads parsed.
- The native SGML `<ACCEPTANCE-DATETIME>` parser correction is covered by offline regression tests. Conflicting distinct clocks fail closed.
- Issuer CIK and as-filed symbol resolved in all 637 filings: 321 distinct issuer CIKs and 321 symbols in this cohort. This is not an effective-dated security master.
- Filing grain: 619 single-owner and 18 multi-owner filings. Do not expand joint filings into duplicated owner trades.
- Non-derivative Table I contains 145 P/A transaction rows (133 in single-owner and 12 in multi-owner filings). SEC code P includes both open-market and private purchases; no exchange-only or discretionary-buy inference is permitted.
- Filing-level Rule 10b5-1 checkbox: 109 yes, 528 no. Do not allocate this document-level flag to individual owners/rows.
- First-seen upper-bound minus acceptance: min 190s, median 14,983s, p90 17,550s, max 23,181s. These are local observation bounds, not public-availability timestamps.
- Aggregate artifact only; no raw payloads or transaction-level rows persisted.

## Decision
- Form 4 remains a conditional research source, not a signal.
- Research observations eligible: 0; signal eligible: 0; alpha testing unauthorized.
- No returns, event study, OOS, bootstrap, LOO or holdout used.
- Next gate: effective-dated security-class/listing identity and historical F80 membership reconciliation. Static ticker overlap is insufficient.

## Other source status at this audit
- FINRA Reg SHO parser correction from Phase 495 is in main, but the latest live capture listed in the current Actions audit predates the corrected parser; no post-fix live FINRA validation is established here.
- CFTC TFF latest visible run 44453066854 completed without new report/revision; historical archive/PIT limitations remain.
- SEC Form 144 latest visible live run 44447184058 completed; its separate capture ledger remains metadata-only.
- Options/Cboe and FINRA ATS historical branches/PRs remain subject to the prior data-license, revision-vintage and PIT gates. No new paid data or access was assumed.

## Baseline
F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen. No universe, parameter, holding-period, exposure, cost, holdout or production change.
