# Phase 479 — SEC Form 144 growing-ledger regression repair

**Audit cutoff:** 2026-11-18 12:29 UTC  
**Base main:** `793af54daa99e5f132199e1151b3823c0ccf5645`  
**Triggering failure:** [scheduled run 44302697069](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44302697069)  
**Disposition:** repair stale snapshot assertions in the Phase 464 read-only audit so the existing Phase 403 scheduled collector can pass its offline gate. No live capture was attempted by the failed run.

## 1. Preflight and no-duplicate check

- Default branch is `main`; repository main HEAD at preflight was `793af54daa99e5f132199e1151b3823c0ccf5645`.
- Latest Actions inventory: 7,843 total workflow runs. Explicit `in_progress` and `queued` queries returned 0/0.
- Latest observed run [44302697069](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44302697069) was a `schedule` event for Phase 403, created 2026-11-18 12:18:41 UTC, completed with failure.
- Jobs: `offline-regression` failed; `live-capture` was skipped because it depends on the offline job. Artifact list was empty. No SEC live request, ledger mutation or artifact was produced by this run.
- The workflow remains on main with configured cron `47 * * * *`. The recorded schedule-run creation time does not match the configured minute; treat this as a schedule-delivery/timestamp discrepancy, not proof of disablement.
- Phase 476 has no scheduled event in the latest 30-run inventory through this cutoff; its minute-17 schedule remains unverified. No manual dispatch or duplicate run was started.

## 2. Root cause

Phase 403's offline regression includes the historical Phase 464 production-capture auditor. That auditor correctly selects the original production run by accession-level `first_seen_poll_run_id=44179257367`, but its test also pinned repository-wide append-only ledger totals and the mutable latest-poll state to the exact 2026-11-17 snapshot.

Since Phase 464, a later successful scheduled capture [44228413864](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44228413864) appended another 90 filing versions and 109 feed-observation rows, with 90 additional acceptance reconciliations. The committed global event and reconciliation ledgers grew from 106 to 196 rows; the complete-poll count grew from 9 to 10. The latest successful poll state now correctly points to run 44228413864 and reports no gap for either feed.

The Phase 464 test still expected:
- exactly 106 global event rows;
- exactly 388 global feed-observation rows;
- exactly 106 global acceptance-reconciliation rows;
- exactly 9 complete polls;
- the prior run ID 44179257367 and its old per-feed gap map.

Two assertions failed first:
1. `event_rows_total`: actual 196 vs stale expected 106;
2. `state_complete_poll_count`: actual 10 vs stale expected 9.

These are test-fixture/snapshot-maintenance defects, not evidence of ledger corruption. The original Phase 464 run-scoped metrics remain stable: 54 new filing versions, 58 feed observations, 54 acceptance reconciliations, four bounded 144/A amendment versions, and zero signal-eligible rows.

## 3. Repair

- Changed global ledger checks from exact row totals to monotonic lower bounds anchored to the Phase 464 snapshot. Run-specific Phase 464 counts remain exact.
- Updated the auditor to expose the current last-successful poll run ID/time separately from the latest poll-attempt run ID.
- Replaced the test that froze the old 9-poll/old-run/old-gap snapshot with structural checks that the mutable state retains a successful anchor, a valid poll status, and boolean gap fields for both feeds.
- The audit remains read-only. It does not rewrite or normalize the live ledger, and it does not relax any PIT, gap, eligibility or signal gate.

## 4. Validation and next gate

The PR's Phase 403 offline job must pass all four existing suites:
- Phase 403 capture;
- Phase 454 ledger migration;
- Phase 464 first-production audit;
- Phase 465 Atom pagination.

The live-capture job is intentionally skipped on pull requests. After merge, wait for the next existing scheduled Phase 403 event; do not manually dispatch a duplicate. A successful live poll must still preserve both feed-specific watermarks and the fail-closed pagination checks before any new observation can be considered bounded.

Issue [#136](https://github.com/jafelix81/NuevaEstrategia/issues/136) is updated: a scheduled Phase 403 event has now been observed, so the earlier missing-run symptom is no longer the immediate blocker; the actual blocker is this stale offline regression. Keep the issue open until a scheduled capture completes successfully.

## 5. Research controls

- No live SEC data request, filing XML/text, transaction rows, prices or new artifact was created in this phase.
- No Form 144 event is promoted to public-availability-certified or signal-eligible.
- No backtest, event study, alpha, OOS, bootstrap, LOO or holdout test.
- No change to the 335-name universe, `F80_TOP20_PARTIAL50_BASELINE_C20`, parameters, capital, exposure, costs, production or holdout.
- FINRA, CFTC, Form 4, Cboe and other Smart Money source hypotheses remain independent. No source interpretation or signal is promoted by this operational repair.
