# Phase 279 — SEC Insider Transactions bulk-history and PIT feasibility gate

**Date:** 2026-11-11 UTC  
**Status:** DOCUMENTED_LONG_HISTORY_CANDIDATE_SCHEMA_AND_PIT_GATES_OPEN  
**Control:** F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen.  
**Scope:** official SEC data-library page, current download inventory, and published data-set readme. No archive bytes were downloaded, no SEC request was sent, and no return test was run.

## Executive finding

The SEC Insider Transactions Data Sets provide a materially broader historical route for the existing Form 4 hypothesis than the two-quarter Phase 39 sample. The SEC currently lists **83 quarterly archives from 2006Q1 through 2026Q3**, covering January 2006–September 2026. Summing the 83 sizes displayed on the SEC page gives approximately **887.43 MB** of ZIP files (listed-size estimate, not downloaded-byte measurement).

The files contain as-filed structured submissions for Forms 3, 4 and 5, including amendments. The published schema includes submission, reporting-owner, non-derivative/derivative transactions and holdings, footnotes and owner signatures. This is a plausible low-cost way to expand Phase 271's high-specificity Form 4 candidate screen across roughly 20.75 years.

**This is the same EDGAR Form 3/4/5 source family, not an independent confirmation source.** The new value is historical breadth and a structured bulk delivery path. No alpha or strict PIT admission follows from archive availability.

## 1. Historical coverage and scale

| Item | SEC page observation |
|---|---:|
| First listed period | 2006Q1 |
| Latest listed period | 2026Q3 |
| Quarterly archives | 83 |
| Sum of displayed ZIP sizes | ~887.43 MB |
| Smallest listed ZIP | 7.59 MB |
| Largest listed ZIP | 16.51 MB |
| Update cadence | Quarterly |
| Page last reviewed | 2026-09-30 |

The SEC says the data are extracted from the XML portion of Forms 3, 4 and 5, presented as filed, and updated quarterly. It explicitly warns that the flattened data may contain redundancies, inconsistencies and discrepancies and are not a substitute for the original filings.

## 2. What the schema supports

The published readme documents eight UTF-8 tab-delimited tables and their row keys:

| Table | Documented key | Research value |
|---|---|---|
| SUBMISSION | ACCESSION_NUMBER | Form family, issuer, filing date, period and original-submission date |
| REPORTINGOWNER | ACCESSION_NUMBER + RPTOWNERCIK | Reporting-person identity and relationship |
| NONDERIV_TRANS | ACCESSION_NUMBER + NONDERIV_TRANS_SK | Table I transaction rows |
| NONDERIV_HOLDING | ACCESSION_NUMBER + NONDERIV_HOLDING_SK | Table I holding rows |
| DERIV_TRANS | ACCESSION_NUMBER + DERIV_TRANS_SK | Table II derivative transactions |
| DERIV_HOLDING | ACCESSION_NUMBER + DERIV_HOLDING_SK | Table II derivative holdings |
| FOOTNOTES | ACCESSION_NUMBER + FOOTNOTE_ID | Transaction explanations and plan/private/mechanical qualifiers |
| OWNER_SIGNATURE | ACCESSION_NUMBER + OWNERSIGNATURENAME | Signature metadata |

For the Form 4 screen, the key transaction fields include TRANS_DATE, TRANS_CODE, TRANS_ACQUIRED_DISP_CD, TRANS_SHARES, TRANS_PRICEPERSHARE, TRANS_TIMELINESS, DIRECT_INDIRECT_OWNERSHIP, NATURE_OF_OWNERSHIP and linked footnote IDs. The submission table includes DOCUMENT_TYPE, ISSUERCIK, ISSUERTRADINGSYMBOL, FILING_DATE, PERIOD_OF_REPORT and DATE_OF_ORIG_SUB.

The FOOTNOTES table makes it feasible in principle to scale Phase 271's explicit open-market/private/plan/mechanical footnote screen without first downloading every original XML document. Original filings remain necessary for adjudication and difficult cases.

## 3. Important schema and attribution limits

### 3.1 Acceptance time is not in the flattened SUBMISSION table

FILING_DATE is date-only. PERIOD_OF_REPORT is the reported event/statement date, not the public-knowledge clock. DATE_OF_ORIG_SUB is an original filing date on an amendment, not a parent accession.

A strict daily panel still needs an accession-level join to the original EDGAR filing index/header for ACCEPTANCE-DATETIME. Acceptance is an availability floor, not an exact first-public-receipt timestamp; the conservative daily rule remains the first full XNYS session after verified acceptance. No acceptance-time join was performed here.

### 3.2 Transaction rows do not carry the reporting-owner CIK

REPORTINGOWNER is keyed by accession plus owner CIK, but NONDERIV_TRANS is keyed by accession plus transaction surrogate key and has no RPTOWNERCIK column in the published schema.

For a filing with multiple reporting owners, joining transactions to owners on accession alone would create a many-to-many expansion and false owner-level attribution. Use the original ownership XML to retain the nested owner-to-transaction relationship, or exclude multi-owner accessions from owner-specific features. Do not infer transaction ownership from row order or address.

### 3.3 Security identity is incomplete

The documented non-derivative transaction table has security title but no permanent security identifier/CUSIP. The submission table has issuer CIK and issuer trading symbol, but these do not uniquely resolve historical share classes, ADRs, ticker reuse, corporate actions or delisted securities. A separate effective-dated security/class/listing master is still mandatory.

### 3.4 AFF10B5ONE is a schema-version issue and a filing-level field

The SEC page says the 2023–2025 archives were updated in July 2025 to include AFF10B5ONE and that future data sets will be processed similarly. The published readme PDF does not list this field. Therefore the archive-specific metadata/schema must be inspected before parsing; do not assume a uniform column set across all 83 files.

The checkbox is at the submission level, not a transaction-row identifier. A missing/pre-checkbox-era value is UNKNOWN, never false. A checked form flag must not be broadcast as a line-specific plan label without footnote/XML review. Even an unchecked flag does not establish discretionary intent.

### 3.5 Code P is not enough

The SEC's transaction-code description defines P as a purchase on an exchange **or from another person**. That does not by itself distinguish open-market from private purchases. The Phase 271 explicit footnote screen remains necessary. Form 4/A amendments can add transaction lines or amend existing lines; they are separate disclosure vintages and must not be counted as fresh trades by default.

## 4. Proposed next gate

Before any full ingestion or return test:

1. Acquire five stratified archives: 2006Q1, 2012Q1, 2023Q2, 2025Q3 and 2026Q3. Preserve exact ZIP bytes, SHA-256 and metadata manifests.
2. Cross-check 2012Q1 and 2026Q3 against the existing Phase 39 source artifact.
3. Validate all eight table schemas, compound-key uniqueness, row counts, accession joins, null conventions and the AFF10B5ONE column by archive era.
4. Reconcile a sample of accessions to original EDGAR filing indices and acceptance timestamps; preserve each Form 4/A as a new as-filed vintage.
5. Reproduce Phase 271's strict transaction screen using footnotes. For multiple-owner filings, parse original XML or exclude.
6. Measure issuer/security-class and historical active/delisted-universe coverage before joining returns.

If these gates pass, expand the candidate-event sample across the 83 quarters, then test only after effective-dated identity, acceptance-time, amendment and survivorship gates pass. The event unit remains issuer × accession/disclosure batch, not transaction row. Compare against frozen LTM/F80 with identical eligible names, signal dates, exposure, turnover and costs; use chronological OOS, time/issuer/owner-clustered bootstrap, leave-one-issuer/owner-out, multiplicity control and prospective confirmation. Do not reuse the consumed legacy holdout.

## 5. Phase 279 disposition

| Gate | Result |
|---|---|
| Official historical range and archive inventory | PASS — documentation only |
| 83-quarter count and listed-size reconciliation | PASS — page inventory calculation |
| Published table/key schema | PASS — readme documentation |
| Actual representative ZIP bytes/schema | NOT RUN |
| AFF10B5ONE archive-era reconciliation | NOT RUN |
| Accession acceptance-time join | NOT RUN |
| Multi-owner transaction attribution | NOT ESTABLISHED |
| Effective-dated security/class mapping | NOT ESTABLISHED |
| Broad active/delisted universe coverage | NOT ESTABLISHED |
| Strict PIT / alpha admission | NOT ADMITTED |

No SEC request, archive download, vendor contact, purchase, forward-return test, bootstrap/LOO, chronological OOS or holdout use occurred. The SEC_CONTACT_EMAIL secret remains absent for automated EDGAR index/header retrieval; no address was invented or used. The public ZIP archive itself was not downloaded in this phase.

**Decision:** promote the SEC bulk Insider Transactions Data Sets to the highest-priority next sample-acquisition candidate for the existing Form 4 line. This does not promote Form 4 as a signal. It materially improves the feasibility case for a broad historical candidate census, while the PIT, owner-attribution and security-identity gates remain closed.

## Sources

- SEC Insider Transactions Data Sets: https://www.sec.gov/data-research/sec-markets-data/insider-transactions-data-sets
- SEC Insider Transactions Data Sets readme: https://www.sec.gov/files/insider_transactions_readme.pdf
- SEC Release 33-11138, Rule 10b5-1 and insider-trading disclosures: https://www.sec.gov/files/rules/final/2022/33-11138.pdf
- SEC Form 4 instructions, including amendments and Rule 10b5-1 checkbox: https://www.sec.gov/about/forms/form4data.pdf
- SEC Form 4 transaction-code explanation: https://www.sec.gov/files/forms-3-4-5.pdf
