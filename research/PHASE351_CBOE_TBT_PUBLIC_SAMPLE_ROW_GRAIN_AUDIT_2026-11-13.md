# Phase 351 — Cboe TBT public sample row-grain and execution-linkage audit

**Date:** 2026-11-13 UTC  
**Status:** `PASS_SAMPLE_SCHEMA_AND_LINKAGE_DIAGNOSTICS_NO_PIT_NO_ALPHA`  
**Run:** https://github.com/jafelix81/NuevaEstrategia/actions/runs/43357228206  
**Artifact:** https://github.com/jafelix81/NuevaEstrategia/actions/runs/43357228206/artifacts/14006049274  
**Branch:** `phase351-cboe-tbt-public-sample-row-grain-audit`

## Executive result

The public Cboe sample downloaded successfully (HTTP 200) and parsed against the 22-field v1.1 schema. It is a **3% sample for one trade date, 2025-03-28**, not a representative multi-day history or a PIT receipt ledger.

- 113,018 rows; 1,250 distinct underlying symbols; 25,015 fully identified option series.
- 0 exact duplicate rows.
- 111,333 nonblank `EXEC_ID` groups; 109,648 singleton groups and 1,685 two-row groups containing both Buy and Sell sides.
- 46,350 nonblank `COMPLEX_EXEC_ID` groups; 2,111 groups span multiple fully identified option series.
- 20,180 rows (17.86%) have blank `OPEN_CLOSE`; 507 rows (0.45%) lack both `OSI_ROOT` and `CALL_PUT_FLAG`; 69 rows (0.061%) have an unrecognized `SIDE` code.
- All 113,018 timestamps are timezone-naive in the sample. 306 rows have a calendar date in `TRANSACT_TIME` different from `TRADING_DT`; the assigned `TRADING_DT` is retained as the trade date.
- Every row has `TRADING_SEGMENT=1), including RTH rows. This conflicts with the v1.1 specification's example that describes segment 1 as prior-evening/overnight and segment 2 as daytime. The session/segment convention is therefore **not admitted** pending clarification.

This is a meaningful measurement result, not an economic result. The sample confirms that TBT contains the dimensions needed for a careful C1 flow study, but also shows material unknown open/close and contract-identity coverage. The parser deliberately preserves these unknowns rather than filling them.

## 1. Source and reproducibility

- Product: https://datashop.cboe.com/enhanced-us-options-trade-by-trade-execution-detail
- v1.1 specification dated 2026-10-05: https://datashop.cboe.com/documents/TBT_Spec_v1.1.pdf
- Public sample endpoint: https://datashop.cboe.com/download/sample/289
- Downloaded outer archive: 3,807,739 bytes; SHA-256 `6c99e69e43d259e81bc31334574579cf9c623f5e77ff596cacf268712cd3262c`.
- Inner CSV: 16,486,601 bytes; SHA-256 `24394a233dc20066f1bad675deb15cd99bf91e8620a69f6bf50f190dfda62ba0`.
- Inner member: `C1_TBT_2025-03-28_sample_3pct.csv`.

The workflow uploaded only aggregate metadata, counts and hashes. No raw rows, underlying names, execution IDs or contract keys were persisted in the artifact.

## 2. Row grain and linkage

### Simple execution IDs

| Measure | Result |
|---|---:|
| Nonblank rows with EXEC_ID | 113,018 |
| Unique EXEC_ID groups | 111,333 |
| Groups with one row | 109,648 |
| Groups with two rows | 1,685 |
| Two-row groups containing both B and S | 1,685 |
| Groups spanning multiple capacities | 1,506 |
| Groups spanning multiple complete option series | 0 |

The sample does not support the assumption that every `EXEC_ID` appears as a complete two-sided pair in the sampled file: 98.49% of IDs appear once. This may reflect the sample's 3% selection, source row grain, or both. The IDs must be retained as linkage keys; raw rows must not be counted as independent executions until the vendor's sampling and row-grain rules are confirmed.

### Complex execution IDs

| Measure | Result |
|---|---:|
| Nonblank rows with COMPLEX_EXEC_ID | 49,332 |
| Unique COMPLEX_EXEC_ID groups | 46,350 |
| Groups spanning multiple complete option series | 2,111 |
| Groups with 1 / 2 / 3 / 4 rows | 43,475 / 2,770 / 103 / 2 |

Complex IDs demonstrably span multiple option series in the sample. A feature pipeline must link and classify complex legs before aggregating volume or exposure; otherwise it risks double-counting multi-leg strategies.

## 3. Missingness and category coverage

| Field / diagnostic | Count | Share of rows |
|---|---:|---:|
| OPEN_CLOSE blank | 20,180 | 17.86% |
| OSI_ROOT blank | 507 | 0.45% |
| CALL_PUT_FLAG blank | 507 | 0.45% |
| SIDE not mapped to B/S | 69 | 0.06% |
| FLOOR_ACTION_TS blank | 112,400 | 99.45% |
| COMPLEX_EXEC_ID blank | 63,686 | 56.35% |

Capacity categories in the sample:

| Capacity | Rows |
|---|---:|
| MarketMaker | 58,293 |
| Customer | 49,989 |
| ProCustomer | 2,699 |
| Firm | 1,879 |
| BrokerDealer | 158 |

These are exchange capacity classifications, not account identities, beneficial owners, or evidence that a participant is informed. Blank/unknown side, open-close, call-put, capacity and session values remain outside any corresponding directional feature.

The 507 rows with missing OSI root and call/put flag are excluded from complete option-series identity counts; no contract attributes are inferred.

## 4. Market context and timestamp diagnostics

- NBBO and local BBO are present on all rows.
- Crossed NBBO: 12 rows; crossed local BBO: 2 rows.
- Trade price outside NBBO: 1,646 rows (1.46%). These remain diagnostics; no aggressor direction is inferred.
- `FLOOR_ACTION_TS` is present on only 618 rows; 61 of those have a `TRANSACT_TIME - FLOOR_ACTION_TS` lag of at least 90 seconds; no negative lag was found.
- 306 rows have different calendar dates in `TRANSACT_TIME` and `TRADING_DT`. Use `TRADING_DT` for assigned market date, not the timestamp's calendar date.
- The sample timestamps contain no timezone offset. Do not silently assign ET or UTC.

### Unresolved session/segment discrepancy

The sample has 111,240 RTH rows, 1,671 GTH rows and 107 Curb rows, but all 113,018 rows have `TRADING_SEGMENT=1). The v1.1 specification gives 1 as prior-evening/overnight and 2 as daytime, with examples such as RTH2. The observed RTH/segment-1 combination is inconsistent with that example. Preserve the raw segment value and do not use it to segment intraday activity until its semantics are clarified.

## 5. Historical availability and PIT ruling

The current Cboe page advertises a historical archive start of 2019-10-07 and T+1 delivery, with C1 as the only currently documented venue. Phase 236 located the first public launch documentation on 2026-02-20; the 2019–pre-launch archive is retrospective backfill, not evidence of live contemporaneous delivery. The 2025-03-28 sample is therefore not strict PIT.

Post-launch files still require actual per-file first-receipt timestamps, immutable correction/revision lineage, schema versions, effective-dated underlying identity and confirmed licensing. A public sample retrieval today cannot substitute for any of these.

C1-only TBT is not all-OPRA. The sample's 1,250 underlyings do not establish coverage of the historical 335-symbol universe or inactive/delisted names. The 3% sample is not assumed to be random or representative.

## 6. Research decision

**Retain TBT as a high-priority conditional C1 measurement candidate, not an admitted signal.** The public sample validates the 22-field parser and demonstrates that execution/complex linkage is essential. It also reveals an 17.86% open-close missing rate, a 0.45% incomplete contract-identity rate, 69 unmapped side rows, and an unresolved session/segment discrepancy.

Before any feature engineering or alpha test:
1. Obtain written clarification of `TRADING_SEGMENT` and the 69 non-B/S side values.
2. Confirm why `OPEN_CLOSE` is blank on 20,180 sample rows and whether missingness varies by trade type/capacity/session.
3. Confirm the 3% sample selection rule and the row-grain/paired-side meaning of `EXEC_ID`.
4. Reconcile complex legs by `COMPLEX_EXEC_ID` and preserve trade-type exclusions.
5. Confirm internal-use/derived-feature licensing and the actual first-receipt/correction protocol.
6. Establish effective-dated underlying identity, including inactive/delisted symbols, and quantify C1 share of OPRA.

No vendor contact, trial request, purchase, return test, alpha test, OOS, bootstrap, LOO or holdout test was made in this phase.

## 7. Controls

`F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen. No production, universe, capital or parameter changes. The legacy holdout remains untouched. The sample's historical date is not treated as an available-at-the-time TBT signal.
