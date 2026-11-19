# Phase 492 — Cross-source scheduled-capture recheck and independent-alpha non-duplication

**Audit cutoff:** 2026-11-19 00:41:50 UTC  
**Main HEAD at preflight:** `2f8b184b8af2f0927e0eca8b5401851a69c9b1e5`  
**Disposition:** **No new scheduled capture appeared after the Phase 491 cutoff. Preserve existing ledgers, do not manually dispatch or duplicate workflows, and do not rerun the already-adjudicated Phase 29 candidate selection. This is an operational delivery gap, not a signal result.**

## 1. Repository and Actions preflight

- Default branch: `main`; repository last pushed at 2026-11-18 23:05:38 UTC.
- Actions API: **7,863 total runs**. Latest 100: **72 success, 26 failure, 2 cancelled**; no queued or in-progress run.
- Latest run: [44396134680](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44396134680), Phase 403 SEC Form 144 scheduled capture, completed 2026-11-18 20:56:50 UTC.
- Branch inventory: **317** (100 + 100 + 100 + 17).
- Open PRs: **56**. PR #1 (Phase 29 independent alpha lab) remains draft/open and unmerged.
- No workflow was dispatched, rerun, cancelled, or duplicated.

## 2. Scheduled-event recheck

The latest 100-run inventory contains only four scheduled runs:

| Run | Workflow | UTC start | Result |
|---|---|---:|---|
| [44396134680](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44396134680) | SEC Form 144/144-A | 20:55:44 Nov 18 | Success |
| [44380395679](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44380395679) | SEC Form 4/4-A | 19:25:35 Nov 18 | Success |
| [44302697069](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44302697069) | SEC Form 144/144-A | 12:18:41 Nov 18 | Failure before live capture |
| [44232546204](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44232546204) | CFTC TFF | 03:44:45 Nov 18 | Success |

No scheduled Phase 469 FINRA Reg SHO run appears.

### Windows elapsed without a corresponding run

- **SEC Form 4/4-A** — existing cron `17 * * * 1-5` UTC. After the 19:25:35 run, the 20:17, 21:17, 22:17, 23:17 and 00:17 windows have no corresponding run in the latest inventory.
- **SEC Form 144/144-A** — existing cron `47 * * * *` UTC. After the 20:55:44 run, the 21:47, 22:47 and 23:47 windows have no corresponding run. The 00:47 window had not occurred at cutoff.
- **CFTC TFF** — existing cron `25 22 * * 1-5` UTC. The 22:25 Nov 18 window has no corresponding run.
- **FINRA Reg SHO** — existing cron `30 22,23 * * 1-5` UTC. Neither the 22:30 nor 23:30 Nov 18 window has a corresponding run.

This is now a cross-source gap extending beyond the Phase 491 cutoff. The available GitHub read interface does not expose the workflow administrative enabled/disabled state; an absent scheduled run is not proof that a workflow is disabled. Do not change crons or manually dispatch merely to fill a missed slot. Recheck the next existing windows and inspect any new run before acting.

## 3. Verified jobs, logs and artifacts

### SEC Form 144 — run 44396134680
- Jobs `offline-regression` and `live-capture`: both successful.
- Offline regression: 40/40 tests.
- Artifact [14470455938](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44396134680/artifacts/14470455938), 2,084 bytes, unexpired at audit.
- Poll: 20:56:07–20:56:30 UTC.
- 51 unique new accessions (50 Form 144, 1 Form 144/A), 52 feed entries, one cross-feed overlap; both prior feed watermarks found; 51/51 XML and acceptance reconciliations.
- Persisted state: 11 complete polls, 247 canonical event rows, zero partial polls.
- The 51 observations are bounded metadata only. Public availability is not certified, historical F80 membership is not verified, and signal-eligible count remains zero. Form 144 is a proposed-sale notice, not proof of execution.

### SEC Form 4/4-A — run 44380395679
- Jobs `offline-regression` and `live-capture`: both successful.
- Offline regression: 37/37 tests.
- Artifact [14463211992](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44380395679/artifacts/14463211992), 680 bytes, unexpired at audit.
- Poll: 19:26:00–19:26:08 UTC.
- Ledger: 35 unique accessions (10 Form 4, 25 Form 4/A), all from the initial baseline with no lower interval bound.
- Current `state.json` still points to run 44380395679 and 19:26:08 UTC. No bounded or signal-eligible Form 4 observations exist.

### CFTC TFF — run 44232546204
- Job `prospective-capture`: successful.
- Artifact [14395926632](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44232546204/artifacts/14395926632), 1,148 bytes, unexpired at audit.
- Persisted state still has last capture 03:44:57 UTC Nov 18, latest report date 2026-11-10 for four contract codes, and 3,035 historical warm-up rows.
- Historical availability remains uncertified; the four contract rows from one report date are not four independent weekly observations. No signal is eligible.

### FINRA Reg SHO — Phase 469
- `research/data/finra_regsho_daily_first_seen/state.json` is absent (404 on main).
- No scheduled run or artifact appears in the latest 100-run inventory.
- The existing collector parses the daily file in memory and commits file-level hashes, timestamps, row counts and schema metadata, not raw daily market data. This matches the Phase 467/469 privacy design; any later research expansion must re-download the exact file and require a SHA-256 match to the first-seen manifest. No manifest exists yet.

## 4. Independent-alpha line: no duplicate run

PR [#1 — Phase 29 independent alpha lab](https://github.com/jafelix81/NuevaEstrategia/pull/1) remains open/draft, based on a stale branch and last executed on 2026-10-24 ([run 40105752275](https://github.com/jafelix81/NuevaEstrategia/actions/runs/40105752275)).

Phase 480 already adjudicated its selected MOM120 result as `MOM120_BASELINE_RECONFIRMATION_NOT_INCREMENTAL`:
- MOM120 overlaps the existing R100/R120/R140/R160 long-momentum family.
- The 20-session validation spread was only +0.12%; partial IC was -0.0005.
- The 60-session final-OOS block-bootstrap interval included zero.
- The recorded 10 bps cost was metadata only and was not applied.
- No matched F80 portfolio, identical-exposure/turnover comparison, or LOO was run.
- Yahoo data did not establish a survivorship-free PIT universe; QQQ was removed from the 335 configured names, leaving 334 candidates.

Do not rerun the same ten-factor selection or promote MOM120. Any re-entry must be a genuinely distinct preregistered hypothesis and wait until the effective-dated universe, total-return/delisting history and exact F80 score are available for a matched-cost comparison.

## 5. Research disposition

| Source / line | Current state | Action |
|---|---|---|
| SEC Form 4/4-A | 35 initial-baseline metadata rows; no second interval | Preserve; wait for next scheduled poll |
| SEC Form 144/144-A | 247 event rows; latest 51 bounded metadata observations | Preserve; no execution inference |
| SEC 13D/G | Issuer/filer identity and timestamp issues remain | Keep panel quarantined; use existing Phase 350/identity lineage |
| FINRA Reg SHO | No first-seen ledger | Wait for existing schedule; no Phase 20B/C promotion |
| FINRA short interest / ATS | Separate historical-vintage and credential/coverage gates | Continue existing stacked PRs; do not conflate with daily short volume |
| CFTC TFF | 3,035-row warm-up; latest report Nov 10; PIT not certified | Continue existing capture only |
| Cboe / OPRA options | Existing Phase 231/352–373 work; rights and PIT gates remain | No duplicate sample download or data purchase |
| Phase 29 independent alpha | MOM120 baseline-family confirmation only | No rerun of the same selection |

No new market, options, SEC transaction, FINRA or CFTC data were acquired. No backtest, event study, forward-return, OOS, bootstrap, LOO or holdout test was run.

## 6. Frozen strategy

`F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen:
- universe and parameters unchanged;
- no holding-period restriction added;
- capital, exposure and costs unchanged;
- holdout and production unchanged;
- no new signal admitted.

**Conclusion:** the prospective-data bottleneck has persisted across SEC Form 4, SEC Form 144, CFTC and FINRA scheduled windows. Existing SEC baselines are intact; Form 144 has bounded metadata but no signal eligibility; Form 4 still lacks a second interval; CFTC remains warm-up only; FINRA has no ledger. The correct response is to preserve the current state, recheck the next scheduled slots, and avoid manual/duplicate captures or unsupported alpha claims.
