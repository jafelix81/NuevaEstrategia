# Smart Money Research State Addendum — Phase 642

**Date:** 2026-11-26  
**Main capture commit:** `e594a7a46b0ec43bf8b6c3490b5b0eb1829b6ae7`  
**Disposition:** post-merge Form 144 natural poll and quality gates passed; no new filings or signal. Reclassify FINRA T1 ATS as venue-concentration/market-structure research, not investor flow.

## New evidence

- Natural Form 144 scheduled run [45827105431](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45827105431) completed both offline and live jobs successfully after PRs #244/#245.
- 53 feed observations appended (50 Form 144, 3 Form 144/A); both feeds complete, no errors/gaps, no new accessions.
- Structured backfill parsed 10 accessions and appended 52 detail rows; 178 remain.
- Structured detail ledger: 825 accessions / 5,495 rows; 0 parse errors and 0 source-hash mismatches.
- Quality audit: 807 bounded poll intervals, 18 initial-baseline rows without a lower bound, 0 malformed intervals, 0 exact-public-availability certifications and 0 signal-eligible filings.
- Refreshed 10b5-1 audit: 304 formal plan dates / 130 distinct dates; 23 positive, 4 negative, 3 ambiguous and 795 no-mention Remarks classifications; 18 sell-to-cover/tax-withholding accessions.
- Four Fermi notices remain negative controls, totaling 2,253,270 proposed units; not executed trades.

## Current run state

Latest 100 Actions runs at audit cutoff: 71 success, 17 failure, 12 cancelled; zero active/queued. No manual dispatch or rerun.

Latest natural captures:
- Form 144: post-merge success, run 45827105431.
- Form 4: run 45759597509, pre-merge of PR #240; post-merge entity duplicate sidecar validation pending.
- SEC 13F: run 45751086501, pre-merge of PR #243 and failed before SEC request; post-merge natural poll pending.
- CFTC TFF: run 45753716471, no new report/revision.
- FINRA Reg SHO: run 45754121648, eight files rejected; zero accepted observations.

## Source priority

1. Form 4: await natural post-merge validation, then preserve owner/transaction identity and Rule 10b5-1 negative controls.
2. Form 144: continue descriptive backfill; proposed sale and plan metadata are not execution or directional proof.
3. FINRA T1 ATS: 209-week historical panel and date-level publication census are promising for ATS venue concentration/liquidity hypotheses, but not institutional investor flow. Effective-dated identity, historical F80 membership and inactive/delisted price coverage remain blocking. PRs #50/#61 remain Draft and heavily diverged; do not merge wholesale.
4. SEC 13F and 13D/G: preserve amendment, manager, reporting-person and CUSIP identity gates; no stale branch merge.
5. CFTC: prospective collection only; eight observations across two report-date clusters are insufficient for a model test.
6. Options: TradeFlow/OPRA/Open-Close remain conditional on versioned history, first receipt/revisions, 335-name coverage, rights and cost. No vendor contact or spend; budget USD 0.
7. FINRA Reg SHO: keep quarantined until BCPC/TPC row-grain and security identity are authoritatively resolved.

## Quantitative controls

- Signals admitted: 0.
- Incremental alpha vs frozen LTM/F80: none demonstrated.
- New OOS/bootstrap/LOO: 0.
- Holdout remains sealed.
- `F80_TOP20_PARTIAL50_BASELINE_C20` frozen.
- Universe, parameters, exposure, costs, capital, holding-period policy and production unchanged.
