# Phase 74 — SEC 13D/13G archive-path and acceptance-time correction
Date: 2026-11-04

## Executive result

Phase 73's 80-filing pilot was a partial data-gate failure, not evidence of 26 malformed or unavailable XML filings. Reinspection of its artifact and SEC source records isolated two deterministic implementation defects:

1. The complete-submission URL was built using the first ten digits of the accession (the submitting account CIK). For agent-filed Schedule 13D/G filings, this is not necessarily the CIK directory under which the archive representation is accessible. The Phase 35 source row carries the subject-issuer CIK. The corrected resolver tries that CIK first, then the accession-prefix CIK as a fallback, and records which path worked. The XML issuer and SEC header subject remain independently compared; the path CIK is never treated as identity evidence.
2. SEC-HEADER ACCEPTANCE-DATETIME is an Eastern wall-clock timestamp without an offset, while submissions[].acceptanceDateTime is ISO-8601 UTC. Phase 73 compared their digit strings directly, causing a systematic five-hour (EST) or four-hour (EDT) mismatch. The corrected function converts the header timestamp using America/New_York and converts both sources to UTC before comparison.

## Evidence from Phase 73

Run 41868352940, job 126708353783, artifact 13342854701 (SHA-256 5d4b05cbd96e7ed485ed020e338ce77a25fc588ef9e18666944255fb7a3dc5a5).

- Stratified sample: 80 filings.
- Successful parses: 54.
- HTTP 404 path failures: 26.
- XML issuer vs SEC header subject: 100% among parsed rows.
- Accession, filer, form and filing-date concordance: 100% among parsed rows.
- Acceptance timestamp concordance: 0% because the sources were in different time zones.
- The failed 26 were retrieval-path failures, not XML parse errors. Example accession 0000950157-25-000788 is accessible under the subject CIK directory 1754301; the accession-prefix directory 950157 returned 404. SEC filing header confirms subject Fox Corp CIK 0001754301 and filed-by MFT SH Family Trust CIK 0002080603. See SEC filing detail and complete submission:
  - https://www.sec.gov/Archives/edgar/data/1754301/000095015725000788/0000950157-25-000788.txt
  - https://www.sec.gov/Archives/edgar/data/2080603/000095015725000788/0000950157-25-000788-index.htm

## Code changes

Branch: `phase74-13dg-archive-path-and-utc-fix`

- `research/phase73_13dg_submission_text_pilot.py`: subject-CIK-first archive-path resolver with accession-prefix fallback; resolved path CIK recorded in output.
- `research/phase73_sec_submission_text_extractor.py`: acceptance timestamp normalization returns UTC; explicit source timezone supported; SEC header callers use America/New_York, submissions API callers use UTC.
- `research/test_phase73_sec_submission_text_extractor.py`: regression coverage for EST, EDT and UTC conversion and agent-filed archive URL construction.
- Pilot workflow allows this isolated branch and one 80-filing rerun under the shared `sec-public-data-research` concurrency group.

Commits:
- 16719f8859435b0e7b4a78fae51f03cfb31d55b1 — UTC timezone-aware normalization.
- cd978cc769b5cb8107bc36ebd0b081a3d6eb88a1 — subject-CIK-first archive path.
- 31bc41b8c10715187adc9dab3ea54a738aa4371a — timezone regression tests.
- 4012a4adf1ab36bf7c428dfdfa1c0314b2352adb — archive-path regression test.
- 8d56c3ddd514423abb35c1787d8d9ef756513aad — isolated pilot workflow branch filter.
- 8600fc253afba9336bee7b011e1ea1a437cf69e5 — single corrected pilot trigger.

## Validation status

The prior Phase 73 hosted test run 41868094850 passed its 16 tests, but it predates the Phase 74 corrections. Phase 74's corrected test suite and 80-filing pilot are awaiting a new hosted Actions result. No claim of PASS is made until the new run and artifact are inspected.

The pilot is capped at 80 filings. The full 8,294-document structured-XML corpus remains prohibited until:
- parse rate >=99.5%;
- XML issuer equals SEC header subject;
- XML filer equals SEC header filed-by and accession prefix where schema requires;
- form and filing date concordance >=99.5%;
- acceptance timestamps match after timezone normalization;
- reporting-person coverage and amendment lineage pass;
- failures are classified (missing source, HTTP, malformed XML, schema drift), not silently dropped.

## Research interpretation

The pilot is still a source-identity and data-feasibility audit over a filer-side retrieval sample, not a subject-issuer census. The legacy Phase 35 ticker/CIK labels remain untrusted until reconciled against SEC header subject and filer roles. No forward returns or economic tests are authorized. No claim about institutional predictive skill is made.

## Frozen strategy protection

`F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen. No production rules, holdings, exposures, costs, holding periods or portfolio parameters were changed.
