# Phase 63 — ThetaData OPRA trade/quote feasibility
**Date:** 2026-11-04  
**Status:** CONDITIONAL — high-priority raw-flow candidate; no data purchase or alpha test authorized.

## Executive decision

ThetaData is a materially stronger raw OPRA candidate than the earlier EOD-only alternatives for reconstructing buyer-/seller-initiated option flow. Its historical trade/quote endpoint returns each OPRA option trade paired with the last NBBO quote, with millisecond timestamps, exchange, size, price, trade condition, bid/ask, sizes and quote conditions. The documentation says historical matching uses quote timestamps less than or equal to trade timestamps; `exclusive=true` changes this to strictly earlier quotes. This supports a transparent aggressor-side classification without relying on a vendor's proprietary buy/sell label.

However, this is not yet a data-feasibility PASS. Business-use licensing, historical flat-file access, delisted-underlying coverage, trade-correction semantics in the historical API, and full 335-name historical coverage remain unverified. The public sample bundle is stock UTP/CTA data, not options data. No credentials or sample options data were acquired.

## Product, history and pricing

Official pricing reviewed 2026-11-04:

| Plan | Advertised price | Historical depth | Relevant features |
|---|---:|---:|---|
| Individual Options Standard | $80/month | 10 years | Tick-level, 4 concurrent requests, every OPRA NBBO quote, 15K trade streams |
| Individual Options Pro | $160/month | 14 years | Tick-level, 8 concurrent requests, every option trade stream, every OPRA NBBO quote, option-chain snapshots |
| Business Options | $1,600/month billed annually | 14 years | Tick-level, 1s/1m/EOD, full real-time trade stream, every OPRA NBBO quote |
| Startup business tier | advertised from $500/month | 14 years on business page | Eligibility, limits and exact terms require a written quote |

The options product page advertises OPRA coverage since June 2012 and 100% NBBO coverage. The Pro tier is therefore the only published individual tier that appears to span the full advertised 2012-06 history. Standard's 10-year window is sufficient for the preregistered 2016+ DOOD replication, but not for a 2012 start.

**Licensing gate:** the retail page explicitly says individual pricing is for personal use only and excludes redistribution or business use. It must not be used for commercial research, a firm workflow, or business deployment unless ThetaData confirms the license. The business page lists $1,600/month billed annually and startup pricing "as low as $500/month"; the latter is not a guaranteed quote. Do not assume the individual $80/$160 plans are permissible for the repo's intended use.

Official pages:
- https://www.thetadata.net/pricing
- https://www.thetadata.net/commercial-use
- https://www.thetadata.net/options-data

## Relevant API evidence

### Trade + contemporaneous NBBO

The v3 `option/history/trade_quote` endpoint returns every option trade reported by OPRA paired with the last NBBO quote at trade time. For deep historical data, the documented matching uses millisecond timestamps and accepts a quote only when `quote_timestamp <= trade_timestamp`. Set `exclusive=true` to require `quote_timestamp < trade_timestamp`; use the strict form for the primary no-lookahead reconstruction.

The response includes:
- underlying, expiration, strike and call/put;
- trade and quote timestamps;
- exchange sequence, exchange, trade condition, size and price;
- bid/ask, bid/ask sizes, exchanges and quote conditions.

The endpoint allows `expiration=*` for all expirations. Multi-day requests are limited to one month and must specify an expiration. The request-sizing guide recommends one week for option tick-level requests and one day for highly liquid symbols such as AAPL/SPX/SPY; it warns that responses above one million ticks can cause memory problems.

Documentation:
- https://www.thetadata.net/docs/operations/option_history_trade_quote.html
- https://www.thetadata.net/docs/Articles/Data-And-Requests/Request-Sizing.html

### Trade Greeks

The first-order trade-Greeks endpoint is marked Pro-only. It calculates Greeks for every OPRA trade and returns Delta, IV, trade timestamp, underlying timestamp and underlying price at the option trade time. It uses Black-Scholes by default; the vendor documents separate binomial-Greek endpoints for American-style options. The calculation defaults to SOFR and no dividend, but allows explicit `rate_value`, `annual_dividend` or `annual_dividend_amount` inputs.

Do not blindly use vendor Greeks as PIT truth. For the primary research panel:
- supply only rates and dividend inputs known at the trade timestamp;
- preserve the underlying timestamp and reject any underlying observation after the option trade;
- compare Black-Scholes and binomial Delta for American-style contracts;
- independently recompute a PIT Delta sensitivity;
- retain `iv_error` and reject materially unstable deep-ITM/OTM solutions under a predeclared rule.

Documentation:
- https://www.thetadata.net/docs/operations/option_history_trade_greeks_first_order.html
- https://www.thetadata.net/docs/Articles/Data-And-Requests/Option-Greeks.html

### Open interest

ThetaData documents that OPRA normally reports OI around 06:30 ET and that the reported amount represents the prior trading day's close. A new OI message may not be sent when a contract has zero OI. Therefore:
- timestamp OI at its actual report time, not at the prior close;
- preserve the prior-session economic reference date separately from KnowledgeDate;
- do not automatically convert a missing row to zero until complete retrieval and the vendor's zero-message semantics are verified.

Documentation:
- https://www.thetadata.net/docs/operations/option_history_open_interest.html

### Contract universe and historical identity

The option symbol-list endpoint returns all currently traded option underlyings and is updated overnight. The expiration-list endpoint returns expirations available for a supplied symbol, also updated overnight. Neither documented endpoint provides a historical as-of symbol master. Thus the advertised "100% market coverage" does not by itself prove that delisted underlyings can be queried or that historical contract roots and adjusted deliverables are retained.

The option history endpoints require a known underlying and expiration. A full F80 panel must not be built from today's symbol list alone.

Documentation:
- https://www.thetadata.net/docs/operations/option_list_symbols.html
- https://www.thetadata.net/docs/operations/option_list_expirations.html
- https://www.thetadata.net/docs/operations/option_list_dates.html

## Trade conditions and classification risks

ThetaData publishes trade- and quote-condition tables. The documented trade-condition codes include:
- 18: AUTO_EXECUTION (common in OPRA; execution mechanism, not investor identity);
- 35–38: SPREAD, STRADDLE, BUY_WRITE and COMBO;
- 40–44: cancellation variants;
- 53–54: CONTINGENT_ORDER and INTERNAL_CROSS.

These categories must not be blended into one directional-flow series. Keep outright trades and complex/contingent/cross trades as separate panels. Preserve all raw conditions. Date-aware condition-code mapping is required; do not assume today's table is historically invariant.

The historical trade_quote response schema exposes a trade condition and sequence but does not document the `records_back` field. The separate flat-file trade_quote schema does expose `records_back` for cancellations/insertions, but the public documentation says bulk flat files are available only for the most recent seven calendar days; longer historical flat files require contacting sales. This leaves historical cancellation/reversal reconstruction unresolved until a sample or written confirmation is obtained.

The quote-condition table distinguishes firm, locked, crossed, non-firm and halted states. The primary classifier should accept only valid two-sided, firm, non-locked, non-crossed, non-halted NBBOs and should enforce a maximum quote age. Preserve the raw quote condition and report rejected/unclassified volume.

Documentation:
- https://www.thetadata.net/docs/Articles/Errors-Exchanges-Conditions/Trade-Conditions.html
- https://www.thetadata.net/docs/Articles/Errors-Exchanges-Conditions/Quote-Conditions.html
- https://www.thetadata.net/docs/operations/option_flat_file_trade_quote.html

## Proposed signed-flow construction (not yet executed)

For each valid trade:
- buyer-initiated if trade price is at or above the valid ask;
- seller-initiated if trade price is at or below the valid bid;
- midpoint/inside-spread trades remain unknown in the primary series;
- quotes must be strictly prior to the trade (`exclusive=true`) and no older than a preregistered tolerance;
- trades outside the contemporaneous NBBO, with invalid/stale quotes, or with unresolved corrections are unclassified;
- outright and complex/contingent/cross trades are separate cohorts.

For trade (j), define (s_j=+1) for buyer-initiated, (-1) for seller-initiated, and missing otherwise. The signed delta-equivalent demand is:

[
SDD_{i,t} = \sum_j s_j \; size_j \; multiplier_{j,t} \; delta_{j,t}
]

The option multiplier/deliverable must be point-in-time and contract-specific; never apply 100 universally. Call and put contributions should also be reported separately. Primary normalization should use a lagged underlying ADV or another denominator known before the signal date, not same-day volume chosen after observing the flow.

This is signed aggressor-side demand, not net opening, net position change, institutional ownership, or proof of informed trading. The flow may reflect hedging, spreads, dealer inventory management or momentum chasing.

## Request and storage feasibility

The API's maximum multi-day interval is one month, but its own request-sizing guide recommends one week for tick-level options and one day for very liquid symbols. A 10-year full-universe reconstruction across 335 names would therefore require at least tens of thousands of symbol/date-window requests; a conservative one-week schedule is roughly 174,000 symbol-week requests before retries, with highly liquid names potentially requiring daily windows. This is a planning estimate, not a measured throughput or quote.

The historical flat-file endpoints documented for option trade_quote and EOD are limited to the latest seven calendar days. A true historical bulk backfill therefore needs either a high-volume API extraction or a separately quoted historical flat-file arrangement. The free sample bundle currently documents stock UTP/CTA trades/quotes only; it does not validate option endpoints.

## Acceptance gates before any economic test

1. Written business-use license and exact price for the required history; no personal plan for business use.
2. Sample with at least one liquid name, one thinly traded name, one adjusted/non-standard option, one historically delisted underlying, and one complex/cancelled-trade day.
3. Historical coverage by date for all 335 candidate names and the historical F80 membership, including delisted names and expirations.
4. Confirm that historical API output applies/corrects cancels and late reports; if not, obtain corrected flat files with revision lineage.
5. Verify OPRA NBBO coverage, quote-age distribution, firm/locked/crossed/halted rates, trade-condition distribution and unclassified-volume share.
6. Reconcile option multipliers/deliverables against PIT OCC reference data.
7. Verify actual delivery/publication timestamps or retain conservative next-session KnowledgeDate. Use next-session close execution for the end-of-day strategy.
8. Only then construct the signed-flow panel and test incremental information versus frozen LTM/F80.

## Relative priority

- **ThetaData:** high-priority conditional raw OPRA trade/quote reconstruction candidate; lower advertised individual price, but business license and historical bulk/correction semantics are unresolved.
- **OptionMetrics TradeFlow:** still the preferred vendor-labeled signed-flow benchmark because IvyDB documents permanent security IDs and delisted-security continuity; quote/sample/price still required.
- **ORATS:** preferred low-cost EOD context candidate for IV/OI/skew, but not an aggressor-side feed.
- **Cboe/MIAX Open-Close:** venue-specific opening/closing and participant-origin data; retain as complementary, not full-market substitutes.

No vendor was contacted, no credentials or data were acquired, no cost incurred, no forward returns calculated, and no alpha claim made. `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen.
