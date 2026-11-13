# Phase 354 — Cboe Open-Close EOD OSI normalization and OCC OI endpoint feasibility

**Date:** 2026-11-13 UTC  
**Branch:** `phase354-occ-cboe-eod-oi-crosscheck`  
**Status:** `COMPLETED_OCC_PUBLIC_DAILY_OI_ENDPOINT_KILLED_FOR_CONTRACT_LEVEL_VALIDATION`

## Objective

Determine whether OCC's public Daily Open Interest batch endpoint can independently validate the per-option-series `open_interest` and `previous_open_interest` fields in the Cboe Open-Close EOD sample.

## Source semantics corrected before the final diagnostic

The official Cboe Open-Close EOD v1.3 specification defines field 4, `option_symbol`, as the **option root**, not a complete OSI option symbol. It separately supplies expiration date, strike, call/put and series type. The final subscription file sources `total_industry_vol` and `open_interest` from OCC; the preliminary file obtains them from OPRA and may differ.

- [Cboe Open-Close EOD v1.3 specification](https://datashop.cboe.com/documents/Open_Close_EOD_Spec_v1.3.pdf)
- [OCC Daily Open Interest batch page](https://www.theocc.com/market-data/market-data-reports/other-market-data-info/batch-processing/daily-open-interest)

The initial Phase 354 attempt incorrectly treated Cboe's `option_symbol` root as a full OSI symbol and did not validate the OCC response schema. Its zero matches are superseded and are **not** interpreted as a data mismatch. The corrected parser reconstructs the normalized OSI key from root, expiration, strike and call/put; duplicate reconstructed keys are quarantined.

## Cboe public sample result

Cboe sample 218, C1 Open-Close EOD, quote date 2025-03-28:

| Measure | Result |
|---|---:|
| Sample ZIP bytes | 3,961,119 |
| SHA-256 | `445cd9d658dc06028c286e09d4ac4818bd5884d7da8addd7509f3a0fa4840552` |
| EOD rows | 23,179 |
| Underlyings | 1,553 |
| Series type S | 23,080 |
| Series type N | 11 |
| Series type F | 88 |
| Invalid reconstructed OSI keys | 0 |
| Duplicate reconstructed OSI rows | 0 |

This confirms that the C1 20% public sample can be normalized into unique OSI keys for this one date. It does **not** establish representative full-market coverage, historical inactive-symbol coverage, first-receipt PIT or a tradable signal.

## OCC endpoint result

Four request variants were tested for March 2025: `reportDate` and `dailyDate`, with encoded and unencoded slashes.

- Both `reportDate` variants returned HTTP 200 and the same 2,878-byte payload/hash.
- The payload is titled **Daily Open Interest — March 2025** and contains 23 daily rows with aggregate columns for Equity, Index/Other, Debt, Futures and OCC Total.
- It has no option-symbol or per-series open-interest field.
- Both `dailyDate` variants returned HTTP 500.

The endpoint is a market-wide aggregate report, not a contract-level OI file. It therefore cannot be joined to Cboe's 23,179 option-series rows. This is a **source-granularity incompatibility**, not evidence that Cboe's OI values are wrong.

Corrected diagnostic run: [43383418385](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43383418385). The run passed all 18 offline tests and uploaded metadata-only artifact [14017970948](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43383418385/artifacts/14017970948). Its initial hosted gate correctly rejected the aggregate-only OCC schema; the workflow gate was then updated to record this as an expected source kill rather than a code failure.

## Decision

1. **Kill OCC's public Daily Open Interest endpoint as an independent per-series OI validator.** Do not retry this same endpoint or treat its aggregate rows as zero/missing contract OI.
2. Retain Cboe Open-Close EOD as a **conditional data candidate**, not an admitted source. Its final OI is documented as OCC-sourced, but this audit could not independently reconcile the series-level values.
3. Keep first-receipt PIT, correction-vintage retention, broad historical/inactive-symbol coverage, four-venue session alignment and licensing unresolved.
4. Do not buy data, contact the vendor, run forward returns/alpha/OOS/bootstrap/LOO, use the holdout, or change production.

## Research controls

`F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen. No signal has been admitted. No parameter, universe, capital or production changes were made. The public 20% sample is a schema/identity diagnostic only.
