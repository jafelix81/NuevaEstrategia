# Phase 511 — OptionMetrics implied-dividend gap: data feasibility and PIT gate

**Date:** 2026-11-19 local  
**Status:** candidate admitted for further feasibility review only; no data purchased, no alpha test authorized.  
**Research class:** option-implied forward fundamental / dividend-risk signal. This is not a direct measure of institutional identity or "smart money".

## Executive finding

OptionMetrics publishes an implied-dividend dataset for U.S. optionable, dividend-paying single-name equities and ETFs. Its product brochure states coverage from 2018-01-01, daily/nightly FTP updates, and records keyed by SecurityID and projected ex-date, with annualized yields and amounts. The product was announced on 2024-10-02. The 2018–2024 historical portion is therefore a backfilled archive relative to the product's public launch unless the vendor can supply contemporaneous vintages or the signal is independently reconstructed from raw historical option quotes.

A vendor-authored research paper, using March 2018–January 2026 data, reports a 54 bp/month (about 6.5% annualized) low-gap minus high-gap spread. The industry-neutral long/short has reported Sharpe 0.71 and max drawdown -8.6%; its Fama-French six-factor alpha is 3.94% annualized with t=1.48, which is **not statistically significant at conventional levels**. No independent replication or untouched holdout is documented in the material reviewed. This is a hypothesis worth auditing, not evidence of a deployable edge.

## Source facts

1. Product page: https://optionmetrics.com/implied-dividend/ — describes risk-neutral dividend projections inferred from U.S. single-name options and American-style binomial pricing.
2. Product brochure: https://optionmetrics.com/wp-content/uploads/2024/09/IvyDB-Implied-Dividend.pdf — states all optionable, dividend-paying U.S. single-name securities and ETFs, coverage beginning 2018-01-01, SecurityID + projected ex-date output, annualized yield/amount, and nightly FTP updates.
3. Product launch: https://optionmetrics.com/news/optionmetrics-ivydb-implied-dividend-data-product-projects-us-security-implied-dividends-two-years-into-future-using-options-sentiment/ — announced 2024-10-02.
4. Vendor paper: https://optionmetrics.com/wp-content/uploads/2026/05/The-Dividend-Valuation-Gap-Extracting-Alpha-from-Option-Implied-Yields-2.pdf — sample March 2018–January 2026; gap = implied yield minus trailing realized yield.
5. IvyDB US product page: https://optionmetrics.com/data-products/ — says daily options history begins January 1996, includes option prices/volume/OI, underlying data, rates, dividends and corporate actions, permanent security IDs, and ticker/name-change history. This may support independent reconstruction, subject to product access and licensing.

## What the vendor paper actually reports

- Universe: optionable, dividend-paying U.S. single-name securities; top 80th percentile by market capitalization in the sorting month; valid implied dividend.
- Signal: Dividend Gap = Implied Yield - Realized Yield.
- Low-gap names are long; high-gap names are short.
- Reported spread: 54 bp/month, approximately 6.5% annualized.
- Industry-neutral long/short: Sharpe 0.71, max drawdown -8.6%.
- FF6 annualized alpha: 3.94%, monthly coefficient 0.3286%, t=1.48. The t-stat is below conventional significance thresholds.
- The paper also reports a dependent double sort within trailing-yield terciles; the largest spread is in the high-yield tercile.
- No verified independent holdout, vendor-independent replication, complete turnover/cost analysis, or live execution record was identified.

Do not present the 6.5% annualized spread as expected net alpha. It is a vendor-reported historical result, not yet independently validated.

## Methodology disclosed by the paper

- Matched call/put pairs at the same strike.
- American-style option valuation using Cox-Ross-Rubinstein binomial trees, solving implied volatility and dividend yield jointly.
- Options expiring more than 60 days out.
- OTM call / ITM put pairs only.
- At least five matched strikes per maturity.
- Remove bids below $0.10; include regular distributions only.
- Median across up to ten strikes per maturity.
- Kalman filtering across projected ex-date term structure and interpolation to a 90-day horizon.
- Trailing realized yield uses the previous four quarters of dividends scaled by current price.

The product brochure calls its smoothing a proprietary Gaussian filter, while the 2026 paper describes a multivariate Kalman filter. Exact filter specification, initialization, one-sided versus two-sided treatment, revision policy, and parameter history must be clarified. A two-sided smoother or any use of future ex-dates/quotes would invalidate historical PIT.

## Data-feasibility and PIT audit

| Gate | Current finding | Disposition |
|---|---|---|
| Historical start | 2018-01-01 advertised | Potentially adequate for exploratory work |
| Product launch | 2024-10-02 | 2018–2024 archive is retrospective unless vintages/reconstruction are proven |
| Daily delivery | Nightly FTP advertised | Exact file-ready time and first receipt not published |
| Revisions | IvyDB US daily patches exist; implied-dividend product revision policy not verified | Must obtain policy and version history |
| Universe | Optionable dividend payers and ETFs | Not all 335 F80 names; overlap and delisted coverage unverified |
| Identity | SecurityID + projected ex-date | Need effective-dated SecurityID↔ticker/CUSIP/CIK crosswalk |
| Model vintage | CRR + Kalman/Gaussian smoothing described at high level | Exact causal algorithm/version history unresolved |
| License/price | No public price in reviewed product materials | Written quote and permitted use required |
| Sample data | No sample downloaded | No schema or actual coverage certification |

**Current admission:** CONDITIONAL_RESEARCH_CANDIDATE / HISTORICAL_PIT_NOT_CERTIFIED.

No vendor contact, subscription, purchase, or credential creation has been performed.

## Preregistered hypotheses (not tested)

- H1 — Return premium: more negative 90-day implied-minus-trailing yield gap predicts higher subsequent total returns among eligible dividend payers.
- H2 — Dividend-risk channel: low-gap names have a higher frequency/severity of dividend reductions over the next 90 days.
- H3 — Incremental information: the gap adds information beyond trailing dividend yield, sector, size, value, profitability, investment, momentum, volatility, liquidity, payout ratio, and earnings risk.
- H4 — Term structure: the 90-day level and a small, pre-specified 90-day versus 1-year slope may add information; do not mine many maturities.
- H5 — Regime/interaction: any stronger high-yield-tercile effect must be tested as a pre-specified interaction, not selected after observing returns.

Competing explanation: the gap may simply price dividend-cut risk, sector composition, borrow constraints, or a dividend-value tilt. A higher return may be compensation for risk rather than exploitable alpha.

## Required reconstruction and test design

1. Use only first-received daily files; record vendor file timestamp, actual receipt timestamp, hash, version, and correction linkage. The first executable observation is the next regular equity session after receipt, not the file's nominal date.
2. If historical vintages cannot be obtained, treat the vendor backfill as exploratory only. Strict historical PIT would require independent reconstruction from contemporaneous raw option quotes, underlying prices, rates, and point-in-time dividend data.
3. Implement a forward-only causal filter. No two-sided smoothing, future quote, future ex-date, or later patch may leak into a historical formation date.
4. Use an effective-dated SecurityID/security-master crosswalk including delisted names. Confirm overlap with the 335-name historical F80 universe before computing coverage.
5. Reconstruct trailing yield only from dividends known by the formation timestamp; do not use a current revised dividend history as if it were available then.
6. Replicate the vendor's monthly formation as a diagnostic, then test incremental value against frozen LTM/F80 using identical capital, exposure, costs, and rebalance/holding rules. Do not compare a gross long/short decile paper portfolio directly with F80.
7. Include realistic bid/ask, commissions, borrow availability/fees, and manufactured dividend payments on short positions. Measure turnover and capacity.
8. Chronological discovery/validation only. Backfilled 2018–2024 data may not enter strict PIT OOS unless independently reconstructed. Prospective data from actual receipt can form a clean forward ledger.
9. Report confidence intervals, block bootstrap, leave-one-out by issuer/sector and regime, multiple-testing correction, and robustness to dividend-yield/sector/size controls. Preserve the holdout.

## Kill criteria

Kill or archive the hypothesis if:
- The gap's return effect disappears after trailing yield, sector, size, value, quality, momentum, volatility and liquidity controls.
- It predicts dividend cuts but offers no positive risk-adjusted return after costs; in that case it may remain a risk flag only if it improves drawdown/utility at equal exposure.
- The effect depends on retrospective revisions, a two-sided smoother, or uncertain first-availability timestamps.
- The result is concentrated in a few issuers, one sector, one dividend-cut episode, or one regime.
- Bootstrap/LOO/OOS evidence is unstable or the FF6-like alpha remains statistically indistinguishable from zero.

## Next gates

1. Obtain a sample, price, license, field dictionary, historical-vintage/correction policy, and exact nightly delivery SLA from OptionMetrics.
2. Confirm whether daily files preserve the original first-delivery state and whether the filter is strictly one-sided.
3. Audit 335-name F80 overlap and delisted-security coverage using SecurityID.
4. If vendor access is uneconomic, estimate whether raw IvyDB US or another properly licensed OPRA source can support an independent causal reconstruction.

No alpha test is authorized until these data gates pass. No change to F80_TOP20_PARTIAL50_BASELINE_C20.
