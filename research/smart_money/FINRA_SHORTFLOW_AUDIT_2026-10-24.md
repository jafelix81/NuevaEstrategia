# Smart Money Research — FINRA Short Flow Audit

Date: 2026-10-24
Branch base: `phase20c-finra-walkforward` @ `b12015997cdb13ea46b48df46b82e52eeedd479f`
Run reviewed: GitHub Actions `40098425254`
Artifact: `phase20c-finra-walkforward`

## Status

**DIAGNOSTIC_WALKFORWARD_READY — not promotion-ready.**

The latest Phase 20C artifact is internally consistent and PIT/chronological, but the result does not support promoting FINRA short-flow features as an incremental signal.

## Data audit

- Valid universe: 329
- Failures: 6
- FINRA CNMS start: 2018-08-01
- Files needed: 2,020
- Files available in this run: 1,382
- Train signals: 24
- FINRA-eligible train signals: 20
- Pseudo-OOS dates: 12
- Final OOS holdout signals: 6

The 1,382/2,020 file availability is a material coverage limitation. It is not treated as a positive result and must be resolved or explicitly modeled before a final economic conclusion.

## Walk-forward results

| Horizon | Mean delta vs blocked control | Median | Positive dates | Positive rate |
|---|---:|---:|---:|---:|
| 5D | +0.141% | -0.049% | 5/12 | 41.7% |
| 10D | -1.686% | -1.837% | 3/12 | 25.0% |
| 20D | -0.858% | -0.333% | 5/12 | 41.7% |

The earlier apparent 20D strength is not reproduced in the latest artifact. This is a material reason **not** to promote the hypothesis.

## Interpretation

The selected features migrate over time (`SHORT_RATIO_PERSIST20` → `SHORT_RATIO_Z20` → `SHORT_EXEMPT_RATIO`). That instability, combined with negative 10D/20D aggregate deltas and incomplete historical file coverage, makes the current evidence insufficient to claim an economic edge.

Do **not** interpret short-sale volume as short interest. FINRA explicitly distinguishes daily short-sale volume from the twice-monthly short-interest position snapshot.

## Decision

- **Do not modify F80_TOP20_PARTIAL50_BASELINE_C20.**
- **Do not tune thresholds to rescue Phase 20C.**
- Keep Phase 20C archived as a diagnostic hypothesis.
- Before another FINRA test, require a data-coverage audit and a pre-specified joint test of short-flow versus short-interest dynamics.
- Prefer the next test to ask whether *flow/position divergence* adds information after controlling for the frozen baseline, rather than testing more variants of short-flow alone.

## Broader Smart Money queue

1. FINRA short-flow + short-interest divergence: conditional continuation only after coverage repair.
2. FINRA OTC/ATS weekly summary: investigate access/authentication and historical PIT coverage.
3. Options: investigate Cboe historical quote/OI/IV availability; do not assume free public coverage is sufficient.
4. 13F: paused due to unresolved historical identity mapping.
5. Form 4: previously killed as an aggregate incremental signal.
6. CFTC/N-PORT/13D-G: remain secondary/paused unless feasibility improves.
