# Smart Money Research state addendum — Phase 491 (2026-11-18)

- Current main at preflight: `e2f2a036d1ba6584045d9dfb4140029651f46d9a`; Phase 491 audit committed as `869b7b1fe1b8795ce3b2c3058bf5399b0728ef14`.
- Actions API: 7,863 total runs; latest 100 inspected; zero in progress/queued in that window. Latest run was SEC Form 144 scheduled capture 44396134680 at 20:55:44 UTC; no run later than its 20:56:50 completion appears at the 23:02 UTC cutoff.
- SEC Form 144 remains at 11 complete polls and 247 canonical event rows. The latest run added 51 bounded metadata observations; 0 public-availability-certified, 0 verified historical F80 members and 0 signal-eligible. Run 44396134680: 40/40 offline tests; artifact 14470455938.
- SEC Form 4/4-A remains at one successful initial baseline: 35 accessions (10 Form 4, 25 Form 4/A), poll 19:26:00–19:26:08 UTC. The state has 0 bounded metadata rows; no later successful scheduled poll appears in the latest 100 Actions runs. Run 44380395679: 37/37 offline tests; artifact 14463211992.
- CFTC TFF state remains last captured at 03:44:57 UTC, with four contract codes on report date 2026-11-10. Baseline manifest has 3,035 historical rows, but historical availability is not certified and rows are not signal-eligible. The configured 22:25 UTC scheduled window is absent from the latest Actions inventory at cutoff.
- FINRA Reg SHO Phase 469 has configured weekday polls at 22:30 and 23:30 UTC. No scheduled run appears in the latest Actions inventory; `research/data/finra_regsho_daily_first_seen` is absent. The 22:30 slot had elapsed; 23:30 was still future. No manual dispatch.
- The absence of later schedule events is not proof that workflows are disabled; GitHub's administrative workflow state is not exposed by the available read interface. Recheck subsequent existing schedule slots; do not duplicate or manually dispatch.
- Branch inventory: 317; open PRs: 56; standalone open issues #9 and #132. Stacked FINRA/CFTC/Cboe/SEC PR chains were preserved.
- Phase 487 remains controlling: FINRA 20B rejected (24/24 replacement RuleScores tied); 20C not promoted; 20A exploratory. SEC 13D/G remains quarantined. Options and CFTC remain conditional on their existing PIT/coverage/licensing gates.
- No new raw market, options, SEC transaction, FINRA or CFTC data; no backtest, event study, forward-return, OOS, bootstrap, LOO or holdout test.
- `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen; no universe, parameter, holding-period, capital, exposure, cost, holdout or production changes; zero new signals admitted.
- Full audit: [Phase 491](PHASE491_CROSS_SOURCE_SCHEDULED_CAPTURE_DELIVERY_AUDIT_2026-11-18.md) · machine-readable summary: [Phase 491 summary](PHASE491_CROSS_SOURCE_SCHEDULED_CAPTURE_DELIVERY_SUMMARY_2026-11-18.json).
