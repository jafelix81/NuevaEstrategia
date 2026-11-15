# Phase 413 — SEC Form 144 schedule-delivery recheck (2026-11-15)

**Audit time:** 2026-11-15 09:14 UTC  
**Disposition:** The SEC capture workflow is enabled and one scheduled poll succeeded, but the intended hourly cadence is not yet demonstrated. No root cause for the missing subsequent schedule events is established. Do not manually duplicate the capture or change the cron speculatively.

## 1. Mainline and Actions audit

- Main HEAD at audit start: `25fcbf6b5b1e4a44285435bca6f0dc5672bb8b33`.
- Default branch: `main`; repository permissions include push/admin.
- Latest 100-run page inspected. Latest runs: Phase 411 offline-only PR regressions [43681298839](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43681298839) and [43681270194](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43681270194), both SUCCESS.
- Explicit Actions filters: `event=schedule` returned 11 repository-wide runs; only one belongs to Phase 403, [43670461605](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43670461605). `status=queued` and `status=in_progress` both returned zero.
- Run 43670461605 is the only Phase 403 schedule event in the inspected history. It started 2026-11-15 03:01:47Z, completed 03:02:06Z, and used main commit `3d450a4d1d27f13663303cbf65f987150571a282`.
- The workflow file at that exact run commit contains `cron: "37 * * * *"`. There are no later Phase 403 schedule events through 09:14Z. The observed run started at 03:01Z rather than the nominal :37 minute, so GitHub delivery is not an exact wall-clock clock; subsequent hourly delivery is unproven.
- The workflow remains present on main with `schedule`, `workflow_dispatch`, offline regression, live-capture, concurrency group `sec-form144-prospective-first-seen`, and append-only persistence. No workflow was dispatched, duplicated, or edited in this audit.

## 2. Run 43670461605 — jobs, logs and artifact

Both jobs succeeded:
- `offline-regression`: SUCCESS.
- `live-capture`: SUCCESS; compile, SEC feed poll, append-only ledger/state commit and artifact upload all completed.

Artifact [14143174642](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43670461605/artifacts/14143174642), 1,188 bytes, ZIP SHA-256 `a518f07b6bb6b67582d3c578ff0e8656171179df5c67ef169cfe588c1dd04c3a`, was downloaded and its `summary.json` inspected.

- `POLL_COMPLETE_NO_NEW_ACCESSIONS`.
- 50 Form 144 and 5 Form 144/A entries observed; 55 per-feed observations appended.
- Zero new accessions, events, issuer-candidate matches or XML resolutions.
- No possible feed-window gap at that poll: the prior latest accession remained present in each feed.
- First-seen remains a poll-receipt upper bound; public-availability certification, same-day use and signal eligibility are all false.
- The 52 initial event rows remain baseline-only.

Persistent state confirms `poll_count=3`, last successful receipt `2026-11-15T03:02:02Z`, last run `43670461605`, and `signal_eligible=false`. No subsequent poll has updated that state.

## 3. CFTC and Phase 411

- Phase 384 workflow is present on main and polls weekdays at 22:15 UTC. Its latest run in the inspected set, [43525140200](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43525140200), is a `push` bootstrap, not a scheduled capture. Job and artifact [14084802705](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43525140200/artifacts/14084802705) were inspected; it contains 3,035 historical rows, no new prospective event, and no alpha eligibility.
- No CFTC schedule run is present yet. The next expected weekday poll is Monday 2026-11-16 at 22:15 UTC, after the currently scheduled COT release at 20:30 UTC. Do not infer the announced semiweekly TFF regime until actual TFF report dates and first-receipt records establish it.
- Phase 411 run [43681298839](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43681298839) is an offline-only PR regression; 17/17 tests passed. It made no CFTC request and produced no capture artifact.

## 4. Open research branches / PR topology

- 56 open PRs were returned by the repository API; most are draft and several are stacked on other research branches rather than directly on main.
- PR #60, the clean Phase 384 mainline activation, is merged. Do not confuse it with open draft PR #59, whose base is Phase 383.
- PR #57 (Phase 381 price-provider audit) remains draft and based on Phase 380; PR #61 (Phase 385 publication-clock census) remains draft and based on Phase 375; neither is itself a mainline activation.
- PR #48 (Cboe source ranking) and PR #37 (SEC 13D/G parent retrieval) remain draft. The latter's SEC contact-secret gate is unchanged.
- No stacked PR was merged or rebased during this audit.

## 5. Research decisions and controls

- SEC Form 144 remains a prospective capture/availability experiment only. Three successful polls do not establish a robust hourly schedule; the one scheduled poll has no new accessions. Do not convert the 52 baseline rows into prospective events.
- FINRA Phase 20C remains blocked at 328/329 valid price histories for the fixed diagnostic panel; missing names remain AVB, EA, EQR, LPRO, ROKU, WBD and WBS. No universe reduction or provider mixing.
- CFTC historical TFF rows remain warm-up/baseline only; prospective first receipt is still required.
- OptionMetrics TradeFlow, Cboe Option Trades/Open-Close and SEC insider sources remain feasibility candidates, not admitted signals; historical delivery/version, lawful sample access and PIT identity gates remain open.
- No new feature, forward-return, alpha, OOS, bootstrap, LOO or holdout test was run. No data purchase, vendor contact, credential change, or production action.
- `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen; holdout, universe, parameters, capital and exposure remain unchanged.

## Next checks

1. Observe whether the existing SEC schedule produces another genuine `schedule` run; inspect actual start/receipt time and feed-window continuity. Do not infer successful hourly operation from the single run.
2. Inspect the first Phase 384 `schedule` run after the Monday 2026-11-16 CFTC publication. Preserve raw hashes and actual receipt time; do not backdate.
3. Continue Phase 20C only after a licensed/reproducible price panel resolves all 329 required histories.
