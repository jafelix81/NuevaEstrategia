# Phase 647 — CFTC Russell fixed-reference feature construction validation

**Audit cutoff:** 2026-11-26 18:18 UTC  
**Main HEAD before this phase:** `2fb3874f1dc2ed59131e798489d617e9fa2dd10f`  
**Preregistration:** [Phase 646](PHASE646_CFTC_RUSSELL_FROZEN_ARCHIVE_REFERENCE_PREREGISTRATION_2026-11-26.md)  
**Disposition:** the frozen-reference feature calculation is reproducible and passes the 480-row data gate. Both current prospective Russell observations fall below the preregistered 80th-percentile high-crowding threshold. This is feature-construction validation only; no return/outcome data, alpha, OOS, bootstrap, LOO or portfolio test was performed.

## 1. Frozen inputs and temporal boundary

| Input | Blob SHA / timestamp |
|---|---|
| `historical_backfill.csv` | `4711abbaeeb6107d1cb8f50a7c2e3627373b6d29` |
| `baseline_manifest.json` | `9e58849093f2144ce8cfbf1d3e5efc626a1aa250` |
| Manifest snapshot creation | 2026-11-13 23:03:38Z |
| Conservative mainline persistence / knowledge bound | 2026-11-14 00:44:59Z, commit [e88e553](https://github.com/jafelix81/NuevaEstrategia/commit/e88e553afc235916e37e9236e1890b714163c229) |

The historical CSV contains 3,035 rows across four index-futures contracts. Russell code `239742` has 482 report-date rows. The fixed reference excludes exactly:
- 2018-09-25: archive page heading mismatch.
- 2019-12-24: archive page returned HTTP 404.

After these exclusions, the reference contains **480 unique, finite Russell observations**, from 2017-08-15 through 2026-11-03. No duplicate report dates, forward-fill or zero-fill were found. The historical rows remain `UNVERIFIED_ARCHIVE_PROXY` and are not historical signals or return observations.

Both prospective events were first received after the conservative 2026-11-14 00:44:59Z knowledge bound. This validates the narrow Phase 646 use of the frozen snapshot as a reference distribution for subsequent prospective events; it does not certify the historical reports' original public-release timestamps.

## 2. Recomputed reference distribution

Feature: `LM_NET_OI = (Leveraged Money long - Leveraged Money short) / open_interest_all`. Spreading positions are excluded.

| Statistic | 480-row reference |
|---|---:|
| Minimum | -27.4092% |
| Mean | -8.0568% |
| Median | -8.4509% |
| 80th percentile | -1.9809% |
| 90th percentile | +2.6658% |
| Maximum | +14.9358% |
| Population standard deviation | 7.9206% |

The fixed threshold remains the empirical mid-rank percentile **P >= 0.80**. No threshold was tuned after observing the prospective values.

## 3. Prospective feature values

The empirical mid-rank is `(count(reference < current) + 0.5 * count(reference == current)) / 480`.

| Report date | First receipt UTC | First eligible XNYS session | LM net/OI | Reference percentile | High crowding |
|---|---|---|---:|---:|---|
| 2026-11-10 | 2026-11-18 03:44:57Z | 2026-11-18 | -10.0843% | 40.6250% | No |
| 2026-11-17 | 2026-11-21 03:17:36Z | 2026-11-23 | -9.2126% | 45.4167% | No |

Exact reference ranks:
- 2026-11-10: 195 reference values below the observation, zero ties.
- 2026-11-17: 218 reference values below the observation, zero ties.

Both current observations are below the fixed 80th-percentile state. This is not evidence of a bearish signal, a low-crowding premium, or a predictive relationship. No alternative low-percentile state was preregistered and none is tested here.

## 4. Interpretation and limitations

1. The fixed archive reference distribution is now usable for prospective Russell feature construction because the entire snapshot was persisted before both first-receipt events.
2. The two current values are feature observations only. Two report-date clusters cannot estimate persistence, conditional drawdown risk, effect size, uncertainty or predictive accuracy.
3. The primary outcome source remains unfrozen. No IWM/Russell adjusted OHLC, VIX, future price path or return label was accessed.
4. The Phase 646 training gate (52 matured prospective observations, including at least 20 high and 40 non-high) and evaluation gate (150 observations, at least 30 high and 100 non-high) remain unmet.
5. Phase 387 ES/NQ is unchanged. Its prospective-only percentile reference and all other preregistered rules remain intact.
6. No Russell feature was added to F80 or any production path.

## 5. Next gates

1. Implement the Phase 646 calculation as a separate Russell-only reproducible script/test, preserving the fixed CSV and event-file hashes.
2. Freeze a permitted, reproducible Russell-proxy adjusted-OHLC and VIX source before inspecting any forward outcome. If that source cannot be established without an unapproved purchase, leave the outcome study blocked.
3. Continue actual first-receipt capture. The official CFTC release calendar currently lists the next report for 2026-11-30 at 3:30 p.m. ET; use the actual collector receipt and do not assume the announced semiweekly transition has reached TFF.
4. Keep the two historical archive exceptions excluded and do not change the Phase 646 threshold or outcome definition.

## Frozen controls

- Signals admitted: **0**.
- Incremental alpha vs LTM/F80: **none demonstrated**.
- New OOS / bootstrap / LOO: **0**.
- Price outcomes inspected: **no**.
- Holdout remains sealed.
- `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen.
- No universe, parameter, capital, exposure, cost, holding-period or production changes.
- Options-data budget remains **USD 0**.
