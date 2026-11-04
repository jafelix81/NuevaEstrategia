# Phase 81 — SEC ownership-disposition endpoint scope correction

**Date:** 2026-11-04  
**Branch:** `phase81-sec-ownership-issuer-endpoint-audit`  
**Decision:** **REJECTED for 13D/13G subject-issuer discovery before any live request.**

## What Phase 80 actually found

The Phase 80 artifact captured the SEC EDGAR Entity Landing Page's current `scripts/index.min.js`. It contains these URL templates:

- `/cgi-bin/own-disp?action=getowner&CIK={cik}`
- `/cgi-bin/own-disp?action=getissuer&CIK={cik}`

A first interpretation treated the names `getissuer` and `getowner` as a possible cross-filer 13D/13G subject/reporting-person index. Direct inspection of the surrounding JavaScript disproves that interpretation.

## Source-native semantics

The templates are assigned only when the SEC page's `headerData.insiderTransactionForOwnerExists` and `headerData.insiderTransactionForIssuerExists` flags are true. The associated page labels are reporter/issuer transactions. In the same script:

- `ownership` and `insiderTransactions` are explicitly filtered to Forms 3, 4 and 5;
- `beneficialOwnership` is a separate filter over the issuer page's own `headerData.submissions`, with form labels SC 13D, SC 13G, SCHEDULE 13D and SCHEDULE 13G.

The latter is still the current issuer CIK's own submissions list. It does not establish a complete cross-filer index of all investors' filings about that issuer. The `getissuer/getowner` links are therefore Section 16 insider-transaction navigation, not a validated 13D/13G subject-discovery API.

## Disposition

- Do **not** execute the seven-request 13D/13G positive-control pilot originally drafted for this branch.
- Do **not** use these endpoints to infer 13D/13G issuer coverage.
- No live SEC request was made by Phase 81; the only queued workflow for this branch is offline tests/compile and its live-audit step is guarded by a commit-message trigger that has not been used.
- The Phase 21C Form 4 standalone hypothesis remains killed; the existence of an SEC navigation endpoint is not a reason to revive it absent a materially different, preregistered mechanism.

The Phase 80 observation remains useful as a correction to the endpoint-discovery parser: it should distinguish Section 16 `own-disp` navigation from beneficial-ownership submission listings. This branch is archived as a **source-scope false lead**, not an empirical failure of SEC data.

## Correct next route

Return to the already-preregistered Phase 74 global-index / subject-identity plan:

1. Measure the full global 13D/13G master-index population by quarter before downloading filings.
2. Preserve master-index CIK, archive-path CIK, accession-prefix submitter CIK, SEC header SUBJECT COMPANY CIK, and FILED BY CIK as distinct roles.
3. Validate a stratified complete-submission sample against header and structured XML.
4. Only after the global index count and subject-identity gate pass, estimate the retrieval burden and target-universe recall.

The SEC EFTS exact-text route remains unvalidated: Phase 78's exact-CIK queries did not find the four cross-filer controls, and the Phase 79 live diagnostic step was skipped. Do not treat Phase 79's unit-test pass as a live endpoint result.

No forward returns, alpha tests, feature tuning, model changes or production changes. `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen.
