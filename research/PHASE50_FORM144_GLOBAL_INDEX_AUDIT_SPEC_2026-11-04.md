# Phase 50 — SEC Form 144 global-index feasibility audit
Date: 2026-11-04
Branch: phase50-sec-form144-feasibility
Status: preregistered technical validation; no return test authorized.

## Why v2 is not a source-coverage pass

The v2 EFTS CIK-query pilot completed technically, but its 50-document deterministic XML sample contained 50/50 Form 144/A amendments and zero original Form 144 notices. The 100% XML parsing and field-presence rates therefore validate the sampled amendment documents only. They do not validate the original-notice population or establish complete subject-issuer coverage.

The v2 artifact also classified all 50 approximate sale dates as unknown because the parser accepted ISO dates only. The actual XML values use EDGAR's MM/DD/YYYY format. An independent reparse of the artifact found 34/50 approximate sale dates before the filing date and 16/50 on the filing date. Notice dates were 48/50 on the filing date and 2/50 one day earlier. These are date relations only; they do not prove execution.

## Research question

Can the SEC global quarterly master index identify the complete Form 144 and 144/A accession population, and can filing-detail pages plus structured XML reliably distinguish Subject issuer, Reporting person/filer, accepted timestamp, and amendment references?

## Method

1. Download the official SEC quarterly `master.idx` for a fixed quarter.
2. Parse every Form 144 and 144/A row and group all rows by accession.
3. Preserve the master-index CIK/name pairs and the archive-path CIK embedded in the filename as separate identifiers.
4. Fetch every filing-detail index page using the exact archive path from the master index first.
5. Parse Subject CIK/name, Reporting CIK/name (or Filed by where that label is used), accession, form, filing date, and accepted timestamp.
6. Match Subject CIK to current SEC ticker/exchange/mutual-fund CIK candidates. This is discovery coverage only, not historical PIT membership.
7. Select a deterministic XML validation sample stratified by original Form 144 versus Form 144/A and target versus non-target Subject CIK.
8. Parse primary_doc.xml and compare XML issuerCik with index Subject CIK. Keep XML filer CIK, index Reporting CIK, archive-path CIK, master-index CIKs, and accession prefix separate.
9. Parse EDGAR dates in MM/DD/YYYY, MM-DD-YYYY, and ISO forms. Record approximate-sale-date relation to filing date descriptively; never call it proof of execution or KnowledgeDate.
10. Retain previousAccessionNumber as a prior-filing reference, not an assumed immediate predecessor.

## Fixed pilot

- Quarter: 2025Q1.
- Candidate universe: frozen 335-name list.
- Current CIK mappings: official SEC company ticker, exchange and mutual-fund files, plus a documented fallback mapping where necessary.
- XML sample: up to 25 target and 25 non-target records per form.
- No forward returns, no event-window returns, no alpha testing.

## Pre-registered technical gates

- At least 300 of 335 candidate tickers have at least one current CIK candidate.
- The global master index contains both 144 and 144/A.
- At least 25 XML sample records per form (or all available if the quarter has fewer).
- At least 95% filing-index page retrieval.
- At least 95% Subject CIK parse coverage.
- At least 95% accepted-timestamp coverage.
- At least 95% agreement between master-index and filing-index form/date.
- At least 95% XML parse success, XML Subject-vs-issuer CIK agreement, and XML form agreement.
- At least 95% presence of issuer, seller, class, quantity, aggregate value, approximate sale date and notice date in parsed XML.

These gates validate a quarter-specific public-data ingestion route only. They do not certify complete historical coverage, current CIK mapping as PIT, historical F80 membership, actual sale execution, seller-group continuity, or predictive value.

## After a pass

- Extend the global-index census quarter-by-quarter from 2023Q2 through the latest complete quarter.
- Reconcile quarterly master-index accessions against EDGAR filing-index Subject/Reporting metadata.
- Measure target-subject coverage by form, year, ticker, and issuer lifecycle; retain delisted and predecessor securities.
- Resolve amendments and deduplicate original/amended notices without treating previousAccessionNumber as the immediate predecessor.
- Add seller relationship, security class, proposed size relative to float/ADTV, prior sales, and 10b5-1 remarks only where reliably populated.
- Reconstruct historical F80 membership before any signal panel.
- Only then preregister whether prospective Form 144 planned-sale information adds incremental information beyond Form 4 and frozen LTM/F80, controlling for price run-up, earnings windows, vesting/exercises, repeated seller/issuer clusters, costs, identical exposure, chronological OOS, block bootstrap, issuer-clustered uncertainty and LOO.

## Decision

Form 144 remains conditional. v2 is a technical amendment-parser pilot only; global-index v3 must pass before historical coverage is considered adequate. F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen.
