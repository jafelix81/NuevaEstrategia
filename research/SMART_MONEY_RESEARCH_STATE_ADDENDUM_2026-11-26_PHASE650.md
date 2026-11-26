# Smart Money Research State Addendum — Phase 650

**Cutoff:** 2026-11-26 20:56:40 UTC  
**Main at branch point:** `a218c79922628d34a87ee3fd59ea3d9c0576ac4c`

- **FINRA Reg SHO:** Phase 469's latest inspected scheduled poll returned eight HTTP 200 CNMS files, all rejected by the old whole-file duplicate-symbol gate. Artifact-level review found only BCPC and TPC repeated across those files; their facility sets overlap and no repeated row is byte-identical. Both tickers are absent from the frozen 335-symbol snapshot. Phase 650 changes the parser to quarantine every row for a repeated symbol while retaining unique symbols in a marked partial file. No rows are summed or selected by heuristic.
- **Historical first-seen:** the eight earlier invalid files are not promoted. Their old poll status was `invalid_file`, not a qualifying prior `not_available` event; the new parser can only create eligible first-seen observations prospectively under the existing clock rules.
- **FINRA interpretation:** daily reported short volume is not short interest and does not identify investor type or informed intent. The source remains a hypothesis for incremental flow information.
- **CFTC Russell:** Phase 648 remains merged and reproducible; two prospective observations are insufficient for outcome testing. Phase 649's price-rights gate remains unresolved.
- **SEC Form 4 / 13F / Form 144:** last inspected scheduled runs remain successful, but no later scheduled SEC captures were visible at this cutoff. Their current baseline/identity/acceptance gates remain unchanged.
- **Options / OPRA:** no purchase, sample request, quote request, vendor contact or license acceptance. Budget USD 0.
- **Actions preflight:** 8,354 total runs; latest 100 = 70 success, 18 failure, 12 cancelled; zero queued or in progress. 85 open PRs were reviewed. No existing workflow was dispatched or duplicated.
- **Strategy:** `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen. No new alpha, OOS, bootstrap, LOO or portfolio evidence. No production strategy changes.

**Phase 650 status:** code and tests prepared on `phase650-finra-cnms-partial-symbol-quarantine`; PR CI must pass before merge. The change is limited to FINRA source parsing and metadata diagnostics.
