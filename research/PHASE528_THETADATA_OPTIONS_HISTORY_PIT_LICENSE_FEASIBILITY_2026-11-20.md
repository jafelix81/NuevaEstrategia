# Phase 528 — ThetaData options history, access, PIT and license feasibility audit

**Audit date:** 2026-11-20 UTC  
**Main HEAD at preflight:** bb437a6956a28457b21a77e88e2820799b202b84 (Phase 527 merged)  
**Disposition:** **CONDITIONAL OPTIONS-FLOW / OPEN-INTEREST / IV CANDIDATE; NOT HISTORICAL-PIT, UNIVERSE-COVERAGE, LICENSE, COST OR ALPHA ADMITTED.** No purchase, sample acquisition, vendor contact, credential creation, collector, backtest or signal admission.

## 1. Why ThetaData was evaluated

Phase 527 found that the standard Cboe DataShop license expressly blocks using its data/methodology to create investment strategies or indicators unless a separate written and executed carve-out is obtained. ThetaData is a potentially different route because its published individual Subscriber Agreement expressly lists internal personal use, trading on the licensee's behalf, analysis and research as permitted uses.

That is not a complete legal clearance. The same agreement contains broad restrictions on copying/modifying/creating derivative works, prohibits disclosure to third parties, and requires data and derived works to be expunged within 30 days after termination. ThetaData's OPRA fee guidance also distinguishes display/internal use from non-display use such as algorithmic trading, risk systems and portfolio analytics. The proposed GitHub-based quantitative research workflow must therefore be classified in writing before any subscription or data acquisition.

**Research role:** potentially useful OPRA trade/quote, daily option EOD, open-interest and Greeks/IV data. It is not an investor-identity feed. No participant/customer/firm identity or true buyer/seller identity is supplied by the described history endpoints.

## 2. Current published subscription scope and price

ThetaData's current pricing page (checked 2026-11-20) advertises individual-personal-use tiers:

| Options tier | Monthly price | Advertised history | Concurrent requests | Relevant access |
|---|---:|---:|---:|---|
| Value | USD 40 | 6 years | 2 | 3 request types; 1-minute intervals |
| Standard | USD 80 | 10 years | 4 | 7 request types; tick-level data, option-chain snapshots, 15K trade streams, every OPRA NBBO quote |
| Pro | USD 160 | 14 years | 8 | 12 request types; tick-level data, option-root snapshots, every option trade, every OPRA NBBO quote |

The pricing page advertises 100% market coverage for U.S. index and stock symbols. This is a vendor claim, not a measured coverage result for our 335-name point-in-time universe. It does not establish coverage of inactive, acquired, renamed, delisted or historically non-optionable underlyings.

A separate **Commercial Use** path is shown on the pricing page. No commercial quote, OPRA classification or business-use price was obtained. Do not assume the individual prices apply to a firm, shared research environment, non-display system or automated strategy workflow.

## 3. Product/API feasibility

### 3.1 Option history EOD

The option_history_eod endpoint returns contract-level EOD information, including:
- underlying symbol, expiration, strike and call/put right;
- generated report time (created) and last trade time (last_trade);
- open/high/low/close, volume and trade count;
- closing NBBO bid/ask and sizes.

ThetaData states that it generates its national option EOD report at approximately **17:15 ET**. This provides a useful event/report clock, but not the subscriber's actual first receipt time. The API is symbol-specific and requires an expiration argument, with * available for all expirations. General request-sizing guidance recommends limiting EOD requests to one month.

### 3.2 Open interest

The option_history_open_interest endpoint returns contract-level open interest. ThetaData states:
- OPRA normally reports OI once daily at approximately **06:30 ET**;
- the reported OI represents the open interest at the end of the **previous trading day**;
- a message may be absent when a contract has no OI.

The OI timestamp/reporting convention must not be confused with the actual time the user can access the response. Use the first successful receipt/validation timestamp as the feature-availability clock. Do not attribute a same-day change to the wrong trading session.

### 3.3 Trade/quote history

The option_history_trade_quote endpoint returns OPRA trades paired with the last NBBO quote. The documentation says historical matching uses millisecond timestamps and a quote at or before the trade timestamp; the exclusive=true setting uses a quote strictly earlier than the trade timestamp. The endpoint's multi-day requests are limited to one month and must specify an expiration. General sizing guidance recommends **one week** for option tick-level requests and **one day** for highly liquid symbols such as AAPL/SPX/SPY, with responses kept below one million ticks where possible.

This permits a carefully filtered **aggressor-side estimate** by comparing trade price with the prevailing NBBO. It does not reveal the actual buyer/seller identity, beneficial owner, customer/firm category, opening/closing intent or whether a trade was part of a multi-leg package. Midpoint, locked/crossed, stale-quote, out-of-sequence, complex/auction and correction-condition records require explicit handling; ambiguous prints must not be forced into a buy/sell label.

### 3.4 Flat files

The current flat-file documentation says:
- flat files are available only to professional users;
- only the seven most recent calendar days are exposed through the documented self-service path;
- historical flat files beyond seven days require contacting sales;
- option trade/quote flat file is approximately 1.2 GB per day;
- option quote flat file is approximately 38 GB per day;
- option OI flat file is approximately 50 MB per day;
- option EOD flat file is approximately 150 MB per day;
- flat files do not include Greeks/IV, At-Time or Snapshot data.

Thus the self-service bulk route is not a historical 14-year backfill. A separate archive/bulk agreement would be needed for a market-wide historical flat-file panel.

## 4. Backfill scale and operational feasibility

The history endpoints are symbol-specific; the documentation explicitly says they have no market-wide wildcard for historical option trade/quote/EOD/OI. The current Pro tier permits eight concurrent requests account-wide; Standard permits four. Requests are not rate-limited in the documented API, but are queued; the default queue is 16 and an overgrown queue can return HTTP 429. The provider recommends a semaphore and small request intervals.

For a **lower-bound planning calculation**, 335 underlying symbols × 14 years × 12 one-month EOD/OI partitions is **56,280 symbol-month requests per endpoint**, before missing dates, retries, coverage checks or any additional contract/expiration partitions. This assumes that the * all-expiration parameter works over the full one-month interval for the selected endpoint; verify that behavior in an authorized sample.

For tick-level trade/quote history, the one-month request must specify an expiration, while one-week is the recommended sizing interval and liquid names may need one-day partitions. The actual request count can therefore be substantially higher than 56,280 and depends on historical expiration calendars, available strikes, liquidity and DTE scope. No credible total backfill time or cost can be stated without an authorized sample and provider limits/quote.

**Operational decision:** do not start a 335-symbol historical backfill from a retail subscription. First obtain a small authorized sample and a bulk-history quote or a written API throughput/retention plan. A narrow EOD/OI panel may be feasible; full OPRA trade/quote reconstruction is a materially larger project.

## 5. License, OPRA and data-retention gate

The current public ThetaData Subscriber Agreement states:
- the individual license is non-exclusive, non-sublicensable and non-transferable;
- the permitted use includes internal personal use, trading on the licensee's behalf, analysis and research;
- one individual may access the data;
- data may not be disclosed/released/distributed to third parties without prior written consent;
- Section 1(b) broadly prohibits copying, modifying or creating derivative works of the data and publishing/displaying compilations based on derived information;
- after termination, the agreement requires deletion/return of data, and states that derived works cannot be redistributed and must be expunged within 30 days.

The vendor's OPRA fee guide (2026-05-29) describes:
- professional display/internal use at an indicative USD 31.50 per user/month;
- non-professional display/internal use at an indicative USD 1.25 per user/month, paid by ThetaData in some cases;
- non-display systems at an indicative USD 2,000/month per category, with examples including algorithmic trading, risk systems and portfolio analytics.

These are vendor-published indicative descriptions, not a binding quote or independent legal determination. The exact classification of this project is unresolved: an individual researching and trading on their own behalf is different from a firm or client-facing system, but a GitHub Actions quant pipeline that programmatically consumes data may be classified as non-display. Do not assume the $160 individual Pro tier covers that use.

**Written answers required before purchase/sample/backfill:**
1. Does an individual subscriber's permitted research/trading use cover offline quantitative model development and historical backtesting in a private GitHub repository?
2. Does scheduled Python/GitHub Actions processing count as non-display OPRA usage? Which OPRA category and fee applies?
3. Are locally derived features, normalized scores, model parameters and backtest results permitted internal derivative works? Which may be retained after termination, and what must be expunged within 30 days?
4. Can raw data remain on private encrypted storage, and can the repository retain only hashes, schema metadata and non-reconstructive aggregate audit results?
5. What are the separate rights for professional historical flat files, internal model development and any later use of derived signals in the user's own trading?
6. What is the current commercial/individual price, any minimum term, OPRA fee, historical bulk fee and retention policy?

No vendor contact was made. No subscription, sample, credentials or purchase was requested. This audit is not legal advice and does not interpret the agreement as authorizing the proposed workflow.

## 6. PIT, revisions and universe coverage

- Contract/trade timestamps are event timestamps, not proof of first subscriber receipt.
- EOD report creation at 17:15 ET and OI publication around 06:30 ET are source/report conventions, not actual receipt timestamps.
- Historical archive availability, original delivery vintages and correction/replacement history have not been established.
- A prospective first-receipt ledger would be mandatory: request start/end, UTC receipt, endpoint, parameters, response headers, raw hash, byte count, schema version, parse status, corrections/revisions and first eligible execution session.
- Historical backfill without original delivery vintages is not strict historical PIT. Do not backdate features to the trade timestamp or nominal report time.
- The 335-name F80 universe, inactive/delisted underlyings, historical optionability, corporate-action-adjusted roots and symbol changes have not been measured.
- Effective-dated underlying/security identity is required. Unknown or ambiguous roots remain unmatched; never map by current ticker alone.

## 7. Candidate research hypotheses (not approved for testing)

If licensing, sample, historical coverage, identity and PIT gates pass, preregister a small set:

1. **Aggressor-estimated directional option demand:** classify only trades unambiguously above/below a valid pre-trade NBBO; aggregate premium- and delta-weighted call/put demand by underlying. Exclude ambiguous prints. Test whether it adds information beyond stock momentum, realized volatility, liquidity, earnings/events and frozen LTM/F80.
2. **Persistent demand plus subsequent OI:** compare signed flow on day T with OI for the same contracts when the previous-day OI report is actually received on T+1. Treat OI change as a noisy persistence proxy, not proof of opening trades or institutional accumulation.
3. **Volatility/skew state:** use quality-controlled EOD IV/Greeks to test forward realized volatility, downside tail risk and drawdown separately from directional returns.
4. **Return-chasing falsification:** control for same-day underlying return, realized volatility, earnings/event windows and option liquidity; test whether apparent flow only follows an already completed move.
5. **Independent/complementary validation:** if a candidate survives, compare against frozen LTM/F80 under identical universe, exposure, turnover and costs; use chronological discovery/validation/OOS, date-block bootstrap, issuer LOO, multiple-testing control and the untouched holdout.

No interpretation of large options volume as "smart money" is permitted. No trade-level participant identity or opening/closing flag is available in the described data.

## 8. Admission gates and final disposition

| Gate | Current result |
|---|---|
| Advertised history | 6 / 10 / 14 years by tier; exact per-symbol start not verified |
| Market coverage | Vendor claims 100%; F80 335-name and inactive coverage unmeasured |
| Historical bulk | Self-service flat files limited to seven recent days; archive needs sales agreement |
| API backfill | Symbol-specific; large request count; no pilot or quote |
| Event timestamps | Trade/quote timestamps and report timestamps documented |
| Actual first receipt / historical vintage | Not certified |
| Identity and delisted coverage | Not certified |
| Internal research rights | Agreement permits personal analysis/research, but derivative-work and retention clauses need written clarification |
| Non-display / OPRA classification | Unresolved; automated research may trigger non-display classification |
| Cost | Retail prices published; actual compliant price/fees unknown |
| Sample validation | Not performed |
| Predictive test / OOS / bootstrap / LOO | Not performed |
| Signals admitted | 0 |

**Retain ThetaData as a conditional options-flow/OI/IV candidate**, with a potentially more workable research-use path than Cboe DataShop's published standard license. Do not purchase or collect until the written-use, OPRA/non-display, derived-work retention, historical bulk, price and PIT questions are resolved.

F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen. No universe, parameter, exposure, cost, holdout, production or workflow changes were made.

## Official provider references

- [ThetaData current pricing](https://www.thetadata.net/pricing)
- [ThetaData Subscriber Agreement](https://www.thetadata.net/subscriber-agreement)
- [ThetaData OPRA fee guide (2026-05-29)](https://www.thetadata.net/articles/2026-05-29-opra-fee-guide-for-options-market-data)
- [Option history EOD schema](https://thetadata.net/docs/operations_python/option_history_eod.html)
- [Option history Open Interest schema](https://thetadata.net/docs/operations_python/option_history_open_interest.html)
- [Option history Trade Quote schema](https://thetadata.net/docs/operations_excel/option_history_trade_quote.html)
- [Request sizing](https://thetadata.net/docs/Articles/Data-And-Requests/Request-Sizing.html)
- [Concurrent request limits](https://thetadata.net/docs/Articles/Data-And-Requests/Concurrent-Requests.html)
- [Flat-file scope and sizes](https://thetadata.net/docs/Flat-Files/Getting-Started)
