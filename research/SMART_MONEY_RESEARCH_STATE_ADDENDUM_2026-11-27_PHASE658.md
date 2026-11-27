# Smart Money Research State Addendum — Phase 658 (2026-11-27)

**Mainline documentation:** [Phase 658 report](PHASE658_FORM4_LIVE_LEDGER_INTEGRITY_AND_AMENDMENT_AUDIT_2026-11-27.md) · [JSON summary](PHASE658_FORM4_LIVE_LEDGER_INTEGRITY_AND_AMENDMENT_AUDIT_2026-11-27.json)

## New Form 4 data-integrity finding

- Current live ledger: 140 filing headers and 276 transaction rows.
- One SHMD P/A row is internally inconsistent in the SEC primary document: period/earliest transaction is November 2026, but Table I says 11/25/2006; the price field is USD 1,731,429 for 60,000 shares. The raw row is preserved and must be quarantined from value aggregation and signal review.
- Ten rows across four accessions have more than 30 calendar days between transaction and filing dates. BNAI's rows are A/M grants/exercise; Crescent's P/A is a NAV final-value amendment; TRON's A/M rows are an ownership-only amendment; SHMD is the malformed source row.
- Two Form 4/A accessions (five transaction rows) have no original-accession link stored in the current ledger. SEC primary documents confirm that one amendment finalizes NAV-based values and the other only adds a joint reporting person. Amendments must be reconciled to original state, not counted as fresh trades.
- Current code semantics remain important: SEC P/S are open-market or private purchases/sales; A/M/F have different award/exercise/tax semantics.

## Eligibility and controls

- All 276 transaction rows remain signal-ineligible.
- No market price series, forward returns, event study, OOS, bootstrap or LOO test was run.
- No new signal or incremental alpha was admitted.
- F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen.
- No paid data, vendor contact or purchase; budget remains USD 0.

## Next gate

Build verified original-accession/amendment state linkage and persistent source-anomaly flags without rewriting raw SEC values. Continue to require exact public-availability bounds, historical security identity/F80 membership, owner attribution and rights-cleared prices before testing any insider hypothesis.
