# Phase 72 — SEC 13D/13G structured XML identity and amendment-lineage audit

Date: 2026-11-04  
Branch: `phase72-13dg-structured-xml-parser`  
Scope: parser/schema feasibility and data-quality diagnosis only. No forward returns or alpha test.

## 1. Material source discovery

The SEC's 2023 final rule requires Schedule 13D/13G disclosures to use a schedule-specific machine-readable XML format from **2024-12-18**; voluntary compliance was permitted from 2023-12-18. The SEC's current technical-specification index lists Schedule 13D & 13G XML specifications and version history.

Official sources:
- SEC final rule, Release 33-11253 / 34-98704: https://www.sec.gov/files/rules/final/2023/33-11253.pdf
- SEC technical specifications (current Schedule 13D/13G XML versions): https://www.sec.gov/submit-filings/technical-specifications
- SEC example 13D/A XML with `previousAccessionNumber`, issuer CIK and multiple reporting-person fields: https://www.sec.gov/Archives/edgar/data/1510865/000168316824008840/primary_doc.xml
- SEC example 13G XML: https://www.sec.gov/Archives/edgar/data/1130166/000149315225012118/primary_doc.xml
- SEC example 13G/A XML with `previousAccessionNumber`: https://www.sec.gov/Archives/edgar/data/315066/000031506626002050/primary_doc.xml

## 2. Existing artifact coverage and parser defect

Inspected the actual Phase 35 artifact from run 41575083622, artifact 13212292743. Its `phase28d_events.csv` contains 20,265 resolved filings across 303 issuers (one retrieval error remains in the summary).

Direct file audit:
- 8,294 rows (40.91%) use a `primary_doc.xml` document; first observed 2024-01-26, last 2026-09-30.
- 8,206 XML rows were filed on/after 2024-12-18; 88 earlier XML rows reflect voluntary structured filing.
- In those 8,206 mandatory-era XML rows, the old flattened-text regex populated `reporting_person` in only 435 rows (5.30%). All 435 non-empty values ended in a trailing numeric “2”, consistent with a row-label capture defect.
- The old regex populated `reporting_person_type` in 1,254 rows (15.28%); 943/1,254 (75.20%) of those non-empty values were not recognized reporting-person type codes.
- By contrast, the existing numeric parser populated `percent_class` in 8,205/8,206 and shares in 8,206/8,206. Those numeric values still require semantic validation; this audit only demonstrates that the name/type fields are not usable as currently parsed.

This is a parser defect, not evidence that SEC structured filings lack reporting-person information.

## 3. Schema-specific fields

The SEC's 13D and 13G XML schemas use different element names. The parser must not flatten both forms into one regex:
- 13D: `issuerCIK`; repeated `reportingPersonInfo` blocks with `reportingPersonCIK`, `reportingPersonNoCIK`, `reportingPersonName`, `memberOfGroup`, ownership fields, `percentOfClass`, repeated `typeOfReportingPerson`; amendments include `headerData/previousAccessionNumber`.
- 13G: `issuerCik`; repeated `coverPageHeaderReportingPersonDetails` blocks with `reportingCik`, `reportingCikNotPresentInEdgarFlag`, `reportingPersonName`, `memberGroup`, ownership fields, `classPercent`, repeated `typeOfReportingPerson`; amendments include `headerData/previousAccessionNumber`.
- 13G may explicitly state that a reporting person has no EDGAR CIK. Preserve that status; never substitute the accession-prefix or filer CIK.
- `memberOfGroup` / `memberGroup` are filing-level evidence fields, not a complete economic-group identifier by themselves.
- `previousAccessionNumber` is a direct predecessor edge for structured amendments. Use it to build exact amendment chains before considering any fuzzy name matching.

The implementation is intentionally XML-only. It attaches no KnowledgeDate: callers must join the SEC submissions `filingDate`. XML event dates remain descriptive, never the information-availability timestamp.

## 4. Parser and tests added

Added `research/phase72_13dg_structured_xml_parser.py` and five regression tests covering:
1. 13D/A with multiple reporting persons, multiple type codes and direct predecessor.
2. 13G/A with its distinct tag names, multiple persons, group flags and direct predecessor.
3. Explicit no-CIK reporting person without filer-CIK substitution.
4. Amendment missing a predecessor, flagged rather than guessed.
5. Invalid XML fails closed.

The parser returns one filing record with a separate list of reporting-person records. It preserves raw group flags and type-code arrays, normalizes only CIK formatting, and keeps original accession lineage explicit.

## 5. Decision and next gate

**STRUCTURED XML FEASIBILITY: PASS. LEGACY HTML / FULL GROUP LINEAGE: STILL OPEN. NO ALPHA AUTHORIZED.**

Next:
1. Run the parser across all 8,294 XML rows in the existing artifact, without repeating the Phase 35 issuer census.
2. Reconcile XML issuer CIK to the existing SEC submissions subject-issuer CIK and identify schema/version exceptions.
3. Measure reporting-person CIK coverage, explicit no-CIK flags, multi-person filings, group-flag coverage, type-code validity, and exact amendment-predecessor coverage.
4. Resolve each `previousAccessionNumber` against the full accession index and recursively follow predecessor links; preserve missing/out-of-window predecessors as left-censored.
5. Use a stratified sample of legacy HTML filings to validate a separate parser; do not mix HTML and XML coverage metrics.
6. Only after deterministic issuer/person lineage and historical F80 membership gates pass, build ownership-state changes and compare against frozen LTM/F80.

No return tests, purchases or baseline changes. `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen.


## 6. Hosted regression execution (2026-11-04)

- Initial run 41863446169 failed one assertion because the no-CIK test fixture omitted a filer CIK, so both the reporting-person CIK and filer CIK were empty. The parser correctly preserved the reporting-person CIK as empty; the assertion did not test the intended non-substitution case.
- Corrected the fixture to include filer CIK `0002081473` while retaining `reportingCikNotPresentInEdgarFlag=Y`. The test now explicitly asserts that the filer CIK is present but the reporting-person CIK remains empty and is classified `declared_no_cik`.
- Rerun 41863595467, job 126691849721, executed all five tests successfully (`Ran 5 tests ... OK`). The REST run object still reports `queued`, but the decoded job log contains the complete successful test output and cleanup. This workflow makes no SEC requests.
- The parser is unit-tested against representative schema-shaped 13D/13G XML fixtures. Full-file validation against the 8,294 actual XML documents in the Phase 35 artifact remains the next data gate; no claim of corpus-wide parser accuracy is made yet.
