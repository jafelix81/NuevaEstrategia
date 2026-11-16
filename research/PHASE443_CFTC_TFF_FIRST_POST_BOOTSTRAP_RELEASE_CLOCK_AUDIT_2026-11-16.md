# Phase 443 — CFTC TFF first post-bootstrap release and publication-clock audit

**Audit time:** 2026-11-16 22:31 UTC  
**Main HEAD at preflight:** `8d5118ad75e7f6c01416ddfb1d412978960d6679` (Phase 442)  
**Disposition:** the first post-bootstrap TFF report is publicly visible, but the 2026-11-16 scheduled Phase 384 capture was not observed by 22:31 UTC. Preserve the next actual first-receipt timestamp; do not backdate or manually simulate it.

## 1. Actions preflight

- Latest 100 Actions runs: 99 completed, 1 in progress; 7,677 total runs.
- The only in-progress run is [43970444015](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43970444015), SEC Form 144 scheduled capture. Its offline-regression job completed successfully; its live-capture job remained in progress. No duplicate was started.
- Latest CFTC TFF capture remains [43525140200](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43525140200), a **push/bootstrap** on 2026-11-13, not a scheduled observation. It completed successfully and uploaded artifact [14084802705](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43525140200/artifacts/14084802705).
- The mainline Phase 384 workflow still specifies weekday cron `15 22 * * 1-5`. No CFTC schedule-event run for 2026-11-16 was present in the latest run inventory at 22:31 UTC. This is an unobserved scheduled slot; the root cause is not established.

## 2. Official source now shows the new report

The official CFTC TFF Futures Only report page now displays **positions as of 2026-11-10**, with changes measured from 2026-11-03. It includes the four TFF categories: Dealer/Intermediary, Asset Manager/Institutional, Leveraged Funds and Other Reportables.

- [Current TFF Futures Only report](https://www.cftc.gov/dea/futures/financial_lf.htm)
- [Official 2026 COT release schedule](https://www.cftc.gov/MarketReports/CommitmentsofTraders/ReleaseSchedule/index.htm): 2026-11-16 is listed as a holiday-delayed 3:30 p.m. ET release; the next listed dates are 2026-11-20 and 2026-11-30.
- [CFTC release 9316-26](https://www.cftc.gov/PressRoom/PressReleases/9316-26), dated 2026-10-27, announces a plan to move COT publication to Monday-position data on Wednesday and Wednesday-position data on Friday by year-end. The current release calendar remains weekly; no observed TFF semiweekly report-date sequence is established.

The official static TFF page confirms that the Nov 10 report is public, but it does **not** establish the exact first second at which the Socrata API became available. The pipeline's own first receipt remains the only admissible prospective clock.

## 3. Reconciliation to the repository baseline

The append-only Phase 384 state currently records:

- Baseline/last capture: **2026-11-13 23:03:38 UTC**, mode `branch_push_baseline`.
- Latest report date by each of the four contract codes: **2026-11-03**.
- Historical rows: **3,035**, all warm-up only and signal-ineligible.
- No Nov 10 report has yet been recorded in the prospective state.

The Phase 384 classifier is conservative: when the next scheduled capture first observes a report date newer than the stored latest date, it records the actual capture timestamp as `first_seen_utc`. It does not use the report date or the nominal 3:30 p.m. ET release time as a substitute. The event can be a research observation from the first regular equity session after that actual receipt; `signal_eligible` remains false. No historical row is promoted and no timestamp is backdated.

If the next scheduled poll on **2026-11-17 at 22:15 UTC** observes the Nov 10 report, its first-seen timestamp will be the actual Nov 17 capture time, not Nov 16. This is a one-day availability delay, not a reason to fabricate a Nov 16 receipt.

## 4. Decision

1. Keep the existing Phase 384 weekday schedule unchanged after this single unobserved slot; the workflow remains the sole capture process.
2. Do not dispatch a manual diagnostic to initialize or advance state. Manual mode is explicitly state-neutral and not research-observation eligible.
3. Do not create a second polling workflow or infer first receipt from the CFTC HTML page.
4. Keep Phase 387's weekly-only preregistration unchanged. The semiweekly COT announcement is a planned regime change, not evidence that TFF has already changed cadence.
5. Inspect the next scheduled run's event type, first_seen_utc, raw hash, contract coverage and artifact before admitting even a research observation.

## 5. Research controls

- No CFTC API data were downloaded or persisted in this audit.
- No event was fabricated or backdated.
- No feature, return, alpha, OOS, bootstrap, LOO or holdout test was run.
- No source or signal was admitted.
- `F80_TOP20_PARTIAL50_BASELINE_C20`, universe, parameters, holdout, capital, exposure and production remain unchanged.
