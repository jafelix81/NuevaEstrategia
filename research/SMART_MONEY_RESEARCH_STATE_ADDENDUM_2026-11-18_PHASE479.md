# Smart Money Research state addendum — Phase 479 (2026-11-18)

- Latest preflight: main `793af54daa99e5f132199e1151b3823c0ccf5645`; 7,843 Actions runs; explicit active/queued counts 0/0.
- Scheduled Phase 403 run [44302697069](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44302697069) was observed at 12:18:41 UTC but failed its offline-regression job. The live-capture job was skipped; no SEC request, ledger mutation or artifact occurred.
- Root cause: Phase 464 tests pinned global append-only ledger totals and mutable latest-poll state to the 2026-11-17 snapshot. The later successful Phase 403 capture [44228413864](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44228413864) increased event rows from 106 to 196, acceptance reconciliations from 106 to 196, and complete-poll count from 9 to 10. The original run-scoped Phase 464 metrics remain unchanged.
- Phase 479 changes global row-count assertions to monotonic lower bounds, keeps Phase 464 run-scoped assertions exact, and tests the current poll-state structure/last-successful anchor without freezing mutable run IDs or gap status. No data ledger was modified.
- PR CI is pending. Live capture is intentionally skipped on PRs. After merge, wait for the next existing scheduled Phase 403 run; no manual dispatch or replacement workflow.
- Phase 476 minute-17 scheduled capture remains unverified in the latest Actions inventory. No duplicate was launched.
- No alpha, backtest, OOS, bootstrap, LOO or holdout test. `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen.
- Report: [Phase 479](research/PHASE479_SEC_FORM144_GROWING_LEDGER_REGRESSION_FIX_2026-11-18.md) · [summary](research/PHASE479_SEC_FORM144_GROWING_LEDGER_REGRESSION_FIX_SUMMARY_2026-11-18.json).
