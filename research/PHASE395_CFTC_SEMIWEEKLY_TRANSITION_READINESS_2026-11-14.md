# Phase 395 — CFTC semiweekly transition readiness and atomic capture-batch guard

**Audit date:** 2026-11-14 UTC  
**Disposition:** capture pipeline hardened for the announced cadence transition; the existing weekly Phase 387 hypothesis remains frozen. No new observations, returns test, alpha test or signal admission.

## 1. Official schedule change

On 2026-10-27, the CFTC announced that it plans to increase COT publication from once to twice weekly by the end of 2026. The official announcement says Monday position data will be published Wednesday and Wednesday position data Friday, both at 3:30 p.m. ET, reducing publication latency from three days to two.

Official announcement: https://www.cftc.gov/PressRoom/PressReleases/9316-26

As of this audit, the CFTC's public release-schedule page still lists the existing weekly calendar. Its next listed release is Monday 2026-11-16 at 3:30 p.m. ET, for positions as of 2026-11-10, delayed for a federal holiday. The exact first semiweekly release date is therefore not inferred from the press release.

Official schedule: https://www.cftc.gov/MarketReports/CommitmentsofTraders/ReleaseSchedule/index.htm

The announcement is for the COT program generally. It does not, by itself, prove the precise transition date, schema behavior or cadence of the specific Socrata TFF Futures Only dataset gpe5-46if used here. Those must be confirmed from actual prospective TFF rows.

## 2. Existing capture schedule is adequate for polling

Phase 384's scheduled workflow polls Monday–Friday at 22:15 UTC. This is after the announced 3:30 p.m. ET publication time in both standard and daylight time. Weekday polling is preferable to a Friday-only cron because it can observe delayed Monday releases and either day of a future semiweekly schedule.

The recorded timestamp remains the pipeline's first observation time, not a claim that the report first became public at that exact second. A delayed poll is conservatively later; no report is backdated.

The mainline bootstrap baseline is present:
- Created 2026-11-13 23:03:38 UTC.
- 3,035 historical rows across ES, NQ, Dow and post-2017 Russell E-mini.
- Latest historical report date in all four contract series: 2026-11-03.
- Historical rows remain ineligible and are not substituted for prospective feature history.

## 3. Atomic-batch lookahead risk found and corrected

A scheduled API poll can return more than one previously unseen report date for the same contract—for example, if a prior poll was missed, the endpoint was delayed, or a transition/backlog releases multiple snapshots before the next successful run.

Before this phase, the capture loop classified every unseen report date later than the stored latest date as a separate eligible new_report. All such rows in one API response share the same first_seen_utc. A downstream process could mistakenly order them by report date and treat an earlier row in the same response as a previously known observation for a later row, even though both became known to the pipeline simultaneously.

The scheduled capture now treats each API response as an **atomic batch per contract**:
- The newest newly observed report date for a contract in that capture may be marked new_report and research_observation_eligible=true.
- Any older newly observed report dates for that same contract in the same response are retained as same_batch_catchup, with research_observation_eligible=false.
- Revisions and older late arrivals remain ineligible.
- All observed hashes are still recorded append-only, and the per-contract latest report date advances to the newest observed date.
- Different contracts remain independent; one latest report per contract may be eligible in the same capture.
- The event file records the capture run ID and atomic-batch policy. Raw event payloads remain raw-only; no archive-derived cadence labels or features are attached.

This is deliberately conservative. A same-batch catch-up row is not counted as a separate prospective evaluation observation or as a prior first-seen observation for the same batch. It remains available for audit but cannot manufacture extra chronological sample size.

## 4. Phase 387 remains weekly and unchanged

Phase 387's preregistered design requires prior 52 valid, prospectively first-seen weekly observations, 20-session downside-risk outcomes, and its original training/evaluation and dependence controls. It is not converted to semiweekly by dividing or reinterpreting report counts.

If the TFF endpoint actually transitions to Monday/Wednesday report dates:
1. Preserve Phase 387 as a weekly-only preregistration; do not stitch weekly and semiweekly observations or relax its gates.
2. Confirm the TFF dataset's actual report-date pattern and first-receipt behavior from prospective captures.
3. Build any semiweekly feature history from eligible first-seen events only. The raw capture event file intentionally contains no derived cadence labels; the downstream feature builder must detect cadence without using the static historical backfill.
4. Preregister a separate semiweekly specification before inspecting forward outcomes. Preserve economic time units (for example, a one-year reference window should remain one year rather than silently shrinking from 52 weeks to 52 reports), account for more overlapping 20-session outcomes, and set dependence-robust inference in calendar/trading-time units.
5. Do not use same-batch catch-up rows to create extra independent observations.

No new threshold, horizon, sample-size gate or model has been selected in this phase.

## 5. Validation and controls

Three offline regression tests were added:
- Only the newest new report per contract in an atomic batch is eligible.
- Separate contracts are classified independently.
- Revisions and older late arrivals remain ineligible.

The dedicated Phase 395 workflow runs only compile/unit tests; it does not call CFTC or any vendor.

No live CFTC capture was triggered by this phase. No forward returns, alpha, OOS, bootstrap, LOO or holdout test was run. No vendor contact or purchase occurred. F80_TOP20_PARTIAL50_BASELINE_C20, universe, capital, exposure, parameters and production remain unchanged.

## 6. Next gate

Verify the scheduled CFTC capture after the official 2026-11-16 release. Confirm whether the TFF Futures Only dataset contains the expected report date and whether the source has transitioned. If more than one new report date appears for a contract in a single poll, the atomic-batch guard prevents same-timestamp pseudo-sequencing. Only after actual TFF cadence is established should a separate semiweekly hypothesis be preregistered.
