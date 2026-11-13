# Phase 355 — Cboe Open-Close EOD participant-volume accounting reconciliation

**Date:** 2026-11-13 UTC  
**Branch:** `phase355-cboe-eod-participant-accounting-audit`  
**Status:** `PASS_ACCOUNTING_DIAGNOSTIC_ONE_C1_20PCT_SAMPLE_ONLY`  
**Run:** https://github.com/jafelix81/NuevaEstrategia/actions/runs/43385780546  
**Artifact:** https://github.com/jafelix81/NuevaEstrategia/actions/runs/43385780546/artifacts/14019160327  
**Draft PR:** https://github.com/jafelix81/NuevaEstrategia/pull/42

## Objective

Validate the internal arithmetic of Cboe Open-Close EOD participant-capacity fields before any feature construction:

1. Do the 34 participant-side volume fields reconcile to `total_exchange_vol`?
2. Do Customer and Professional Customer size-bucket quantity/volume aggregates respect their documented per-trade size bands?
3. Can exchange volume be compared correctly with OCC-sourced industry contract volume without mixing units?

This is a one-day public-sample diagnostic, not a market-behavior or return test.

## Source semantics and unit correction

The official Cboe v1.3 specification says `total_exchange_vol` counts **both sides of a trade** (field 14). The final file's `total_industry_vol` is sourced from OCC (field 15). OCC reports its volume as contracts. A direct comparison of the raw two-sided exchange total with the one-sided contract count therefore mixes units.

- Cboe EOD specification: https://datashop.cboe.com/documents/Open_Close_EOD_Spec_v1.3.pdf
- OCC volume reporting example: https://www.theocc.com/newsroom/views/2025/01-03-occ-annual-2024-and-december-2024-volume

The diagnostic consequently compares `total_exchange_vol / 2` with OCC industry contract volume. It preserves the raw comparison only as a diagnostic and does not treat raw `exchange > industry` as a data error.

The participant-side sum is compared with the full two-sided `total_exchange_vol`, because the participant fields are separately classified by buy/sell side.

## Public sample

- Source: Cboe Open-Close public sample bundle 218, C1 EOD, 20% sample, quote date **2025-03-28**.
- Archive: 3,961,119 bytes; SHA-256 `445cd9d658dc06028c286e09d4ac4818bd5884d7da8addd7509f3a0fa4840552`.
- EOD member: 23,179 rows; 1,553 underlyings; 86 columns.
- Unique option-series keys: 23,179; duplicates: 0.
- Series types: S 23,080; N 11; F 88.
- Calls: 12,380; puts: 10,799.
- All 34 participant-volume fields and their 34 trade-quantity fields were present. No missing or invalid numeric cells; no row-width errors.

## Results

| Check | Result |
|---|---:|
| Participant-volume sum equals `total_exchange_vol` | **23,179 / 23,179 (100%)** |
| Total participant-side volume | 4,506,840 |
| Total exchange volume (both sides) | 4,506,840 |
| Exchange contract-equivalent after /2 | 2,253,420 |
| OCC industry contract volume across sampled rows | 12,228,281 |
| Customer/Pro-Customer size-bucket pairs checked | 556,296 |
| Size-bucket arithmetic violations | **0** |
| Rows where exchange contract-equivalent exceeded industry volume | **0 / 23,179** |
| Odd-valued two-sided exchange-volume rows | 0 |
| Duplicate option-series keys | 0 |

All 24 Customer/Professional-Customer quantity/volume field pairs per row were checked across the three documented size buckets. The aggregate constraints were satisfied in all 556,296 comparisons.

### Important false alarm avoided

A raw, unadjusted comparison would label **7,576 rows (32.68%)** as having exchange volume greater than industry volume. That is not a source defect: the Cboe exchange field counts both sides, whereas the OCC comparison is in contracts. After matching units, there were **zero** violations. The normalized per-series ratio (`total_exchange_vol / 2 / total_industry_vol`) had p50 0.25, p90 1.00, p95 1.00 and maximum 1.00 in this selected sample. These are sample diagnostics, not a representative Cboe market-share estimate.

The participant sum also reconciled exactly on every row, with no residual difference. This confirms internal arithmetic for this C1 sample; it does not identify beneficial owners or prove that any participant category is informed.

## Hosted validation

- Run **43385780546** completed successfully.
- **9/9** offline regression tests passed.
- Hosted sample download, parser, accounting checks and diagnostic-only gates passed.
- Metadata-only artifact **14019160327**; artifact ZIP SHA-256 `7b78e2756ab1cd11bb6876e4e3c337b395d0a7725d8a178e48360759cadebdde`.
- Raw sample rows were not uploaded to the artifact.

## Decision

**Pass the Cboe EOD participant-volume accounting gate for this one C1 public sample.** This removes one schema/arithmetic uncertainty and makes participant-flow feature construction technically more credible, but it does not admit the source for research returns.

Still unresolved:

1. Broad historical coverage across C1/BZX/C2/EDGX, all eligible underlyings, inactive/delisted names and historical option-root changes.
2. C1 RTH/GTH versus RTH-only Option EOD context alignment.
3. Preliminary/final file lineage, exact first-receipt UTC and immutable correction vintages.
4. S/N/F and deliverable crosswalk to OPRA Option EOD Summary.
5. Licensing and total acquisition cost.

No vendor contact, trial, subscription, purchase or license acceptance occurred. No forward returns, feature tuning, alpha, OOS, bootstrap, LOO or holdout test was performed. No signal was admitted. `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen.
