# Phase 305 — SEC Latest Filings RSS start-offset pagination audit

**Date:** 2026-11-12  
**Status:** pending hosted live probe.  
**Branch:** \`phase305-sec-rss-start-offset-pagination-audit\`

## Research question

Phase 304 found that Forms 4 and 4/A RSS queries returned the same rows at requested \`count=100, 200, 500, 1000\`; the Form 4 query remained at 100 entity rows / 50 accessions. This phase tests whether the SEC \`start\` parameter provides offset pagination and whether entity rows for one accession can be split across page boundaries.

## Protocol

- Query Forms 4 and 4/A with \`count=100\` and \`start=0, 99, 100, 101, 200, 500, 1000\`.
- Preserve raw Atom responses, HTTP headers, UTC poll times and SHA-256.
- Reconcile Atom entry IDs to filing-link accessions, query form and path/title CIK.
- Preserve all Issuer and Reporting rows; do not assume exactly two entity rows per accession.
- Measure page hashes, row/accession sets, cross-page overlap and accession splits between adjacent 0/100 and 100/200 pages.
- Keep the test strictly at source pagination/coverage level.

## Interpretation limits

- Atom \`updated\` is an acceptance-time proxy in the Phase 303/304 cross-check samples, not first-public time.
- An accession split across pages must be reassembled by accession without dropping or duplicating entity rows.
- A single offset snapshot cannot establish feed retention duration, historical backfill completeness or prospective gap recovery.
- No strict PIT, return/alpha, bootstrap/LOO, chronological OOS or holdout test is authorized.

## Frozen controls

\`F80_TOP20_PARTIAL50_BASELINE_C20\` remains frozen. No production, universe, capital, parameter, vendor, licensing or holdout changes.

## Hosted result

Pending.
