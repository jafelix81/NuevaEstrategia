# Phase 482 — Scheduled capture delivery census and research gate status

**Audit cutoff:** 2026-11-18 15:18 UTC  
**Main HEAD at preflight:** `f0ef405855b0d72a70657bbca37663c3da009fa1`  
**Disposition:** repository-wide schedule delivery remains materially incomplete for SEC first-seen collectors. No signal, return test, or production change.

## 1. Preflight — runs, jobs, artifacts, branches, PRs and research files

- Default branch: `main`; repository visibility: public.
- Latest main commit: `f0ef405855b0d72a70657bbca37663c3da009fa1` (Phase 481 operational delivery audit).
- GitHub Actions: **7,844 total runs**. The latest 100 comprise 56 pull-request, 41 push and 3 schedule events.
- Explicit API queries: **0 in progress; 0 queued**. No workflow was dispatched, rerun, duplicated or cancelled.
- Schedule-filtered history: **22 total schedule-triggered runs**. The latest three are Phase 403 at 12:18 UTC (failure), CFTC Phase 384 at 03:44 UTC (success), and Phase 403 at 03:09 UTC (success).
- Branches: **311** (all branch-search pages exhausted); open PRs: **56**; workflow files: **82**; recursive main tree: **416 entries**.
- Relevant mainline files and prior reports were inspected: Phase 403/476/469/384 workflow YAMLs; Phase 469/470; Phase 481; Phase 392; Phase 386; Phase 450/451; Phase 456; Phase 391; Phase 430; and the Phase 20C/price-provider and delisted-security reports.
- No current Actions run is active. The latest successful PR CI is not treated as a live market-data capture.

## 2. SEC Form 144 — post-fix scheduled capture still missing

Configured schedule: `47 * * * *` UTC.

- Last successful scheduled capture: [44228413864](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44228413864), created 2026-11-18 03:09:36 UTC. Both jobs succeeded and compact artifact [14393319006](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44228413864/artifacts/14393319006) exists (2,276 bytes). It established the first post-pagination baseline; it did not create a new lower bound for later first-seen intervals.
- Next scheduled run: [44302697069](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44302697069), created 12:18:41 UTC, failed in `offline-regression`. Two Phase 464 assertions were stale: `state_complete_poll_count` expected 9 but was 10; `event_rows_total` expected 106 but was 196. The `live-capture` job was skipped; artifact list is empty; no SEC request or ledger mutation occurred.
- PR #140 merged the test repair at 12:32:51 UTC. Its successful PR check [44304878119](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44304878119) passed 40 tests, but the live job was skipped by design.
- No post-fix schedule event appears for 13:47 or 14:47 UTC. The 15:47 UTC slot is still ahead of this audit cutoff.

The failure is a test-snapshot regression, not a live SEC data failure. Until a later scheduled run completes both jobs, the post-pagination Form 144 receipt clock remains unadvanced.

## 3. SEC Form 4/4-A — no scheduled first-seen poll observed

Configured schedule: `17 * * * 1-5` UTC. The workflow is present on main and the default branch remains main.

- Phase 478 merge completed at 11:18:15 UTC.
- No schedule-triggered Phase 476 run exists in the 22-run schedule history.
- Expected post-merge slots 12:17, 13:17, 14:17 and 15:17 UTC are absent.
- The latest Phase 476 regression [44293347434](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44293347434) passed 37/37 offline tests; its live-capture job was skipped. There is no live artifact and no local first-seen receipt.

This is a delivery gap, not proof that the workflow is disabled. The connected read interface does not expose the administrative enabled/disabled state. Issue [#142](https://github.com/jafelix81/NuevaEstrategia/issues/142) was updated with the full schedule census and the same narrow human check: confirm the existing Phase 476 workflow is enabled and permitted on main. Do not change cron, dispatch manually or create a replacement poller.

## 4. FINRA Reg SHO and CFTC — next scheduled windows not yet due

- Phase 469 FINRA Reg SHO is configured for `30 22,23 * * 1-5` UTC. At 15:18 UTC on 2026-11-18, today's 22:30 and 23:30 UTC slots have not occurred. No schedule miss is recorded for today's slots yet.
- Phase 384 CFTC TFF is configured for `25 22 * * 1-5` UTC. Today's 22:25 UTC slot is also still ahead.
- The last successful CFTC run [44232546204](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44232546204) produced artifact [14395926632](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44232546204/artifacts/14395926632). It records one prospective report cycle (four contract rows), not four independent weekly observations. The preregistered 52-observation warm-up is not met; all remain signal-ineligible.
- No FINRA or CFTC workflow was manually dispatched or duplicated.

## 5. Research-source disposition — no false “smart money” labels

- **FINRA Reg SHO:** flow-only source. Short volume is not net short positioning, beneficial ownership, institutional identity or informed trading. Require first-seen receipt and next eligible session.
- **FINRA ATS T1:** date-level publication and revision audits exist, but HHI/top-share measure reporting ATS/firm venue concentration, not customer or beneficial-owner concentration. Effective-dated security identity and full historical universe gates remain open.
- **Cboe Open-Close / Complex Order Flow:** potentially useful opening/closing and participant-capacity context, but full historical coverage, version/PIT and licensing gates remain open. Public sample artifact rights issue [#132](https://github.com/jafelix81/NuevaEstrategia/issues/132) remains unresolved; no deletion or permission is claimed.
- **OptionMetrics TradeFlow:** leading conditional signed-flow candidate; product lineage is documented, but current schema/version history, first-delivery/correction vintages, commercial rights and 335-name coverage are unresolved.
- **Nasdaq NOTO/PHOTO:** highest-priority conditional Nasdaq options source because opening/closing and participant-origin fields are more interpretable than opaque sentiment scores. It is venue-specific, not consolidated OPRA; historical coverage, exact delivery receipts and license must be verified before acquisition.
- **Nasdaq UREF/DF and USRFH:** retail-flow/crowding controls, not smart-money proxies. UREF has broad historical coverage claims but needs actual 335-name reach and local first-receipt capture. USRFH trade/price/holdings values are deliberately scaled/noised; pre-2024-10-29 holdings are monthly, so prioritize breadth rather than raw size if a lawful sample is ever evaluated.
- **Nasdaq Options Pulse (NOSI):** low-priority comparator because its score is derived/opaque and the vendor whitepaper is not independent OOS evidence.
- **SEC N-PORT:** kill the current standalone QoQ share-growth stock-selection hypothesis. Phase 386's six-period diagnostic had mean IC -0.0697 (positive 1/6) and mean top-minus-bottom spread -0.95 pp (positive 2/6); it did not establish a net portfolio edge. Quarterly short-position levels remain delayed context only.
- **SEC 13F:** parked for broad-universe stock selection; Phase 22C coverage was 63.28% (2016Q1), 73.43% (2020Q1) and 83.58% (2024Q1) of the frozen 335 names.
- **CFTC TFF:** only one prospective report cycle is recorded; no positioning feature or return test is authorized.
- **Phase 20C:** seven delisted/corporate-action price histories remain unresolved; do not reduce the 335-name universe, impute, or mix providers without a reconciled source and terminal-return treatment.

## 6. Next gates

1. Human confirmation of Phase 476 workflow enablement; keep its existing schedule unchanged.
2. Observe the next existing Phase 403 :47 UTC schedule after the Phase 479 fix; require offline and live jobs plus a compact artifact before calling the collector restored.
3. Let today's existing FINRA 22:30/23:30 UTC and CFTC 22:25 UTC schedules run; inspect results only after they occur. Do not pre-empt them.
4. Continue the conditional options-source feasibility path (NOTO/PHOTO, OptionMetrics TradeFlow, Cboe/ThetaData) only when a lawful sample, exact field semantics, historical coverage, first-receipt/version policy and frozen-universe overlap can be verified.
5. Resolve the seven inactive/delisted price histories and corporate-action terminal returns before any full-universe Phase 20C economic test.

## 7. Frozen controls

`F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen. No universe, parameter, holding-period, capital, exposure, cost, holdout or production change. No new backtest, forward-return test, OOS, bootstrap, LOO or signal admission occurred in Phase 482.
