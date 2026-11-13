# Phase 369 — FINRA T1 ATS expanded PIT and grain audit

**Date:** 2026-11-13 UTC  
**Status:** COMPLETED — all 19 partitions retrieved; 17/19 pass both original date and strict grain gates. Residual exceptions diagnosed in Phase 370.  
**Research class:** source feasibility / PIT and data-grain audit only.

## Question

Do the Phase 368 T1 ATS date-field result and Phase 361 bridge result survive a wider, stratified historical sample across the FINRA historic weekly-summary window?

## Preregistered sample

19 T1 weeks, stratified across November 2021–November 2025:

2021-11-15; 2022-01-03; 2022-04-04; 2022-07-11; 2022-10-03; 2023-01-09; 2023-04-03; 2023-07-10; 2023-10-02; 2024-01-08; 2024-04-01; 2024-07-08; 2024-10-07; 2025-01-06; 2025-04-07; 2025-07-07; 2025-10-06; 2025-10-20; 2025-11-10.

The workflow retrieves every row in each partition and reconciles Record-Total and pagination headers. No raw rows, symbols, MPIDs, CRDs or firm names are retained.

## Gates

### A. T1 ATS date gate

For all ATS summary types (ATS_W_FIRM, ATS_W_SMBL, ATS_W_SMBL_FIRM, ATS_W_VOL_STATS), measure missing/invalid dates and lastUpdateDate minus initialPublishedDate.

A partition passes the date candidate only if all date fields are complete, ATS rows exist, and no ATS row has a positive update-date gap. This is a conservative candidate gate, not proof of exact intraday availability or a complete vintage archive.

### B. Symbol-to-firm bridge

For ATS_W_SMBL aggregates and ATS_W_SMBL_FIRM firm rows:
- Join at symbol grain only after confirming exactly one aggregate row and one nonmissing productTypeCode per symbol. Firm rows do not carry productTypeCode; do not fabricate it as a row-level key.
- Compare sum of firm shares and trades to the symbol aggregate.
- Count aggregate-only/firm-only symbols, ambiguous aggregate symbols, missing symbols, missing participant identifiers, duplicate participant-symbol keys, De Minimis rows and invalid numeric values.
- Never use lastReportedDate as a universal join key.
- Do not compute HHI or infer beneficial-owner identity.

A partition passes the bridge gate only with full symbol coverage, exact share/trade reconciliation, no ambiguous or orphan symbols, no missing participant identity, no duplicate participant-symbol keys and no De Minimis rows.

## Interpretation constraints

A full retrieval or passing date/grain gate does not establish a predictive signal. FINRA ATS participants are reporting intermediaries, not beneficial owners, and the data do not provide trade direction. A date-level next-session rule remains conditional on the wider sample and holiday/calendar validation.

No forward returns, alpha, OOS, bootstrap, LOO, holdout or production tests are authorized. F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen.


## Execution result — 2026-11-13

Run [43462182950](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43462182950) completed successfully; job [132011676403](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43462182950/job/132011676403); anonymized artifact [14056609868](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43462182950/artifacts/14056609868).

- 19/19 full partitions retrieved: **1,022,474 rows / 215 pages**, zero retrieval errors; every Record-Total reconciled.
- Original ATS date gate passed 18/19 weeks. The sole failure was the historical boundary week 2021-11-15: 2,411 ATS rows had positive lastUpdateDate-minus-initialPublishedDate gaps. Phase 370 showed 4 rows at 225 days, 56 at 283 days and 2,351 at 284 days across ATS summary types. The initial publication date was 2021-12-06; revisions were dated 2022-07-19, 2022-09-15 and 2022-09-16. Exclude this boundary week from a date-level PIT candidate sample.
- Original strict bridge gate passed 18/19. In 2025-11-10, one symbol had two aggregate rows with different productTypeCode values (CTS and UTP). The other 2,418 symbols had exact share and trade reconciliation.
- Phase 370 confirmed the two aggregate rows sum to **6,977,436 shares / 100,079 trades**, exactly equal to the 28 firm rows for that symbol (28 distinct participant keys). The firm rows do not carry productTypeCode and cannot be allocated to CTS versus UTP. Grouping by lastReportedDate does not reconcile the UTP row; therefore lastReportedDate remains rejected as a join key.
- Revised interpretation: a symbol-level bridge can combine aggregate rows only when there is exactly one row for each distinct nonmissing product type and the combined shares/trades exactly equal the firm-level symbol total. This preserves symbol-week totals but does **not** permit product-specific participant attribution. Under that narrowly defined fallback, all 2,419 symbols in 2025-11-10 reconcile at combined symbol grain. This fallback still requires broader monthly validation before admission.
- After excluding the 2021-11-15 boundary week and using the documented multi-product combined-symbol fallback, the sampled evidence is 18/18 date candidates and 19/19 symbol-level total reconciliations. This is not proof of exact intraday PIT, a complete vintage ledger, or full-history coverage.

No raw rows, symbols, MPIDs, CRDs or firm names were retained in artifacts. No forward returns, alpha, OOS, bootstrap, LOO or holdout tests were run. F80 remains unchanged.
