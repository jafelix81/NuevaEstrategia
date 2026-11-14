# Phase 404 — SEC Form 144 cross-feed provenance integrity

**Date:** 2026-11-14 UTC  
**Disposition:** PROVENANCE GAP CONFIRMED; APPEND-ONLY PER-FEED OBSERVATION LEDGER ADDED. NO NEW SIGNAL OR RETURN TEST.

## Finding

The Phase 403 bootstrap returned 50 entries from the Form 144 feed and five from the dedicated Form 144/A feed. Three accessions appeared in both feeds, producing 52 unique filing versions from 55 feed entries.

The first-seen event ledger correctly deduplicated each accession to one event row, but the cross-feed source provenance was not retained. The three overlapping Form 144/A accessions were first encountered in the `144` feed and then skipped in the `144A` loop because the shared accession set had already been updated. As a result, all 52 event rows have a single `feed_names` value even though three accessions were observed in both feeds. The three affected accessions in the bootstrap ledger are:

- `0001628280-26-073919`
- `0001950047-26-011100`
- `0001950047-26-011101`

This is a provenance/auditability defect, not a missing-event defect: all 52 unique accessions were captured and XML-resolved. It does mean the event ledger alone cannot reconstruct which official feed endpoints returned each overlapping accession.

## Correction

The capture client now:

1. Builds a deterministic accession-to-feed-name map across both snapshots before event deduplication.
2. Stores all source feed names on newly created first-seen event rows.
3. Counts new feed entries per feed independently of unique event rows, so overlaps remain visible in the poll summary.
4. Writes an append-only `feed_observations.csv` ledger with one row per `(poll_run_id, feed_name, accession)`, including the raw-feed SHA-256, feed update timestamp, response receipt time, URL and archive-path CIK.
5. Makes the per-feed ledger idempotent on workflow reruns with the same run ID; it never rewrites previous observations.
6. Leaves the existing `events.csv` first-seen ledger immutable. No historical rows are rewritten to manufacture provenance that was not captured at the time.

The new ledger records each feed's response independently. It does not claim that feed update time is first-public availability. The existing interval policy, 50-entry possible-gap guard, acceptance reconciliation and next-session-only economic eligibility remain unchanged.

## Validation

- Added regression for one accession present in both feeds; both feed observations must survive while the filing version remains one unique accession.
- Added idempotency regression for reruns of the same workflow run ID.
- Existing Phase 403 PIT, gap, identity and no-signal tests remain unchanged.
- No SEC network calls, forward returns, alpha, OOS, bootstrap, LOO or holdout use in CI.

## Current data status at audit time

The mainline Phase 403 state still has two successful bootstrap polls only:
- `poll_count=2`
- `last_successful_poll_mode=bootstrap`
- last successful poll: `2026-11-14T20:48:22Z`
- no scheduled prospective interval has yet been recorded
- all 52 bootstrap events remain research-ineligible and signal-ineligible

The first hourly scheduled poll after the bootstrap is expected at 2026-11-14 21:17 UTC, subject to GitHub Actions scheduling delay. A scheduled observation can be used only as a bounded feed-observation interval when both prior/current feed-window checks pass; the receipt timestamp remains an upper bound, not an exact public-availability timestamp.

## Research controls

- `signal_eligible=false` remains universal.
- `public_availability_certified=false` remains universal.
- `same_day_intraday_use_authorized=false` remains universal.
- Historical F80 membership and effective-dated security identity remain unverified.
- Form 144/A remains a version of the same proposed-sale event, not a second sale.
- `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen.
