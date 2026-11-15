# Phase 419 — CFTC TFF preregistered event-count feasibility audit

**Audit time:** 2026-11-15 16:32 UTC  
**Main HEAD before this report:** `1eeb142ed118249dbf9a7a9db94fa1ad36f44eb0`  
**Disposition:** THE PHASE 387 EVENT-COUNT GATES ARE STRICT BUT MAY REQUIRE A MULTI-YEAR PROSPECTIVE SAMPLE; KEEP THEM FROZEN. NO DATA, RETURN TEST OR SIGNAL WAS ADDED.

## 1. Repository and Actions preflight

- Inspected the latest 100 Actions runs (7,658 total reported), all schedule-filtered runs, the latest SEC/CFTC/Phase 411 jobs, step summaries, logs and artifacts, the mainline research state, the Phase 387 preregistration, the Phase 409 schedule audit, Phase 411 cadence audit, Phase 418 options correction, open PRs and branch pages.
- Main HEAD was `1eeb142ed118249dbf9a7a9db94fa1ad36f44eb0`.
- Repository tree: 217 files; research directory: 87 entries; branches: 261 across three API pages; open PRs: 56. Most open PRs are draft/stacked research branches; none was merged or retargeted.
- Latest 100 runs: 62 success, 37 failure, 1 cancelled. Explicit status queries returned zero queued, in-progress, waiting or requested runs. No workflow was started or rerun.

### Latest relevant runs

| Run | Event / result | Evidence |
|---|---|---|
| [43709012759](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43709012759) | SEC Form 144 schedule / success | Both jobs succeeded; 15/15 offline tests; 55 feed observations; zero new accessions/events; no detected feed-window gap; artifact [14159294388](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43709012759/artifacts/14159294388). |
| [43681298839](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43681298839) | Phase 411 PR regression / success | 17/17 offline tests; no artifact or live CFTC request. |
| [43525140200](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43525140200) | CFTC Phase 384 push/bootstrap / success | 11/11 tests; 3,035 historical warm-up rows; zero signal-eligible historical rows; artifact [14084802705](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43525140200/artifacts/14084802705). It is not a scheduled prospective capture. |

The latest SEC scheduled receipt is 2026-11-15 11:28:22 UTC. The workflow remains configured at minute :37 hourly, but Actions scheduling is not a precise clock and can be delayed or dropped. The feed poll remains interval-censored; acceptance time is not first-public availability. Do not manually dispatch or duplicate polling.

## 2. CFTC calendar and prospective-capture status

The official CFTC calendar lists the next TFF/COT release for **Monday 2026-11-16 at 3:30 p.m. ET (20:30 UTC)**, delayed for a federal holiday. It covers positions as of Tuesday 2026-11-10. Phase 384 polls at **22:15 UTC**, 105 minutes later. The public TFF Futures Only dataset still showed a last update of 2026-11-06 at this audit.

The CFTC's 2026-10-27 announcement describes a plan to move COT publication to twice weekly by year-end. The current release calendar and TFF dataset have not yet demonstrated that the TFF Futures Only series has changed cadence. Keep Phase 387 weekly-only. If prospective TFF report dates establish a semiweekly regime, suspend the weekly hypothesis and require a separate preregistration; do not stitch frequencies.

Official sources:
- https://www.cftc.gov/MarketReports/CommitmentsofTraders/ReleaseSchedule/index.htm
- https://publicreportinghub.cftc.gov/Commitments-of-Traders/TFF-Futures-Only/gpe5-46if
- https://www.cftc.gov/PressRoom/PressReleases/9316-26

## 3. Phase 387 event-count gate calculation

Phase 387 defines the primary crowding state as the empirical mid-rank percentile of current Leveraged Money net-long/open-interest against the **prior 52 valid prospectively first-seen weekly observations**. The current observation is excluded from its reference distribution. High crowding is fixed at percentile >= 0.80.

Under an idealized IID continuous null (no ties), the current value's rank among itself plus 52 prior observations is uniform over 53 ranks. The high state therefore occurs when the current observation ranks 43rd through 53rd, giving:

`p(high) = 11/53 = 20.7547%`.

This is a mathematical reference, **not an empirical estimate** of actual TFF crowding frequency. Serial dependence, ties, regime changes and missing reports can alter the realized rate.

### 3.1 Training gate

The preregistration requires at least 52 prior prospective training observations, including at least 20 high-crowding and 40 non-high observations, with every training outcome fully matured before the evaluation timestamp.

Under the IID reference:

| Prospective training observations | Expected high events | Probability of at least 20 high |
|---:|---:|---:|
| 52 | 10.79 | 0.26% |
| 96 | 19.92 | 53.28% |
| 112 | 23.25 | 80.71% |
| 122 | 25.32 | 90.61% |
| 130 | 26.98 | 95.14% |

The 20-high requirement, not the 40 non-high requirement, is the binding event-count condition under this reference distribution.

### 3.2 Evaluation gate

The preregistration requires at least 150 valid prospective evaluation observations per contract, including at least 30 high-crowding and 100 non-high observations.

| Evaluation observations | Expected high events | Probability of at least 30 high | Probability of at least 100 non-high |
|---:|---:|---:|---:|
| 150 | 31.13 | 62.20% | 99.99% |
| 164 | 34.04 | 80.77% | effectively 100% |
| 175 | 36.32 | 90.05% | effectively 100% |
| 185 | 38.40 | 95.01% | effectively 100% |

Thus, 150 is a hard minimum, not a reliable planning count if the objective is to have a high probability of meeting the 30-event gate. Under the idealized reference, 175–185 evaluation observations provide approximately 90–95% probability of reaching 30 high observations.

### 3.3 Indicative calendar duration under weekly cadence

The training sample includes the first 52 observations used for the percentile reference; those observations can enter training only after their 20-session outcomes mature. Using the 90% event-count planning values, the indicative collection path is approximately:

- 122 prospective weekly reports to accumulate the training gate;
- about four additional weeks for the last training outcome to mature;
- 175 prospective evaluation reports.

Total: approximately **301 weekly reports, or 5.8 years**, assuming no missed reports, no cadence change, stable event frequency and no additional data-quality exclusions. A 95% event-count planning envelope is approximately 319 reports, or 6.1 years.

This is a planning diagnostic, not a forecast or a reason to relax the preregistration. Actual capture gaps, TFF cadence, ties, serial dependence, contract changes and data-quality exclusions may lengthen the period. If TFF becomes semiweekly, the existing weekly hypothesis is suspended rather than mechanically accelerated.

## 4. Decision

1. Keep all Phase 387 feature definitions, thresholds, training gates, evaluation minimums, outcome definitions and kill rules unchanged.
2. Do not use the 3,035-row historical archive to fill prospective warm-up, training or evaluation observations.
3. Do not lower the 20-high training gate or 30-high evaluation gate to accelerate completion.
4. Do not reinterpret the 150-observation minimum as a guarantee of adequate power. The calculation above concerns event-count feasibility only; it is not a power analysis for a particular effect size.
5. Inspect the first genuine Phase 384 scheduled run after the 2026-11-16 release. Only a new report with reproducible first-receipt metadata can enter the prospective ledger.
6. If the CFTC changes to semiweekly publication, freeze the weekly study and preregister a separate cadence-specific design before using any new observations.

## 5. Strategy controls

- No forward-return, alpha, OOS, bootstrap, LOO or holdout test was run.
- No source or signal was admitted.
- `F80_TOP20_PARTIAL50_BASELINE_C20`, universe, parameters, holdout, capital, exposure and production remain unchanged.
- No data purchase, vendor contact, API key, manual dispatch or workflow modification occurred.
