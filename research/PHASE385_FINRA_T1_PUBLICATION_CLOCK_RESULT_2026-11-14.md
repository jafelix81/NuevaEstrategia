# Phase 385 — FINRA T1 ATS date-level publication-clock result

**Audit date:** 2026-11-14 UTC  
**Disposition:** DATE-LEVEL CLOCK VALIDATED; historical return testing remains NOT AUTHORIZED.  
**Source:** FINRA OTC Transparency weeklySummaryHistoric, Tier T1, target grain ATS_W_SMBL.

## Hosted evidence

- Successful run: [43536354917](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43536354917)
- Anonymized date-only artifact: [14096455337](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43536354917/artifacts/14096455337)
- Artifact SHA-256: `8c5b1f15cca3bc90093afd2a81ba154d793bac22f718fa1f3b3f1b7d3084fcac`
- Phase implementation PR: [#61](https://github.com/jafelix81/NuevaEstrategia/pull/61) (draft; based on the Phase 375 branch, not main).

A second push-triggered run [43536490386](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43536490386) remains in progress. Its head is two commits after the successful run; the compare shows only a workflow-file and report-file change, with no script or test changes. The successful run therefore validates the same retrieval/test implementation. No further run was started.

## Results

| Control | Result |
|---|---:|
| T1 weekly partitions | 209/209 |
| Unique partition pairs | 1,045 |
| Full T1 records paginated | 10,917,933 |
| Target ATS_W_SMBL aggregate rows | 438,822 |
| Pages | 2,292 |
| Partition Record-Total reconciliations | 209/209 |
| One valid initialPublishedDate per partition | 209/209 |
| Publication schedule matches | 209/209 |
| NYSE session mappings strictly after publication | 209/209 |
| FINRA metadata stable during census | Yes |
| Retrieval errors | 0 |

The actual `initialPublishedDate` lag was 21 calendar days for 186 partitions and 22 days for 23 partitions. The 22-day cases align with the next NYSE business session when the nominal date fell on a market holiday. Every observed date matched the expected first NYSE session on or after `weekStartDate + 21 calendar days`.

The conservative daily eligibility rule is:

> Use the first NYSE regular session strictly after the actual `initialPublishedDate`; never use the same-day close/open and never infer an intraday release time.

Examples:
- Week starting 2021-11-15: initial publication 2021-12-06; first eligible session 2021-12-07.
- Week starting 2025-11-10: initial publication 2025-12-01; first eligible session 2025-12-02.

Among the 438,822 target-grain aggregate rows, 432,828 had `lastUpdateDate == initialPublishedDate` and 5,994 had a later update. These are row-grain counts and must not be conflated with Phase 375's symbol-week counts. Phase 375's stricter aggregate-plus-firm revision quarantine remains authoritative: 432,804 of 438,798 symbol-week groups were stable and concentration-ready, representing 98.633996% symbol-week coverage and 96.943175% of mapped aggregate share volume.

## What this validates — and what it does not

**Validated:** the date-level publication clock is consistent across the full 209-week T1 inventory, including the holiday-adjusted 21/22-day schedule. The first subsequent NYSE session is a conservative daily availability bound for stable observations.

**Not validated:**
- exact intraday first receipt or a historical first-receipt ledger;
- intermediate historical vintages beyond the initial and current update dates;
- effective-dated security identity, ticker changes, share classes, inactive/delisted securities or historical F80 membership;
- representativeness outside FINRA T1's NMS/ATS coverage.

The artifact deliberately retains date-level aggregates only; it does not retain symbols, MPIDs, CRDs, firm names or raw rows.

## Research authorization

The artifact confirms:
- `date_level_clock_validated = true`;
- `intraday_first_receipt_certified = false`;
- `effective_dated_security_master_gate_passed = false`;
- `historical_return_test_authorized = false`;
- no forward returns, alpha, OOS, bootstrap, LOO or holdout use;
- no F80, production, universe, capital, exposure or parameter change.

**Decision:** Phase 385 passes the date-level publication-clock gate only. FINRA ATS is not yet admitted to a return or alpha test.

## Next gate

Before any economic test, build and validate a security-identity/universe crosswalk that:
1. uses permanent listing/security identifiers rather than ticker-only joins;
2. handles ticker changes, share classes, symbol reuse, relistings and delisted securities;
3. proves historical eligible-universe membership and overlap with the frozen comparison universe without survivorship leakage;
4. retains the Phase 375 symbol-week quarantine and the conservative Phase 385 session clock;
5. freezes the crosswalk and eligibility rules before inspecting forward returns.

The current 335-name F80 list is a curated fixed set; its original selection rule and complete historical membership have not been recovered. A present-day ticker match is not sufficient to claim survivor-bias-free OOS coverage. CRSP remains the preferred active/inactive return and delisting benchmark if access is available; Databento remains the best-documented two-clock PIT reference layer; Norgate is a potential index-defined alternative. No vendor has been contacted or purchased, and no acquisition is authorized.

## Frozen controls

`F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen. The legacy holdout remains consumed and unavailable. No CAGR target or fixed portfolio holding-period limit is imposed.
