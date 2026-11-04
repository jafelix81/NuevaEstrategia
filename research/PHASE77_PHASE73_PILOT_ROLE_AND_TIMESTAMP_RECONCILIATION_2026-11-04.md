# Phase 77 — Phase 73 pilot role and timestamp reconciliation

**Date:** 2026-11-04  
**Branch:** phase77-13dg-agent-filer-identity-correction  
**Source:** Phase 73 corrected-retrieval artifact 13345491458, run 41872288761.  
**Scope:** re-interpret the existing 80-filing artifact with correct SEC identity semantics; no new SEC requests and no return tests.

## Executive result

The corrected Phase 73 retrieval run fetched and parsed all 80 sampled complete-submission files. The artifact's overall gate was marked FAIL because its metrics incorrectly required the accession-prefix CIK to equal the SEC header FILED BY / XML filer CIK, and treated absent secondary submissions-API metadata as a mismatch.

That requirement is invalid. The SEC explains that the first ten accession digits are the CIK of the entity submitting the filing, which can be a third-party filing agent. The submitting account is not necessarily the beneficial owner/reporting person named in FILED BY. The correct identity comparison is XML filerInfo CIK versus SEC header FILED BY CIK; accession prefix is retained as a separate submitter-account field.

Official SEC source: https://www.sec.gov/about/webmaster-frequently-asked-questions

## Recomputed artifact metrics

| Validation | Result | Interpretation |
|---|---:|---|
| Complete-submission files parsed | 80/80 | PASS |
| XML issuer CIK = header SUBJECT COMPANY CIK | 80/80 (100%) | PASS |
| XML filer CIK = header FILED BY CIK | 80/80 (100%) | PASS |
| Header accession = source accession | 80/80 (100%) | PASS |
| XML/header form concordance | 80/80 (100%) | PASS |
| Source filing date = SEC header FILED AS OF DATE | 80/80 (100%) | PASS |
| Submission API filing-date cross-check | 54/54 available (100%) | PASS; API row available for 54/80 |
| SEC header ACCEPTANCE-DATETIME present | 80/80 | PASS |
| Header ET to submissions API UTC cross-check | 54/54 available (100%) | PASS; API timestamp available for 54/80 |
| Reporting-person rows | 147 | Parsed; 100% of filings have at least one |
| Amendments with previousAccessionNumber | 26 | All 26 predecessors outside this 80-row sample |
| Cross-issuer predecessor edges | 0 | PASS |

### Why the old 67.5% metrics were false failures

- Header FILED BY CIK equals accession-prefix CIK in 54/80 (67.5%). The other 26 use a different submitting account / filing-agent CIK. This is allowed by the SEC accession-number definition and is not a filer-identity mismatch.
- XML filer CIK equals header FILED BY CIK in 80/80 (100%). This is the correct identity check.
- Submission API metadata was found for 54/80 (67.5%). For those 54, filing date and timezone-normalized acceptance timestamp both match the SEC header in 54/54. The remaining 26 are missing secondary submissions-index metadata; they are not failed header/XML identity records.
- The source Phase 35 field named issuer_cik is mixed: it matches header FILED BY in 59/80 (73.75%) and header SUBJECT COMPANY in 21/80 (26.25%). It must never be treated as a certified issuer identity.

## Corrected PIT handling

- Preserve SEC header FILED AS OF DATE and compare it to the source filing date; use the filing date as a conservative date-level KnowledgeDate.
- Preserve SEC header ACCEPTANCE-DATETIME as Eastern wall-clock time and normalize using America/New_York, including DST.
- Compare the normalized UTC timestamp to submissions API acceptanceDateTime only when the API record exists. Missing API metadata is NA, not False.
- For any return test, do not assume EDGAR acceptance time equals public availability time. Use the next complete trading session after filing date as the conservative first executable point unless a separate public-dissemination timestamp is validated.
- Keep accession-prefix submitter CIK, SEC header FILED BY CIK, XML filerInfo CIK, XML issuer CIK and header SUBJECT COMPANY CIK as separate columns.

## Code correction

The Phase 77 branch adds explicit helpers:
- compare_filer_identity: XML filer vs header FILED BY, with accession-prefix equality reported separately.
- compare_filing_dates: source/header date is primary; submissions API date is a conditional cross-check.
- compare_acceptance_datetimes: header Eastern timestamp is converted to UTC; API comparison is conditional on API metadata availability.

The previous 80-filing artifact is not re-downloaded. This phase changes the validation semantics and prepares future pilot runs; it does not trigger a SEC data crawl.

## Decision

**Phase 73 schema/identity feasibility passes for the sampled structured-XML filings.** The artifact remains a filer-side sample, not a subject-issuer census. Historical F80 membership, legacy HTML coverage, complete amendment lineage and subject-side discovery remain open. The full 8,294-document parse and all economic tests remain blocked until those coverage gates are met.

No forward returns, alpha tests, purchases or production changes. F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen.
