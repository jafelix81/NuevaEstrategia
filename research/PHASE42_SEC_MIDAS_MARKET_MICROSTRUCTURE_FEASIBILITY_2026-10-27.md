# Phase 42 — SEC MIDAS market-microstructure feasibility gate

Date: 2026-10-27

## Objective
Evaluate public SEC Market Information Data Analytics System (MIDAS) market-structure data as a Smart Money / informed-trading hypothesis source, without assuming that microstructure activity represents informed capital.

## Source and confirmed public coverage
The SEC's current public page **Metrics by Individual Security and Exchange** states that the dataset covers **January 2012 through June 2026** and provides security-by-day-by-exchange fields including Ticker, Date, Security, Cancels, Trades, LitTrades, OddLots, Hidden, TradesForHidden, OrderVol, TradeVol, LitVol, OddLotVol, HiddenVol and TradeVolForHidden. The page currently lists quarterly ZIP downloads from 2012 Q1 through 2026 Q2; individual quarterly files are roughly 68–190 MB.

The SEC methodology independently confirms that the Monthly User Download Files contain each variable for each ticker, day and exchange. MIDAS internally processes exchange order/quote messages, cancellations and executions with microsecond timestamps, but the public downloadable security-level series are derived daily aggregates. Therefore this research line should be treated as **daily market-structure information**, not as raw intraday order-flow data.

## Candidate variables
Pre-register before OOS:
- Trade-to-order volume ratio.
- Hidden trade rate / hidden volume.
- Odd-lot rate / odd-lot volume.
- Cancel-to-trade ratio, with documented exchange-methodology exclusions.
- Changes/shocks in each variable relative to the security's own history.

These are market-structure variables, not direct measures of institutional ownership or "smart money". The hypothesis is that abnormal changes in displayed-liquidity interaction and hidden execution may contain incremental information about future returns or volatility.

## Important methodology breaks / exclusions
- The SEC says the CRSP security universe is updated monthly with a **3–4 week lag** from the final trading day of the previous month. This must be handled as a separate PIT universe-selection issue.
- MIDAS switched from the NYSE Ultrabook level feed to the NYSE Integrated Feed beginning **May 1, 2017**.
- The SEC warns that NYSE/Amex level-book data are not directly comparable with order-based feeds for cancel-to-trade and certain odd-lot measures. Prefer trade-to-order and hidden-volume measures initially.
- The SEC changed the round-lot definition beginning **Nov. 3, 2025**. Any odd-lot feature must either be split into regimes or normalized so the definition change cannot create a false signal.
- SEC feedback notes that some exchanges can be excluded from hidden-order ratios when the feed does not allow definitive identification; the denominator must therefore be respected exactly as documented.

## Feasibility gates
1. Use an actual quarterly public ZIP and inspect its schema rather than relying only on summary charts.
2. Measure overlap with the frozen 335-stock universe across multiple quarters, including pre/post 2017 and pre/post 2025 methodology regimes.
3. Determine the actual historical release/publication availability of each quarterly file. Observation date is not the knowledge date.
4. Construct a conservative PIT knowledge date using the documented release process; if exact posting timestamps cannot be reconstructed, use a deliberately later availability assumption.
5. Separate security-universe eligibility from metric observation date to avoid look-ahead from the monthly CRSP universe update.
6. Determine whether the usable public series is sufficiently frequent for the intended holding horizons; if only quarterly releases are practical, it cannot support a daily signal despite daily observations inside the files.
7. Only after these gates pass, run a small chronological OOS test versus frozen F80/LTM.

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
- Explicit PIT knowledge-date filter based on actual SEC release availability and conservative universe timing.
- Kill if incremental information is not robust OOS or if the feature is merely a repackaged momentum/volume effect.

## Current decision
`FEASIBLE_PUBLIC_CANDIDATE_PENDING_ACTUAL_FILE_AUDIT`

The source is now confirmed to have a long, continuous public download history and the required security-level variables. The decisive remaining gate is an actual-file audit for universe overlap and PIT release timing. No alpha claim and no production strategy change are justified yet.

## Official sources
- SEC Metrics by Individual Security and Exchange.
- SEC Market Activity Report Methodology.
- SEC MIDAS overview / Market Structure Analytics.
