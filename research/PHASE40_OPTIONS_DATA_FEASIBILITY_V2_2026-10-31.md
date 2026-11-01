# Phase 40 — Historical options data feasibility V2 — 2026-10-31

## Status
**DATA FEASIBILITY STRENGTHENED; PURCHASE/COVERAGE GATE STILL OPEN. No alpha authorized.**

## Fresh official-source verification
Cboe DataShop's current FAQ states historical availability beginning:
- Open-Close Volume Summary EOD C1: January 2005.
- Option Quotes: January 2010 in the FAQ.
- Option EOD Summary: January 2010.
- Option Trades: January 2010 in the FAQ.
- Option Sentiment: January 2012.

Current product pages are more conservative for some products: the current Option Trades and Option Quotes pages advertise historical data from January 2012 onward. For research reproducibility, the product-specific purchase page and actual delivered files must govern the final usable start date, not the FAQ alone.

Option Quotes currently supports 1-minute/custom intervals with NBBO, OHLC, volume, optional open interest, and optional implied volatility/Greeks. Daily files are delivered overnight/early morning; intraday files are delayed 15 minutes after the snapshot. This gives a defensible ex-ante timestamp for daily and interval studies, subject to the exact subscription/purchase terms used.

Option Trades currently provides trade-by-trade records across the OPRA universe, including trade price/size, exchange, prevailing NBBO, and optional point-in-time IV/Greeks. The current product page advertises historical availability from January 2012.

Cboe's Option Sentiment specification describes daily historical order-flow analytics, including call/put volume, trade counts, average trade size, premiums, and open-interest-supported concentration analysis. It states that complete subscription files are delivered the following morning, generally by 5–6 a.m. ET. The dataset should be treated as a candidate analytical product until current purchase availability and field-level coverage are verified.

## New priority finding — Open-Close is the strongest first options audit candidate
Fresh review of the current Cboe Open-Close product page shows a materially better fit to the Smart Money hypothesis than raw Option Trades/Quotes for the first audit. The EOD product explicitly classifies option volume by participant capacity (Customer, Pro-Customer, Broker-Dealer, Market Maker), buy/sell action, and open/close position; Customer and Pro-Customer activity is additionally bucketed by contract size. It includes OHLC, total volume and open interest in the EOD files.

Historical coverage is unusually strong for this purpose:
- C1 EOD: 2005-01-03 onward.
- C1 10-minute: 2011-01-03 onward.
- C1 1-minute: 2019-10-07 onward.
- BZX/C2/EDGX EOD: 2018-01-02 onward.
- BZX/C2/EDGX 10-minute and 1-minute: 2019-03-01 onward.

This is preferable to treating generic call/put volume as a Smart Money proxy because the participant and open/close dimensions are explicit. The 2005–2010 C1 history also materially extends the potential research sample.

Important historical convention: C1 open-interest/previous-open-interest fields are shifted one day ahead through 2019-10-04, and C2 through 2018-05-11. Any historical test must correct for these documented conventions before constructing PIT features. Total-industry-volume and total-exchange-volume conventions also changed historically and must be normalized before cross-period comparisons.

## Revised hypotheses
H1: abnormal directional options activity by non-market-maker capacities contains incremental information beyond frozen LTM/F80.
H2: flow combined with prior-night/opening open interest is more informative than raw volume alone.
H3: IV/skew changes add information conditional on underlying momentum, volatility and liquidity.
H4: any apparent predictive power must survive controls for prior returns, underlying volume, volatility, and explicit return-chasing tests.
H5: the incremental information, if any, is stronger when open/close and participant-capacity dimensions identify new directional positioning by Customer/Pro-Customer accounts rather than aggregate option volume.

## Critical PIT rule
Open interest that is only known after the close must not be used for a same-close decision. For daily signals, use the latest OI demonstrably available before the decision timestamp (e.g. prior-night/start-of-day OI when the product provides it). For end-of-day sentiment files delivered the next morning, the earliest permitted trading decision is the next session unless a historical delivery timestamp proves earlier availability.

For historical Open-Close data, the documented C1/C2 OI shifts must be corrected using the vendor's historical conventions before any feature is treated as PIT. No feature may use a field whose information timestamp is later than the simulated decision timestamp.

## Required remaining gates
1. Obtain a reproducible historical sample from Cboe or another documented source; **Open-Close EOD is now the preferred first purchase/coverage audit.**
2. Measure coverage on the frozen 335-name universe across multiple historical windows, including delisted/name-change cases where available.
3. Record exact product, purchase date, delivery timestamp, and missing-symbol/date behavior.
4. Freeze field definitions before testing, including participant capacity, buy/sell, open/close and open-interest interpretation.
5. Correct all documented historical convention breaks before cross-period feature construction.
6. Build only features that would have been available at the intended decision time.

## Decision
The source family is now technically credible enough to justify a concrete data-purchase/coverage audit. **Cboe Open-Close EOD is the preferred first candidate** because it combines long history with explicit participant capacity and open/close classification. This does not constitute evidence of predictive alpha. No alpha testing is authorized until actual delivered historical files pass universe coverage and PIT audits.

No change to `F80_TOP20_PARTIAL50_BASELINE_C20`.

## 2026-10-31 execution note
The latest Phase 35/13D-13G audit run is `41273580859` (run #58) and is still `in_progress`; job `124751137006` remains on the corrected historical-CIK PIT audit step. No duplicate execution was launched. No artifact exists yet. The active job's log endpoint is unavailable through the current GitHub connector response, so no internal progress should be inferred from missing logs.

The immediately preceding Phase 22C/13F mapping audit run `41273580840` (run #70) completed successfully. Its production decision remains unchanged: insufficient historical coverage for the frozen universe, so no alpha test is authorized.

## 2026-11-01 execution note
Fresh official-source verification confirms the current Cboe DataShop FAQ still lists Open-Close EOD C1 from January 2005, while current product pages describe the Open-Close product as capacity/side/transaction-type volume data on Cboe exchanges. Cboe's 2025 rule filing explicitly states that EOD Open-Close is proprietary exchange data and does not include other exchanges; therefore exchange coverage must be treated as a first-class audit variable rather than assuming OPRA-wide coverage. The current FINRA catalog also confirms that Reg SHO Daily Short Sale Volume, Blocks Summary, OTC Block Summary and other off-exchange datasets are available as distinct products; FINRA explicitly warns that short-sale volume is not equivalent to short interest. These facts reinforce the research priority: use participant-classified options only if delivered historical files cover the frozen universe adequately, and keep FINRA short-flow and short-interest as separate signals rather than conflating them.

Fresh official references:
- Cboe DataShop FAQ: https://datashop.cboe.com/faqs
- Cboe Data Products: https://datashop.cboe.com/data-products
- Cboe Open-Close rule filing: https://cdn.cboe.com/resources/regulation/rule_filings/approved/2025/SR-CboeEDGX-2025-047.pdf
- FINRA dataset catalog: https://developer.finra.org/catalog
- FINRA short-interest explanation: https://syndication.finra.org/content/short-interest-what-it-what-it-not

Current Actions state checked 2026-11-01: Phase 35 run `41306633592` (#60) completed successfully; job `124848250890` completed the corrected historical-CIK PIT audit and uploaded artifact `13091036734` (`phase35-13dg-pit-event-crosswalk-audit`). No active run was duplicated. The Phase 35 audit returned 20,254 resolved filings out of 20,266 candidates, 12 retrieval failures, 97.11% event-date coverage and 100% filing-date coverage; its PIT rule remains filing_date as the knowledge date.
