# Phase 186 — Nasdaq Trade Outline Cross-Venue Historical Coverage and PIT Feasibility Audit

**Audit date:** 2026-11-07  
**Status:** Evidence-only. No paid sample, return test, holdout use, vendor contact or production change.

## Executive decision

Nasdaq Trade Outline is a **high-priority conditional options-flow data candidate**. It provides exchange-specific opening/closing activity by participant capacity across six Nasdaq-affiliated options venues, with archive history reaching 2006–2017 depending on venue. It is not a consolidated OPRA feed and does not identify beneficial owners.

The most serious issue is cross-venue attribution: Nasdaq's own FAQ says orders routed away to another exchange are included in Trade Outline and there is no flag identifying them. **Do not aggregate the six venues until this is resolved.**

A second issue is snapshot mutability. Cumulative intraday volume can be revised downward, rows can disappear after cancellations, and EOD can include corrections after the last intraday snapshot. Without immutable first-received vintages, historical backfill is not a strict-PIT event tape.

This phase also corrects Phase 185: Cboe's one-minute filings were filed on 2025-06-13 but state a 30-day operative delay. The earliest legal operative date is 2025-07-13; the first possible regular session is 2025-07-14. June 13 was not the live-product floor.

## 1. Six-venue archive and live-product chronology

Nasdaq's current FAQ lists six separate products: PHOTO, NOTO, ISE, GEMX, MRX and TEXAS (the legacy BX product now associated with NTX).

| Venue / product | Intraday archive | EOD archive | Documented live-product floor | PIT interpretation |
|---|---:|---:|---|---|
| PHLX / PHOTO | 2009-01 | 2009-01 | 2010-09-01 | Pre-launch archive is retrospective |
| ISE Trade Profile | 2009-10 | 2006-01 | EOD 2007-08-15; intraday 2010-01-04 | Both archive starts predate documented floors |
| NOM / NOTO | 2011-11 | 2011-11 | Not before 2011-11-11 under the 30-day operative-delay clause | First receipt unverified |
| GEMX Trade Profile | 2013-08 | 2013-08 | Exact data-product first-live date not established | Archive start is not proof of first availability |
| MRX | 2017-09 | 2017-09 | Nasdaq announced 2024-09-03, pending SEC approval | 2017–2024 archive is backfill |
| NTX / TEXAS (legacy BX) | 2014-09 | 2014-09 | Nasdaq announced 2024-09-03, pending SEC approval | 2014–2024 archive is backfill |

The ISE intraday product became effective on 2010-01-04; its current archive begins in October 2009. PHOTO was introduced on 2010-09-01, while its archive begins in January 2009. NOTO was filed on 2011-10-12 and the SEC notice states the change does not become operative for 30 days; 2011-11-11 is the conservative legal lower bound, not a subscriber first-receipt record.

Nasdaq's September 2024 technical notice announced MRX and BX Trade Outline products effective 2024-09-03, pending SEC approval, while advertising historical files from September 2017 and December 2014 respectively. Those pre-launch years are historical backfill, not contemporaneous live-product evidence.

GEMX launched as an options exchange in 2013 and the archive begins in August 2013, but the exact first live date of the Trade Profile product was not established. Do not infer it from the exchange launch date.

**Admission result:** zero of six venues are strict-PIT admitted. Product launch dates are only legal/commercial lower bounds. Every venue still requires first-receipt evidence, immutable file vintages, correction lineage and point-in-time underlying identity.

## 2. What the product measures

The products report proprietary electronic options trades for the respective exchange. The FAQ describes aggregate trade quantity and volume by customer capacity and opening buy, closing buy, opening sell and closing sell. They cover electronically traded series on each reporting venue, including index and ETF options; they do not represent the entire U.S. options market.

Participant fields are capacity labels, not investor identities:

- **Firm:** a member's own proprietary account.
- **Broker/Dealer:** a broker-dealer account that is not the member's own proprietary account.
- **Market Maker:** a participant registered as a market maker on that exchange.
- **Customer:** an OCC customer-range transaction subject to the exchange's customer definition and the 390-orders/day threshold.
- **Professional Customer:** a non-broker/dealer customer exceeding the average 390 listed-options orders/day threshold for its own beneficial account(s).

None identifies a fund, beneficial owner, investment manager or economic purpose. Firm, Professional and Customer are not synonyms for Smart Money or Retail. Treat every participant interpretation as a hypothesis.

Market makers do not have to specify opening versus closing for PHOTO, NOTO, MRX and TEXAS. ISE/GEMX did not include market-maker trade/volume counts in the old client experience; enhanced tables began including them on 2026-03-04. This is a material capacity-coverage break, and post-cutover market-maker open/close semantics still require sample validation.

## 3. Delivery timing and snapshot semantics

The current Nasdaq FAQ describes:
- 10-minute cumulative intraday snapshots, first regular file at 09:40 ET for 09:30:00–09:39:59.
- Current expected delivery within two minutes after the reporting interval.
- EOD on T+1 by 07:00 ET; earlier delivery is not guaranteed.
- EOD can include corrections processed after the final intraday interval.

Older SEC product filings for PHLX and NOTO describe a five-minute delivery window. The current two-minute FAQ must not be retroactively applied to every historical period. Historical SLA regimes and actual first-receipt times remain unverified.

Snapshots are cumulative, not independent interval volumes. Volume can decrease after corrections/cancellations; if all trades for a series are cancelled, the row can disappear from subsequent updates. Therefore:
- Never sum successive snapshots.
- A snapshot difference is a change in the published cumulative state, not necessarily pure interval trade volume.
- Preserve every received version and its timestamp/hash.
- Do not convert an absent row to zero without a complete coverage indicator.
- Do not use same-day EOD data for a same-day closing execution.

## 4. Cross-venue routing is a hard aggregation blocker

Nasdaq's FAQ explicitly states that orders routed away to another exchange are included in Trade Outline and there is no flag indicating they were routed away.

Until Nasdaq documents the exact attribution and counting semantics, we cannot assume each venue file is a disjoint set of executions. Aggregating PHOTO + NOTO + ISE + GEMX + MRX + NTX could double-count or misattribute routed order activity.

This is a hard blocker for a six-venue aggregate. It does not prove that each single-venue series is useless; it means the feature must be described as venue-reported order/trade-origin activity, not unambiguously venue-executed volume, until clarified.

## 5. Schema and denominator breaks

1. ISE/GEMX enhanced tables began 2026-03-04. They add market-maker counts and change the old size-bucket presentation to a single cumulative field. Legacy table codes were scheduled for decommissioning after 2026-06-02.
2. PHOTO/NOTO bucket trade counts and volumes using both individual-trade counts and aggregate-volume thresholds. Older ISE/GEMX bucket assignment used trade counts; post-2026-03-04 tables use a single cumulative field. MRX/TEXAS also use a single cumulative field.
3. Before 2026-03-04, ISE/GEMX Total Industry Volume was reported per side and was twice the contract-total convention used by PHOTO/NOTO/MRX/TEXAS. The enhanced ISE/GEMX tables moved to contract totals. Any cross-venue denominator needs effective-dated normalization.
4. Moneyness is available only in EOD for ISE/GEMX/MRX/TEXAS, not uniformly across all intraday products.
5. Open Interest and Total Industry Volume are EOD fields sourced from OCC across all U.S. options exchanges. OI is a market-wide outstanding-contract snapshot, not participant direction or proof of informed opening demand.

## 6. New NTX one-minute Intra-Day Snapshots

SEC Release 34-106176 records a Nasdaq Texas filing on 2026-08-11, noticed on 2026-08-24. The rule has a 30-day operative delay, giving 2026-09-10 as the earliest legal operative date. The filing says an implementation date would be announced by public notice no later than 30 days after the operative date. An implementation notice and actual first delivery were not located in the official sources reviewed by 2026-11-07.

The mechanism is unusual:
- A snapshot is disseminated when at least two trades involving at least three origin types occur in an option series during a one-minute interval.
- Activity not meeting the criteria is reported at the end of that one-minute interval.
- The report does not disclose the actual trade count or identifying details.
- Fields include total exchange volume, open interest, and aggregate opening/closing quantity and volume by origin type.
- Snapshot fields do not provide buy/sell side, so they are not a direct bullish/bearish option-flow measure.
- The SEC describes this as a market-sentiment indicator, not a trade-reporting system, and says it is not a real-time data feed.

This is a potentially useful prospective measure of multi-capacity participation, but it has no admitted historical first-receipt series in this audit.

## 7. Current published data cost

The Nasdaq 2025/2026/2027 U.S. Options price list shows these 2026 internal-distribution distributor fees:

| Venue | Intraday / month | EOD / month |
|---|---:|---:|
| PHLX | $3,000 | $850 |
| NOM | $2,000 | $575 |
| ISE | $2,500 | $850 |
| GEMX | $1,500 | $575 |
| MRX | $1,500 | $750 |
| BX / NTX legacy label | $1,500 | $750 |
| **Six-venue total** | **$12,000** | **$4,350** |

The ISE combined EOD + intraday subscription is $3,100/month; buying both products across all six venues is therefore about $12,600/month. The current-subscriber discount for the most recent 36 months is $57,000 for intraday and $33,000 for EOD across all six. At per-requested-month historical rates without ongoing subscriptions, 36 months of intraday would be approximately $171,000 and EOD $99,000.

These are published schedule amounts, not a quote. External distribution/derived-data rights are separate. No purchase or vendor contact was made. The price alone argues against buying a six-venue historical bundle before sample-level validation.

## 8. Phase 185 correction — Cboe one-minute operative date

Phase 185 incorrectly treated 2025-06-13 as the Cboe one-minute live-product floor. The four SEC notices (C1, C2, BZX and EDGX) identify 2025-06-13 as the filing date, but each states that the rule does not become operative for 30 days after filing unless the Commission designates a shorter period.

The corrected conservative floor is:
- Filing date: 2025-06-13.
- Earliest legal operative date: 2025-07-13.
- First possible regular trading session: 2025-07-14.
- Actual first subscriber receipt: not verified.

The Phase 185 report and JSON are updated in this commit. Pre-2025-07-13 one-minute archive rows are retrospective for live-PIT research. Even post-floor rows remain quarantined until first-receipt logs and immutable revisions are demonstrated.

## 9. Decision and next gates

**Status: CONDITIONAL_HIGH_PRIORITY_DATA_FEASIBILITY_CANDIDATE — NOT PIT ADMITTED.**

1. Audit an authorized/public sample file and all six schemas before considering a subscription.
2. Obtain written clarification of routed-away order attribution and cross-venue duplication.
3. Capture first-receipt timestamps, file hashes, revisions, cancellations and delivery delays prospectively.
4. Validate historical option-series-to-underlying mappings, corporate actions, delistings and overlap with the actual stock universe.
5. Harmonize participant capacities only where definitions are demonstrably equivalent; retain native venue categories otherwise.
6. Only after these gates, preregister a feature test separating information continuation, temporary price pressure and reversal. Compare against frozen LTM/F80 with identical exposure/costs, chronological validation, bootstrap and LOO.

No alpha test was run, no holdout was used, no data was purchased, no provider was contacted, and production was not changed. F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen.

## Official sources

1. [Nasdaq Trade Outline FAQ — archive dates, delivery, schema, routing and corrections](https://assets.ctfassets.net/mx0rke14e5yt/71lokR7lXiJBnX49Nuvuur/741a4f9d4e0ab2625ced20003b0f3c9f/Trade_Outline_FAQ_-_Post_ISE_and_GEMX_TO_Migration__2_.pdf)
2. [ISE EOD Trade Profile — SEC Release 34-56254 (2007)](https://www.sec.gov/files/rules/sro/ise/2007/34-56254.pdf)
3. [ISE intraday Trade Profile — SEC Release 34-61317 (2010)](https://www.sec.gov/files/rules/sro/ise/2010/34-61317.pdf)
4. [PHLX PHOTO — SEC Release 34-62887 (2010)](https://www.sec.gov/files/rules/sro/phlx/2010/34-62887.pdf)
5. [NOM NOTO — SEC Release 34-65587 (2011)](https://www.sec.gov/files/rules/sro/nasdaq/2011/34-65587.pdf)
6. [GEMX Data Link publisher and archive product description](https://data.nasdaq.com/publishers/GMINI)
7. [GEMX rulebook — Trade Outline definition](https://listingcenter.nasdaq.com/rulebook/gemx/rules/GEMX%20Options%203)
8. [Nasdaq Trader Data Technical News 2024-19 — MRX/BX launch and archive starts](https://nasdaqtrader.com/TraderNews.aspx?id=dtn2024-19)
9. [MRX SEC filing SR-MRX-2024-40](https://listingcenter.nasdaq.com/assets/rulebook/mrx/filings/SR-MRX-2024-40.pdf)
10. [BX/NTX SEC filing SR-BX-2024-028](https://listingcenter.nasdaq.com/assets/rulebook/nasdaqtx/filings/SR-BX-2024-028.pdf)
11. [NTX one-minute Intra-Day Snapshots — SEC Release 34-106176 (2026)](https://www.sec.gov/files/rules/sro/nasdaqtx/2026/34-106176.pdf)
12. [Nasdaq U.S. Options Price List 2025/2026/2027](https://www.nasdaqtrader.com/content/ProductsServices/PriceList/Nasdaq_US_Options_Price_List_2025_2026_2027.pdf)
13. [Cboe C1 one-minute filing — SEC Release 34-103323](https://www.sec.gov/files/rules/sro/cboe/2025/34-103323.pdf)
14. [Cboe C2 one-minute filing — SEC Release 34-103324](https://www.sec.gov/files/rules/sro/c2/2025/34-103324.pdf)
15. [Cboe BZX one-minute filing — SEC Release 34-103322](https://www.sec.gov/files/rules/sro/cboebzx/2025/34-103322.pdf)
16. [Cboe EDGX one-minute filing — SEC Release 34-103321](https://www.sec.gov/files/rules/sro/cboeedgx/2025/34-103321.pdf)
