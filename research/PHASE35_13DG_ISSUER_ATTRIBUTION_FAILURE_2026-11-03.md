# Phase 35 — critical 13D/13G subject-issuer attribution failure

Date: 2026-11-03
Branch: phase35-13dg-issuer-attribution-repair
Scope: source identity and parser audit only; no forward-return test.

## Executive decision

**The current Phase 35 artifact is not a valid issuer-level 13D/13G panel. Economic testing is blocked.**

The latest GitHub Actions run 41652405132 completed successfully (job 125973726145; artifact 13256930771). That proves the retrieval/parser workflow completed; it does not prove that every row belongs to the ticker mapped by the query CIK. Direct inspection found a 13G XML row assigned to TFC even though the filing's subject issuer is Federated Hermes ETF Trust.

## Reproducible row-level defect

Artifact row for accession 0000092230-25-000015:

| Field | Current artifact |
|---|---|
| ticker | TFC |
| issuer_cik | 0000092230 |
| form | SC 13G/A |
| filing_date | 2025-02-06 |
| reporting_person | null |
| percent_class | 38.0 |

The current source code creates each submissions row with issuer_cik=cik, where cik is the CIK queried from the ticker map. Its document parser then searches for the legacy text label CENTRAL INDEX KEY and falls back to that query CIK when the label is absent.

The SEC's actual XML for this exact accession identifies:
- issuerCik: **0001849998**
- issuerName: **Federated Hermes ETF Trust**
- issuerCusip: **31423L503**
- reportingPersonName: **TRUIST FINANCIAL CORP**
- classPercent: 38.0
- previousAccessionNumber: 0000092230-25-000001

The XML is available at:
https://www.sec.gov/Archives/edgar/data/92230/000009223025000015/primary_doc.xml

A SEC filing-detail page for another filing by the same reporting person against the same subject issuer explicitly distinguishes TRUIST FINANCIAL CORP (Filed by), CIK 0000092230, from Federated Hermes ETF Trust (Subject), CIK 0001849998:
https://www.sec.gov/Archives/edgar/data/92230/000009223025000138/0000092230-25-000138-index.htm

Therefore the artifact's issuer_cik=0000092230 and ticker=TFC are wrong for this filing. The row is a Truist reporting-person filing about a different issuer, not a TFC issuer event.

## Scope and consequences

The artifact contains:
- 20,266 retrieved rows;
- 303 distinct values currently labelled as issuers, but these are **not validated subject-issuer counts**;
- 7,858 XML 13G rows (89 in 2024, 4,356 in 2025, 3,413 in 2026);
- 437 XML 13D rows (22 in 2024, 239 in 2025, 176 in 2026);
- 14,542 rows marked as amendments;
- 19,680 rows with a parsed event date.

All 7,858 XML 13G rows are **at risk of subject-issuer misattribution** until their issuerCik is parsed and compared with the intended frozen-universe CIK. The sample above proves at least one false assignment; it does not establish the contamination rate. The 437 XML 13D rows and the legacy HTML/TXT rows also require a subject-CIK consistency audit rather than being assumed correct.

The 13G XML parser mismatch is separately visible in the data: all 7,858 XML 13G rows have null reporting_person in the current artifact. This is not evidence that the filings omit the reporting person. Schedule 13G XML uses coverPageHeaderReportingPersonDetails and fields such as reportingPersonName, reportingPersonBeneficiallyOwnedAggregateNumberOfShares, classPercent, and repeated typeOfReportingPerson; the current parser only expects the 13D-style reportingPersonInfo structure.

The current unique_issuers=303, ticker coverage, form distributions by ticker, and ownership field coverage therefore cannot be used as issuer-level coverage statistics. The previous accession-prefix/group counts (3,115 provisional sequences and 58.5% provisional amendment-first rows) are also not valid economic-group or true-first-event counts.

A separate known PIT-reporting defect remains: two MS rows have event_date=2024-12-31 but filing dates 2024-02-09 and 2024-02-12. filing_date remains the conservative KnowledgeDate; event_date is not PIT-certified.

## Positive technical finding: exact amendment pointers

Structured 13D and 13G XML can contain previousAccessionNumber. In the example above, the 2025 13G/A points directly to its 2025-01-07 initial 13G accession. This is a deterministic edge in the filing-lineage graph and can bridge from structured filings into older legacy filings. It is substantially safer than inferring a chain from accession prefixes or filing counts.

## Parser repair prototype

Added:
- research/phase35_13dg_parser_v2.py
- research/test_phase35_13dg_parser_v2.py

The parser separates query/archive CIK from subject issuer CIK; SEC index Filed-by CIK from Subject CIK; 13D reportingPersonInfo from 13G coverPageHeaderReportingPersonDetails; and filing-level predecessor accession from reporting-person/group identity.

It parses issuerCIK/issuerCik, CUSIP variants, eventDateRequiresFilingThisStatement, previousAccessionNumber, reporting-person nodes, ownership fields, and legacy multiple-name layouts.

**Local unit tests: 5 passed.** These tests use small synthetic fixtures modeled on actual SEC XML/index structures, including the 13G schema in the example above. They are parser unit tests, not a full reprocessing of the 20,266-row artifact; production integration is not yet authorized.

## Corrected data model

Every row must preserve separate fields:
1. query_cik / archive_path_cik: CIK used to retrieve the submissions block or archive path;
2. subject_issuer_cik: parsed from XML issuerCIK/issuerCik or SEC index Subject metadata;
3. filed_by_cik: parsed from SEC index Filed by metadata;
4. reporting_person_ciks and reporting_person_names: parsed from the filing itself;
5. submission_cik: accession prefix, retained only for traceability.

No field may be substituted for another. In particular, query CIK, archive path CIK, accession prefix, and Filed-by CIK are not automatically the subject issuer or the complete economic group.

## Required next gates

1. Reprocess all 7,858 XML 13G rows and compare parsed subject_issuer_cik with the intended target-universe CIK; classify true subject matches, filer-side false positives, and unresolved cases.
2. Perform the same issuer-CIK validation on all 437 XML 13D rows and a stratified sample of legacy HTML/TXT filings.
3. Deduplicate accessions that may appear under both filer and subject CIK archive directories; retain one canonical subject-issuer row.
4. Expand the subject-issuer filing census before initiation tests; recursively follow exact previousAccessionNumber links and mark incomplete chains left-censored.
5. Rebuild historical active-universe coverage and resolve the 27 previously unresolved ticker mappings.
6. Rebuild all reporting-person/group and ownership-state fields from the corrected issuer panel.
7. Only after these gates pass, preregister and run the incremental test versus frozen LTM/F80 with chronological OOS, identical exposure/costs, issuer-clustered bootstrap and LOO.

## Decision

**Retrieval completion: PASS. Subject-issuer attribution: FAIL / NOT CERTIFIED. Reporting-group and amendment normalization: NOT AUTHORIZED. Economic test: BLOCKED.**

No forward returns, no threshold/horizon optimization, and no changes to F80_TOP20_PARTIAL50_BASELINE_C20.


## Additional root cause: wrong discovery universe, not only wrong XML parsing

The prior workflow queried submissions for the target ticker-mapped CIKs. This retrieves filings submitted by those CIKs, not all Schedule 13D/G filings about those companies. The global master-index census is therefore required even after XML subject parsing is corrected. The old 20,266 records are not a complete subject-issuer sample and must not be treated as one.

A new branch prototype implements:
- parser v3 with correct 13G reportingCik/memberGroup/issuerCusips handling;
- SEC master.idx filtering for all 13D/G forms;
- filing-detail index parsing for Filed-by and Subject CIKs;
- a 2025Q1 pilot with a 95% Subject CIK coverage gate and a fixed Truist/Federated validation accession.

The prototype uses current ticker mappings only as candidate CIKs and does not claim historical active-universe coverage. No economic tests are authorized.


## 2026-11-03 — Master-index pilot diagnostics
The initial pilot failed because it did not normalize SCHEDULE-prefixed form labels and omitted the accession directory from filing-detail URLs. The saved 2025Q1 master.idx itself is comprehensive: 16,629 13D/G rows, 8,318 unique accessions, with 8,311 two-CIK pairs and seven single-CIK accessions. Known pairs include Federated/Truist and Sandisk/FMR. These pairs are not role-labelled; the SEC filing-detail page must establish Subject and Filed-by. The corrected pilot uses the paired CIKs to locate each index page and filters by the page's Subject CIK.
