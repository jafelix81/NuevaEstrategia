# Smart Money Research state addendum — Phase 598 (2026-11-24 15:34 UTC)

Main HEAD at preflight: `14344939f64a7dd789ccab29bcc46bee9765545b`. This is an operational delivery recheck; no alpha or strategy phase was run.

## Actions and repository preflight

- Total Actions runs: **8,109**.
- Latest 100: **90 success / 10 failure**; all 100 completed.
- Explicit `status=in_progress` and `status=queued` queries: **0 / 0**.
- Schedule-triggered run inventory: **59**.
- Branches: **380** (four pages enumerated); open PRs: **72**; workflow files: **96**; research directory entries: **492**.
- No workflow was dispatched, rerun, cancelled, merged, rebased or duplicated.

## SEC scheduled-capture gap — renewed at 15:34 UTC

Latest natural SEC runs and persisted poll ends:
- Form 4 / Phase 476: [45332760566](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45332760566), schedule event created 05:21:36 UTC; poll ended 05:22:13 UTC. Workflow at its run SHA still declares `17 * * * 1-5`. Missing due slots: **06:17–15:17 UTC (10 weekday slots)**.
- Form 144 / Phase 403: [45330252226](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45330252226), schedule event created 05:00:27 UTC; poll ended 05:01:16 UTC. Workflow at its run SHA still declares `47 * * * *`. Missing due slots: **05:47–14:47 UTC (10 hourly slots)**.

Other schedule workflows did execute during the gap:
- CFTC TFF [45338400329](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45338400329), 06:09:53 UTC, success.
- FINRA Reg SHO [45339067236](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45339067236), 06:15:11 UTC, success at workflow level.

This makes a repository-wide scheduled-Actions outage less likely and points instead to workflow-specific disablement/paused state or repeated per-workflow event loss. Form 144 has a concurrency group but no active/queued run; Form 4 has no concurrency group. The read-only GitHub connection does not expose each workflow's enabled/disabled state, so the cause cannot be adjudicated from the API.

Next nominal slots after this cutoff: Form 144 15:47 UTC and Form 4 16:17 UTC. Human action: verify that both individual workflows are enabled in Actions and that no workflow-specific pause/disablement exists. Do not manually dispatch, rerun, change cron or create replacement pollers solely to test delivery. Issue [#194](https://github.com/jafelix81/NuevaEstrategia/issues/194) received the 15:34 UTC evidence.

## Latest source artifacts rechecked

Downloaded and inspected the latest FINRA, CFTC, Form 4, Form 144 and Form 144 10b5-1 artifacts, plus relevant job logs:
- FINRA artifact [14895571787](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45339067236/artifacts/14895571787): six HTTP-200 CNMS files rejected; BCPC/TPC repeated in all six; 12 extra rows; zero valid files/first-seen/eligible observations; raw rows and volume values not persisted. Same-day 2026-11-24 request recorded as one `not_available` response.
- CFTC artifact [14895036288](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45338400329/artifacts/14895036288): 3,043 rows, no new reports/revisions, zero signal-eligible historical rows; 17 offline tests passed.
- Form 4 artifact [14892950135](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45332760566/artifacts/14892950135): both watermarks passed; 516 new canonical accessions; 1,239 observations; 24 transaction-detail rows and 11 owner rows appended; 2,273 transaction backfills and 20 owner accessions remain; four multi-owner cases quarantined; zero public-availability-certified or signal-eligible rows.
- Form 144 artifact [14891955642](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45330252226/artifacts/14891955642): 118 new accessions/XML resolutions; 477 accessions / 3,360 details; 801 new detail rows; 113/118 acceptance reconciliations added and five unresolved; 238 backfills remain; 174 formal plan-date accessions across 89 dates; zero public-availability-certified or signal-eligible headers.
- Form 144 post-capture 10b5 artifact [14891416912](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45330252226/artifacts/14891416912): 16 sell-to-cover/tax-withholding accessions in the ledger; no signal admitted.

## Branch and PR disposition

- Phase 20C remains divergent from main: **12 ahead / 608 behind**; same-day-close implementation remains NO-GO for publication-time look-ahead.
- Cboe OPRA feasibility branch: **5 ahead / 110 behind**; retain as a conditional, license/PIT/coverage-gated candidate; do not merge stale branch.
- Massive Options branch: **5 ahead / 154 behind**; license gate remains unresolved.
- Form 4 overlap branch: **5 ahead / 110 behind**; descriptive audit only.
- Old SEC 13F branches are over 500 commits behind; old 13D parent-retrieval branch is highly divergent (269 ahead / 514 behind). Do not merge or replay as-is.
- Open PR count remains 72. No PR was merged.

## Research decision

- New signals admitted: **0**.
- Incremental alpha demonstrated: **none**.
- New valid OOS / bootstrap / LOO results: **0**.
- Phase 20C same-day-close: **NO-GO**; Phase 372 next-open retest remains untested.
- `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen. No model, universe, parameters, exposure, costs, holding-period, holdout or production changes.
