# Smart Money Research state addendum — Phase 665

**2026-11-27 15:22 UTC**

- Phase 665 resolves Phase 664's unknown Form 144 formal-plan-date/PIT intersection using an exact accession-level join of the committed `sale_details.csv` and `events.csv` ledgers.
- Source snapshot: `main` at `f875be29d740f7ac8dc861d8dae607e13eb34b44`; capture run [46015828465](https://github.com/jafelix81/NuevaEstrategia/actions/runs/46015828465).
- `sale_details.csv`: 5,651 detail rows / 855 unique accessions. `events.csv`: 1,003 rows / 1,003 unique accessions. All 855 detail accessions match the event ledger on six PIT fields with zero mismatches; 148 event-only accessions still lack structured details.
- The 322 formal plan-date accessions split into 290 bounded research-observation-eligible accessions and 32 initial-baseline accessions with no lower bound. There are 134 distinct plan-adoption dates (320 Form 144 and 2 Form 144/A accessions).
- Exact intersection: 290/322 = 90.06% of the formal-plan-date cohort is research-observation eligible; 32/322 = 9.94% is baseline. The correct share within the 807 research-observation-eligible accessions is 290/807 = 35.94%. The all-structured-detail rate remains 322/855 = 37.66%.
- Fourteen accession-level detail fields were internally consistent; six PIT fields matched across the event and detail ledgers. The 148 event-only accessions remain outside the plan-date denominator until backfill.
- Zero accessions are public-availability-certified and zero are signal-eligible. A bounded first-seen interval is not an exact public-release timestamp; Form 144 remains a proposed-sale notice, not execution confirmation.
- Added a standard-library reproducibility script, fixture tests, and an offline-only PR workflow. No SEC request or live capture is part of Phase 665.
- No return data, event study, alpha, chronological OOS, bootstrap, LOO or holdout was used. No signal promoted. `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen. No vendor contact or purchase; data budget USD 0.

See `research/PHASE665_FORM144_ACCESSION_LEVEL_PIT_PLAN_DATE_JOIN_2026-11-27.md` and the companion JSON summary.
- PR [#254](https://github.com/jafelix81/NuevaEstrategia/pull/254) merged into `main` as `d7e02134a4604063c197758b35c20edd51521d4b`. Validation [run 46025579803](https://github.com/jafelix81/NuevaEstrategia/actions/runs/46025579803) passed **93 tests** and reproduced the committed-ledger join; artifact [15212117265](https://github.com/jafelix81/NuevaEstrategia/actions/runs/46025579803/artifacts/15212117265). Live capture was skipped for the PR event.
- Supplemental Phase 665 backlog audit: among the 148 feed-event accessions without structured details, 26 match the static candidate CIK manifest across 16 issuer names, but none is research-observation eligible or historically verified as an F80 member. Twelve are initial-baseline/no-lower-bound and 14 have possible feed-window gaps; the four bounded pending accessions are non-candidate matches. The 148 records have 502 feed-observation rows. This shows detail backfill alone will not repair the candidate-match PIT gap; see the expanded Phase 665 report/JSON.
