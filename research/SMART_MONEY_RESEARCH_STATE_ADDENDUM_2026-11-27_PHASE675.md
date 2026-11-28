# Smart Money Research state addendum — Phase 675

**Audit cutoff:** 2026-11-27 local / 2026-11-28 UTC  
**PR:** [#262](https://github.com/jafelix81/NuevaEstrategia/pull/262)  
**Branch:** \`phase675-13f-latest-report-period-selector\`  
**Base:** \`phase613-sec-13f-legal-dissemination-floor\` (stacked; not main)

## Completed in this phase
- Added \`select_latest_holdings_period\` to the Phase 48 13F manager-period state machine.
- Selection uses maximum \`report_period\`; filing date and accession order are not selection keys.
- Late original filings and late amendments remain attached to their historical report periods.
- A blocked latest period never falls back to older holdings.
- A newer 13F-NT remains a notice-only freshness warning, not a zero-holdings portfolio.
- Older blocked periods are surfaced as historical gaps; period-to-period features remain ineligible across those gaps.
- Added eight synthetic regression cases and a PR-only offline Actions workflow.

## Evidence motivating the regression
Phase 614 run [46084129349](https://github.com/jafelix81/NuevaEstrategia/actions/runs/46084129349) captured four bounded metadata observations and downloaded zero filing XML/holdings rows. Phase 674 adjudicated three late original IronOak filings for 2025-12-31, 2026-03-31 and 2026-06-30, all filed 2026-11-27, while IronOak's 2026-09-30 report had already been filed 2026-11-06. This is a concrete case where latest filing date is not latest portfolio period.

## Validation status
- PR #262 created as draft, stacked on PR #230's Phase 613 branch.
- GitHub Actions [run 46092474064](https://github.com/jafelix81/NuevaEstrategia/actions/runs/46092474064): success; 22/22 tests passed. The first two attempts exposed and then corrected a test-fixture ordering assertion (ascending expectation vs descending selector output).
- No live SEC capture or holdings download was run.

## Other source state
- Form 144: Phase 673 dynamic-ledger and post-capture reconciliation repair passed PR offline validation. First natural post-merge scheduled capture remains pending; run 46079844681 predates the Phase 673 merge and run 46088870898 was PR validation with live capture skipped.
- Form 4: latest successful scheduled capture in the reviewed run set is 46057111964; no new signal eligibility.
- FINRA Reg SHO: Issue #214 remains fail-closed due unresolved duplicate BCPC/TPC symbol rows. No rows accepted, no volume aggregation and no signal.
- CFTC TFF: 3,043 historical rows; only eight prospective observations across two dates in the last reviewed state. Context-only.
- SEC 13D/G: global live sample remains pending.
- Options/Cboe: historical-vintage, sample and license gates remain open. No quote request, vendor contact, purchase or data spend.

## Strategy controls
\`F80_TOP20_PARTIAL50_BASELINE_C20\` remains frozen. No new signal, alpha claim, return test, OOS result, bootstrap/LOO result, or holdout use. Data spend remains USD 0.
