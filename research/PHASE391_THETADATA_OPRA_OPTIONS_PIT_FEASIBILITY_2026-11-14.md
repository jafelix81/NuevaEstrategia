# Phase 391 — ThetaData / OPRA options-flow feasibility and source ranking

**Audit date:** 2026-11-14 UTC  
**Disposition:** THETADATA PRO IS A STRONG CONDITIONAL RAW-OPRA RECONSTRUCTION CANDIDATE; OPTIONMETRICS SIGNED VOLUME/TRADEFLOW REMAINS THE PRIMARY SIGNED-FLOW CANDIDATE; NO OPTIONS SOURCE IS PIT- OR ALPHA-ADMITTED.  
**Scope:** Official documentation and public pricing review only. No account, API key, sample download, trial, vendor contact, purchase, return test, OOS, bootstrap, LOO, holdout or production change.

## Executive decision

The current ThetaData v3 documentation materially improves the options-source map. It documents tick-level options history from 2012-06-01 at Pro tier, trade-plus-NBBO reconstruction, historical open interest, implied volatility and trade Greeks. Its `trade_quote` endpoint supports a strict prior-quote match using `exclusive=true`; its open-interest convention explicitly describes a prior-trading-day value. This makes ThetaData a strong independent raw-OPRA reconstruction candidate.

This is not a PIT or coverage pass. The vendor's public coverage claim has not been measured against the frozen 335-name list, historical inactive/delisted underlyings, contract adjustments, or first-delivery/correction vintages. Retail pricing is expressly individual-use only; commercial use is separately licensed. No subscription or contact was initiated.

OptionMetrics' current IvyDB Signed Volume page confirms daily buyer-/seller-initiated volume, five- and 30-minute snapshots and EOD, with an advertised history for every option since January 2016. This remains the leading conditional signed-flow product. The public page does not establish a historical first-receipt ledger, correction vintages or whether the current "Signed Volume" label is exactly the same schema/version as the repository's previously audited "TradeFlow" four-table product. That product-identity/schema reconciliation remains mandatory.

## 1. ThetaData v3 — raw OPRA trade/NBBO and EOD/OI

### Historical access and coverage claims

The official subscriptions page lists options first-access dates by tier:

| Tier | First access date | Granularity | Relevant historical endpoints |
|---|---|---|---|
| FREE | 2023-06-01 | EOD, 1-day delayed | EOD only |
| VALUE | 2020-01-01 | 1-minute | EOD, quote, OI, OHLC |
| STANDARD | 2016-01-01 | Tick | Trade, quote, trade_quote, IV, first-order Greeks |
| PRO | 2012-06-01 | Tick | Standard endpoints plus higher-order and trade Greeks |

The page advertises 100% coverage for U.S. stock and index options. This is a vendor coverage claim, not a measured F80 or inactive-underlying coverage result. Pro lists eight concurrent requests; Standard lists four. The retail pricing page currently lists Options Pro at $160/month and states that the retail page is for individual personal use only, with no redistribution or business use. Commercial use is a separate route. Price is not a license determination.

### Trade/quote matching

The v3 `option/history/trade_quote` endpoint returns each OPRA-reported option trade paired with the last NBBO quote. For deeper history the quote match is timestamp-based with quote timestamp `<=` trade timestamp. The `exclusive=true` setting requests a quote timestamp strictly less than the trade timestamp. Multi-day requests are limited to one month and must specify an expiration.

**Research rule if a sample is later authorized:** set `exclusive=true`; retain both trade and quote timestamps; calculate quote age; quarantine stale, locked, crossed, zero-sided and otherwise invalid NBBO states; apply the vendor's trade-condition map; separately classify complex, auction, late, corrected/cancelled and other special-condition prints. Do not force every trade into buyer/seller categories. A trade at/above ask or at/below bid is an execution-side estimate, not an investor identity or beneficial-owner label. Midpoint/ambiguous trades remain unclassified or in a separate bucket.

The strict-prior-quote setting reduces same-timestamp quote lookahead, but does not by itself certify the quote's age, correction lineage, OPRA sequence integrity or first vendor receipt. Those must be tested from actual files.

### Open interest and EOD timing

ThetaData documents that option open interest is normally reported by OPRA around 06:30 ET and represents the end of the previous trading day. A new OI message may be absent when a contract has no open interest.

Implications:
- OI attached to a morning observation is prior-session OI, not same-day closing OI.
- Do not align the 06:30 report to the current day's end-of-day position.
- Do not interpret volume/OI as opening institutional demand without later OI confirmation and a precise report-date alignment.
- Missing OI messages must not silently become zero.

ThetaData's generated national options EOD report is created at 17:15 ET; its `created` field is the report-generation timestamp and `last_trade` is the last trade timestamp. `created` is not proof of the first time our process received the file. A prospective capture must persist the actual first-received timestamp and raw-file hash; historical EOD data without that receipt ledger remains retrospective backfill.

### Operational and identity gaps

- The Terminal must be running; the historical trade_quote request requires symbol and expiration, with multi-day windows limited to one month. Full-universe extraction therefore needs a deterministic symbol/expiration scheduler, request-budget measurement and completeness reconciliation.
- The documentation reviewed does not establish a full historical inactive/delisted-underlying roster, historical contract-deliverable adjustments, corporate-action lineage or record-known vintage for every mutable reference field.
- No actual response bytes were obtained. Schema, request sizing, rate limits under a full 335-name workload, error recovery, row counts and hash reproducibility remain untested.
- No first-receipt/correction/bust ledger has been demonstrated for historical files.

**Decision:** strong conditional independent raw-OPRA candidate; no PIT, universe, economic or alpha admission.

## 2. OptionMetrics IvyDB Signed Volume / TradeFlow reconciliation

The current official IvyDB Signed Volume page describes:
- daily detailed option volume;
- buyer-initiated/seller-initiated classification using trade price and the bid/ask quote at the time of trade;
- five-minute and 30-minute snapshots plus EOD;
- an advertised history for every option, every day since January 2016;
- linkage of symbols/security IDs to IvyDB US.

This is the best current candidate for a ready-made broad signed-volume panel. The repository's prior TradeFlow research (Phases 142/143/180/181) remains controlling: the product's participant labels are execution-style proxies, not verified beneficial-owner identities; the 2016 archive is retrospective backfill following the 2026-09-30 product launch; first-receipt, methodology-version, correction, sample, licensing and F80 coverage gates remain open.

**New reconciliation gate:** obtain the current data dictionary and prove whether "IvyDB Signed Volume" is the same product/schema/version as the repository's previously audited "TradeFlow" four-table structure or a renamed/expanded release. Do not join or merge fields based on product-name similarity.

**Decision:** retain as the primary conditional signed-flow candidate; no data or alpha admission.

## 3. Cboe Open-Close — complementary capacity/open-close source

The current Cboe DataShop page states that Open-Close covers Cboe exchanges BZX, C1, C2 and EDGX, with separate files per exchange. It classifies volume by participant type (Customer, Professional Customer, Broker-Dealer, Market Maker), buy/sell action and open/close position; Customer and Professional Customer are further divided by contract-size buckets. This is complementary to signed OPRA flow, not a consolidated all-OPRA feed.

Documented historical starts:
- C1 EOD: 2005-01-03; 10-minute: 2011-01-03; 1-minute: 2019-10-07.
- BZX, C2 and EDGX EOD: 2018-01-02; 10-minute and 1-minute: 2019-03-01.
- C1 GTH coverage: 2023-12-11.

EOD delivery is described as overnight after midnight ET. Exact first receipt must still be captured prospectively. The page documents historical convention breaks: C1 OI/previous OI shifted one day ahead through 2019-10-04; C2 through 2018-05-11; C2 Total Industry Volume doubled through 2018-05-11; C1 Total Exchange Volume used (B+S)/2 through 2019-10-04. These must be handled by venue/date-specific rules, not a single global formula.

Effective 2026-11-08, intraday snapshots reflect trade breaks/busts/cancellations in later snapshots and have schema/field/compression changes. Do not backdate a later corrected snapshot to the first interval receipt; keep pre/post-2026-11-08 schemas separate.

**Decision:** useful complementary capacity × side × open/close source on four Cboe venues; not all OPRA, not beneficial-owner identity, and not PIT-admitted.

## 4. Independent OPRA reconstruction candidates

- **Cboe Option Trades:** existing Phase 373 audit ranks this as an independent OPRA-wide raw trade/NBBO candidate with advertised history from January 2012. It has no documented participant capacity or open/close field; aggressor side must be inferred and trade conditions handled. Sample bytes and first-receipt/correction vintages remain unresolved.
- **Databento OPRA.PILLAR:** Databento announced historical/live OPRA in August 2023, covering consolidated trades and NBBO across U.S. options exchanges. Its timestamp conventions distinguish event and receive timestamps (`ts_event`, `ts_recv`), which are valuable for independent timestamp validation. The available OPRA history is much shorter than ThetaData's advertised 2012 start, so it is better suited to a recent overlapping validation sample than the primary long-history test.
- **Cboe PITCH/TBT:** retain the separate Phase 373/351/352 decisions. PITCH is depth/order-book microstructure; TBT is C1 execution-level detail. Neither is a substitute for broad all-OPRA coverage.

## 5. Updated conditional ranking

| Role | Candidate | Why | Binding unresolved gates |
|---|---|---|---|
| Primary signed-flow panel | OptionMetrics IvyDB Signed Volume / TradeFlow | Daily + 5m/30m, all-options history advertised from 2016, security-ID linkage | Product/schema identity, PIT/vintages, corrections, sample, F80 coverage, license |
| Independent raw-OPRA reconstruction | ThetaData Pro | Tick history from 2012-06-01; trade + NBBO; strict prior-quote option; T-1 OI convention | Actual sample, F80 and delisted coverage, contract adjustments, first receipt/corrections, commercial rights |
| Independent raw-OPRA validation | Cboe Option Trades | OPRA-wide trade/NBBO, advertised from 2012 | Sample bytes, first receipt/vintages, contract and inactive-underlying mapping |
| Complementary participant/open-close | Cboe Open-Close | Capacity × buy/sell × open/close on BZX/C1/C2/EDGX | Venue share, historical convention breaks, PIT delivery/corrections, license |
| Recent independent timestamp check | Databento OPRA.PILLAR | Consolidated trades/NBBO and receive/event timestamps | Shorter history from 2023, sample/access, universe overlap, license |
| EOD options panel alternative | HistoricalOptionData/DeltaNeutral; HistoricalData.net | Prior Phase 34 audit documents long history and T-1 OI claims | Sample/full archive, current schema, delisted coverage, PIT and license |

No ranking means "smart money." These products measure trade-side estimates, capacity categories, quotes, volume, OI or volatility; none identifies the beneficial owner or proves informed intent.

## 6. Pre-acquisition sample protocol

If a lawful sample/trial is later made available, the first task is a data audit only, not a return test:

1. Obtain exact license/business-use terms, historical product version, start dates, delivery schedule, correction/bust policy and archive-vintage guarantees in writing.
2. Select a stratified date set across quiet, crisis, high-volatility, earnings and 0DTE regimes; include both current and inactive/delisted underlyings where available. Preserve the fixed 335-name list as a diagnostic universe only; it is not a recovered PIT selection rule.
3. Measure median F80-name coverage >=90% and worst intended OOS date-bucket coverage >=80%, plus contract counts, valid quote rate, stale-quote rate, ambiguous/complex-condition rate, missing OI/IV and zero-calculation flags.
4. Verify contract identifiers, OSI/root, expiration, strike, right, multiplier/deliverable and corporate-action adjustments against an independent reference. No ticker-only historical join.
5. For ThetaData, compare raw trade_quote aggregates with an independent Cboe/Databento overlap on the same contracts and dates; report signed notional concordance, ambiguous volume, duplicate/sequence behavior and quote-age distributions.
6. For OptionMetrics, reconcile Signed Volume to the current TradeFlow product identity and validate the classifier on overlapping raw OPRA trades/NBBO; keep participant proxies separate from true investor identity.
7. Capture a prospective file-receipt ledger with immutable SHA-256, schema/version, file date, received timestamp, correction lineage and earliest tradable session.
8. Only after all gates pass, preregister one economic hypothesis versus frozen LTM/F80. Use identical dates, holdings/exposure, costs and execution assumptions; chronological OOS, dependence-aware bootstrap, LOO and no legacy holdout.

The Phase 34 acceptance thresholds remain in force. A sample that fails coverage or PIT is archived; the universe is not narrowed to make a provider pass.

## 7. Research authorization and next step

- No vendor account, key, trial, contact, purchase or paid sample was used.
- No options feature, forward return, alpha, OOS, bootstrap, LOO or holdout test was run.
- No new signal is admitted.
- `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen; no production, universe, capital, exposure or parameter change.

**Next technical step:** if a sample becomes available under suitable rights, run the pre-acquisition schema/coverage/PIT audit before any feature construction. Until then, continue free documentation work and preserve OptionMetrics as the signed-flow primary, ThetaData as the strongest raw-OPRA reconstruction candidate, and Cboe Open-Close as a complementary capacity/open-close source.

## Official sources reviewed 2026-11-14

- OptionMetrics IvyDB Signed Volume: https://optionmetrics.com/signed-volume/
- ThetaData subscriptions / first-access dates / endpoint entitlements: https://www.thetadata.net/docs/Articles/Getting-Started/Subscriptions.html
- ThetaData retail pricing and separate commercial-use route: https://www.thetadata.net/pricing
- ThetaData option trade_quote and strict prior-quote parameter: https://www.thetadata.net/docs/operations/option_history_trade_quote.html
- ThetaData option open-interest publication convention: https://www.thetadata.net/docs/operations/option_history_open_interest.html
- ThetaData generated EOD report timestamp: https://www.thetadata.net/docs/operations/option_history_eod.html
- Cboe Open-Close product, venue coverage, history and conventions: https://datashop.cboe.com/cboe-options-open-close-volume-summary
- Databento OPRA introduction: https://databento.com/blog/opra-data
- Databento timestamp conventions: https://databento.com/docs/conventions/common-fields-enums-types
- Existing repository reconciliation: PHASE34_OPTIONS_HISTORICAL_FEASIBILITY_AUDIT.md and Phase 373 report/PR #48.
