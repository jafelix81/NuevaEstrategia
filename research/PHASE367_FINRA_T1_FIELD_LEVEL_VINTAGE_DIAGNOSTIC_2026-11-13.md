# Phase 367 — FINRA T1 field-level vintage diagnostic

**Date:** 2026-11-13 UTC  
**Status:** COMPLETED — 24 selected-field mismatches isolated; every mismatch is confined to sub-cent `totalNotionalSum` precision.  
**Research class:** historical row consistency / PIT feasibility only

## Executive result

Phase 367 re-fetched the full 2025-10-20 T1 partition from `weeklySummaryHistoric` and `weeklySummary`: **65,116 rows per dataset, 14 pages each, zero retrieval errors**.

The 24 row mismatches found in Phase 366 are now explained:

- 65,092/65,116 rows match exactly across the canonical business fields.
- The remaining 24 rows differ **only** in `totalNotionalSum`.
- No difference exists in `totalWeeklyShareQuantity`, `totalWeeklyTradeCount`, `lastReportedDate`, `summaryStartDate`, symbol, product, participant identifier, publication/update date, or any other canonical field.
- Current-minus-historic signed sum of the 24 notional differences: **+$0.000003**.
- Sum of absolute differences: **$0.000039**.
- Maximum absolute difference on any one row: **$0.000005**.
- No identity-key groups exist only in one dataset; there are 65,116 unique keys and no duplicate key groups.

The discrepancy is therefore a tiny decimal precision difference in the notional field, not a coverage, symbol, participant, quantity or trade-count difference in this sampled partition. It is immaterial at cent-level economic scale, but the raw difference remains documented rather than silently rounded away.

## 1. Row-level result

| Measure | Result |
|---|---:|
| Rows in current dataset | 65,116 |
| Rows in historic dataset | 65,116 |
| Exact canonical row matches | 65,092 |
| Rows differing only in notional | 24 |
| Rows with any other field difference | 0 |
| Current-only identity keys | 0 |
| Historic-only identity keys | 0 |
| Duplicate identity-key groups | 0 |
| Distinct symbols in each dataset | 2,420 |
| Participant-ID rows in each dataset | 60,282 |
| De Minimis rows in each dataset | 2,420 |

The canonical field set includes `summaryStartDate`. `lastReportedDate` is compared as a field rather than used as a join key. The historic-only `historicalweek` query helper is excluded from the business-row comparison.

## 2. Mismatch distribution

The 24 notional-only differences were distributed as follows:

| Summary type | Mismatched rows |
|---|---:|
| ATS_W_FIRM | 1 |
| ATS_W_SMBL | 4 |
| OTC_W_FIRM | 6 |
| OTC_W_SMBL | 12 |
| OTC_W_SMBL_FIRM | 1 |
| **Total** | **24** |

No share-volume or trade-count differences were detected. No other field mismatch was detected.

## 3. Reproducibility

- GitHub Actions: [run 43456024316](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43456024316) — **SUCCESS**.
- Offline regression tests passed.
- Artifact: [14053738587](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43456024316/artifacts/14053738587).
- Artifact contains only aggregate counts and anonymized comparison statistics. No raw rows, symbols, MPIDs, CRDs or firm names were retained.

## 4. PIT caveat remains unresolved

Row-level equivalence does not establish point-in-time availability. Phase 366 showed that some 2025-10-20 T1 rows carry `lastUpdateDate` values as late as 2026-09-30, long after the initial publication date. The final historical snapshot therefore includes later updates. `lastUpdateDate` and `lastReportedDate` are not automatically publication timestamps, and the historic dataset does not expose intermediate vintages in the current audit.

Do not backdate final values to `initialPublishedDate`. Before any historical signal test, quantify update lags and determine whether a conservative availability ledger can be reconstructed without lookahead. If not, retain FINRA for descriptive/current monitoring only and archive historical alpha use as infeasible.

## 5. Decision

- The current and historic datasets are economically equivalent for the sampled 2025-10-20 T1 partition except for tiny sub-cent notional precision differences.
- Do not round or overwrite the source values silently; preserve the difference and use explicit numeric tolerances only in documented validation checks.
- This single partition does not prove full-history or universe coverage.
- FINRA T1 remains a conditional venue/market-structure candidate; it is not evidence of beneficial-owner identity, trade direction or informed activity.
- No signal admitted. No return, alpha, OOS, bootstrap, LOO or holdout test was run.
- `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen.

Official reference: [FINRA Developer Center — Query API and historical datasets](https://developer.finra.org/docs).
