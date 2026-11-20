# Smart Money Research — state addendum (2026-11-20, Phase 512)

## Phase 512 — CFTC historical availability falsification

- Replayed the date-only artifact from Phase 380 run 43499455469 / artifact 14074090576 (ZIP SHA-256 `f74850aed35d7ed885f33de892895d6bbc755edbd7d4546340427d28468ceb9b`).
- Of 851 post-launch TFF report dates, 846 archive pages were retrieved. After the original weak checks, 843 pages passed (exact heading and archive Updated >= report date).
- A stronger comparison against the CFTC's normal Friday 3:30 p.m. ET publication rule and its official historical announcements found six dates whose archive Updated date precedes the normal/known publication date: 2012-07-03, 2012-09-04, 2015-06-16, 2018-12-18, 2021-03-23 and 2021-05-04.
- One additional 2014-12-30 / Updated 2015-01-03 row is left unresolved and excluded from the six-count.
- Disposition: archive Updated is not a safe global PIT upper bound. Historical CFTC TFF feature/backtest use remains blocked until report-level publication dates are independently reconstructed. Prospective first-receipt capture remains the strict PIT path.
- Report: [Phase 512](PHASE512_CFTC_UPDATED_DATE_PUBLICATION_CONFLICT_AUDIT_2026-11-20.md) · [summary](PHASE512_CFTC_UPDATED_DATE_PUBLICATION_CONFLICT_AUDIT_SUMMARY_2026-11-20.json).

## Operational status — SEC Form 4 / Form 144 parser validation

- Phase 509 and Phase 510 parser code is merged on main, but neither parser has a post-merge live validation in the persisted state.
- Phase 403 state still points to run 44614323236 (2026-11-19 21:00:36 UTC); `sale_details.csv` is absent.
- Phase 476 state still points to run 44598981676 (2026-11-19 19:31:20 UTC); `transaction_details.csv` is absent.
- Issue [#136](https://github.com/jafelix81/NuevaEstrategia/issues/136) was reopened to request a human check of both workflows' enabled state and latest scheduled attempts. The connected GitHub read surface does not expose the repository-wide Actions run list or workflow enabled state, so missing persisted state cannot distinguish disabled, delayed, queued or failed attempts.
- No manual dispatch/rerun, workflow/cron change, credential change or data mutation was made.

## Other candidate status

- OptionMetrics IvyDB Implied Dividend remains a conditional vendor candidate; no purchase, trial or license acceptance. Vendor-reported alpha t-statistic 1.48 is not conventionally significant and is not independent validation.
- SEC Form 4 / Form 144 structured ledgers remain unvalidated live until the next successful scheduled captures.
- FINRA Short Interest still requires authorized credentials and a successful asynchronous completeness/reconciliation pilot.
- FINRA Reg SHO still requires a real post-Phase-495 capture.
- CFTC TFF remains a broad-market positioning/crowding hypothesis, not stock-specific smart-money identity.

## Strategy controls

- `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen.
- No new signal admitted; no new return/backtest/OOS/bootstrap/LOO/holdout test.
- No change to universe, parameters, exposure, costs, holding period, capital or production.
