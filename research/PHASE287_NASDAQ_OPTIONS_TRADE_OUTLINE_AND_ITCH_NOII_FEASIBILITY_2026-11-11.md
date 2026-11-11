# Phase 287 — Nasdaq options Trade Outline and TotalView-ITCH/NOII feasibility
Date: 2026-11-11  
Status: source-feasibility audit only; no raw data admitted, no alpha test.

## Executive decision

Two additional Nasdaq source families are worth retaining, but neither is admitted to signal research yet:

1. **Nasdaq ISE Trade Outline EOD** is the strongest new options-flow candidate by historical depth: EOD history is documented from January 2006; intraday history from October 2009. It provides series-level open/close activity by exchange origin category, plus open interest and industry-volume context. Its historical cost is prohibitive for a full-history purchase.
2. **Nasdaq TotalView-ITCH / NOII** is the strongest new equity microstructure candidate. The historical feed preserves order lifecycle and trade messages, while NOII isolates auction imbalance messages. It is exchange-specific, very large, requires account credentials for the full SFTP archive, and only some orders carry MPID attribution.

PHLX PHOTO has a useful free six-month 2014 sample formally documented by the SEC, but the current retrieval location has not been verified. This is the best no-purchase route for a first schema/coverage inspection if the sample can be recovered.

No source in this phase demonstrates predictive or economic value. Do not change F80, production, universe, capital, parameters or holdout.

## 1. ISE Trade Outline — high historical value, high acquisition cost

Official ISE filings and the current ISE Options 7 fee schedule document:

- End-of-day history beginning **January 2006**.
- Intraday history beginning **October 2009**.
- EOD subscription: **$850/month** (annual subscription).
- Ad-hoc EOD historical data: **$600 per requested month**.
- Current-distributor discount: **$7,200 for the most recent 36 months**, requiring purchase of the current EOD product in the same month.
- Intraday subscription: **$2,500/month**; ad-hoc historical: **$1,000 per requested month**; current-distributor 36-month price: **$12,000**.
- A one-month EOD free trial is listed for first-time subscribers, including non-members.

The EOD profile is series-level and includes opening/closing activity, buy/sell side, open interest, exchange and industry volume, and participant-origin categories. Intraday reports are 10-minute snapshots. The intraday product is cumulative; snapshots must not be summed. EOD is available the next business day, so any historical signal must be delayed until the next executable session unless a separate, verifiable earlier availability timestamp is established.

**Origin categories are not investor identities.** Priority Customer is a regulatory order-count category; Professional Customer is not synonymous with a hedge fund or institution. Firm Proprietary and Market Maker are exchange/clearing classifications, not beneficial-owner identifiers. No fund-level identity is supplied.

Cost screen: Jan 2006–Oct 2026 is approximately 250 calendar months. At the current $600 ad-hoc rate, a full EOD history would be approximately **$150,000**, before any current subscription or other charges. The $7,200 discount covers only the latest 36 months and requires a current subscription. This is not justified before a free/low-cost sample establishes coverage and schema stability.

## 2. PHLX PHOTO — useful second venue and a documented free sample

PHLX PHOTO covers PHLX electronic options trades by series and origin category (Customer, Broker-Dealer, Market Maker, Firm, Professional), with open/close and buy/sell distinctions. The EOD product includes industry volume and open interest; the intraday product is cumulative 10-minute snapshots. EOD is updated overnight and available the following morning, approximately 7:00 a.m. ET per the product FAQ.

Documented history begins **January 2009**. The PHOTO FAQ says the Security Type field is only available back to June 2010; therefore do not assume a fully uniform field panel from the 2009 start. The Professional category is defined by an average of more than 390 listed-options orders per day for the participant's own beneficial accounts; it does not identify an institution or beneficial owner.

Current PHLX Options 7 fees:
- EOD subscription: **$850/month**.
- Intraday subscription: **$3,000/month**.
- Ad-hoc historical: **$500 per EOD month** / **$1,000 per intraday month**.
- Current-distributor 36-month discount: **$6,000 EOD** / **$12,000 intraday**.
- External distribution of derived PHOTO data is separately priced at **$5,000/month**; no external redistribution is contemplated here.

The SEC-approved 2017 filing explicitly made **January 1–June 30, 2014** EOD and intraday PHOTO history available free to any person, including non-subscribers. The current successor download path is not verified: NasdaqTrader's legacy PHOTO page redirects to Nasdaq Data Link, whose browser-rendered database page does not expose the file listing in this environment. Treat the free sample as a documented retrieval lead, not as a file already obtained.

Cost screen: Jan 2009–Oct 2026 is approximately 214 months. At $500 per EOD month, a full history would be approximately **$107,000**. The 36-month discount is still $6,000 and requires a current subscription. Do not purchase full history.

## 3. TotalView-ITCH / NOII — high-value microstructure, heavy data burden

Nasdaq's historical SFTP guide documents versioned archives:
- ITCH 5.0 from April 8, 2014;
- ITCH 4.1 from May 3, 2010;
- ITCH 4.0 from January 12, 2009;
- ITCH 3.0 from August 13, 2007;
- older ITCH 2.0 files before August 17, 2007.

The guide requires a Nasdaq Historical TotalView-ITCH account username/password for the full SFTP archive. The public HTTP directory is a sparse sample archive, not a complete daily backtest history. The public NOII sample directory currently lists one file, `S050922-v50-NOII.txt.gz` (96,588,423 bytes, 2022-05-09). Full ITCH sample files are multi-gigabyte; Nasdaq's Data Link FAQ reports v5 files averaging roughly 5–10 GB compressed and 15–25 GB uncompressed.

ITCH can support order-book and order-flow features: add/execute/cancel/replace imbalance, queue/depth imbalance, order lifetime, replenishment, price impact and auction-cross dynamics. NOII-only files contain message types I/T/S (imbalance, timestamp, system event), so they are much smaller and may be the better first pilot for a daily swing strategy.

**Attribution is partial.** ITCH has an Add Order message without MPID attribution (type A) and a separate attributed Add Order message (type F). MPID is a market-participant identifier, not a beneficial-owner or fund identifier; un-attributed orders remain un-attributed. The feed covers activity on the Nasdaq execution system, not all U.S. exchanges, ATSs or off-exchange trading. Do not describe it as complete institutional flow.

The file's event timestamps are source timestamps, not proof that the strategy received the data at that time. Historical files are delivered T+1 through the account-based service. For a daily strategy, default to using trade-date t information no earlier than the next executable session; record file receipt/availability separately. The v2/v3/v4/v4.1/v5 format transitions require version-specific parsers and cross-version tests.

A public sample download was attempted in this environment but no bytes were obtained because outbound DNS/network access to emi.nasdaq.com is unavailable. This is an environment limitation, not evidence that the public file is absent. No Nasdaq account, credentials, trial, purchase or vendor contact was initiated. The current public price list does not establish the historical SFTP license fee; obtain written pricing and usage terms before any acquisition.

## 4. Cross-source interpretation and admission gates

| Source | Historical window documented | Availability / PIT | Universe and semantic limitation | Current disposition |
|---|---|---|---|---|
| Cboe Open-Close | Existing Phase 248/249/251 work; real EOD sample reprocessed | EOD/intraday conventions already audited; preserve version/venue | Four Cboe venues only; venue-specific | Retain existing sample; no new purchase |
| ISE Trade Outline | EOD Jan 2006; intraday Oct 2009 | EOD next business day; intraday cumulative 10-min | ISE only; origin classes, not owner identities | High-priority sample candidate; cost gate |
| PHLX PHOTO | Jan 2009; Security Type only from Jun 2010 | EOD next morning; intraday cumulative 10-min | PHLX only; origin classes, not owner identities | Seek documented free 2014 sample first |
| Nasdaq NOTO | Nov 2011 (Phase 286) | EOD T+1; intraday cumulative | NOM only | Keep as one-venue comparator |
| NYSE Arca/American Open-Close | EOD Dec 2018; intraday Arca Aug 2022 / American Nov 2023 | EOD T+1; schema gaps and duplicate Flex/Flex Percent rows already identified | Two NYSE options venues only | Lower priority until data-quality gaps resolved |
| Nasdaq ITCH/NOII | Versioned formats documented from 2007; v5 from Apr 2014 | Historical file T+1; event timestamps are not receipt timestamps | Nasdaq execution system only; partial MPID attribution | High-potential microstructure candidate; access/volume gate |

Before any model test, require:
1. A real raw sample and file hashes, with exact source version and documented terms.
2. Daily coverage by underlying against the **historical point-in-time universe**, including inactive/delisted names.
3. Effective-dated option-series and underlying-symbol mapping, corporate actions and adjusted/non-standard series handling.
4. Exact field availability by date; do not backfill fields that were introduced later.
5. Receipt/availability timestamps and a conservative executable timestamp. Intraday snapshots must be differenced, not summed.
6. Per-series venue volume divided by industry volume where valid; do not sum venue data as if it were the whole options market.
7. A preregistered test of incremental information over frozen LTM/F80, chronological splits, no-lookahead, costs, identical exposure, bootstrap/LOO, multiplicity controls and a fresh OOS holdout.

Potential hypotheses only: (a) opening customer/professional/firm activity by call/put and open/close; (b) exchange-specific flow share after controlling for total industry volume; (c) auction imbalance persistence/reversal; (d) order-book replenishment/cancellation and imbalance. Each must be tested against return-chasing and contemporaneous price/volume controls. No participant class is assumed to be “smart money.”

## 5. Decision and next step

- Do **not** purchase full ISE, PHLX or ITCH history.
- First recover the free PHLX Jan–Jun 2014 sample and/or obtain the one-month ISE EOD trial only with explicit account/terms approval.
- For ITCH, first obtain written SFTP price/usage terms and a permitted NOII-only sample; do not download multi-GB daily files until the parser and coverage economics are proven.
- Continue SEC Form 4 PIT work separately; `SEC_CONTACT_EMAIL` remains unconfigured and no SEC request was made.
- No raw option/ITCH sample was admitted in this phase; no backtest, alpha estimate, bootstrap, LOO or OOS result was produced.

## Sources (official / primary)

- Nasdaq ISE Options 7 fee schedule: https://listingcenter.nasdaq.com/rulebook/ise/rules/ise-options-7
- Nasdaq ISE 2024 Trade Profile history and fee filing: https://listingcenter.nasdaq.com/assets/rulebook/ise/filings/SR-ISE-2024-36.pdf
- Nasdaq PHLX Options 7 fee schedule: https://listingcenter.nasdaq.com/rulebook/phlx/rules/phlx-options-7
- Nasdaq PHLX PHOTO FAQ: https://www.nasdaqtrader.com/content/productsservices/dataproducts/PHLX%20Options/PHOTO%20FAQs%20v1.3.pdf
- SEC Release 34-81117 (free PHLX 2014 sample): https://www.sec.gov/rules/sro/phlx/2017/34-81117.pdf
- Nasdaq Historical TotalView-ITCH SFTP guide: https://www.nasdaqtrader.com/content/technicalSupport/specifications/dataproducts/ITCHFTP.pdf
- Nasdaq TotalView-ITCH 5.0 specification: https://nasdaqtrader.com/content/technicalsupport/specifications/dataproducts/NQTVITCHSpecification.pdf
- Nasdaq Data Link Historical TotalView-ITCH FAQ: https://data.nasdaq.com/databases/NTV
- Public sample archive: https://emi.nasdaq.com/ITCH/Nasdaq%20ITCH/
- Public NOII sample directory: https://emi.nasdaq.com/ITCH/Nasdaq%20ITCH/NOII/
- Nasdaq NOTO dataset documentation: https://data.nasdaq.com/databases/NOTOI
- NYSE Open-Close product/specification: https://www.nyse.com/data-products/catalog/open-close-volume-summary
- Cboe Open-Close product: https://datashop.cboe.com/cboe-options-open-close-volume-summary
