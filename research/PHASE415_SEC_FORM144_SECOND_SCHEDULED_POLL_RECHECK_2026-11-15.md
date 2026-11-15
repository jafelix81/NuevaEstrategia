# Phase 415 — SEC Form 144 second scheduled-poll recheck

**Audit time:** 2026-11-15 11:42 UTC  
**Disposition:** A second genuine SEC Form 144 scheduled poll completed successfully. It found no new accessions, events or candidate matches. This improves evidence that the schedule trigger is enabled, but does not establish reliable hourly delivery. No manual poll, duplicate workflow, cron edit or signal test was initiated.

## 1. Repository and Actions preflight

- Main HEAD before this note: `b114543557ce43846adfe4c230f46c20c060cfe4`, created by the successful capture run's append-only state/ledger commit.
- Inspected the latest 100 Actions runs, first 100 branch records, all 56 open PRs returned by the repository API, 63 workflow files, the central research state, the SEC capture workflow and the CFTC capture workflow.
- No workflow was queued, waiting or in progress at the audit time.
- Open PR topology remains mostly draft/stacked. PR #57 (Phase 381 price-provider fallback), #61 (Phase 385 FINRA clock census), #48 (Cboe source ranking) and #37 (SEC 13D/G parent retrieval) remain drafts on their existing bases. No PR was merged, rebased or duplicated.

## 2. Run 43709012759 — verified scheduled capture

- Event: `schedule`; branch: `main`; run URL: https://github.com/jafelix81/NuevaEstrategia/actions/runs/43709012759
- Run created: 2026-11-15 11:27:32 UTC; capture started 11:27:46 UTC and completed 11:28:22 UTC.
- Both jobs succeeded: `offline-regression` and `live-capture`.
- Offline regression: 15/15 tests passed.
- Live capture and append-only commit completed successfully. Mainline capture commit: `b114543557ce43846adfe4c230f46c20c060cfe4`.
- Artifact: [14159294388](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43709012759/artifacts/14159294388), 1,187 bytes, SHA-256 `29f3d2b6ddcd78b7a7f46fdf86a534beedcc4c78f2e965da4a187a514b80c442`.

Artifact disposition: `POLL_COMPLETE_NO_NEW_ACCESSIONS`.

- Form 144 feed: 50 entries; Form 144/A feed: 5 entries; 55 per-feed observations appended.
- Zero new accessions, event rows, candidate issuer matches, XML resolutions or eligible observations.
- Both prior latest accessions remained present; neither feed showed a possible 50-entry-window gap.
- The observation ledger now contains 110 rows: 55 for schedule run 43670461605 and 55 for schedule run 43709012759.
- The event ledger remains 52 unique baseline rows (47 Form 144 and 5 Form 144/A); all 52 were first seen in bootstrap run 43639113589 and all remain research-/signal-ineligible.
- Persistent state now reports `poll_count=4`, per-feed poll count 4, last successful mode `schedule`, run 43709012759 and receipt `2026-11-15T11:28:22Z`. The four-poll state counter includes bootstrap/poll history; only the two later scheduled polls appear as 55-row batches in the feed-observation ledger.
- First-seen remains a poll-receipt upper bound, not exact public-availability time. Public-availability certification, same-day use, intraday use and signal eligibility remain false.

## 3. Schedule-delivery interpretation

The two successful Phase 403 schedule runs in the latest 100-run page are 43670461605 (created 03:01:47 UTC; receipt 03:02:02 UTC) and 43709012759 (created 11:27:32 UTC; receipt 11:28:22 UTC). Their receipt interval is 8h26m20s. Both are genuine schedule events, but the observed run times do not match the configured minute `:37`, and the interval does not demonstrate hourly delivery. Treat schedule execution as best-effort; do not manually dispatch or create a parallel poll.

## 4. CFTC TFF next capture

- Phase 384 remains on its existing weekday `22:15 UTC` schedule; no new schedule capture occurred during this Sunday audit.
- The official CFTC 2026 release calendar currently lists **Monday 2026-11-16** as a delayed release date at 3:30 p.m. Eastern (20:30 UTC). The existing Phase 384 poll is therefore expected at 22:15 UTC, 105 minutes later. Official schedule: https://www.cftc.gov/MarketReports/CommitmentsofTraders/ReleaseSchedule/index.htm
- Do not infer that the announced semiweekly cadence is already live for TFF. Keep Phase 387 weekly semantics until actual TFF report dates and first-receipt timestamps demonstrate the new cadence.

## 5. Research and strategy controls

- FINRA Phase 20C remains blocked at 328/329 valid price histories; unresolved names remain AVB, EA, EQR, LPRO, ROKU, WBD and WBS. Massive remains a conditional provider candidate only; no subscription, key, API request, vendor contact or data purchase occurred.
- Options, SEC Form 4, SEC 13D/G, FINRA short-flow/short-interest and off-exchange research remain at their existing feasibility/identity/PIT gates. No source or signal was admitted.
- No forward-return, alpha, OOS, bootstrap, LOO or holdout test was run.
- `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen. Holdout, universe, parameters, capital, exposure and production remain unchanged.

## Next checks

1. Let the existing SEC workflow continue; inspect the next actual scheduled run and its feed-window continuity. Do not duplicate the capture.
2. Inspect the first Phase 384 scheduled capture after the CFTC's 2026-11-16 delayed release; preserve the actual receipt time and raw hashes.
3. Resume Phase 20C only after an authorized/reproducible price panel passes the complete 329-history gate and the corporate-action/identity checks.
