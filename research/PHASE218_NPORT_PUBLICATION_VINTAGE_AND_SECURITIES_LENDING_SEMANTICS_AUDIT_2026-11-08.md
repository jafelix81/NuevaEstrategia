# Phase 218 — SEC N-PORT publication vintage and securities-lending semantics audit

**Audit date:** 2026-11-08  
**Status:** PUBLICATION_AND_FIELD_SEMANTICS_AUDIT_PASS_NO_ALPHA

## Executive decision

N-PORT remains a conditional source candidate, but two distinct constructs must be kept separate:

1. **Lagged public fund short exposure:** a fund's disclosed short payoff positions at the report date, revealed materially later.
2. **Fund-reported securities-lending supply:** holdings that the fund itself has lent, reported through Item C.12.

Neither is a direct measure of market-wide short interest, securities-borrow demand, beneficial-owner conviction, or an executable institutional order. No alpha test is authorized.

## 1. Official archive coverage: correct the catalog discrepancy

The current SEC Form N-PORT Data Sets page lists **28 quarterly archives from October 2019 through September 2026**, including 2026 Q3 (440.95 MB). The page was last reviewed/updated September 30, 2026.

The Data.gov catalog page still lists **27 resources through 2026 Q2**. It is one quarterly archive behind the current SEC page. Phase 191's 28-quarter count is therefore consistent with the current SEC source; the older Data.gov catalog should not be used as the sole current coverage inventory.

This phase verified the official page metadata and links, not the bytes of the 2026 Q3 ZIP. No archive was downloaded or hashed.

Sources:
- SEC current archive page: https://www.sec.gov/data-research/sec-markets-data/form-n-port-data-sets
- Data.gov catalog: https://catalog.data.gov/dataset/form-n-port-data-sets

## 2. Reporting frequency is not public-disclosure frequency

The SEC describes N-PORT as monthly portfolio reporting, but the public data regime remains quarterly as of this audit:

- Funds report monthly portfolio holdings.
- The first and second months of a fund's fiscal quarter are not publicly disclosed under the current regime.
- The third-month report is made public upon filing.
- The SEC bulk data sets are updated quarterly.
- Documents filed after 5:30 p.m. Eastern on the last business day of a quarter are included in the next quarterly posting.

The 2024 amendments that would increase the frequency and timeliness of public N-PORT reporting were delayed on April 22, 2025. The delayed effective/compliance date is November 17, 2027 for larger fund groups and May 18, 2028 for smaller groups. We must not assume monthly public N-PORT availability in 2026.

Sources:
- SEC archive page: https://www.sec.gov/data-research/sec-markets-data/form-n-port-data-sets
- Data.gov rights description: https://catalog.data.gov/dataset/edgar-form-n-port
- Federal Register, April 22, 2025: https://www.govinfo.gov/content/pkg/FR-2025-04-22/html/2025-06861.htm

## 3. Filing-lag pilot: 19 SEC filing-index records

A purposive, search-indexed sample of 19 NPORT-P filing-index pages across 2020–2025 shows report-date-to-filing-date lags of:

- Minimum: **49 calendar days**
- Median: **58 calendar days**
- Maximum: **60 calendar days**

This is a feasibility sample, not a random or representative sample of all funds or filings. It establishes that the observed public snapshot is commonly about seven to nine weeks old at filing; it does not establish the population distribution.

The complete accession-level manifest and acceptance timestamps are in phase218_nport_publication_vintage_and_lending_audit.json.

For a daily strategy:
- Never use REPORT_DATE as the knowledge date.
- Preserve the EDGAR accession and acceptance timestamp.
- Until first public receipt is independently captured, use the first full regular trading session after acceptance as a conservative candidate availability boundary.
- Treat report-to-filing lag as an explicit feature/stratification variable, not as a constant 58-day offset.

## 4. N-PORT table semantics: short positions are not securities lending

The SEC N-PORT README defines the relevant tables and keys:

### Fund-reported holdings
FUND_REPORTED_HOLDING is keyed by ACCESSION_NUMBER + HOLDING_ID. It contains:
- PAYOFF_PROFILE (long, short, N/A)
- BALANCE and UNIT
- CURRENCY_VALUE and PERCENTAGE
- issuer CUSIP and other identifiers, including ISIN and ticker where supplied

This supports parsing a fund-reported short payoff position. It does not identify the fund's beneficial-owner rationale, nor does it establish that the position is a directional short rather than a hedge or relative-value leg.

### Securities lending
SECURITIES_LENDING is keyed by HOLDING_ID and contains:
- IS_LOAN_BY_FUND
- LOAN_VALUE

These fields describe whether the fund has lent a portion of that holding and the value of the securities on loan. This is **fund-reported lending supply**, not the fund's borrowed short inventory and not market-wide borrow demand or utilization.

### Borrowers
BORROWER is keyed by ACCESSION_NUMBER + BORROWER_ID and reports borrower NAME, LEI, and AGGREGATE_VALUE, defined as the aggregate value of all securities on loan to that borrower. The README does not document a security-level borrower-to-HOLDING_ID link. Do not allocate this aggregate borrower value to individual stocks.

The README also states that bulk data are as-filed, include amendments, and may contain redundancies, inconsistencies, or discrepancies relative to prior submissions and other publication formats. Preserve each accession/amendment as a separate vintage; do not overwrite earlier filings by report date.

Source: https://www.sec.gov/files/nport_readme.pdf

## 5. Phase 217 evidence boundary

The ACAP Strategic Fund filing 0001145549-25-033457 has report date 2025-03-31 and was accepted 2025-05-28 at 16:04:35 ET (58 calendar days after report date). Its SEC-hosted XSLT-rendered primary document was inspected.

Phase 217's 23 short rows remain a **selected documentary pilot**, not an exhaustive parse or prevalence estimate:
- Raw submission SHA-256: not verified.
- Raw primary XML SHA-256: not verified.
- Complete holdings parse: not established.
- First public receipt capture: not verified.
- Broad-universe security identity: not established.

The rendered SEC HTML view is useful for inspection, but it is not a substitute for downloading and hashing the original raw submission and XML.

Sources:
- Filing index: https://www.sec.gov/Archives/edgar/data/1467631/000114554925033457/0001145549-25-033457-index.html
- SEC-hosted rendered primary document: https://www.sec.gov/Archives/edgar/data/1467631/000114554925033457/xslFormNPORT-P_X01/primary_doc.xml

## 6. Research decisions and next gates

Keep two separately named hypotheses:

- H-NPORT-SHORT: changes in public fund-reported short equity exposure, lagged by the actual filing/acceptance time.
- H-NPORT-LEND: changes in fund-reported security lending supply for individual holdings.

Do not:
- Treat either as market-wide short interest.
- Treat short payoff as proof of directional bearish conviction.
- Treat the borrower aggregate as security-level borrow demand.
- Deduplicate amendments by report date or overwrite as-filed vintages.
- Use report date as the signal-availability date.

Before any return test:
1. Retrieve and SHA-256 hash the complete raw submission, primary XML, and index metadata for the stratified Phase 192 sample.
2. Parse all holdings and lending rows, not selected excerpts.
3. Reconcile accession, registrant, series, report date, filing date, and acceptance timestamp.
4. Build amendment lineage while preserving each as-filed vintage.
5. Establish effective-dated security/listing identity, including inactive and delisted securities.
6. Estimate eligible-filing and US common-equity coverage across the broad PIT universe.
7. Only then consider a preregistered chronological test against frozen LTM/F80 with identical exposure, costs, bootstrap/LOO and untouched OOS discipline.

**Current result:** no alpha test, no holdout use, no production change, no data purchase, no vendor contact. F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen. Holdout remains CONSUMED_NOT_PRISTINE.

## Reproducibility

- Structured evidence: phase218_nport_publication_vintage_and_lending_audit.json
- Deterministic validator: phase218_nport_publication_vintage_and_lending_audit.py
- Regression tests: test_phase218_nport_publication_vintage_and_lending_audit.py

The validator recomputes report-to-filing calendar-day lags from the accession-level manifest and checks the explicit non-admission controls. It does not download SEC data or claim raw-file integrity.
