# Phase 663 — Actions evidence reconciliation, FINRA status correction, and Form 4 audit integration

**Audit cutoff:** 2026-11-27 12:13 UTC  
**Main after integration:** `0dee2a2264f46a376acd6cf14542faf471973b68`  
**Disposition:** repository/evidence reconciliation only. No new market signal or alpha test.

## Executive result

Three previously validated Form 4 research PRs were safely integrated into `main` after rechecking their diffs, tests, jobs and artifacts:

- Phase 658 / PR #248 → `597909f2265628011fa0d2708809ee78957c7b31`
- Phase 659 / PR #249 → `84820fbaeb5506c542f1f5385f212263e4547c78`
- Phase 660 / PR #250 → `0dee2a2264f46a376acd6cf14542faf471973b68`

All three PRs were additive audit/report/test changes; their diffs added six files each and deleted no existing files. They were not production strategy changes. Their PR validations and artifacts were successful (details below).

A raw-log reconciliation also corrects an earlier FINRA description: run `45939887443` does **not** show an HTTP 403. Its persisted summary reports seven HTTP 200 files, one `not_available`, and zero HTTP errors. The prior “one 403” characterization is unsupported and should be treated as a documentation error. The unavailable file's HTTP status is not established by the inspected summary; do not infer it.

## 1. FINRA run 45939887443 — raw log result

Live-capture job: `140311565034`  
Artifact: [15172510181](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45939887443/artifacts/15172510181)  
Artifact ZIP SHA-256: `565b4d530807f14cfdf11bc60318a7f9905109176719baf657edfd1d51bf83e0`

The job log records eight requested trade dates (2026-11-26, 25, 24, 23, 20, 19, 18 and 17 November) and these counts:

| Metric | Result |
|---|---:|
| HTTP 200 | 7 |
| HTTP errors | 0 |
| Not available | 1 |
| Valid files | 7 |
| Partial files | 7 |
| Bootstrap files | 7 |
| Duplicate diagnostic files | 7 |
| Duplicate symbol groups | 14 |
| Extra duplicate rows | 14 |
| Quarantined row occurrences | 28 |
| First-seen / late-first-seen | 0 / 0 |
| Research-observation eligible | 0 |
| Signal eligible | 0 |

The one `not_available` result is not evidence of a 403. The seven returned files were all bootstrap observations, and duplicate-symbol quarantine remained active. The 335-symbol filter is a static reference, not historical F80 membership. No volume-bearing eligible observation exists yet.

## 2. Form 4 natural capture 45976055356

Both offline and live-capture jobs completed successfully. Artifact [15186742638](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45976055356/artifacts/15186742638), 5,887 bytes.

The live log reports:
- 0 new accessions and 0 new canonical event rows;
- 48 structured transaction-detail rows appended across 10 previously known accessions;
- 65 transaction-linked footnote references and 60 additional footnote references;
- 10 filing-level owner rows appended;
- 16 Form 144 proposed-sale crosswalk matches across 15 Form 4 accessions;
- 2 unresolved Form 144 acceptance-clock rows;
- 0 research-observation-eligible and 0 signal-eligible rows.

These are enrichment/backfill rows, not new economic events.

## 3. Integrated Form 4 audits and their validation

| Phase / PR | Actions run | Result | Artifact |
|---|---:|---|---|
| 658 / #248 | [45951568842](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45951568842) | Offline regression successful; 7/7 tests | [15177630455](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45951568842/artifacts/15177630455) |
| 659 / #249 | [45958047426](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45958047426) | Offline regression successful; 6/6 tests | [15179597528](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45958047426/artifacts/15179597528) |
| 660 / #250 | [45977030482](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45977030482) | Offline regression and immutable-summary comparison successful; 6/6 tests | [15188150476](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45977030482/artifacts/15188150476) |

The merge commits are:
- [Phase 658](https://github.com/jafelix81/NuevaEstrategia/commit/597909f2265628011fa0d2708809ee78957c7b31)
- [Phase 659](https://github.com/jafelix81/NuevaEstrategia/commit/84820fbaeb5506c542f1f5385f212263e4547c78)
- [Phase 660](https://github.com/jafelix81/NuevaEstrategia/commit/0dee2a2264f46a376acd6cf14542faf471973b68)

Phase 658 retains the source-level SHMD chronology/price anomaly as quarantined, plus the amendment-lineage diagnostics. Phase 659 resolves two original Form 4/A accession links without creating new economic events. Phase 660's reproducible code-P census remains descriptive: 89 P rows / 59 accessions, only 3 accessions and 11 rows in the static 335-symbol reference (UPST and TEAM), with zero eligible rows and no proof of historical F80 membership or open-market venue.

## 4. Phase 661 / 662 live gates

- Phase 661 PR validation [45978861267](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45978861267): offline tests successful (65/65); live capture skipped because this was a PR event. No production FINRA volume panel has yet been populated by a post-merge natural capture.
- Phase 662 PR validation [45988359829](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45988359829): offline regression successful (34/34); live SEC sample skipped by design. Phase 616 remains manual-dispatch-only with `run_live_sample=true`; no live 13D/G request was made in this audit.

The GitHub connector exposes lookup of known run jobs, logs and artifacts, but not a repository-wide Actions-run listing. The commit-associated run lookup for the latest merge commit returned no PR-triggered runs; that is not proof that every scheduled workflow is idle. No workflow was dispatched or duplicated.

## 5. Branch and PR state

The phase-specific branches for 658, 659, 660, 661 and 662 still appear in branch search; the first three are now merged and their refs were left intact. The open-PR search still shows older stacked draft work, including the SEC 13F sequence/clock chain. Those unrelated branches were not merged or retargeted because their dependency order and historical PIT gates need separate review.

## 6. Research disposition and controls

- FINRA short-volume panel: no eligible first-seen observation yet.
- Form 4: no new canonical events in the latest natural capture; no signal-eligible row.
- Form 4 code-P overlap: UPST remains one issuer-level descriptive cluster; TEAM remains a planned-trading control. No event study is justified by the current sample.
- SEC 13D/G: the 44-header sample remains a manual live gate.
- No prices or forward returns inspected in this phase; no event study, OOS, bootstrap, LOO or holdout test.
- `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen.
- No production, universe, capital, exposure, cost, parameter or holding-period change.
- No vendor contact, quote request or data purchase; data budget remains USD 0.
