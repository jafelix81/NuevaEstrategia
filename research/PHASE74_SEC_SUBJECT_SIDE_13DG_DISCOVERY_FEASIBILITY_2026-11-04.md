# Phase 74 — SEC subject-side 13D/13G discovery feasibility

Date: 2026-11-04  
Branch: phase74-sec-subject-side-13dg-discovery  
Status: preregistered feasibility audit; no data crawl yet.

## 1. Problem being solved

The Phase 35 artifact is a filer-side retrieval sample: it enumerates Schedule 13D/13G filings submitted by CIKs associated with the 335 current ticker map. It does not enumerate every investor filing about those 335 issuers. A 13D/G is submitted by the beneficial owner/reporting person, while the subject issuer is a separate identity in the SEC header and structured XML.

Therefore, the Phase 35 sample is useful for parser/schema tests but cannot be used as a subject-issuer ownership panel or to claim coverage of the F80 issuers.

## 2. Newly identified SEC discovery routes

### Route A — EDGAR Full-Text Search (EFTS)

The SEC's official EDGAR Full Text Search page says it searches electronic filing text since 2001 and supports filtering by company, person, date and filing category:
- https://www.sec.gov/edgar/search/

The SEC Webmaster FAQ states that XML element content is indexed, although element names are not associated with the indexed text:
- https://www.sec.gov/about/webmaster-frequently-asked-questions

The search page is backed by an observed JSON endpoint:
- https://efts.sec.gov/LATEST/search-index

This endpoint is not documented as a supported public API. Treat it as experimental and version-sensitive. Candidate parameters observed in public technical investigations are q, forms, startdt, enddt, from, and ciks. Do not assume the ciks filter means subject issuer; test its semantics.

Hypothesis: an exact quoted 10-digit subject CIK appearing as the XML issuerCik/issuerCIK value can retrieve cross-filer 13D/G documents because the SEC states XML content is indexed. Every candidate must still be downloaded and parsed; query hits are not issuer attribution.

### Route B — SEC Entity Landing Page

The official SEC Entity Landing Page has a dedicated “Beneficial ownership (Schedule 13D and 13G)” section and a “View all beneficial ownership” control:
- https://www.sec.gov/edgar/browse/?CIK=1479290

The page's underlying data endpoint and historical pagination are not yet documented. It is a second candidate if EFTS exact-CIK search is incomplete.

### Route C — submissions API (control only)

The documented data.sec.gov submissions API is per filer:
- https://www.sec.gov/search-filings/edgar-application-programming-interfaces

It is useful for filer metadata and acceptance timestamps, but does not by itself solve subject-side discovery. Do not confuse it with the subject issuer's beneficial-ownership history.

## 3. Known cross-filer positive controls

The pilot must retrieve both known filings when searching by the subject issuer, not only by the filer:

| Subject issuer | Subject CIK | Filer | Filer CIK | Form | Accession |
|---|---:|---|---:|---|---|
| Revance Therapeutics | 0001479290 | JPMorgan Chase & Co. | 0000019617 | SC 13G/A | 0000019617-25-000296 |
| Osisko Development Corp. | 0001431852 | Double Zero Capital, LP | 0002083861 | SC 13D | 0001062993-25-015044 |

Official SEC filing pages and complete-submission text:
- https://www.sec.gov/Archives/edgar/data/1479290/000001961725000296/0000019617-25-000296-index.htm
- https://www.sec.gov/Archives/edgar/data/19617/000001961725000296/0000019617-25-000296.txt
- https://www.sec.gov/Archives/edgar/data/2083861/000106299325015044/0001062993-25-015044-index.htm
- https://www.sec.gov/Archives/edgar/data/1431852/000106299325015044/0001062993-25-015044.txt

The complete submission header distinguishes SUBJECT COMPANY from FILED BY; the XML must be checked against both roles.

## 4. Phase 74A — small feasibility probe (after Phase 73 data pilot finishes)

No overlapping SEC crawl is allowed. Wait for Phase 73 run 41868352940 to complete and archive its artifact before starting this probe.

For each positive control:
1. Query EFTS with exact quoted subject CIK, forms SC 13D / SC 13G (including amendments), and a narrow filing-date window.
2. Query EFTS with ciks=subject_CIK and ciks=filer_CIK separately to determine whether that filter is filer-only or includes subject identity.
3. Record total hit count, document-level hits, distinct accessions, returned CIKs, form, file date, and pagination.
4. Fetch the exact complete-submission text for the known accession and validate the SEC header subject/filer CIKs plus XML issuer/filer CIKs.
5. Compare results with the SEC Entity Landing Page's beneficial-ownership listing where accessible.
6. Repeat on a small control set of at least 20 cross-filer filings spanning 13D, 13D/A, 13G, 13G/A and 2024-2026.

The test is about discovery recall and subject/filer separation, not prediction.

## 5. Phase 74B — if 74A passes

Build a subject-side candidate panel for the 335 current ticker CIKs and any historical CIKs later established by a PIT security master.

- Search each issuer CIK separately; keep issuer CIK, query, accession, filer CIK, form and filing date distinct.
- Deduplicate by accession and document filename.
- Download complete-submission text, extract primary XML, parse subject and filer separately.
- Retain only records whose XML issuer CIK equals the queried subject CIK; classify mismatches and ambiguous cases rather than force-assigning them.
- Reconcile all query hits to the source page / SEC header and store immutable raw-hit metadata.
- Record EFTS endpoint/query version, search timestamp, pagination offsets, total hits, response hashes and request headers.
- Check the 10,000-result cap and pagination behavior; use date windows if necessary.
- Preserve original acceptanceDateTime and filingDate; conservative KnowledgeDate is the first confirmed public filing/acceptance time, never eventDate or quarter-end.

## 6. Acceptance gates

The route advances only if:
- both known cross-filer positive controls are found by subject CIK;
- exact accession, form and filing date match;
- downloaded XML issuer CIK matches SEC header SUBJECT COMPANY CIK;
- XML filer CIK matches SEC header FILED BY CIK and accession prefix;
- a 20+ accession validation set shows >=99.5% subject identity concordance and zero cross-issuer contamination;
- pagination totals reconcile and no unexplained 10,000-hit truncation occurs;
- results are reproducible on a second run and the endpoint has no unresolved schema drift.

If exact CIK search misses known positive controls, test the Entity Landing Page route and then CUSIP/name-based full-text search. Do not silently accept a partial search result as complete coverage.

## 7. Economic research boundary

Only after subject-side coverage, historical CIK/ticker/share-class mapping, and point-in-time availability are established may a 13D/13G signal be tested.

Keep event families separate:
- 13D initial filings and 13D amendments (activist/control-intent hypothesis);
- 13G Rule 13d-1(b) QII, 13d-1(c) passive, and 13d-1(d) exempt/other categories;
- original filings vs amendments;
- group reporting persons vs individual reporting persons;
- share-count change vs percentage change caused by issuer denominator changes.

Do not infer a trade from a reported ownership snapshot. Use filing/acceptance as public KnowledgeDate. 13G timing can be materially delayed and varies by filer category. Test incremental value against frozen LTM/F80, with identical exposure/costs, chronological OOS, bootstrap and leave-one-issuer-out only after the data gates pass.

No forward returns, alpha tests, production changes or data purchases are authorized by this specification.

F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen.

## 8. Search semantics and query controls

The documented SEC UI supports CIK searches in the main full-text query field and exact-phrase matching; its FAQ says the search covers electronic filings since 2001. The Webmaster FAQ separately confirms that XML element content is indexed but element names are not. Therefore the primary feasibility test is an exact quoted CIK value as a text query, not an assumption about the undocumented ciks filter.

For each positive control, test both zero-padded and unpadded CIK text:
- "0001479290" and "1479290";
- "0001431852" and "1431852".

Filter the query by the four ownership forms and narrow dates. Dedupe document-level hits to accession-level records. Compare the Entity facet and ciks parameter only as secondary controls; their semantics must be inferred from the known cross-filer examples, not assumed.

The SEC search FAQ states that results can include all data in the filing and attachments, and that search relevance can rank documents rather than guarantee a complete accession listing. Accordingly, exact-CIK search results must be reconciled by accession and followed by source-native XML validation; an exhibit-only hit does not count as a primary ownership filing.
