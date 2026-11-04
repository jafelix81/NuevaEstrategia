# Phase 80 — SEC Entity Landing Page subject-side discovery feasibility

**Date:** 2026-11-04  
**Branch:** phase80-sec-entity-landing-page-pit-audit  
**Scope:** three subject issuers / four cross-filer controls; raw page and script inspection only.

## Why this route

Phase 78's direct EFTS query construction returned zero hits in 13/13 HTTP-200 requests. Do not scale that implementation.

A more promising official route is the SEC EDGAR Entity Landing Page. Its Ownership disclosures section explicitly separates insider transactions from beneficial ownership (Schedule 13D and 13G). The search-indexed Revance entity page (CIK 0001479290) lists the March 6, 2025 Schedule 13G/A positive control. SEC filing-detail pages independently identify subject and filed-by entities for Revance, Osisko and Fox:
- Revance: accession 0000019617-25-000296, subject CIK 0001479290, filed by JPMorgan CIK 0000019617, filed 2025-03-06.
- Osisko: accession 0001062993-25-015044, subject CIK 0001431852, filed by Double Zero Capital CIK 0002083861, filed 2025-08-28.
- Fox: accession 0000950157-25-000788, subject CIK 0001754301, filed by MFT SH Family Trust CIK 0002080603, filed 2025-09-12.
- Fox: accession 0000950170-25-114595, subject CIK 0001754301, filed by Cruden 2 LLC CIK 0002084288, filed 2025-09-12.

The page is a subject-centric discovery candidate, but the raw HTML may be a client-rendered shell. Phase 80 checks the HTML and a bounded set of linked JavaScript assets to identify a stable JSON/data endpoint.

## Bounded audit

- Five page requests: Revance default, owner=exclude, owner=include; Osisko default; Fox default.
- Up to eight same-domain JavaScript assets fetched.
- Search raw HTML and scripts for the four known accessions, issuer CIKs, company names and candidate API paths.
- Preserve raw HTML/JS and SHA-256, response status, content type, script sources and candidate endpoints.
- No global 335-CIK crawl, no filing-document crawl, no forward returns.

## Decision

If raw HTML or a linked endpoint exposes the subject-side filing rows with pagination, date/form filters and stable accession IDs, validate the four controls and then run a capped 20-issuer coverage sample. If the page is only a client-rendered shell, use the discovered endpoint only after confirming it is public, reproducible and rate-limit compliant. Do not infer PIT history from a current landing page.

No purchases or production changes. F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen.
