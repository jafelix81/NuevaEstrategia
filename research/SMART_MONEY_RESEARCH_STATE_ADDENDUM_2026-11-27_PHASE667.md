# Smart Money Research — Phase 667 state addendum

**Cutoff:** 2026-11-27 17:12 UTC  
**Phase:** 667 — SEC 13F value-unit restatement primary audit  
**Parent:** Phase 666, PR #255 (open draft)

## Update

- Reconciled four primary SEC 13F-HR/A XML filings for BI Asset Management Fondsmaeglerselskab A/S (CIK 1778131): accessions 0001778131-26-000018, -000021, -000022 and -000023.
- All four are amendment 1 / RESTATEMENT and state that the whole report is restated to correct Column 4 and the summary value total from thousands to nearest dollars, with no other report information changed.
- This matches the SEC EDGAR Release 22.4.1 change effective 2023-01-03. The older FAQ still shows the legacy x1000 convention, so the pipeline must version the unit rule and retain raw values.
- This verifies value-only treatment for 4/14 accessions in the candidate-CIK batch. Ten remain primary-unadjudicated; the separate 0001046192-26-000018 event remains unverified.
- Do not treat the batch as 14 new trades or manager signals. Do not backdate amended dollar values to original public-availability times. Do not assume every 13F RESTATEMENT is value-only.

## Decision

`CLASSIFY_AS_VALUE_UNIT_RESTATEMENT_NOT_NEW_POSITION_SIGNAL` for the four primary-verified filings. All 15 Phase 666 events remain metadata-only: research eligible 0; signal eligible 0; historical F80 membership verified 0.

Next: primary-verify remaining accessions, diff original/amended information tables, and implement a schema-versioned 13F amendment taxonomy and value-unit normalization audit across managers.

No prices or returns inspected; no OOS, bootstrap or LOO; holdout untouched; baseline unchanged; spend USD 0.

- Inspected the Phase 614 live job log and downloaded artifact 15212890251. The ZIP contains only poll_summary.json; all four feeds succeeded and 15 metadata observations were bounded, but no filing XML/text or holdings rows were downloaded, and research/signal eligibility remains zero.
