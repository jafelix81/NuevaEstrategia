# Smart Money Research State Addendum — Phase 643

**Date:** 2026-11-26  
**Documentation commit:** `9095e1739b7bb2883043b8fbe91d0e19c0696b97`  
**Capture state:** first natural post-merge Form 4 and 13F polls succeeded; Form 144's post-merge natural poll had already succeeded in Phase 642. All three SEC capture workflows are operational on their current schedules. No human action is required to repair SEC_USER_AGENT.

## New evidence

- **Form 4 — run 45848689364:** both feeds and both jobs passed. Zero new accessions/event rows; two prior-watermark entity observations. The new `entity_duplicate_audit.csv` was generated and committed; both rows show zero exact or cross-page duplicates. This validates sidecar execution, not a positive duplicate case. Ten-accession backfills added 23 detail rows, 25 + 24 footnote references, and 10 owner rows; zero parse errors; zero signal-eligible crosswalk matches.
- **SEC 13F — run 45839454376:** all four feeds returned HTTP-OK and passed continuity gates. 29 first-seen baseline observations: 18 13F-HR, 9 13F-HR/A, 2 13F-NT, 0 13F-NT/A. The environment's SEC_USER_AGENT secret was empty; the Phase 401 shared-contact fallback worked. Because this was the first successful poll, all records are `INITIAL_BASELINE_NO_LOWER_BOUND`; metadata/research/signal eligibility all remain zero. No holdings or raw transaction rows were downloaded.
- **Form 144 — run 45827105431:** latest natural post-merge capture remains successful; 53 feed observations, zero new accessions, 52 detail rows added by bounded backfill, 825 accessions / 5,495 detail rows, 807 bounded intervals, 18 initial-baseline rows, zero public-availability-certified or signal-eligible filings.

## Actions and branch state

- Latest 100 Actions runs: 71 success / 17 failure / 12 cancelled; zero queued, waiting, requested, pending or in-progress.
- Repository total: 8,350 workflow runs at audit cutoff.
- No manual dispatch, rerun or duplicate capture was launched.
- Relevant open research PRs remain Draft, including the SEC 13F chain #221–230, SEC 13D/G #37, FINRA T1 ATS #50/#61, options #200 and MIDAS #201. No stale branch chain was merged.

## Source gates

- Form 4: natural post-merge entity-sidecar validation passed; continue bounded backfills and identity/acceptance-clock quarantine.
- Form 144: descriptive proposed-sale/10b5-1 context and negative controls only; never treat proposed sales as executions.
- 13F: next natural poll can bound genuinely new accessions. The 29 initial-baseline records cannot be retroactively given a lower bound; no holdings-level signal until PIT dissemination, amendment, manager, security and historical-universe gates pass.
- 13D/G: 43/44 parent retrieval and CUSIP mismatches remain unresolved as in Phase 636.
- FINRA Reg SHO: eight files rejected under BCPC/TPC row-grain gate; zero accepted observations.
- FINRA T1 ATS: 209-week venue-concentration panel remains a conditional market-structure hypothesis, not investor identity or smart-money flow; identity, historical universe and inactive-price gates remain.
- CFTC TFF: 3,035 historical rows remain unverified PIT proxies; eight prospective observations across two report-date clusters are insufficient for a model test.
- Options / MIDAS: feasibility only; no vendor contact, sample, quote, license or purchase. Options budget remains USD 0.

## Quantitative disposition

- Signals admitted: **0**.
- Incremental alpha vs frozen LTM/F80: **none demonstrated**.
- New OOS/bootstrap/LOO: **0**.
- Holdout remains sealed.
- `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen; no universe, parameter, exposure, cost, capital or holding-period change.

## Next gates

1. Continue natural SEC 13F polling; only newly observed entries can obtain bounded first-seen intervals.
2. Continue Form 4 and Form 144 natural capture and bounded backfills.
3. Resolve source-specific PIT, identity, historical-universe and inactive-security coverage before any return study.
4. Keep all source hypotheses quarantined until incremental tests versus LTM/F80 can be run with identical exposure/costs and chronological OOS, bootstrap and LOO discipline.
