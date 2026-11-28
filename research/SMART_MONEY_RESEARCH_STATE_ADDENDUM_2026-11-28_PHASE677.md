# Smart Money Research — state addendum (Phase 677)

**Updated:** 2026-11-28 UTC  
**Main HEAD at audit preflight:** `2a0d92463cc8a9b5915b673aa61e4f7d2cebba3f`  
**Phase 677 integration:** PR [#263](https://github.com/jafelix81/NuevaEstrategia/pull/263) merged at 2026-11-28 03:51:59 UTC; merge commit `c854cb04797ad60611c5df5156d16f8a6fd0f199`.

## Repository and Actions preflight

- Latest 100 Actions runs: 79 success / 17 failure / 4 cancelled; 0 active and 0 queued among the returned 100; 8,405 total runs.
- Branch census before Phase 677: 422; open PRs before Phase 677: 86. Phase 677 added one branch and one PR, then merged the PR; the branch remains.
- Latest run [46099559273](https://github.com/jafelix81/NuevaEstrategia/actions/runs/46099559273) (Phase 476 Form 4) completed both offline and live-capture jobs successfully; its artifact is [15244348107](https://github.com/jafelix81/NuevaEstrategia/actions/runs/46099559273/artifacts/15244348107).
- Phase 675 PR #262 remains draft and based on draft PR #230; its latest offline validation [46092535366](https://github.com/jafelix81/NuevaEstrategia/actions/runs/46092535366) passed. Do not merge the selector until the Phase 612/613 dependency chain is reconciled.

## Phase 677 — AMS Capital unit anomaly

- Primary SEC accession `0001717977-26-000005` identifies AMS Capital Ltda, Form 13F-HR, filing date 2026-11-27, accepted 14:32:31 ET, report date 2026-09-30, 15 entries, and cover-page value total 289,276 rounded to the nearest dollar.
- The SEC-rendered information table labels each value as nearest dollar; all 15 displayed row values sum to 289,276.
- Seven eligible unique common-stock CUSIPs (six `COM`, one `COMMON STOCK`) were checked against same-report-date closes. All seven imply a 1,000× scale within 0.5%; median absolute relative error 0.002337%, maximum 0.004534%. Factor 1 has zero passing rows and median error 99.9000%.
- Under the existing Phase 671 thresholds, the filing is a `LEGACY_THOUSANDS_CANDIDATE`. This is retrospective integrity evidence, not a trading feature.
- The raw XML was not downloaded or hashed; the evidence uses SEC XSL-rendered primary filing pages and secondary close references. Only 7/15 rows were price-checked. No rescaling, parser integration, return test, OOS, bootstrap, LOO, or holdout use.

## Other live-source state

- Form 4: 156 new unique accessions in run 46099559273; metadata only, zero research/signal-eligible rows. Backfills appended 32 transaction-detail rows, 12 owner rows and 29 footnote references; transaction-line owner attribution remains unverified.
- Form 144: latest scheduled live capture [46079844681](https://github.com/jafelix81/NuevaEstrategia/actions/runs/46079844681) ran before PR #261 / Phase 673 merged. It added 101 accessions and 588 detail rows (ledger 966 accessions / 6,314 rows); post-merge natural validation of the new Phase 665 and Phase 525 steps is still pending. Do not dispatch a duplicate capture.
- SEC 13F feed: [46084129349](https://github.com/jafelix81/NuevaEstrategia/actions/runs/46084129349) added four metadata accessions, but the collector downloaded zero holdings rows. Phase 677's AMS table review was a separate SEC primary-page audit.
- FINRA Reg SHO: issue [#214](https://github.com/jafelix81/NuevaEstrategia/issues/214) remains blocked by unresolved BCPC/TPC duplicate-symbol row grain; keep the parser fail-closed.
- CFTC TFF: 3,043 rows remain; prospective coverage remains insufficient for the preregistered OOS test.
- SEC 13D/G: global live sample remains pending; its workflow is manual-only and was not dispatched.
- Options/OPRA/Cboe: historical-vintage, PIT, and license/redistribution gates remain unresolved; no vendor contact or purchase.

## Strategy controls

`F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen. No new signal, alpha claim, return test, OOS result, bootstrap/LOO result, or holdout use. Data spend remains USD 0.

## Next priorities

1. Retrieve/hash AMS Capital's raw information-table XML and reconcile all 15 rows.
2. Continue 13F unit-control expansion to at least 20 independent positive/negative manager filings.
3. Verify the first natural scheduled Form 144 capture after Phase 673 merge.
4. Continue FINRA row-grain resolution and SEC 13D/G global sample only when the existing workflow/credentials permit; do not duplicate runs.
5. Keep all institutional signals descriptive until PIT availability, historical universe mapping, and incremental OOS economics are demonstrated.
