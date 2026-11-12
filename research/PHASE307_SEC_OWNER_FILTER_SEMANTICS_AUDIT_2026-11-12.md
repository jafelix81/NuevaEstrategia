# Phase 307 — SEC owner filter semantics audit

**Date:** 2026-11-12  
**Status:** protocol committed; live audit pending.  
**Branch:** phase307-sec-rss-owner-only-filter-audit

## Research question

Phase 306 showed that the SEC query type=4 with owner=include contains a large number of unrelated 4-prefixed forms. Test whether owner=only isolates ownership filings and whether owner=exclude acts as a valid negative control, while preserving the exact Form 4 accession set.

## Protocol

- Query type=4 and type=4/A under owner=include, owner=only and owner=exclude.
- For owner=only, scan starts 0, 80, 160, 240, 320 and 400 with count=100 and 20-row overlap; re-fetch page zero for each form after the scan.
- For include/exclude controls, query starts 0 and 80.
- Preserve every raw Atom response, headers, UTC poll times and SHA-256.
- Parse the full form token exactly; normalize Issuer, Reporting and Filer CIK/role; deduplicate only the event ledger, not the raw pagination sequence.
- Compare ordered overlap signatures and page-zero rechecks.
- Treat owner=only isolation, owner=exclude negative-control behavior, and preservation of page-zero Form 4 accessions as separate hypotheses.

## Decision rule

owner=only is useful for capture only if it contains no non-ownership forms in the type=4 query (allowing 4/A as an ownership-form spillover), the type=4/A query contains only 4/A, owner=exclude returns no exact Form 4/4/A accessions, the include control demonstrates the expected non-target prefix contamination, and the page-zero exact Form 4 accession set is preserved.

A successful HTTP/parser audit does not imply the filter hypothesis passed. If the SEC endpoint behaves differently, record the observed behavior and do not assume owner=only is exact.

## Interpretation limits

This is a current-feed query-semantics audit, not a historical coverage study. No first-public timestamp, strict PIT, PAC event stream, return/alpha, bootstrap/LOO, chronological OOS or holdout claim is made.

F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen. No production, universe, capital or parameter changes.

## Hosted result

Pending.
