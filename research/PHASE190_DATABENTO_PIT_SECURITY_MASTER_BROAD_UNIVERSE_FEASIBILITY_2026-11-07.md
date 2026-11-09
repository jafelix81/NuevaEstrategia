# Phase 190 — Databento PIT Security Master and Broad-Universe Feasibility

**Audit date:** 2026-11-07  
**Disposition:** CONDITIONAL TOP-PRIORITY REFERENCE-DATA CANDIDATE  
**Research class:** universe and identity infrastructure, not an alpha signal

## Executive decision

Databento Security Master is the strongest newly revalidated candidate for the missing point-in-time security-identity layer. Its official documentation describes a historical security master beginning 2005-01-01, listing-level records for listed and delisted securities, and two separate time axes: ts_record (when a record last changed) and ts_effective (when its attributes became effective). Its API exposes historical get_range queries on either axis. The schema also includes listing_id, security_id, issuer_id, CUSIP, FIGI, ISIN, CIK, symbols, exchange, security type, listing status, and listing/delisting dates.

This is directly relevant to the project's unresolved 335-name universe problem and to identity gates for SEC FTD, 13D/G, options-underlying mapping, and other security-level sources. It could replace ticker-only joins with listing/security/issuer identities and support a broader historical US-equity universe.

**It is not admitted yet.** The documentation is unusually promising, but several important facts remain unverified: actual US common-equity coverage and exclusions, the distinction between vendor record time and first customer receipt, update cadence, record-history completeness, the exact count represented by the marketing claims, and the applicable subscription price. The product page itself contains conflicting count, update-frequency, and per-symbol pricing statements.

No API request, sample download, account creation, vendor contact, purchase, terms acceptance, return test, alpha test, holdout use, or production change was made. F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen. Phase 20C remains killed for its tested short-volume stock-selection implementation.

## 1. Why this source matters

The 335 tickers were selected arbitrarily and are not a defensible historical universe. Existing work has also exposed unresolved identity problems:

- SEC FTD records contain CUSIP/ticker observations, but the project has not established a complete effective-dated crosswalk to historical securities and returns.
- SEC 13D/G filings identify issuers and reporting persons, but issuer CIK alone does not identify a particular listed security or share class.
- OpenFIGI Phase 149 mapped a 553-CUSIP sample but left 109 unresolved and did not produce an effective-dated historical security master.
- Options-flow sources need a stable underlying-security join that survives symbol changes, listings, delistings, and relistings.

A single listing-level reference layer could improve all of those pipelines. This is foundational infrastructure, not evidence that any institutional-flow feature predicts returns.

## 2. What the official documentation establishes

The Databento Security Master dataset guide states:

- Historical coverage from 2005-01-01 to present.
- Global coverage and weekly updates.
- Listing-level records, including securities after delisting and through relisting.
- Point-in-time retrieval through the Reference API.

The schema defines:

- ts_record: UTC timestamp when the record last changed.
- ts_effective: UTC timestamp from which the record details are effective.
- ts_created: UTC timestamp when the record was added to Databento's database.
- listing_id: listing-level identifier.
- security_id: identifier linking multiple listings for the same security.
- issuer_id: issuer-level identifier.

The Reference API get_range method accepts index=ts_effective or index=ts_record. It supports symbol, country, and security-type filters; the documentation allows up to 2,000 input symbols per request and documents ALL_SYMBOLS/None as an all-symbol selection. That API-level request limit must not be confused with account entitlements.

The security-master product page advertises 215 venues and US coverage including Nasdaq, NYSE, NYSE American, NYSE Arca, Cboe BZX, IEX, NYSE National, FINRA OTCBB, and OTC Markets Group. FINRA TRACE is also shown on the broad venue list but is fixed-income infrastructure and must not be treated as an equity listing venue.

## 3. Point-in-time interpretation: promising, but not yet proven

The two axes are materially better than a latest-state-only security master:

- ts_effective answers when a status or attribute is described as effective.
- ts_record answers when the provider's stored record last changed.
- ts_created records when the record entered Databento's database.

For a strict historical reconstruction, the research should preserve all three timestamps and query on ts_record when asking what the provider's record contained at a past time. ts_effective is needed to determine when the listing/status actually applied. A current get_last response must never be used to backfill historical membership.

However, none of these fields, by itself, proves the first time the exchange made the information public or the first time a Databento customer could retrieve it. ts_record is a vendor record-change timestamp, not an exchange announcement timestamp. ts_created is a database-ingestion timestamp, not a customer-delivery receipt. The published weekly cadence also conflicts with the product FAQ's statement that new data are appended four times per day. We therefore do not yet admit the source as an executable, strict-PIT universe.

Required validation must compare ts_record, ts_effective, and ts_created across new listings, ticker changes, exchange transfers, corporate actions, delistings, relistings, corrections, and retrospective backfills. A prospective immutable capture of actual API responses is required before any live signal relies on the feed.

## 4. Identity model and expected use

Do not collapse the identifiers:

| Identifier | Intended role | Research rule |
|---|---|---|
| listing_id | One listing on one venue | Primary key for listing history |
| security_id | One security across multiple listings | Security-level continuity key |
| issuer_id | Issuing company | Issuer grouping only; not a share-class key |
| us_code / CUSIP | North American security identifier | Crosswalk key; verify effective periods and reuse |
| FIGI | Instrument/listing identifier | Preserve exact FIGI type and mapping scope |
| ISIN | International security identifier | Preserve effective periods and class distinctions |
| CIK | SEC issuer/entity identifier | Do not treat as a security identifier |
| symbol / nasdaq_symbol / local_code | Trading-symbol representations | Attributes, never permanent primary keys |

Preserve exchange and operating_mic separately. The documentation describes exchange as a more stable normalized venue code and notes that MIC values can change or may not be available in a timely fashion.

A future crosswalk should be many-to-many and time-aware. It must not force one CUSIP, FIGI, CIK, or ticker into a single permanent mapping when multiple listings or share classes exist.

## 5. Coverage and universe caveats

The documentation supports broad global coverage, but it does not yet establish the count of eligible US common-equity listings needed for this project.

The current product page displays 860,000+ in its headline, while another section displays 310,000+ for listed and delisted instruments. These figures may use different scopes or definitions, but the page does not reconcile them. The dataset guide's 2005 start and 21-year product headline are consistent as of this audit date; an older cached 18-year marketing snippet is treated as stale, not as a competing current history claim.

The product page's sample description is only a sample of 500 Nasdaq stocks and ETFs (9,100 CSV records, labelled 2024), plus 500 global securities (1,000 records). It is not proof of full US exchange coverage, common-stock-only coverage, delisted coverage, or historical completeness.

The next sample audit must explicitly classify:
- Common stocks and ordinary shares.
- ADRs and other depositary receipts.
- REITs, BDCs, preferred shares, closed-end funds, ETFs, ETNs, warrants, rights, units, and other hybrid instruments.
- Primary versus secondary listings and duplicate listings.
- OTC transitions and relistings.
- Delisted names and securities with no current ticker.
- Multiple share classes and reused symbols.

The target universe should be built from historical listing records plus ex-ante liquidity/price rules, not from the legacy 335 tickers or a current index constituent list. The 335-name set remains a diagnostic comparison only.

## 6. Access, update cadence, and economics

The public page advertises a 1,000-symbol plan allocation. Its sample section says each additional symbol costs USD 0.50 per month; the FAQ instead refers to a Starter plan and USD 1.75 per additional symbol per month, with a 12-month term when upgrading. The page also says new users receive USD 125 in credits. The base plan price and the applicable current per-symbol rate were not resolved.

Arithmetic-only scenarios, excluding the base plan and any taxes or other fees:

| Requested symbols | Symbols above 1,000 | At USD 0.50/month | At USD 1.75/month |
|---:|---:|---:|---:|
| 5,000 | 4,000 | USD 2,000/month | USD 7,000/month |
| 10,000 | 9,000 | USD 4,500/month | USD 15,750/month |

These are not vendor quotes. The 2,000-symbol API request maximum is separate from the 1,000-symbol plan allocation and does not override it. The source's count-by-symbol allocation model means a full-universe request could be materially more expensive than a small sample.

The product page says updates are weekly, while its FAQ says new data are appended four times per day at 4–5 AM, 9–10 AM, 2–3 PM, and 7–8 PM London time. The dataset guide says weekly. Until reconciled, use neither schedule as a first-receipt guarantee.

The product page states internal use is permitted, including non-display use, while external redistribution over files or API is not allowed. This is compatible with internal research in principle, but the exact plan and license terms still require review before use.

## 7. Comparison with alternatives

### Norgate Data Platinum

Norgate's official US package includes major-exchange active securities, selected delisted securities and historical index constituents back to 1990, at USD 630 for 12 months. Its FAQ describes a stable assetid that survives symbol changes, exchange/OTC transitions, delisting, and other corporate actions. This is a credible lower-cost daily-price and survivorship-bias alternative.

It is not equivalent to Databento's documented record-time PIT model: Norgate says it does not provide prior symbols/tickers or the dates of symbol changes, and its historical index membership is effective-date membership rather than an announcement-time archive. It also does not solve the broader event-source identity problem by itself. The two products could be complementary if their license and data fields pass inspection.

### CRSP

CRSP remains the benchmark comparator for active/inactive US securities, permanent identifiers, corporate actions, and delisting returns. Its cost and access route remain unresolved in this audit. CRSP may be the better return-series reference; Databento may be the more useful high-resolution reference/identity layer. Neither should be assumed to replace the other before sample reconciliation.

## 8. Admission gates and next research sequence

1. **Access and cost gate:** obtain user authorization before creating a Databento account, using free credits, accepting terms, contacting sales, or incurring any charge. Resolve the 1,000-symbol plan, the USD 0.50/USD 1.75 discrepancy, annual commitment, and internal-use license.
2. **Sample gate:** if authorized, acquire only the advertised 500-US-security sample or a bounded sample within the included symbol allocation. Preserve the exact download and retrieval timestamps and file hash.
3. **PIT semantics gate:** test historical records using both ts_record and ts_effective. Include late corrections and retrospective changes. Compare against contemporaneously archived exchange notices where possible.
4. **Identity gate:** test known ticker changes, share-class pairs, exchange transfers, OTC transitions, delistings, relistings, and ticker reuse. Require deterministic, collision-audited listing_id/security_id/issuer_id chains.
5. **Coverage gate:** quantify US common-equity coverage by year, venue, security type, active/delisted status, and market-cap/liquidity bucket. Do not report a single global security count as US-equity coverage.
6. **FTD bridge:** crosswalk SEC FTD CUSIP/ticker observations to the PIT security master, then report unmatched, ambiguous, class-confused, and time-inconsistent records separately. No FTD alpha test until this and the return join pass.
7. **Returns gate:** obtain or validate a separate survivorship-bias-free return series with delisting returns and corporate-action handling. Security Master is reference data, not a price/return dataset.
8. **Broad-universe gate:** construct a historical US common-equity universe from listing records and lagged, ex-ante eligibility rules. Keep ETFs and other instrument classes separate.
9. **Only then:** resume source-specific predictive tests against frozen LTM/F80 using identical exposure, executable timing, costs, chronological validation, bootstrap/LOO, and a genuinely untouched prospective holdout.

## 9. Final disposition

**Conditional top-priority reference-data candidate; not admitted for alpha research.**

Databento is the first candidate found in this line with an explicitly documented 2005-start PIT security-master history, separate effective and record timestamps, and listing/security/issuer identifiers that could materially improve the project's broad-universe and source-identity foundations.

The remaining access, coverage, timestamp, and pricing gates are material. No vendor contact or purchase is authorized or performed. No alpha result is claimed. No holding-period constraint is introduced. Phase 20C is not reopened, no prior holdout is reused, and F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen.

## Official sources reviewed

- Databento Security Master dataset guide: https://databento.com/docs/datasets/security-master
- Databento Security Master schema: https://databento.com/docs/schemas/security-master
- Databento Reference API: https://databento.com/docs/api-reference-data
- Databento Security Master product page: https://databento.com/security-master
- Databento pricing and credits: https://databento.com/pricing
- Norgate US stock packages: https://norgatedata.com/stockmarketpackages.php
- Norgate data coverage, identity, and historical-index FAQ: https://norgatedata.com/data-package-faq.php
- CRSP US Stock Databases: https://www.crsp.org/research/crsp-us-stock-databases/
