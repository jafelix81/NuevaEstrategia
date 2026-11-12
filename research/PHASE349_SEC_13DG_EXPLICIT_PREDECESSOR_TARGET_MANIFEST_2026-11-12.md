# Phase 349 — SEC 13D/G explicit predecessor target manifest

**Date:** 2026-11-12 UTC  
**Status:** `COMPLETE_TARGET_MANIFEST_ONLY`  
**Mode:** Offline replay from immutable Phase 84 and Phase 93 artifacts. No new SEC requests.

## 1. Reproducible target set

The 200-filing Phase 93 lineage sample contains 44 explicit `previousAccessionNumber` references whose parent accessions are outside the 600-row Phase 84 header sample. Phase 349 constructs a deterministic retrieval manifest for those references; it does not retrieve or validate the parent documents.

| Measure | Result |
|---|---:|
| Explicit out-of-sample parent references | 44 |
| Unique parent accessions | 44 |
| Unique subject issuer CIKs | 41 |
| Form family | 25 13D / 19 13G |
| Unique parent archive-path CIKs | 31 |
| Parent accession prefix differs from child accession prefix | 9 |
| Child CUSIP valid and nonzero | 43 |
| Child CUSIP all-zero sentinel | 1 |
| Explicit reporting-person CIK present | 25/44 |
| Reporting-person names present | 44/44 |
| Reporting-person rows represented | 128 |

The parent accession prefix is retained only as the SEC archive-path component needed to retrieve a filing. It is not treated as the subject issuer, reporting person, beneficial owner, or economic group. The child subject CIK, child filer CIK, child accession-path CIK, and parent archive-path CIK remain separate fields.

One child has the all-zero CUSIP sentinel and is quarantined from a CUSIP identity join. The other 43 child CUSIPs pass the check digit. This says nothing yet about whether the parent filing has the same security identifier.

## 2. Event semantics caution

The 44 rows are not 44 activist events. Non-exclusive Phase 93 triage tags appear in only 1 row for activist/control-action language, 11 for aggregated client/adviser holdings, 3 for business-combination consideration, and 21 remain unclassified. Tags are not verified intent or an investment signal.

13D and 13G remain separate hypotheses. No parent/child event is collapsed, and `previousAccessionNumber` is not assumed to name the immediate predecessor.

## 3. Next retrieval gate (Phase 350)

Retrieve each of the 44 exact parent accessions from the SEC archive, preserving the complete raw submission and SHA-256. For every parent, independently verify:

1. Exact parent accession and SEC-HEADER subject CIK.
2. 13D/13G family agreement with the child.
3. Filing date and acceptance UTC strictly earlier than the child.
4. Primary-document format and CUSIP cardinality/check digit.
5. CUSIP comparison with the child, without forcing equality when the security may have changed.
6. Reporting-person identity only from explicit person-level fields/names; never from accession-prefix or filer CIK.
7. Any unavailable, ambiguous, multi-CUSIP, changed-CUSIP, or identity-conflicting record remains quarantined.

A validated explicit reference is not necessarily the immediate predecessor and does not establish a complete chain. No ticker, venue, historical F80 membership, or price coverage is inferred.

## 4. Controls

- Parent documents retrieved in Phase 349: 0.
- New SEC requests: none.
- Strict PIT source admission: false.
- Forward returns, alpha, OOS, bootstrap, LOO and holdout: not run.
- `F80_TOP20_PARTIAL50_BASELINE_C20` and production remain frozen.


The hosted workflow replays this manifest from the immutable Phase 84 and Phase 93 artifacts, validates the committed summary, and uploads the row-level CSV. This phase intentionally performs no SEC network retrieval; the 44 parent documents remain for Phase 350.


## Hosted regression correction — 2026-11-12

The first hosted replay, [run 43325883938](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43325883938), passed Phases 347–348 but stopped in two Phase 349 test fixtures before any manifest replay or SEC request. One fixture attempted to mutate a tuple; the other exposed that the normalization test covered undashed accessions but not the dashed SEC representation. Both fixtures and the dashed-accession path are corrected, and a JSON-writer regression test was added. The next hosted replay is the acceptance gate; the target manifest remains offline-only.


The second hosted replay, [run 43326083200](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43326083200), passed Phases 347–348 but found a source-code escaping defect in the Phase 349 whitespace-normalization expression before the manifest tests could run. The implementation now uses character-wise digit/whitespace normalization rather than regex escaping, and the test suite explicitly covers dashed accessions. No SEC retrieval occurred.


The first successful manifest replay, [run 43326350589](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43326350589), confirmed all 22 regression tests and the 44-row summary, but inspection of its ZIP showed the workflow upload path omitted `phase349_output/`. The workflow now explicitly includes the Phase 349 CSV and summary, and checks the 44 unique parent accessions, 43 valid nonzero CUSIPs, one zero sentinel, and the archive-path-only role before upload. The next hosted run is the final artifact-integrity gate.


## Final hosted replay — 2026-11-12

- [Workflow run 43326498877](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43326498877): SUCCESS.
- 22 regression tests passed: 8 Phase 347, 5 Phase 348 and 9 Phase 349.
- [Artifact 13992528474](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43326498877/artifacts/13992528474), SHA-256 `5073e9f67f0bf3c83f5eb25f513fb231848d3bee2c806eaf8e84da57c02110ef`.
- The ZIP contains the 44-row Phase 349 CSV plus deterministic Phase 347/348 outputs. Its SHA-256 and row counts were checked after download.
- Phase 349 made no SEC network requests; parent retrieval remains Phase 350.
