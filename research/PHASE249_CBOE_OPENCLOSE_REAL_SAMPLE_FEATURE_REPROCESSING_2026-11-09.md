# Phase 249 — Cboe Open-Close EOD real-sample feature reprocessing

**Date:** 2026-11-09  
**Status:** HOSTED_REAL_SAMPLE_RUN_PENDING  
**Control:** `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen.  
**Scope:** apply the preregistered Phase 248 feature contract to the public Cboe C1 Open-Close EOD sample in memory. No historical returns, PIT reconstruction, holdout, vendor purchase or production change.

## Why this phase matters

Phase 248 validated the feature contract with synthetic rows only. Phase 249 closes that implementation gap by applying the exact same measurement helper to the actual public sample previously audited in Phase 114. It does not broaden the sample or infer predictive value.

## Preregistered sample and cohort handling

- Source: Cboe public Open-Close EOD sample ZIP, nested EOD CSV, C1 exchange.
- Expected sample date: 2025-03-28; expected sample designation: 20%.
- Use the exact 86-field EOD schema.
- Reconcile the sum of all participant buy/sell contract-volume buckets to `total_exchange_vol` on every row before feature construction.
- Exclude Index/Warrant security types from stock-selection features.
- Keep Equity and ETF underlyings in separate groups.
- Exclude FLEX series type F from the primary panel while retaining standard/nonstandard S/N rows for the same underlying. FLEX rows are counted as exclusions, not allowed to contaminate the primary group.
- Aggregate at underlying × security type × date after validating unique option-series keys.
- Build the fixed Phase 248 feature family: Customer and Pro-Customer opening flow overall and by size bucket; Customer and Pro-Customer closing controls; Firm and Broker-Dealer opening controls.
- Report only cross-sectional aggregate diagnostics; do not persist raw rows or underlying names.

## Required validation

The hosted workflow runs offline regression tests, downloads the public sample, independently applies the Phase 168 archive/schema gate, and computes Phase 248 features on the real C1 EOD rows. It uploads only a metadata/aggregate JSON artifact.

A successful result establishes that the preregistered feature implementation runs on this particular public sample and that participant-volume accounting reconciles. It does **not** establish daily archive continuity, inactive/delisted coverage, historical first-receipt times, preliminary/final vintage history, broad PIT security identity or return prediction.

## Economic and PIT boundary

This is a single-date 20% sample. Cross-sectional positive/negative feature distributions are descriptive only. They are not a prediction test and must not be interpreted as an alpha result. No forward returns, momentum controls, exposure matching, costs, bootstrap, LOO, chronological OOS or consumed holdout are used.

Strict PIT, return-test and alpha gates remain closed. The first future scheduled capture, if separately authorized and integrated, is a baseline state, not a new event. No trial, card, API subscription or vendor contact is authorized.

## Files

- `research/phase249_cboe_openclose_real_sample_reprocessing.py`
- `research/test_phase249_cboe_openclose_real_sample_reprocessing.py`
- `.github/workflows/phase249_cboe_openclose_real_sample_reprocessing.yml`

