# Phase 73 — SEC Schedule 13D/13G complete-submission XML recovery

Date: 2026-11-04  
Branch: phase73-13dg-submission-text-xml-recovery  
Scope: repair the Phase 72 source-document ingestion path and validate identity against SEC header roles. No forward returns or alpha test.

## Executive decision

Phase 69's incremental fund-registrant scan completed with a PASS data gate but found zero incremental accessions for the ten newly mapped fund registrant CIKs across the audited 14-quarter Form 144 panel. The expanded panel therefore remains 21,648 candidate accessions / 21,634 issuer-matched events; the new current CIK map did not add Form 144 events in this sample. This is a negative coverage result, not evidence that the registrants have no filings outside the scanned panel or no historical series/class activity.

Phase 72's 80-filing 13D/13G XML pilot failed: 80/80 selected records raised an ElementTree mismatched-tag error, producing zero parsed filings. The failure is an ingestion/representation issue, not a demonstrated absence of structured data. The artifact is preserved and no corpus-wide coverage or parser-accuracy claim is made.

## 1. Phase 69 result — no incremental Form 144 accessions

Run: https://github.com/jafelix81/NuevaEstrategia/actions/runs/41863703923  
Artifact: https://github.com/jafelix81/NuevaEstrategia/actions/runs/41863703923/artifacts/13340957307

- Current universe map: 335/335 tickers; 319 candidate registrant CIKs.
- Ten new fund registrant CIKs were identified and reconciled against the legacy 309-CIK set.
- Incremental candidate accessions: 0.
- Incremental issuer events: 0.
- Expanded panel: 21,648 candidate accessions; 21,634 issuer-matched rows; 14 filer-only false positives; 289 unique issuer CIKs.
- 280 control pairs retained 100% concordance.
- No duplicate accessions, identity conflicts, XML errors or unresolved incremental rows.
- Historical F80 membership, fund series/class mapping and accepted-timestamp availability remain untested.

The 10 new CIKs are current fund registrant mappings, not a PIT security master. A registrant-level match is not assigned to every ETF ticker sharing that CIK.

## 2. Phase 72 pilot — actual failure, not a PASS

Run: https://github.com/jafelix81/NuevaEstrategia/actions/runs/41865034118  
Artifact: https://github.com/jafelix81/NuevaEstrategia/actions/runs/41865034118/artifacts/13341118476

- Stratified sample: 80 XML rows across 13D/13G, original/amendment and pre-/post-mandate strata.
- Submission metadata index: 80/80 accession matches; zero submissions-index errors.
- Direct XML parse: 0/80.
- Parse errors: 80/80, predominantly ElementTree mismatched-tag at repeated generated-document line locations (13G around line 338; 13D around line 330).
- No reporting-person, issuer-concordance or lineage metrics can be inferred from this failed pilot.
- The run REST status snapshot remained queued even though the job log and artifact show the audit process and upload completed; the artifact summary is the authoritative result for this diagnostic.

The failed artifact is retained as a regression fixture for the old retrieval route. It must not be counted as missing SEC filings or zero ownership.

## 3. Source-native diagnosis

The SEC filing-detail page for accession 0000019617-25-000296 identifies JPMorgan Chase & Co. as filer (CIK 0000019617) and Revance Therapeutics, Inc. as subject (CIK 0001479290). The complete submission text file exposes distinct SEC-HEADER SUBJECT COMPANY and FILED BY blocks, then contains the filed primary_doc.xml payload inside DOCUMENT/TEXT/XML markers. The XML independently carries issuerCik=0001479290 and filer CIK 0000019617.

A second official example, accession 0001062993-25-015044, identifies Osisko Development Corp. as subject (CIK 0001431852) and Double Zero Capital, LP as filer (CIK 0002083861); its complete submission text includes the raw 13D XML and multiple reporting-person blocks.

Official SEC examples:
- https://www.sec.gov/Archives/edgar/data/1479290/000001961725000296/0000019617-25-000296-index.htm
- https://www.sec.gov/Archives/edgar/data/19617/000001961725000296/0000019617-25-000296.txt
- https://www.sec.gov/Archives/edgar/data/2083861/000106299325015044/0001062993-25-015044-index.htm
- https://www.sec.gov/Archives/edgar/data/1431852/000106299325015044/0001062993-25-015044.txt

Design rules:
1. The Phase 35 issuer_cik field is mixed/ambiguous: the generator seeds it with the query/filer CIK and may overwrite it using a heuristic CIK extraction from the fetched document. It is not a certified subject issuer CIK and must be reconciled against the complete-submission SEC header.
2. Use the complete submission .txt as the transport container, extract only the primary_doc.xml document's inner XML payload, and validate XML issuer against SEC header SUBJECT COMPANY CIK.
3. Validate XML filer against SEC header FILED BY CIK and the accession-prefix CIK. Preserve all three identities separately.

The complete-submission route is a source-format correction. It does not turn the Phase 35 filer-side sample into a subject-issuer census.

## 4. Phase 73 implementation

Added a fail-closed extractor that:
- parses the SEC-HEADER subject and filer blocks separately;
- selects only the document whose filename is primary_doc.xml;
- extracts the inner XML payload rather than parsing the SGML wrapper or an alternate rendered representation;
- preserves acceptance timestamp, filing date, form, subject CIK/name and filer CIK/name;
- never infers a missing subject/filer CIK from the other role or accession prefix.

The pilot compares:
- XML issuer CIK vs SEC header SUBJECT COMPANY CIK;
- XML filer CIK vs SEC header FILED BY CIK and accession prefix;
- XML form vs SEC header form and SEC submissions metadata;
- filing date vs SEC header and submissions metadata;
- acceptanceDateTime vs SEC header and submissions metadata;
- reporting-person extraction and same-issuer amendment edges.

The first hosted step is unit tests only. The 80-document SEC pilot has a separate trigger and will not run until tests pass and the SEC public-data concurrency group is free.

## 5. Decision and next gates

- Do not run the 8,294-document full corpus yet.
- Run the 80-document complete-submission pilot only after Phase 73 tests pass.
- Require >=99.5% XML parse, issuer/header subject concordance, filer/header/accession concordance, form/date/acceptance concordance and positive reporting-person counts; require zero cross-issuer predecessor edges.
- If the pilot passes, expand to the full 8,294 XML rows with checkpoints, retry bounds, immutable input hash and a fresh artifact. Keep legacy HTML rows separate.
- Continue exact previousAccessionNumber lineage, but treat predecessors outside the input panel as left-censored.
- No forward returns, no alpha test, no data purchase and no economic test authorization.

F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen.


## 6. Hosted extractor regression note

The first hosted Phase 73 test attempts exposed fixture-only CIK zero-padding mistakes in the test expectations, not parser defects. The 13G and 13D extracted/header/XML CIKs are ten-digit values; the fixture assertions have been corrected. The pilot also normalizes SEC submissions API ISO acceptanceDateTime values to the SEC header's 14-digit form before concordance testing and now checks accession identity explicitly. The corrected hosted suite is queued; no SEC data pilot has been triggered.


## 7. Hosted test status at 2026-11-04 16:31 UTC

- Run 41867865628 passed all 16 tests: 5 existing Phase 72 parser tests, 7 Phase 72 corpus-helper tests and 4 Phase 73 complete-submission extractor tests. This confirms the 13D/13G fixtures correctly separate subject and filer identities after the ten-digit CIK expectation correction.
- A further test adds normalization of SEC submissions API ISO acceptanceDateTime values to the SEC header's 14-digit timestamp and an explicit accession-number concordance gate.
- Run 41868027603 was queued with the first timestamp-normalization revision; run 41868094850 was queued with the corrected digit-normalization regex. The latter is the current code revision to verify.
- The separate SEC data-pilot trigger has not been created or pushed. No SEC crawl is running from Phase 73.

## 8. Regulatory timing regimes — separate from XML schema regime

The SEC's 2023 final rule creates three distinct timing cutovers that must not be collapsed into one XML-era flag:

- Schedule 13D revised deadlines apply from February 5, 2024: initial filings within five business days after the >5% acquisition; material amendments within two business days.
- Revised Schedule 13G deadlines apply from September 30, 2024. The filing category matters: QIIs and Exempt Investors generally file initial 13Gs within 45 days after quarter-end when >5% at quarter-end; QIIs crossing >10% have a five-business-day month-end deadline; Passive Investors file within five business days after crossing >5%. Material amendments generally follow a 45-calendar-day quarter-end deadline, with additional monthly thresholds for QIIs/Passive Investors.
- Structured XML becomes mandatory only from December 18, 2024; voluntary XML began December 18, 2023.

Consequently the event panel must carry separate fields for (a) form family, (b) filer rule designation (13d-1(b)/(c)/(d)), (c) 13D vs 13G deadline regime, and (d) XML submission regime. A single "pre/post-2024-12-18" flag is appropriate only for schema availability, not for expected filing lag or economic interpretation.

Sources: SEC Release 33-11253 / 34-98704, 88 FR 76896 (Nov. 7, 2023), especially compliance dates and shortened 13G deadlines: https://www.sec.gov/files/rules/final/2023/33-11253.pdf ; SEC Corporation Finance Interpretations, Regulation 13D-G (updated July 11, 2025): https://www.sec.gov/rules-regulations/staff-guidance/corporation-finance-interpretations/exchange-act-sections-13d-13g-regulation-13d-g-beneficial-ownership-reporting

Research implication: 13D filings/amendments and 13G QII/passive/exempt filings must be tested as separate event families. A 13G report's event date/quarter-end is not its public KnowledgeDate; no event is actionable before EDGAR filing/acceptance. Do not infer actual trade date or institutional information advantage from the reported ownership snapshot alone.

## 9. Immutable Phase 35 artifact — XML schema-era coverage

I independently counted primary_doc.xml rows in the downloaded immutable Phase 35 artifact (20,265 source rows). It contains 8,294 XML rows, dated 2024-01-26 through 2026-09-30:

- Before voluntary XML authorization (pre-2023-12-18): 0.
- Voluntary XML period (2023-12-18 through 2024-12-17): 88.
- Mandatory XML period (from 2024-12-18): 8,206.

The 88 voluntary rows comprise 2 13D/A, 39 13G originals and 47 13G/A; no 13D original was present in that voluntary-period subset. The 8,206 mandatory rows comprise 49 13D originals, 386 13D/A, 2,569 13G originals and 5,202 13G/A.

This is coverage within the immutable Phase 35 filer-side retrieval artifact only, not a subject-issuer census or universe coverage estimate. The Phase 73 stratified sample should preserve the voluntary/mandatory schema split, while future economic tests must additionally split the separate 13D (2024-02-05) and 13G (2024-09-30) deadline regimes.

## 10. Phase 73 data-pilot execution

Run 41868352940 was triggered after the corrected Phase 73 regression suite passed. The run has completed dependency installation, all parser regression tests, Python compilation, immutable Phase 35 artifact download and source-file validation. Its stratified 80-filing complete-submission retrieval/parse step is currently in progress; no pilot artifact or data-gate result is available yet. Do not start a second SEC data crawl while this run is active.

## 11. Phase 35 source-field role correction

Inspection of the actual Phase 28D generator on main shows that the Phase 35 artifact is built by enumerating submissions for the 307 CIKs selected from the 335-name universe (the filer/query universe), then parsing a CIK from the fetched document and remapping that CIK to a ticker. The parser initially seeds issuer_cik with the query/filer CIK and overwrites it only if its heuristic finds a CENTRAL INDEX KEY in the fetched document.

Therefore the artifact's issuer_cik/ticker fields are **not certified subject-issuer identities**: depending on the fetched document representation, the value can be the submitting filer CIK or the subject issuer CIK. The JPM/Revance example is a concrete filer-vs-subject false attribution in the raw artifact: the row is mapped to JPM (CIK 0000019617), while the SEC header/XML identify Revance (CIK 0001479290) as subject. Other rows can correctly map to the subject, as shown by rows whose subject CIK differs from the accession-prefix filer CIK.

This refines the prior description: Phase 35 is a filer-universe-limited crawl with a mixed, heuristic subject-CIK field, not a clean filer-only table and not a complete subject-side census. It misses filings by filers outside the 335 CIK query universe and may misattribute some rows to the filer. The Phase 73 pilot's source_cik/header_subject/header_filer columns are intended to quantify this role mix and identify misassigned rows. No Phase 35 event row is accepted for economic testing until subject identity is confirmed against the complete-submission SEC header and XML.
