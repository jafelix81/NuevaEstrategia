# Phase 39 — SEC Form 4 insider-transaction feasibility gate

Date: 2026-10-27 (actual-file gate completed)

## Objective
Assess whether SEC insider transactions can provide a security-level, point-in-time Smart Money candidate for the frozen universe without look-ahead.

## Fresh official-source verification
The SEC Insider Transactions Data Sets currently cover **January 2006 through September 2026** and are published quarterly. The SEC page lists actual downloadable quarterly ZIP files, including 2026 Q3 and 2012 Q1. The data are extracted from the as-filed XML portions of Forms 3, 4 and 5. SEC also notes that documents filed after 5:30 PM ET on the last business day of a quarter roll into the subsequent quarterly posting.

Primary source: https://www.sec.gov/data-research/sec-markets-data/insider-transactions-data-sets
Documentation: https://www.sec.gov/files/insider_transactions_readme.pdf

## PIT rule
The quarterly dataset publication date is **not** the event-level knowledge date. The flat files contain `ACCESSION_NUMBER`, `FILING_DATE`, and `PERIOD_OF_REPORT`, but the representative schemas do **not** contain an event-level `ACCEPTANCE-DATETIME`/filing timestamp. Therefore `FILING_DATE` is usable only as a conservative date-level PIT boundary unless we reproducibly join each accession to EDGAR filing metadata containing acceptance time.

Form 4 instructions state that a Form 4 is due before the end of the second business day following the transaction and is deemed filed on the date received by the Commission. Therefore transaction date defines the economic event, while filing acceptance/publication time defines when the information becomes public.

## Actual-file audit — COMPLETED
GitHub Actions run `40606706518` completed successfully on 2026-10-28. Artifact: `phase39-sec-form4-actual-file-audit` (22.9 MB).

Representative files audited:
- **2012 Q1**: `2012q1_form345.zip`
- **2026 Q3**: `2026q3_form345.zip`

Both periods contain the expected historical flat-file family:
- `SUBMISSION.tsv`
- `REPORTINGOWNER.tsv`
- `NONDERIV_TRANS.tsv`
- `DERIV_TRANS.tsv`
- holdings, footnotes, signatures and metadata/readme files.

Key schema fields confirmed in both periods:
- issuer CIK/name/trading symbol in `SUBMISSION.tsv`;
- `ACCESSION_NUMBER` and `FILING_DATE`;
- transaction date (`TRANS_DATE`);
- transaction code (`TRANS_CODE`);
- transaction shares and price per share;
- acquired/disposed indicator;
- shares owned following transaction;
- direct/indirect ownership;
- reporting-owner identity and relationship.

This establishes genuine long-history data availability and the fields required to construct economically meaningful insider-transaction hypotheses. It also demonstrates schema continuity between 2012 and 2026 for the core non-derivative transaction table.

## PIT consequence
The actual-file audit **passes schema/history feasibility but does not yet pass the final PIT gate**. The next step is a reproducible accession-level join from `SUBMISSION.tsv` to EDGAR filing metadata to recover acceptance datetime. Until that is demonstrated, any return test must not use intraday timing and should use a conservative next-trading-session implementation only if the filing-date boundary is explicitly defined.

## Hypotheses — explicitly not assumed to be "smart money"
H1: discretionary open-market insider purchases contain incremental information beyond F80/LTM.
H2: clustered purchases across multiple insiders are more informative than isolated purchases.
H3: net insider buying after excluding grants, exercises, tax withholding, gifts and other non-discretionary codes is more informative than raw Form 4 activity.
H4: insider activity may predict returns only because it follows prior returns; residualized tests must distinguish information from return-chasing.

## Required feasibility gates before any return test
1. Security-level issuer/ticker mapping for the frozen universe.
2. Historical coverage sufficient for an apples-to-apples test; no reduced-universe alpha test if coverage is inadequate.
3. Reproducible filing acceptance/publication timestamp or an explicitly conservative filing-date implementation.
4. Transaction-code filtering that separates discretionary open-market buys/sells from grants, awards, option exercises, tax withholding, gifts and other mechanical transactions.
5. No use of holdings reported after the transaction as if known at transaction time.
6. Chronological validation only; no full-sample feature selection.
7. If the gate passes, compare incremental information against frozen LTM/F80 using identical exposure, realistic costs, bootstrap/LOO, and a genuinely untouched OOS period.

## Kill conditions
- Inadequate frozen-universe coverage.
- No reproducible filing-time PIT boundary and no conservative alternative.
- Signal vanishes after excluding non-discretionary transactions.
- Signal is explained by prior returns/volume/volatility.
- Apparent alpha exists only in-sample or fails chronological OOS/bootstrap discipline.

## Latest Phase 35 crosswalk result — 2026-10-28
Run `40644893540` completed successfully and produced artifact `phase35-13dg-pit-event-crosswalk-audit` (581,390 bytes).

The actual audit covered the frozen 335-name universe using issuer-specific SEC submissions plus a historical CIK crosswalk:
- 307 CIKs selected;
- 27 unresolved tickers;
- 20,266 candidate filings;
- 19,721 resolved filings across 303 issuers;
- 14,219 amendments;
- 545 document-resolution errors, predominantly SEC HTTP 429 responses;
- **0 resolved `event_date` values**.

The parser's own output correctly records `filing_date` as the PIT knowledge date. The apparent `event_date_available: 19721` in its field-coverage counter is a counting artifact because the counter counts boolean `False` as a non-null value; the actual event-date count is zero. The extraction pattern currently searches only for the literal `DATE OF EVENT WHICH REQUIRES FILING` label, which is not robust across the heterogeneous 13D/13G document formats encountered.

### Decision
13D/13G is **not authorized for alpha testing yet**. The current result is a parser/document-format failure, not evidence for or against the economic hypothesis. Because event/report-date extraction is incomplete and SEC archive requests also generated material 429 errors, the source does not currently satisfy the reproducible historical-event gate needed for a clean security-level test.

The correct next action is either a robust structured/XML-aware extraction of event/report dates with rate-limit controls, or archival/secondary official SEC data that supplies those fields reproducibly. No return test should be built on the current 13D/13G output.

## Phase 39 PIT parser correction — 2026-10-28
The first EDGAR PIT gate run (`40667764722`) successfully downloaded both representative filing texts and recovered valid 14-digit acceptance timestamps:
- 2012 Q1 representative filing: `20120131121051`;
- 2026 Q3 representative filing: `20260731164155`.

The run nevertheless failed because the parser expected XML tags such as `<ACCESSION-NUMBER>` and `<ACCEPTANCE-DATETIME>`. The actual EDGAR text header uses label-style fields in these representative filings, so accession and filing-date extraction returned null even though acceptance datetime was present. This is a **parser-format defect, not a source/PIT failure**.

The Phase 39 workflow was corrected in commit `9b9f128d729a5ce6a539075514a921f13006305` to accept both XML-tagged and label-style EDGAR header forms for accession, filing date and acceptance datetime. The workflow retains the SEC descriptive User-Agent, retry policy, concurrency protection, and exact 14-digit acceptance validation.

No alpha test is authorized yet. The corrected workflow must pass on both historical representatives before the accession-level PIT gate is considered complete.

## Status
**Form 4: SCHEMA/HISTORY GATE PASSED; PIT JOIN GATE CORRECTED AND PENDING RE-RUN.**

**13D/13G: DOCUMENT-EXTRACTION GATE FAILED/PENDING REPAIR; NO ALPHA TEST AUTHORIZED.**

The frozen `F80_TOP20_PARTIAL50_BASELINE_C20` remains unchanged.
