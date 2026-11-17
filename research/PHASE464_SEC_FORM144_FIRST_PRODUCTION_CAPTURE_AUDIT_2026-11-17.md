# Phase 464 — First post-migration SEC Form 144 production-capture audit

**Audit time:** 2026-11-17 21:49 UTC  
**Main HEAD at preflight:** `1992e73625432851ea4f7d98a473204f66ce5a0d` (automated ledger commit from Phase 403 run 44179257367)  
**Disposition:** production schema migration succeeded and 54 filing versions were appended. The Form 144 endpoint remains gap-contaminated; only four bounded Form 144/A amendment versions qualify as raw research observations. No newly eligible observation matched the current 290-CIK diagnostic manifest. No signal or return test is admitted.

## 1. Preflight and no-duplicate check

- Repository: `jafelix81/NuevaEstrategia`, default branch `main`.
- Latest 100 Actions runs: 100 completed; zero in progress or queued in that window. Total Actions runs reported by GitHub: 7,718.
- Branch inventory: 296 branches (100 + 100 + 96 across three pages).
- Open PRs: 56. Workflow files: 76.
- Latest scheduled capture: [Phase 403 run 44179257367](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44179257367), status/conclusion success.
- No workflow was dispatched, rerun or duplicated.
- The workflow file at the run's exact head SHA and current main both specify `47 * * * *`. GitHub records this schedule-event run as created/started at 2026-11-17 21:23:10 UTC, not at minute :47. This timestamp/cron mismatch is unresolved; do not change the cron based on one observation. Compare the next scheduled event before diagnosing schedule reliability.

## 2. Production migration succeeded

Run 44179257367 executed the previously unverified Phase 454 migration against the committed `events.csv` before the live capture.

The artifact's `schema_migration.json` reports:

- `reason=header_migrated`
- `changed=true`
- `rows_migrated=52`
- Added `cross_feed_provenance_complete` and `capture_poll_status`.
- Both new fields were left blank for the 52 historical bootstrap rows; no historical provenance was fabricated.

The committed ledger now has 43 header fields and 106 event rows (52 bootstrap + 54 new filing-version rows). The workflow bot committed the migration and append-only capture in [commit 1992e73625432851ea4f7d98a473204f66ce5a0d](https://github.com/jafelix81/NuevaEstrategia/commit/1992e73625432851ea4f7d98a473204f66ce5a0d), changing only the four SEC first-seen data/state files.

## 3. Live capture result

Run: [44179257367](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44179257367)  
Jobs:
- `offline-regression`: success.
- `live-capture`: success; migration, SEC feed capture, append/commit and artifact upload all completed.

Artifact: [14371301851](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44179257367/artifacts/14371301851)  
ZIP SHA-256: `e1e1baa44b99eef37cbb2f31494ca6cd00ed2d30f1b663f0eb8591a407db7142`.

Poll began at 2026-11-17 21:23:27 UTC and completed at 21:23:39 UTC. Both feed responses record receipt upper bound 21:23:27 UTC.

| Measure | Result |
|---|---:|
| New event-ledger filing versions | 54 |
| XML resolved | 54/54 |
| Acceptance reconciliations added | 54 |
| Acceptance reconciliations unresolved | 0 |
| Atom `updated` exactly equals SEC filing-detail `Accepted` | 54/54 |
| Feed-observation rows appended | 58 |
| Current-candidate CIK matches | 14 |
| Raw research-observation-eligible rows | 4 |
| Signal-eligible rows | 0 |

The 58 feed-observation rows preserve 50 observations from the `144` endpoint and eight from the dedicated `144/A` endpoint. Four of the eight 144/A observations were already known filing versions; they were re-observed in the feed ledger but not appended as new event rows.

## 4. Feed-specific coverage decision

| Endpoint | Entries returned | Previous latest present? | Gap status | New event rows | Decision |
|---|---:|---|---|---:|---|
| `type=144` | 50 | No | Possible feed-window gap | 50 | Quarantine all 50 |
| `type=144/A` | 8 | Yes | No detected gap | 4 | Retain as bounded filing-version observations |

### Form 144 endpoint

The `type=144` endpoint returned exactly 50 entries although the request asks for 100. The prior latest accession (`0001950047-26-011102`) was absent. The guard correctly marked `POSSIBLE_FEED_WINDOW_GAP`, suppressed the interval lower bound and set all 50 new rows to research-ineligible. The 14 current-candidate CIK matches all occur in this gap-contaminated group and cannot be promoted.

This is an observed response-window limitation, not proof that the endpoint's permanent maximum is 50. The next source-feasibility task is to establish official pagination/offset behavior or reconcile the feed against the SEC daily index before treating any `type=144` interval as complete.

### Form 144/A endpoint

The dedicated endpoint returned eight entries and contained its prior latest accession (`0001950047-26-011101`). Four accessions were new to the event ledger and had a bounded interval from 2026-11-16 11:59:27 UTC through the 2026-11-17 21:23:27 UTC receipt upper bound.

All four are Form 144/A amendments with explicit parent accessions:

| Issuer | Amendment accession | Parent accession |
|---|---|---|
| Ceribell, Inc. | `0001959173-26-008026` | `0001959173-26-008019` |
| NRG Energy, Inc. | `0001974078-26-000419` | `0001974078-26-000418` |
| Amplitude, Inc. | `0001959173-26-008070` | `0001959173-26-008066` |
| Universal Electronics Inc. | `0000921895-26-003196` | `0000921895-26-003017` |

They are four newly observed filing versions, not four independent proposed-sale events. Keep each amendment immutable and group it with its parent for economic event analysis. None matched the current 290-CIK diagnostic candidate manifest.

## 5. Point-in-time interpretation

- Atom `updated` matched SEC filing-detail `Accepted` to the exact second for all 54 reconciled accessions in this poll. This validates the feed field's acceptance-time semantics in this sample only; it does not certify first public availability at acceptance.
- The actual first-seen field is the feed response receipt upper bound, 21:23:27 UTC, not an exact public-release timestamp.
- Across all 54 new versions, receipt-upper-bound minus acceptance ranged from 98 to 101,348 seconds. For the four bounded 144/A amendments it ranged from 83,338 to 101,348 seconds.
- The four 144/A versions are eligible only as bounded raw filing observations under the existing conservative gate. Their first usable research session must be after the observed receipt upper bound, not backdated to acceptance or filing date.
- A Form 144 is a notice of a proposed sale, not proof that a sale was executed. A Form 144/A is a filing amendment, not another independent sale.

## 6. No signal admission

For every new row:
- `signal_eligible=false`;
- `public_availability_certified=false`;
- `historical_f80_membership_verified=false`;
- `same_day_intraday_use_authorized=false`.

The 290-CIK Phase 401 manifest is a current-candidate diagnostic, not an effective-dated historical F80 security master. The 14 matches in the 144 gap group do not establish F80 membership. The four bounded 144/A amendments have zero candidate matches. No return, alpha, OOS, bootstrap, LOO or holdout test was run.

## 7. Reproducibility and next gates

Added a read-only auditor and nine offline tests that recompute the production-run counts and fail if the committed ledgers drift from the recorded audit. The Phase 403 workflow's PR path filter and offline regression command are extended to run these tests; the live-capture job remains excluded on pull requests.

Next:
1. Observe the next scheduled run and reconcile its actual event timestamp against the configured :47 UTC cron.
2. Resolve the `type=144` 50-entry gap with verified pagination/offset or SEC daily-index cross-source coverage; do not relax the guard.
3. Preserve 144/A parent lineage and distinguish amended filing versions from underlying proposed-sale events.
4. Rebuild effective-dated issuer/security identity and historical F80 membership before any universe-level test.
5. Keep FINRA, CFTC, Cboe/Nasdaq options and other source audits independent; do not make Form 144 the sole Smart Money line.

`F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen. No production strategy, universe, parameters, capital, exposure, holding period or holdout changed.
