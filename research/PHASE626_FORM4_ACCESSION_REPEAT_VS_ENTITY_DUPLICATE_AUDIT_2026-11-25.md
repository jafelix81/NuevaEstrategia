# Phase 626 — Form 4 accession-repeat vs exact entity-duplicate audit

**Date:** 2026-11-25  
**Status:** offline regression passed 78/78; awaiting review and natural post-merge production validation  
**Base:** main at `54c6e324b20e44307c9ed0244c70c9da3c8797fe`

## Production evidence reviewed

- Natural Form 4 run: [45714679017](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45714679017).
- Artifact: [15069775951](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45714679017/artifacts/15069775951).
- Persisted sidecar: `research/data/sec_form4_first_seen/entity_observations.csv`.
- Existing audit: [Issue #239](https://github.com/jafelix81/NuevaEstrategia/issues/239).

The run reported 491 same-feed repeated accession occurrences. This is accession-grain repetition, not an exact-entity duplicate count.

Independent parsing of the persisted sidecar found:

- 912 entity-observation rows.
- 421 feed/accession groups.
- 417 unique accession values across feeds.
- 910 distinct `(feed, accession, role, entity CIK, entity name)` keys.
- Two exact repeated entity rows, affecting two entity keys.
- 489 additional entity rows are legitimate multi-entity expansion beyond the first row per accession.
- Four cross-feed repeated accession occurrences remain separately identified.

The two exact repeats are the issuer and reporting-owner rows for accession `0001193125-26-477834`, observed at offsets 1200 and 1300 with different page-response hashes. The raw Atom page bodies were not retained, so the cause is unresolved; do not call this a proven pagination defect.

A different accession, `0001493152-26-054228`, has a reporting-owner row at offset 600 and issuer row at offset 700. These are distinct entities and must both be retained.

## Phase 626 implementation

This branch adds a separate append-only `entity_duplicate_audit.csv` sidecar. It does not alter or migrate the existing accession/entity ledgers.

The audit key is deliberately strict:

`feed_name | accession | entity_role | entity_CIK | NFKC/casefold/whitespace-normalized entity name`

Only parsed entities with a recognized role, CIK and non-empty name receive a key. Unparsed or incomplete rows are preserved with an unkeyed status; no fuzzy matching is attempted.

The poll summary now reports separately:

- `same_feed_repeated_accession_occurrences` — accession-level repeated feed occurrences.
- `exact_duplicate_entity_observation_rows` — exact repeated entity rows beyond the first.
- `exact_duplicate_entity_key_groups`.
- Exact repeated entity rows/groups spanning page offsets.
- `legitimate_multi_entity_accessions_split_across_pages`.
- Unkeyed entity observations.

The old `same_feed_duplicate_occurrences` summary field remains as a compatibility alias and has the same accession-occurrence meaning; it must not be interpreted as an exact entity-duplicate count.

## Regression coverage added

- Same accession with distinct reporting-owner and issuer entities across pages.
- Exact same entity repeated across page offsets, with normalized name matching.
- Multi-entity accession split across pages remains legitimate.
- Unparsed entities remain unkeyed and are not fuzzy-deduplicated.
- Existing same-feed and cross-feed accession-provenance tests continue to assert canonical event emission once.

## Research and production controls

- No raw page body was reconstructed or inferred.
- No issuer selection, canonical event count, watermark, or signal eligibility rule is changed.
- No transaction XML is downloaded by this correction.
- No event return, alpha, OOS, bootstrap or LOO test is authorized.
- No manual dispatch, rerun, cron change, paid data or vendor contact.
- `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen; options-data budget remains USD 0.

## Validation and acceptance gate

- [Run 45724430616](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45724430616) passed the Phase 476 offline regression: **78 tests passed**.
- The PR live-capture job was skipped as intended.
- The first CI attempt failed on a test-fixture line-continuation syntax error; that was corrected before the successful full regression.
- PR #240 remains Draft. Do not merge until reviewed. The first natural scheduled Form 4 capture after merge must confirm the new sidecar and separate counts against live Atom data.
