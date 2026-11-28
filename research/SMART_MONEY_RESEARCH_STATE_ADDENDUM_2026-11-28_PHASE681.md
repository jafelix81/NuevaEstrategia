# Smart Money Research — state addendum (Phase 681)

**Updated:** 2026-11-28 08:54 UTC  
**Main HEAD:** `5a1e01e3aea498cc52576007c8f36a99bfba57f1`.

## Phase 681 — Cross-source scheduled-capture latency and PIT clock audit

- Inspected the latest 100 Actions runs, explicit `in_progress` and `queued` status filters (both zero), five source workflows, recent jobs/logs/artifacts, relevant branches/PRs and current source-state files.
- Documented configured-cron-to-observed-start latency for Form 144, Form 4, 13F, FINRA Reg SHO and CFTC TFF.
- The latest three FINRA scheduled runs started 4h35m–5h55m after one of the two configured daily slots; the latest three CFTC runs started 5h34m–5h55m after the configured weekday slot. SEC capture workflows show variable delays, including one Form 4 run 3h27m after the last weekday slot.
- Exact intended cron slot is not exposed in each run record; these are nearest-prior-slot diagnostics, not exact queue-latency measurements. Do not infer the source's public-release time from cron or run start.
- No cron changes, manual dispatches, reruns, cancellations, duplicate collectors, data purchases or vendor contacts.

Full report: [Phase 681 cross-source capture latency and PIT clock audit](PHASE681_CROSS_SOURCE_SCHEDULED_CAPTURE_LATENCY_AND_PIT_CLOCK_AUDIT_2026-11-28.md).

## Source state at this checkpoint

- **Form 144:** 1,104 event accessions; 976 accessions with structured details; 6,360 detail rows; 128 pending. Latest run 46110032075 passed both jobs and 103/103 tests. 52 feed rows are poll observations, not new economic events. Two Form 144 acceptance clocks remain unresolved; zero signal-eligible crosswalk matches.
- **Form 4:** latest run 46099559273 passed both jobs; 17 proposed-sale crosswalk rows across 16 Form 4 accessions; nine multi-owner accessions quarantined; zero signal-eligible matches.
- **FINRA Reg SHO:** 327 symbol rows for one prospective trade date (2026-11-27), 335-name frozen universe; seven earlier dates are bootstrap-only. Raw payload not retained; 0 signal-eligible rows.
- **CFTC TFF:** no new report/revision; 3,043 historical rows remain, with historical PIT restrictions.
- **13F:** four new accession observations in metadata only; holdings not downloaded.

## Outstanding gates

- SEC 13D/G Phase 616 still requires the existing manual `workflow_dispatch` with `run_live_sample=true`. No live sample is claimed.
- 13F PR #262 and PR #230 remain draft in their dependency chain; do not merge out of order. N-PORT PR #17 remains open on its separate Phase 312 branch.
- FINRA Reg SHO still needs a longer prospective sample and an approved PIT price/security master. Do not treat the 12-month Query API as a multi-year history source.
- Options/OPRA remains blocked by historical rights/vintage requirements; no paid source authorized.

## Strategy controls

- Signals promoted: **0**.
- Incremental alpha demonstrated: **none**.
- New OOS/bootstrap/LOO result: **0**.
- `F80_TOP20_PARTIAL50_BASELINE_C20`: **frozen**.
- No production, universe, exposure, cost, parameter or holding-period changes.
- Data spend: **USD 0**.
