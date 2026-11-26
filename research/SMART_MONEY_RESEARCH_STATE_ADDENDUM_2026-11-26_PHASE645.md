# Smart Money Research State Addendum — Phase 645

**Audit cutoff:** 2026-11-26 17:45 UTC  
**Base main HEAD:** `e377c25e35f37d180ad860f889f4283127eb7ae6`  
**Phase 645 report:** [CFTC Russell prospective-vintage and release-clock reconciliation](PHASE645_CFTC_RUSSELL_PROSPECTIVE_VINTAGE_AND_RELEASE_CLOCK_RECONCILIATION_2026-11-26.md)  
**Disposition:** data-clock reconciliation completed; no predictive test or model change.

## New evidence

- Reconciled the 482-row post-2017 Russell E-mini archive panel from Phase 383 with the two later prospective report dates in the Phase 384 append-only event ledger.
- The prospective dates are 2026-11-10 and 2026-11-17, first received at 2026-11-18 03:44:57Z and 2026-11-21 03:17:36Z, respectively.
- Both first receipts occurred after the official CFTC scheduled release: 31h 14m 57s and 6h 47m 36s later. Use actual pipeline receipt as the conservative knowledge upper bound; it is not exact first-public availability.
- Earliest eligible XNYS sessions are 2026-11-18 and 2026-11-23.
- Russell E-mini normalized net/OI changes across the two prospective vintages: Asset Manager +2.2085 pp, Dealer -2.3418 pp, Leveraged Money +0.8717 pp; open interest +4.3475%. The category directions are mixed.
- The historical archive remains 480/482 valid pages, with 2018-09-25 heading mismatch and 2019-12-24 404 excluded. The 23/23 schedule cross-checks do not certify every historical page or exact first-public timestamps.
- The current CFTC inventory remains 3,035 historical archive rows plus eight prospective observations across two report-date clusters; zero signal-eligible rows.

## Current operational state

- Latest CFTC scheduled capture [45753716471](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45753716471): successful, no new report/revision, 3,043 rows.
- Latest Form 4 [45848689364](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45848689364): successful; zero new accessions, bounded structured backfill continues, zero eligible signal rows.
- Latest SEC 13F [45839454376](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45839454376): successful initial baseline of 29 accessions, all without lower first-seen bounds; no holdings downloaded.
- Latest Form 144 [45827105431](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45827105431): successful; 825 accessions / 5,495 detail rows, 807 bounded intervals, 18 initial-baseline rows, zero public-availability-certified or signal-eligible filings.
- Latest FINRA Reg SHO [45754121648](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45754121648): eight HTTP-200 files, eight rejected by BCPC/TPC row-grain gate; zero admitted rows.
- Actions inventory: 8,350 total runs; latest 100 = 71 success / 17 failure / 12 cancelled; zero active or queued at cutoff. No manual dispatch or rerun was launched.
- The next official CFTC release is scheduled for Monday 2026-11-30 at 3:30 p.m. ET after the Thanksgiving delay. Keep weekday polling and use the actual first receipt; no manual poll is needed.

## Source decisions

- CFTC Russell 239742 post-2017: retain as a conditional macro/small-cap positioning candidate; not strict historical PIT and not stock-level informed flow.
- CFTC broad historical archive: remain excluded from PIT features, labels and returns.
- Phase 387: remains the pre-registered ES/NQ weekly downside-risk hypothesis. Do not add Russell to it; any Russell-specific study needs a separate preregistration before outcomes are inspected.
- FINRA T1 ATS: 209-week venue/reporting-participant concentration panel remains conditional; security identity, historical F80 membership and inactive-security price coverage are still unpassed.
- FINRA Reg SHO: quarantine remains.
- SEC 13D/G: 43/44 parent documents retrieved; CUSIP/identity exceptions remain quarantined.
- Options / OPRA / Open-Close: feasibility only; no sample, quote, vendor contact, license or purchase; budget USD 0.
- SEC MIDAS: exchange market-structure candidate only, not dark-pool or participant-identity evidence.

## Quantitative controls

- Signals admitted: **0**.
- Incremental alpha vs frozen LTM/F80: **none demonstrated**.
- New OOS / bootstrap / LOO: **0**.
- Holdout remains sealed.
- `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen.
- No universe, parameters, capital, exposure, costs or holding-period policy changed.
- No paid data or options-data spend.

## Next gates

1. Continue actual first-receipt polling through the 2026-11-30 CFTC release and record any cadence change; do not assume the announced semiweekly transition has reached TFF.
2. Keep the two prospective report-date clusters separate from the historical archive proxy.
3. Do not calculate a Russell predictive test until a separate preregistration and defensible price/market-regime outcome panel exist.
4. Continue SEC capture and backfill without converting acceptance/first-seen upper bounds into exact public timestamps.
5. Resolve FINRA T1 historical identity/universe/prices before any return test; keep Reg SHO rows rejected until consolidated-symbol semantics are resolved.
