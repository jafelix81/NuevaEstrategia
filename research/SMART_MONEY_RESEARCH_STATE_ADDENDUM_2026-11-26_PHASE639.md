# Smart Money Research State Addendum — Phase 639 (2026-11-26)

## Completed in this branch

- Identified a Form 144 Atom timestamp parser inconsistency: timezone-naive `updated` values were silently interpreted as UTC, unlike the strict Form 4 parser.
- Proposed fail-closed behavior: naive or offset-less timestamps remain raw-only and have no normalized UTC value.
- Added a regression test; PR validation will be offline-only and will not poll SEC.
- Phase 638 remains merged in main; its 82/82 offline regression passed and its live-capture job was skipped.

## Integration blockers discovered

- SEC 13F PR chain #221–230 is internally stacked but stale against current main. Root PR #8 is 21 ahead / 587 behind; final Phase 613 branch is 137 ahead / 587 behind. Do not merge the final stacked PR directly. Rebase/rebuild on current main and rerun all offline gates.
- SEC 13D/G PR #37 is based on an old Phase 347 branch; its Phase 350 branch is 292 ahead / 565 behind main. Rebase/port deliberately before integration.
- The latest full Actions schedule inventory remains the Phase 638 10:53 UTC snapshot: 0 queued / 0 in progress; no post-merge natural Form 4, Form 144 or 13F capture was visible. The available connector cannot read the repository-wide run list or administrative workflow enabled-state; absence of runs is not proof of disabled workflows.

## Source disposition

- Form 4: keep entity-aware capture and transaction/footnote provenance; next natural run must validate Phase 626 duplicate audit after its merge.
- Form 144: 815 headers / 5,443 detail rows; 807 bounded observation-eligible, 8 expected bootstrap rows quarantined, 0 malformed intervals, 0 exact public-availability certifications, 0 signal-eligible.
- SEC 13F: historical schema/manager graph and timestamp feasibility are promising, but current stack is not integrated and F80 security identity remains incomplete.
- SEC 13D/G: 43/44 parent retrieval; 31/42 valid child CUSIPs match; mismatches/missing identity remain quarantined.
- FINRA Reg SHO: keep BCPC/TPC rows in quarantine.
- CFTC TFF: 3,035 archive rows are not PIT; only eight prospective observations across two report dates; too few observations for predictive tests.
- Options / microstructure: feasibility only; no paid data, vendor contact or quote request; budget USD 0.

## Model controls

`F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen. No incremental alpha, valid OOS, bootstrap or LOO evidence. No universe, exposure, costs, capital, parameters, holdout or holding-period policy changes.
