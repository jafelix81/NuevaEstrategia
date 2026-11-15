# Phase 409 — SEC scheduled-trigger delivery audit and CFTC release-clock recheck

**Audit time:** 2026-11-15 01:48 UTC  
**Main HEAD:** `3d450a4d1d27f13663303cbf65f987150571a282` (Phase 408)  
**Disposition:** SEC Form 144 scheduled polls remain unobserved after the cron re-time; do not manually duplicate. CFTC's next official release remains scheduled for 2026-11-16. No signal or strategy change.

## 1. SEC workflow and Actions audit

Inspected the mainline workflow `.github/workflows/phase403_sec_form144_first_seen_capture.yml` and repository Actions runs.

- Default branch is `main`; the Phase 403 workflow is present on main.
- The workflow declares `schedule: 37 * * * *`, `workflow_dispatch`, and a serialized concurrency group `sec-form144-prospective-first-seen`.
- The latest run visible in the repository-wide recent-run page is [43650633912](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43650633912), created 2026-11-14 22:55:57Z. It is a `pull_request` validation, not a scheduled capture. Its `offline-regression` job passed; `live-capture` was skipped; it uploaded no artifacts.
- A created-after query beginning 2026-11-14 22:55:00Z returned exactly that PR run and no later run. The same query filtered to `event=schedule` returned zero runs.
- Therefore no schedule run is evidenced for the :37 slots at 23:37Z, 00:37Z or 01:37Z as of this audit. GitHub may delay or drop scheduled events; this does not prove the workflow is disabled.
- No run was queued or in progress in the recent-run results inspected. No manual dispatch, rerun, branch push or duplicate capture was started.

### Persistent SEC state

- `research/data/sec_form144_first_seen/state.json` remains at `poll_count=2`, last successful mode `bootstrap`, last successful poll `2026-11-14T20:48:22Z`, run `43639405055`.
- `events.csv` still contains 52 bootstrap events; all remain research-ineligible, signal-ineligible and uncertified for public availability.
- `feed_observations.csv` still contains only its header.
- Acceptance reconciliation remains 52/52, but acceptance time is not first-public-receipt time.

A successful scheduled poll should append per-feed observations and advance state even when no new accession appears. Neither change is present. Do not infer a first-seen interval or use bootstrap rows.

### Operational limitation

The available GitHub connection can inspect workflow source and run/job/artifact records, but it does not expose the workflow enable/disable administration endpoint. The repository owner should verify in **Actions → Phase 403 workflow** that the workflow is enabled. Do not change the cron again until that state is checked; Phase 405 already changed it from :17 to :37 and another cron edit would not diagnose a disabled workflow.

## 2. SEC 13D/G retrieval remains blocked

PR [#37 — Phase 350](https://github.com/jafelix81/NuevaEstrategia/pull/37) remains draft.

- Run [43327053770](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43327053770) passed 10/10 offline tests but SEC Archives returned HTTP 403 on request 1/44.
- Zero parent documents were saved and zero references were validated.
- The effective User-Agent shown in the log contains only the project URL and no monitored contact email. No request was retried.

The required repository Actions secret `SEC_USER_AGENT` must contain a project identifier and monitored contact email before the 44 exact-parent requests are resumed. Do not paste the email into chat. This is separate from the scheduled Form 144 trigger issue.

## 3. CFTC TFF release and capture clock

The official [CFTC 2026 Release Schedule](https://www.cftc.gov/MarketReports/CommitmentsofTraders/ReleaseSchedule/index.htm) lists the next report for **Monday 2026-11-16 at 3:30 p.m. ET (20:30 UTC)**, delayed for a federal holiday. It covers positions as of Tuesday 2026-11-10.

Phase 384's mainline weekday capture is scheduled for **22:15 UTC**, 105 minutes after the scheduled release. This is a conservative first-receipt poll, not a guarantee that the API will have updated. If the source is not updated, no row is invented; the actual first scheduled receipt governs.

The committed CFTC state remains the non-eligible branch-push baseline from 2026-11-13 23:03:38Z, ending at report date 2026-11-03 for all four contract codes. The next weekday cron slot after that Friday baseline is Monday 2026-11-16 at 22:15 UTC; no weekday schedule slot was due over the intervening weekend.

The CFTC's announced twice-weekly transition has no effective date established by the official 2026 release schedule reviewed here; retain weekly feature semantics until prospective source observations demonstrate a cadence change.

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

## Recheck addendum — 2026-11-15 02:48 UTC

The follow-up audit confirmed the workflow files and inspected the jobs, logs, artifacts and persisted source state directly.

### SEC

- Mainline workflow file is confirmed at `.github/workflows/phase403_sec_form144_first_seen_capture.yml`; it still declares the :37 hourly schedule and serialized concurrency group.
- Run [43650633912](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43650633912) has two completed jobs: `offline-regression=success`, `live-capture=skipped`; no artifact.
- Bootstrap run [43639405055](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43639405055) has both jobs successful and artifact [14130779748](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43639405055/artifacts/14130779748). The artifact confirms `mode=bootstrap`, 52 reconciled acceptance timestamps, zero new accessions, zero research-observation-eligible events and `public_availability_certified=false`.
- Mainline `state.json` is still at poll 2 / bootstrap at 20:48:22Z; `feed_observations.csv` remains header-only. No later scheduled capture is evidenced by persisted state or capture commits. The connector still cannot conclusively enumerate queued/in-progress repository-wide runs or inspect workflow enablement. No duplicate poll was launched.

### CFTC

- Mainline workflow file is confirmed at `.github/workflows/phase384_cftc_tff_prospective_capture.yml`; it declares weekday `15 22 * * 1-5` (22:15 UTC), `workflow_dispatch`, and a serialized concurrency group.
- Run [43525140200](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43525140200) is a **push/bootstrap** run on the mainline-activation branch, not a scheduled observation. Its job succeeded, all 11 tests passed, and artifact [14084802705](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43525140200/artifacts/14084802705) confirms 3,035 historical rows, no new events, no state overwrite, zero historical signal-eligible rows and `alpha_test_authorized=false`.
- Mainline CFTC state remains the 2026-11-13 23:03:38Z branch-push baseline, latest report date 2026-11-03 for all four codes. Because the workflow is weekday-only and the next official release is Monday, 2026-11-16, the first relevant scheduled poll is still in the future at 22:15 UTC that day. No early/manual poll was started.
- The official schedule currently lists Nov 16, Nov 20 and Nov 30 as release dates; the CFTC's Oct 27 announcement is a plan for semiweekly publication by year-end, not proof that the TFF dataset has already changed cadence. The code's atomic-batch guard and weekly-feature suppression remain appropriate until actual prospective report dates establish a new cadence.

The Phase 409 branch remains an audit-only draft; this addendum changes no workflow, data, model, feature, signal or strategy setting.


## Recheck addendum — first successful SEC scheduled poll (2026-11-15 03:47 UTC)

The earlier Phase 409 conclusion that no scheduled poll had been observed is superseded by the first completed schedule-triggered run:

- Run [43670461605](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43670461605) explicitly reports `EVENT_NAME=schedule`. The live-capture job started at 03:01:58Z and completed successfully; the offline regression and live-capture jobs both concluded SUCCESS. The offline suite passed **15/15**.
- Artifact [14143174642](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43670461605/artifacts/14143174642) was uploaded successfully (1,188 bytes; SHA-256 `a518f07b6bb6b67582d3c578ff0e8656171179df5c67ef169cfe588c1dd04c3a`).
- The live-poll summary is `POLL_COMPLETE_NO_NEW_ACCESSIONS`: 50 Form 144 entries and 5 Form 144/A entries observed; **55 per-feed observations appended**; zero new feed entries, zero new accessions, zero new events, zero candidate-issuer matches and zero new XML resolutions.
- Both feeds retained the previous latest accession; `possible_feed_window_gap=false`. The observation interval is bounded by the previous successful poll (2026-11-14 20:48:21/22Z) and this receipt (2026-11-15 03:02:02Z). This establishes a successful scheduled observation, not a new filing event.
- Mainline state now records `poll_count=3`, mode `schedule`, run `43670461605`, and last successful receipt `2026-11-15T03:02:02Z`. The 52 initial event rows remain baseline-only; `events_written=0`; no row is public-availability-certified or signal-eligible.
- The workflow is demonstrably enabled and capable of completing a scheduled run. The previous request for the repository owner to verify workflow enablement is no longer necessary. The nominal cron remains `37 * * * *`; this run began at 03:01:58Z, illustrating that Actions scheduling is not an exact wall-clock service. Do not manually dispatch or duplicate a poll. At audit time, no later capture commit was visible; the connector cannot conclusively enumerate a queued/in-progress later schedule run.

### CFTC recheck

- Phase 384 remains on its weekday `15 22 * * 1-5` schedule. Latest inspected run [43525140200](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43525140200) is still the push/bootstrap run; its successful job and artifact [14084802705](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43525140200/artifacts/14084802705) report 3,035 historical rows, no new events and no alpha authorization.
- The official CFTC schedule lists the next COT release for **Monday 2026-11-16 at 3:30 p.m. ET (20:30 UTC)**. The existing 22:15 UTC poll is 105 minutes later. See [CFTC release schedule](https://www.cftc.gov/MarketReports/CommitmentsofTraders/ReleaseSchedule/index.htm). Do not infer that the announced semiweekly cadence is already effective for TFF; retain weekly feature semantics until actual prospective releases demonstrate otherwise.

### Strategy disposition

No Form 144 event was newly observed and no return/alpha/OOS/bootstrap/LOO/holdout test was run. The SEC feed clock is now operationally proven for one scheduled poll, but one poll with no new accession does not yet establish a usable event sample or economic signal. Historical F80 membership remains unverified. `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen; holdout, universe, parameters, capital, exposure and production are unchanged.


## CFTC semiweekly transition watch — official announcement vs effective TFF cadence (2026-11-15)

- CFTC Press Release 9316-26 (2026-10-27) announced a plan to move COT publication from once to twice weekly by the end of 2026: positions from Monday to be published Wednesday, and positions from Wednesday to be published Friday, both at 3:30 p.m. ET, reducing stated latency from three days to two. The release does not specify in its text whether every report family, including TFF Futures Only, will enter the same rollout.
- As of this audit, the official 2026 COT release calendar still lists the holiday-delayed Monday 2026-11-16 release (positions 2026-11-10), then 2026-11-20 and 2026-11-30; it does not yet list Wednesday releases. The public TFF Futures Only dataset still reports last update 2026-11-06. Therefore the semiweekly cadence is an announced plan, not an observed TFF regime change.
- Phase 384 already polls weekdays at 22:15 UTC, so it is operationally compatible with Wednesday/Friday publication without a cron change. Its current cadence detector classifies weekly gaps of 6–8 days and semiweekly gaps of 2–5 days; the weekly 4-report / 52-report features are suppressed outside the weekly regime. The atomic batch rule makes only the newest new report per contract in a capture eligible; earlier same-batch catch-up rows remain ineligible.
- Do not change Phase 387's weekly preregistration, combine weekly and semiweekly histories, or infer an effective date from the press release. Watch the official release calendar and actual TFF report-date sequence. If TFF enters the new regime, freeze the weekly hypothesis and preregister a separate cadence-specific design before using any semiweekly observations.
- No data were downloaded, no CFTC workflow was duplicated, no returns/alpha/OOS/bootstrap/LOO/holdout tests were run, and no signal or strategy setting changed.

Official references: CFTC Press Release 9316-26 (2026-10-27), https://www.cftc.gov/PressRoom/PressReleases/9316-26 ; COT release schedule, https://www.cftc.gov/MarketReports/CommitmentsofTraders/ReleaseSchedule/index.htm ; TFF Futures Only dataset, https://publicreportinghub.cftc.gov/Commitments-of-Traders/TFF-Futures-Only/gpe5-46if .