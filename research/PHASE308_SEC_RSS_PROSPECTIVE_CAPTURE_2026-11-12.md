# Phase 308 — SEC RSS prospective first-observation capture

**Date:** 2026-11-12  
**Status:** five consecutive complete current-feed snapshots captured; Phase 309 corrected event-level observation semantics and quarantined legacy placeholders.  
**Branch:** `phase308-sec-rss-prospective-capture`

## Purpose and acquisition design

Phase 307 showed that `owner=only` isolates ownership filings from unrelated 4-prefixed forms while preserving the page-zero Form 4 accession set. Phase 308 implements repeatable prospective capture:

- Query SEC Latest Filings Atom with `owner=only`, separately for exact Form 4 and Form 4/A.
- Scan count=100 pages with 20-row overlap, exact form-token filtering, accession/entity reassembly, stable page-zero recheck and a 50-page cap.
- Preserve raw Atom pages, response headers, poll-start/completion UTC times and SHA-256 in each run artifact.
- Maintain a cumulative accession ledger in `research/data/sec_rss_prospective_ledger.json`.
- Keep Atom `updated` separate from first observation; it is not relabeled as first-public time.
- Record capture gaps, incomplete scans, changed entity-row sets, missing/new accessions between complete snapshots and raw-page hashes.
- The hourly research automation updates `research/SEC_RSS_CAPTURE_TRIGGER.json`; workflow concurrency prevents overlapping Phase 308 captures.
- Raw artifacts are retained for 90 days. A compact ledger snapshot is committed once per UTC day; intervening hourly state is carried by the Actions cache and run artifacts.

## Hosted capture results

| Run | Status | Form 4 accessions / rows | Form 4/A accessions / rows | New accessions | Gap from prior complete end |
|---|---|---:|---:|---:|---:|
| [43142830440](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43142830440) | PASS | 1,022 / 2,111 | 18 / 36 | 1,040 initial | left-censored |
| [43143888820](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43143888820) | PASS | 1,022 / 2,111 | 18 / 36 | 0 | 8.839 min |
| [43144426570](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43144426570) | PASS | 1,022 / 2,111 | 18 / 36 | 0 | 4.294 min |
| [43144785036](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43144785036) | PASS | 1,022 / 2,111 | 18 / 36 | 0 | 2.589 min |
| [43145246814](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43145246814) | PASS | 1,022 / 2,111 | 18 / 36 | 0 | 3.666 min |

All five snapshots completed all 30 SEC requests, passed the head recheck and contiguous-overlap checks, and reported zero target structural errors and zero row-fingerprint conflicts. The cumulative ledger contains five captures and 1,040 unique accession keys. The four subsequent snapshots showed zero new accessions, zero changed entity-row sets and zero missing accessions relative to the preceding complete snapshot.

Artifacts:
- Initial: [13910476984](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43142830440/artifacts/13910476984), SHA-256 `3277211eccd5c048932a98a9fe7ac9b8061e167db66ab61449668041f1d78eb8`.
- Second: [13910598338](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43143888820/artifacts/13910598338), SHA-256 `dacb208aec85762975dab0452ad5b4be5d025be8f09a1d88004866d77946deda`.
- Third: [13909999401](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43144426570/artifacts/13909999401), SHA-256 `7df92cf7056e5f7b59c7bd9f8625f34845b043d8de957c55b6ccd029d1985ebe`.
- Fourth: [13910594586](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43144785036/artifacts/13910594586), SHA-256 `4ad1da53d979e996d0d2e20738f72712346b2a6563c8a1b921f7e91a013bd7be`.
- Fifth: [13911053496](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43145246814/artifacts/13911053496), SHA-256 `acbbf03bae44d7d07fff1666896ae8d8e2bed6da5d7310ac8a71f4c9c0f9e597`.

## Phase 309 timestamp correction

The original ledger implementation used the overall capture start as the interval end for every accession. That precedes the actual page response and is not a valid upper bound on when the collector first observed an accession.

Phase 309 now:
- Uses the earliest successful Atom page `poll_completed_at_utc` containing any row for an accession as the collector-observation time.
- Preserves the matching `poll_started_at_utc`, page offset and page label separately.
- Unions issuer/reporting-owner rows across pages without adding timestamps to row identity.
- Computes interval width from the previous complete-capture end to the event-specific response completion.
- Marks an event interval invalid if its event timestamp precedes the previous complete-capture boundary.
- Quarantines all 1,040 initial-run records: their old capture-start placeholders are moved to `legacy_capture_started_at_utc`; `first_observed_at_utc` and interval end are nulled, with quality `legacy_capture_start_pre_response_not_observation`. They remain left-censored and cannot be admitted as PIT events.

Hosted run [43144785036](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43144785036) passed **53/53 regressions** (13 Phase 308, 14 Phase 306, 8 Phase 305, 11 Phase 304, 7 Phase 303) and completed another 30/30-request capture. The artifact ledger confirms all 1,040 legacy placeholders were quarantined.

No new accession arrived in the five snapshots. Thus the page-level timestamp path is regression-validated but has not yet been observed on a newly arriving live accession. The next new accession is the first empirical live test of a non-left-censored interval.

## Durable legacy-ledger migration snapshot

The follow-up run [43145246814](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43145246814) passed **54/54 regressions** (14 Phase 308 + 14 Phase 306 + 8 Phase 305 + 11 Phase 304 + 7 Phase 303) and completed another 30/30-request capture. The migration-specific snapshot override correctly forced a repository commit even though the normal once-per-UTC-day snapshot had already been made.

The migrated five-capture ledger was committed as [1431ab323f37382fc9c6480e266db676b8afeee3](https://github.com/jafelix81/NuevaEstrategia/commit/1431ab323f37382fc9c6480e266db676b8afeee3). Artifact [13911053496](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43145246814/artifacts/13911053496) confirms all 1,040 legacy placeholders remain quarantined and the durable snapshot records five complete captures. This prevents a cache eviction from reverting the repository ledger to the pre-migration timestamp state.

## Interpretation limits and frozen controls

- The RSS current-feed is a rolling snapshot, not a historical archive.
- Exact SEC first-public timestamp: **not verified**.
- The initial 1,040 accessions remain left-censored; their legacy capture-start placeholders are explicitly unusable.
- Collector-observation intervals are not exact first-public timestamps.
- PAC/deletion events are not captured by this query.
- Strict PIT admission, return/alpha, bootstrap/LOO and chronological OOS: **not authorized / not run**.
- Holdout used: **false**.
- `F80_TOP20_PARTIAL50_BASELINE_C20`, production, universe, capital and parameters: unchanged.
- No vendor purchase, email sent, PR opened or merged.
