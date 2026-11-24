# Smart Money Research state addendum — Phase 47 (2026-11-24 23:13 UTC)

## SEC 13F — accession and amendment gate passed

- [Actions run 45507919882](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45507919882) succeeded; six offline tests passed; [artifact 14974051376](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45507919882/artifacts/14974051376) includes source hashes and summary.
- 2018 Q1: 6,570 submissions, 1,879,731 holdings rows, 100% accession join, 4,683 managers with holdings, 25,816 CUSIPs, no FIGIs.
- 2026 Jun–Aug: 11,852 submissions, 3,830,274 holdings rows, 100% accession join, 8,872 managers with holdings, 34,951 CUSIPs, 22,519 FIGIs.
- No missing accession joins, CUSIPs or negative-value rows. Filing lag is now computed once per accession, not weighted by holdings rows.
- Submission-weighted median / p75 filing lag: 44/45 days (2018) and 41/45 days (2026). 13F-HR/A median lag is 78 days (2018) and 135 days (2026), with p75 231 and 410 days respectively.
- Amendments must be joined from COVERPAGE, not inferred from SUBMISSIONTYPE suffix alone. Each sample contains one 13F-HR with ISAMENDMENT=Y; the 2026 case is directly verified in SEC EDGAR as amendment number 1, “adds new holdings entries.” The code now uses COVERPAGE.ISAMENDMENT and amendment number/type as primary amendment state.
- Observed amendments: 294 (2018) and 406 (2026); RESTATEMENT 189/262, NEW HOLDINGS 105/144. No missing amendment number/type.
- SUBMISSION.tsv contains filing date only, not accepted timestamp. Conservative eligibility is first full regular session strictly after filing date; exact EDGAR acceptance timestamps are still needed for F80-relevant accessions.
- The SEC's quarterly data-set publication is not first public availability. Original EDGAR filings are the authority; see [SEC Form 13F Data Sets](https://www.sec.gov/files/form_13f.pdf) and [verified 2026 filing detail](https://www.sec.gov/Archives/edgar/data/2051980/000137647426000479/0001376474-26-000479-index.htm).
- Full report: [Phase 47](PHASE47_SEC_13F_PIT_ACCESSION_JOIN_AND_AMENDMENT_AUDIT_2026-11-24.md).

## Research decision

- 13F remains a low-frequency ownership-change hypothesis, not proof of informed trading.
- Next gate: historical CUSIP/FIGI-to-F80 crosswalk, resolve 13F-NT notice managers, then an as-of amendment state machine. No signal or OOS test yet.
- No production, universe, exposure, costs, parameter or capital change. F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen.
- Options budget remains USD 0; no vendor sample, license, purchase or quote request.
