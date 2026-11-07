# Phase 114 — Cboe Open-Close EOD public sample and historical conventions audit

**Date:** 2026-11-05  
**Branch:** phase99-broad-pit-universe-charter  
**Scope:** public sample/schema audit and official specification reconciliation only. No forward returns, alpha test, purchase, subscription, authentication or vendor contact.

## Why this source moves ahead of the other options candidates

The current Cboe DataShop product page describes Open-Close Volume Summary as exchange-specific option volume categorized by participant capacity, buy/sell side and opening/closing position. It is available EOD and intraday, with separate files by exchange. The product page states that the EOD C1 history begins 2005-01-03; C1 10-minute history begins 2011-01-03; C1 1-minute history begins 2019-10-07; BZX/C2/EDGX EOD begins 2018-01-02. The C1 Global Trading Hours extension begins 2023-12-11.

This makes C1 EOD the most promising options-flow history found so far: it has much longer advertised coverage than C1 TBT (2019-10-07 onward) and exposes participant category × side × open/close at the option-series level. It remains a single-exchange view, not whole-OPRA coverage. Cboe's factsheet says approximately 98% of trading activity is included in the exchange-specific Open-Close files; this is not 98% of the entire U.S. options market.

## Official source documentation

- Product page: https://datashop.cboe.com/cboe-options-open-close-volume-summary
- Current EOD specification v1.3: https://datashop.cboe.com/documents/Open_Close_EOD_Spec_v1.3.pdf
- Legacy C1 EOD specification v2.7: https://datashop.cboe.com/documents/Legacy_C1_Open_Close_EOD_Spec_v2.7.pdf
- Factsheet: https://datashop.cboe.com/documents/Cboe_Open-Close_Factsheet.pdf
- FAQ/history table: https://datashop.cboe.com/faqs
- Related C1 TBT product: https://datashop.cboe.com/enhanced-us-options-trade-by-trade-execution-detail

The current EOD specification defines 86 fields from quote date, underlying, option series, prices, volume and open interest through participant buckets:
- Firm: opening/closing buy/sell quantities and volumes;
- Broker-dealer: opening/closing buy/sell quantities and volumes;
- Market maker: buy/sell quantities and volumes;
- Customer and Pro-Customer: opening/closing buy/sell quantities and volumes split into <100, 100–199, and >=200 contract buckets.

Origin mapping in the specification is: Firm = F/J/L; Broker-Dealer = B; Market Maker = M/N; Customer = C; Pro-Customer = U/W. These are clearing origin/capacity classifications, not beneficial-owner identities. A Customer bucket can include retail and institutions; Pro-Customer is an exchange/OCC category, not proof of a professional fund or informed trader.

## Critical historical convention breaks

Do not treat the entire advertised history as one homogeneous panel.

1. **Pre-2011 vs post-2011 schema and bucket meaning.** The C1 migration/format change starts 2011-01-02. Pre-2011 legacy fields include Customer and Firm only; customer size buckets are based on order size. Post-2011 adds Broker-Dealer and Pro-Customer and the size buckets are based on execution size. A long sample must either split at 2011 or use only a harmonized subset whose meaning is stable.
2. **C1 total exchange volume.** Through 2019-10-04, total_exchange_vol is calculated as (buy + sell)/2; from 2019-10-07 onward, it is buy + sell. Do not use this denominator unadjusted across the break.
3. **C1 open interest.** Open Interest / Previous Open Interest are shifted one day ahead from the start of history through 2019-10-04. Avoid these fields before 2019-10-07 unless the shift is corrected and independently verified.
4. **C1 previous close.** Through 2019-10-04, C1 previous close is the last trade on C1 only; current convention is industry-wide.
5. **C1 Global Trading Hours.** GTH coverage starts 2023-12-11. Pre/post comparisons must account for session coverage.
6. **Other exchanges.** C2 Total Industry Volume was doubled through 2018-05-11; BZX/EDGX conventions differ. Keep C1-only in the first study to avoid mixing venue methodologies.

The EOD specification says subscriptions normally provide preliminary and final files the next morning. The preliminary file uses OPRA values for Total Industry Volume and Open Interest; the final file uses OCC authoritative values. The final file should be the reference for historical analysis, with availability conservatively no earlier than the next regular session unless historical delivery timestamps are independently reconstructed.

## Preregistered public-sample audit

The live workflow downloads only the public Cboe sample and current/legacy public specifications. It recursively inspects nested ZIP/GZIP archives, hashes source files, validates the post-2011 86-field schema, parses dates/numeric values, measures underlying and series coverage, checks duplicate series keys and nonnegative quantities/volumes/prices, and compares the sum of participant buy/sell volume buckets against total_exchange_vol row by row. It does not assume the reconciliation must be exact; mismatches are retained and reported.

The sample can establish file/schema feasibility only. It cannot prove historical completeness, 2005 archive accessibility, symbol coverage of inactive/delisted securities, or license cost.

## Economic hypothesis candidates — not yet tested

If the history and broad PIT identity gates pass, candidate features may include:
- Pro-Customer opening buy-minus-sell and closing buy-minus-sell, normalized by a consistent denominator;
- Customer size-bucket opening imbalance, with execution-size semantics only post-2011;
- Firm and Broker-Dealer opening/closing imbalances, interpreted as capacity activity rather than institutional ownership;
- participant mix and the divergence between opening and closing pressure;
- put/call and delta-weighted aggregates only if the underlying option Greeks can be sourced with consistent historical conventions.

A positive customer/pro-customer imbalance is not automatically bullish. Option buyers can be hedging, spreads may be represented on multiple legs, and customer capacity does not identify the ultimate beneficial owner. Test whether the signal predicts subsequent underlying returns or merely follows contemporaneous returns/volatility. Compare incremental information against frozen LTM/F80 with identical exposure and costs, chronological OOS, bootstrap and issuer LOO.

## Gates before any return test

1. Public sample must parse with reproducible hashes and a stable schema.
2. Inspect all volume reconciliation exceptions; understand whether total exchange volume and participant-side bucket volumes count the same side population.
3. Verify actual historical archive accessibility at 2005-01-03 and 2011-01-02/03 boundaries, plus missing dates; the product-page claim is not proof that every date can be delivered.
4. Quantify underlying/series coverage, including delisted/inactive issuers, against the broad PIT universe.
5. Build two separate schema regimes (pre-2011 and post-2011) or preregister a post-2011-only sample. Do not silently bridge bucket meaning.
6. Use C1 only initially; apply 2019 volume/OI and 2023 GTH breaks explicitly.
7. Establish T+1 final-file availability, preliminary/final revisions and correction behavior.
8. Estimate license cost only after these free gates. No purchase or vendor contact without explicit user authorization.
9. Only after all gates, preregister a narrow feature set and compare with frozen LTM/F80.

## Initial decision

**Priority candidate, conditional on the public sample and history audit.** This source is materially more promising than OCC account-type volume and more historically complete than TBT, but it is still C1-only and uses capacity buckets rather than beneficial-owner identity. No alpha test is authorized. F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen.


## Hosted execution

The guarded live run downloads only the public sample and public specifications. It does not purchase data, authenticate, add anything to a cart, contact Cboe, or accept terms. The artifact will be inspected before a source decision is made.


## Final hosted result — run 42027724358

The public sample and both current/legacy EOD specifications downloaded successfully. The run passed all seven offline parser tests and uploaded artifact 13415230222.

- Public sample ZIP: 3,961,119 bytes; SHA-256 445cd9d658dc06028c286e09d4ac4818bd5884d7da8addd7509f3a0fa4840552.
- Nested C1 EOD sample: trade date 2025-03-28; filename identifies a 20% sample; 5,165,163 bytes; SHA-256 1c960e9a7b8b25311d2c8f012c36ea2c43087fe756335e57ffc952699a393ff6.
- Rows: 23,179; unique underlyings: 1,553; fields: 86.
- Security types: Equity 15,189; ETF 4,897; Index 3,093.
- Series types: Standard 23,080; Nonstandard 11; FLEX 88.
- Duplicate series keys: 0; invalid/negative numeric values: 0; blank numeric cells: 0.
- Participant buy-volume buckets: 2,253,420; sell-volume buckets: 2,253,420; total participant side volume: 4,506,840.
- Total C1 exchange volume: 4,506,840; Total Industry Volume: 12,228,281.
- Row-level participant bucket sum equals total_exchange_vol on all 23,179/23,179 rows (100%).

The sample archive also contains C1 1-minute and 10-minute sample packages, but Phase 114 intentionally parsed only the EOD file. Intraday files have separate schemas and upcoming 2026-11-08 changes; they are not part of this EOD approval.

**Decision:** PASS for public-sample schema, integrity and participant-bucket accounting. This is a material improvement over the TBT raw sample, whose side/open-close conventions remain partly unresolved. The result does not establish the actual 2005 archive boundary, complete daily availability, broad PIT security coverage, historical dissemination timestamps, or license cost. No alpha test, purchase, subscription, authentication or vendor contact occurred.

A same-date C1 TBT-vs-Open-Close sample consistency audit is documented separately in Phase 115.


**History-start discrepancy:** the legacy C1 specification describes its pre-migration format as covering 1990-01-02 through 2010-12-31, but the current DataShop product availability table advertises C1 EOD history only from 2005-01-03. Treat 2005-01-03 as the earliest advertised purchasable date; do not assume 1990–2004 files are available without a verified archive response.
