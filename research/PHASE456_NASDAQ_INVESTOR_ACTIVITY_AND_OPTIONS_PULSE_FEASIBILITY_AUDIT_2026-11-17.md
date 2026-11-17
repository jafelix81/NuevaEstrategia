# Phase 456 — Nasdaq investor activity and options-pulse source feasibility audit

**Date:** 2026-11-17  
**Repository:** jafelix81/NuevaEstrategia  
**Main HEAD at preflight:** 20544866495c1f9c5d36cd117c1498637489d2e8

## Objective and scope

Screen additional Nasdaq Data Link products that were not present in the repository's prior source registry. The purpose is to identify data that could add information beyond frozen LTM/F80, while separating institutional/participant flow from retail crowding and opaque vendor sentiment. This is a data-feasibility audit only; no vendor data were purchased or queried.

## Operational preflight

- Latest overall run: [44087732566](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44087732566), Phase 455 PR CI, completed successfully. The audit job passed and uploaded aggregate-only artifact 14329718579 (1,567 bytes).
- Phase 454 PR CI: [44086525354](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44086525354), offline regression passed; live capture was skipped as designed on pull_request.
- Latest main scheduled SEC Form 144 run: [44083941814](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44083941814), offline regression passed but live capture failed on the pre-migration event-ledger schema mismatch. Phase 454 subsequently merged; the next scheduled main capture is the live migration/persistence validation gate.
- Explicit Actions queries returned zero in-progress and zero queued runs. No workflow was dispatched, rerun, or duplicated.
- Branch pagination returned 288 unique branches (100 + 100 + 88); 56 open PRs; 71 workflow files.
- The Phase 403 main workflow remains configured at minute :47 UTC. The next configured slot after this preflight is 2026-11-17 13:47 UTC. CFTC's next configured weekday slot is 22:25 UTC. Neither was due at the 13:24 UTC preflight.
- Main remains at 20544866495c1f9c5d36cd117c1498637489d2e8. No production code or scheduled workflow was changed in this phase.

## Source audit

### 1. Nasdaq US Retail Equities Flow — UREF/DF

**Documented feasibility**
- Daily ticker-level aggregation, history from January 2016, more than 10,000 U.S. stocks, ADRs and ETPs.
- Fields include trade date, point-in-time ticker, buy/sell share volume and buy/sell VWAP.
- Includes pre- and post-market transactions.
- Nasdaq states that the previous trading day's file is updated by 10:00 UTC Tuesday through Saturday.
- Securities priced below USD 1 are excluded. Nasdaq documents a small number of incomplete dates/tickers before 2021.
- Public sample is limited to seven named tickers on 2016-01-04; full access is Premium.

**Assessment**
- Medium-priority candidate as a *retail-flow/crowding control*, not a smart-money proxy.
- Plausible features include net retail notional, normalized buy/sell imbalance, flow breadth and changes in participation. Both continuation and contrarian signs must be tested; neither is assumed.
- The 335-name overlap, per-name history, missingness and historical coverage are not yet measured. The sample is not representative of the target universe.
- Historical trade date is not historical first-public-receipt time. Backfill can be used for coverage and feature-distribution warm-up only. A prospective receipt ledger is required before any tradable backtest.

### 2. Intraday US Retail Equities Flow — UREFINT

**Documented feasibility**
- 15-minute ticker-level aggregation, history from January 2016, more than 10,000 U.S. stocks, ADRs and ETPs.
- The product page states delivery within 30 minutes after each interval; historical tables are separated by year for 2016–2024, with a current table from 2025 onward.
- Securities below USD 1 are excluded and a small number of pre-2021 dates/tickers are incomplete.
- Documentation surfaces are not fully aligned: the dedicated UREFINT page and the combined Investor Activity Intelligence page expose different field lists (including differences around VWAP/market-volume versus update-time/health fields). Exact purchased-table metadata must be reconciled before feature design.

**Assessment**
- Conditional intraday comparator, lower priority than daily UREF/DF for the current end-of-day strategy.
- Use actual first receipt after interval completion; an interval label or vendor update timestamp is not by itself proof of availability.
- If acquired, preserve health flags and schema version. Do not silently substitute fields between documentation versions.

### 3. Nasdaq Options Pulse — NOSI / Investor Activity Intelligence

**Documented feasibility**
- Nasdaq describes symbol-, sector/industry- and market-level sentiment scores, updated on 10-minute intervals, with history from January 2019.
- The combined product documentation says the options sentiment is derived from customer and professional-customer opening-buy transactions across Nasdaq options exchanges. It is a proprietary sentiment score, not a raw OPRA trade tape.
- The documented symbol table exposes trade date, interval, underlying symbol, sentiment score and interval sentiment score. A separate ticker-change table maps symbol to FIGI with an effective start date.
- Product access is Premium. No public raw sample bytes, exact table-level first-receipt history, complete score construction or 335-name coverage were verified in this audit.

**Vendor-whitepaper evidence audit**
- Nasdaq's whitepaper reports 1,548 observations over January 2019–February 2025.
- Its Granger test reports p=0.7299 at one day (not significant), p=0.0001 at two days and p=0.0003 at three days.
- The VAR table shows a negative one-day and positive two-day Nasdaq put/call coefficient, consistent with a dynamic sign reversal rather than a single stable directional rule.
- The portfolio description says the ratio is compared with moving averages of 5/10/15/30/60 days, enters the next day and holds for x+1 days. The reported return table does not provide enough detail to reproduce the signal threshold, trade count, overlap treatment, turnover, costs, risk, multiple-testing correction or an untouched OOS holdout. The performance metric label is also insufficiently defined.
- These vendor results are a hypothesis generator, not independent evidence of alpha. They must not be imported as a prior or treated as proof of predictive ability.

**Assessment**
- Low-priority comparator only. Consider a market-level risk-regime feature or symbol-level incremental test only after sample access, exact score methodology, first-receipt logging and point-in-time FIGI mapping are verified.
- Do not call customer/professional-customer activity institutional or informed without separate evidence.

### 4. US Retail Flow and Holdings — USRFH

**Documented feasibility**
- History from January 2021. Nasdaq reported more than 460,000 U.S. retail investors as of May 2025, covering over 9,700 stocks, 8,600 options, 800 bonds and 35 cryptocurrencies.
- Includes user-level trades, holdings and demographics, plus security-level aggregates. Trade records expose execution and order-placement timestamps, anonymized user IDs, side, CUSIP/ISIN and anonymized data-source IDs.
- Trades are delivered daily around 19:00 Eastern; holdings around 09:00 Eastern Tuesday–Saturday. Holdings history before 2024-10-29 is monthly; after that it is daily T+1. The product reports variable lag.
- Volumes and prices are deliberately scaled/noised: volume is multiplied by a fixed factor plus mean-zero random noise; prices receive additional uniform noise. Absolute notional, price and small-sample trade-size inference are therefore not clean observed quantities.

**Assessment**
- Low-priority retail breadth/crowding candidate, not smart money.
- User counts, breadth and anonymized cohort persistence may be more robust than raw volume/VWAP, subject to sample representativeness, user churn and data-source stability.
- Monthly pre-2024-10-29 holdings are too coarse for daily positioning reconstruction. No first-receipt timestamps or partner-panel representativeness were verified.

### 5. Nasdaq Options Trade Outline — NOTO / PHOTO and related venues

**Documented feasibility**
- Nasdaq's Trade Outline suite covers six Nasdaq options venues through separate products: PHLX, GEMX, ISE, NOM, MRX and NTX.
- Product definitions describe electronic trades by option series, with aggregate trade quantity/volume by participant-origin category and opening buy, closing buy, opening sell and closing sell. Some product specifications also include open interest and industry volume.
- NOTO history is documented from November 2011; PHLX PHOTO historical data is documented from January 2009. EOD is next-business-day; intraday products are updated in 10-minute intervals.
- Coverage is venue-specific, not a consolidated all-OPRA market view. Electronic-only coverage excludes other trade types/venues.
- The products are proprietary and subject to internal-use/licensing restrictions. Published fee schedules include subscription and historical charges; those published distributor/internal-distribution amounts are not a verified quote for this account.

**Assessment**
- Highest-priority *conditional* Nasdaq options source in this audit because the open/close and participant-origin fields are more transparent than the proprietary NOSI sentiment score.
- Keep participant categories as exchange classifications, not identities. Customer, professional customer, firm and market-maker labels do not establish informed trading.
- Re-entry requires a lawful sample, full field dictionary, venue share/coverage audit versus OPRA, historical depth by underlying and series, actual delivery timestamps, and approved internal-use terms.

### 6. Free RTAT top-ten series

Nasdaq's free daily RTAT10 table is limited to the ten most active retail tickers, while the full-universe RTAT table is Premium. The top-ten table may be retained as a market-attention control only; it is not suitable for a 335-name cross-sectional signal because inclusion is activity-selected.

## Research hypotheses and controls

1. **Retail-flow continuation versus reversal:** test UREF net notional and normalized imbalance both ways, controlling for prior 1/5/20-session returns, volatility, liquidity, market beta, earnings/news and volume. Explicitly test whether apparent prediction is merely return-chasing.
2. **Opening options flow:** if NOTO/PHOTO data are lawfully available, test opening-buy minus opening-sell imbalance by participant-origin and call/put, normalized by series/underlying volume and open interest. Do not equate participant type with institutional identity.
3. **Options Pulse incrementality:** only after schema and PIT validation, test symbol/market sentiment as an incremental feature over frozen LTM/F80 and compare with simpler put/call baselines. Pre-register lags and signs; do not select them from the holdout.
4. **Retail breadth/crowding:** if USRFH is acquired, prioritize account breadth and concentration over perturbed absolute volume. Keep it separate from the smart-money hypothesis.
5. All tests must use the same exposure, costs, chronological train/validation/OOS boundaries, block bootstrap and leave-one-out discipline. Historical backfills without first-receipt vintages are not OOS evidence.

## PIT and licensing gates

- Store trade date, interval, actual first-receipt UTC timestamp, retrieval timestamp, source/table version, response metadata and content hash.
- Never use execution time, trade date, interval label or public release time as a substitute for when our system first received the data.
- Use PIT tickers/FIGI/CUSIP/ISIN with effective-dated joins. Unknown and missing must remain unknown, not zero.
- No raw proprietary files or derived redistributable outputs may be committed before the relevant license is confirmed.
- No vendor account, trial, purchase, API key, credentials or vendor contact was created or changed.

## Disposition

| Source | Status | Reason |
|---|---|---|
| NOTO/PHOTO Trade Outline | Conditional, highest-priority options candidate | Transparent opening/closing and participant-origin fields; venue coverage and license still gate |
| UREF/DF | Conditional, medium priority | Broad PIT retail flow; 335 coverage and first receipt unverified |
| UREFINT | Conditional, medium-low priority | Intraday retail flow; schema mismatch and first receipt need validation |
| NOSI / Options Pulse | Low-priority comparator | Opaque derived score; vendor whitepaper is not independent OOS evidence |
| USRFH | Low-priority crowding research | Retail-only panel; scaled/noisy size and monthly pre-2024-10-29 holdings |
| RTAT10 | Market-attention control only | Top-ten activity-selected sample, not full-universe coverage |

**No data were purchased, no API calls were made, no raw data were downloaded, no signal was admitted, and no return/alpha/OOS/bootstrap/LOO/holdout test was run.** The frozen baseline F80_TOP20_PARTIAL50_BASELINE_C20, universe, parameters, capital, exposure, holding rules, holdout and production remain unchanged.

## Official source references

- [UREF — US Retail Equities Flow](https://data.nasdaq.com/databases/UREF)
- [UREFINT — Intraday US Retail Equities Flow](https://data.nasdaq.com/databases/UREFINT)
- [NIFI — Investor Activity Intelligence / NOSI schema](https://data.nasdaq.com/databases/NIFI)
- [USRFH — US Retail Flow and Holdings](https://data.nasdaq.com/databases/USRFH)
- [Nasdaq Options Pulse product](https://www.nasdaq.com/products/data/options-pulse)
- [Nasdaq Options Pulse whitepaper](https://www.nasdaq.com/solutions/data/options-pulse/whitepaper)
- [Nasdaq Options Trade Outline suite](https://www.nasdaq.com/products/data/options/trade-outline)
- [NOTO product documentation](https://data.nasdaq.com/databases/NOTOI)
- [Nasdaq options price list 2025–2027](https://www.nasdaqtrader.com/content/ProductsServices/PriceList/Nasdaq_US_Options_Price_List_2025_2026_2027.pdf)
- [Cboe Open-Close licensing and delivery](https://datashop.cboe.com/cboe-options-open-close-volume-summary)
