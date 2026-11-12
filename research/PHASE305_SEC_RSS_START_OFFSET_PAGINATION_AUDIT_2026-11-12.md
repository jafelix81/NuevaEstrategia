# Phase 305 — SEC Latest Filings RSS start-offset pagination audit

**Date:** 2026-11-12  
**Status:** completed; hosted live probe passed.  
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


## Hosted result — 2026-11-12 01:17 UTC

- Final workflow [43133481229](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43133481229) passed. The job completed **26/26** regression tests: 8 Phase 305, 11 Phase 304 and 7 Phase 303. All 14 SEC Atom requests returned HTTP 200. Artifact [13905777719](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43133481229/artifacts/13905777719), ZIP SHA-256 `b0306105144e91e6486f9b919ee1e1f7baf78a07c036c09755ff0fc6eb8b2bfd`.
- The SEC `start` parameter is effective and operates on **entity rows**, not unique accessions. With `count=100`, the overlaps were exactly 1 entity row between starts 0 and 99, 99 rows between starts 99 and 100, and 99 rows between starts 100 and 101. This is direct evidence of row-offset semantics.
- Across sampled Form 4 offsets 0, 99, 100, 101, 200, 500 and 1,000, exact-form filtering produced **202 unique Form 4 accessions and 413 unique entity rows**. The first three non-overlapping pages (0, 100, 200) had 50, 49 and 47 accessions respectively. No accession was shared across the 0/100 or 100/200 page boundaries in this snapshot; multiple-owner accessions of 4 and 8 entity rows were nevertheless observed and must be reassembled by accession.
- Important discovery: `type=4` behaves as a **prefix filter**, not an exact Form 4 filter. The start=500 and start=1,000 pages contained 87 non-target rows: 40-APP/A (12), 424B2 (43), 424B3 (9), 424B5 (10), 425 (3), 485BPOS (4) and 497 (6). The parser now extracts the complete form token before the spaced title separator and admits only exact `4` rows to the Form 4 panel. The non-target rows remain in the raw artifact and are counted, not discarded silently.
- The Form 4/A query returned 36 rows / 18 accessions at start=0 and empty pages at all later offsets. This is only the current feed snapshot; it does not prove long-term Form 4/A retention.
- Exact target-form rows had zero structural errors: no orphan accessions, Atom-id/link accession mismatches, target form mismatches, path/title CIK mismatches, duplicate entity rows or conflicting per-accession update timestamps. The earlier Phase 305 failures were offline test expectation/parser-hardening iterations; the final hosted run passed before the live probe result was accepted.

**Decision:** offset pagination can support controlled gap-recovery/backfill only if it is treated as entity-row pagination and the exact form token is revalidated on every row. Do not assume `type=4` is exact, do not assume pages align to accessions, and do not discard multi-owner rows. The next design gate is a deterministic contiguous-page scan with a conservative overlap and deduplication ledger, followed by a separate first-receipt capture design. No strict PIT or alpha admission.
