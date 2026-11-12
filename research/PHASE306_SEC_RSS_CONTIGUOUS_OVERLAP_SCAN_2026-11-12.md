# Phase 306 — SEC Latest Filings RSS contiguous overlapping scan

**Date:** 2026-11-12  
**Status:** completed; hosted live scan passed, Form 4 feed coverage remains capped.  
**Branch:** phase306-sec-rss-contiguous-overlap-scan

## Research question

Phase 305 established that the SEC Atom start parameter offsets entity rows, not unique accessions; count=100 is the effective page size; and type=4 is a prefix filter that includes non-target forms. This phase tests whether a contiguous, overlapping scan can reconstruct the current Form 4 and Form 4/A feed snapshot without losing multi-owner rows or silently claiming completeness when the feed changes during pagination.

## Final hosted result

Final workflow [43141258597](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43141258597) passed **39/39 tests** (13 Phase 306, 8 Phase 305, 11 Phase 304, 7 Phase 303). All **53 SEC Atom requests** succeeded and parsed. Artifact [13910016050](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43141258597/artifacts/13910016050), ZIP size 225,439 bytes, SHA-256 1930481f22dae87525273ba028901df5ec0e10009c8b1edbffef4783c399720c.

### Form 4 query (type=4, owner=include)

- 50 contiguous pages at starts 0 through 3,920, count=100, step 80, 20-row overlap; 4,020 raw row positions covered.
- The page cap was reached with the final page still full. **This is not a complete current-feed scan**; additional rows may exist beyond the sampled 4,020 positions.
- Exact title-token filtering yielded **979 unique Form 4 accessions and 2,025 unique Form 4 entity rows**.
- The same query contained **1,939 unique non-target entity rows**. The largest contaminant was 424B2 (1,510 rows), followed by 40-APP/A (66), 425 (51), 497 (48), 424B3 (75), 424B5 (34), 485BXT (32), and other 4-prefixed forms. Exact Form 4 rows were 51.1% of the unique raw rows in this scanned window; non-target rows were 48.9%.
- Across 5,000 raw row appearances, 3,964 distinct row identities were observed. There were 1,036 repeated appearances: 65 exact duplicate rows within pages and 971 row identities repeated across overlapping pages.
- **All 49 adjacent 20-row overlaps matched exactly in order**, and the final page-zero recheck was identical to the initial page zero. There were zero row-fingerprint conflicts and zero target-form structural errors.
- 250 accessions appeared in multiple page windows; 22 had different entity-row subsets across those windows. The accession ledger must therefore reassemble all entity rows by accession before any event is consumed.

### Form 4/A query (type=4/A, owner=include)

- One page contained 36 entity rows representing **18 unique accessions**; the next page was empty, so the observed Form 4/A current snapshot reached its tail.
- The final page-zero recheck was identical. No row-fingerprint conflicts, orphans, or target-form structural errors were found.
- This establishes only the current feed snapshot, not historical retention or a 30-day capture guarantee.

## Important correction made during this phase

The preliminary 25-page scan used set intersection to validate page overlaps and reported one 19/20 mismatch. Inspection of the preserved raw Atom pages showed that the 20-row overlap was in fact identical in order; an exact duplicate Filer row reduced the set cardinality. The final implementation now compares ordered row signatures (preserving multiplicity), normalizes Filer CIK/role for raw-row identity, and separately counts within-page duplicates. The final 50-page scan then passed all 49 overlap checks.

The initial 25-page scan was not used as the final coverage result. The first workflow import-path failure and the intermediate stale-test failure both occurred before SEC requests; the final run is the authoritative Phase 306 result.

## Interpretation and next gate

- The type=4 + owner=include query is materially contaminated by other 4-prefixed forms and remains too expensive to call complete within a 50-page cap.
- **Next: test SEC owner=only semantics** against the same exact-form parser and a few contiguous offsets. If it isolates ownership forms, it may provide a much cleaner, cheaper capture path. Do not assume this parameter is exact until live results and negative controls confirm it.
- Then design prospective first-observation capture with raw response hashes, UTC poll intervals, missed-run/gap markers and accession-level deduplication.
- Atom updated remains an acceptance-time proxy in prior cross-checks, not an independent first-public timestamp. The RSS scan does not establish exact first public receipt.
- Keep Form 4/A separate from actual PAC/deletion events; no PAC event stream was captured.

## Frozen controls

- Strict PIT admitted: **false**.
- Exact first-public timestamp verified: **false**.
- Return/alpha, bootstrap/LOO and chronological OOS tests: **not run**.
- Holdout used: **false**.
- F80_TOP20_PARTIAL50_BASELINE_C20, production, universe, capital and parameters: **unchanged**.
- No vendor purchase/contact, no email sent, no PR opened or merged.
