# Smart Money Research — state addendum (Phase 676)

**Updated:** 2026-11-28 UTC

## Current repository state

- Main HEAD after the latest scheduled Form 4 capture: `5a85dcc2ff90d92c277f8544642d4c69e4b7e97d`.
- Latest 100 Actions runs: 79 success / 17 failure / 4 cancelled / 0 active; 8,405 total runs.
- Branch inventory: 422; open PRs: 86.
- Phase 675 PR #262 remains draft and stacked on draft PR #230. Its latest validation passed 22/22 tests, but the selector is not merged into main.

## Form 4

- Latest scheduled run [46099559273](https://github.com/jafelix81/NuevaEstrategia/actions/runs/46099559273) completed successfully.
- 156 new unique Form 4 accessions / 156 canonical issuer events; 156 bounded metadata-only observations.
- Entity ledger: 351 candidate occurrences collapse to 156 unique accessions; 86 distinct issuer CIKs and 180 distinct reporting-owner CIKs. There are 149 one-owner and 7 multiple-owner filings.
- Zero missing/multiple issuer identities, unknown roles, quarantines, path/entity CIK mismatches or exact duplicate entity-key groups.
- Accession prefix equals issuer CIK for only 36/156 filings; never infer issuer identity from the accession prefix.
- No public-availability certification, research eligibility or signal eligibility. The collector did not download filing XML/text for this capture.
- Backfills appended 32 transaction-detail rows, 12 owner rows and 29 footnote references with zero parser errors. Remaining bounded queues: 3,614 transaction-detail accessions, 20 owner-identity accessions and 30 footnote accessions. Transaction-line owner attribution remains unverified.

## Form 144 / Form 4 crosswalk

- The latest Form 4 run rebuilt the crosswalk against the prior scheduled Form 144 capture: 17 proposed-sale matches, 16 Form 4 accessions, 12 issuers and 16 owners.
- Nine multi-owner accessions and three ambiguous transaction-reuse cases were quarantined; two Form 144 acceptance clocks remain unresolved.
- Zero signal-eligible matches. Historical F80 membership and intraday execution time are not verified.
- The crosswalk is refreshed, but Phase 673's accession-level PIT/plan-date join still awaits the first natural scheduled Form 144 capture after merge. Run 46088870898 was PR validation; live capture was skipped.

## Other sources

- SEC 13F: run 46084129349 added four metadata accessions; no holdings downloaded; no eligible observations. Phase 675 report-period selector is still draft PR #262.
- FINRA Reg SHO: latest scheduled run 45939887443 returned seven HTTP 200 files, but 14 duplicate symbols led to 28 row occurrences quarantined; zero eligible observations. Later Phase 661 PR validation did not run live capture.
- CFTC TFF: run 45939298160 reported no new report/revision; 3,043 rows remain; no signal-eligible historical rows.
- SEC 13D/G: run 45988473657 passed offline regression but skipped the live sample.
- Options/OPRA/Cboe: no new Actions run in the latest 100; historical-vintage, PIT and license/redistribution gates remain unresolved. No vendor contact or data purchase.

## Strategy controls

`F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen. No new signal, alpha claim, return test, OOS result, bootstrap/LOO result or holdout use. Data spend remains USD 0.
