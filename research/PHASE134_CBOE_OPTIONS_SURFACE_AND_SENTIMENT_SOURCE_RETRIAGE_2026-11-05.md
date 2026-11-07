# Phase 134 — Cboe options surface, sentiment and delivery source re-triage

**Date:** 2026-11-05  
**Branch:** `phase99-broad-pit-universe-charter`  
**Status:** documentation/source-feasibility adjudication; no new market-data download, return test, vendor contact, purchase, authentication or production change.

## 1. Repository and execution gate

Reviewed the latest 25 of 756 GitHub Actions runs, current branch ref, PR #13, run jobs/logs/artifacts, the Phase 132–133 reports and the research-state file.

- Current branch head before this commit: `3b1b88b2a35d97288c981e7291d24d9e3d14ddc6`.
- Latest run: [Phase 133, 42097577204](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42097577204), completed successfully. Job 127491551422 passed compilation, seven offline tests, seven fixed-date requests and artifact upload. Artifact 13448395010 is present (2,852 bytes; ZIP SHA-256 `55abe7c48dd74bdcc9fdca6009deef6cb3e8fef5d157e94eb11cf91c08f0a318`).
- Phase 133 result remains **FAIL_FOR_LONG_OOS / RECENT_CROSSCHECK_ONLY**: four pre-2025 OCC Flex OI dates returned “File requested does not exist”; the recent files were not contract-parsed; no OI values or contract keys were validated; the report page says 24-month retention; first-publication timestamps remain unverified.
- Phase 129 run 42081987897 is cancelled at its 45-minute limit, not active; its 45-quarter live step produced no artifact. Do not rerun unchanged.
- No workflow is queued or running.
- PR [#13](https://github.com/jafelix81/NuevaEstrategia/pull/13) remains open, mergeable and unmerged.

## 2. New official-source finding: Cboe Volatility Surfaces is a current, long-history IV/skew product

The current [Volatility Surfaces product page](https://datashop.cboe.com/volatility-surfaces) advertises historical data from **August 2011** and daily EOD subscription files. It describes start-of-day 09:40 ET and end-of-day 15:45 ET / 16:00 ET snapshots; 16:15 ET is limited to indices trading through that time.

The April 2025 v1.0 [file specification](https://datashop.cboe.com/documents/VolatilitySurfacesSpecifications%20(1).pdf) defines four daily files:
- expiration-specific delta-relative;
- expiration-specific price-relative;
- constant-maturity delta-relative;
- constant-maturity price-relative.

The surfaces are interpolated from listed-option mid-volatility surfaces using Cboe Hanweck Volera. They include volatility points across 5–95 delta or 50%–150% of underlying price, strikes, calculation timestamps and weighted confidence fields. The specification explicitly warns that confidence below 0.5 should be treated with suspicion; negative confidence codes identify extrapolation/flat-lining conditions.

**Decision:** promote this to the leading *volatility-surface context* candidate. It is not participant flow, signed demand or proof of informed trading. The model-fitted surface is not interchangeable with raw NBBO or a vendor-independent IV calculation. Its sample-wide underlying coverage, inactive/delisted coverage, historical missing dates, exact file-delivery timestamps, revisions and price remain unverified. The public sample link was not machine-readable in this audit, so no sample schema or coverage claim is made.

A future, preregistered surface hypothesis may examine confidence-filtered downside/upside skew and constant-maturity term-structure changes. Candidate definitions must be frozen before seeing returns; for example, price-relative 90%-versus-110% IV and 30D-versus-90D ATM IV, subject to confirming that the relevant tenors and fields exist on each date. No such feature has been computed or tested.

## 3. Option Sentiment: unusually rich specification, but current orderability is not established

The [Option Sentiment v1.4 specification (May 2025)](https://datashop.cboe.com/Documents/Cboe_OptionSentiment_Specs.pdf) describes a daily/historical product with fields including:
- directional call/put volume and trade counts;
- call/put premium bought and sold, directional call/put volume and net option delta;
- call/put open interest, IV30, IV90, normalized 30-day 25-delta skew and implied borrow;
- customer, firm and market-maker volume;
- exchange volume, size buckets and days-to-expiration buckets.

The specification says its direction classifier is relative to midpoint: above midpoint is Buy and below midpoint is Sell; spreads, late and tied trades are excluded, and cancelled trades are backed out. It describes preliminary subscription files after market close and a complete file by the following morning. The current DataShop FAQ still lists an Option Sentiment history start of January 2012.

However, the former [product URL](https://datashop.cboe.com/option-sentiment) now redirects to the DataShop home page, and Option Sentiment is absent from the current Options product catalog pages. A surviving PDF and FAQ row do **not** establish that the product can currently be ordered, that its methodology is unchanged, or that historical files can be obtained.

**Decision:** retain as a high-information *dormant candidate*, not an available source. Re-entry requires a current orderable product page or written confirmation, a current sample, current specification/version, historical coverage and delivery/revision terms. No contact was made.

## 4. Re-adjudication of the currently listed Cboe products

| Product | Advertised history | Information | Current decision |
|---|---:|---|---|
| C1 Open-Close EOD | 2005-01-03 | Cboe venue capacity × buy/sell × open/close | Best participant/open-close candidate; historical PIT and full coverage still gated |
| Cboe Volatility Surfaces | Aug 2011 | Model-fitted IV/skew/term surfaces + confidence | Best new IV/skew context candidate; sample/coverage/PIT/cost pending |
| Option EOD Summary | Jan 2012 product page; FAQ also says Jan 2010 | OPRA series NBBO, volume, OI; optional 15:45 IV/Greeks | Complementary chain context; use Jan 2012 conservative floor |
| Option Trades | Jan 2012 | OPRA trade/size/exchange/NBBO; optional trade-time IV/Greeks | Daily context only until sample timestamp discrepancy is resolved |
| Option Sentiment | FAQ says Jan 2012 | Directional flow, IV/skew/OI and participant aggregates | Dormant: current product orderability not verified |
| OCC Flex OI | 24-month UI window | Intended series-level OI | Closed for long OOS by Phase 133 |

Sources:
- [Cboe Open-Close product/history/conventions](https://datashop.cboe.com/cboe-options-open-close-volume-summary)
- [Cboe Option EOD Summary](https://datashop.cboe.com/option-eod-summary)
- [Cboe Option Trades](https://datashop.cboe.com/option-trades)
- [Cboe DataShop FAQ](https://datashop.cboe.com/faqs)
- [Cboe Options catalog](https://datashop.cboe.com/options)

### Important distinctions

1. Open-Close is proprietary Cboe exchange activity, not full OPRA. C1 history begins 2005; BZX/C2/EDGX EOD begins 2018. Pre/post-2011 schema and bucket meanings differ; C1 volume/OI conventions change through 2019-10-04; GTH begins 2023-12-11. Keep C1 isolated for an initial study.
2. Option EOD Summary is the broader OPRA chain snapshot. Its existing public sample (Phase 55) contains only four underlyings (^SPX, SPY, TSLA, ^VIX), so it does not establish broad symbol coverage. The product page says January 2012 while the FAQ says January 2010; retain January 2012 as the conservative floor.
3. Option Trades is described as all OPRA prints with contemporaneous NBBO and optional trade-time IV/Greeks. Phase 112 found that its public sample uses a compact time-only `quote_datetime` inconsistent with the published full timestamp specification. Do not use its timestamp for intraday sequencing or signed-flow reconstruction until the discrepancy is resolved.
4. Open-Close capacity labels (Customer, Pro-Customer, Firm, Broker-Dealer, Market Maker) are clearing/exchange categories, not beneficial-owner identities. Customer includes retail and institutional activity; no category is assumed to be informed.

## 5. Point-in-time and licensing gate

The [DataShop FAQ](https://datashop.cboe.com/faqs) says daily equity/option subscription files are normally delivered the following day, typically 00:05–03:00 ET, but delays can cause delivery after the next market open. This is current operational guidance, not historical per-file delivery evidence. The Volatility Surfaces product page says daily EOD but does not publish its exact delivery clock. Option Sentiment's specification gives its own preliminary/complete schedule, but current orderability is unverified.

Therefore:
- Never use the trade date as the feature's KnowledgeDate.
- Do not infer historical first-publication timestamps from a current FAQ, a file's internal timestamp, or the date on a historical purchase.
- Until actual delivery logs or written product-specific timing are obtained, use a deliberately delayed availability sensitivity and do not claim strict historical PIT proof.
- Historical data purchases and raw-data/derived-data rights remain subject to Cboe licensing. The Open-Close product page says raw data is for internal use and external distribution of derived data requires additional licensing/approval.
- No vendor was contacted, no cart was used, no terms were accepted and no data were purchased.

## 6. Research priority after this re-triage

Keep separate hypotheses rather than creating a generic “smart money” score:

1. **Participant/open-close:** C1 Open-Close opening versus closing imbalance by capacity, call/put and trade-size bucket, weighted by valid option delta only after the OPRA context join is validated.
2. **Signed demand:** OptionMetrics IvyDB US + Signed Volume remains the leading external signed-flow candidate from the prior Phase 59 screen, conditional on a sample, exact PIT/identity fields, licensing and price. Cboe Option Trades remains a possible independent reconstruction route only after its timestamp/condition issue is resolved.
3. **Volatility surface:** confidence-filtered skew and term-structure changes from Volatility Surfaces; test whether they predict underlying residual returns or future volatility beyond prior price/realized-volatility behavior.
4. **Combined tests:** only after each component passes its own source, identity and PIT gate; compare each single source first, then a small preregistered interaction set.

All tests must use an effective-dated security/option-root crosswalk, include inactive/delisted names where available, distinguish prior price/volatility chasing from predictive behavior, compare incrementally with frozen LTM/F80 under identical exposure/costs, and use chronological OOS, block bootstrap and ticker/sector LOO. No forward-return or alpha test is authorized by this phase.

## 7. Frozen control

`F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen. No strategy, universe, feature, sizing, stop, holding-period or production setting was changed.
