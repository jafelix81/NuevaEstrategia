# Phase 35 — 13D/13G Event Normalization Specification

Updated: 2026-11-03 (subject-issuer attribution correction)

## Purpose
Build a deterministic subject-issuer and reporting-person event panel before any return test. This is a preregistration guardrail; the previous 20,266-row artifact is a retrieval output, **not a certified issuer-level panel**.

## Current data-gate status: FAIL / NOT CERTIFIED
- Frozen universe: 335 names.
- Ticker-to-CIK candidates selected: 307; 27 unresolved.
- Latest artifact: run 41652405132, artifact 13256930771, 20,266 retrieved rows.
- The prior summary's 303 "unique issuers" is not validated: the base script writes the query CIK into issuer_cik and the old parser falls back to that CIK when it cannot find a legacy CENTRAL INDEX KEY label.
- At least one 13G XML row is demonstrably misattributed: TFC / CIK 0000092230 is assigned to a filing whose XML subject issuer is Federated Hermes ETF Trust / CIK 0001849998.
- 7,858 XML 13G rows require subject-CIK re-extraction; 437 XML 13D rows and legacy HTML/TXT rows also require validation.
- filing_date remains the conservative KnowledgeDate, but only after the subject issuer is verified. event_date is not KnowledgeDate and is not PIT-certified.

## Required identity model
Keep the following identifiers separate on every filing:
1. query_cik: CIK used to query the SEC submissions endpoint.
2. archive_path_cik: CIK used in the archive URL for the retrieved document.
3. submission_cik: first ten digits of accession, retained only as submission traceability.
4. subject_issuer_cik: parsed from XML issuerCIK/issuerCik or SEC filing-index Subject metadata.
5. filed_by_cik: parsed from SEC filing-index Filed by metadata.
6. reporting_person_ciks / reporting_person_names: parsed from the filing body.

Never substitute query CIK, archive-path CIK, accession prefix, or Filed-by CIK for subject issuer or the complete reporting group.

## Schema-specific parsing rules
- **13D XML:** parse all reportingPersonInfo nodes and the issuer fields from XML, not from display labels alone.
- **13G XML:** parse issuerCik, issuerCusip, eventDateRequiresFilingThisStatement, and previousAccessionNumber. Its reporting person is commonly represented under coverPageHeaderReportingPersonDetails, with fields including reportingPersonName, reportingPersonBeneficiallyOwnedAggregateNumberOfShares, classPercent, voting/dispositive power and repeated typeOfReportingPerson. Do not expect only the 13D reportingPersonInfo structure.
- **Legacy HTML/TXT:** preserve table/line boundaries; extract every reporting-person cover-page block, CUSIP/class, event date, Item 4 purpose where present, joint-filing agreement and explicit accession references. Do not assume the first name or Filed-by entity is the whole group.
- **SEC filing index:** retain Filed by and Subject CIK/name separately, plus the raw accepted timestamp. Do not use accepted time for same-day portfolio timing until timezone/session handling is verified.

A schema-aware parser prototype and unit tests are stored in research/phase35_13dg_parser_v2.py and research/test_phase35_13dg_parser_v2.py. Five synthetic-fixture tests pass; this is not yet a full-artifact validation.

## Amendment lineage
- For structured XML, previousAccessionNumber is an exact predecessor edge. Follow it recursively, validate that the predecessor exists, and retain cross-form transitions (13G to 13D) as explicit transitions rather than silently pooling families.
- For legacy filings, use only explicit accession references or a separately validated deterministic linkage. If no exact predecessor can be established, classify the chain as ambiguous/left-censored; do not infer from accession prefixes or amendment counts.
- An initial filing is not a true first event unless the predecessor/history census establishes that earlier relevant filings are absent from the covered history.

## Event construction rules
1. Separate 13D and 13G families initially; never pool them without independent evidence.
2. Each accession is a disclosure update, not automatically a new economic event.
3. Link amendments only through exact predecessor edges or validated deterministic legacy evidence.
4. A first-observable event requires complete enough history; otherwise mark left-censored and exclude from initiation tests.
5. Directional ownership changes require two sequential states for the same verified subject issuer and reporting group. Missing/ambiguous prior state means unknown.
6. Do not infer a buy/sell from price movement, market capitalization, or subsequent filings.
7. Missing purpose text is not evidence of passivity or activism.
8. Active-universe membership must be PIT-effective for the subject issuer; current ticker membership is insufficient.
9. KnowledgeDate is the filing date. Event date, report date, ownership values and narrative are available only as disclosed in that filing.
10. No same-day signal unless intraday accepted timestamp and market-session timing are explicitly modeled.

## First economic hypothesis (pre-registered, not yet authorized)
After the corrected issuer/group panel passes the gates, test whether newly disclosed 13D ownership/control events add information beyond frozen LTM/F80. Test 13G separately. Do not assume either family is informed, bullish or persistent.

## Validation protocol
- Chronological train/validation/final-OOS split; final OOS touched once.
- Identical exposure, costs and portfolio construction for baseline and augmented models.
- Block bootstrap appropriate for overlapping holding periods; issuer-clustered uncertainty and LOO.
- Equalized issuer exposure and concentration checks (with/without dominant issuers).
- Separate announcement-window price reaction from persistent post-disclosure behavior.
- Explicit controls for return-chasing and mechanical regulatory thresholds.
- Kill unstable hypotheses; no post-hoc horizon or threshold rescue.

## Next gate — required audit output
1. Subject-CIK match rate by form, year and XML/HTML/TXT schema.
2. False-positive filer-side rows and duplicate accession counts.
3. Exact predecessor-chain coverage and left-censoring rate.
4. Reporting-person/group identity coverage, with CIK/name/ambiguity classes.
5. Historical active-universe coverage by issuer and period.
6. Counts of eligible 13D/13G first-observable events and increase/decrease/unknown transitions.
7. Exclusion counts and reasons.

No forward returns until all seven outputs are produced and reviewed.
