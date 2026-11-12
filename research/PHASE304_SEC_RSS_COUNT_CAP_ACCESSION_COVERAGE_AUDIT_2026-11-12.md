# Phase 304 — SEC Latest Filings RSS count-cap and accession-grain coverage audit

**Date:** 2026-11-12  
**Status:** pending hosted live probe.  
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
