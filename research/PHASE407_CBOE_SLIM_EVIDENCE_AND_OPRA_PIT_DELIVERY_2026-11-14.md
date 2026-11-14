# Phase 407 — Cboe SLIM evidence reconciliation and Option Trades PIT-delivery gate

**Audit date:** 2026-11-14 UTC  
**Disposition:** MATERIAL LITERATURE / MEASUREMENT CORRECTION; CBOE OPTION TRADES REMAINS CONDITIONAL; NO SIGNAL OR ALPHA ADMISSION.

## Executive decision

Phase 406's economic interpretation needs a correction. The 2025 paper by Amaya, Garcia-Ares, Pearson and Vasquez, *New Evidence on the Performance of Customer Options Trades* (April 7, 2025), challenges the simple inference that single-leg improvement-mechanism (SLIM) activity is uniformly unprofitable retail flow. It shows that conclusions are sensitive to (i) estimated versus actual trade direction, (ii) expiry value versus the last pre-expiry NBBO midpoint, and (iii) opening versus closing activity.

This is a methodological correction, not evidence of a predictive edge for the underlying stock. The paper's average net profitability estimates are positive but statistically insignificant. It does not show that SLIM flow predicts equity returns, and its Cboe "customer" capacity is not equivalent to retail or to a verified beneficial owner.

Cboe Option Trades remains a strong conditional all-OPRA reconstruction source, but its product page and FAQ disagree on historical start (January 2012 versus January 2010), daily files are T+1 with variable delivery, and first-receipt/correction vintages are not established. No sample bytes or official mapping workbook were inspected in this audit. Do not buy, contact the vendor, or run economic tests.

## 1. New evidence: direction and lifecycle measurement matter

Amaya et al. use Cboe trade records for single-name and ETF options on CBOE, EDGX, C2 and BATS from January 2020 through June 2023. These four exchanges represented more than 30% of single-name options volume across U.S. options exchanges in their sample. Their customer SLIM analysis focuses on CBOE and EDGX, the two venues offering the relevant single-leg improvement mechanism.

The Cboe-specific trade records contain:
- trading capacity of each counterparty;
- which party bought and which sold;
- execution channel;
- opening/closing status for non-market-maker capacities.

This is materially richer than consolidated OPRA Option Trades, which supplies prints, trade conditions and prevailing NBBO but not customer capacity or the actual buyer/seller side.

### Quantitative findings reported by the paper

| Finding | Result | Interpretation |
|---|---:|---|
| SLIM trades classified as closing | 42.4% | A large share is not new opening exposure |
| SLIM volume classified as closing | 42.6% | Treating every print as an opening position is untenable |
| SLIM volume classified as opening | 57.4% | Opening and closing must be separated |
| Cboe customer share of SLIM volume | >98% | "Customer" is the dominant exchange capacity, not proof of retail identity |
| BPS-style quote-rule trade-direction misclassification on Cboe SLIM | 42.4% of trades; 42.6% of volume | Quote-rule signs can be materially wrong in this subset |
| Net average daily lifecycle profitability, Jan 2020–Jun 2023 | +$0.34m/day; t=0.29 | Positive point estimate, statistically insignificant |
| Net average daily lifecycle profitability, Jan 2020–Jun 2021 | +$2.07m/day; t=1.19 | Positive point estimate, statistically insignificant |

The 2020–2021 window is close to, but does not fully match, the BPS November 2019–June 2021 sample; it starts in January 2020. The paper's full 2020–2023 result also remains statistically insignificant. Its net P&L calculation uses actual trade prices, but does not include commissions. Gross P&L uses NBBO midpoints and therefore does not reflect bid-ask execution costs.

The paper cannot match each closing trade to its specific opening trade. Its aggregate lifecycle accounting assumes positions opened in the SLIM channel are subsequently closed in that same channel. This assumption must remain visible; it is not a matched round-trip ledger.

### Why the prior "retail loses / dealer hedging" interpretation is too strong

The 2022 BPS evidence and the 2025 Amaya et al. evidence differ materially once trade direction, expiry marking and closing activity are handled differently. The 2025 paper reports that the BPS-style quote rule misclassifies 42.4% of Cboe SLIM trades and 42.6% of volume in its Cboe subset. Replacing estimated direction with actual buyer/seller direction and using intrinsic expiration values changes the held-to-expiration profitability estimate from negative to positive, but not statistically significantly.

The paper also notes that the public-customer capacity category includes hedge funds, mutual funds and other institutional investors. Therefore:
- SLAN / SLIM is an execution-mechanism proxy, not a beneficial-owner label.
- "Customer" is an exchange capacity category, not synonymous with retail.
- A positive aggregate options P&L estimate is not an equity-return forecasting signal.
- A positive flow/return association may still be inventory transfer, dealer hedging, temporary price pressure, or risk compensation rather than informed trading.

The paper is hosted by Cboe and acknowledges support from an Options Institute data research grant. Treat it as important evidence and a methodological challenge, not as settled independent consensus.

## 2. Consequences for our OPRA / Cboe source design

Keep three concepts separate:

1. **Trade direction:** buyer versus seller of the option contract. Consolidated OPRA Option Trades does not provide this directly; quote-rule aggressor signing is an estimate.
2. **Position direction and lifecycle:** opening versus closing, plus call/put and whether the position is being opened or reduced. Cboe TBT has an OPEN_CLOSE field for non-market-maker capacities, but Phase 351 found it blank on 17.86% of rows in its one-day sample.
3. **Participant capacity:** Customer, ProCustomer, Firm, BrokerDealer, MarketMaker. These are exchange classifications, not beneficial-owner identities or proof of information advantage.

Do not collapse these into one "smart money" feature.

### Conditional calibration path

Cboe TBT can potentially provide a venue-specific calibration/diagnostic subset for OPRA condition-based flow, because it contains actual side and capacity fields. But the existing Phase 351 public sample is only a 3% sample for one trade date (2025-03-28), C1 only, and its sampling rule is unverified. It cannot support population-level calibration or prevalence estimates. It also has:
- 17.86% blank OPEN_CLOSE;
- 0.45% incomplete option-series identity;
- 69 rows with unmapped SIDE values;
- a TRADING_SEGMENT/session inconsistency;
- no strict contemporaneous first-receipt ledger.

Any future deterministic cross-source match must first prove compatible row grain, timestamps/time zone, contract identity, exchange, trade price/size and correction semantics. A non-random 3% sample may be useful for schema/linkage diagnostics but not for population weights or a universal confusion matrix.

## 3. Cboe Option Trades historical-coverage discrepancy

Two official Cboe pages currently disagree:
- The Option Trades product page advertises history from **January 2012**.
- The DataShop FAQ's dataset-availability table lists **Option Trades from January 2010**.

Do not select the longer history by assumption. The effective start must be verified by an actual date/symbol availability audit or written product clarification before the historical-coverage gate passes.

Official product page: https://datashop.cboe.com/option-trades  
Official FAQ: https://datashop.cboe.com/faqs

## 4. T+1 delivery is not a guaranteed pre-open clock

Cboe's FAQ states:
- daily files for a trade date are delivered the following day through SFTP;
- uploads are typically between 00:05 and 03:00 U.S. Eastern time;
- delays can cause the previous day's file to arrive during the following day after the market opens;
- files remain on SFTP for 30 days after processing, then are removed;
- intraday delivery requires a separate discussion with Cboe.

Implications:
- Never assume a daily file is available before the next 09:30 ET open merely because typical delivery is overnight.
- If a file is first received after the next regular-session open, its first eligible use must be delayed to the next session after actual receipt; do not backdate.
- A prospective receipt ledger must archive raw bytes, hashes, filenames, source path, file date, receipt time, schema version and correction/replacement lineage.
- The 30-day SFTP retention means our own immutable archival process is mandatory.
- Intraday use is not supported by the published daily product terms and must not be assumed.

No account, subscription, vendor contact, price quote, sample purchase or data acquisition occurred.

## 5. Official mapping and sample-access status

The product page links the official LiveVol Trade Condition ID mapping workbook:
https://datashop.cboe.com/documents/livevol_trade_condition_ids.xlsx

The browser/runtime used in this audit rejected the XLSX binary content type, so workbook rows were not inspected. The public Option Trades sample endpoint is:
https://datashop.cboe.com/download/sample/216

The sample ZIP was also not retrievable by the current inspection tools (binary ZIP content type). This is an inspection limitation, not evidence that Cboe has withdrawn the sample. Do not implement the condition map from the academic/third-party mapping alone; reconcile it to the official workbook first.

Cboe Option Trades v1.3 specification:
https://datashop.cboe.com/documents/Option_Trades_File_Specification.pdf

## 6. Revised preregistration gates

Before any option-flow feature is constructed or any return window is opened:

1. Obtain the official condition workbook and reconcile every condition ID, including cancellations, late/out-of-sequence, auction, complex, stock-option and new OPRA message regimes.
2. Inspect actual Option Trades sample bytes; verify exact columns, row grain, sequence ordering, duplicate behavior, correction/bust replacement semantics and file completeness.
3. Resolve Jan-2010 versus Jan-2012 historical start and audit symbol/date availability for the frozen diagnostic universe, including inactive/delisted names and adjusted contracts.
4. Establish first receipt prospectively from SFTP; archive raw files immutably; measure delivery-time distribution and post-open delays.
5. Determine commercial/internal-use and derived-feature rights and pricing before acquisition.
6. Use Cboe TBT only as a venue-specific calibration/validation source after its 3% sampling rule, row grain, timezone, OPEN_CLOSE missingness and session mapping are resolved.
7. Preserve separate features for (a) estimated option buyer/seller side, (b) auction/condition class, (c) complex/package activity, (d) capacity where truly observed, and (e) opening/closing only where observed. Unknown/missing categories remain separate; no imputation.
8. Preregister price-pressure versus information hypotheses. Test contemporaneous/next-session price impact and decay separately from multi-day predictive returns. Control for underlying momentum, volatility, liquidity, earnings/events, option volume, spread and dealer-hedging proxies.
9. Compare incremental information against frozen LTM/F80 using identical exposure, costs and chronology. Require rolling/expanding OOS, clustered/Newey-West or block-bootstrap inference, LOO/concentration diagnostics and an untouched final holdout. Correct for multiple hypotheses.
10. Do not label a signal "institutional" or "smart money" unless participant identity is directly observed and validated; even then, test whether it predicts returns rather than merely describing who traded.

## Decision

**Retain Cboe Option Trades as a conditional all-OPRA reconstruction source, but revise the behavioral interpretation.** The 2025 evidence materially weakens any blanket claim that SLAN/SLIM customers are unprofitable retail traders. It also shows that quote-rule signing and ignoring closing trades can materially distort inference. None of this proves a predictive edge for the underlying equity.

No sample rows, raw data, forward returns, alpha, OOS, bootstrap, LOO or holdout were used in this phase. No signal is admitted. F80 and production remain frozen.

## References

- Amaya, D., Garcia-Ares, P., Pearson, N. D. & Vasquez, A. (2025-04-07), *New Evidence on the Performance of Customer Options Trades*: https://cdn.cboe.com/resources/education/research_publications/Retail_Profitability.pdf
- Cboe Option Trades product: https://datashop.cboe.com/option-trades
- Cboe DataShop FAQs: https://datashop.cboe.com/faqs
- Cboe Option Trades v1.3 specification: https://datashop.cboe.com/documents/Option_Trades_File_Specification.pdf
- Official LiveVol Trade Condition ID mapping: https://datashop.cboe.com/documents/livevol_trade_condition_ids.xlsx
- Bryzgalova, Pavlova & Sikorskaya, *Retail Trading in Options and the Rise of the Big Three Wholesalers*: https://www.aeaweb.org/conference/2023/program/paper/5N8FE6RZ
- Existing Cboe TBT sample audit: https://github.com/jafelix81/NuevaEstrategia/blob/phase351-cboe-tbt-public-sample-row-grain-audit/research/PHASE351_CBOE_TBT_PUBLIC_SAMPLE_ROW_GRAIN_AUDIT_2026-11-13.md
- Phase 406 source audit: https://github.com/jafelix81/NuevaEstrategia/blob/main/research/PHASE406_CBOE_OPTION_TRADES_OPRA_SCHEMA_AND_TRADE_CONDITION_AUDIT_2026-11-14.md
