# Phase 60 — OptionMetrics DOOD replication and incremental-value preregistration

Date: 2026-11-04  
Original branch: phase60-optionmetrics-dood-hypothesis-preregistration  
Superseding formula correction: Phase 94  
Status: hypothesis preregistered; data-feasibility gate not passed; no return test run.

## 1. Prior evidence (not independent validation)

OptionMetrics' paper, published June 2, 2022, studies Demand for Option Order Delta (DOOD) using IvyDB US and IvyDB Signed Volume. It reports a January 2016–March 2022 sample and five-trading-day rebalancing.

Reported results:
- High-minus-low DOOD spread: 0.32% per week.
- Weekly three-factor alpha: 0.26%, described as significant at 5%.
- Detailed Table 2 discussion: long/short Sharpe 1.03.
- Abstract: long/short Sharpe 1.08 versus 0.81 for the S&P 500.
- Volatility-targeted Sharpe: 1.15.

The paper therefore contains an internal 1.08 versus 1.03 Sharpe discrepancy. Preserve both claims; do not silently select one. Reconcile against the source table/calculation if a replication is ever run.

The paper filters to optionable securities, excludes ETFs and indices, retains the upper 90% of market capitalization, requires price above $5, IV below 300%, and at least 1,000 contracts of ask volume. It uses equal-weighted weekly decile portfolios.

This is vendor-produced prior evidence, not proof of an investable edge:
- The data vendor produced the study and sells the data.
- The sample ends in March 2022; no independent 2023–2026 OOS result is established by the paper.
- The paper's universe and filters differ from historical F80.
- It explicitly discusses both informed trading and dealer hedging/momentum.
- DOOD is reported as positively autocorrelated.
- Gross decile spreads do not establish net incremental value over frozen F80/LTM.

Primary paper: https://optionmetrics.com/wp-content/uploads/2023/05/Demand-for-Option-Order-Delta-DOOD.pdf

## 2. Data-feasibility gate before returns

Preferred input is the historical IvyDB US + IvyDB Signed Volume series used by the paper. IvyDB TradeFlow is the current evolution of Signed Volume and may provide richer context, but it is not automatically identical to the legacy fields.

Required before any economic test:
1. Obtain a sample for representative F80 names and historical delisted/predecessor issuers, with 5-minute, 30-minute and EOD fields.
2. Obtain the exact data dictionary for bid/ask/midpoint/unknown volume, trade conditions, complex trades, venue, VWAP, NBBO aggressiveness, lot-size buckets, retail/institutional proxy labels and correction handling.
3. Confirm whether legacy Signed Volume fields used by the 2022 paper are reproducible back to January 2016.
4. Resolve the discrepancy between the current product page's January 2016 history claim, the 2022 paper's January 2016 sample, and the January 2020 launch announcement that described history beginning in March 2018. A later backfill is possible but unverified.
5. Confirm whether TradeFlow's new proprietary fields are historically backfilled to 2016 or begin later; obtain methodology/version dates and restatement policy.
6. Obtain IvyDB permanent security/contract IDs, adjusted deliverables, multipliers, expired options, ticker changes and delisted-underlying retention.
7. Obtain snapshot cutoffs, file delivery/publication timestamps, late corrections and patch files. Use next trading session as conservative KnowledgeDate until exact historical availability is evidenced.
8. Reconstruct historical F80 membership and optionability point in time. Current 335 tickers are not a historical universe.
9. Require at least 95% coverage of historically optionable eligible issuer-days in each tested period, with missingness by year, issuer, market cap and liquidity.
10. Confirm business-use licensing, storage/retention and derived-feature rights.

Official product sources:
- TradeFlow: https://optionmetrics.com/ivydb-tradeflow/
- Signed Volume: https://optionmetrics.com/signed-volume/
- January 2020 launch announcement: https://www.tradersmagazine.com/departments/options/optionmetrics-launches-ivydb-order-flow-tracker/

No purchase or forward-return test is authorized until these gates pass.

## 3. Primary signal definition — corrected by Phase 94

For issuer s and information date t, reproduce the paper's equation exactly:

DOOD(s,t) = SUM over option symbols i of [ Delta(i,t) * (TotalAskVolume(i,t) - TotalBidVolume(i,t)) ] / UnderlyingDailyShareVolume(s,t)

The published paper does not include a contract multiplier. The earlier Phase 60 draft inserted one; that was not an exact replication and is superseded by Phase 94.

Rules:
- Use the signed delta supplied by the validated IvyDB field.
- Put deltas are negative; do not flip the put sign a second time.
- Sum across the full option chain.
- Use the paper's same-day underlying daily share-volume denominator for exact replication.
- Keep midpoint, unknown and unclassified volume separately; do not force it into ask or bid.
- Do not assume a multiplier of 100 for adjusted contracts.

A separate sensitivity may calculate multiplier-adjusted delta-equivalent shares:
SUM[Delta * historical multiplier/deliverable * (AskVolume - BidVolume)] / underlying share volume.
This is a different feature, not published DOOD. Report it separately and only after the exact formula is locked.

Other preregistered sensitivities:
- Prior-20-day ADV normalization instead of same-day stock volume.
- Calls and puts separately, preserving signed put delta.
- ITM/ATM/OTM, delta, DTE and expiration buckets.
- Exclude 0DTE from the primary swing-trading diagnostic and report it separately.
- Separate bid/ask/midpoint/unknown and trade-condition/complex-order categories.
- Lot-size and TradeFlow participant-proxy features only as separate post-2021/history-verified hypotheses; never treat lot size or proprietary labels as beneficial-owner identity.

## 4. Competing explanations

- H1 — Information: positive net buyer-initiated delta demand predicts positive subsequent underlying returns after controlling prior returns, volatility, liquidity, earnings and market/sector exposures.
- H2 — Dealer hedging / momentum: flow is a response to prior price movement and dealer hedging; predictive value weakens after prior-return and same-day momentum controls.
- H3 — Volatility/positioning: flow predicts changes in IV/skew or subsequent realized volatility more reliably than return direction.
- H4 — Incremental model value: the signal improves frozen F80/LTM under identical exposure and costs.
- H5 — Participant-proxy heterogeneity: TradeFlow's proprietary retail/institutional proxy buckets differ, but results survive methodology-version and threshold checks.

All explanations remain hypotheses. Do not describe any category as Smart Money before evidence.

## 5. Chronological validation and holding-period discovery

Initial split, frozen before forward returns:
- Development: 2016–2019.
- Validation/model selection: 2020–2022.
- Locked OOS: 2023–2026 through the last complete date.

First reproduce the vendor's five-session weekly portfolio design as a diagnostic. Then examine the full decay/horizon profile at 1, 2, 5, 10, 20 and 40 trading sessions and event-time exits. These are measurement horizons, not imposed holding-period limits. Any horizon/exit selection belongs in nested chronological validation; final OOS remains untouched.

KnowledgeDate and execution:
- If EOD files arrive overnight, KnowledgeDate is the next trading session unless archived original delivery evidence proves otherwise.
- For comparison with frozen F80, execute at the next session close, not the signal-date close.
- Apply identical availability and execution rules to baseline and augmented models.

## 6. Controls and tests

At minimum, control for:
- 1/5/20/60-session prior returns and trend.
- Realized volatility and gap risk.
- Market beta, sector/industry returns and broad risk regime.
- Market cap, price, ADV, spread/liquidity and borrow constraints where relevant.
- Earnings/event windows, optionability and option-chain liquidity.
- IV level, skew, term structure, DTE composition and 0DTE share.
- Frozen LTM/F80 scores and ranks.

Report:
- Cross-sectional rank IC and conditional return spreads.
- Standalone DOOD and incremental F80-augmented model.
- Same portfolio exposure, turnover, costs and missing-data treatment.
- Net returns, drawdown, volatility, Sharpe/Sortino and tail loss; no CAGR target.
- Chronological walk-forward, purging/embargo where labels overlap, block bootstrap and issuer-clustered uncertainty.
- Leave-one-issuer-out and regime sensitivity.
- Multiple-testing correction across all tested signal variants and horizons.

## 7. Kill criteria

Kill or archive the hypothesis if:
- Historical PIT coverage or timestamp integrity fails.
- Legacy formula/fields cannot be reproduced.
- The signal does not survive prior-return/momentum controls.
- The effect is contemporaneous or reverses before next-session execution.
- Results concentrate in one issuer, event cluster or regime.
- The signal adds no robust OOS improvement versus frozen F80 at identical exposure and costs.
- Costs, turnover, liquidity constraints or realistic fills erase the effect.
- Results fail block bootstrap, issuer-clustered uncertainty or LOO robustness.
- TradeFlow classification definitions cannot be reconstructed historically.

A negative result is valid. Do not relax gates after viewing returns.

## 8. Decision

DOOD remains a high-priority research hypothesis. The exact published formula is now specified separately from multiplier-adjusted and enhanced TradeFlow features. No OptionMetrics data has been purchased or downloaded, no vendor contact has been sent, no forward returns have been calculated, and no strategy change is authorized.

F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen.
