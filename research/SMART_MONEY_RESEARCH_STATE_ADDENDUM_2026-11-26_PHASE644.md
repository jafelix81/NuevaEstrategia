# Smart Money Research State Addendum — Phase 644

**Date:** 2026-11-26 16:48 UTC  
**Main HEAD after Phase 644 report:** `f7ab0f373fede387daa9f5bb05ac9714aa483958`

## New research disposition

- Reconciled Phase 640's broad CFTC TFF historical PIT failure with the narrower Phase 383 Russell E-mini `239742` post-2017 archive panel in Draft PR #58.
- The narrow panel contains 482 report-date/code rows; 480/482 archive pages were valid. The two exceptions (2018-09-25 heading mismatch and 2019-12-24 404) remain excluded.
- Archive `Updated` dates are a conservative candidate availability proxy, not exact first-publication timestamps. The 23 official-schedule cross-checks are supportive but do not certify all 480 valid pages.
- Retain the Russell panel as a **conditional macro-positioning / small-cap regime candidate** only. No alpha test, signal or F80 integration is authorized until the full page-level clock and provenance gate is reproduced.
- Broad multi-contract CFTC archive remains non-PIT-certified; do not apply the Russell subpanel conclusion to other contracts or eras.
- Prospective Phase 384 collector remains the strictest source of new report first-receipt timestamps. Latest observed run [45753716471](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45753716471) reported no new reports/revisions; Phase 643's eight prospective observations across two report-date clusters remain too few for model testing.

## Operational snapshot

- Actions API: 8,350 total runs; latest 100 = 71 success / 17 failure / 12 cancelled; zero active or queued.
- Latest natural SEC runs visible at cutoff: Form 4 [45848689364](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45848689364) at 15:23 UTC, 13F [45839454376](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45839454376) at 14:29 UTC, Form 144 [45827105431](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45827105431) at 13:13 UTC. No later scheduled run was visible by the 16:48 UTC cutoff; zero queued/in-progress runs. This is an observed delivery gap, not proof that workflows are administratively disabled.
- Form 4: feeds successful, zero new accessions in latest poll; 10 detail accessions parsed, 23 detail rows appended, 25 + 24 footnote references, 10 owner rows; 3,404 bounded detail accessions remain; zero signal-eligible rows.
- SEC 13F: four feeds successful in latest poll; 29 initial-baseline accessions (18 HR, 9 HR/A, 2 NT); all have no lower interval bound; holdings not downloaded; zero eligible observations/signals.
- Form 144: 53 feed observations, 825 accessions, 5,495 detail rows; 807 bounded intervals, 18 initial-baseline intervals, 178 detail-backfill accessions remain; zero public-availability-certified or signal-eligible filings.
- The existing scheduler-delivery issue [#194](https://github.com/jafelix81/NuevaEstrategia/issues/194) remains the operational record. Do not dispatch manual or duplicate captures; next natural polls should be observed.

## Open research branches / PRs

- CFTC PR #58 remains Draft and stacked; clean mainline prospective activation PR #60 is merged.
- FINRA T1 ATS PR #50 (Phase 375) and PR #61 (Phase 385) remain Draft on an old stacked branch chain. Their 209-week panel is venue/reporting-participant concentration, not beneficial-owner identity or directional flow. Security-master, historical F80 membership and inactive-price gates remain unpassed.
- SEC 13D/G PR #37 remains Draft; 43/44 parent retrieval and CUSIP discrepancies remain unresolved.
- Cboe options PR #200 remains Draft; strategy use remains blocked pending separate written license authorization. No sample, quote, vendor contact or purchase.
- SEC MIDAS PR #201 remains Draft; retain only as exchange-market-structure/liquidity-state context, not off-exchange or institutional-identity flow.

## Frozen quantitative controls

- `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen.
- Signals admitted: **0**.
- Incremental alpha vs LTM/F80: **none demonstrated**.
- New OOS / bootstrap / LOO: **0**.
- Holdout remains sealed.
- No universe, parameter, capital, exposure, cost or holding-period changes.
- Options data budget remains **USD 0**.
