# Smart Money Research state addendum — Phase 565 (2026-11-23)

- Latest natural Form 144 scheduled run: [45085664016](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45085664016), created 23:53:30 UTC (6m30s after the 23:47 cron minute); both jobs succeeded. This is one observed recovery, not proof of uninterrupted hourly delivery.
- Form 144/144-A feeds: 53 observations appended; no new accession/event; both feeds complete with no errors or possible gap.
- Structured-detail backfill parsed 10 existing accessions and appended 82 rows; ledger now 295 accessions / 2,196 rows; 268 remain. Zero parse errors, unresolved accessions or source-hash mismatches.
- 295 filings are research-observation-eligible, but zero are public-availability-certified and zero signal-eligible. No return/alpha/OOS test.
- The Phase 560 10b5-1 artifact is generated before live capture and is stale relative to the post-capture ledger. Draft PR adds a post-capture Phase 549 summary, exact count reconciliation to Phase 516 and a separate artifact; no new collector.
- Actions inventory: 8,070 total; latest 100 = 96 success / 4 failure / 0 active; 372 branches; 72 open PRs.
- PR #204 remains Draft/diverged (11 ahead / 11 behind); SEC_USER_AGENT remains required for bounded FTD validation.
- Phase 20C remains at 328/335 valid histories; no weekend FINRA capture expected.
- No new signal or incremental OOS evidence. `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen.
- Full report: [Phase 565](PHASE565_FORM144_SCHEDULE_RECOVERY_AND_POSTCAPTURE_10B5_ARTIFACT_GATE_2026-11-23.md).
