# Phase 160 — SEC 13D/G direct previous-accession reconciliation against the global master index

**Date:** 2026-11-06  
**Status:** COMPLETED — accession-level lineage cross-check only; no alpha test

## Executive finding

The explicit previousAccessionNumber field in structured 13D/G XML can be reconciled against the 43-quarter global SEC master-index artifact with high coverage in the Phase 124 sample:

- 32 structured filings contain a non-empty direct previousAccessionNumber.
- All 32 parent accession values are unique; none is reused by another sampled child.
- 30/32 parent accessions are present in the 2016Q1–2026Q3 global index after canonical accession normalization.
- 29 parents match exactly as written. One is recovered by padding a missing leading zero in the accession CIK: 1376474-25-000733 becomes 0001376474-25-000733.
- The two absent parent accessions are from 2012 and 2015, before the index starts at 2016Q1.
- All 30 found parents match the child 13D/13G family, precede the child filing date, and are non-amended SC 13D or SC 13G index rows.
- The parent index candidate-CIK set contains the current filer CIK in 30/30 cases and the current SEC-header subject CIK in 29/30 cases.

This validates a direct-accession discovery and chronology check for structured filings. It does not prove subject identity: Phase 82 explicitly treats master-index/archive-path CIKs as candidates, not role-labelled subject/filer identities.

## Immutable inputs and integrity

- Phase 82 global index: run [41892370262](https://github.com/jafelix81/NuevaEstrategia/actions/runs/41892370262), artifact 13353118959, ZIP SHA-256 e925ad8fe9792f27e570b9e882dff772bb67d9edd67f1c93404a198faab80985.
- Phase 124 role-aware sample: run [42073725379](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42073725379), artifact 13436764625, ZIP SHA-256 85f69e083b5af65731c9bcfe24e8c75821fc0f2c2476bfa8ba573e2e884570dc.
- Phase 82 contains 324,964 unique 13D/G accessions across 43 quarters, 2016Q1–2026Q3, with zero duplicate accessions and zero unexplained metadata conflicts.
- Phase 124 contains 600 sampled submissions; 102 are structured XML. The 32 direct predecessor links are a sample subset, not a population-wide estimate.
- Both inputs were reused from immutable artifacts. No new SEC request was made.

## Reconciliation results

| Check | Result |
|---|---:|
| Structured sample rows with direct predecessor | 32 |
| Unique predecessor accessions | 32/32 |
| Parent accession found in global index | 30/32 |
| Exact raw accession lookup | 29 |
| Recovered by canonical CIK/sequence padding | 1 |
| Parent before index history | 2 |
| Parent 13D/13G family matches child | 30/30 found |
| Parent filing date before child filing date | 30/30 found |
| Parent is non-amended SC 13D or SC 13G | 30/30 found |
| Current filer CIK appears among parent index candidate CIKs | 30/30 found |
| Current subject CIK appears among parent index candidate CIKs | 29/30 found |
| Reused parent accession across sampled children | 0 |

The two out-of-window predecessors are 0000315066-12-002323 and 0001088875-15-000026. Their absence is expected given the 2016Q1 start of Phase 82 and does not establish that no parent document exists.

## Identity/role exception — quarantine

Current accession 0001445546-25-002475 points directly to 0001445546-21-002430. The parent accession is present in the global index and its candidate CIKs include the current filer CIK 0001184765, but do not include the current XML subject CIK 0001510337. The parent index candidates are 0001184765 and 0001667919.

This is not proof that the explicit predecessor pointer is wrong. The index CIK set is not role-labelled, and a corporate/series identity transition or source-role discrepancy cannot be adjudicated from the master index alone. Keep the accession link but quarantine subject continuity until the parent submission's SEC header/XML and effective-dated security identity are inspected.

## Method and safeguards

1. Use only structured sample rows with xml_present=true, a real 13D/G submission, and a non-empty previousAccessionNumber.
2. Canonicalize accession formatting by zero-padding the CIK to 10 digits and sequence to six digits; do not alter the year or fuzzy-match accessions.
3. Require a unique exact parent accession in the global index.
4. Check 13D/13G family concordance and strict parent filing-date precedence.
5. Record parent candidate CIK presence only as a diagnostic. Do not label candidate CIKs as subject or filer based on their position in the index.
6. Preserve out-of-window and identity/role exceptions as unresolved; do not substitute same-filer/date-proximity guesses.

## What remains unresolved

- Phase 156 found 59 structured amendments, but only 32 have previousAccessionNumber; the other 27 still need predecessor reconstruction from the accession document and filing history.
- The 497 legacy HTML filings from Phase 157 do not gain a parent link from this structured-XML test. Cover-page Amendment No. is only an amendment indicator, not a parent accession.
- The two pre-2016 parents require an earlier global index/submission source if full chain coverage is needed.
- The single subject-CIK candidate discrepancy requires the original parent submission, not a guessed CIK crosswalk.
- The index contains discovery metadata, not a permanent security master or historical active-universe membership.

## Decision

PASS for direct structured-XML accession lookup and chronology validation; UNRESOLVED for complete 13D/G amendment-state reconstruction. Use previousAccessionNumber as the primary explicit parent pointer where present, then validate the parent document and subject/security continuity. Do not infer parent links for legacy HTML from filing-agent CIK, date proximity, or a positive Amendment No.

No forward returns, feature panel, bootstrap/LOO, OOS test, final holdout, vendor contact/purchase, or production change. F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen.

## Reproducibility

- Helper: research/phase160_13dg_previous_accession_index_reconciliation.py
- Tests: research/test_phase160_13dg_previous_accession_index_reconciliation.py
- Workflow: .github/workflows/phase160_sec_13dg_previous_accession_index_reconciliation.yml
- Output: phase160_13dg_previous_accession_index_reconciliation.csv and phase160_13dg_previous_accession_index_summary.json


## CI reproducibility note

The first Phase 160 GitHub Actions attempt could not download the 185 MB Phase 82 cross-run artifact: the download action returned “Bad credentials” before the audit step. The source artifact remains available and unexpired. To avoid repeating a cross-run credential dependency, the workflow now uses compact, hash-pinned excerpts extracted from the immutable Phase 82 and Phase 124 artifacts. The manifest preserves both original run/artifact IDs and full ZIP SHA-256 values; the helper verifies the compact CSV hashes before recomputation. The compact index excerpt contains only the 30 found parent rows, and the compact child file contains the 32 explicit predecessor links. The full 324,964-row index integrity figures remain sourced from the completed Phase 82 full-index audit, not recomputed from the excerpt. This distinction is explicit in the manifest and summary.


## Final CI execution note

The first CI attempt failed at cross-run artifact download with Bad credentials; the workflow was changed to use compact, hash-pinned excerpts from the immutable Phase 82 and Phase 124 artifacts. The next compact run passed all 19 tests but exposed a missing CSV/JSON output-writer function in the helper. The writer is now implemented and covered by a regression test. Final GitHub Actions run [42256372788](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42256372788) completed successfully: 20/20 regression tests passed, compact input hashes verified, the 32-link reconciliation recomputed, and artifact 13521928292 uploaded. Phase 160 is CI-green on the recorded head.
