# Phase 21 — Smart Money Source Feasibility

## Objective

Identify public data sources that can reveal informed/institutional behavior and are usable in a strict chronological research design. FINRA short-flow remains one source, not the architecture.

## Decision criteria

A source is promoted to research only if it has:

1. Historical depth sufficient for meaningful training and OOS validation.
2. Security-level or economically relevant market-level coverage for the research universe.
3. A reproducible observation timestamp / publication timestamp so point-in-time availability can be reconstructed.
4. A stable machine-readable access path.
5. Enough observations to test horizons without excessive multiple-testing risk.
6. A clear economic interpretation that can be falsified.

## Current feasibility ranking

| Source | Historical depth | Security-level | Point-in-time timestamp | Initial priority | Notes |
|---|---:|---:|---:|---:|---|
| SEC EDGAR Form 4 | Strong | Yes | Yes | HIGH | Insider transactions; acceptance time is available and filings are generally public within minutes. |
| FINRA OTC/ATS transparency | Multi-year, with historic datasets | Yes | Yes/mostly | HIGH | Weekly ATS/non-ATS activity and block summaries; potentially useful as a second microstructure/off-exchange layer. |
| FINRA Short Flow + Short Interest | Strong for available periods | Yes | Yes | HIGH | Already under Phase 20; short volume is not the same thing as short position. |
| OCC options statistics | Strong aggregate history | Mostly aggregate from public monthly pages | Limited for contract-level point-in-time | MEDIUM | OCC confirms large and growing options volume and publishes open-interest statistics; contract-level historical accessibility must be verified before research. |
| CFTC COT / TFF | Very strong | No, futures/market level | Yes | MEDIUM | Excellent historical depth and classification, but mostly useful as a market-regime/context factor rather than a stock selector. Reports use Tuesday positions and are generally released Friday. |
| 13F institutional holdings | Strong | Yes | Yes, but delayed | MEDIUM | Useful for slower institutional accumulation/ownership hypotheses; filing delay makes it unsuitable as a naive short-horizon signal. |
| SEC XBRL / corporate filings | Strong | Yes | Yes | MEDIUM | Useful for event/information-flow features beyond Form 4, especially filing timing and revisions. |
| Exchange/order-book microstructure | Potentially strong | Yes | Depends on vendor | LOW until audited | High potential but historical depth and cost/access are the gating issues. |

## Research hypotheses

Do not encode "smart money" as a directional assumption. Test whether observable behavior precedes returns after controlling for prior returns, volatility, liquidity and frozen LTM.

Examples:

- Insider accumulation intensity and clustering.
- Off-exchange/ATS block activity relative to total volume.
- Change in off-exchange share concentration by reporting participant.
- Short-flow changes that are abnormal relative to each security's history.
- Option activity/open-interest changes relative to baseline, only if point-in-time historical contract data is reproducible.
- Slow institutional ownership changes from 13F as a regime/context variable.
- CFTC financial positioning as a market-level regime variable.

## Required validation

Every candidate factor must be evaluated with:

- feature timestamp <= signal timestamp;
- publication/availability timestamp <= signal timestamp;
- chronological train/validation/test splits;
- cross-sectional and time-series diagnostics;
- residualized incremental tests against LTM;
- F80 counterfactual with identical exposure and costs when warranted;
- bootstrap confidence intervals;
- leave-one-date-out diagnostics;
- horizon grid without a predetermined holding period;
- stability by market regime and liquidity bucket.

F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen.

## Current Phase 20C interpretation

The first chronological FINRA walk-forward run completed successfully. It produced 12 pseudo-OOS test dates after requiring at least 8 prior FINRA-eligible training signals. Replacement-minus-blocked mean delta was approximately -0.50 percentage points at H5, -1.30 pp at H10, and +1.65 pp at H20. The selected factor varied across dates (SHORT_RATIO 5, SHORT_RATIO_PERSIST20 4, SHORT_RATIO_ACCEL 2, SHORT_EXEMPT_RATIO 1). This is insufficient evidence for a production FINRA overlay and indicates that the next research effort should broaden the source set rather than force FINRA into F80.
