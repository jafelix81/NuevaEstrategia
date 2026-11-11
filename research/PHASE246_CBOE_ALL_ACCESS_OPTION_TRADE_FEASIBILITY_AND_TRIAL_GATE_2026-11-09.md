# Phase 246 — Cboe All Access API option time-and-sales feasibility and trial gate

**Audit date:** 2026-11-09  
**Status:** HIGH_PRIORITY_CONDITIONAL_HISTORICAL_TRADE_MEASUREMENT_CANDIDATE_NO_PIT_NO_ALPHA  
**Control:** F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen.  
**Scope:** Official Cboe DataShop and LiveVol API documentation audit only. No account signup, card authorization, API call, data download, vendor contact, purchase, return test or production change.

## Executive finding

Cboe's All Access API exposes historical option time-and-sales endpoints with a vendor-advertised history start in **2003**. The documented trade record can include option price and size, exchange ID, trade-condition ID, exchange sequence, vendor sequence, cancellation flag, timestamp, NBBO bid/ask and a price-relative-to-market classification (option_trade_at). A separate endpoint adds IV and Greeks.

This is a potentially important alternative to the project's ORATS Time & Sales candidate (advertised history from 2022-09-09) and Cboe C1 TBT (advertised archive from 2019-10-07, venue-specific). It may offer a much longer historical trade-measurement window and a **14-day evaluation trial**. It does not provide participant capacity, beneficial-owner identity or open/close classification. It is not yet established that trial access includes the historical OPRA price fields, that the historical tape is complete across all venues, or that any old backfill is point-in-time.

**Decision:** elevate Cboe All Access Time & Sales to a high-priority *sample-acquisition candidate*, not to a PIT-admitted source or alpha signal. Do not register, authorize a card, accept terms or make a purchase without explicit user authorization.

## 1. Official product and API facts

The Cboe DataShop product page documents:
- Free trial: 14 days, 500 points per day, $0 base price; card authorization is required for verification, and the page says the card will not be charged.
- Trial overage is unavailable.
- Paid Tier 3: 1,250,000 points per month at $2,499/month.
- Paid Tier 4: 4,000,000 points per month at $4,599/month.
- Historical option prices are listed as included with the subscription. Live or delayed option prices require an OPRA subscription.
- Trial subscriptions are not eligible for SIP data access. The product page also requires an internal-use selection and distinguishes individual from firm use.

The LiveVol API reference documents:
- Historical option-trade and option-trade-with-Greeks endpoints, with advertised historical availability from 2003.
- Historical request cost: 15 points.
- limit up to 10,000 rows per page; seq_no supports pagination.
- Trade fields include OSI security, root, expiry, strike, call/put, option trade price/size, exchange ID, condition ID, exchange sequence, vendor sequence, timestamp and cancel_flag.
- The enriched endpoint adds IV, delta, gamma, vega, theta, rho and dollar Greek fields.
- option_trade_at classifies the trade price relative to the options market as Below Bid, On Bid, Mid Market, On Ask, Above Ask, Crossed Market or No Market.
- The reference endpoint maps numeric exchange IDs to exchange name and security types.

The docs label the time filters as Eastern Standard Time. They do not establish whether historical timestamps and filters follow fixed EST or US Eastern daylight-saving transitions. This must be tested, not guessed.

## 2. Trial sampling capacity

At 15 points per historical request, a 500-point daily trial budget supports at most **33 full historical requests per day** (495 points), or **462 full requests over 14 days** if the full daily allowance is used. This is a request budget, not a guarantee of row volume or usable coverage. A busy ticker/date can require multiple pages, and each page consumes another request.

A 24-query initial stratified sample would use 360 points before pagination. Suggested strata:
- Four historical eras: 2003–2006, 2011–2014, 2018–2021 and 2024–2026.
- Liquid index/ETF, large-cap equity, mid-cap equity, lower-liquidity equity, inactive/delisted equity and adjusted-contract/corporate-action cases.
- At least one high-volatility and one ordinary session in each era where the trading calendar permits.

The sample must measure actual rows/page, pagination completeness, missing NBBO/Greeks, condition and exchange distributions, inactive-symbol retrieval and contract-identity exceptions. Do not infer full-universe coverage from a few successful tickers.

## 3. Measurement semantics and fail-closed handling

### Trade-price classification

option_trade_at is a price-relative-to-market classification, not a participant identity or a guaranteed aggressor flag. A conservative *proxy* mapping for measurement only is:
- Above Ask / On Ask: buy-side price pressure candidate.
- Below Bid / On Bid: sell-side price pressure candidate.
- Mid Market / Crossed Market / No Market: unknown or ambiguous; do not force a sign.

Validate the classification against the returned NBBO, quote freshness, crossed markets and trade conditions. Do not call this institutional flow or assume every ask-side print is opening demand.

### Cancellations and sequencing

The documented cancel_flag values are 0 (normal), 1 (canceled trade) and 2 (cancel-trade message). Preserve all raw rows and sequence fields. The initial volume feature must not count flags 1 or 2 as new trades. Reconcile cancellation messages to original prints using documented sequence/linkage rules; unmatched or ambiguous cancellations remain quarantined. Do not assume seq_no and exchange_seq_no have interchangeable scopes.

### Greeks, prices and contract identity

- Treat vendor Greeks as vendor-derived measurements; verify their timestamp alignment to the trade before using them.
- Do not assume dollar-Greek units, contract multiplier or adjusted deliverables from field names alone.
- Resolve OSI/root, adjusted contracts, corporate actions, ticker changes and delisted securities with an effective-dated contract/security master.
- Use independent point-in-time underlying prices for equity-return labels. Historical underlying bid/ask fields are separately SIP-dependent in the documentation.
- Do not use a later corrected trade/quote state to rewrite an earlier historical observation.

## 4. Point-in-time ruling

The advertised 2003 start is a **historical backfill claim**, not evidence that the same data were available to a subscriber in 2003. The documentation reviewed does not provide:
- per-file or per-row first-receipt timestamps;
- immutable historical correction/bust vintages;
- a complete historical venue-coverage manifest;
- a delisted/inactive-symbol retention guarantee;
- an independently verified live-product launch date or historical live/backfill parity.

Therefore historical API responses are not admitted to strict PIT backtests. A prospective capture, if later authorized, must retain request parameters, API/product version, UTC receipt timestamp, exact response bytes and SHA-256; every replacement/correction must be appended as a new vintage. Earliest strategy use is the next full regular session after actual receipt, not the historical trade date.

## 5. Relationship to existing candidates

| Source | Advertised historical start | Useful measurement | Main limitation |
|---|---:|---|---|
| Cboe All Access Time & Sales | 2003 | Trade price/size, exchange, condition, NBBO-relative price class, optional Greeks | Trial historical-field access and actual venue coverage unverified; no capacity/open-close |
| ORATS Time & Sales | 2022-09-09 | Inferred aggressor side, size, exchange/conditions, NBBO and minute-snapshot Greeks | Backfill not PIT; live/history enrichment mismatch; paid token and no free trial |
| Cboe TBT | 2019-10-07 archive claim | C1 execution-level side × open/close × capacity × trade type | C1 venue only; pre-launch history is backfill; expensive; no sample bytes |

These products may share OPRA-derived observations. Cross-vendor agreement is a measurement comparison, not independent raw-market confirmation. Cboe All Access must not be described as OPRA-wide until the sample's exchange distribution and written coverage scope establish that.

## 6. Preregistered research design — not yet authorized

If a lawful sample is obtained and the measurement/PIT gates pass, evaluate separately:
1. Trade-at signed premium/delta pressure by contract, expiry, moneyness and tenor.
2. Continuation versus reversal after large buy-/sell-side price-class imbalances.
3. Incremental value of flow after lagged underlying returns, option volume/OI, IV/skew, spread, liquidity, earnings and market-regime controls.
4. Whether results survive cancellation removal, condition exclusions, quote freshness, adjusted contracts and exchange stratification.

Test both underlying residual returns and option returns; do not assume one predicts the other. Option returns require executable entry/exit marks and realistic spread/slippage. Compare any stock-selection overlay with frozen LTM/F80 on identical eligible names, signal dates, exposure, turnover and costs; evaluate an options-only model separately rather than silently changing the equity baseline. Use chronological expanding/rolling validation, time-block/cluster bootstrap, issuer and contract/expiry LOO, multiplicity control and an untouched prospective confirmation. The consumed legacy holdout is not reused.

Kill the hypothesis if trade-at classifications fail NBBO reconstruction, effects disappear after prior-return/IV/liquidity controls, results are concentrated in a few venues or symbols, costs erase the effect, or the feature does not survive chronological OOS.

## 7. Admission gates and human dependency

| Gate | Result |
|---|---|
| Official product/API documentation | PASS |
| Advertised historical start and field schema identified | PASS — documentation only |
| Trial request budget estimated | PASS — 33 calls/day, 462 over 14 days at 15 points/call |
| Historical option-price access during trial | UNVERIFIED — product page says historical prices included but trial excludes SIP access |
| Representative raw sample and SHA-256 | NOT OBTAINED |
| Venue/OPRA coverage and historical completeness | NOT ESTABLISHED |
| First-receipt/correction vintages | NOT ESTABLISHED |
| Timezone/DST semantics | NOT ESTABLISHED |
| Delisted and adjusted-contract coverage | NOT ESTABLISHED |
| Licensing/internal-use terms for the intended research | NOT REVIEWED |
| Strict PIT / alpha admission | NO |

**Human action required to test the free route:** create/authorize the Cboe All Access 14-day trial. Cboe states that card authorization is required but that the trial will not be charged; the trial has no overage. No signup, card authorization, terms acceptance, API token or request was initiated in this phase. Historical option-price access within the trial must be verified before designing the sample around it.

No paid tier was selected. Tier 3 and Tier 4 prices are recorded only as current published reference points, not purchase recommendations.

## Sources

- Cboe All Access API product, trial, pricing and licensed-provider terms: https://datashop.cboe.com/cboe-all-access-api
- LiveVol option trades endpoint: https://api.livevol.com/v1/docs/Help/Api/GET-allaccess-time-and-sales-option-trades_symbol_root_expiry_strike_option_type_min_time_max_time_seq_no_exchange_id_condition_id_limit_min_size_max_size_min_price_max_price_date?apiGroupName=allaccess
- LiveVol option trades with Greeks endpoint: https://api.livevol.com/v1/docs/Help/Api/GET-allaccess-time-and-sales-option-trades-with-greeks_symbol_root_expiry_strike_option_type_min_time_max_time_seq_no_exchange_id_condition_id_limit_min_size_max_size_min_price_max_price_date?apiGroupName=allaccess
- LiveVol exchange reference: https://api.livevol.com/v1/docs/Help/Api?apiId=GET-allaccess-reference-exchanges
- ORATS Time & Sales documentation: https://orats.com/docs/time-and-sales-api
- Existing Cboe TBT feasibility: research/PHASE236_CBOE_TBT_EXECUTION_DETAIL_FEASIBILITY_AND_PIT_AUDIT_2026-11-09.md

## Controls

No API token, account signup, credit-card authorization, API request, raw data, vendor contact, data purchase, alpha/return test, bootstrap/LOO, OOS, holdout use, universe change or production change. F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen.
