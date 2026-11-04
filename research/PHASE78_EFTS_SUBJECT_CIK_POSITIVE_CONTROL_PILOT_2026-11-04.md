# Phase 78 — SEC EFTS subject-CIK positive-control pilot

**Date:** 2026-11-04  
**Branch:** phase78-efts-subject-cik-positive-control-pilot  
**Scope:** small search-discovery feasibility probe; no full-universe crawl and no return tests.

## Research question

Can SEC Full-Text Search find Schedule 13D/13G filings by an exact quoted subject-company CIK even when the reporting person / FILED BY CIK and accession-prefix submitter are different entities?

The official SEC EDGAR search documentation says electronic filings are searchable since 2001, supports CIK, form and date searches, and indexes XML element content (not element names):
- https://www.sec.gov/edgar/search/
- https://www.sec.gov/edgar/search/efts-faq.html
- https://www.sec.gov/about/webmaster-frequently-asked-questions

This is a potentially efficient subject-side discovery route because it can search the issuer CIK embedded in the primary ownership document without enumerating every reporting person's submissions history. The underlying JSON endpoint is not documented as a stable public API, so all requests, parameters, response hashes and pagination metadata are retained.

## Positive controls

| Subject issuer | Subject CIK | FILED BY CIK | Accession | Form | Filing date |
|---|---:|---:|---|---|---|
| Revance Therapeutics | 0001479290 | 0000019617 | 0000019617-25-000296 | SC 13G/A | 2025-03-06 |
| Osisko Development | 0001431852 | 0002083861 | 0001062993-25-015044 | SC 13D | 2025-08-28 |
| Fox Corporation | 0001754301 | 0002080603 | 0000950157-25-000788 | SC 13D | 2025-09-12 |
| Fox Corporation | 0001754301 | 0002084288 | 0000950170-25-114595 | SC 13D | 2025-09-12 |

All four are cross-filer examples. The two Fox accessions share the same subject issuer and date but have different FILED BY entities and accession-prefix submitters.

## Query design

Thirteen narrow-window queries:
- Six exact text queries: quoted zero-padded and unpadded subject CIK, separately for the three subject/form/date groups.
- Three diagnostic queries using the EFTS ciks parameter with subject CIK.
- Four diagnostic queries using the ciks parameter with FILED BY CIK.

Each query filters by exact form and a three-day window (filing date ±1 day), uses pagination, records raw response hashes and deduplicates by accession. The ciks parameter is diagnostic only; it is not assumed to mean subject issuer.

## Acceptance gates

- All four known accessions must appear in the union of padded/unpadded exact-text subject-CIK queries.
- Each found accession must have the expected form and filing date.
- Every exact-text query must complete pagination and return no HTTP/API errors.
- ciks-parameter results are reported separately to infer whether that filter is filer-side, subject-side or mixed.
- Any document-level result is still checked at accession level; exhibits are not counted as separate ownership events.

A PASS proves that exact-CIK search can retrieve these known cross-filer controls. It does not establish global recall, precision, or historical F80 coverage.

## Implementation and execution controls

- research/phase78_efts_subject_cik_pilot.py performs 13 queries with 0.6-second spacing and a 10-page maximum.
- research/test_phase78_efts_subject_cik_pilot.py has eight offline tests.
- phase78_efts_subject_cik_tests.yml runs tests only.
- phase78_efts_subject_cik_pilot.yml runs the 13-query SEC probe only when the dedicated trigger file is added. It uses the shared SEC data concurrency group and does not cancel an existing data job.
- No trigger file has been added yet; no SEC query has been sent from Phase 78.

## Next decision

If exact-text queries find all four controls with correct form/date and complete pagination, proceed to a capped recall audit across a small stratified sample of current target CIKs and legacy/structured periods. If they fail, inspect the SEC Entity Landing Page Beneficial Ownership section and the global master-index archive-path approach before any broader scan.

No forward returns, alpha tests, data purchases or production changes. F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen.


## 2026-11-04 pilot result — FAIL, no positive controls found

The bounded 13-query pilot ran twice due an already-queued push event (runs 41874223573 and 41874376222; first artifact 13345621813). Both runs used the same query construction.

- 13/13 HTTP requests returned 200.
- 0/13 queries returned document hits.
- 0/4 known cross-filer accessions were found by padded or unpadded exact-CIK queries.
- 0 results from the diagnostic ciks=subject and ciks=filer filters.
- Pagination was complete for all queries and there were no HTTP/API exceptions.

This is a FAIL for the current EFTS request construction, not proof that the SEC index lacks the filings. The API response body/query echo was not preserved in this first run, so we cannot yet distinguish a bad parameter combination from a query-tokenization or index-coverage issue.

Decision: do not scale EFTS or use its ciks filter. Phase 79 will run a smaller diagnostic matrix with:
- a generic known-positive query to confirm the endpoint returns any results;
- company-name terms (Revance, Osisko, Fox) with and without form/date filters;
- zero-padded and unpadded CIK text without quotes;
- root-form filters (SC 13D / SC 13G, rather than amendment strings);
- full response body and query echo hashes.

If company-name controls also fail while generic controls work, exact CIK tokenization is unsuitable. If generic controls fail, stop using this endpoint and move to the SEC filing-detail index / Entity Landing Page route. No further EFTS crawl until Phase 79 diagnostics are reviewed.
