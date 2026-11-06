# Phase 149 — OpenFIGI CUSIP crosswalk feasibility audit

**Date:** 2026-11-06  
**Status:** pending hosted API audit  
**Scope:** current identifier mapping only; no forward-return test, no vendor purchase/contact, no production change.

## Question

Can a free public identifier-mapping API provide a candidate bridge from the 553 distinct checksum-valid CUSIPs in the Phase 124/127 stratified 13D/13G filing sample to stable FIGI identifiers and current ticker/name metadata?

## Immutable input

- Phase 124 sample: run 42073725379, artifact 13436764625, SHA-256 85f69e083b5af65731c9bcfe24e8c75821fc0f2c2476bfa8ba573e2e884570dc.
- Phase 127 corrected CUSIP sample: run 42079517644, artifact 13438903901, ZIP SHA-256 b80d15d736ba6c45f4f3c5dd569604175e221414b31a28fd58a62010a805c166.
- Phase 127 CSV SHA-256: 5fc30ba22d4e3ef99113761059a5761f1fd4ae61a6d0e3a69961fe194d739447.
- Population: 599 actual 13D/G filings after one index alias quarantine; 571 checksum-valid CUSIP rows; 553 distinct CUSIPs.
- Input file SHA-256: 5c97aced36060bb89dafb57ba8e07f3487865ec5c5d6ce064aa285d50f3b90fb.

The earlier SEC header subject CIK/name fields are provenance only. Phase 126 found legacy header subject/issuer discrepancies, so they are not ground truth.

## API contract and protocol

OpenFIGI documents a free public v3 mapping endpoint accepting ID_CUSIP jobs. Unlisted equities are excluded by default; includeUnlistedEquities=true requests their inclusion. The unauthenticated limit is 25 requests per 60 seconds and 10 jobs per request. Response fields include FIGI, ticker, name, exchange code and security-type metadata.

The workflow uses 56 sequential batches of at most 10 CUSIPs, with a 2.5-second minimum interval (24 requests/minute). It uses no API key. Each batch records request/receipt timestamps, response hash, status and rate-limit headers. HTTP 429/5xx responses receive bounded retries respecting Retry-After.

Official documentation: https://www.openfigi.com/api/documentation

## Identity logic

- Deduplicate venue-level results by shareClassFIGI; fall back to compositeFIGI, then FIGI.
- Preserve all venue FIGIs, tickers, names and security types; do not silently choose one.
- Distinguish no match, one stable identity, multiple identities, mixed identity-key levels and records without a stable identifier.
- Preserve non-equity matches separately; do not treat every CUSIP as common stock.

## Hard limitations

The documented response does not include issuer CIK, effective-from/effective-to dates, or historical listing-status dates. includeUnlistedEquities=true broadens the result set but does not label which result is currently listed versus delisted. A present-day ticker cannot be backdated to the 13D/G filing date. A FIGI is a stable instrument identifier, but the current mapping response is not a historical security master.

## Decision gate

A high match rate can justify keeping OpenFIGI as a candidate current CUSIP-to-FIGI crosswalk for manual/independent validation. It cannot authorize historical returns or PIT event tests. Those still require effective-dated security identity, historical active-universe membership and a return source that can be joined without survivorship or ticker-reuse bias.

F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen.
