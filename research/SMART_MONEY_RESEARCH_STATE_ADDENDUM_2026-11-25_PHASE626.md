# Smart Money Research state addendum — 2026-11-25 — Phase 626

## Current verified checkpoint

Main at audit start: `54c6e324b20e44307c9ed0244c70c9da3c8797fe`.

Latest natural SEC Form 4 run reviewed: [45714679017](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45714679017). Both offline and live jobs succeeded. Artifact 15069775951 is present. The run recorded 415 new canonical metadata events, 912 entity observations, both Form 4/4-A watermarks, no issuer identity mismatches, no unknown roles and no quarantined accessions. No filing XML was downloaded for the 415 new events; zero research-observation-eligible and zero signal-eligible rows.

## Phase 626 — duplicate semantics

The existing `same_feed_duplicate_occurrences` field counts repeated accessions in a feed, not exact repeated entities. Production sidecar audit found 912 rows, 910 distinct entity keys and two exact repeated entity rows. The two repeated entity rows span offsets 1200 and 1300 for accession `0001193125-26-477834`; raw Atom page bodies are not retained, so the reason is unresolved.

A new branch proposes a separate append-only `entity_duplicate_audit.csv` with strict exact entity keys, cross-page duplicate flags, legitimate multi-entity cross-page counts and unkeyed rows. Existing ledgers remain unchanged. The old summary field is retained as a compatibility alias and paired with the clearer `same_feed_repeated_accession_occurrences`.

Implementation passed offline CI (78/78 tests) in [Run 45724430616](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45724430616); the live-capture job was skipped. PR #240 remains Draft pending review and natural post-merge production validation. No production rollout has occurred.

## Other source priorities

- Form 4: continue conservative first-seen capture and bounded backfills; transaction-line owner attribution remains unverified where filings have multiple owners.
- Form 144: proposed sales remain non-execution observations; do not infer completed sales.
- 13F: first-seen workflow is configured but no production capture is yet verified at this checkpoint; apply acceptance-time legal dissemination floor before signal use.
- 13D/G: global-index discovery is integrated; bounded live sample remains a separate manual gate.
- FINRA ATS: prioritize stable-row publication vintages and effective-dated security identity; do not substitute lastReportedDate for public availability.
- FINRA Reg SHO: continue fail-closed; overlapping facility rows are not safely additive.
- CFTC TFF: historical archive remains descriptive until prospective vintage count meets the preregistered minimum.
- Options: no purchase or quote request; authorized budget remains USD 0.

## Model controls

`F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen. No universe, capital, exposure, cost, parameter or production change. No incremental alpha/OOS, bootstrap or LOO result has been established by this checkpoint.
