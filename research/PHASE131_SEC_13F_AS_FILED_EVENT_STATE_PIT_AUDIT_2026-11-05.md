# Phase 131 — SEC Form 13F as-filed event-state and PIT feasibility audit

**Date:** 5 November 2026  
**Status:** Official-source/schema audit complete; no 13F holdings panel or alpha test authorized.  
**Scope:** SEC Form 13F structured bulk data, accession-level EDGAR metadata, amendment semantics, manager attribution and usable knowledge time. This is distinct from Phase 129, which audits the quarterly Section 13(f) eligible-security list.

## 1. Historical coverage and reproducibility

The SEC's current Form 13F Data Sets page labels coverage **July 2013–August 2026** and exposes quarterly bulk ZIP files. The SEC's data-set specification says structured XML data begins in May 2013. The old text-based 13F format was discontinued on 20 May 2013. For a reproducible standardized panel, use the SEC bulk data from its documented start; any pre-2013 extension would require a separate legacy parser and independent validation, not silent concatenation.

The bulk data are quarterly, flattened extracts of structured EDGAR submissions, presented **as filed**. The SEC warns that the files can contain redundancies, inconsistencies and discrepancies, omit filing metadata, and are not a substitute for the underlying accession documents. The SEC refreshed all historical files into a common format on 12 March 2024 and included processing fixes for missing information-table rows and manager address codes. Preserve source ZIP hashes and the exact vintage used in every run.

**Coverage decision:** roughly 13 years of standardized quarterly structured history is feasible for exploratory research, but not a full-cycle 2000s history. Bulk dataset publication is not the knowledge timestamp for each individual filing.

## 2. The bulk dataset does not contain the required acceptance timestamp

The SEC's published schema defines:

- `SUBMISSION`: `ACCESSION_NUMBER` (primary key), `FILING_DATE`, `SUBMISSIONTYPE`, filer `CIK`, and `PERIODOFREPORT`.
- `COVERPAGE`: amendment flag/number/type, confidentiality-related fields, manager name and report type.
- `OTHERMANAGER` and `OTHERMANAGER2`: other-manager relationships.
- `INFOTABLE`: accession + row surrogate key, issuer, class, CUSIP, value, share/principal amount and type, put/call, investment discretion, other-manager sequence, and voting authority.

The bulk `SUBMISSION` table documents a filing **date**, not the EDGAR acceptance time-of-day. Therefore, a strict PIT panel must join each accession to its EDGAR filing-detail/submission metadata and preserve the exact accepted timestamp. Do not infer an intraday timestamp from `FILING_DATE`, the report quarter, or the later quarterly bulk ZIP publication.

Two live EDGAR examples demonstrate why this matters:

- Accession `0001275218-26-000008`: filing date 11 Aug 2026, but accepted 10 Aug 2026 at 18:34:09 ET; it is a 13F-HR/A restatement for 2024Q1.
- Accession `0001635409-25-000005`: filing date 14 Aug 2025, but accepted 13 Aug 2025 at 19:30:14 ET.

The operational feature-availability time must be no earlier than the accession's accepted timestamp. If accepted outside the regular session, the first eligible execution is the next regular trading session. Keep event/report quarter, filing date, accepted timestamp, and first tradable session as separate fields.

## 3. Amendment handling requires an event-state machine

The SEC bulk schema includes `ISAMENDMENT`, `AMENDMENTNO`, and `AMENDMENTTYPE`; the SEC FAQ distinguishes at least two materially different cases:

1. **Restatement:** the filer resubmits the entire corrected filing; the amendment supersedes the original.
2. **Adds-new-holdings:** the amendment contains only omitted/new entries and supplements the original.

Confidential-treatment denials/expirations can also lead to later add-only amendments that disclose previously omitted positions. Multiple amendments may exist for the same report quarter. The SEC data-set specification explicitly includes amendments as filed, rather than collapsing them into one canonical current snapshot.

Required PIT rule:

- At each accession's accepted timestamp, apply only the information actually disclosed by that accession.
- A restatement replaces the prior reported state only from its own accepted timestamp; never rewrite the historical state before that time.
- An add-only amendment supplements the then-public state from its own accepted timestamp.
- A confidentiality-release amendment adds the newly disclosed positions from that amendment's accepted timestamp; do not backdate them to quarter-end or the original filing.
- Retain every accession and its raw filing hash. Never choose the latest amendment using present-day knowledge when reconstructing an earlier date.

The bulk files alone are not sufficient to infer every amendment's legal/economic effect without inspecting the cover-page fields and, for ambiguous or malformed rows, the original accession documents.

## 4. Manager attribution and double-counting risks

Form 13F is filed by institutional investment managers exercising investment discretion over at least $100 million in Section 13(f) securities. It is not a census of all investors. The SEC permits aggregation of positions under sole or shared discretion, and the filing identifies other included managers and shared-discretion relationships.

Do not sum every filer row as independent beneficial ownership. Build an accession-level manager graph using filer CIK, Form 13F file number, `OTHERMANAGER` / `OTHERMANAGER2`, the information-table `OTHERMANAGER` sequence and investment-discretion field. Quarantine unresolved shared-manager relationships. Keep manager identity distinct from the issuer/security identity.

Additional selection/incompleteness:

- Positions are long-only disclosures; short equity positions are not reported or netted against longs.
- Held puts/calls may be reported, but written options are not. The option row identifies the underlying security CUSIP and a put/call flag; it is not an option-contract tape with strike/expiry/greeks.
- A filer may omit a position when it is both below 10,000 shares and below $200,000 fair value.
- Confidential treatment can delay public disclosure.
- The $100 million filing threshold and Section 13(f) eligible-security list exclude parts of the market and investor population.

Consequently, 13F cannot be interpreted as net institutional positioning, complete ownership, real-time flow, or proof of informed trading.

## 5. Candidate research use — conditional, not yet approved

If the PIT and identity gates are later satisfied, the only plausible initial hypothesis is a **delayed public holdings-change/manager-breadth feature**, not transaction flow:

- Compare reported share quantities, not only dollar values, to reduce mechanical price-chasing.
- Separate original filings, restatements, add-only amendments and confidential-release amendments.
- Use accession acceptance time and next tradable session.
- Aggregate only after resolving shared discretion and manager duplication.
- Normalize for splits, mergers, class changes, CUSIP transitions and shares outstanding using an effective-dated security master.
- Distinguish manager entry/exit, position-size change, and simple market-value change.
- Test whether the information adds to frozen LTM/F80 after publication, rather than whether quarter-end holdings correlate with returns already earned during the quarter.

This remains a hypothesis. The 45-day filing lag, incomplete short/options disclosure, confidential omissions and possible price-chasing may make the signal too stale or too weak. A failure should be archived, not retuned until it passes.

## 6. Decision and next gates

1. **PIT timestamp gate:** build and test an accession-to-acceptance-time crosswalk. Missing acceptance times are not imputed from filing date.
2. **Amendment gate:** unit-test restatement replacement, add-only supplementation, multiple amendments and confidentiality-release additions using actual SEC accessions.
3. **Manager gate:** reconcile shared-discretion and other-manager relationships without duplicate economic exposure.
4. **Security identity gate:** the existing Phase 128 result shows internal 13D/G CUSIP repetition is not a broad security master. An independent, effective-dated crosswalk remains mandatory.
5. **Coverage gate:** measure CUSIP/security coverage against the broad point-in-time universe, including delisted securities; the 13(f) official list from Phase 129 is only an eligibility cross-check.
6. Only after all gates pass may a preregistered delayed-13F hypothesis be tested chronologically against frozen LTM/F80 with identical exposure/costs, bootstrap and leave-one-out analysis.

**No 13F holdings backtest, forward-return test, alpha claim, vendor purchase or production change was made.** Phase 129 remains a separate live 13(f) list audit. `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen.

## Official sources

- SEC, [Form 13F Data Sets](https://www.sec.gov/data-research/sec-markets-data/form-13f-data-sets) — documented bulk history, quarterly publication, as-filed status and format refresh.
- SEC, [Form 13F Data Sets technical documentation](https://www.sec.gov/files/form_13f.pdf) — table definitions, keys, fields and amendment metadata.
- SEC, [Frequently Asked Questions About Form 13F](https://www.sec.gov/rules-regulations/staff-guidance/frequently-asked-questions-about-form-13f) — filing deadlines, manager scope, options/short limitations, de minimis omissions and amendment semantics.
- SEC EDGAR, [0001275218-26-000008](https://www.sec.gov/Archives/edgar/data/1275218/000127521826000008/0001275218-26-000008-index.htm) — accepted 10 Aug 2026 18:34:09 ET; filing date 11 Aug 2026; 2024Q1 restatement.
- SEC EDGAR, [0001635409-25-000005](https://www.sec.gov/Archives/edgar/data/1635409/000163540925000005/0001635409-25-000005-index.htm) — accepted 13 Aug 2025 19:30:14 ET; filing date 14 Aug 2025.
- SEC EDGAR, [0001011438-25-000243](https://www.sec.gov/Archives/edgar/data/1654111/0001011438-25-000243-index.html) — 2025Q1 example with accepted timestamp and filing date on the same calendar date.
