# Smart Money Research — Phase 535 addendum

- FINRA ATS Transparency's separate downloadable archive may extend weekly security-by-ATS history to 2014, earlier than the Query API's rolling historic endpoint. The official 2015 guide documents `tblTrading` machine download and per-row shares/trades update dates.
- The old 2014 $12k/$18k ATS data fee schedule was removed by SR-FINRA-2015-023; FINRA made the ATS data public at no charge effective July 13, 2015. Do not treat the old fees as current. The website's user certification/terms remain binding; Phase 535 does not accept them.
- `blocksSummary` is market-wide by ATS/MPID/month and has no ticker field; stock-selection hypotheses are killed.
- Phase 100 API sample: 968,139 rows / 10 partitions; 100% initialPublishedDate on symbol aggregates; observed 21/35-day publication lags; 1,882 later updates; two missing-symbol rows and two LND duplicate-key groups; strict data/integrity and PIT-vintage gates remain open.
- Live GET-only archive audit returned HTTP 530 from GitHub Actions; no table or report data were accessible, and no certification was accepted. Corrected workflow passed 5/5 offline tests; artifact 14672703365. No raw data stored, no alpha test, no signal admitted. F80 remains frozen.
