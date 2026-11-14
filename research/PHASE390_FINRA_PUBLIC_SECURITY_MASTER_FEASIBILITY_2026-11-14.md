# Phase 390 — FINRA T1 public security-master feasibility audit

**Audit date:** 2026-11-14  
**Disposition:** NO FREE PUBLIC SOURCE PASSES BOTH EFFECTIVE-DATED IDENTITY AND RECORD-KNOWN PIT. FINRA RETURN TEST REMAINS NOT AUTHORIZED.  
**Scope:** Documentation and source-feasibility only. No vendor contact, purchase, API-key use, sample acquisition, price download, forward return, alpha, OOS, bootstrap, LOO or holdout test.

## Executive decision

Phase 385 validated a conservative date-level publication clock for all 209 FINRA T1 weekly partitions. Phase 375 validated a revision-stable symbol-week panel. The remaining binding gate is not the FINRA report date; it is effective-dated security identity plus a defensible historical universe and price/delisting join.

FINRA's weekly summary uses an exchange-assigned issueSymbolIdentifier/symbol. The public schema does not provide a permanent listing/security identifier such as PERMNO, FIGI, CUSIP or a FINRA-issued immutable security key. A ticker-only join is therefore insufficient for symbol reuse, class changes, relistings and delisted names.

The source comparison below distinguishes:
1. Effective-dated identity: what symbol/security was effective on a historical date.
2. Record-known PIT: when the vendor/source first knew or recorded a mutable fact.
3. Investable-universe PIT: whether the security was eligible under a frozen rule at the time.
4. Return completeness: active and inactive prices, corporate actions and terminal/delisting returns.

No no-cost public source reviewed here passes all four.

## Source comparison

| Source | Historical/effective identity | Record-known PIT | Inactive/delisted | Decision |
|---|---|---|---|---|
| FINRA T1 ATS | Symbol-level only | Initial publication date validated; no security-master record clock | Historical symbols appear in reports, but no permanent ID | Not a security master |
| SEC company ticker files | Periodically updated current associations; SEC does not guarantee accuracy or scope | No historical record-vintage clock | Not a complete historical listing/delisting master | Reject as sole crosswalk |
| Massive (formerly Polygon) All Tickers | Date query returns historically effective ticker/name/exchange/active status from 2003-09-10; inactive records available | Historical-date results are current database records, not archived versions as known on that date; old rows can carry later last_updated_utc | Yes, with optional delisted_utc | Useful effective-date candidate, fails strict record-known PIT |
| Databento Security Master | Listing/security/issuer IDs, listing/delisting dates, CUSIP/FIGI and security type | Explicit ts_record and ts_effective clocks | Listed and delisted coverage documented | Best documented PIT reference candidate; sample/license/history gates remain |
| CRSP US Stock Database | Permanent PERMNO/PERMCO, active/inactive history, corporate actions and delisting returns | Public docs reviewed do not establish a complete record-known vintage clock for all mutable reference fields | Strongest return/delisting benchmark candidate | Pair with a two-clock PIT reference source if accessible |
| Norgate | Stable assetid and daily historical index membership | Effective membership is available; announcement/record-known timestamps are not | Listed/delisted coverage documented, with stated exclusions | Good separate index-defined universe; not a PIT announcement feed |
| SEC-API Mapping | Historical/delisted ticker/CUSIP/CIK mappings advertised | Daily current mapping; no historical record-vintage clock established | Yes | Not sufficient alone for PIT admission |

### FINRA

Official FINRA documentation identifies the security symbol as an exchange-assigned symbol for NMS securities (and FINRA-assigned for OTC equity securities). The weekly schema and Phase 375/385 artifacts contain no permanent listing/security key that can safely survive symbol reuse or class changes.

- Official API docs: https://developer.finra.org/docs
- Official OTC Transparency User Guide: https://www.finra.org/sites/default/files/OTC-transparency-data-user-guide-v5.pdf
- Phase 375 report: research/PHASE375_FINRA_T1_ATS_FULL_WEEKLY_REVISION_AUDIT_2026-11-13.md
- Phase 385 result: research/PHASE385_FINRA_T1_PUBLICATION_CLOCK_RESULT_2026-11-14.md

### SEC public ticker files

The SEC says its ticker/CIK/exchange files are periodically updated for EDGAR search functionality and does not guarantee their accuracy or scope. They are not an effective-dated historical security master. EDGAR's filing archives can support event discovery and CIK continuity, but a CIK is an issuer/filer identity, not a unique share-class/listing identifier.

- SEC access to EDGAR data: https://www.sec.gov/search-filings/edgar-search-assistance/accessing-edgar-data
- SEC Webmaster FAQ: https://www.sec.gov/about/webmaster-frequently-asked-questions

### Massive All Tickers (formerly Polygon)

Massive documents a historical-date All Tickers endpoint from 2003-09-10, including inactive/delisted records. Its own knowledge-base article explicitly cautions that a historical-date response is effective-dated but not a copy of the record as known on that historical date: current-maintained records can carry a later last_updated_utc. It also states that no single permanent identifier survives every US-stock security change; share-class FIGI is preferred when present, with CIK+ticker fallback, but FIGIs can change and older rows often lack FIGI/type/exchange fields.

This is a useful candidate for a secondary effective-date cross-check, not a strict PIT record-vintage source. Plan coverage also matters: the free Stocks Basic plan is limited to two years of ticker-reference history; full history requires a paid plan. No API key, plan or sample was acquired.

- All Tickers: https://massive.com/docs/rest/stocks/tickers/all-tickers
- Historical security-master limitations: https://massive.com/knowledge-base/article/does-massive-have-a-downloadable-security-master
- Plan history: https://massive.com/knowledge-base/article/how-much-historical-stock-data-does-massive-have

### Databento

The documented Security Master provides listing-level listing_id, security-level security_id, issuer-level issuer_id, ts_record and ts_effective, security type, listing/delisting dates, CUSIP, FIGI and CIK. This is the clearest public documentation of separate record-known and effective clocks among the reviewed candidates.

Still required before admission: confirm 2016–present US coverage, historical corrections/vintages, class-share symbology, exchange/listing completeness, delisted/relisted lifecycle, and license/use rights. Public history-start descriptions have differed; do not assume coverage until a sample or written specification is available.

- Security Master schema: https://databento.com/docs/schemas/security-master
- Security Master API: https://databento.com/docs/api-reference-data

### CRSP and Norgate

CRSP remains the preferred return/delisting benchmark if access exists because of permanent identifiers and active/inactive return history. Norgate remains the strongest practical alternative for a separate index-defined universe because it documents stable asset IDs and daily historical constituent membership. Neither should be represented as a full record-known PIT reference feed based only on the public documentation reviewed here.

See Phase 97 for the prior detailed audit:
research/PHASE97_PIT_SECURITY_MASTER_AND_BROAD_UNIVERSE_SOURCE_RERANK_2026-11-05.md.

## Decision and next gate

1. Do not join FINRA ATS to prices by ticker alone.
2. Keep the 209-week Phase 385 date-level clock and Phase 375 revision quarantine as necessary but insufficient gates.
3. If a no-cost feasibility sample becomes available, compare historical FINRA symbols against a reference source using a stratified sample of ticker changes, symbol reuse, multiple share classes, ADRs, mergers, delistings and relistings. Record unmatched/ambiguous rows; do not fuzzy-resolve them.
4. For strict PIT admission, require both an effective date and a record-known/first-seen timestamp (or an explicit conservative bound) for every mutable identity field.
5. Require active and inactive price history, corporate actions and terminal/delisting returns.
6. Require historical universe eligibility to be reconstructed from a rule frozen before return inspection. The original F80 335-name selection rule remains unrecovered; a security master cannot restore names omitted by that selection.
7. If F80's original universe remains unrecoverable, a separate index-defined or broad-exchange universe may be researched, but it must have its own frozen eligibility and validation protocol. It must not be called a reconstruction of F80.

**Current authorization:** no FINRA return/alpha test. No vendor contact, purchase or acquisition. F80 remains frozen; no capital, exposure, universe, parameter or production changes. The consumed legacy holdout remains unavailable.
