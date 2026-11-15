# Phase 409 — SEC scheduled-trigger delivery audit and CFTC release-clock recheck

**Audit time:** 2026-11-15 01:48 UTC  
**Main HEAD:** `3d450a4d1d27f13663303cbf65f987150571a282` (Phase 408)  
**Disposition:** SEC Form 144 scheduled polls remain unobserved after the cron re-time; do not manually duplicate. CFTC's next official release remains scheduled for 2026-11-16. No signal or strategy change.

## 1. SEC workflow and Actions audit

Inspected the mainline workflow `.github/workflows/phase403_sec_form144_first_seen_capture.yml` and repository Actions runs.

- Default branch is `main`; the Phase 403 workflow file is present on main.
- The workflow declares `schedule: 37 * * * *`, `workflow_dispatch`, and a serialized concurrency group `sec-form144-prospective-first-seen`.
- The latest run visible in the repository-wide recent-run page is [43650633912](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43650633912), created 2026-11-14 22:55:57Z. It is a `pull_request` validation, not a scheduled capture. Its `offline-regression` job passed; `live-capture` was skipped; it uploaded no artifacts.
- A created-after query beginning 2026-11-14 22:55:00Z returned exactly that PR run and no later run. The same query filtered to `event=schedule` returned zero runs.
- Therefore no schedule run is evidenced for the :37 slots at 23:37Z, 00:37Z or 01:37Z as of this audit. GitHub may delay or drop scheduled events; this does not prove the workflow is disabled.
- No run was queued or in progress in the recent-run results inspected. No manual dispatch, branch push, rerun or duplicate capture was started.

### Persistent SEC state

- `research/data/sec_form144_first_seen/state.json` remains at `poll_count=2`, last successful mode `bootstrap`, last successful poll `2026-11-14T20:48:22Z`, run `43639405055`.
- `events.csv` still contains 52 bootstrap events; all remain research-ineligible, signal-ineligible and uncertified for public availability.
- `feed_observations.csv` still contains only its header.
- Acceptance reconciliation remains 52/52, but acceptance time is not first-public-receipt time.

A successful scheduled poll should append per-feed observations and advance state even when no new accession appears. Neither change is present. Do not infer a first-seen interval or use bootstrap rows.

### Operational limitation

The available GitHub connection can inspect workflow source and run/job/artifact records, but it does not expose the workflow enable/disable administration endpoint. The repository owner should verify in **Actions → Phase 403 workflow** that the workflow is enabled. Do not change the cron again until that state is checked; Phase 405 already changed it from :17 to :37 and another cron edit would not diagnose a disabled workflow.

## 2. SEC 13D/G retrieval remains blocked

PR [#37](https://github.com/jafelix81/NuevaEstrategia/pull/37) remains draft. Phase 408's evidence is unchanged: run [43327053770](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43327053770) stopped on HTTP 403 at request 1/44, saved zero parent documents, and showed a project-URL-only User-Agent without a monitored contact email.

The required repository Actions secret `SEC_USER_AGENT` must contain a project identifier and monitored contact email. No request was retried. This is separate from the scheduled Form 144 trigger issue.

## 3. CFTC TFF release and capture clock

The official [CFTC 2026 Release Schedule](https://www.cftc.gov/MarketReports/CommitmentsofTraders/ReleaseSchedule/index.htm) lists the next report for **Monday 2026-11-16 at 3:30 p.m. ET**, delayed for the federal holiday. In November standard time this is 20:30 UTC. The report is expected to cover positions as of Tuesday 2026-11-10.

Phase 384's mainline weekday capture remains scheduled for 22:15 UTC (5:15 p.m. ET), 105 minutes after the scheduled release. This is a conservative first-receipt poll, not a guarantee that the API will have updated. If the source is not updated, no row is invented; the actual first scheduled receipt governs.

The committed CFTC state remains the non-eligible branch-push baseline from 2026-11-13 23:03:38Z, ending at report date 2026-11-03 for all four contract codes. No prospective event ledger exists yet. The CFTC's announced twice-weekly transition has no effective date established by the official 2026 schedule reviewed here; retain weekly feature semantics until prospective source observations demonstrate a cadence change.

## 4. Strategy and research controls

- `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen.
- No Smart Money feature or signal admitted.
- No forward-return, alpha, OOS, bootstrap, LOO or holdout test performed.
- Holdout untouched; universe, parameters, capital, exposure and production unchanged.
- No vendor purchase, trial, account or contact.

## Next gates

1. Repository owner verifies that the Phase 403 workflow is enabled in Actions; then observe a genuine `schedule` run. Do not use bootstrap/push as a substitute for prospective capture.
2. Keep SEC 13D/G parent retrieval stopped until `SEC_USER_AGENT` is updated with monitored contact details.
3. Inspect the first Phase 384 scheduled run after the 2026-11-16 CFTC release; reconcile report date, actual first-receipt UTC, event classification and earliest eligible NYSE session.
4. Continue FINRA only after the effective-dated security-master and delisting-return gates pass; continue options only after actual sample rows, trade-condition mapping and delivery-vintage semantics are inspected.
