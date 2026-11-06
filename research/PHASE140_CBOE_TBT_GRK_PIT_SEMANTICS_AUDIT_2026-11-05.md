# Phase 140 — Cboe TBT/GRK semantics, missingness and PIT join audit

**Date:** 2026-11-05 (America/Hermosillo)  
**Status:** TBT remains a high-information but conditional C1 execution source; open/close feature gate FAIL pending explanation of non-random missingness. GRK forward-join implementation requires correction before use for event-time features. No alpha test, purchase, vendor contact, subscription or production change.

## 1. Repository preflight

- Repository: `jafelix81/NuevaEstrategia`.
- Branch: `phase99-broad-pit-universe-charter`, head `26ef1b8428cb1dc22b4e70248ad6171cc4ab394b`.
- PR #13 is open, unmerged, mergeable, targeting `main`.
- Latest 30 of 761 Actions runs inspected; zero queued/in-progress. Latest run is Phase 139 run [42140245367](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42140245367), job `127638473121`, success. Its steps were checkout, Python setup, compile, and 23/23 offline tests; it produced no artifact. Prior Phase 139 run [42140195923](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42140195923) also passed. No duplicate workflow started.
- Phase 129 remains cancelled/no final artifact; do not rerun unchanged.
- Downloaded and inspected existing Phase 113 artifact `13413280759` (not re-downloaded from Cboe). The raw sample SHA-256 remains `6c99e69e43d259e81bc31334574579cf9c623f5e77ff596cacf268712cd3262c`; nested CSV SHA-256 `24394a233dc20066b1fad675deb15cd99bf91e8620a69f6bf50f190dfda62ba0`.

## 2. Revalidated product scope and T+1 delivery

Cboe's current Enhanced US Options Trade-by-Trade (TBT) page describes execution-level records with timestamp, underlying/OSI, price/size, buy/sell, open/close, capacity, trade type, NBBO/local BBO and execution IDs. Current scope is **C1 only**; BZX/C2/EDGX are planned future releases. Advertised historical start is 2019-10-07. TBT is delivered T+1 after midnight ET, typically 00:30–01:30 ET.

Official sources:
- Product: https://datashop.cboe.com/enhanced-us-options-trade-by-trade-execution-detail
- TBT spec v1.1 (2026-10-05): https://datashop.cboe.com/documents/TBT_Spec_v1.1.pdf
- GRK product: https://datashop.cboe.com/us-options-trade-by-trade-greeks
- GRK spec v1.0 (2026-02-17): https://datashop.cboe.com/documents/GRK_Spec_v1.0.pdf
- General DataShop delivery FAQ: https://datashop.cboe.com/faqs

The sample remains a 2025-03-28 C1 3% sample containing an embedded v1.0 spec (2026-01-12), while the current TBT specification is v1.1 (2026-10-05). The current v1.1 field table still documents SIDE as B/S and OPEN_CLOSE as O/C; it does not explain the sample's T values or blank OPEN_CLOSE. The sample is not a current post-v1.1 file and cannot resolve the discrepancy.

T+1 is a delivery schedule, not a preserved historical first-receipt timestamp. The FAQ says daily files are typically uploaded in an overnight window but can be delayed until the next market session has opened. Therefore a backfilled TBT file cannot be assigned a strict historical knowledge timestamp from trade time or the nominal T+1 schedule alone. Require actual immutable first-receipt logs for strict PIT. Conservative lag sensitivities may be descriptive only.

## 3. New cross-tab: OPEN_CLOSE missingness is strongly non-random by capacity

Recomputed from the archived Phase 113 sample (113,018 rows; 1,250 underlyings; C1 only). Blank/whitespace is normalized as missing; no value is imputed.

| Capacity | Rows | Blank OPEN_CLOSE | Blank rate |
|---|---:|---:|---:|
| MarketMaker | 58,293 | 19,907 | **34.15%** |
| Customer | 49,989 | 197 | 0.39% |
| ProCustomer | 2,699 | 17 | 0.63% |
| Firm | 1,879 | 56 | 2.98% |
| BrokerDealer | 158 | 3 | 1.90% |
| **Total** | **113,018** | **20,180** | **17.86%** |

The MarketMaker missing rate is approximately 87 times the Customer missing rate. Of the 20,180 blank OPEN_CLOSE rows, 20,111 have SIDE B/S; only 69 are SIDE T. Thus excluding SIDE=T does not solve the open/close missingness problem.

MarketMaker blanks are concentrated in:
- Simple Add: 6,007
- Simple Remove: 5,419
- COA Responder: 3,325
- Complex Remove: 2,587
- AIM Responder - Complex: 806
- AIM Responder - Simple: 713
- Contra to Legged in Complex: 410
- SUM Response: 308

SIDE=T appears on 69 rows (37 MarketMaker, 17 Customer, 13 Firm, 2 ProCustomer); every one has blank OPEN_CLOSE. The v1.1 specification only documents B/S and O/C. Keep T and blanks unclassified; do not infer buyer/seller or open/close.

**Decision:** any Customer-vs-MarketMaker opening/closing comparison built from raw TBT rows is currently invalid if it silently drops blank OPEN_CLOSE rows. Missingness is highly capacity-dependent and would bias the comparison. Customer-only O/C fields are much more complete in this sample, but sample-level completeness does not establish historical population coverage. C1 Open-Close EOD remains preferable for daily classified O/C aggregates because its public sample passed exact bucket-to-total-volume accounting. TBT remains useful for trade-type/execution diagnostics, not as a clean standalone O/C feature source.

## 4. GRK join: temporal semantics and a reproducible Python-example defect

GRK provides per-trade delta, gamma, vega, theta, rho and theoretical price. Its v1.0 spec joins TBT to GRK by `formatted_symbol + trading_dt + price` and selects the closest GRK row within five seconds using a **forward ASOF** condition (`TBT.transact_time <= GRK.transact_time`).

That is a future Greek snapshot relative to the TBT transaction timestamp. It is not a pre-trade/event-time state. Treat it as post-trade attribution only. For event-time-causal features, use a backward ASOF join (GRK timestamp at or before TBT timestamp) and report the match rate separately. A forward join may be used for a next-day aggregate only if the entire TBT/GRK file is actually received before the strategy decision time; it must not be described as a Greek known at the trade timestamp.

The GRK PDF's Python sample sorts both frames by `[formatted_symbol, price, trading_dt, transact_time]` before `pandas.merge_asof`. Pandas requires the `on` key to be globally sorted; grouping-key-first sorting can leave `transact_time` non-monotonic and raises `ValueError: left keys must be sorted`. A synthetic two-symbol reproduction confirmed the failure. The new helper sorts globally by the as-of timestamp using stable mergesort, preserves the grouping keys, retains unmatched TBT rows, and labels forward joins `POST_TRADE_ATTRIBUTION_ONLY`.

The TBT sample's `transact_time` values are timezone-naive, and the published TBT/GRK field tables do not encode a timezone in the field type. Do not assume UTC or localize silently. Descriptive same-file joins can be run with the source's original clock, but strict intraday PIT/time-of-day analysis needs the timezone documented by Cboe.

## 5. Late trades, GTH and complex execution safeguards

- `TRANSACT_TIME` is when a trade was processed/booked; `FLOOR_ACTION_TS` is when it was agreed on the floor. Cboe defines a late floor trade as a difference of at least 90 seconds. Do not backdate the public knowledge time to FLOOR_ACTION_TS; preserve both and flag late records.
- `TRADING_DT` may differ from the calendar date around GTH midnight. Use `TRADING_DT` plus SESSION; the sample has 306 such mismatches, all GTH.
- The sample has `TRADING_SEGMENT=1` on every row, including RTH, despite the spec's illustrative mapping (prior-evening/overnight=1, daytime=2). Do not use this field for segmentation until Cboe explains it or a verified post-v1.1 file resolves it.
- Repeated `EXEC_ID`/`COMPLEX_EXEC_ID` groups are linkage structures, not duplicate rows. Exact duplicate rows were zero in the sample. Do not deduplicate by execution ID. Complex executions must be grouped/linked before aggregating legs or premium/delta.
- Do not sum all rows as total market volume without resolving whether a row is a participant-side record, a linked execution leg, or an execution event. Keep capacity/side aggregates separate and reconcile to C1 Open-Close on identical series/date/population.

## 6. Gate decision and next steps

| Gate | Decision |
|---|---|
| Schema parsing | PASS on archived 2025 sample |
| Side semantics | FAIL for SIDE=T |
| Open/close completeness | FAIL for cross-capacity comparison due non-random missingness |
| Segment semantics | UNRESOLVED |
| Timezone | UNRESOLVED for intraday PIT |
| GRK forward join | Post-trade only |
| Vendor Python join sample | FAIL; global sort defect |
| T+1 exact first receipt | UNVERIFIED |
| C1 historical completeness / inactive underlyings | UNVERIFIED |
| Whole-OPRA representativeness | UNVERIFIED |

Next:
1. Keep C1 Open-Close EOD as the preferred daily participant-capacity O/C candidate; do not promote TBT O/C rows until the capacity-specific missingness is explained.
2. Compare C1 TBT volume against OPRA-wide Option EOD Summary volume by underlying/series/date to estimate C1 share and its stability. Do not apply a single expansion weight.
3. Obtain a post-v1.1 sample after the documented spec/sample update and re-run side, O/C, segment, timezone and execution-link diagnostics.
4. Require immutable per-file first-receipt timestamps and hashes for a strict PIT backtest; use T+1 only as a documented availability floor/sensitivity until then.
5. If GRK is used, report backward and forward match rates separately. Forward-only Greeks are post-trade attribution; backward is the event-time-causal candidate.
6. No alpha test until historical coverage, inactive/delisted identity, C1/OPRA representativeness, file availability and licensing pass. No vendor contact, purchase, trial, terms acceptance or production change.

`F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen.
