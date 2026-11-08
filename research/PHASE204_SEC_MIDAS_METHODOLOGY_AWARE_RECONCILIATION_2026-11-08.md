# Phase 204 — SEC MIDAS methodology-aware aggregate/per-exchange reconciliation

**Date:** 8 November 2026  
**Status:** Completed; 7/7 offline tests passed; hosted reconciliation artifact generated.  
**Research role:** SEC on-exchange market-structure context only. This is not off-exchange flow, participant identity, or a directional Smart Money signal.

## Scope and result

The SEC publishes 58 quarterly archives for both “Metrics by Individual Security” and “Metrics by Individual Security and Exchange” (2012 Q1–2026 Q2). Phase 204 fully CRC-validated and parsed three paired quarters: 2016 Q2, 2017 Q2 and 2019 Q4.

| Quarter | Aggregate rows | Aggregate tickers | Per-exchange rows | Sample tickers | Security-day keys compared |
|---|---:|---:|---:|---:|---:|
| 2016 Q2 | 338,183 | 5,393 | 2,888,147 | 256 | 16,125 |
| 2017 Q2 | 330,536 | 5,353 | 2,797,885 | 256 | 15,752 |
| 2019 Q4 | 369,433 | 5,902 | 4,180,726 | 258 | 16,157 |

**All 12 shared activity fields reconcile exactly (zero mismatches) on every sampled security-day key when the embedded README's field-specific exchange rules are applied.** There were zero aggregate-key conflicts and zero per-exchange-key conflicts.

A simple sum across every exchange fails for six methodology-sensitive fields. The all-exchange mismatch counts were:

| Field | 2016 Q2 | 2017 Q2 | 2019 Q4 |
|---|---:|---:|---:|
| Cancels | 5,492 | 2,086 | 12,822 |
| LitTrades | 5,299 | 2,053 | 7,876 |
| OddLots | 5,031 | 1,963 | 10,281 |
| OddLotVol | 5,012 | 1,953 | 10,179 |
| TradesForOddLots | 5,321 | 2,058 | 11,762 |
| TradeVolForOddLots | 5,317 | 2,058 | 11,723 |

The README's exact metric-specific rules reconcile these fields; generic order-based or simplified venue-exclusion variants fail in later samples. The SEC methodology documents the NYSE Integrated Feed cutover on 1 May 2017 and the historical venue-coverage changes. This is why one static exchange list is unsafe.

## What this establishes — and what it does not

- It establishes a reproducible method to reconstruct the sampled aggregate fields from per-exchange components without deleting or imputing rows.
- It does **not** establish complete-universe reconciliation: the row-level comparison used a deterministic 250-ticker sample plus controls, not all securities in the archives.
- The three archive pairs carry HTTP Last-Modified dates of 19 December 2020. These are migration/re-hosting metadata, not verified first-publication dates for 2016, 2017 or 2019.
- MIDAS public metrics remain on-exchange aggregate microstructure. They do not identify beneficial owners, institutional participants, or off-exchange/dark-pool flow.
- Historical permanent security identity, broad PIT universe coverage and first-publication timestamps remain unresolved.

## Decision

**Keep MIDAS as a conditional market-microstructure context candidate; do not admit it to stock-selection or alpha testing.** The reconciliation issue is solved for the three sampled quarters, but the PIT, complete-universe and security-identity gates remain closed. No return test or holdout use was authorized.

## Reproducibility

- Auditor: [phase204_sec_midas_methodology_aware_reconciliation.py](https://github.com/jafelix81/NuevaEstrategia/blob/phase99-broad-pit-universe-charter/research/phase204_sec_midas_methodology_aware_reconciliation.py)
- Full hosted JSON artifact: [run 42438958146 / artifact 13601285381](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42438958146/artifacts/13601285381)
- Committed compact result: [phase204_sec_midas_methodology_aware_reconciliation_result.json](https://github.com/jafelix81/NuevaEstrategia/blob/phase99-broad-pit-universe-charter/research/phase204_sec_midas_methodology_aware_reconciliation_result.json)
- Official SEC methodology: https://www.sec.gov/featured-topics/market-structure-analytics/market-activity-report-methodology

**Controls:** `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen. No vendor purchase/contact, holdout use, production change or universe change.
