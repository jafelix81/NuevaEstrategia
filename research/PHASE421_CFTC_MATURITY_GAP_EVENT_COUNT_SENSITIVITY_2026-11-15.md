# Phase 421 — CFTC rolling-rank event gates with explicit outcome-maturity gap

**Audit time:** 2026-11-15 19:34 UTC  
**Main HEAD at audit start:** `3d5a96847eef84ca1e667965885dfee71ae200dc`  
**Disposition:** Phase 420's event-count probabilities were rechecked with the four-report training-outcome maturity gap explicitly excluded from both training and evaluation event-count blocks. The resulting probabilities are effectively unchanged; the Phase 420 calendar totals and Phase 387 preregistration remain unchanged.

## 1. Repository and Actions preflight

- Inspected the latest 100 Actions runs (7,659 total): 62 success, 37 failure, 1 cancelled; zero queued, in-progress, waiting or requested. No workflow was started or rerun.
- Inspected the full branch listing across three non-empty pages (261 branches), 56 open PRs and all 63 workflow files. No PR was merged, retargeted or otherwise changed.
- Main HEAD at audit start was `3d5a96847eef84ca1e667965885dfee71ae200dc`.

### SEC Form 144

Latest run [43743993846](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43743993846) is a successful `schedule` run. Both jobs passed; the offline regression passed 15/15. Live receipt was 2026-11-15 17:58:03 UTC. The two feeds returned 50 Form 144 and 5 Form 144/A entries; 55 feed-observation rows were appended, with zero new accessions, events, candidate issuer matches or XML resolutions. No feed-window gap was detected at that poll. Artifact [14173342433](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43743993846/artifacts/14173342433), SHA-256 `0f00cbcc4b2809f18cd8e7c0292b67713c21d55015aff6c06452d56031e50a10`.

Persistent state: poll_count=5 (two bootstrap plus three scheduled polls); 165 feed-observation rows across the three scheduled runs; the 52 initial event records remain baseline-only and signal-ineligible.

The configured `:37` schedule slot at 18:37 UTC was not visible in Actions by 19:34 UTC. This is an unobserved slot, not a confirmed workflow deactivation or a known root cause. The next nominal slot is 19:37 UTC. Do not manually dispatch, duplicate or edit the cron based on this observation.

### CFTC TFF

The latest Phase 384 run remains [43525140200](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43525140200), a branch-push bootstrap, not a prospective schedule capture. Its job passed 11/11 tests; the log confirms 3,035 historical rows, no overwrite of the existing baseline, and zero signal-eligible historical rows. Artifact [14084802705](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43525140200/artifacts/14084802705).

The persistent CFTC state still has last_capture_utc=2026-11-13T23:03:38Z, mode=branch_push_baseline, 3,035 row hashes, and latest report date 2026-11-03 for ES, NQ, YM and RTY. No Phase 384 `schedule` run exists yet. The next expected poll is Monday 2026-11-16 at 22:15 UTC, after the official 20:30 UTC CFTC release. Phase 387 remains weekly-only pending actual prospective report dates.

## 2. Why this sensitivity was needed

Phase 420's simulation evaluated consecutive training and evaluation blocks, while its calendar envelope separately added approximately four weekly intervals for the final training outcome to mature. The calendar arithmetic was conservative, but the simulated joint event-count probability did not explicitly exclude those four intervening report indicators.

Phase 421 repeats the same synthetic rolling-rank experiment but excludes a four-report maturity gap between the final training block and the start of the evaluation block. A five-report gap is included as a small holiday/delay sensitivity. The gap observations are not counted in either block.

## 3. Reproducible simulation

Added `research/phase421_cftc_maturity_gap_event_count_simulation.py`.

- 200,000 synthetic IID continuous paths; NumPy `default_rng(20261115)`.
- Prior-only 52-observation rolling reference; current observation excluded.
- HIGH iff at least 42 of the prior 52 values are below the current value.
- Same training gates (at least 20 HIGH and 40 non-HIGH) and evaluation gates (at least 30 HIGH and 100 non-HIGH).
- Same consecutive block plans as Phase 420; evaluation starts after an explicitly excluded gap of 0, 4 or 5 rolling indicators.
- Wilson 95% Monte Carlo intervals.
- No CFTC history, TFF positions, market prices, labels, returns or actual signal observations are used.

### Joint gate sensitivity

| Training + evaluation | No gap | 4-report gap | Change | 5-report gap |
|---|---:|---:|---:|---:|
| 111 + 161 | 82.1435% | 82.2050% | +0.0615 pp | 82.1975% |
| 116 + 166 | 91.1070% | 91.1355% | +0.0285 pp | 91.1500% |
| 120 + 170 | 95.3290% | 95.3600% | +0.0310 pp | 95.3620% |

Four-gap Wilson 95% intervals:
- 111 + 161: 82.0368%–82.3720%.
- 116 + 166: 91.0101%–91.2593%.
- 120 + 170: 95.2669%–95.4513%.

The four-report gap barely changes the joint probabilities under the IID continuous reference. The 116+166 plan remains just above 90% joint event-count feasibility; the 120+170 plan remains just above 95%. The 111+161 plan remains below 90% jointly and is not the selected ~90% planning case.

## 4. Calendar and interpretation

The Phase 420 calendar totals remain unchanged because they already included the four-report training-maturity interval:

- ~90% joint event-count plan: 52 warm-up + 116 training + 4 maturity-gap reports + 166 evaluation + 4 final-outcome-maturity reports = **342 weekly reports (~6.6 years)**.
- ~95% joint event-count plan: 52 + 120 + 4 + 170 + 4 = **350 weekly reports (~6.7 years)**.

The 4/5-report gap is a planning approximation only. Actual 20-NYSE-session outcome maturity must be calculated from the NYSE session calendar and each observation's eligible entry session. Do not replace the actual maturity timestamp with a fixed row offset.

The simulation still assumes IID continuous raw inputs. Real CFTC positions may be serially dependent, tied/discrete, regime-dependent, revised or late. These are synthetic event-count diagnostics, not empirical HIGH-state frequencies, statistical power, expected completion dates or evidence of alpha.

## 5. Decision and controls

- Phase 387's feature, 0.80 threshold, 20/40 training and 30/100 evaluation gates, outcomes, chronological rules, block bootstrap/HAC and kill/advance rules remain frozen.
- No historical CFTC rows were used for features, labels, returns or model fitting.
- No forward-return, alpha, OOS, bootstrap, LOO or holdout test was run.
- No source or signal was admitted.
- `F80_TOP20_PARTIAL50_BASELINE_C20`, universe, parameters, holdout, capital, exposure and production remain unchanged.
- No vendor purchase/contact, data request, credential change or workflow modification.
