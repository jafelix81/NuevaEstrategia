# Phase 304 — SEC Latest Filings RSS count-cap and accession-grain coverage audit

**Date:** 2026-11-12  
**Status:** completed; hosted live probe passed.  
**Branch:** \`phase304-sec-rss-count-cap-accession-coverage-audit\`

## Research question

Phase 303's one-time probe requested \`count=100\` and received 100 Form 4 entity rows but only 50 unique accessions; the Form 4/A query returned 36 rows and 18 accessions. Before a prospective capture can be designed, determine whether the RSS \`count\` parameter caps entity rows or filings, whether larger counts are accepted, and whether accession sets expand monotonically.

This audit deliberately preserves entity rows. It does not assume that every filing has exactly two rows: joint/multiple reporting owners may create more than two rows.

## Protocol

- Query Forms 4 and 4/A separately at requested counts 100, 200, 500 and 1,000.
- Record UTC poll start/completion, HTTP status and headers, response bytes, SHA-256, raw Atom body, row count, unique accessions and the oldest/newest \`updated\` values.
- Reconcile Atom \`id\` accession to the accession parsed from the filing link.
- Check query form, path/title CIK consistency, duplicate entity rows, per-accession role counts, and conflicting \`updated\` values.
- Compare accession sets across increasing count requests. A non-nested result is flagged rather than silently treated as complete.
- For the largest successful snapshot of each form, download the newest and oldest available complete submissions and compare Atom \`updated\` with SEC-HEADER \`ACCEPTANCE-DATETIME\`.
- Use at least one second between SEC requests. Preserve raw response bytes in the workflow artifact.

## Interpretation limits

- Atom \`updated\` was equal to acceptance time in 2/2 Phase 303 cross-checks. It is not treated as first-public availability.
- Poll time is an observation time, not exact publication time.
- This is a single-snapshot capacity audit, not a 30-day capture and not historical backfill.
- No insider transaction is labelled discretionary, informed, or open-market solely from this feed.
- No strict PIT, return/alpha, bootstrap/LOO, chronological OOS, or holdout test is authorized.

## Frozen controls

\`F80_TOP20_PARTIAL50_BASELINE_C20\` remains frozen. No production, universe, capital, parameter, vendor, licensing, or holdout changes are allowed in this phase.

## Hosted result

Pending.


## Hosted result — 2026-11-12 01:10 UTC

- Workflow [43132595262](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43132595262) passed. Job `count-cap-audit` completed successfully; 11 Phase 304 tests and 7 Phase 303 parser regressions passed (18/18).
- All 8 Atom requests succeeded: Forms 4 and 4/A at requested counts 100, 200, 500 and 1,000. For Form 4, every request returned exactly **100 entity rows / 50 unique accessions**; increasing `count` did not expand the result. For Form 4/A, every request returned **36 rows / 18 accessions**. The observed Form 4 response therefore behaves as if capped at 100 entity rows, or the larger `count` values are ignored; the probe does not distinguish those server-side explanations.
- Accession sets were nested across increasing requests for both forms. The larger requests did not reveal additional accessions in this snapshot. Form 4's 50 entries span 2026-11-10 20:30:04–21:59:02 ET; Form 4/A's 18 entries span 2026-11-09 12:16:40–2026-11-10 13:29:39 ET.
- The largest successful snapshot showed zero orphan rows, Atom-id/link accession mismatches, query-form mismatches, path/title CIK mismatches, duplicate entity rows, form conflicts or per-accession `updated` conflicts. All 50 Form 4 and 18 Form 4/A accessions in this snapshot had one Issuer row and one Reporting row; this is a sample property, not a parser assumption. Multiple-owner rows remain supported and preserved.
- Four complete submissions (newest and oldest from each form) were downloaded and SHA-256 hashed. Atom `updated` equaled SEC-HEADER `ACCEPTANCE-DATETIME` in **4/4** additional cross-checks. Combined with Phase 303, this strengthens the acceptance-time interpretation but still does not establish first-public availability.
- Artifact [13905652996](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43132595262/artifacts/13905652996), ZIP SHA-256 `ae8a81b0d3067348fdcb36063b659cc38a8b9ef6a0987c250866bf5c3e4d2dda`, preserves eight raw Atom responses, four complete submissions and the result JSON. No raw source data was committed to the repository.

**Decision:** do not assume `count=1000` increases feed coverage. The next gate is a controlled `start`-offset test at `0, 100, 200, 500, 1000`, preserving raw entity rows and checking for accession splits/overlaps across page boundaries. Only after offset semantics are established should a prospective polling cadence or gap-recovery design be finalized. No strict PIT or alpha admission.
