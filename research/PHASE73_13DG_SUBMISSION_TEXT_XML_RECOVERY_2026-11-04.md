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
1. The old Phase 35 issuer_cik column is a filer/query-side key for this source artifact; it must not be compared with XML issuerCik as if it were the subject issuer.
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
