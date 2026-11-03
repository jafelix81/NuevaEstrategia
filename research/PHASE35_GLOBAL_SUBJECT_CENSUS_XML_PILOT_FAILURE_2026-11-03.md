# Phase 35 — global subject-census pilot failure and XML-path repair

Date: 2026-11-03  
Branch: `phase35-13dg-issuer-attribution-repair`  
Run: [41707588968](https://github.com/jafelix81/NuevaEstrategia/actions/runs/41707588968)  
Job: `126166891297`  
Artifact: `phase35-global-subject-census-2025q1` (ID `13267337601`, SHA-256 `dfc78500fdb11e19bb28a0830be10ac50a908a2b01a5528de9b46781d2f00101`)

## Result

The run completed with **failure at the validation gate**, not an HTTP/data-availability failure.

- Both test suites passed: 6 parser tests and 4 global-census tests.
- The SEC 2025Q1 `master.idx` was downloaded and parsed: 16,629 13D/G rows, 8,318 accessions.
- Candidate mapping produced 307 CIKs for 335 frozen tickers; 27 tickers remained unresolved.
- The pilot selected 1,100 target-relevant accessions and 206 non-target validation accessions.
- All 1,306 filing-detail pages were fetched without HTTP errors.
- However, the page parser extracted **zero** Subject CIKs and zero Filed-by CIKs, including the known Truist/Federated fixture. The pilot correctly failed rather than treating the master-index CIK pair or row order as role metadata.

This is a parser/representation failure in the filing-detail HTML path, not evidence that the SEC source lacks the information. The downloaded artifact's summary reports `FAILED_VALIDATION`, zero Subject/Filed-by coverage, and no forward-return use.

## Repair decision

For the 2025Q1 pilot, use the structured `primary_doc.xml` directly:

- `issuerInfo/issuerCik` (or `issuerCIK`) is parsed as `subject_issuer_cik`.
- `headerData/filerInfo/filer/filerCredentials/cik` is retained separately as `submission_filer_cik`.
- Reporting persons, `previousAccessionNumber`, ownership fields, event date, and CUSIPs are retained separately.
- The XML is fetched through each archive CIK path represented in the master-index accession group. The master-index CIK pair and its row order are never used to infer roles.
- `submission_filer_cik` is not automatically treated as the complete economic group or as proof of beneficial ownership. The reporting-person list and legal group evidence remain separate.

The SEC's Modernization of Beneficial Ownership Reporting final rule required structured data for Schedules 13D/13G beginning December 18, 2024; therefore 2025Q1 is a suitable structured-XML feasibility pilot. Official source: https://www.sec.gov/files/rules/final/2023/33-11253.pdf. The known Truist/Federated XML example is: https://www.sec.gov/Archives/edgar/data/92230/000009223025000015/primary_doc.xml.

## Predeclared pilot gates

- At least 95% Subject CIK coverage in target-relevant and non-target validation samples.
- At least 95% submission-filer CIK coverage and at least 95% match of both parsed identities to the master-index CIK pair.
- At least 95% form-type agreement with the master index.
- XML fetch error rate no greater than 5%.
- Exact Truist/Federated fixture: submission filer `0000092230`, subject issuer `0001849998`.
- Filing date from the master index remains the conservative KnowledgeDate; any signal must use a strictly later signal date. No same-day inference.

Reporting-person CIK coverage is measured but is not used to invent missing identities. A reporting-person-set fingerprint is only a checksum, not an economic-group identifier.

## Research boundary

No forward returns, no alpha test, no horizon or threshold selection. The current ticker map is a candidate set, not a point-in-time historical security master. The 27 unresolved tickers, historical active-universe membership, predecessor-chain completeness, and left-censoring remain open gates. `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen.


## Follow-up — run 41714047979
The XML pilot did not reach its network/census stage. Six parser-v3 tests and four master-index tests passed. In the XML pilot test suite, the two identity/URL tests passed; the negative test for a missing reporting-person CIK errored because the deliberately non-SEC URL lacked the `/data/` path segment assumed by `identity_row()`. This was an unguarded archive-path extraction in the testable row builder, not an SEC response or schema failure. The repair now treats archive_path_cik as nullable unless the URL matches the SEC archive path. The next run must first pass all 13 local tests, then execute the 2025Q1 XML census. No artifact or census result exists for run 41714047979.
