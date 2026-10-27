# Phase 40 — Historical options data feasibility

Date: 2026-10-26

## Objective
Identify a reproducible historical options source capable of testing whether security-level options activity contains incremental information beyond frozen LTM/F80.

## Leading source
Cboe DataShop is currently the strongest candidate for a security-level options-flow/OI/IV/skew audit.

Official Cboe documentation reports historical availability beginning:
- Open-Close Volume Summary EOD C1: January 2005.
- Option Quotes: January 2010 in the DataShop FAQ; the current interval product page advertises January 2012 onward, so exact product-specific start date must be verified before use.
- Option EOD Summary: January 2010.
- Option Trades: January 2010 in the DataShop FAQ.
- Option Sentiment: January 2012.

Cboe's Open-Close product provides volume summaries by capacity (Customer, Pro-Customer, Broker, Firm, Market Maker). Option Quotes can provide NBBO/quote fields with optional open interest and implied-volatility/Greek calculations; Option Trades provides transaction-level detail.

## Hypothesis — explicitly not assumed to be "smart money"
H1: abnormal directional options activity by non-market-maker capacities contains incremental information beyond LTM/F80.
H2: flow combined with changes in open interest is more informative than volume alone.
H3: IV/skew changes add information conditional on underlying momentum/volatility.
H4: any apparent predictive power must survive controls for prior returns, volume, volatility and return-chasing.

## Required feasibility gates
1. Full frozen-universe security mapping.
2. Historical coverage across multiple periods, with a stable common universe.
3. Reproducible ex-ante timestamp: determine exactly when each purchased historical field would have been available to a strategy.
4. Explicit treatment of OCC end-of-day open interest as prior-night information when applicable.
5. Transaction/capacity definitions documented before testing.
6. Commercial-license/accessibility confirmed before building a production dependency.

## Research rule
No alpha test is authorized until the data-feasibility gate passes. If commercial access cannot be obtained reproducibly, archive the candidate rather than substitute a different vendor or a look-ahead-prone proxy.

## Current status
FEASIBILITY DESIGN COMPLETE. Commercial access and actual frozen-universe coverage remain to be established. No strategy change authorized.
