# Phase 58 — Intrinio U.S. EOD Historical Options feasibility review

Date: 2026-11-04  
Branch: `phase58-intrinio-options-eod-feasibility`  
Status: CONDITIONAL LOW-COST FULL-OPRA CONTEXT / NOT YET DATA-VALIDATED. No return test authorized.

## Research question

Can Intrinio's U.S. EOD Historical Options feed provide a lower-cost, broad-OPRA historical options panel for the frozen F80 universe, supplying optionability, contract-level volume/OI, IV and Greeks as context for exchange-specific Cboe/MIAX participant-flow data?

## Official product facts

Product page: https://intrinio.com/options/eod-historical-options

- Source: OPRA; update frequency: daily.
- Product page advertises full option chains, close/bid/ask, volume, open interest, open-interest change, next-day open interest, IV change and Greeks.
- Individual plan access is advertised from $150/month, with a free trial.
- Standard plan history begins 2021-09-27.
- A one-time bulk download is advertised back to 2008-01-02; the public page does not state its exact price or whether all 335 requested symbols and delisted/expired series are included.
- Two delivery variants are described: approximately 4:45 p.m. ET (may require exchange paperwork) and 3:00 a.m. ET (no additional paperwork/fees).

Relevant API documentation:
- Options Chain EOD: https://docs.intrinio.com/documentation/web_api/get_options_chain_eod_v2
- Option Prices EOD by ticker: https://docs.intrinio.com/documentation/web_api/get_options_prices_eod_by_ticker_v2
- Option Prices EOD by contract identifier: https://docs.intrinio.com/documentation/web_api/get_options_prices_eod_v2

The by-ticker endpoint is described as returning contracts currently associated with a ticker. That wording creates a potential survivorship/expired-contract risk for historical research. The contract-identifier and chain endpoints support date/history parameters, but actual retention of expired contracts and delisted underlyings must be proven with a sample before this source can pass.

## What this source can and cannot identify

Potentially useful:
- Full-OPRA optionability by underlying/date.
- Contract-level volume, OI and OI changes.
- Bid/ask and closing prices.
- IV and Greeks for constructing put/call skew, term structure, delta buckets and exposure proxies.

Not supplied by this feed:
- Cboe/MIAX participant origin.
- Beneficial-owner identity.
- Reliable opening-versus-closing classification by participant.
- A verified aggressor-side label. Any bid/ask-volume field found in older CSV documentation must not be treated as buy/sell aggressor flow until its current definition and sample values are confirmed.

This is therefore a market-implied positioning/volatility context source, not a standalone “smart money” identifier.

## Relationship to Cboe and MIAX

- Intrinio and Cboe Option EOD Summary both describe OPRA-sourced market-wide options data. They are alternative vendor implementations of substantially the same consolidated market source, not independent market venues.
- Cboe Open-Close and MIAX Open-Close are exchange-specific participant/origin datasets. They can be joined to a broad OPRA context panel only after contract identifiers, adjusted roots, multipliers/deliverables, units and date conventions reconcile.
- Intrinio could reduce the cost of the full-OPRA denominator/IV/OI layer if its historical coverage and field quality pass. It cannot replace the participant classifications in Cboe/MIAX Open-Close.

## Conservative PIT treatment

- Preserve raw trade date and actual file/API retrieval timestamp separately.
- The advertised 3:00 a.m. ET version is after the prior session. Until actual historical delivery logs are available, set KnowledgeDate to the next trading session and execute no earlier than the next-session close, matching the existing end-of-day strategy convention.
- Do not use same-day EOD OI/IV as if known at the prior close.
- Exclude `next_day_open_interest` from the initial signal panel until the vendor confirms exactly when it becomes available and how it is calculated.
- Retain the vendor's delivered IV/Greek fields and model metadata. If recalculating, freeze one model and input convention before testing.
- Zero, stale, crossed or otherwise invalid bid/ask/IV/Greek observations remain missing; do not convert them to valid zeros.

## Required sample audit before any purchase or economic test

Request a free-trial or sample extract covering:
- At least 30–50 frozen-universe symbols, including ETFs, single names, low/high-option-volume names, delisted names, and known corporate-action/adjusted-root cases.
- Multiple dates spanning 2018/2019 (only if bulk data is supplied), 2021, 2023, 2025 and 2026.
- All expirations/strikes for each sample underlying/date, not a narrow current chain.
- At least one expired contract and one adjusted contract per applicable sample.
- Raw fields, pagination, symbol/contract identifiers, delivery timestamps, correction/revision policy and license terms.

Measure separately:
1. all-335 ticker/date reach;
2. reach among historically optionable F80 names;
3. completeness of contract-level close/bid/ask/volume/OI;
4. positive and valid IV/Greek rates;
5. expired-contract and delisted-underlying retention;
6. stable identifier and OCC multiplier/deliverable mapping;
7. missing/corrected file rate and reproducible KnowledgeDate.

No coverage percentage can be inferred from the product page's “full options chains” wording. Set the production coverage gate only after the sample definition and PIT optionable denominator are frozen.

## Candidate feature families (not yet preregistered for returns)

If the data gate passes, freeze a small set before inspecting returns:
- 25-delta put IV minus 25-delta call IV at matched expiry.
- 20–60 DTE term-structure slope at fixed delta/moneyness.
- Put/call OI and volume ratios by delta bucket.
- OI change normalized by prior OI, with explicit publication lag.
- Delta/gamma exposure proxies only with PIT multiplier/deliverable mapping.

These describe market-implied positioning and volatility, not the identity or skill of the traders. Control for prior underlying returns, realized volatility, earnings, liquidity, optionability, and broad market/sector moves.

## Decision

**CONDITIONAL — worth a sample/trial audit before paying for Cboe Option EOD Summary or MIAX multi-year flow.**

The advertised $150/month entry point and free trial make Intrinio a potentially efficient full-OPRA context candidate. However, bulk-history pricing, historical expired-contract retention, 335-name PIT coverage, contract identity and actual delivery timestamps remain unverified. No data has been purchased or downloaded, no forward returns were run, and no alpha claim is made.

`F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen.
