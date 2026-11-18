# Phase 491 — Cross-source scheduled-capture delivery and ledger readiness audit

**Audit cutoff:** 2026-11-18 23:02 UTC  
**Main HEAD at preflight:** `e2f2a036d1ba6584045d9dfb4140029651f46d9a` (Phase 490; committed 22:30:10 UTC)  
**Disposition:** **No duplicate/manual captures. SEC Form 144 and Form 4 have successful first baselines, but no later scheduled run is present in the latest 100-run Actions inventory. The first scheduled CFTC (22:25 UTC) and FINRA Reg SHO (22:30 UTC) windows are also absent at cutoff. This is a schedule-delivery observation, not proof that any workflow is disabled.**

## 1. Repository and Actions preflight

- Default branch: `main`; current main ref: `e2f2a036d1ba6584045d9dfb4140029651f46d9a`.
- Actions API reports **7,863 total runs**. The latest 100 were inspected; **0 were in progress and 0 were queued**.
- Latest run: [44396134680](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44396134680), Phase 403 SEC Form 144 scheduled capture, completed successfully at 20:56:50 UTC.
- Previous scheduled capture: [44380395679](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44380395679), Phase 476 SEC Form 4/4-A, completed successfully at 19:26:15 UTC.
- No Actions run later than 20:56:50 UTC appears in the latest 100-run inventory at the 23:02 UTC cutoff.
- Branch pagination: **317 unique branches** (100 + 100 + 100 + 17).
- Open pull requests: **56**. The two non-PR open issues are #132 (Cboe public sample rights) and #9 (SEC 13D/G historical coverage). The issues endpoint includes PRs, so its 58 returned items are not 58 standalone issues.
- Relevant stacked draft PRs remain open: #61 (FINRA T1 publication clock), #59/#58/#56/#55 (CFTC TFF lineage), #57 (FINRA price-provider fallback), #48 (Cboe options source ranking), #37 (SEC 13D/G parent retrieval), and #1 (independent alpha lab). Their base branches are intentionally divergent; none was merged or rebased in this audit.
- No workflow was dispatched, rerun, cancelled, or duplicated. No branch or code change was made to a capture workflow.

## 2. Scheduled-window census

The latest 100 Actions runs contain only four scheduled events:
- [44396134680](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44396134680), SEC Form 144, 20:55:44 UTC start.
- [44380395679](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44380395679), SEC Form 4, 19:25:35 UTC start.
- [44302697069](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44302697069), SEC Form 144, failed at 12:18:41 UTC before the live capture.
- [44232546204](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44232546204), CFTC TFF, 03:44:45 UTC start.

| Workflow | Existing UTC schedule | Last verified scheduled run | Window(s) elapsed by cutoff with no run in inventory |
|---|---|---|---|
| SEC Form 4/4-A | minute 17, weekdays | 19:25:35 | 20:17, 21:17, 22:17 |
| SEC Form 144/144-A | minute 47, daily | 20:55:44 | 21:47, 22:47 |
| CFTC TFF | 22:25 weekdays | 03:44:45 | 22:25 |
| FINRA Reg SHO daily | 22:30 and 23:30 weekdays | No scheduled run found | 22:30; 23:30 was still in the future |

The missing events may reflect GitHub scheduled-event delay or delivery behavior. The available read interface does not expose workflow administrative enabled/disabled state. Do **not** infer that workflows are disabled from this census. Recheck the next scheduled windows before escalating; do not manually dispatch simply to fill a missing schedule slot.

## 3. SEC Form 144/144-A — successful capture, no signal eligibility

Run [44396134680](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44396134680):
- Jobs: `offline-regression` and `live-capture`, both successful.
- Offline regression: **40/40** tests passed.
- Poll: **20:56:07–20:56:30 UTC**.
- 51 unique new accessions: 50 Form 144 and 1 Form 144/A; 52 feed entries with one cross-feed duplicate.
- 51/51 XML and acceptance reconciliations; both prior feed watermarks found; no possible gap.
- Current persisted state: 11 complete polls, 247 canonical event rows, 0 partial polls.
- Current poll added 51 bounded metadata observations, but **0 public-availability-certified, 0 verified historical F80 members, and 0 signal-eligible events**.
- Artifact [14470455938](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44396134680/artifacts/14470455938), SHA-256 `a6d47ef938306f3efa4fcff412c3a737995611030b00a3afe498e5e9ee525d07`.
- Job logs confirm the live capture committed the append-only state and uploaded the artifact.

Form 144 remains a proposed-sale notice, not evidence of a completed execution. Keep the 51 rows as metadata-only observations; do not interpret them as executed insider sales.

## 4. SEC Form 4/4-A — baseline only; no second interval

Run [44380395679](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44380395679):
- Jobs: `offline-regression` and `live-capture`, both successful.
- Offline regression: **37/37** tests passed.
- Poll: **19:26:00–19:26:08 UTC**.
- 35 unique accessions: 10 Form 4 and 25 Form 4/A.
- Both feeds completed one page; no pagination errors.
- Persisted state still records the same single successful poll, with no previous watermark. All 35 rows remain `INITIAL_BASELINE_NO_LOWER_BOUND`.
- Bounded metadata rows: **0**; research-eligible rows: **0**; signal-eligible rows: **0**.
- Artifact [14463211992](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44380395679/artifacts/14463211992), SHA-256 `7765d6bd966aa2370b8ba5baff37a0bb3f3ba9445a0e278b3caa8c971532f5e6`.
- The live job log confirms run ID 44380395679 and the 19:26:00–19:26:08 UTC baseline; fixture examples in the offline test suite are not live observations.

The next successful scheduled poll must find both previous feed watermarks before any new event can be bounded. Do not backfill the baseline into a false historical interval.

## 5. CFTC TFF — prospective state stale at cutoff

The current `research/data/cftc_tff_prospective/state.json` reports:
- Last successful capture: **2026-11-18 03:44:57 UTC**.
- Latest report date for each of four contract codes: **2026-11-10**.
- Baseline manifest: 3,035 historical rows (851 each for three codes; 482 for the fourth).
- Historical availability: `NOT_CERTIFIED; feature warm-up only`.
- Historical rows are not signal-eligible.

The existing workflow schedule is 22:25 UTC weekdays. No later CFTC scheduled run appears in the latest 100-run Actions inventory at cutoff. The 22:25 window is therefore unverified, not a successful capture. The four contract rows from the Nov 10 report date must not be counted as four independent weekly observations.

No CFTC data were downloaded or altered in this audit.

## 6. FINRA Reg SHO — first scheduled window not observed

The existing Phase 469 workflow is present in `main` and declares weekday polls at 22:30 and 23:30 UTC. Its design stores only file-level hashes, timestamps, row counts and schema metadata; raw daily files are held in memory and are not committed. A first observation of an older trade-date file is bootstrap, not a same-day research observation.

At cutoff:
- No scheduled Phase 469 run appears in the latest 100 Actions runs.
- `research/data/finra_regsho_daily_first_seen` does not exist on main.
- No first-seen FINRA raw-file manifest or observation has been persisted.
- The 22:30 UTC window had elapsed by 32 minutes; the 23:30 UTC window had not yet occurred.

This does not establish that the 22:30 event was permanently dropped or that the workflow is disabled. Do not dispatch manually. If the 23:30 poll appears, inspect its job log and artifact before interpreting any row.

## 7. Cross-source research disposition

| Source | Current evidence | Disposition |
|---|---|---|
| SEC Form 4/4-A | 35 initial-baseline accessions; no bounded interval | Continue existing collector; no signal |
| SEC Form 144/144-A | 247 event rows; latest 51 bounded metadata observations | Continue; no execution or signal inference |
| SEC 13D/G | Issuer/filer identity defects; panel remains quarantined | Rebuild only through existing Phase 350/identity lineage |
| FINRA Reg SHO | No first-seen ledger yet | Wait for existing scheduled capture; no Phase 20B/C promotion |
| FINRA short interest / ATS | Separate historical vintage, coverage and identity gates remain | Continue existing stacked PRs; do not conflate with daily short volume |
| CFTC TFF | 3,035-row historical warm-up, availability uncertified; prospective latest report date Nov 10 | Continue existing prospective capture; no signal before PIT history |
| Cboe / OPRA options | Existing Phase 231/352–373 work and PR #48; sample rights and PIT/licensing gates remain | Do not duplicate the options audit or acquire data without rights |
| N-PORT / 13F | Delayed disclosure, historical identity and amendment gates remain | No new workflow or signal |

Phase 487 remains the controlling FINRA adjudication: Phase 20B's replacement ranking had no RuleScore dispersion (24/24 replacements tied), and Phase 20C's tested incremental spreads did not establish stable, cost-adjusted alpha. Those implementations remain rejected; Phase 20A remains exploratory only.

## 8. Frozen strategy and controls

No prices, transaction rows, raw FINRA files, option trades, or new market data were acquired. No backtest, event study, forward-return, OOS, bootstrap, LOO or holdout test was run.

`F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen:
- universe and parameters unchanged;
- no holding-period restriction added;
- capital, exposure and costs unchanged;
- holdout and production unchanged;
- no new signal admitted.

**Conclusion:** the two SEC collectors have each demonstrated one successful scheduled baseline/capture, but only Form 144 has a bounded interval at this cutoff. CFTC and FINRA did not show their expected first evening scheduled events in the latest Actions inventory. The correct response is to preserve the current ledgers, recheck subsequent existing schedule slots, and avoid manual or duplicate captures. This is an operational delivery audit, not evidence of predictive alpha.
