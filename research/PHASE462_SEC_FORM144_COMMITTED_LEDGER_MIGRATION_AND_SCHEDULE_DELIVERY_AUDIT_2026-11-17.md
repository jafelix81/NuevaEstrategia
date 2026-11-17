# Phase 462 — SEC Form 144 committed-ledger migration replay and schedule-delivery audit

**Audit time:** 2026-11-17 19:31 UTC  
**Main HEAD at preflight:** `a9b05a794a974b4043b562a5ec625e4e16e78c8f` (Phase 461)  
**Disposition:** the actual committed first-seen ledger is still on the 41-column pre-Phase-454 header, while the current writer expects 43 columns. Phase 454's PR CI passed, but its live-capture job was skipped; no post-migration scheduled run has yet demonstrated the real-file migration. A regression now replays the migration against a temporary copy of the committed ledger and preserves every historical value by column name.

## 1. GitHub preflight — before edits

- Latest 100 Actions runs: 66 success, 33 failure, 1 cancelled; 7,706 total runs.
- Explicit `status=in_progress` query: 0. Explicit `status=queued` query: 0.
- Branches: 294, enumerated as 100 + 100 + 94.
- Open PRs: 56. Workflow files in main: 75.
- Latest Phase 461 PR run [44138210614](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44138210614) passed its single offline-regression job; no artifact. Phase 461 push run [44138177779](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44138177779) passed 21/21; Phase 460 compatibility run [44138210184](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44138210184) passed 16/16. No artifacts.
- Phase 454 PR run [44086525354](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44086525354): offline regression passed; `live-capture` was **skipped** because the event was `pull_request`.
- No workflow was dispatched, rerun or duplicated.

## 2. Reproducible inspection of the committed ledger

Fetched `research/data/sec_form144_first_seen/events.csv` directly from main (Git blob SHA `f61b43ea8989dd7af709c23650295749b82f87fc`, 42,388 bytes). Parsed it with a CSV parser that respects quoted embedded newlines in remarks.

Observed:
- 52 complete data records.
- Committed header: 41 fields.
- Current `EVENT_FIELDS` in `phase403_sec_form144_first_seen_capture.py`: 43 fields.
- The only missing header fields are `cross_feed_provenance_complete` and `capture_poll_status`.
- All 52 rows are `capture_mode=bootstrap`.
- All rows share the bootstrap first-seen timestamp `2026-11-14T20:45:08Z`.
- 0 rows are marked `research_observation_eligible=true`, `signal_eligible=true`, or `public_availability_certified=true`.

Thus the committed file is a historical/bootstrap baseline only. It contains no prospective eligible observation, and the Phase 454 migration has not yet been applied to the persisted main-branch file.

## 3. Exact failure and current workflow contract

The last scheduled SEC Form 144 run remains [44083941814](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44083941814). Its offline job passed; live capture failed in `fetch_acceptance_from_index` when `int(path_cik)` received the shifted timestamp `2026-11-16T16:55:39-05:00`. The append/commit step was skipped and no artifact was produced.

The current main workflow `.github/workflows/phase403_sec_form144_first_seen_capture.yml` contains:
- hourly cron `47 * * * *`;
- a migration step before live SEC capture;
- a non-cancelling concurrency group;
- scheduled/push commits of the append-only ledger;
- PR runs that execute offline tests but skip live capture.

No schedule-event run appears after the 12:31 UTC scheduled failure; the subsequent 12:47–18:47 UTC hourly slots are absent from the Actions inventory. The read interface does not expose the workflow's enabled/disabled administrative state. Do not change the cron or create another polling workflow; a human must verify that this individual workflow is enabled if the next scheduled slot is also absent.

## 4. Phase 462 regression added

Extended `test_phase454_form144_event_ledger_schema_migration.py` with a replay test against the actual committed ledger, copied to a temporary directory.

The test:
1. accepts only the exact known 41-field legacy header or the current 43-field header;
2. runs the migration on a copy, never on the checked-in source file;
3. verifies every existing field is preserved row-by-row, including multiline remarks;
4. verifies the two new fields are blank for legacy rows;
5. checks bootstrap rows remain non-eligible;
6. remains idempotent after a future successful scheduled migration.

This closes a gap in the earlier synthetic tests: the exact committed main-ledger schema is now a regression fixture. The PR CI is still offline; it cannot prove the SEC feed or scheduled persistence works.

## 5. Other source clocks

### CFTC TFF

- Current workflow on main: `phase384_cftc_tff_prospective_capture.yml`, weekday cron `25 22 * * 1-5` UTC.
- Last observed CFTC run: [43525140200](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43525140200), a 13-Nov branch-push bootstrap, not a scheduled observation.
- Phase 443 recorded that the 16-Nov scheduled slot was absent. At this audit time (19:31 UTC), today's 22:25 UTC slot is still in the future. Do not manually dispatch: manual mode is state-neutral and cannot establish prospective eligibility.
- The 3,035 bootstrap rows remain warm-up only and `signal_eligible=false`.

### FINRA

- [Run 44007662531](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44007662531) stopped at the credential guard.
- `FINRA_ACCESS_TOKEN`, `FINRA_CLIENT_ID` and `FINRA_CLIENT_SECRET` were empty in that run; no FINRA request was made.
- One-settlement validation remains blocked until credentials are configured as Actions secrets. No bulk history run should precede that validation.

## 6. Research disposition and controls

- Form 4 multi-owner transaction lines remain quarantined under Phase 461; no owner-count clustering or inferred line attribution is admitted.
- CFTC TFF remains a prospective crowding/downside-risk hypothesis only; its weekly preregistration is unchanged.
- FINRA ATS is venue-concentration / market-structure data, not investor identity.
- Options candidates remain conditional on actual authorized samples, PIT/vintage evidence, F80 coverage and business-use licensing.
- No forward-return, alpha, OOS, bootstrap, LOO or holdout test was run in Phase 462.
- No raw SEC/FINRA/CFTC or vendor data were committed.
- `F80_TOP20_PARTIAL50_BASELINE_C20`, universe, parameters, capital, exposure, holdout and production remain frozen.

## 7. Next gates

1. Merge this regression only after CI passes.
2. Observe the next scheduled Phase 403 run. Require `schema_migration.json` to report `header_migrated`, an artifact, and a committed 43-field ledger before treating migration as operationally complete.
3. If the scheduled SEC event is absent again, verify the individual workflow's enabled state in GitHub Actions; do not create a second poller.
4. Inspect today's 22:25 UTC CFTC scheduled run when it becomes available; admit only actual scheduled first-receipt events.
5. Configure FINRA OAuth secrets and run exactly one settlement-date validation before any historical batch.

No source, feature or trading signal was admitted by this phase.

## 8. CI result

- PR run [44160283721](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44160283721) completed successfully.
- Offline-regression job [134311911943](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44160283721/job/134311911943) ran 25 tests; all passed, including the new committed-ledger replay test.
- The `live-capture` job was correctly skipped on the pull-request event. No artifacts were produced. This validates the migration against a temporary copy of the committed file, not live SEC availability or persisted main-branch migration.
