# Phase 200 — SEC MIDAS duplicate and negative-field diagnostics

**Date:** 2026-11-08  
**Hosted run:** [42435872069](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42435872069)  
**Artifact:** [phase200-sec-midas-duplicate-negative-diagnostics, 13599572534](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42435872069/artifacts/13599572534)  
**Disposition:** duplicate-field audit passed for six disputed quarters; activity fields do not conflict in any duplicate key. Negative Hidden/HiddenVol numerator values remain unexplained and quarantined.

## 1. Duplicate security-day keys: resolved as rank-only

Phase 200 re-downloaded and parsed all six disputed SEC MIDAS quarters. The audit key is (Ticker, Date, Security). Every duplicate group was compared field-by-field against the first row.

| Quarter | Valid rows | Tickers | Dates | Duplicate groups | Exact | Rank-only conflicts | Activity conflicts | Negative Hidden | Negative HiddenVol |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 2014 Q2 | 318,489 | 5,168 | 63 | 0 | 0 | 0 | 0 | 75 | 76 |
| 2016 Q1 | 323,454 | 5,393 | 61 | 2 | 0 | 2 | 0 | 82 | 184 |
| 2016 Q2 | 338,183 | 5,393 | 64 | 61 | 6 | 55 | 0 | 77 | 147 |
| 2016 Q3 | 338,099 | 5,400 | 64 | 68 | 0 | 68 | 0 | 70 | 153 |
| 2016 Q4 | 331,875 | 5,365 | 63 | 43 | 2 | 41 | 0 | 78 | 244 |
| 2019 Q4 | 369,433 | 5,902 | 64 | 6 | 0 | 6 | 0 | 4 | 9 |

**Key result:** across all six quarters there were **zero duplicate groups with conflicting activity fields**. Every conflicting group differed only in McapRank, PriceRank and/or TurnRank; the other duplicate groups were exact. No duplicate rows were deleted.

This materially narrows the data-quality problem. Activity measures can be treated as identical within these duplicate security-day keys in the six audited quarters, but rank fields are not reliable at row level and should be excluded or separately reconciled. Any future deduplication must be explicit and must preserve the original raw rows/hashes.

## 2. Negative values are not a simple -1 sentinel

The Phase 199 field naming was corrected: Hidden is a raw hidden-trade-count numerator, with TradesForHidden as its denominator; HiddenVol('000) is a hidden-volume numerator in thousands of shares, with TradeVolForHidden('000) as its denominator. The SEC methodology's Hidden Rate and Hidden Volume are derived ratios, not the raw numerator columns themselves.

Across all six quarters:
- Negative Hidden values: 386.
- Negative HiddenVol values: 813.
- Negative values are not concentrated at -1; distributions include material negatives (Hidden down to -251; HiddenVol down to -2,527.154 in the six-quarter sample).
- Every negative numerator observation had a positive, non-missing denominator in these samples. Therefore the negatives are not explained by a zero or missing denominator.
- The exact negative-value histograms and up to 12 row examples per field/quarter are preserved in the JSON artifact.

Do not assume these are documented sentinels. They may reflect corrections, net adjustments, feed behavior or source anomalies; the archive README files and SEC documentation have not yet been reconciled. Affected observations remain quarantined.

## 3. Derived hidden-volume share diagnostic

For rows with nonnegative HiddenVol and positive TradeVolForHidden, Phase 200 calculated HiddenVol / TradeVolForHidden:

| Quarter | Valid ratios | Denominator zero | Ratios above 1 | Maximum |
|---|---:|---:|---:|---:|
| 2014 Q2 | 305,880 | 12,533 | 2 | 2.267144319344933 |
| 2016 Q1 | 304,324 | 18,800 | 0 | 1 |
| 2016 Q2 | 317,010 | 21,026 | 0 | 1 |
| 2016 Q3 | 316,812 | 21,134 | 0 | 1 |
| 2016 Q4 | 311,939 | 19,692 | 0 | 1 |
| 2019 Q4 | 348,121 | 21,303 | 0 | 1 |

Five quarters had no ratio above 1. 2014 Q2 had two, with a maximum of 2.2671. This is a further data-quality exception; no clipping or winsorization was applied. The Hidden / TradesForHidden rate is explicitly left for the next phase so the README and denominator semantics can be checked together.

## 4. Decision

- **Duplicate activity conflict gate:** PASS for these six quarters only. Rank columns remain excluded from any candidate feature until separately reconciled.
- **Negative numerator gate:** FAIL / unresolved. Negative Hidden and HiddenVol values with positive denominators cannot be treated as ordinary missing data.
- **Hidden-volume share bounds:** five quarters pass the observed bound; 2014 Q2 has two exceptions.
- **PIT:** NOT ADMITTED. The six archives' original first-publication times, complete 58-quarter release-vintage ledger and permanent historical security identity remain unresolved.
- **Alpha:** no return test, no feature tuning, no holdout use. MIDAS remains a conditional market-structure candidate, not direct institutional flow.

## 5. Next phase

Phase 201 will extract the README files embedded in all six ZIPs, compare documentation versions and compute both derived ratios (Hidden / TradesForHidden and HiddenVol / TradeVolForHidden) with denominator/missing/negative diagnostics. Only documented, reproducible semantics can move the raw fields toward a PIT feature specification.

No raw archive was committed. No data were purchased, no provider contacted, no production change, no holdout use; F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen.

## Official references

- SEC [Metrics by Individual Security](https://www.sec.gov/data-research/sec-markets-data/marketstructuredata-security).
- SEC [Market Activity Report Methodology](https://www.sec.gov/featured-topics/market-structure-analytics/market-activity-report-methodology).
- SEC [MIDAS Feedback / FAQ](https://www.sec.gov/securities-topics/market-structure-analytics/midas-feedback).
