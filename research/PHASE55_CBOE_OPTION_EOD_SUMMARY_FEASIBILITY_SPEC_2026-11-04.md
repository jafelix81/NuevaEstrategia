# Phase 55 — Cboe Option EOD Summary feasibility
Date: 2026-11-04
Branch: phase55-cboe-option-eod-summary-feasibility
Status: sample schema validation pending.

## Product facts

Official product page: https://datashop.cboe.com/option-eod-summary

- Covers listed U.S. stock, ETF and index options disseminated over OPRA (not options on futures or non-U.S. markets).
- Historical data available from January 2012 to present.
- Daily file delivery; one file per day or month depending on grouping.
- Two snapshots: 15:45 ET and end-of-day.
- EOD fields: OHLC, trade volume, VWAP, NBBO bid/ask and size, and open interest.
- Optional Calcs purchase adds 15:45 implied volatility and Greeks (Delta, Gamma, Theta, Vega, Rho) plus active underlying price.
- Pick Symbols is supported, so a 335-ticker order may be possible; exact quote for the selected symbols/date range/Calcs must be confirmed in DataShop.

## Research value

This is a full-OPRA options-market snapshot, unlike the Cboe Open-Close EOD dataset which classifies participant flow only on Cboe exchanges. The two can be joined on trade date, underlying, root, expiration, strike and option type:

- Option EOD Summary: full-market NBBO, volume, OI and optional IV/Greeks.
- Open-Close EOD: Cboe-exchange participant type, buy/sell and open/close volumes.

Together they could test whether Cboe-observed participant imbalances lead changes in underlying price, volatility surface, OI or skew across the full OPRA market. They remain hypotheses, not evidence of informed trading.

## Sample audit

- Public sample ZIP: https://datashop.cboe.com/download/sample/217
- Inspect ZIP members, actual CSV schemas, non-null field rates, sample date, option-type coverage, target ticker overlap and optional Calcs fields.
- Do not infer full historical coverage from a sample file.

## Gates and limitations

- Base schema: at least 70% exact coverage of the frozen 335 tickers in the sample and at least 95% non-null coverage for the required EOD fields.
- Calcs gate is separate: IV/Greeks may be absent unless the Calcs option is included.
- Historical availability is documented, but point-in-time release timestamps are not. Use next-session KnowledgeDate conservatively.
- This source has no participant type, buy/sell side or open/close classification.
- Historical active/delisted ticker mapping and option-root/corporate-action normalization remain necessary.
- Licensing and price for a 335-symbol pick-list plus Calcs must be obtained before bulk retrieval.
- No forward returns or alpha test.

F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen.
