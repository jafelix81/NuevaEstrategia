# Phase 79 — EFTS query semantics diagnostic

**Date:** 2026-11-04  
**Branch:** phase79-efts-query-semantics-diagnostic  
**Scope:** bounded query-syntax diagnostics only; no broad search or return tests.

Phase 78 returned HTTP 200 but zero hits for all 13 exact-CIK and ciks-filter requests. It did not preserve the EFTS query echo, so the cause is unresolved. Phase 79 tests the endpoint itself and query semantics before deciding whether to abandon EFTS.

## Diagnostic matrix

- Generic baseline: Apple 10-Ks during 2025.
- Revance: company name, exact name, root form SC 13G, amendment form SC 13G/A, no form filter, padded/unpadded/quoted subject CIK.
- Osisko: company name and unpadded subject CIK.
- Fox: company name and unpadded subject CIK.
- Revance company-name query with ciks filter set separately to subject and FILED BY CIK.

The run preserves full response bodies, response hashes, URL, query echo, error payloads, hit metadata and accession-level expected-control matches. It uses 0.6-second spacing and no pagination beyond the first 100 hits because the sample windows are narrow.

## Decision rules

- If the generic baseline is zero, the endpoint or request contract is unresolved; stop using it until a known-good request is established.
- If generic baseline works but company-name positive controls fail, subject-side EFTS discovery is not validated; use filing-detail index pages / Entity Landing Page or the global master-index path audit.
- If company-name queries find all four cross-filer accessions with correct form/date, EFTS may proceed to a capped, stratified recall audit.
- Exact CIK and ciks-filter behavior are diagnostic only; no assumption is made that ciks means subject issuer.

No full-universe scan, data purchase, forward returns, alpha tests or production changes. F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen.
