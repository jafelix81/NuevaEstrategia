# Phase 331 — historical security-master source feasibility comparison

**Date:** 2026-11-12 UTC  
**Status:** COMPLETED — candidate ranking only; no source admitted  
**Research class:** historical reference-data feasibility, survivorship and identity; no alpha test.

## Executive decision

Phases 328–330 show that SEC periodic XBRL and visible cover-page tables cannot provide a complete historical ticker/security crosswalk in the tested collision panel. Phase 329 also shows why periodic snapshots alone fail across ticker changes and mergers.

A new official-documentation review identifies **Massive (formerly Polygon) All Tickers** as the most practical low-cost historical snapshot candidate to test next: its date parameter supports US-stock reference snapshots back to 2003-09-10, including active and delisted records, CIK and (where populated) composite/share-class FIGIs. However, the provider explicitly says the historical list is the current maintained record for the requested effective date, not a version of what the provider knew at that historical time. Older rows may lack type/exchange fields, and Massive does not publish a universal permanent identifier across every change.

CRSP remains the strongest benchmark for survivor-bias-free US security continuity and returns if access is available. Databento remains the strongest documented record-time/effective-time security-master design, but its price and license are unresolved. **No API account was created, no key was used, no vendor was contacted and no data were purchased.**

## 1. Candidate comparison

| Source | Documented historical scope | Identity / time semantics | Delisted coverage | Disposition |
|---|---|---|---|---|
| CRSP US Stock Database | Product page lists over 32,000 active/inactive US securities and inception dates including 1926/1965 | PERMNO/PERMCO permanent security/company identifiers; corporate actions and delisting returns; monthly/quarterly/annual releases | Yes | Best research benchmark if access/cost can be resolved |
| Databento Security Master | 2005-01-01 to present | listing_id, security_id, issuer_id, CUSIP, FIGI, ISIN, CIK; ts_record, ts_effective, ts_created | Listed and delisted, including relistings | Best documented record/effective-time model; price/license/cadence unresolved |
| Massive All Tickers | 2003-09-10 to present on paid historical tiers; Stocks Basic has only two years | Date-based effective snapshot; CIK, composite_figi, share_class_figi where populated; ticker events; no universal permanent ID and no historical record-version query | Yes, active=false plus date | Best practical low-cost next sample candidate; not strict record-time PIT |
| Norgate Data Platinum | US package and selected delisted/index history back to 1990 | Stable assetid survives symbol/exchange/OTC/delisting changes; no prior ticker history or change dates | Selected delisted securities | Useful survivorship-free daily universe/price comparator; not a complete PIT identity ledger |
| Alpha Vantage LISTING_STATUS | Historical date parameter for dates later than 2010-01-01 | CSV snapshots of symbol, name, exchange, asset type, IPO/delisting date and status; no documented permanent security ID | Active and delisted states | Supplementary broad-listing snapshot; not a class/security crosswalk |
| OpenFIGI | Current identifier mapping/search API | Maps CUSIP/ISIN/other identifiers to FIGI/shareClassFIGI/compositeFIGI; no effective-date history | Unlisted/delisted can be included explicitly | Identifier enrichment only, not a historical master |
| SEC periodic XBRL / cover page | Tested 2006–2026 collision sample | Structured TradingSymbol facts in 14/56 observations; visible Trading Symbol table in 0/25 no-inline-fact documents | Incomplete | Not admitted as a complete crosswalk |
| SEC Form 4 XML | 282/283 sampled originals recovered in Phases 326/327 | Event-level issuerTradingSymbol and transaction securityTitle; 282/282 recovered XML symbols match bulk candidate | Event filings only | Primary event record, not independent security master |

## 2. Massive: promising date snapshots, but not historical record-time PIT

Official Massive documentation states:

- All Tickers is GET /v3/reference/tickers and accepts a date parameter for historical US-stock snapshots back to 10 September 2003.
- active=true returns records active on that date; active=false returns records already delisted by that date, with delisted_utc where populated.
- All Tickers returns up to 1,000 rows per page; full snapshots require following pagination.
- Rows can include CIK, composite_figi and share_class_figi. The FAQ says these FIGI fields can follow a rename, but also says Massive publishes no permanent identifier that survives every change.
- Historical records are the current records maintained by Massive for the requested effective date. A 2003 row may have last_updated_utc in 2025; there is no API parameter to retrieve an older version of the provider's record.
- Older records can have blank type or primary_exchange. Filtering on those fields can silently drop genuine securities; an initial census must retrieve unfiltered rows and classify them afterward.
- Ticker events expose ticker_change events, but delisted securities can return no events. Delisting must also be reconstructed from active=false snapshots.

Plans shown in the official Stocks overview: Basic Free, Starter USD 29/month, Developer USD 79/month and Advanced USD 199/month. The official FAQ says Basic has only two years of reference-ticker history; full history back to 2003-09-10 is on Starter and higher. These are published plan prices, not a quote for this project. No account was created and no request was made.

Official sources:
- [Massive: downloadable security master and point-in-time ticker snapshots](https://massive.com/knowledge-base/article/does-massive-have-a-downloadable-security-master)
- [Massive Stocks REST overview and plan coverage](https://massive.com/docs/rest/stocks/overview)
- [Massive ticker events endpoint](https://massive.com/docs/rest/stocks/corporate-actions/ticker-events)
- [Massive historical point-in-time tickers announcement](https://massive.com/blog/new-point-in-time-tickers-api)

## 3. Alpha Vantage: useful 2010+ active/delisted snapshots, weak identity

Official documentation for LISTING_STATUS describes:
- a date parameter for any YYYY-MM-DD later than 2010-01-01;
- state=active or state=delisted;
- CSV output for US stocks and ETFs.

This could help cross-check a survivorship-aware ticker universe from 2010 onward. It does not document a permanent security/share-class identifier, a first-public timestamp, or a record-time version history. It cannot cover 2006/2008 cases in the Phase 325 collision panel and cannot independently resolve multiple share classes or CIK relationships.

Official source: [Alpha Vantage API documentation — Listing & Delisting Status](https://www.alphavantage.co/documentation/#listing-status).

## 4. CRSP: benchmark-quality continuity, access unresolved

CRSP's current US Stock Database page describes more than 32,000 active and inactive US securities, daily/monthly data and corporate actions, survivor-bias-free history, and permanent PERMNO/PERMCO identifiers. The product page lists inception dates including January 1, 1926 and January 1, 1965. CRSP is therefore the strongest comparator for historical return continuity, delisting returns and permanent security identity in this source review.

Access is available through routes including WRDS and other institutional delivery formats, but the project's entitlement and price are unknown. No account or institutional access was assumed.

Official sources:
- [CRSP US Stock Databases — 2025 layout](https://www.crsp.org/research/crsp-us-stock-databases-2025-layout/)
- [CRSP research data products](https://www.crsp.org/research/)

## 5. Norgate and OpenFIGI

**Norgate:** the official FAQ documents a stable assetid that survives ticker changes, exchange/OTC transitions, delisting and other corporate actions. Its Platinum US package is documented in the existing Phase 190 audit at USD 630 per 12 months and includes active plus selected delisted securities and historical index constituents back to 1990. The same FAQ says prior tickers and ticker-change dates are not supplied. That makes it useful for a survivorship-free daily-price/universe comparison, but not sufficient as a strict event-time symbol history.

Source: [Norgate Data FAQ](https://norgatedata.com/data-package-faq.php).

**OpenFIGI:** the API is free, maps third-party identifiers to FIGI/shareClassFIGI/compositeFIGI and can include unlisted/delisted equities when includeUnlistedEquities=true. The documented API does not supply historical effective dates or prior record versions. Use it to enrich a CUSIP/ISIN mapping when available, not to backfill a point-in-time security master.

Source: [OpenFIGI API documentation](https://www.openfigi.com/api/documentation).

## 6. Recommended sequence

1. Keep the SEC Form 4 XML as the event-level source for issuerTradingSymbol and transaction securityTitle, with the missing TSBK accession quarantined. Classify transaction codes, ownership form and derivative/non-derivative security before treating an event as an insider buy/sell.
2. If access is authorized, run a bounded Massive historical snapshot audit first because its published Starter tier is relatively low-cost and its date parameter reaches 2003. Test a stratified set of dates and cases: ticker renames, CIK changes, multiple share classes, ADRs, preferreds, mergers, exchange transfers, OTC transitions, delistings and relistings.
3. Require 95%+ exact coverage for the target common-equity universe, but report missing/ambiguous classes separately. Never filter older Massive records by type/exchange before measuring blanks.
4. Compare Massive snapshots with CRSP PERMNO/PERMCO if institutional access exists. Treat CRSP as the return/delisting benchmark, not merely another ticker file.
5. Revisit Databento only after access and cost authorization; compare ts_record, ts_effective and ts_created against dated exchange/company events. Do not interpret vendor record time as first-public time.
6. Use Alpha Vantage and OpenFIGI only as supplemental cross-checks until their identity and timing limitations are resolved.
7. Only after a broad historical universe and corporate-action graph pass coverage should source-specific signals be tested against frozen LTM/F80 with identical exposure, executable timing, costs, chronological validation, bootstrap/LOO and a genuinely untouched prospective holdout.

## Controls and final disposition

- No API request, account creation, key use, vendor contact, terms acceptance or purchase.
- No security master admitted and no universe coverage claimed.
- No return, alpha, bootstrap/LOO, chronological OOS or holdout test.
- F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen.
- No production, universe, capital or parameter changes.
- No minimum or maximum holding period imposed.
