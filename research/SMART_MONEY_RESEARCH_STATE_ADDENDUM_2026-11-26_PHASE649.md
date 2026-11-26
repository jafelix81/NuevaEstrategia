# Smart Money Research State Addendum — Phase 649

**Audit cutoff:** 2026-11-26 20:20 UTC  
**Main HEAD before addendum:** `b4d57f524c6ecd79e18c23cbec1bd853a619e047`  
**Phase 649 report:** [Russell outcome-source rights and daily-history feasibility audit](PHASE649_RUSSELL_PRICE_AND_VOLATILITY_SOURCE_RIGHTS_AUDIT_2026-11-26.md)  
**Disposition:** the Russell outcome-price/volatility gate remains blocked under the current USD 0 / no-vendor-contact authorization. FRED-hosted Cboe series and Cboe website content are not admitted to strategy development without explicit rights. IWM remains an unverified daily total-return proxy candidate.

## 1. Latest Actions / repository state

- 8,354 total Actions runs.
- Latest 100: 70 successful, 18 failed, 12 cancelled.
- Zero queued, waiting, requested, pending or in-progress runs at cutoff.
- Main HEAD before this addendum: `b4d57f524c6ecd79e18c23cbec1bd853a619e047`.
- PR #246 / Phase 648 is merged. Final run [45883866597](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45883866597) passed 10/10 tests. Artifact [15148442172](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45883866597/artifacts/15148442172) was downloaded and inspected; it contains two prospective Russell observations, both below the fixed 80th-percentile threshold, and `signals_admitted=0`.
- 85 open PRs remain, many stacked Draft research branches. No old stack was merged. Relevant Drafts include #200 Cboe OPRA, #201 SEC MIDAS, #188 Massive options, #159 FINRA short interest, #50/#61 FINRA T1 and #57 price-provider fallback.

## 2. Natural-capture state at cutoff

| Source | Latest scheduled run | Verified result | Signal status |
|---|---|---|---|
| SEC Form 4 | [45848689364](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45848689364), 15:23:55 UTC | Both feeds successful; bounded owner enrichment appended 10 owner rows; descriptive crosswalk 12 rows; 2 unresolved acceptance-clock rows; 7 multi-owner accessions quarantined | 0 eligible matches |
| SEC 13F | [45839454376](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45839454376), 14:29:01 UTC | 29 new accessions; all initial baseline with no lower bound; no holdings downloaded | 0 eligible observations |
| SEC Form 144 | [45827105431](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45827105431), 13:13:48 UTC | 53 feed observations; 825 structured accessions; 5,495 detail rows; 178 backfill accessions remain | 0 eligible observations |
| CFTC TFF | [45753716471](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45753716471), 04:12:21 UTC | No new reports/revisions; 3,043 total records; archive rows remain signal-ineligible | 0 eligible observations |
| FINRA Reg SHO daily first-seen | [45754121648](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45754121648), 04:16:05 UTC | 0 first-seen / eligible events; no raw market data persisted | 0 eligible observations |

All listed jobs completed successfully and their artifacts were unexpired at audit. Form 4's scheduled 20:17 UTC slot was not visible by the 20:20 UTC cutoff. This is an observed schedule-delivery gap, not proof of administrative disablement. No manual dispatch, rerun or duplicate poll was made. The next Form 144 and 13F schedule slots had not yet occurred at cutoff.

## 3. SEC Form 4 interpretation guard

The latest Form 4 enrichment result is descriptive only:
- 10 owner rows appended in the bounded batch.
- 12 crosswalk rows, but zero signal-eligible matches.
- Two unresolved acceptance-clock rows.
- Seven multi-owner accessions remain quarantined.
- The new `entity_duplicate_audit.csv` contains two observations; both are prior-watermark rows and neither is an exact duplicate.

Do not equate Form 4 filing date, acceptance timestamp, first-seen poll interval, owner identity, or transaction-line attribution. Do not count every proposed Form 144 sale or Form 4 disposition as an executed discretionary sale. Existing 10b5-1, option exercise, tax/withholding, gifts, multi-owner and acceptance-clock controls remain in force.

## 4. Source rights decision

Phase 649 rejects FRED `RVXCLS`/`VIXCLS` and direct Cboe website content as unlicensed inputs for this software/strategy workflow. Cboe's historical VIX page is technically accessible but its Use of Content page requires prior approval and a signed license. The FRED series is Cboe-copyrighted and FRED terms restrict use of FRED content in software development. IWM tracks the Russell 2000 and has a 2000-05-22 inception, but the official page did not provide an accessible reproducible daily total-return history in this audit. No data were downloaded.

No vendor was contacted, no quote or trial requested, no account/API key created and no data purchased. The existing options-data budget remains USD 0.

## 5. Research priorities

1. Continue natural CFTC capture; do not backdate any report or use archive rows as PIT signals.
2. Keep the Russell fixed-reference feature pipeline offline and outcome-blind until a lawful price/control source is frozen.
3. Continue Form 4/144 bounded enrichment and preserve all uncertainty/negative controls.
4. Continue 13F first-seen observation collection; no holdings panel or broad-universe return test until the identity/coverage gates pass.
5. Treat FINRA T1 ATS as venue/firm concentration, not investor identity; security identity and total-return history remain separate blockers.
6. Keep FINRA Reg SHO / short interest in quarantine until complete snapshots, structural-zero proof, identity and publication clocks pass.
7. Keep SEC MIDAS as a conditional exchange-market-structure/liquidity hypothesis, not dark/off-exchange institutional accumulation.
8. Keep Cboe OPRA/Open-Close and Massive options parked pending historical PIT/correction clocks, exact-universe coverage and rights.

## 6. Frozen strategy controls

- `F80_TOP20_PARTIAL50_BASELINE_C20`: frozen and unchanged.
- Incremental alpha: none demonstrated.
- New OOS / bootstrap / LOO: none.
- Legacy holdout: untouched.
- No universe, parameter, capital, exposure, cost, holding-period or production change.
- Options-data budget: USD 0.
