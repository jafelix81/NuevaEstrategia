# Phase 681 — Cross-source scheduled-capture latency and PIT clock audit

**Audit cutoff:** 2026-11-28 08:49 UTC  
**Main HEAD:** `60307cc245aebb748a1c49a0158e03991574052d`  
**Disposition:** operational timing audit completed; preserve actual first-seen bounds, do not backdate to cron slots, and do not change capture schedules. No signal, alpha or strategy change.

## 1. Repository and Actions preflight

- Repository Actions inventory: 8,408 total runs.
- Explicit status-filtered queries: **0 `in_progress` and 0 `queued`**.
- The latest 100 runs were inspected; the latest five source workflows were checked at run, job, log and artifact level.
- Main HEAD is the Phase 680 state-recording commit above.
- Relevant open PRs remain unchanged: #262 (Phase 675) and #230 (Phase 613) are drafts in the 13F dependency chain; #17 (Phase 313 N-PORT parser correction) remains open against the Phase 312 branch. No dependency was merged or retargeted.
- No workflow was dispatched, rerun, cancelled or duplicated.

## 2. Schedule-to-start latency

Method: compare each observed `created_at/run_started_at` with the latest configured cron slot not later than the observed start. For FINRA, which has two daily slots, the run record does not expose which slot generated the event; both possible slot-relative delays are shown. These are **schedule-latency diagnostics**, not exact GitHub queue-time measurements. A skipped/coalesced earlier slot could make the true delay longer.

### Latest observations

| Source | Configured UTC cron | Run | Observed start UTC | Latest prior slot | Delay |
|---|---|---:|---|---|---:|
| SEC Form 144 | `47 * * * *` | [46110032075](https://github.com/jafelix81/NuevaEstrategia/actions/runs/46110032075) | Nov 28 04:59:36 | Nov 28 04:47 | 12m36s |
| FINRA Reg SHO | `30 22,23 * * 1-5` | [46105917821](https://github.com/jafelix81/NuevaEstrategia/actions/runs/46105917821) | Nov 28 04:05:39 | Nov 27 23:30 / 22:30 | 4h35m39s / 5h35m39s |
| CFTC TFF | `25 22 * * 1-5` | [46105422375](https://github.com/jafelix81/NuevaEstrategia/actions/runs/46105422375) | Nov 28 03:59:39 | Nov 27 22:25 | 5h34m39s |
| SEC Form 4 | `17 * * * 1-5` | [46099559273](https://github.com/jafelix81/NuevaEstrategia/actions/runs/46099559273) | Nov 28 02:44:46 | Nov 27 23:17 | 3h27m46s |
| SEC 13F | `41 * * * 1-5` | [46084129349](https://github.com/jafelix81/NuevaEstrategia/actions/runs/46084129349) | Nov 27 23:44:09 | Nov 27 23:41 | 3m09s |

### Recent-run consistency check

| Source | Additional observed starts | Slot-relative delay |
|---|---|---:|
| Form 144 | Nov 27 22:59:05; Nov 27 14:25:39 | 12m05s; 38m39s |
| FINRA | Nov 27 04:25:48; Nov 26 04:16:05 | 4h55m48s–5h55m48s; 4h46m05s–5h46m05s |
| CFTC | Nov 27 04:19:49; Nov 26 04:12:21 | 5h54m49s; 5h47m21s |
| Form 4 | Nov 27 19:30:02; 09:43:16; 00:38:23; Nov 26 15:23:55 | 13m02s; 26m16s; 21m23s; 6m55s |
| 13F | Nov 27 15:35:54; 05:21:59; Nov 26 23:18:22; 14:29:01 | 54m54s; 40m59s; 37m22s; 48m01s |

**Finding:** the last three observed FINRA and CFTC scheduled runs each started roughly 4.6–5.9 hours after their configured slot(s). SEC capture workflows also show variable latency, including one Form 4 run that began 3h27m after the last weekday slot. Form 144 and Form 4 have additional shorter-delay observations; this is not evidence that every run is delayed by the same amount.

## 3. Point-in-time interpretation

1. A cron expression is not a source-publication timestamp.
2. `created_at/run_started_at` is the workflow start, not the SEC/FINRA/CFTC release time.
3. The collector's own bounded receipt interval and actual source metadata remain the only admissible knowledge-time evidence. Do not substitute a nominal schedule time or backdate an event to its trade/report date.
4. Schedule latency widens the interval in which a source may have become public but was not yet observed. It reduces timing precision; it does **not** authorize look-ahead.
5. Do not move the cron simply to make the displayed delay look smaller. GitHub's scheduled-run latency is outside the collector, and more frequent cron entries do not guarantee a more timely or complete poll.

## 4. Latest source-state reconciliation

- **Form 144:** run 46110032075 passed both jobs and 103/103 regressions. The 52 appended feed rows are polling observations, not new economic events. Ledger: 1,104 accessions, 976 with structured details, 6,360 detail rows, 128 pending; two Form 144 acceptance clocks remain unresolved in the crosswalk; zero signal-eligible matches.
- **Form 4:** run 46099559273 passed both jobs; the live crosswalk contains 17 proposed-sale rows across 16 Form 4 accessions. Two Form 144 acceptance clocks remain unresolved, nine multi-owner accessions are quarantined, and zero matches are signal-eligible.
- **FINRA Reg SHO:** run 46105917821 passed both jobs and 65/65 tests. The committed symbol panel contains 327 rows for one prospective trade date (2026-11-27), against 335 frozen tickers. Seven earlier dates are bootstrap-only. The raw source payload is not retained; every symbol row remains `signal_eligible=false`.
- **CFTC TFF:** run 46105422375 succeeded but produced no new report/revision; 3,043 historical rows remain, with historical PIT limitations unchanged.
- **13F:** run 46084129349 succeeded and observed four new accessions in metadata only. No holdings were downloaded; no new position-level observation or signal was created.

## 5. Research disposition

The timing audit improves the operational map of the collectors but does not create a return observation or a new Smart Money feature.

- Signals promoted: **0**.
- Incremental alpha demonstrated: **none**.
- New OOS, bootstrap or LOO result: **none**.
- No source, feature, universe, parameter, cost, exposure, holding-period or production change.
- `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen.
- No vendor contact, quote, purchase or paid-data use; spend remains USD 0.

## 6. Next gates

1. Keep all event-study clocks anchored to actual first-seen/acceptance evidence and carry the schedule-latency uncertainty into the data-quality flags.
2. Continue prospective FINRA accumulation; do not evaluate returns until there are enough distinct eligible dates and a reviewed PIT price/security master.
3. Keep CFTC as a delayed regime/context candidate until enough prospective reports accumulate.
4. Continue Form 4/Form 144 identity, transaction and acceptance-clock reconciliation; filings and feed polls are not executions.
5. Keep 13F/N-PORT ownership changes contextual until effective-dated security identity, full-universe coverage, amendment lineage and public-vintage controls pass.
6. The existing Phase 616 SEC 13D/G bounded sample still requires its manual `workflow_dispatch` input `run_live_sample=true`; do not create a duplicate crawler or infer a successful live sample from offline PR checks.

**Conclusion:** capture latency is now documented across five source workflows. It is a timing-quality limitation, not evidence for or against a trading signal. All strategy controls remain unchanged.
