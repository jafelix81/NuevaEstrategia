# Phase 39 — SEC Form 4 insider-transaction feasibility gate

Date: 2026-10-28 (PIT gate revalidated)

## Objective
Assess whether SEC insider transactions can provide a security-level, point-in-time Smart Money candidate for the frozen universe without look-ahead.

## Fresh official-source verification
The SEC Insider Transactions Data Sets currently cover January 2006 through September 2026 and are published quarterly. The SEC page lists actual downloadable quarterly ZIP files, including 2026 Q3 and 2012 Q1. The data are extracted from the as-filed XML portions of Forms 3, 4 and 5. SEC also notes that documents filed after 5:30 PM ET on the last business day of a quarter roll into the subsequent quarterly posting.

## PIT rule
The quarterly dataset publication date is not the event-level knowledge date. The flat files contain `ACCESSION_NUMBER`, `FILING_DATE`, and `PERIOD_OF_REPORT`, but the representative schemas do not contain an event-level `ACCEPTANCE-DATETIME`/filing timestamp. Therefore `FILING_DATE` is usable only as a conservative date-level PIT boundary unless we reproducibly join each accession to EDGAR filing metadata containing acceptance time.

Form 4 instructions state that a Form 4 is due before the end of the second business day following the transaction and is deemed filed on the date received by the Commission. Therefore transaction date defines the economic event, while filing acceptance/publication time defines when the information becomes public.

## Actual-file audit — PASSED
GitHub Actions run `40606706518` completed successfully on 2026-10-28. Artifact: `phase39-sec-form4-actual-file-audit` (22.9 MB).

Representative files audited:
- 2012 Q1: `2012q1_form345.zip`
- 2026 Q3: `2026q3_form345.zip`

Both periods contain the expected historical flat-file family, including `SUBMISSION.tsv`, `REPORTINGOWNER.tsv`, `NONDERIV_TRANS.tsv`, `DERIV_TRANS.tsv`, holdings, footnotes, signatures and metadata/readme files.

Core fields confirmed in both periods include issuer CIK/name/trading symbol, accession number, filing date, transaction date, transaction code, shares, price, acquired/disposed indicator, shares owned following transaction, direct/indirect ownership, reporting-owner identity and relationship.

This establishes genuine long-history data availability and schema continuity between 2012 and 2026 for the core non-derivative transaction table.

## Accession-level PIT gate — PASSED
Representative EDGAR filing texts successfully yielded acceptance timestamps in both historical regimes:
- 2012 Q1: accession `0000920371-12-000007` → acceptance `20120131121051`;
- 2026 Q3: accession `0001709048-26-000199` → acceptance `20260731164155`.

The initial parser expected XML-tagged header fields, while EDGAR text headers use label-style fields in these examples. The parser was corrected to accept both forms. Corrected workflow run `40671502886` passed and produced artifact `phase39-sec-form4-pit-acceptance-gate`; the latest revalidation run `40671611979` also passed all PIT steps and produced the same artifact class. This confirms the accession-level acceptance-time join is reproducible rather than a one-off successful parse.

## Hypotheses — explicitly not assumed to be smart money
H1: discretionary open-market insider purchases contain incremental information beyond F80/LTM.
H2: clustered purchases across multiple insiders are more informative than isolated purchases.
H3: net insider buying after excluding grants, exercises, tax withholding, gifts and other non-discretionary codes is more informative than raw Form 4 activity.
H4: insider activity may predict returns only because it follows prior returns; residualized tests must distinguish information from return-chasing.

## Required gates before any return test
1. Security-level issuer/ticker mapping for the frozen universe.
2. Historical coverage sufficient for an apples-to-apples test; no reduced-universe alpha test if coverage is inadequate.
3. Reproducible filing acceptance/publication timestamp or an explicitly conservative filing-date implementation.
4. Transaction-code filtering separating discretionary open-market buys/sells from grants, awards, option exercises, tax withholding, gifts and other mechanical transactions.
5. No use of holdings reported after the transaction as if known at transaction time.
6. Chronological validation only; no full-sample feature selection.
7. If the gate passes, compare incremental information against frozen LTM/F80 using identical exposure, realistic costs, bootstrap/LOO and a genuinely untouched OOS period.

## Kill conditions
- Inadequate frozen-universe coverage.
- No reproducible filing-time PIT boundary and no conservative alternative.
- Signal vanishes after excluding non-discretionary transactions.
- Signal is explained by prior returns/volume/volatility.
- Apparent alpha exists only in-sample or fails chronological OOS/bootstrap discipline.

## 13D/13G status
The latest Phase 35 crosswalk audit remains blocked at document/event-date extraction. The run resolved 19,721 filings across 303 issuers but recovered zero actual event dates; the apparent coverage count was a boolean-counting artifact. SEC archive requests also generated material 429 errors. This branch is not authorized for alpha testing until robust structured/document extraction with rate-limit controls is demonstrated.

## Status
**FORM 4: SCHEMA/HISTORY GATE PASSED; ACCESSION-LEVEL PIT GATE PASSED; NEXT: FROZEN-UNIVERSE SECURITY/TICKER COVERAGE + TRANSACTION-CODE FILTERING.**

**13D/13G: DOCUMENT-EXTRACTION GATE FAILED/PENDING REPAIR; NO ALPHA TEST AUTHORIZED.**

The frozen `F80_TOP20_PARTIAL50_BASELINE_C20` remains unchanged.
