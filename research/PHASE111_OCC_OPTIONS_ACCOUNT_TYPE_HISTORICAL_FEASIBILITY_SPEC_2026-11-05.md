# Phase 111 — OCC options volume by account type: historical-access audit

**Date:** 2026-11-05  
**Branch:** phase99-broad-pit-universe-charter  
**Scope:** public-source feasibility and historical-access audit only; no forward returns, no alpha test, no data purchase.

## Executive decision

OCC's Volume by Account Type / ONN data is a newly prioritized public options-participation candidate. Its raw daily report appears to provide per-symbol/per-exchange Customer, Firm and Market-Maker volume across listed options. It is potentially useful as a participant-composition feature, but it does **not** identify buyer/seller initiation, opening/closing status, beneficial owners or informed traders.

The OCC website currently describes the interactive report as covering the past 24 months. Its official batch-processing documentation, however, provides a daily-download example dated 2019-05-31 and supports daily, weekly, monthly, rolling-year and annual report types. This discrepancy is the reason for the live audit below; neither statement alone proves the full historical archive.

## Official source evidence

- Volume by Account Type page: https://www.theocc.com/market-data/market-data-reports/volume-and-open-interest/volume-by-account-type
- Batch download instructions: https://www.theocc.com/market-data/market-data-reports/other-market-data-info/batch-processing/volume-by-account-type-download-batch-processing
- Batch search instructions: https://www.theocc.com/market-data/market-data-reports/other-market-data-info/batch-processing/volume-by-account-type-search-batch-processing
- Record layout: https://beta-md.theocc.com/getmedia/f7517699-a966-4c84-bcf6-acd9fba381dd/onn-volume-vol-only-no-totals-record-layout.pdf

The official no-totals raw layout is fixed-width:
- Group: columns 1–6
- Symbol: columns 7–12
- Exchange: column 13
- Customer volume: columns 14–22
- Firm volume: columns 23–31
- Market-maker volume: columns 32–40

Exchange codes include AMEX, ARCA, BATS, BOX, CBOE, C2, EDGX, MIAX, NASDAQ/ISE/PHLX families, MEMX and others. The report is not a trade-side tape: it reports account-type volume, not signed buys/sells. It must be treated as clearing-capacity composition, not a direct institutional-flow or smart-money measure.

The documented batch endpoint is:
https://marketdata.theocc.com/onn-volume-download

Parameters from OCC documentation:
- productKind=options
- reportType=D
- reportDate=YYYYMMDD
- reportFormat=volume
- issues=all
- reportView=raw

## Historical-access experiment

The hosted audit queries four fixed dates:
- 2016-05-31 — tests whether the archive reaches beyond the documented 2019 example;
- 2019-05-31 — exact historical date shown in OCC's official batch documentation;
- 2023-11-03 — intermediate historical coverage;
- 2026-11-03 — recent production coverage.

For each date it preserves raw response bytes, HTTP status, content type, Last-Modified, retrieval timestamp, byte count and SHA-256. The parser validates the fixed-width layout, report header dates, exchange codes, nonnegative integer volumes, unique Group/Symbol/Exchange keys and per-account-type totals.

A 200 response is not by itself a pass. HTML/error pages, empty responses, malformed fixed-width rows, wrong report dates or unexplained duplicate keys remain failures. The live job is diagnostic and does not silently reinterpret a 24-month limit as a longer history.

## Point-in-time and economic limitations

1. The report date is the activity date, not a verified publication timestamp. Use no earlier than the next regular session after the report date in any future event study, and add a one-session delay sensitivity. This is a conservative candidate rule, not proof of historical dissemination time.
2. Customer, Firm and Market Maker are clearing/account classifications. Customer may include retail and institutions; Firm is not synonymous with a hedge fund or informed investor; Market Maker volume is not necessarily proprietary directional positioning.
3. The report does not distinguish calls from puts, buyer from seller, opening from closing, or long from short. It is a participant-mix feature only.
4. It must not be summed with OCC Volume Query rows without understanding whether each source counts both sides and whether their denominators differ.
5. Symbol history, corporate actions, inactive securities and delisted issuers still require a point-in-time permanent-identifier crosswalk before security-level return tests.

## Preregistered next gate

If the live audit confirms reproducible 2019 and recent daily files:
1. Test a bounded stratified set of dates across years and market regimes, not only four endpoint examples.
2. Reconcile raw rows against the OCC totals view and the public record layout.
3. Quantify symbol and exchange coverage, including delisted/inactive names where a historical crosswalk exists.
4. Establish a reproducible availability lag from official publication evidence; absent exact timestamps, use next-session plus one-session sensitivity.
5. Compare OCC account-type composition against Cboe Open-Close on overlapping Cboe venues/dates, without assuming their definitions or denominators are identical.
6. Only after broad PIT identity and frozen-universe rules are complete, preregister a participant-composition hypothesis against frozen LTM/F80 with identical exposure/costs, chronological OOS, bootstrap and issuer LOO.

If the historical batch endpoint is limited to 24 months or the file cannot be reconciled, archive the limitation and park the source. No purchases, vendor contact, forward returns or production changes are authorized.

## Adjacent options-source finding: Cboe Option Sentiment

Cboe's official v1.4 specification describes a substantially richer daily product than a simple put/call ratio: directional trade premium and volume, net option delta, call/put open interest, IV30/IV90, normalized 25-delta skew, implied borrow, customer/firm/market-maker volume, trade-size buckets and days-to-expiration buckets. The specification defines direction relative to the midpoint and excludes spreads, late and tied trades; cancelled trades are backed out. Cboe's FAQ lists historical availability beginning January 2012 and says its options datasets cover U.S.-listed stocks, ETFs and indices disseminated over OPRA.

However, the old product URL currently redirects to the DataShop home page and Option Sentiment is absent from the current three-page Options product catalog, even though the FAQ and PDF remain online. Current orderability, pricing, sample availability and method continuity are therefore unverified. It is a high-value conditional candidate, not an available dataset we can assume access to. No contact or purchase was made.

Official references:
- Specification: https://datashop.cboe.com/Documents/Cboe_OptionSentiment_Specs.pdf
- FAQ/history and coverage: https://datashop.cboe.com/faqs
- Former product URL: https://datashop.cboe.com/option-sentiment

## Research boundary

This phase is data feasibility only. It does not claim that customer/firm/MM composition predicts returns, that any account category is informed, or that the data improves F80. F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen.


## Hosted execution

A guarded live audit was triggered after the parser and offline tests were committed. Results will be appended only after the run and artifact are inspected. The workflow does not purchase data, authenticate to a paid service, or accept any terms on the user's behalf.
