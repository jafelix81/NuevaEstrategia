# Phase 309 — SEC RSS event-level first-observation bound correction

**Date:** 2026-11-12  
**Status:** IMPLEMENTED; hosted regressions passed; live capture complete.  
**Branch:** `phase308-sec-rss-prospective-capture`

## Finding

Review of the first Phase 308 artifact showed that the ledger set every new accession's `first_observed_at_utc` and interval end to the overall capture start. The first request actually began 42 microseconds later and completed at a later timestamp. More generally, a multi-page scan can span multiple seconds, so capture start is not a valid upper bound on when a page response first exposed a given accession.

The field represented a pre-response placeholder, not a collector observation. Retaining it as an observation timestamp could allow an event to appear available before the collector had received the response.

## Correction

The capture parser now associates every accession with the earliest successful Atom page response containing any of its entity rows:

- `first_observed_at_utc` and `first_observation_interval_end_utc` use that page's `poll_completed_at_utc`.
- The matching `poll_started_at_utc`, page offset and page label are preserved separately.
- Issuer and reporting-owner rows are still unioned across all pages for the accession.
- The interval lower bound remains the end of the previous complete capture.
- The width is computed using the event-specific response completion, not the overall capture start.
- If the event timestamp precedes the prior complete boundary, the interval is marked invalid and its width is null.

This is the collector's first-observation interval, not the SEC's exact first-public timestamp.

## Legacy-ledger quarantine

The initial Phase 308 run (43142830440) created 1,040 left-censored records before page-level timestamps were implemented. Their capture-start placeholders cannot be treated as actual observations.

The migration now:
- moves the old value to `legacy_capture_started_at_utc`;
- sets `first_observed_at_utc` and `first_observation_interval_end_utc` to null;
- sets `first_observation_interval_valid=false`;
- labels the value `legacy_capture_start_pre_response_not_observation`;
- preserves `left_censored_no_prior_complete_capture` as the interval quality.

The fourth-capture artifact was inspected directly: all **1,040/1,040** legacy placeholders were quarantined. No record was silently assigned a false observation time.

## Regression and hosted validation

Final workflow: [43144785036](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43144785036)  
Artifact: [13910594586](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43144785036/artifacts/13910594586)  
Artifact ZIP SHA-256: `4ad1da53d979e996d0d2e20738f72712346b2a6563c8a1b921f7e91a013bd7be`

- Phase 308: **13/13** tests.
- Phase 306: 14/14.
- Phase 305: 8/8.
- Phase 304: 11/11.
- Phase 303: 7/7.
- **Total: 53/53** regressions passed.
- Live capture: **30/30** SEC requests successful; complete contiguous snapshot; 1,022 Form 4 accessions / 2,111 entity rows and 18 Form 4/A accessions / 36 entity rows.
- Zero new accessions, zero changed entity-row sets, zero missing accessions, zero target structural errors and zero row-fingerprint conflicts.
- Five complete snapshots are now recorded; the latest interval from previous complete capture end to new capture start was 2.589 minutes.

No new accession arrived in these snapshots. Therefore the page-level event timestamp is validated by deterministic regression tests, but a live non-left-censored accession interval has not yet been observed. Continue prospective capture until at least one new accession appears and its interval can be inspected.

## Research disposition

- No strict PIT admission yet.
- No forward-return/alpha test, bootstrap/LOO or chronological OOS.
- No holdout use; legacy holdout remains `CONSUMED_NOT_PRISTINE`.
- `F80_TOP20_PARTIAL50_BASELINE_C20`, production, universe, capital and parameters remain frozen.
- No email sent, data purchased, or PR opened/merged.

## Next gate

On the next new accession:
1. Verify it is absent from the preceding complete snapshot.
2. Confirm the ledger interval starts at the previous complete-capture end.
3. Confirm the interval ends at the first successful page response completion containing the accession.
4. Reconcile the raw Atom page hash, entity rows and exact form token.
5. Check for capture gaps and head-page drift.

Only after repeated new-event observations and independent historical knowledge-date checks should this collector be considered for a strict PIT event panel.


## Durable-snapshot follow-up — run 43145246814

A final regression and capture run verified that the legacy timestamp migration is persisted even when the ordinary daily repository snapshot has already occurred.

- Hosted run [43145246814](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43145246814) passed **54/54 regressions** (14 Phase 308, 14 Phase 306, 8 Phase 305, 11 Phase 304, 7 Phase 303).
- Another complete live capture passed **30/30 requests** with 1,022 Form 4 accessions / 2,111 entity rows and 18 Form 4/A accessions / 36 entity rows.
- No new accessions, entity-row changes, missing accessions, structural errors or row-fingerprint conflicts occurred. The interval from the previous complete-capture end to this capture start was 3.666 minutes.
- The migration-specific snapshot override set `repo_snapshot_due=true` despite the same-day snapshot already being committed. The five-capture migrated ledger was durably committed as [1431ab323f37382fc9c6480e266db676b8afeee3](https://github.com/jafelix81/NuevaEstrategia/commit/1431ab323f37382fc9c6480e266db676b8afeee3).
- Artifact [13911053496](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43145246814/artifacts/13911053496), SHA-256 `acbbf03bae44d7d07fff1666896ae8d8e2bed6da5d7310ac8a71f4c9c0f9e597`, confirms the durable ledger has five captures, 1,040 accessions, and all 1,040 legacy placeholders quarantined.

This closes the persistence gap: cache loss can no longer roll the branch's committed ledger back to the pre-migration timestamp placeholders. The first 1,040 accessions remain left-censored; no live newly arriving accession has yet exercised a bounded event interval.
