# Smart Money Research — state addendum (Phase 674)

**Updated:** 2026-11-27 local / 2026-11-28 UTC

## Current repository and capture state

- Phase 673 merged via PR #261, commit `221f3aa9433fc66837c2093e2db685a9845d56d1`.
- Phase 403's offline regression no longer hard-codes stale Phase 665 row counts. It uses structural ledger invariants and includes Phase 525 crosswalk tests.
- Phase 403 now recomputes the accession-level Phase 665 PIT/plan-date join and refreshes the descriptive Phase 525 Form 144/Form 4 crosswalk after each successful live Form 144 capture.
- PR validation run 46088870898 passed offline regression. It did not run live capture. At 2026-11-28 00:47:51 UTC, no post-merge scheduled Phase 403 run was visible yet; no manual dispatch or rerun was made. Treat the first natural post-merge run as pending, not as a disabled schedule.

## Form 144

Current reproducible Phase 665 counts: 966 structured accessions / 6,314 detail rows; 908 bounded research-observation eligible; 58 initial-baseline/no-lower-bound; 385 formal plan-date accessions; 352 plan-date + bounded observation; 33 plan-date + baseline; 1,104 event accessions; 138 event-only; zero detail-only, zero PIT mismatches, zero public-availability certifications and zero signal-eligible accessions.

The previous Form 144/Form 4 crosswalk was stale after the 101-accession live capture. Phase 673 makes it refresh after every successful Form 144 capture; until the next scheduled run executes, the refreshed crosswalk is pending.

## SEC 13F

Phase 614 run 46084129349 added four bounded metadata observations, but downloaded no XML or holdings and admitted no research/signal observations. Three accessions are original IronOak Wealth LLC filings for Q4 2025, Q1 2026 and Q2 2026 submitted on 2026-11-27, respectively 283, 196 and 105 calendar days after the standard SEC deadline benchmarks. This is not a legal conclusion about the filer's obligation for each period; its threshold-trigger history has not been adjudicated. The fourth accession (0001717977-26-000005) is AMS Capital Ltda, original Q3 2026 report, filed 11 calendar days after the standard Nov 16 deadline benchmark. Its primary cover page reports 15 entries and tableValueTotal 289276; secondary sources suggest a possible ×1,000 unit issue, but the information table has not been downloaded and no correction is authorized.

Keep reporting period and first-seen/public-availability as separate clocks. A late original report must not be treated as a current-quarter portfolio change. No holdings or units were normalized. AMS Capital's cover-page total remains a unit-review flag only.

## Other sources

- Form 4: latest successful capture remains run 46057111964 (94 new accessions; 21 new transaction rows). No new signal eligibility.
- FINRA Reg SHO: no post-Phase-661 natural capture is visible yet; run 45978861267 was a PR validation with live capture skipped. Await the next scheduled natural poll; do not duplicate it.
- CFTC TFF: 3,043 historical records; only eight prospective observations across two dates in the last reviewed state; no predictive result.
- SEC 13D/G: global live sample remains pending; the prior PR validation skipped its live job.
- Options/Cboe: retain the licensing and historical-vintage gates; no purchase or vendor contact.

## Strategy controls

`F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen. No new signal, alpha claim, OOS result, bootstrap/LOO result, or holdout use. Data spend remains USD 0.
