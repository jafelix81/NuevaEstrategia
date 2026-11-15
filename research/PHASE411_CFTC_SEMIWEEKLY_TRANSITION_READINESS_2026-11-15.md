# Phase 411 — CFTC semiweekly COT announcement and TFF transition readiness

**Date:** 2026-11-15 UTC  
**Status:** announcement verified; TFF effective-date and report-family scope not yet confirmed; no signal or feature admission.  
**Parent:** Phase 384 prospective TFF capture; Phase 387 weekly crowding-risk preregistration; Phase 410 BPR feasibility.

## Executive decision

CFTC has officially announced a plan to increase COT publication frequency from once to twice weekly by the end of 2026. The current official 2026 release calendar and TFF Futures Only dataset still show the existing weekly regime. The announcement does not explicitly state in its text whether TFF Futures Only is included in the same rollout. Treat this as a **planned source-regime change**, not an observed TFF cadence change.

No capture schedule change is needed: Phase 384 already polls Monday through Friday at 22:15 UTC. The existing parser detects weekly versus semiweekly report-date gaps and suppresses weekly features when cadence is not weekly. This phase adds a regression for the announced Monday/Wednesday report-date pattern (2-day then 5-day gaps). It does not create a second capture workflow.

## 1. Official announcement and current calendar

CFTC Press Release 9316-26, dated 2026-10-27, states a plan to publish:

- data from Monday on Wednesday;
- data from Wednesday on Friday;
- both releases at 3:30 p.m. Eastern Time;
- stated report latency reduced from three days to two days.

The release describes a plan to roll out by year-end. It does not provide a TFF-specific implementation date or an explicit list of report families covered.

As of 2026-11-15, the official 2026 COT release schedule still lists the next report on **Monday 2026-11-16 at 3:30 p.m. ET (20:30 UTC)** for positions as of 2026-11-10, followed by 2026-11-20 and 2026-11-30; no Wednesday publication dates are listed. The public TFF Futures Only dataset reports its last update as **2026-11-06**. These are consistent with the old weekly cadence still being operational as of this audit.

## 2. Phase 384 compatibility review

The existing Phase 384 workflow polls weekdays at 22:15 UTC. That time is after a 3:30 p.m. ET release in both U.S. daylight and standard time. It therefore covers potential Wednesday and Friday releases without a cron change. Actual source first receipt, not the nominal cron, remains the knowledge clock.

Code review of research/phase384_cftc_tff_prospective_capture.py confirms:

- weekly cadence is recognized from four recent report-date gaps of 6–8 calendar days;
- semiweekly cadence is recognized from four recent gaps of 2–5 calendar days;
- weekly 4-report change is calculated only when all four adjacent intervals are 6–8 days;
- rolling weekly z-score history is suppressed when its prior report intervals are not weekly;
- prospective event payloads contain raw source rows only; historical archive-derived features are not attached;
- classify_batch permits only the newest new report per contract in a single capture to be research-observation-eligible; older same-batch catch-up rows are recorded but remain ineligible.

This is conservative under missed or delayed polls. It does not backdate an earlier report or pretend a missed Wednesday capture occurred.

## 3. Regression added

The new offline test uses report dates Monday 2026-01-05, Wednesday 2026-01-07, Monday 2026-01-12, Wednesday 2026-01-14 and Monday 2026-01-19. The resulting 2,5,2,5-day pattern must be classified as SEMIWEEKLY; the weekly feature gate must be false and the weekly 4-report change must remain null.

The regression workflow runs only the existing Phase 384 offline unit suite. It makes no CFTC request and does not execute the capture client.

## 4. Research and implementation rules

1. Do not change Phase 387's weekly preregistered hypothesis until actual TFF report-date sequences and first-receipt records show a semiweekly regime.
2. Do not stitch weekly and semiweekly observations or annualize them as if they were homogeneous.
3. If TFF moves to semiweekly, suspend the weekly hypothesis and preregister a separate cadence-specific feature, warm-up, sample-size and inference design before using semiweekly observations.
4. Keep each report's first-receipt UTC, raw hash, report date, contract code and earliest eligible NYSE session. Late arrivals and revisions remain ineligible and are never backdated.
5. The current 2026-11-16 release is still treated as the holiday-delayed weekly report until observed otherwise.

## 5. Sources

- CFTC Press Release 9316-26 (2026-10-27): https://www.cftc.gov/PressRoom/PressReleases/9316-26
- Official COT release schedule: https://www.cftc.gov/MarketReports/CommitmentsofTraders/ReleaseSchedule/index.htm
- TFF Futures Only dataset: https://publicreportinghub.cftc.gov/Commitments-of-Traders/TFF-Futures-Only/gpe5-46if
- Phase 384 capture workflow: .github/workflows/phase384_cftc_tff_prospective_capture.yml

## 6. Controls

- No CFTC source data were downloaded in this phase.
- No new capture workflow or duplicate polling process was created.
- No return, alpha, OOS, bootstrap, LOO or holdout test was run.
- No signal admitted; no Phase 387 threshold or feature changed.
- F80_TOP20_PARTIAL50_BASELINE_C20, universe, parameters, capital, exposure, holdout and production remain unchanged.


CI note: .github/workflows/phase411_cftc_semiweekly_transition_regression.yml runs only the offline Phase 384 unit suite on pull requests; it does not call CFTC or execute capture.
