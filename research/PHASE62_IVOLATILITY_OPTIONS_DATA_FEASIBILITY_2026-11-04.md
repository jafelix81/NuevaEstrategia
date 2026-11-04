# Phase 62 — IVolatility options data feasibility audit

Date: 2026-11-04  
Branch: phase62-ivolatility-options-data-feasibility  
Status: **HIGH-PRIORITY CONDITIONAL SOURCE — documentary feasibility only; sample, PIT vintage, universe coverage and commercial terms not yet passed.**

## 1. Executive finding

IVolatility may provide a more complete route to historical options context and signed trade-flow reconstruction than the current ORATS + OptionMetrics split:

- EOD option chains since January 2005, with bid/ask, OHLC, volume, OI, raw IV and Greeks.
- A 15:45 ET options snapshot.
- Non-standard options with corporate-action-adjusted deliverables.
- Stable option identifiers across splits, mergers and symbol changes.
- Corporate actions, listings/delistings and full symbol history.
- A separate US options trade-level product with trade price, size, exchange, condition, option NBBO and underlying quotes at trade time; legacy vendor guides document history from 2014.

The current institutional managed-database page confirms the EOD, non-standard, stable-ID, corporate-action, and trade-level field families. The detailed intraday guide is dated June 2020, so the exact current intraday history start, schema, delivery schedule and condition-code version must be reconfirmed in a current sample and contract.

Official sources:
- US options coverage: https://www.ivolatility.com/historical-options-data/us-index-equity-options/
- Managed database and data model: https://www.ivolatility.com/managed-db/
- Data Download product and retail pricing: https://www.ivolatility.com/data-download-intro/
- FAQ / usage classification: https://www.ivolatility.com/faq/
- Intraday trade data guide (last updated June 2020): https://www.ivolatility.com/doc/Intraday_options_trades_data_guide.pdf

## 2. Product inventory and history

| Product / table family | Documented content | History / timing | Status |
|---|---|---|---|
| Options Raw IV EOD | Bid/ask, OHLC, volume, OI, IV, Greeks | US history from Jan 2005 | Candidate |
| Options NBBO EOD | Contract prices, volume, OI | US history from Jan 2005 | Candidate |
| 15:45 ET snapshot | Option quotes and Greeks 15 minutes before close | US; exact first date not shown on current page | Candidate |
| Non-standard options | Adjusted contracts and deliverables | US; exact historical start to confirm | Critical candidate |
| Option identifiers | Stable ID per contract across corporate actions and symbol changes | US; exact effective-date semantics to confirm | Critical candidate |
| Corporate actions & splits | Splits, special dividends, listings/delistings, full symbol history | EOD; current page | Critical candidate |
| Option Trades | Every US options trade: price, size, exchange, condition, option NBBO and underlying quotes at trade time | Legacy guide: since 2014-03-13; current confirmation required | Highest-priority flow candidate |
| IV & Greeks per trade | Calculated using underlying price at trade time | Legacy guide; non-standard contracts lack IV/Greeks in that guide | Candidate |

The US equity-options product page states coverage of more than 5,500 US equity/ETF underlyings and major indices, with history from January 2005. The managed database page separately lists stable option identifiers, non-standard deliverables, corporate actions/splits including listings and delistings, and trade-level fields.

### Coverage wording conflict

The current FAQ describes options on both currently listed and delisted names. The Data Download landing page describes its coverage as currently listed names. The managed database page describes full symbol history including listings/delistings. Do not treat these statements as interchangeable: obtain written confirmation that the exact selected product and historical extract retain delisted underlyings, expired contracts, and predecessor identifiers for the requested dates.

## 3. Intraday trade fields and order-flow potential

The legacy intraday guide lists:

- Underlying symbol, exchange and company name.
- Trade date and trade time.
- Option trade price and trade size.
- Trade exchange and trade condition.
- Option symbol, expiry, strike, call/put and style.
- Option bid/ask prices, quote times, sizes and exchanges at the time of trade.
- Underlying bid/ask/trade prices and times at the time of the option trade.
- Price used for IV/Greeks, IV, Delta, Gamma, Theta, Vega and Rho.

The current managed-database page independently confirms that the Option Trades product contains every US options trade with trade price, size, exchange, condition, NBBO and underlying quotes at the time of the trade, plus a separate IV/Greeks-per-trade dataset.

This is materially richer than daily call/put volume and could support a reproducible aggressor-side estimate. It does **not** identify the beneficial owner or account category and must not be described as institutional or informed trading.

### Candidate signed-flow reconstruction

For each eligible single-leg trade, compare execution price with contemporaneous valid NBBO:

- Buyer-initiated: execution at/above ask within a predeclared tick tolerance.
- Seller-initiated: execution at/below bid within a predeclared tick tolerance.
- Inside-spread, midpoint, stale, locked/crossed, missing or otherwise ambiguous: retain as unknown; do not force a side.
- A tick-test or quote-rule fallback may be reported only as a separately preregistered sensitivity, never silently substituted for unknown trades.

Use quote timestamps and sizes to test quote freshness and whether the trade size was executable against displayed size. Preserve exchange and trade-condition codes. Trade-condition handling must be date-aware: the legacy guide documents code changes/effective dates around November 4, 2019.

### Complex trades and condition filters

The legacy guide distinguishes regular, late, out-of-sequence, opening/late-open, adjusted, spread, straddle, stopped, buy/write, combination, ISO, multi-leg auction/cross/floor and cancellation conditions.

Primary directional flow must exclude or separately bucket:
- Multi-leg, spread, straddle, combination and stock-option package trades.
- Late and out-of-sequence reports until their sequencing/correction treatment is verified.
- Cancellations and cancelled trades.
- Stopped/auction/cross/QCC-style conditions where aggressor side is not equivalent to a simple customer-initiated buy/sell.

Do not assume that a trade condition labelled “regular” is sufficient by itself; reconcile it with contemporaneous quote state. Preserve all raw rows and condition codes for audit.

## 4. Candidate DOOD reconstruction

IVolatility could independently reconstruct the economic mechanism in Phase 60 without buying OptionMetrics TradeFlow initially:

SignedDeltaDemand(s,t) = sum over eligible trades j of [Delta(j,t) × DeliverableFactor(j,t) × SignedContracts(j,t)]

Normalize by independently sourced underlying share volume or prior-available ADV. Do not assume a universal multiplier of 100. Use the stable option ID and PIT deliverable/corporate-action reference. For standard contracts, validate the conventional share factor; for adjusted/non-standard contracts, use the documented deliverable and a defensible equivalent-share conversion.

Important limitations:
- The 2020 intraday guide says non-standard contracts have trade information but no IV/Greeks. Keep them out of the primary delta-flow signal until a validated historical Greek/deliverable calculation exists; report them separately.
- Trade-level Delta is computed from a contemporaneous underlying price; verify the model, quote/trade selection, and whether the value is original/as-traded or subsequently recalculated.
- Underlying trade/quote data from the same vendor may be used for the flow calculation, but the return target and baseline execution prices must come from the existing independent stock-price source.
- Keep ambiguous signed volume as a separate feature/coverage metric.

## 5. PIT and revision risks

The legacy guide (June 2020) states:
- Non-scrubbed trade data were available around 4:50 p.m. ET each trading day.
- Trade data with calculated IV/Greeks were available after 5:00 p.m. ET.
- EOD auxiliary tables were updated in the mornings before the market opened.
- The provider performs after-close reviews and corrections; cancellation/out-of-sequence conditions are documented.

The current managed database page says daily updates include both new records and corrections to prior history. This creates a vintage risk: the latest corrected historical database may not equal what was first available to a strategy at the time.

Conservative rule until proven otherwise:
- KnowledgeDate = next trading session for all after-close trade data.
- Use next-session close execution for both F80 and augmented variants.
- For EOD OI, respect the one-day exchange publication lag; do not use same-day OI unless the vendor proves its exact timestamp.
- Require correction/vintage files or archived daily deliveries to establish what was known at each date. A current corrected backfill alone is not a PIT archive.
- Do not use the legacy 4:50/5:00 p.m. schedule as current proof until reconfirmed in writing.

## 6. Cost and licensing screen

Current Data Download retail pricing (personal/private-use tariff; professional usage is separately classified):
- $0.40 per ticker per day for option prices/NBBO and historical volatility.
- $0.60 per ticker per day for Raw IV, IV Surface by Moneyness and IV Index.
- No subscription or minimum for the Data Download tool; maximum single order 10 GB.
- Sample files are advertised for NBBO and Raw IV, but the web tool could not inspect the CSV downloads because they are served as application/octet-stream.

Indicative EOD cost for 335 symbols and 252 sessions:
- NBBO at $0.40: 335 x 252 x $0.40 = $33,768 per year.
- Raw IV at $0.60: 335 x 252 x $0.60 = $50,652 per year.
- Five years: $168,840 NBBO or $253,260 Raw IV, before any custom/institutional quote or discount.

These retail calculations are not a quote for professional research, managed DB, non-standard options, 15:45 snapshots or intraday trades. The managed DB is explicitly for institutional clients; professional usage requires a tailored license. No purchase is authorized.

The cost screen makes a targeted sample more sensible than an immediate full-universe purchase. A 20-symbol x 20-session sample would represent 400 ticker-days, or an indicative $160 NBBO / $240 Raw IV at the published retail rates, if those datasets and symbols are eligible under the user's license. This is only an arithmetic illustration, not a purchase recommendation or authorization.

## 7. Comparison with current candidates

| Source | Strength | Main gap | Current role |
|---|---|---|---|
| ORATS Near-EOD | Low-cost historical option context from 2007; broad one-date sample passed schema | No signed flow; no multiplier/deliverable in sample; PIT publication and delisted retention not proven | Context candidate |
| OptionMetrics TradeFlow | Direct signed buyer/seller volume, 2016+ | Vendor category/classification semantics and contract coverage need sample validation | Directional-flow candidate |
| IVolatility EOD + Option Trades | EOD context, stable IDs, corporate actions, adjusted deliverables, trade-level execution and contemporaneous NBBO | Intraday guide is old; exact current coverage, vintage, licensing and quote still required | **Highest-priority alternative / possible consolidated stack** |
| Cboe Open-Close | Venue-specific opening/closing and participant-origin dimensions | Cboe-only venue, historical cost and coverage | Complementary venue evidence |
| MIAX Open-Close | Venue-specific origin, side and open/close | Expensive; limited venue share and history | Later replication |

IVolatility and OptionMetrics may both ultimately rely on the same consolidated US options market feeds. Treat them as independent vendor pipelines/methodologies, not independent economic sources, unless provenance demonstrates otherwise.

## 8. Required vendor sample / written answers

Before purchase, request:
1. A current schema and data dictionary for EOD NBBO, Raw IV, 15:45 snapshot, non-standard options, stable option IDs, corporate actions, and Option Trades.
2. Sample dates spanning 2014, 2018, 2020, 2022, 2024 and 2026.
3. Representative F80 candidates across mega/large/mid/small cap, ETFs, delisted issuers and predecessor/successor symbols.
4. Explicit proof of expired-contract and delisted-underlying retention for each requested product.
5. Exact start dates and symbol/contract coverage by year.
6. Trade-condition codebook and historical version/effective-date mapping, including cancellations, corrections, late/out-of-sequence, complex orders, auctions, ISO and stock-option packages.
7. Quote timestamp precision, quote staleness, NBBO source/coverage, exchange coverage, locked/crossed quote treatment and trade-condition correction handling.
8. Stable contract-ID continuity, OCC/OPRA symbology crosswalk, deliverable quantities, cash components, multiplier/position multiplier and effective dates.
9. Historical delivery timestamps and, critically, archived daily vintages or a correction log sufficient to reconstruct what was available at each date.
10. Current price and license quote for a small sample, a 335-symbol subset, and professional/commercial research use; distinguish EOD from intraday trade-level products.

## 9. Decision

**CONDITIONAL — advance to sample/quote gate, not economic testing.**

IVolatility is now a higher-priority data candidate than purchasing the full ORATS archive or OptionMetrics TradeFlow immediately, because its documented product families may provide both market context and raw trade-level inputs for signed-flow reconstruction, plus stable IDs and corporate-action references.

Do not infer alpha from product richness. No vendor data have been acquired; no forward returns have been calculated; no purchase or vendor contact has been authorized; no source has passed PIT vintage or historical F80 coverage. Phase 60's DOOD preregistration remains unchanged. F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen.
