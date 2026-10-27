# Phase 41 — Cboe Borrow Intensity feasibility gate

Date: 2026-10-27

## Objective
Evaluate whether Cboe Hanweck Borrow Intensity Indicators are a feasible historical source for an independent/complementary Smart Money hypothesis, particularly after the public FINRA short-interest line failed economically.

## Why this source is different
Borrow Intensity is not treated as "smart money" by assumption. It is a securities-lending/short-demand proxy derived from option-implied borrow and adjusted using liquidity/term characteristics. The hypothesis is that changes in the cost/intensity of obtaining stock exposure for shorting may contain information that is not captured by semi-monthly reported short interest.

## Documented source characteristics
Cboe states that the product covers securities underlying U.S.-listed options (approximately 4,000 symbols), is available historically back to September 2014, and provides raw/smoothed indicators plus confidence measures for constant maturities including 45, 60, 90, 180, 270 and 360 days. Current observations are available at 20-minute intervals; the underlying calculation is described as millisecond-granularity implied borrow. Delivery is via CSV/SFTP.

## Candidate hypotheses — not assumptions
H1: An abnormal increase in Borrow Intensity predicts subsequent relative returns after controlling for LTM/F80, prior returns, volatility and liquidity.

H2: The change/slope in Borrow Intensity is more informative than its level alone.

H3: Borrow Intensity adds incremental information to FINRA short-interest change, rather than simply restating reported short interest.

H4: Any apparent signal must survive a return-chasing control: the feature must retain predictive value after conditioning on recent momentum and volatility.

## Feasibility gates before alpha testing
1. Obtain a reproducible historical sample or licensed access; no synthetic/proxy replacement is authorized.
2. Inspect the actual file schema and observation timestamps. Confirm that each historical observation has an unambiguous knowledge/availability time.
3. Verify frozen-universe overlap against the 335-name research universe across multiple historical dates, not just current coverage.
4. Verify survivorship treatment and symbol history for securities that changed ticker or ceased trading.
5. Establish the exact ex-ante rule for a daily strategy: e.g. last observation demonstrably available before the signal timestamp, with no use of later-revised observations.
6. Check whether raw/smoothed/confidence fields are revised historically. If revisions exist, only point-in-time retrievable values may be used.
7. Pre-register a small feature set before OOS testing: level percentile, 5/20-day change, and standardized change are sufficient initially. No broad parameter sweep.

## Economic test design if the gate passes
- Frozen comparator: F80_TOP20_PARTIAL50_BASELINE_C20.
- Chronological walk-forward only; no random train/test split.
- Same universe, dates, execution assumptions, exposure and costs for control and candidate.
- Primary test: incremental residual return after controlling for frozen LTM/F80 ranking.
- Secondary test: top/bottom buckets, Spearman IC, hit rate, block bootstrap CI and leave-one-out stability.
- Explicit return-chasing control using recent momentum/volatility features.
- Kill criterion: no statistically/economically credible incremental information after controls. Do not tune thresholds to rescue a weak result.

## Commercial/access constraint
Cboe lists Borrow Intensity as a DataShop product and provides a purchase interface; therefore this is not currently classified as a freely reproducible public source. This does **not** authorize a strategy dependency. The research state is `FEASIBLE_CANDIDATE_PENDING_ACCESS_AND_SCHEMA_AUDIT`.

## Decision
Borrow Intensity is promoted to a high-priority feasibility candidate because it has substantially longer history than the failed public FINRA short-interest series and directly measures a different economic mechanism. No alpha test and no change to F80/LTM are authorized until the actual historical dataset passes the PIT/schema/universe gates.

## Sources
- Cboe Borrow Intensity Indicators product documentation: https://datashop.cboe.com/borrow-intensity-indicators
- Cboe DataShop FAQ: https://datashop.cboe.com/faqs
- Cboe DataShop Academic Discount / licensing information: https://datashop.cboe.com/academic-discount
