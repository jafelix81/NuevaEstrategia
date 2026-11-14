# Phase 401 — Full Form 144/A parent-identity census

**Status:** hosted SEC retrieval pending. Research-only; no return calculations.

## Objective

Phase 400 recovered three selected unmatched parent documents and found three issuer-CIK changes among those exceptions. That does not establish whether the same issue occurs in amendments whose child issuer CIK falls outside the Phase 67 candidate panel. It also cannot detect the reverse case: a parent issuer CIK is in the candidate set but the amended child issuer CIK is not, which would leave a stale parent version in the candidate panel.

Phase 401 therefore expands the audit from the 196 candidate 144/A rows to **all 609 Form 144/A accessions** in the 14-quarter Phase 67 master-index census (2023Q2–2026Q3). It resolves each explicit `previousAccessionNumber` parent, compares issuer/filer/seller/security and proposed-sale tranche fields, and measures transitions across the exact 290 candidate CIKs present in Phase 67 accession pairs.

## Frozen inputs and reproducibility

- Candidate CIK snapshot: `PHASE401_FORM144_CANDIDATE_CIK_MANIFEST_2026-11-14.json`.
- Source artifact: Phase 67 artifact 13334881835, SHA-256 `939d5564b14ce0f41df23a2c9ab681977cfde141cd0ea2b3c1213b1c5bfaf613`.
- The 290 CIKs are a current-CIK candidate set observed in Phase 67 master-index pairs, **not** a historical F80 security master.
- The 2023Q2–2026Q3 child census is expected to reproduce 56,167 accessions and 609 amendments.
- Phase 400's curated original-parent payload is used only for a known parent accession outside the 14-quarter census; it is labelled separately and is not represented as a fresh retrieval.

## Predeclared quality gates

1. Reproduce the 56,167-accession / 609-amendment Phase 67 census exactly.
2. Parse at least 99.5% of all 609 child XMLs; no silent drops.
3. At least 99.5% of parsed children must match master-index form and both XML CIK roles must reconcile to the master-index pair.
4. Every parsed 144/A must expose an explicit previousAccessionNumber.
5. Resolve at least 99.5% of explicit parent links; parent/child form and filing-date ordering are audited separately.
6. Keep all unresolved accessions in an explicit error file.
7. Report both candidate-boundary directions, not only parent-noncandidate to child-candidate.
8. Do not treat every CIK change as a correction unless the amendment itself supports that interpretation.

## Interpretation controls

- A 144/A is a version/update of a proposed-sale notice, not a new sale by default.
- Corrected issuer identity is not backdated to the original filing.
- Filer CIK and issuer CIK remain separate.
- Missing fields in a curated parent fixture are treated as unknown, not as changed values.
- `noOfUnitsOutstanding` remains killed as a numeric denominator/feature.
- No actual execution is inferred from a proposed-sale notice.

## Economic authorization

This phase calculates no forward returns, no alpha, no model comparison, no bootstrap/LOO and does not touch the holdout. Historical F80 membership, inactive/predecessor security identity, accepted-time PIT and actual sale execution remain separate gates. F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen.


## Existing Form 144 → Form 4 work (do not duplicate)

The repository's separate draft branches behind PRs #29 and #30 already contain a 2026Q3 descriptive conversion/linkage study. Its reported sample is 1,451 Form 144 notices / 1,460 tranches and 38,152 Form 4 submissions / 59,885 nonderivative transaction rows. It found 570 one-to-one notice-to-Form-4 links (39.3% of eligible notices), 521 exact date-and-share matches, and 481/521 class-family agreements. A separate selection audit matched 570/1,665 eligible Form 4 sale blocks (34.2%). A global placebo audit found 12/13 tests significant after Holm correction, but those tests concern non-random document linkage, not forward-return prediction. Phase 275 uses issuer CIK × filing date as the descriptive event unit; owner independence remains unproven.

These results are useful execution-conversion evidence, but they are a single-quarter descriptive sample on unmerged draft branches. They do not establish broad historical coverage, strict PIT identity, an independent owner-level panel, or alpha. Phase 401 therefore does **not** repeat the Form 144/Form 4 matching test. It addresses the broader 144/A parent-identity selection boundary that must be solved before any historical proposed-supply event study.

## Current hosted execution

- Run [43621827885](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43621827885) is the single active live census. Its offline regression job passed; the SEC XML retrieval step is still running.
- No second live census is to be launched while that run is active.
