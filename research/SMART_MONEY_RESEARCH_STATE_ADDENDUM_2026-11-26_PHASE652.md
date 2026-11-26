# Smart Money Research State Addendum — Phase 652

**Cutoff:** 2026-11-26 23:08 UTC  
**Main before report:** `6964a7863121387174c44467926f1a00ab8c747e`  
**Phase 652 report commit:** `58d355d14e8e7b593a129dbf1382b5894d27e568`

- **Latest natural run:** SEC Form 144 run [45906061652](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45906061652), 22:38:18 UTC. Both jobs succeeded. Artifacts 15157033731, 15157308416 and 15157992808 were downloaded and inspected.
- **Form 144 delta:** 0 new accessions/events; 10 bounded historical accessions backfilled; 42 detail rows appended; 0 parser errors; 0 source-hash mismatches; 168 backfills remain. Ledger = 835 accessions / 5,537 detail rows; 807 bounded intervals, 18 initial baselines, 0 malformed intervals.
- **10b5-1 descriptive refresh:** 314 formal plan-date accessions / 132 distinct dates; 313 plan dates precede the notice, one is same-day, zero follow it. Median notice lag 182 days, p75 273, maximum 1,687. Remarks polarity: 23 positive explicit, 4 negative explicit, 3 ambiguous, 805 no mention. Eighteen sell-to-cover/tax-withholding accessions; four same-issuer/same-day Fermi notices total 2,253,270 proposed units. Proposed units are not verified executions. No signal admitted.
- **Latest Actions:** 8,356 total; latest 100 = 72 success / 17 failure / 11 cancelled; zero active or queued. Main advanced automatically to `6964a7863121387174c44467926f1a00ab8c747e` via the Form 144 capture commit.
- **Form 4:** latest natural run 45848689364 succeeded; 0 new accessions, 23 transaction rows, 25 then 24 additional footnote references, 10 owner rows, crosswalk 12 rows / 0 eligible.
- **13F:** latest natural run 45839454376 succeeded; 29 accessions are initial baselines with no lower bounds; no holdings downloaded; 0 eligible.
- **FINRA Reg SHO:** latest natural run 45754121648 predates Phase 650 merge; 8/8 files rejected by old parser. PR #247 is merged; PR validation 45895296971 passed 62/62 offline tests and skipped live capture. Await next natural run.
- **CFTC:** latest run 45753716471, 3,043 rows, no new reports/revisions or state change; two prospective Russell observations remain insufficient.
- **Source ranking:** SEC Form 4 remains the leading public event candidate (2006–2026 as-filed dataset; accession-header acceptance join exists, but effective-dated F80 identity/coverage is unresolved). Schedule 13D/G remains high-potential but quarantined (43/44 parent retrieval, CUSIP mismatches and one unresolved parent). SEC MIDAS is a conditional quarterly-release market-quality panel, not dark-pool flow. FINRA T1 ATS remains conditional on archive/PIT/identity/prices. OCC options remains RIGHTS_BLOCKED; Cboe/Databento require written rights. No options quote/purchase/contact; budget USD 0.
- **Killed hypotheses preserved:** N-PORT raw quarter-over-quarter aggregate share-growth remains killed (Phases 386/526); Phase 20C same-day-close FINRA remains NO-GO (Phase 593).
- **Strategy:** `F80_TOP20_PARTIAL50_BASELINE_C20` frozen. No incremental alpha, OOS, bootstrap, LOO or production changes; holdout untouched.

**Next:** continue Form 144 backfill, await natural Form 4/13F/FINRA polls, and prioritize effective-dated issuer/security identity and historical universe coverage before any return study.
