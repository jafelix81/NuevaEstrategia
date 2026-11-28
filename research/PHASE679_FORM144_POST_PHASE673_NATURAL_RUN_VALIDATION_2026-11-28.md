# Phase 679 — SEC Form 144 post-Phase 673 natural-run validation

**Audit cutoff:** 2026-11-28 05:00 UTC  
**Base main before capture:** `7c528b5960ab11ff5ba91dbd4722e2cf42d5ccb4`  
**Main HEAD after capture:** `3f7a6cc4968b372e7629d91ce4b79682fa54f12b`  
**Disposition:** first natural scheduled run after Phase 673 validated the integrated post-capture joins; no new Form 144 events or signals were admitted.

## 1. Preflight and run

- Inspected the latest 30 Actions runs, current jobs/artifacts, open PRs, branch inventory and research files. The latest 30 runs had no queued or in-progress jobs; no duplicate workflow was dispatched.
- Phase 673 PR [#261](https://github.com/jafelix81/NuevaEstrategia/pull/261) was confirmed merged to `main` at 2026-11-28 00:38:02 UTC (merge commit `221f3aa9433fc66837c2093e2db685a9845d56d1`).
- The first subsequent natural scheduled Phase 403 run was [46110032075](https://github.com/jafelix81/NuevaEstrategia/actions/runs/46110032075), created 04:59:36 UTC and completed 05:00:10 UTC.
- Both jobs passed: offline regression and live capture. The offline suite passed **103/103 tests**.
- The live job executed the integrated post-capture Phase 665 accession-level PIT/plan-date join, Phase 560/565 10b5-1 refreshes, Phase 516 ledger-quality audit, and Phase 525 Form 144/Form 4 crosswalk refresh.
- The run committed the append-only poll state to `main` as `3f7a6cc4968b372e7629d91ce4b79682fa54f12b`.

## 2. Feed poll — no new notices

Both SEC feeds completed successfully:

| Feed | Entries in current page | New accessions | Pagination |
|---|---:|---:|---|
| Form 144 | 50 | 0 | Complete; previous latest accession found |
| Form 144/A | 2 | 0 | Complete; previous latest accession found |

- 52 feed-observation rows were appended; these are poll observations, not 52 new filings or economic events.
- `new_event_count=0`, `new_feed_entry_count=0`, `new_xml_resolved_count=0`, and `new_candidate_issuer_matches=0`.
- Both feeds passed continuity checks; `possible_feed_window_gap=false`.
- The bounded poll interval ran from 2026-11-27 22:59:22 UTC to 2026-11-28 04:59:56 UTC. The upper bound is the collector's receipt time, not the exact public-release timestamp.
- The current run admitted zero new research observations and zero signals.

## 3. Structured-detail backfill and current ledger

The bounded backfill parsed 10 previously known accessions and appended 46 structured detail rows:

- Parse errors: **0**
- Unresolved accessions: **0**
- Source-hash mismatches: **0**
- Remaining accessions in this backfill queue: **128**

The post-capture ledger now reconciles to:

| Measure | Result |
|---|---:|
| Event-ledger rows / unique accessions | 1,104 / 1,104 |
| Structured-detail accessions | 976 |
| Structured-detail rows | 6,360 |
| Structured accessions without an event | 0 |
| Event accessions still without structured details | 128 |
| Parse-error rows | 0 |
| Issuer CIKs represented in structured details | 496 |

The append-only source files are represented by these SHA-256 values in the run audit:

- `events.csv`: `bf85616e964e81cda377c44e1c4211afdcc187461e9c09d6e4278765f23fc439`
- `sale_details.csv`: `0f49b33322b35776240f4b754b9c7caecc8427802c32e57f98c2a257d25047d6`

## 4. PIT, plan-date and cross-source reconciliation

The integrated Phase 665 join passed and reported:

| Measure | Result |
|---|---:|
| Research-observation-eligible accessions | 908 |
| Initial-baseline accessions without a lower bound | 68 |
| Formal plan-date accessions | 389 |
| Distinct formal plan-adoption dates | 146 |
| Plan-date accessions also research-observation-eligible | 352 |
| Public-availability-certified accessions | **0** |
| Signal-eligible accessions | **0** |

The current Form 144/Form 4 descriptive crosswalk contains 17 proposed-sale matches across 16 Form 4 accessions. It still quarantines three ambiguous transaction-reuse cases and nine multi-owner accessions; two Form 144 acceptance clocks remain unresolved. **Signal-eligible matches remain zero.**

Important distinctions remain in force:
- A Form 144 is a proposed-sale notice, not proof of execution.
- First-seen poll bounds are not exact public-release times.
- A formal 10b5-1 adoption date does not prove that a particular sale was executed under that plan.
- Reporting-owner identity at filing grain does not establish transaction-line ownership or discretionary intent.

## 5. Artifacts and reproducibility

The run produced four unexpired artifacts:

- [Phase 403 first-seen poll](https://github.com/jafelix81/NuevaEstrategia/actions/runs/46110032075/artifacts/15249780062)
- [Phase 665 accession-level PIT join](https://github.com/jafelix81/NuevaEstrategia/actions/runs/46110032075/artifacts/15249651063)
- [Phase 560 current 10b5-1 refresh](https://github.com/jafelix81/NuevaEstrategia/actions/runs/46110032075/artifacts/15249551296)
- [Phase 565 post-capture 10b5-1 audit](https://github.com/jafelix81/NuevaEstrategia/actions/runs/46110032075/artifacts/15248998781)

## 6. Research decision and next gates

**Phase 673's natural-run integration gate is now closed:** the scheduled workflow executed the new post-capture join and crosswalk on the updated mainline, rather than merely passing PR-only synthetic validation.

This is an ingestion/reconciliation milestone, not a predictive result. It does not establish that Form 144 notices predict returns or reveal informed selling.

Next:
1. Continue the bounded structured-detail backfill; 128 event accessions remain without structured details.
2. Keep public-availability certification, issuer/security identity, transaction semantics and historical F80 membership as separate gates.
3. Run the preregistered 44-accession SEC 13D/G global-index sample only through the existing Phase 616 manual workflow dispatch with `run_live_sample=true`. The shared SEC User-Agent fallback was merged in PR #252; do not create another crawler or request a new credential.
4. Continue prospective FINRA, Form 4, CFTC and 13F capture without treating poll observations as signals.

No return labels, event study, alpha, OOS, bootstrap, LOO or holdout test was run. No data were purchased, no vendor contacted, and no production, universe, parameter, capital, exposure, cost or holding-period rule changed.

`F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen.
