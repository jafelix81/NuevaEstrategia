# Phase 466 — CFTC schedule delivery and prospective sample-feasibility audit

**Audit time:** 2026-11-17 23:51 UTC  
**Main HEAD:** `43cc8a85d6744722bb6d895322584d5104d3542b`  
**Disposition:** CFTC prospective capture remains unverified despite the workflow being present on the default branch. Correct the stale 22:15 UTC documentation to the current 22:25 UTC cron. No source row was backdated, no manual capture was dispatched, and no strategy change was made.

## 1. Preflight and no-duplicate controls

- Repository metadata confirms public, unarchived repository; default branch is `main`.
- Main HEAD is Phase 465 finalization commit `43cc8a85d6744722bb6d895322584d5104d3542b`.
- Branch enumeration: 299 branches across four pages. Open PR search: 56.
- The connected GitHub interface in this audit does not expose a repository-wide workflow-run listing or workflow enablement endpoint. Therefore this report does **not** claim a current zero-active/zero-queued inventory.
- Directly inspected known jobs/logs/artifacts:
  - SEC scheduled run [44179257367](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44179257367): both `offline-regression` and `live-capture` succeeded; artifact [14371301851](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44179257367/artifacts/14371301851). This run predates Phase 465 pagination.
  - Phase 465 PR CI [44195015699](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44195015699): 40/40 offline tests passed; live-capture was skipped, as intended; no artifact.
  - CFTC run [43525140200](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43525140200): successful branch-push bootstrap, not a scheduled first-receipt capture; artifact [14084802705](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43525140200/artifacts/14084802705).
- No workflow was dispatched or rerun. The SEC workflow's next hourly slot was 23:47 UTC; because the current run inventory is unavailable and the slot may still be running, no duplicate SEC poll was started.

## 2. CFTC activation topology is correct; delivery is not evidenced

The clean activation PR [#60](https://github.com/jafelix81/NuevaEstrategia/pull/60) is **merged** to `main` (2026-11-14 00:45 UTC, merge commit `e88e553afc235916e37e9236e1890b714163c229`). The workflow file exists on the default branch:

- [Workflow](https://github.com/jafelix81/NuevaEstrategia/blob/main/.github/workflows/phase384_cftc_tff_prospective_capture.yml)
- Current blob SHA: `40e385004c69e188dc0dcc6e336d0675280cae61`
- Current schedule: `25 22 * * 1-5` UTC (weekday polling).
- The workflow has `schedule` and `workflow_dispatch` triggers. Its push trigger is branch-scoped to the bootstrap branch; that does not prevent default-branch schedule execution.

**Documentation correction:** Phase 465's report/addendum says the CFTC slot is 22:15 UTC. The current mainline workflow file is authoritative and uses **22:25 UTC**, moved after the missed 2026-11-16 slot. The 22:15 wording is stale and must not be used for operational timing.

No successful scheduled CFTC capture commit or artifact is evidenced after the Nov 13 bootstrap. The 2026-11-17 22:25 UTC slot was not evidenced in the last known run inventory (the Phase 465 preflight at 22:47 UTC). Because current repository-wide run listing and workflow enablement are not exposed, the cause cannot be distinguished between a disabled workflow, a missing schedule event, or a failed scheduled run. Do not infer the cause from absence of a capture commit alone.

## 3. Current official CFTC publication clock

Official sources checked on 2026-11-17:

- The CFTC release calendar lists the holiday-delayed **2026-11-16, 3:30 p.m. ET** release for positions as of 2026-11-10; the next listed releases are **2026-11-20** and **2026-11-30**, also at 3:30 p.m. ET. [Official release schedule](https://www.cftc.gov/MarketReports/CommitmentsofTraders/ReleaseSchedule/index.htm).
- TFF Futures Only dataset `gpe5-46if` shows **Last Updated 2026-11-16**, approximately 47.4K rows. [Official dataset](https://publicreporting.cftc.gov/Commitments-of-Traders/TFF-Futures-Only/gpe5-46if).
- CFTC's October 27 announcement says it plans to move COT publication from weekly to twice weekly by the end of 2026 (Monday positions on Wednesday, Wednesday positions on Friday). The current official release calendar still lists the existing dated releases; the announcement alone is not proof that TFF has switched cadence. [CFTC release 9316-26](https://www.cftc.gov/PressRoom/PressReleases/9316-26).

The existing Phase 384 state remains the Nov 13 branch-push baseline: 3,035 historical warm-up rows across four index contracts, latest report date Nov 3, and zero prospectively received observations. The Nov 10 report is visible at the source but has not been recorded by our pipeline. It must receive the actual first-receipt time of the first successful scheduled capture; do not backdate it to Nov 16 or to its Tuesday position date.

## 4. Prospective study sample feasibility

Phase 387's preregistered ES/NQ crowding-risk study requires, **per contract**, at least 52 fully matured prospective training observations followed by at least 150 evaluation observations, with separate high/non-high event-count minima. Under the current weekly regime this implies at least 202 eligible weekly report events (about 3.9 years at 52 reports/year) before the primary evaluation sample can complete.

The 3,035-row static archive cannot shorten this clock: its historical first-publication availability is not certified and every baseline row remains signal-ineligible. If TFF becomes semiweekly, the weekly preregistration must be suspended and replaced by a separately preregistered cadence/horizon design; four reports must not be treated as four weeks.

**Conclusion:** CFTC TFF remains a potentially useful slow-moving risk/crowding context source, but it is not a near-term alpha candidate under the current prospective-only design. The sample clock and unverified delivery are binding feasibility constraints.

## 5. SEC Form 144 status after Phase 465

- The latest inspected live SEC run [44179257367](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44179257367) ran before Phase 465's pagination code was merged. Its Form 144 feed returned 50 rows and omitted the prior watermark, so those rows remained gap-quarantined.
- Phase 465 PR [#126](https://github.com/jafelix81/NuevaEstrategia/pull/126) merged and its 40-test CI passed, but the live-capture job was skipped on PR.
- The SEC schedule is hourly at minute 47. The post-merge 23:47 UTC poll may be active or may have completed, but the available connector cannot enumerate it. No manual dispatch or rerun was started.
- Pagination is not live-validated until a post-merge scheduled run's job log and artifact confirm page offsets, watermark recovery, page hashes, and conservative poll-start bounds. The first post-upgrade poll must retain the legacy-clock ineligibility rule.

## 6. Human operational gate

Before the next weekday CFTC slot, verify in GitHub Actions that **“Phase 384 - CFTC TFF prospective first-receipt capture”** is enabled. If enabled, inspect the 2026-11-17 scheduled run and its job log; if disabled, enable the existing workflow rather than creating another workflow or changing its cron. The connected read interface cannot inspect or change that setting.

No FINRA credentials or SEC contact secret were read or changed. FINRA OAuth and the monitored-contact `SEC_USER_AGENT` remain separate human gates.

## 7. Research disposition

- CFTC historical archive: warm-up only; no PIT admission.
- CFTC prospective observations: zero verified.
- SEC Form 144 pagination: offline-tested, live validation pending.
- FINRA: no new API request; old truncated Phase 31 panel remains killed as retrieved.
- Nasdaq NOTO/PHOTO and UREF: still conditional on licensed/sample access and universe-coverage audit.
- No return/alpha/OOS/bootstrap/LOO test or signal admission.
- `F80_TOP20_PARTIAL50_BASELINE_C20`, universe, parameters, capital, exposure, holding rules, holdout and production remain frozen.

## 8. Reproduction references

- Phase 465 report: [PHASE465_SEC_FORM144_ATOM_PAGINATION_AND_CFTC_DELIVERY_AUDIT_2026-11-17.md](PHASE465_SEC_FORM144_ATOM_PAGINATION_AND_CFTC_DELIVERY_AUDIT_2026-11-17.md).
- Phase 465 CI: [44195015699](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44195015699).
- Phase 384 workflow: [.github/workflows/phase384_cftc_tff_prospective_capture.yml](../.github/workflows/phase384_cftc_tff_prospective_capture.yml).
- Phase 384 bootstrap report: [PHASE384_CFTC_TFF_PROSPECTIVE_CAPTURE_BOOTSTRAP_2026-11-13.md](PHASE384_CFTC_TFF_PROSPECTIVE_CAPTURE_BOOTSTRAP_2026-11-13.md).
