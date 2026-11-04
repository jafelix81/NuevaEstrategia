# Phase 35 — 13D/13G Event Normalization Specification

Updated: 2026-11-04 (cross-quarter lineage semantics correction)

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
- For structured XML, preserve previousAccessionNumber as an explicit prior-filing reference. It is not guaranteed to identify the immediately preceding amendment and may point to an original/root accession. Validate subject issuer, reporting-person identity, form family and security class/CUSIP; do not treat the pointer as a sequential edge without independent chronological validation. Retain cross-form transitions (13G to 13D) explicitly rather than silently pooling families.
- For legacy filings, use only explicit accession references or a separately validated deterministic linkage. If no exact predecessor can be established, classify the chain as ambiguous/left-censored; do not infer from accession prefixes or amendment counts.
- An initial filing is not a true first event unless the predecessor/history census establishes that earlier relevant filings are absent from the covered history.

## Event construction rules
1. Separate 13D and 13G families initially; never pool them without independent evidence.
2. Each accession is a disclosure update, not automatically a new economic event.
3. Preserve explicit previousAccessionNumber references as lineage anchors, not assumed immediate-predecessor edges. Link sequential states only after identity and chronology are independently validated; missing or ambiguous links remain unresolved.
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


## 2026-11-03 correction: discovery must be subject-issuer based, not query-CIK based

The earlier 28D/35 method is structurally invalid as an issuer census. It queried SEC submissions for CIKs mapped from the target ticker list. SEC submissions are filings made by the queried CIK; for Schedule 13D/G that CIK is commonly the reporting person/filer, while the target security issuer is a different entity. The TFC/Truist/Federated example proves this distinction. A schema-aware XML parser alone cannot correct the sampling frame because filings submitted by investors outside the 335-name universe were never queried.

### Required global discovery frame
1. Download the SEC quarterly global master.idx for each quarter in the research history.
2. Filter its Form Type column to SC 13D, SC 13D/A, SC 13G and SC 13G/A. The master index CIK is the filer/submitting entity only.
3. For every candidate accession, fetch the SEC filing-detail index page and parse its Filed by and Subject CIK/name fields separately.
4. Use Subject CIK as the issuer identity for legacy-compatible discovery. Where structured XML exists, parse issuerInfo/issuerCik or issuerCIK and require consistency with the index Subject CIK; disagreements are quarantined.
5. Preserve accession-prefix/submission CIK, master-index filer CIK, index Filed-by CIK, XML filer CIK, subject issuer CIK, reporting-person CIKs/names, and security-class CUSIP(s) as separate fields.

### Corrected 13G schema details
The structured 13G schema uses:
- issuerInfo/issuerCik, issuerName and issuerCusips/issuerCusipNumber;
- coverPageHeaderReportingPersonDetails/reportingCik and reportingPersonName;
- memberGroup (not memberOfGroup);
- reportingPersonBeneficiallyOwnedNumberOfShares with nested voting/dispositive fields;
- reportingPersonBeneficiallyOwnedAggregateNumberOfShares, classPercent and repeated typeOfReportingPerson;
- headerData/previousAccessionNumber as an explicit prior-filing reference; it is not guaranteed to be the immediately preceding amendment.

A reporting-person-set hash is not an economic-group identifier. Group continuity must use exact predecessor links plus explicit reporting-person and legal/group evidence. Missing CIKs or incomplete sets remain ambiguous.

### Pilot and gates
- Pilot quarter: 2025Q1.
- Validate the known Truist/Federated accession 0000092230-25-000015: Filed-by CIK 0000092230; Subject CIK 0001849998.
- Report global candidate counts by form, Subject CIK parse coverage, Filed-by coverage, target-subject matches, target-filer matches, and exact duplicates.
- Minimum pilot Subject CIK parse coverage: 95%. This is a parser/data-quality gate, not an alpha threshold.
- Expand to all quarters back to the earliest usable EDGAR full-index history (1993 archive onward where available) only after the pilot passes.
- The 335 current ticker-to-CIK candidates are not historical active-universe membership. Build a PIT-effective historical issuer/security master before any return test.
- Filing date remains KnowledgeDate. Accepted timestamp is retained separately; no same-day signal without verified timezone/session handling.
- No first-event claim if predecessor history is left-censored or incomplete. No forward returns until subject-issuer coverage, group identity, amendment lineage and historical universe gates all pass.

Pilot code: research/phase35_global_subject_census_pilot.py. Parser: research/phase35_13dg_parser_v3.py. Six local parser tests are synthetic/schema tests only; the full SEC census has not yet run.


## 2026-11-03 — Master-index form and paired-CIK findings
The 2025Q1 master.idx contains 16,629 13D/G rows after normalizing both SCHEDULE and SC form labels, and 8,318 unique accessions. 8,311 accessions have two associated CIK/name rows; seven have one. This is a promising coverage structure, but the master index does not label those CIKs as Subject or Filed by.

The first pilot's seven-row count was caused by accepting only SC-prefixed form labels; the zero Subject-CIK parse was caused by constructing archive URLs without the accession subdirectory. Both defects are corrected. The new pilot groups by accession, tries archive paths for each associated CIK, verifies the accession on the filing-detail page, and validates the page's Subject/Filed-by CIKs against the master-index pair.

The candidate ticker map now includes SEC exchange-listed and mutual-fund/series files. Current mapping is not historical active-universe membership. No event or return test is authorized until the pilot passes.


## Implementation addendum — 2025Q1 structured-XML pilot (2026-11-03)

The global master-index + primary XML pilot passed only the 2025Q1 subject/filer role-extraction gate. It does not pass historical universe, reporting-group, or event-lineage gates. See `research/PHASE35_GLOBAL_SUBJECT_CENSUS_XML_PILOT_RESULTS_2026-11-03.md`.

### Identity and discovery controls

- Count a record as a target-company filing only when `subject_issuer_cik` maps to the candidate issuer CIK. A target `submission_filer_cik` alone is not a target-company filing. In the 2025Q1 pilot, 1,100 accessions were selected by the union of subject/filer candidates, but only 242 parsed records had a target subject; 858 were filer-only cross-issuer records.
- The 2025Q1 sample resolved 307 candidate CIKs for 335 current tickers; 27 remain unresolved. Current mapping is not historical active-universe membership.
- The 13G schema makes `reportingCik` optional. Missing `reportingCik` must remain missing in the source record. Never equate `submission_filer_cik` with every reporting person or an economic group.
- A possible single-person crosswalk may use a frozen deterministic name rule: normalized Unicode/case/punctuation; fixed legal-suffix and leading-`THE` handling; order-invariant tokens only for type `IN`; order-preserving tokens for entities; exactly one reporting-person match to the master-index name for `submission_filer_cik`. The 2025Q1 development sample yielded 203/213 unique links and the non-target sample 91/100. These are coverage rates, not precision. Do not write inferred CIKs into source data or use this rule until independently validated on separate quarters and audited for false matches.
- For multi-person filings, a unique filer-to-one-person match identifies at most that one person. It does not identify other reporting persons or establish group membership. A reporting-person-set fingerprint remains a checksum only.
- Preserve `memberGroup` values and explicit joint-filing/group text. Missing or contradictory group markers mean group identity unresolved; do not infer a group from shared filing or filer CIK.

### Lineage controls

- Preserve `previousAccessionNumber` exactly when present. Treat it as an explicit lineage pointer, not automatically as the immediately preceding amendment; it may point to an original accession.
- Missing `previousAccessionNumber` is unresolved unless a separately preregistered, unique predecessor rule is validated. Six of 25 target-subject 13D/A records and 38 of 164 13G/A records in the 2025Q1 pilot lacked this field.
- Add `amendmentNo` to the parsed output before attempting any fallback lineage reconstruction. A missing predecessor must not be repaired by accession-prefix equality alone.
- Extend the accession history across quarters before declaring a first-observable event. A quarter-only sample is left-censored by construction.

### KnowledgeDate and economic boundary

- Continue to use master-index filing date as conservative KnowledgeDate. Signal date must be strictly later. Do not use event date as KnowledgeDate.
- No forward returns, threshold/horizon selection, or economic test is authorized from the 2025Q1 pilot.
- The next identity validation should use separate 2025Q2 and 2025Q3 quarters with the name-crosswalk rule frozen before those runs. Historical active-universe membership and legacy pre-structured-XML subject attribution remain separate mandatory gates.
- `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen.
