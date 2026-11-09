# Phase 159 — SEC Schedule 13D cover-page amendment-number and Item 4 cohort audit

**Date:** 2026-11-06  
**Status:** COMPLETED — filing-role correction / source-feasibility audit only; no alpha test

## Executive finding

Phase 158 grouped 72 legacy HTML filings indexed as SC 13D into an “initial” cohort. That label was too strong. A cover-page audit finds **four non-/A index filings with an explicit positive Amendment No.** All four have an extracted Item 4 section and were labelled INITIAL_DISCLOSURE by Phase 158.

They are now quarantined as COVER_NUMBERED_AMENDMENT_CANDIDATE. Their parent accessions are not resolved in the Phase 124 sample. The absence of a positive number in the remaining 68 documents does not prove they are initial filings: 40 cover fields are blank/N/A and 28 are missing or unparseable.

This is a lower-bound correction, not a complete amendment-lineage solution.

## Immutable inputs

- Phase 124: run 42073725379 / artifact 13436764625; 600 raw submissions.
- Phase 157: run 42224436013 / artifact 13504962007; 497 legacy HTML rows.
- Phase 158: run 42231437618 / artifact 13510130459; 180 legacy 13D rows and 117 Item 4 sections.
- ZIP SHA-256: Phase 124 85f69e083b5af65731c9bcfe24e8c75821fc0f2c2476bfa8ba573e2e884570dc; Phase 157 c7c46e51ddda8ac85b60763a337e5cd2273f5af0c522d91f862bdb668791ce4a; Phase 158 dac2421a7eb56fa0fe7c3322fa3da4bb8c1c6189561aef22993df5ab5370bfd9.
- All 600 Phase 124 raw hashes were rechecked. The 180 legacy 13D records reconcile by accession and hash across phases. All 117 Phase 158 Item 4 section hashes reproduce from raw submissions.

## Corrected role counts

| Class | Filings | Item 4 sections | Coverage |
|---|---:|---:|---:|
| Index-coded SC 13D/A | 108 | 58 | 53.70% |
| Index SC 13D, cover-numbered amendment candidate | 4 | 4 | 100.00% |
| Index SC 13D, no positive cover number; initial status unconfirmed | 68 | 55 | 80.88% |
| **Total** | **180** | **117** | **65.00%** |

Among the 72 index non-/A forms: four have a positive numeric Amendment No.; 40 have blank, underscore or N/A fields; 28 have no parseable field. The Phase 158 “initial” Item 4 count was 59. Four of those 59 (6.78%) are removed from that candidate cohort, leaving 55 non-/A, non-numbered Item 4 candidates. They are still not verified initial filings.

## Four cover-numbered candidates

| Accession | Issuer candidate | Cover number | Filed / accepted ET | Item 4 content |
|---|---|---:|---|---|
| 0000752642-16-000020 | UMH Properties, Inc. | 34 | 2016-01-22 / 14:12:30 | Investment-purpose holding, no change of control and no current plans for listed extraordinary actions. |
| 0001534424-16-000499 | MRI Interventions, Inc. | 3 | 2016-01-08 / 08:54:04 | Investment-purpose holding, possible future increase and communications, but no current plans for enumerated actions. |
| 0001599916-18-000173 | Exceed World, Inc. | 1 | 2018-10-09 / 09:43:23 | States e-Learning no longer owns shares; describes prior control acquisition/director changes and no remaining authority over the board. Item 4 refers to the statement as Schedule 13D/A. |
| 0000860662-23-000007 | AGTB Private BDC | 4 | 2023-01-09 / 17:13:05 | Explicitly says Item 4 is amended to add the completed January 1, 2023 merger. Acceptance is after 16:00 ET; next conservative daily session is January 10, 2023. |

All four have no previous_accession in the Phase 124 sample. The number is a strong amendment indicator, not a resolved parent link, new trade, new purchase or standalone event.

## Method and controls

- Parse only the first cover-page Amendment No. field in non-/A index filings.
- Skip cover-field parsing for index-coded /A documents; short amendment documents can expose body references inside the first 80 lines.
- Positive numeric values are amendment candidates. Blank, underscore, N/A, missing and unresolved values never prove an initial filing.
- Reproduce and verify the Phase 158 Item 4 section hash before including each row.
- Do not infer parent accessions or event novelty from the cover number.

## Decision

1. Supersede Phase 158's INITIAL_DISCLOSURE interpretation for the four accessions above. Its total of 117 extracted Item 4 sections remains correct; its 59/58 role split does not.
2. Use 58 index-coded amendment sections, four additional cover-numbered amendment candidates, and 55 Item 4 sections on non-/A forms whose initial status remains unconfirmed.
3. Do not train an activist-intent classifier or run returns tests on the 55 until parent lineage, subject/security identity and universe coverage are resolved.
4. A full parent search across earlier quarters remains necessary. Blank or missing Amendment No. fields are not evidence of an initial filing.
5. No forward returns, feature panel, bootstrap/LOO, final holdout or production change. F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen.

## Reproducibility

- Helper: research/phase159_13d_cover_amendment_role_audit.py
- Tests: research/test_phase159_13d_cover_amendment_role_audit.py
- Workflow: .github/workflows/phase159_sec_13d_cover_amendment_role_audit.yml
- Artifact: phase159-sec-13d-cover-amendment-role-audit (180-row role table plus summary)
