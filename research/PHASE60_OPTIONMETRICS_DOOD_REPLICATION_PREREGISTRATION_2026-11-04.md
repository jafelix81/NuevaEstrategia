# Phase 60 — OptionMetrics DOOD replication and incremental-value preregistration

Date: 2026-11-04  
Branch: `phase60-optionmetrics-dood-hypothesis-preregistration`  
Status: hypothesis preregistered; data-feasibility gate not yet passed; no return test run.

## 1. Prior evidence (not independent validation)

OptionMetrics published a vendor research note introducing Demand for Option Order Delta (DOOD). It defines a daily cross-sectional signal as the sum, across option contracts, of option delta multiplied by buyer-initiated minus seller-initiated volume, scaled by underlying share volume.

The note reports a Jan 2016–Mar 2022 sample and a weekly (five-trading-day) rebalancing design. It reports:
- High-minus-low DOOD spread: approximately 32 bp per week (about 17% annualized).
- Long/short Sharpe: approximately 1.03.
- Weekly three-factor alpha: approximately 0.26%, reported significant at 5%.
- The vendor's volatility-scaled variant reports Sharpe around 1.15.

The paper filters to optionable securities, excludes ETFs and indices, keeps the upper 90% of market capitalization, requires price above $5, IV below 300%, and at least 1,000 contracts of ask volume. It uses equal-weighted weekly decile portfolios.

This is a useful prior hypothesis, not proof of an investable edge for our strategy:
- It is vendor-produced research on the same vendor's data.
- The sample ends in March 2022; there is no independent 2023–2026 OOS result in that note.
- The filters and universe differ materially from historical F80.
- The proposed informed-trading explanation is not unique. The paper also discusses dealer delta/gamma hedging and positive feedback from prior returns; it notes DOOD is positively autocorrelated.
- Reported gross portfolio spreads do not establish net incremental performance versus frozen LTM/F80 under our exposure, costs, timing and risk constraints.

Primary source: https://optionmetrics.com/wp-content/uploads/2023/05/Demand-for-Option-Order-Delta-DOOD.pdf

## 2. Data-feasibility gate before returns

Preferred input is IvyDB US + IvyDB TradeFlow, with ORATS Near-EOD as a lower-cost historical context/validation source.

Required before any economic test:
1. TradeFlow sample for representative F80 names and known delisted/predecessor issuers, with 5-minute, 30-minute and EOD fields.
2. Exact data dictionary and definitions for bid/ask/midpoint classification, trade description codes, venue, VWAP, lot-size buckets, retail/institutional proxy labels and correction handling.
3. Confirmation that classification rules are stable and historically applied back to January 2016; retain methodology version and any restatements.
4. IvyDB permanent security/contract IDs, adjusted deliverables, multiplier, expired options, ticker changes and delisted underlyings.
5. Timestamp of each snapshot, EOD delivery, late corrections and patch files. Use next trading session as conservative KnowledgeDate until exact historical availability is evidenced.
6. Historical F80 membership and optionability reconstructed point-in-time. Current 335 tickers are not a historical universe.
7. Coverage target: at least 95% of historically optionable F80 issuer-days in each tested period, with missingness reported by year, issuer, market cap and liquidity.
8. ORATS sample must confirm expired/delisted contract continuity, 3:46 p.m. snapshot semantics, prior-night OCC OI and file publication timing.

No purchase or forward-return test is authorized until these gates pass.

## 3. Primary signal definition

For issuer (s) and information date (t):

[
DOOD_{s,t} =
rac{
sum_{c in mathcal{C}(s,t)}
Delta_{c,t},M_{c,t}
left(AskInitiatedVolume_{c,t}-BidInitiatedVolume_{c,t}ight)
}{
UnderlyingShareVolume_{s,t}
}
]

Where:
- (Delta_{c,t}) is the point-in-time option delta.
- (M_{c,t}) is the contract multiplier/deliverable conversion for that historical contract.
- Ask-initiated and bid-initiated volumes retain unknown/midpoint/ambiguous categories separately; do not force them into either side.
- The denominator is independent underlying share volume for the same information date.
- Use the vendor's permanent contract/security identifiers and adjusted deliverables. Never assume every contract has a multiplier of 100.

Replicate the vendor's definition first. Only after that replication is locked, evaluate preregistered alternatives:
- Normalize by prior 20-day underlying ADV instead of same-day volume.
- Separate calls and puts; ITM/ATM/OTM and delta buckets; short/medium/long DTE.
- Exclude 0DTE from the primary swing-trading signal; report it separately.
- Separate bid/ask/midpoint and trade-condition/complex-order categories.
- Compare raw signed delta demand with flow scaled by option notional and by prior OI.
- Use TradeFlow's retail/institutional labels only as vendor-derived proxies, not actual investor identity.

## 4. Competing explanations

- H1 — Information: positive net buyer-initiated delta demand predicts positive subsequent underlying returns after controlling for prior returns, volatility, liquidity, earnings and market/sector exposures.
- H2 — Dealer hedging / momentum: flow is primarily a response to prior price movement and dealer hedging; apparent predictability weakens materially after controlling for prior returns and same-day momentum.
- H3 — Volatility/positioning: flow predicts changes in IV/skew or subsequent realized volatility more reliably than direction of stock returns.
- H4 — Incremental model value: the signal improves the frozen F80/LTM model under identical exposure and costs, not merely as a standalone equal-weight decile spread.
- H5 — Participant-proxy heterogeneity: TradeFlow's retail/institutional proxy buckets have different predictive properties, but any result must survive alternative lot-size thresholds and classification-methodology checks.

All explanations remain hypotheses. Do not describe any category as "smart money" before evidence.

## 5. Chronological validation and holding-period discovery

OptionMetrics TradeFlow history begins January 2016. Initial chronological design:
- Development: 2016–2019.
- Validation and model selection: 2020–2022.
- Locked OOS: 2023–2026 through the last fully available date.

The exact split can be refined only before any forward returns are viewed. No random shuffling.

First reproduce the vendor's five-session weekly portfolio design as a diagnostic. Then examine the full decay/horizon profile at 1, 2, 5, 10, 20 and 40 trading sessions and event-time exits. These are measurement horizons, not imposed holding-period limits. Any horizon/exit selection must occur in nested chronological validation, with the final OOS untouched.

KnowledgeDate and execution:
- If EOD/snapshot data arrive overnight, KnowledgeDate is the next trading session.
- For comparison with frozen F80, execute at the next session close, not at the signal-date close.
- Apply the identical rule to baseline and augmented model.

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
- The signal does not survive prior-return/momentum controls.
- The apparent effect is contemporaneous or reverses before next-session execution.
- Results are concentrated in one issuer, one event cluster or one regime.
- The signal adds no robust OOS improvement versus frozen F80 at identical exposure and costs.
- Costs, turnover, liquidity constraints or realistic fills erase the effect.
- Results fail block bootstrap, issuer-clustered uncertainty or LOO robustness.
- TradeFlow classification definitions cannot be reconstructed historically.

A negative result is a valid research outcome. Do not relax gates after seeing returns.

## 8. Decision

OptionMetrics TradeFlow is the preferred candidate for directional option-flow research, subject to sample, coverage, timestamp and classification gates. ORATS Near-EOD is the preferred low-cost context source for IV/OI/quotes, subject to sample and PIT checks. No data has been purchased, no vendor contact has been sent, no forward returns have been calculated, and no strategy change is authorized.

`F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen.
