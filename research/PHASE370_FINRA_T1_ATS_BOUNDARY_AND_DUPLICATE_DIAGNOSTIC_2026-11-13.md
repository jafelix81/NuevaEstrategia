# Phase 370 — FINRA T1 ATS boundary and duplicate-symbol diagnostic

**Date:** 2026-11-13 UTC  
**Status:** COMPLETED — retrieval and diagnostic passed; no signal test authorized.  
**Research class:** source feasibility / PIT and data-grain diagnostic only.

## Question

Diagnose the two residual exceptions from Phase 369:
1. Why the 2021-11-15 T1 ATS partition failed the update-date candidate gate.
2. Why one symbol in 2025-11-10 had two ATS_W_SMBL aggregate rows and failed the strict one-row-per-symbol bridge.

## Execution

Run [43473406924](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43473406924) completed successfully. Job [132050912230](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43473406924/job/132050912230); artifact [14061977572](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43473406924/artifacts/14061977572). Five unit tests passed. Retrieval covered both full partitions: **111,245 rows / 24 pages**, zero errors and all Record-Total values reconciled.

## Finding A — 2021-11-15 is a revised boundary vintage

The partition contains 37,287 ATS rows. Of these, 2,411 have lastUpdateDate later than initialPublishedDate:

| Summary type | Positive-gap rows | Gap days |
|---|---:|---|
| ATS_W_FIRM | 1 | 284 |
| ATS_W_SMBL | 1,205 | 225 (4), 283 (56), 284 (1,145) |
| ATS_W_SMBL_FIRM | 1,205 | 225 (4), 283 (56), 284 (1,145) |

All ATS rows have complete, valid date fields. The initial publication date is 2021-12-06. Later update dates are 2022-07-19, 2022-09-15 and 2022-09-16. This is consistent with a substantially revised early-history vintage, not a missing-date problem.

**Decision:** exclude 2021-11-15 from the date-level PIT candidate sample. Do not treat the historic endpoint's current row values as if the revised values were available on 2021-12-06.

## Finding B — the 2025-11-10 ambiguity is a multi-product symbol, not an unexplained volume mismatch

One symbol (anonymized stable hash 68915d5a1b08021e) has two ATS_W_SMBL aggregate rows:

| Product type | Last reported date | Shares | Trades |
|---|---|---:|---:|
| CTS | 2025-11-10 | 1,830,614 | 24,543 |
| UTP | 2025-11-14 | 5,146,822 | 75,536 |
| **Combined** | — | **6,977,436** | **100,079** |

The symbol has 28 ATS_W_SMBL_FIRM rows and 28 distinct participant keys. Their combined totals are exactly 6,977,436 shares and 100,079 trades. No missing participant IDs, duplicate participant keys, De Minimis rows or invalid numeric values were found for this symbol.

However, the firm rows do not carry productTypeCode. Their lastReportedDate distribution is not a valid allocation key: the aggregate UTP row (5,146,822 shares / 75,536 trades) does not match the firm rows grouped on 2025-11-14 (6,965,752 / 100,071). The combined symbol totals match exactly, but product-specific participant attribution is unavailable.

**Decision:** permit a narrowly defined symbol-level fallback only when there is exactly one aggregate row per distinct nonmissing productTypeCode and the sum across those product types exactly reconciles to the firm-level symbol total. Do not split firm rows across CTS/UTP and do not use lastReportedDate as a universal join key.

## Revised evidence from Phases 369–370

- 19 sampled T1 weeks, 1,022,474 rows, complete retrieval and Record-Total reconciliation.
- Excluding the revised boundary week 2021-11-15 leaves 18/18 sampled weeks with zero ATS post-initial update-date gaps.
- The strict bridge passed 18/19 weeks. The sole exception is resolved at combined symbol grain by the explicit multi-product fallback; 2,419/2,419 symbols reconcile in 2025-11-10, while 2,418/2,418 were unambiguous under the original strict rule.
- The sample is quarterly/stratified, not a complete weekly history. It does not establish coverage of all historical securities, delisted names or first-receipt timestamps.
- initialPublishedDate is a date, not an intraday timestamp. A next-tradable-session rule is a conservative candidate only after broader validation and calendar checks.

## Controls and disposition

No raw symbols, MPIDs, CRDs or firm names are retained. The artifact stores only aggregate counts, date distributions and a stable hash for the single ambiguous symbol. No forward returns, alpha, OOS, bootstrap, LOO or holdout tests were run. No signal is admitted. F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen.

**Next phase:** expand the revised symbol-level bridge and date gate to one full T1 partition per month from 2022-01 through 2025-11; calculate only descriptive broker-dealer reporting concentration after exact reconciliation, and retain the same no-lookahead and anonymization controls.
