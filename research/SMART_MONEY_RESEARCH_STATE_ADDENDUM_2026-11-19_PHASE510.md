# Smart Money Research state addendum — Phase 510 (2026-11-19)

## Preflight
- Main HEAD reviewed: 44b2560cd931b52c474cd05f939fe440ae484f0d.
- Latest Actions run before changes: [44629534273](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44629534273), PR regression success; offline-regression passed 59 tests and live-capture was skipped by design.
- Latest scheduled Form 144 run: [44614323236](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44614323236), successful on pre-Phase-509 main; artifact [14573957396](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44614323236/artifacts/14573957396). It predates the Phase 509 parser merge.
- Latest scheduled Form 4 run: [44598981676](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44598981676), successful; artifact [14566842676](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44598981676/artifacts/14566842676). It remains metadata-only.
- Latest FINRA Reg SHO run: [44453548570](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44453548570), successful transport, zero eligible first-seen events; it does not establish a post-Phase-495 parser validation.
- Latest CFTC TFF run: [44453066854](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44453066854).
- Actions API inventory: 7,912 total; latest 100 inspected; no active/queued runs. No scheduled Phase 403 or Phase 476 run after the Phase 509 merge was visible at the cutoff. Treat this as a schedule-delivery gap, not proof that workflows are disabled. No manual dispatch, rerun or duplicate poll was started.
- Open PR count at preflight: 57; Phase 510 PR #163 was then created. PR #159 remains draft for FINRA Short Interest credentials. PR #1 remains draft and its MOM120 replacement hypothesis is not promoted under Phases 480/499. The first 330 branch names were inspected; the Phase 509 branch is present and no conflicting Phase 510 branch existed before creation.

## Phase 510 changes
- Added phase510_form4_structured_transaction_ledger.py and 11 synthetic regression tests; combined Phase 476 + Phase 510 CI passed 50/50 in [run 44642337001](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44642337001).
- PR #163 is open and mergeable; live-capture was skipped by design. The parser-version-aware reprocessing test and strict timestamp validation pass.
- Integrated the detail backfill into the existing Phase 476 scheduled job. No new cron or second SEC poller.
- Newest-first backfill, max 10 accession documents per scheduled run, only when the source event has a bounded metadata interval.
- Separate filing-header, non-derivative and derivative rows; preserves first-seen interval and a separate XML retrieval clock.
- Form 4/A remains an amendment information arrival; P/A remains open-market-or-private, not confirmed exchange execution.
- No owner CIK is attached to transaction rows; multi-owner rows are quarantined.
- Raw XML and full footnote text are not persisted.
- All structured rows remain non-signal and not public-availability-certified.

## Existing quantitative dispositions
- Phase 487: FINRA 20B continuous replacement killed for zero-variance ties; 20C adaptive replacement killed for unstable, small pseudo-OOS; 20A residual IC exploratory only after multiplicity correction.
- Phase 499: MOM120 standalone replacement rejected; mean daily excess about 0.71 bps, block-bootstrap intervals include zero, only eight OOS rebalance dates, static universe and no delisted terminal-return coverage.
- Phase 386: N-PORT quarter-over-quarter share-growth killed as specified; 13F parked pending PIT identity/coverage.
- Form 4 Phase 497: 81 structural-completeness rows are not a discretionary/open-market cohort; 2/81 explicit open-market footnote keyword count came from an incomplete 636/637 repeat and remains provisional.
- No Smart Money signal has been admitted.

## Controls
- No forward-return/event study/backtest/OOS/bootstrap/LOO/holdout test in Phase 510.
- No new signal admitted.
- F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen: universe, parameters, holding period, capital, exposure, costs, holdout and production unchanged.
