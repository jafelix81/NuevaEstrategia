# Phase 502 — Cboe Option Quotes intraday-delivery and actionable PIT gate

**Date:** 2026-11-19 UTC  
**Branch:** phase501-cboe-opra-trades-quotes-pit-feasibility (supplement to PR #157 / Phase 501)  
**Baseline main at Phase 501 start:** 408a8fdfaeac81408760b90b2c0ecff2c34ae7b2  
**Disposition:** documented 15-minute-delayed intraday subscription path improves prospective feasibility; **not admitted** for alpha or production.

## 1. New finding: Option Quotes has a distinct intraday subscription delivery mode

The current Cboe Option Quotes product page states that:
- Option Quote Intervals are 1-minute or custom N-minute summaries across listed U.S. stock, ETF and index options disseminated over OPRA.
- Each snapshot includes NBBO, bid/ask size, interval OHLC and trade volume; optional Calcs provide IV and Greeks; optional open-interest is available.
- **Intraday files are delayed by 15 minutes after each snapshot is recorded.** Daily files are delivered overnight or early the following day.
- The page separately says real-time delivery requires contacting Cboe; do not confuse the documented 15-minute delayed intraday product with real-time delivery.

The v1.1 Option Quotes specification independently confirms a distinct **Subscription orders / Intraday delivery** file pattern, with timestamped HHMI filenames. quote_datetime is the end-of-interval timestamp in U.S. Eastern time. This is not merely an overnight file with an intraday timestamp.

Official references:
- Product page: https://datashop.cboe.com/option-quote-intervals
- v1.1 file specification: https://datashop.cboe.com/documents/Option_Quotes_Layout.pdf
- FAQ (delivery and field semantics): https://datashop.cboe.com/faqs

## 2. What the intraday file can and cannot measure

### Available interval fields
- NBBO bid/ask at the interval timestamp.
- Bid/ask sizes as defined by the specification (largest size from an options exchange participant at the NBB/NBO, not a complete depth-of-book reconstruction).
- Interval OHLC and total option-contract volume.
- Underlying bid/ask for equities and ETFs by default.
- Optional IV, Delta, Gamma, Theta, Vega and Rho.
- Optional OCC start-of-day open interest.

The FAQ says quote bid/ask is a snapshot at the timestamp; volume/OHLC reflect trades after the prior interval record up to the current timestamp. The file specification defines quote_datetime as the end of the interval.

### Explicit non-capabilities
- Option Quotes interval volume is **not trade-by-trade flow** and does not label buyer- versus seller-initiated contracts.
- Interval OHLC plus volume cannot be promoted to signed aggressor flow without additional trade-level data and a validated classification method.
- Bid/ask size is not full depth or a consolidated order book.
- OCC OI is previous-night EOD OI carried as start-of-day OI and held static during the session; it is not intraday-changing OI or same-day closing OI.
- A change between consecutive SOD OI snapshots is a change in outstanding contracts, not a direct measure of opening/closing direction or informed buying.
- The standard Option Trades subscription is daily file delivery. Cboe says intraday delivery of Option Trades requires contacting sales; no public delivery SLA or terms were established in this audit.

The companion Option Trades product/specification still provides OPRA-wide trade prints, execution exchange, trade condition, contemporaneous NBBO and optional trade IV/Greeks. Its file specification says RTH and GTH trades are included. Its canceled_trade_condition_id is legacy and always zero; corrections/bust/replacement treatment remains unresolved.

Official references:
- Option Trades product: https://datashop.cboe.com/option-trades
- Option Trades v1.3 specification: https://datashop.cboe.com/documents/Option_Trades_File_Specification.pdf

## 3. PIT interpretation: prospective path is feasible, historical strict PIT is not certified

The documented 15-minute delay gives a prospective delayed-data observation path, but it is not a substitute for a measured receipt ledger.

For every intraday file, a future collector must append:
1. quote_datetime (source interval end time, ET);
2. first local receipt UTC from SFTP polling;
3. remote path and filename including HHMI;
4. remote size/mtime where exposed;
5. local byte count and SHA-256;
6. retrieval attempt, successful receipt, parse status and revision/replacement lineage;
7. actual delay = receipt UTC minus interval-end UTC, with timezone conversion recorded.

**Actionable timestamp = actual first receipt**, not quote_datetime + 15 minutes. Never backdate a signal to the source interval timestamp. A feature can enter a simulation only after its actual receipt; execution uses the first executable underlying price after receipt, with realistic latency/slippage. Missing or late files remain missing/late; do not fill them with a nominal 15-minute assumption.

This supports a new *prospective* PIT study if a lawful subscription is obtained. It does not repair the lack of historical first-delivery vintages or certify historical strict PIT for 2012-present files.

## 4. Practical data-volume constraint

Cboe's current Option Quotes page estimates annual disk use for all symbols:
- 1-minute with Calcs: 2,300 GB compressed / 16,300 GB uncompressed;
- 15-minute with Calcs: 155 GB compressed / 1,100 GB uncompressed;
- 60-minute with Calcs: 40 GB compressed / 285 GB uncompressed.

These are full-market estimates, not estimates for the frozen 335-name universe. Do not extrapolate linearly: contract counts and listing activity vary materially by underlying and date. Obtain a vendor quote for the exact symbol panel and selected interval before committing.

A 15-minute interval is the preferred first feasibility quote for a swing-trading research design; 60-minute can be a lower-volume robustness/coverage alternative. One-minute full-market capture is not justified before a narrower pilot.

## 5. Revised two-track research design (conditional)

### Track A — Option Quotes intraday (15-minute delayed)
Candidate hypotheses, not assumed smart-money signals:
- abnormal call/put contract-volume imbalance by underlying, expiry and moneyness;
- IV/skew/term-structure changes relative to underlying return and realized volatility;
- delta-/vega-weighted *unsigned* activity proxies using interval volume and optional Greeks;
- volume divided by prior-night SOD OI, with liquidity/coverage filters;
- changes in SOD OI on the next available session, treated as a delayed stock variable rather than intraday flow.

Do not label any of these buyer-initiated or institutional. The primary question is whether they add information after controlling for underlying momentum, volatility, liquidity, earnings/event calendar and frozen LTM/F80 features.

### Track B — Option Trades (trade-level, standard daily delivery)
If daily files are licensed, classify prints against contemporaneous NBBO only when quote/condition data permit. Separate ambiguous, midpoint, locked/crossed, complex, auction, late, out-of-sequence and non-price-forming conditions. Use actual receipt time for the actionable clock. Intraday Option Trades is a separate vendor question and must not be assumed available merely because intraday Option Quotes exists.

### Combination
Only combine A and B after timestamp reconciliation. The quote stream may be available during the session with a 15-minute delay while standard trade-level files arrive overnight/next day. Features must retain their own observation/receipt clocks; do not assign a common timestamp to both.

## 6. Structural breaks and identity gates retained
- Quote-size methodology changes effective 2026-06-22; segment or normalize size-based features across the break.
- Zero IV/Greeks are missing/model-failure cases, not zero values.
- Zero underlying bid/ask is missing.
- Non-standard roots/adjusted contracts require deliverable and multiplier resolution.
- Effective-dated underlying/share-class identity is required, including delisted names.
- Confirm RTH/GTH coverage for Option Quotes specifically; do not infer it from a different Cboe product.
- Historical-start conflict remains: product pages say January 2012; FAQ table says January 2010. Continue to use January 2012 as the conservative common start pending written vendor confirmation.
- Per-symbol/date availability remains unverified; OPRA-wide product scope is not a completeness guarantee for every symbol/date.

## 7. Human/vendor gate before implementation
Obtain written confirmation of:
1. Price for 335-name Option Quotes at 15-minute and 60-minute intervals, with Calcs and OI;
2. Individual versus firm registration, research/business-use rights, retention and internal-use terms;
3. per-symbol/date availability including delisted underlyings and adjusted contracts;
4. actual intraday file schedule, expected and maximum delay, missed-file/recovery process and SFTP metadata;
5. correction, replacement, late trade and bust semantics for Option Trades;
6. whether Option Trades intraday delivery is available, its cadence/delay and price;
7. Option Quotes RTH/GTH coverage and any separate OPRA/SIP fees.

No vendor contact, purchase, sample download, credential request or paid commitment was made. No sample bytes are stored.

## 8. Decision and controls
- Promote Option Quotes from a generic daily quote companion to a **conditional prospective 15-minute-delayed intraday candidate**.
- Keep strict historical PIT status **not certified**.
- Do not call interval volume signed flow or smart money.
- No parser, collector, feature, backtest, event study, OOS, bootstrap, LOO or signal admission is authorized by this documentation phase.
- No changes to production or F80_TOP20_PARTIAL50_BASELINE_C20.
- Next step is a human-approved vendor quote/license decision and, if accepted, a small lawful 15-minute/60-minute sample plus a prospective receipt-time pilot before expanding to all 335 names.
