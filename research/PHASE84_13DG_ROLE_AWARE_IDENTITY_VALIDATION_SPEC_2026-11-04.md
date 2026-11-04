# Phase 84 — Role-aware SEC 13D/13G identity validation

**Date:** 2026-11-04  
**Branch:** phase84-13dg-role-aware-identity-validation  
**Input snapshot:** Phase 82 run 41892370262, artifact 13353118959  
**Phase 83 reference:** run 41893546069, artifact 13353988656

## Research question

Can the global 2016Q1–2026Q3 SEC master-index candidate set be converted into a reliable *subject-issuer* discovery set by resolving every candidate CIK against SEC-HEADER SUBJECT COMPANY and FILED BY, without treating the master-index CIK, archive-path CIK or accession-prefix CIK as an issuer by assumption?

## Why Phase 84 is separate

Phase 83's preregistered gate failed because only 11/44 unique-candidate CIK hits (25%) were subject issuers; 33/44 were filer-only. This failure is preserved. It is not appropriate to loosen the old gate retrospectively. Phase 84 tests a different, explicitly role-aware proposition: filer-only hits are expected false positives that must be excluded, while target subject CIKs must be found in the index/path candidate set and resolved from the header.

## Frozen sample design

- Input: the accepted Phase 82 global candidate-accession file from artifact 13353118959.
- Universe: 319 current candidate CIKs, not a historical PIT security master.
- Sample: 600 complete submissions, deterministic SHA-256 ordering with a Phase 84 salt.
- Stratification: form family (13D/13G) × original/amendment × form-specific timing regime × candidate class (unique/ambiguous/control).
- All 120 Phase 83 accessions are excluded. Their per-stratum role counts are retained for a combined descriptive, post-stratified estimate.
- SEC request throttle: 0.8 seconds, bounded retries; HTTP 404 archive-path misses are terminal for that path and the next recorded path is attempted.
- Every successful complete submission is preserved with source URL, resolved archive CIK, HTTP status, byte count, SHA-256 and UTC retrieval timestamp.

## Preregistered role-aware gates

1. All 600 sample rows retrieved and parsed; no fetch errors.
2. Header parse, accession/form/date concordance, subject/filer CIK presence and acceptance timestamp validity each at least 99.5%.
3. For rows whose header SUBJECT COMPANY CIK is in the 319 current candidates, that subject CIK must appear in the master-index or archive-path candidate set at least 99.5% of the time; zero target-subject misses are required.
4. Every candidate CIK must resolve to header SUBJECT COMPANY or FILED BY; unresolved candidate CIKs must be no more than 0.5%.
5. For timing regimes where structured XML is mandatory, XML must be present at least 99.5% of the time. Where XML exists, issuer/filer must match header subject/filer at least 99.5%.
6. Raw submission bytes, SHA-256 and UTC retrieval timestamps must be reproducible for at least 99.5% of the sample.

**Important:** the fraction of unique candidate CIKs that are subjects is reported, not gated to 99.5%. Filer-only hits are an expected false-positive class and must be removed by role resolution; they are not issuer events.

## Weighted role estimate

Phase 84 reports a descriptive post-stratified estimate using Phase 83 and Phase 84 disjoint samples, with weights from the full Phase 82 population counts in each stratum. It has no inferential confidence interval because the deterministic hash sample is not a formally randomized design. It is a data-feasibility diagnostic, not an alpha result.

## Economic and production boundary

No forward returns, signal construction, alpha testing, tuning, data purchase or production change is authorized. A Phase 84 pass would authorize only a full subject-side coverage/event-normalization design, still conditional on historical ticker/CIK/security lineage and the unresolved original F80 membership rule (Phase 71). F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen.
