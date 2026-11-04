# Phase 81 — SEC ownership issuer/reporter endpoint audit

**Date:** 2026-11-04  
**Branch:** `phase81-sec-ownership-issuer-endpoint-audit`  
**Status before live run:** preregistered bounded transport/positive-control audit; no alpha test authorized.

## Discovery that motivates this phase

The Phase 80 artifact captured the current SEC EDGAR Entity Landing Page JavaScript. In `scripts/index.min.js`, the SEC defines two legacy ownership-disposition URL templates:

- issuer-side: `/cgi-bin/own-disp?action=getissuer&CIK={cik}`
- reporter-side: `/cgi-bin/own-disp?action=getowner&CIK={cik}`

The Phase 80 endpoint extractor did not surface these templates because its path allow-list omitted `cgi-bin` / `own-disp`. This is a bounded discovery correction, not evidence that either endpoint works or is complete.

## Preregistered pilot

Seven SEC requests only:

- Three subject-issuer CIKs: Revance, Osisko Development, and Fox Corporation.
- Four reporter/filer CIKs corresponding to four known cross-filer SC 13D/13G accessions.
- For each subject issuer, test whether `getissuer` returns its expected accessions.
- For each reporting person, test whether `getowner` returns its expected accession.
- Preserve raw HTML, response hash, status, final URL, table-row count, extracted accession IDs, and positive-control matches.

The SEC's own template uses numeric (unpadded) CIK values in the URL. The audit therefore normalizes CIKs to ten digits internally and emits the unpadded integer form in the request.

## Gate

A current endpoint positive-control pass requires HTTP 200 on all seven calls and all four expected accessions found in both the issuer-side and reporter-side queries. Partial success is reported explicitly; it is not promoted to a coverage pass.

Even a complete positive-control pass does **not** establish:

1. historical endpoint availability or stable pagination;
2. historical universe/security identity;
3. recall or precision across the frozen 335-name universe;
4. ex-ante timestamp/vintage reproducibility;
5. completeness of 13D/13G amendments or reporting-group identity.

Any follow-on work must first perform a stratified accession-level recall/precision audit against an independent known universe and verify historical retrieval/availability. Filing date remains the conservative knowledge timestamp. No event date may be substituted without separate PIT certification.

## Explicit non-goals

No broad crawl, forward returns, alpha test, feature tuning, model change, or production change. `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen.
