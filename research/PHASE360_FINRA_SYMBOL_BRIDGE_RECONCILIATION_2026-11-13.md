# Phase 360 — FINRA symbol-only bridge and firm-total reconciliation

**Date:** 2026-11-13 UTC  
**Branch:** `phase360-finra-symbol-bridge-reconciliation`  
**Corrected run:** https://github.com/jafelix81/NuevaEstrategia/actions/runs/43426428636  
**Metadata artifact:** https://github.com/jafelix81/NuevaEstrategia/actions/runs/43426428636/artifacts/14037407295

## Objective

Validate whether FINRA's `weeklySummaryHistoric` symbol aggregate rows can provide a safe product-type crosswalk for symbol-firm rows, and whether firm-grain share quantity and trade count reconcile exactly to the symbol aggregate. This is a data-grain and accounting audit only.

## Retrieval and controls

- Four partitions: 2022-01-03/T1, 2022-01-03/T2, 2025-10-20/T1 and 2025-10-20/T2.
- 409,225 rows across 84 pages.
- All four API Record-Total counts matched the retrieved rows.
- No request or pagination errors.
- **12/12 offline regression tests passed** on the corrected run.
- First run 43426326025 failed two offline assertions caused by diagnostic gate-classification defects. The duplicate-key count was corrected to distinguish repeated `(symbol, productTypeCode)` keys from legitimate multi-product symbols, and the PASS/PASS_WITH_EXCLUSIONS classification was corrected. The corrected run 43426428636 completed successfully.
- Artifact contains only summary metadata and page hashes; no raw firm-level data is committed.
- No forward returns, alpha test, holdout, or F80 changes.

**Retrieval gate:** PASS.  
**Research data gate:** PASS_WITH_EXCLUSIONS.

## Phase 359 result explained

Phase 359 found zero exact `(symbol, productTypeCode)` overlaps because `productTypeCode` is systematically absent on the firm-grain symbol rows:

- **363,241/363,241** symbol-firm rows had blank `productTypeCode`.
- Symbol aggregate rows carried `CTS` or `UTP`.
- Ignoring product type, aggregate and firm symbol sets aligned in every partition; there were no aggregate-only or firm-only symbols among rows with nonblank symbols.

FINRA's official guide describes the Product field as the SIP trade feed classification for a symbol, which supports treating it as symbol-level metadata rather than a participant key. The guide also describes separate firm-level detail for ATSs and non-ATS firms. See the [FINRA OTC Transparency User Guide, pp. 10–11](https://www.finra.org/sites/default/files/OTC-transparency-website-user-guide-v5.pdf).

## Safe symbol-only bridge

Within each exact week, tier and ATS/OTC summary family, inherit the product type from the symbol aggregate only when exactly one aggregate row and exactly one nonblank product type exist for that symbol. Do not join across weeks, tiers, ATS/OTC families or multiple product types.

| Week | Tier | Family | Unambiguous bridge | Ambiguous symbols excluded | Exact share + trade reconciliation | Non-ATS de-minimis share of volume |
|---|---|---|---:|---:|---:|---:|
| 2022-01-03 | T1 | ATS | 1,941 / 1,941 | 0 | 1,941 / 1,941 | — |
| 2022-01-03 | T1 | OTC non-ATS | 1,946 / 1,946 | 0 | 1,946 / 1,946 | 33.13% |
| 2022-01-03 | T2 | ATS | 8,871 / 8,874 | 3 | 8,871 / 8,871 | — |
| 2022-01-03 | T2 | OTC non-ATS | 9,645 / 9,650 | 5 | 9,645 / 9,645 | 31.06% |
| 2025-10-20 | T1 | ATS | 2,414 / 2,414 | 0 | 2,414 / 2,414 | — |
| 2025-10-20 | T1 | OTC non-ATS | 2,420 / 2,420 | 0 | 2,420 / 2,420 | 22.95% |
| 2025-10-20 | T2 | ATS | 8,621 / 8,622 | 1 | 8,621 / 8,621 | — |
| 2025-10-20 | T2 | OTC non-ATS | 9,354 / 9,355 | 1 | 9,354 / 9,354 | 12.11% |
| **Total** | | | **45,212 / 45,222** | **10** | **45,212 / 45,212** | **19.71% weighted across these four sampled partitions** |

The unambiguous bridge covers **99.9779%** of the 45,222 shared symbols. On every mapped symbol, both firm-level weekly share quantities and trade counts sum exactly to the symbol aggregate. There were no invalid numeric symbols, duplicate aggregate symbol/product keys, duplicate participant-symbol keys, or missing MPID/CRD identities among non-de-minimis participant rows.

The 10 ambiguous symbol-family-period cases are:
- 2022-01-03/T2 ATS: `VPCC`, `VPCC.W`, `YSACW`.
- 2022-01-03/T2 OTC non-ATS: `VPCC`, `VPCC.W`, `YSAC`, `YSACU`, `YSACW`.
- 2025-10-20/T2 ATS and OTC non-ATS: `VNCE`.

One 2022-01-03/T2 OTC symbol aggregate row and one OTC firm row also lacked a symbol; both remain explicit exclusions. No imputation or multiplication was used.

## What the reconciliation does — and does not — establish

**ATS:** The symbol-to-ATS bridge is arithmetically reconciled for all mapped symbols. In the two T1 samples there were no ambiguous symbols, missing participant identifiers or duplicate participant-symbol keys, so ATS-level intermediary concentration is technically measurable on those samples. No HHI or concentration metric was calculated in this phase. This would describe ATS/venue routing concentration, not institutional beneficial-owner concentration or informed direction.

**OTC non-ATS:** The symbol totals also reconcile exactly, but every mapped symbol has a De Minimis Firms row. Its volume is aggregated and non-attributed. Across the four samples, the de-minimis bucket represents 12.11%–33.13% of shares by partition; the weighted share across these four sampled partitions is 19.71% (17.19% of trades). Therefore complete firm-level concentration is censored and must not be reported as if all firms were identified.

FINRA's guide states that non-ATS firms below reporting thresholds are aggregated as De Minimis Firms and further aggregation can occur below a per-security threshold. It also documents approximately two-week publication delay for Tier 1 and four-week delay for Tier 2/OTC. See the [official guide, pp. 1 and 11](https://www.finra.org/sites/default/files/OTC-transparency-website-user-guide-v5.pdf).

## PIT and economic disposition

This result repairs the **data-grain join and arithmetic reconciliation**, not the point-in-time history. The historic endpoint supplies final snapshots; it does not provide the full sequence of interim vintages. Publication delay and later `lastUpdateDate` values mean final rows cannot be backdated to the initial publication date. A strict PIT/OOS test remains closed until first-receipt and correction vintages are archived prospectively or independently established.

- ATS weekly participant data remains a **conditional venue-level market-structure candidate**, not a Smart Money identity signal.
- OTC non-ATS participant concentration is **censored by de-minimis aggregation**.
- No trade direction is provided by these fields.
- No return prediction, incremental information, cost-adjusted edge, OOS, bootstrap or LOO test was run.
- No source is promoted to alpha; no signal or production change is authorized.

## Next gate

1. Audit broader weekly coverage over the available historic window, including inactive/delisted symbols and the frozen 335-symbol panel as a comparison denominator only.
2. Determine whether prospective capture of first-published and revised weekly snapshots is feasible without excessive retrieval/storage burden.
3. Keep ATS venue concentration separate from OTC non-ATS firm activity and do not call either “smart money” without independent evidence.
4. Only after coverage and PIT pass, consider descriptive ATS concentration features and then a strictly chronological incremental test versus frozen LTM/F80, with identical exposure/costs and a new untouched holdout.

**Decision:** Phase 360 passes the symbol-only bridge and arithmetic reconciliation gate with explicit exclusions. FINRA ATS data remains conditional for market-structure research; non-ATS concentration is censored. F80 remains frozen.
