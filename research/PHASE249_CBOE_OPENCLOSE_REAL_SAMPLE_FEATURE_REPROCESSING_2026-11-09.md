# Phase 249 — Cboe Open-Close EOD real-sample feature reprocessing

**Date:** 2026-11-09  
**Status:** REAL_SAMPLE_FEATURE_REPROCESS_PASS_NO_PIT_NO_ALPHA  
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

The hosted workflow ran 11 offline regression tests, downloaded the public sample, independently applied the Phase 168 archive/schema gate, and computed Phase 248 features on the real C1 EOD rows. It uploaded only a metadata/aggregate JSON artifact.

A successful result establishes that the preregistered feature implementation runs on this particular public sample and that participant-volume accounting reconciles. It does **not** establish daily archive continuity, inactive/delisted coverage, historical first-receipt times, preliminary/final vintage history, broad PIT security identity or return prediction.

## Economic and PIT boundary

This is a single-date 20% sample. Cross-sectional positive/negative feature distributions are descriptive only. They are not a prediction test and must not be interpreted as an alpha result. No forward returns, momentum controls, exposure matching, costs, bootstrap, LOO, chronological OOS or consumed holdout are used.

Strict PIT, return-test and alpha gates remain closed. The first future scheduled capture, if separately authorized and integrated, is a baseline state, not a new event. No trial, card, API subscription or vendor contact is authorized.

## Files

- `research/phase249_cboe_openclose_real_sample_reprocessing.py`
- `research/test_phase249_cboe_openclose_real_sample_reprocessing.py`
- `.github/workflows/phase249_cboe_openclose_real_sample_reprocessing.yml`



## Hosted result — 2026-11-10 UTC

<badge>PASS — real sample reprocessed</badge>

- GitHub Actions run [42726166910](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42726166910) completed successfully; job 129532318774.
- **11/11 offline regression tests passed.**
- Metadata-only artifact [13722241996](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42726166910/artifacts/13722241996), 1,918 bytes; uploaded ZIP SHA-256: `938895ff32cf17a1e25d55799f2e389d76149f2521c11743598bcfc813f3533f`.
- Retrieval timestamp recorded by the workflow: `2026-11-10T00:10:12.869575+00:00`. HTTP ETag and Last-Modified headers were absent; this is a current retrieval observation, not a historical first-receipt record.
- Sample archive: 3,961,119 bytes, SHA-256 `445cd9d658dc06028c286e09d4ac4818bd5884d7da8addd7509f3a0fa4840552`. C1 EOD member SHA-256 `1c960e9a7b8b25311d2c8f012c36ea2c43087fe756335e57ffc952699a393ff6`; both hashes match the Phase 114 sample audit.

### Reprocessed cross-section

| Diagnostic | Result |
|---|---:|
| EOD option-series rows | 23,179 |
| Equity rows / underlyings | 15,189 / 1,255 |
| ETF rows / underlyings | 4,897 / 289 |
| Index rows / underlyings | 3,093 / 9 |
| Series S / N / F | 23,080 / 11 / 88 |
| FLEX rows excluded from Equity/ETF | 69 |
| Primary Equity/ETF rows after FLEX exclusion | 20,017 |
| Primary underlying groups | 1,543 (1,255 Equity; 288 ETF) |
| Participant-volume reconciliation | 23,179/23,179 exact; 0 mismatches |
| Feature groups built | 18,516/18,516; 12 specifications × 1,543 groups |
| Aggregation errors | 0 |

The one ETF underlying with only FLEX rows does not enter the primary cohort. Index/Warrant rows are excluded. The 69 FLEX exclusions apply only to the Equity/ETF cohort; 88 FLEX rows exist across the full sample.

### Descriptive feature sparsity — not predictive results

- Customer opening, all sizes: active in 1,257/1,543 groups; 639 positive, 576 negative, 328 zero; median directional imbalance among active groups = **+0.0400**.
- Customer opening under 100 contracts: active in 1,254 groups; 637 positive, 572 negative, 334 zero; median = **+0.043216**.
- Pro-Customer opening, all sizes: active in 344 groups; 170 positive, 172 negative, 1,201 zero; median = **−0.007246**.
- Pro-Customer 100–199 bucket: active in 6 groups; Pro-Customer greater-than-199 bucket: active in only 4 groups.
- Customer 100–199 and greater-than-199 buckets are active in 99 and 59 groups, respectively.

This shows that the broad Customer opening proxy is measurable on the sample, while Pro-Customer size buckets are very sparse in this 20% extract. It does **not** imply predictive direction: positive/negative counts are signs of the constructed flow proxy, not stock returns. The sample is one date and 20% of the exchange data; no extrapolation to the full market or full universe is valid.

### Final disposition

- Phase 249 feature construction: **PASS on the actual public sample**.
- Historical archive continuity, inactive/delisted coverage, first-receipt vintages and strict PIT: **NOT PROVEN**.
- Forward returns, momentum/volatility/liquidity controls, costs, bootstrap/LOO, chronological OOS and alpha: **NOT RUN**.
- Do not kill or promote the signal from this one-day cross-section. The next gate is multi-date archive availability, PIT receipt/vintage proof and effective-dated underlying identity.
- `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen; holdout unused; production/universe/capital unchanged.
