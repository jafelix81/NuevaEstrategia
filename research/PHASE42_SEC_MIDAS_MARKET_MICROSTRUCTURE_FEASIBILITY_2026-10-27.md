# Phase 42 — SEC MIDAS market-microstructure feasibility gate

Date: 2026-10-27

## Objective
Evaluate a public SEC Market Information Data Analytics System (MIDAS) dataset as a Smart Money / informed-trading hypothesis source, without assuming that microstructure activity represents informed capital.

## Source
The SEC publicly documents MIDAS as collecting exchange order/quote messages, cancellations, executions and off-exchange executions, with microsecond timestamps internally. The public market-structure downloads expose derived security-level daily metrics rather than the full raw feed.

The SEC methodology states that the Monthly User Download Files contain each variable for each ticker, day and exchange. The current public market-structure dataset pages cover January 2012 through June 2026.

## Candidate variables
Initial candidates, to be pre-registered rather than optimized after seeing returns:
- Trade-to-order volume ratio.
- Cancel-to-trade ratio, with exchange-methodology exclusions respected.
- Hidden trade rate / hidden volume.
- Odd-lot rate / odd-lot volume.
- Changes in these measures relative to each security's own history.

These are market-structure variables, not direct measures of institutional ownership or "smart money". The hypothesis is that abnormal changes in displayed-liquidity interaction and hidden execution may contain incremental information about future returns or volatility.

## Feasibility gates
1. Download an actual public user file and inspect the schema; do not rely only on summary charts.
2. Confirm security identifier/ticker coverage against the frozen research universe across multiple historical periods.
3. Confirm the exact publication/availability date of each file. The SEC methodology states the security universe is updated monthly with a 3–4 week lag; the signal must use only information demonstrably available before the simulated signal timestamp.
4. Treat any metric revisions or methodology changes as separate regimes. In particular, NYSE feed methodology changed in May 2017 and the SEC changed the round-lot definition beginning Nov. 3, 2025.
5. For cancel-to-trade, do not mix incomparable NYSE/Amex level-book measures with order-based feeds. Prefer trade-to-order and hidden-volume measures initially because the SEC explicitly documents their methodology and comparability constraints.
6. Check whether the public file contains only end-of-day aggregates. If so, this source is a slower weekly/monthly-information signal rather than an intraday order-flow signal.
7. Establish a conservative knowledge date equal to the documented release/publication date, not the observation date.
8. Only after all gates pass, run a small chronological OOS test versus frozen F80/LTM with identical exposure, costs and universe.

## Hypotheses — not assumptions
H1: An abnormal increase in hidden-volume share predicts subsequent relative returns after controlling for LTM/F80 and recent momentum/volatility.

H2: Changes in trade-to-order volume or cancellation intensity contain incremental information about future returns after controlling for recent returns, turnover and volatility.

H3: A combined microstructure shock is more informative than any single raw level, but only if the combination is pre-registered before OOS testing.

H4: Any apparent predictive power must survive a return-chasing control and must not simply identify stocks that already experienced abnormal price/volume moves.

## Economic test design if feasible
- Frozen comparator: F80_TOP20_PARTIAL50_BASELINE_C20.
- Chronological walk-forward only.
- Same universe, dates, execution, exposure and transaction-cost assumptions for control and candidate.
- Primary metric: incremental residual forward return after controlling for frozen LTM/F80 ranking.
- Secondary: Spearman IC, bucket spread, hit rate, block-bootstrap CI and LOO stability.
- Explicit PIT knowledge-date filter based on actual SEC release availability.
- Kill if incremental information is not robust OOS or if the feature is merely a repackaged momentum/volume effect.

## Current decision
`FEASIBLE_PUBLIC_CANDIDATE_PENDING_ACTUAL_FILE_AUDIT`

This source is materially more attractive than another round of tuning failed FINRA short-interest signals because it is public, long-history (2012–2026), security-level, and directly related to market microstructure. It is not yet an alpha candidate: the decisive unknown is the exact public-file release timing and the resulting usable universe overlap under a conservative PIT rule.

## Sources
- SEC MIDAS overview and public-data description.
- SEC Market Activity Report Methodology.
- SEC Summary Metrics by Decile and Quartile / market-structure downloads.
