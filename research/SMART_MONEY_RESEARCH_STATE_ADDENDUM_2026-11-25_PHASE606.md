# Smart Money Research state addendum — Phase 606 (2026-11-25 UTC)

- Completed bounded live SEC Form 13F manager-table audit for 2018 Q1 and 2026 Jun–Aug. Both official ZIPs downloaded using the existing shared project contact fallback; no SEC_USER_AGENT secret was required.
- Latest run 45531619890 completed successfully: offline regression and live audit jobs passed; 8/8 offline tests passed; artifact 14985386673 uploaded.
- OTHERMANAGER2 has multiple rows per accession in both samples (472 and 607 accessions respectively). SUMMARYPAGE OTHERINCLUDEDMANAGERSCOUNT reconciles exactly in 5,017 / 10,036 compared rows. Thus ACCESSION_NUMBER alone is not a sufficient row-level key in the observed data.
- Candidate (ACCESSION_NUMBER, SEQUENCENUMBER) has 20 duplicate pairs in 2018 Q1 and 3 in 2026 Jun–Aug; it is not yet globally unique.
- INFOTABLE.OTHERMANAGER tokens predominantly match OTHERMANAGER2.SEQUENCENUMBER, not OTHERMANAGER.OTHERMANAGER_SK (zero matches to the latter). Zero values are a separate sentinel bucket.
- Remaining reference exceptions: 160,897 unmatched + 10,070 malformed nonzero tokens in 2018; 107,348 unmatched + 82,824 malformed nonzero tokens in 2026. Some are nonnumeric filer-supplied values. No name-based repair is allowed.
- Notice rosters are present for all 1,572 / 1,952 notice accessions in the samples; none of those accessions has INFOTABLE holding rows.
- Phase 605's synthetic parser remains not admitted for live manager attribution until original EDGAR XML reconciles duplicate sequences, unmatched references and nonnumeric values.
- Next gate: stratified original filing XML and information-table XML reconciliation for known exception accessions; then revise manager graph and notice/combination amendment state.
- No alpha/OOS, production, capital or exposure change. F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen; options budget USD 0.
