# Phase 248 — Cboe Open-Close EOD directional feature contract and preregistration

**Audit date:** 2026-11-09  
**Status:** FEATURE_CONTRACT_PASS_SYNTHETIC_ONLY_NO_PIT_NO_ALPHA  
**Control:** F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen.  
**Scope:** measurement contract, sample evidence reuse, historical convention audit and preregistration. No historical archive was purchased or downloaded; no vendor was contacted; no returns or alpha were tested.

## Executive decision

Cboe C1 Open-Close EOD remains the strongest currently identified options-flow candidate in this project, but the raw fields support only **capacity-classified, volume-only directional proxies**. They do not provide option Greeks, participant identity, beneficial-owner identity or complex-order linkage.

Phase 248 converts the public 86-field schema into a fail-closed feature contract and pre-registers a narrow post-2019 study. Twenty-nine synthetic regression tests cover call/put signs, opening/closing separation, capacity buckets, aggregation, missingness, duplicate series and denominator handling. This does not apply the feature to the historical sample or establish alpha.

## 1. Verified public sample evidence

Phase 114 audited the Cboe public 20% C1 EOD sample for 2025-03-28:

- 23,179 option-series rows and 1,553 underlyings.
- 86 fields in the post-2011 format.
- Zero duplicate series keys and zero numeric errors in the audited sample.
- Participant buy/sell volume buckets reconciled exactly to total_exchange_vol on 23,179/23,179 rows.
- Sum of C1 total_exchange_vol: 4,506,840.
- Sum of total_industry_vol: 12,228,281.
- The ratio of those two reported totals is 36.8559%. This is a one-day sample ratio, not a validated market-share estimate; do not interpret it as full OPRA coverage.

The sample is a schema/accounting diagnostic, not a representative historical panel. The Phase 115 TBT comparison is not independent validation because Cboe states that TBT transactions are used to derive Open-Close summaries; the sample fractions also differ.

## 2. Exact field semantics

The current Cboe EOD specification v1.3 (2025-11-10) defines:

- vol = trade volume in contracts;
- qty = quantity of trades, not contract volume;
- Customer and Pro-Customer fields split buy/sell × open/close × execution-size buckets (<100, 100–199, >=200 contracts each);
- Firm and Broker-Dealer fields split buy/sell × open/close, without those size buckets;
- Market-Maker fields have buy/sell totals but no open/close fields.

The origin mapping is Firm F/J/L, Broker-Dealer B, Market Maker M/N, Customer C and Pro-Customer U/W. These are clearing origin/capacity classifications, not beneficial-owner identities. Customer can include retail and institutional activity. Pro-Customer is not proof of a fund, professional money manager or informed trader. The >=200 bucket is based on execution size, not investor identity.

The file has no delta, gamma, vega, implied-volatility, underlying-spot or complex-order linkage fields. Therefore:
- Do not call these features delta-weighted.
- Do not infer an institution from Pro-Customer or large-size buckets.
- Do not treat a series-level row as an independently identified trade.
- Complex spreads may contribute multiple legs; the EOD summary does not let us reliably link or net those legs by execution.

## 3. Preregistered feature definition

For each option-series row and capacity group, using contract volume fields:

**Calls**
- signed net = opening/closing buy volume − sell volume.

**Puts**
- signed net = sell volume − buy volume.

This sign convention makes call buying and put selling positive directional proxies, and call selling and put buying negative. It is an unweighted call/put contract proxy, not actual option delta.

For each capacity/action/size bucket, calculate:
1. signed net contracts;
2. signed net / total_exchange_vol;
3. signed net / total_industry_vol when that denominator is present and positive;
4. signed net / gross capacity volume when gross volume is positive.

At the underlying/date level, sum signed numerators and denominators across unique option-series keys, then calculate ratios. Never average series-level ratios. Normalize the source MM/DD/YYYY quote_date and reject invalid/pre-2019-10-07 dates, mixed dates, mixed underlyings, mixed security types, duplicate option-series keys, FLEX/unknown series types, missing volume fields, negative values, non-integer contract volumes and capacity volume exceeding the reported exchange total. A zero denominator yields an undefined ratio, not zero. Missing values remain UNKNOWN.

### Primary candidates

- Customer opening call and put imbalance, separately.
- Pro-Customer opening call and put imbalance, separately.
- Customer and Pro-Customer execution-size buckets (<100, 100–199, >=200) kept separate.
- Primary target: subsequent underlying equity returns, not option returns.

### Secondary controls

- Customer/Pro-Customer closing imbalances.
- Firm and Broker-Dealer opening/closing activity as capacity controls.
- Market-Maker buy/sell totals only as context; the EOD schema does not expose Market-Maker open/close.

No combined call/put feature is promoted as a delta estimate. The primary call and put components remain separate until a separately validated Greek source is available.

## 4. Historical sample regime

The product page advertises C1 EOD history from 2005-01-03, but actual daily archive completeness and inactive/delisted coverage remain unverified.

The first preregistered homogeneous panel is **2019-10-07 onward**, because:
- C1 total_exchange_vol changes convention through 2019-10-04;
- C1 open-interest fields are shifted one day ahead through 2019-10-04;
- post-2011 customer size buckets are based on execution size, unlike the pre-2011 order-size convention.

Additional regime controls:
- C1 Global Trading Hours coverage starts 2023-12-11.
- FLEX series type F was added 2024-10-16; exclude F from the primary panel and study it separately.
- Primary security type 1 (Equity); type 2 (ETF) is a separate cohort; type 3 (Index) and type 4 (WCO) are excluded from stock-selection tests.

Use final daily files only. The specification says preliminary files can use OPRA values for Total Industry Volume and Open Interest, while final files source those values from OCC. Preliminary and final files must never be mixed as if they were one vintage.

## 5. Point-in-time gate

The specification says subscriptions typically receive a preliminary and a final file the next morning, between 00:30 and 01:00 US EST. This is a delivery target, not a verified historical first-receipt log. Historical backfill cannot be treated as data known to investors on its trade date or on a presumed next-session timestamp.

Before any return test:
1. Obtain a lawful sample or trial only after required human authorization; no card, account, purchase or terms acceptance is implied.
2. Verify daily archive continuity, including inactive/delisted underlyings and adjusted/nonstandard series.
3. Establish final-file first-receipt timestamps, preliminary/final revisions and correction policy.
4. Prospectively capture original final bytes, SHA-256, exact UTC receipt time, source filename and revision lineage. The first scheduled capture is a baseline, not a new signal event.
5. Use the first full regular U.S. equity session after actual final-file receipt as the earliest signal boundary. Do not backdate to quote_date or assume a T+1 opening fill.

No such prospective capture is active on main. Strict PIT is NOT ADMITTED.

## 6. Economic test — only after data gates pass

Fixed-direction hypothesis: greater bullish Customer/Pro-Customer opening proxy predicts higher subsequent underlying residual returns after conditioning on price momentum, realized volatility, liquidity and market/sector exposure. This is a hypothesis, not a result; failure to add incremental information kills the feature.

Predeclared diagnostics:
- 5, 20, 63 and 126 trading sessions, reported together with multiplicity control;
- lagged 5/20/60/120-session returns, same-day underlying return, realized volatility, ADV, beta, sector, option activity and C1-to-industry volume ratio as controls;
- Customer and Pro-Customer kept separate; no post-hoc capacity pooling or sign reversal;
- same eligible securities, signal dates, exposure, turnover and realistic costs when comparing against frozen LTM/F80;
- chronological expanding/rolling OOS, date-block/issuer-cluster bootstrap, leave-one-underlying/sector-out diagnostics and a separate untouched prospective confirmation;
- gross/net return, drawdown, tail risk, turnover, missingness and capacity reported together.

Do not use the consumed holdout. No minimum or maximum holding period is imposed; the horizon family is diagnostic only. Option-return testing is deferred until executable option prices, Greeks and transaction costs are independently admitted.

## 7. Validation and disposition

- 29 deterministic synthetic tests pass locally.
- The helper computes a measurement contract only; no raw Cboe sample was reprocessed in Phase 248.
- Strict PIT, return testing and alpha admission remain false.
- No purchase, card authorization, vendor contact or terms acceptance occurred.
- No production, universe or capital change occurred.

**Decision:** retain C1 Open-Close EOD as a high-priority conditional options-flow candidate. Do not start a historical return test until archive completeness, actual final-file receipt, historical security identity and broad-universe coverage are established. F80 remains frozen.

## Sources and repository evidence

- Cboe, Open-Close EOD Specification v1.3: https://datashop.cboe.com/documents/Open_Close_EOD_Spec_v1.3.pdf
- Cboe Open-Close product page: https://datashop.cboe.com/cboe-options-open-close-volume-summary
- Cboe history/availability FAQ: https://datashop.cboe.com/faqs
- Phase 114 sample audit: research/PHASE114_CBOE_OPENCLOSE_EOD_SAMPLE_AUDIT_2026-11-05.md
- Phase 115 cross-sample audit: research/PHASE115_CBOE_TBT_OPENCLOSE_CROSS_SAMPLE_CONSISTENCY_2026-11-05.md
- Phase 248 feature helper: research/phase248_cboe_openclose_feature_contract.py
- Phase 248 synthetic tests: research/test_phase248_cboe_openclose_feature_contract.py
