# Phase 178 — SEC legacy 13D in-sample predecessor-candidate coverage audit

**Date:** 2026-11-07  
**Status:** COMPLETED — negative sample-coverage result; no parent edge or alpha feature admitted.

## Executive result

The 180-row legacy Schedule 13D cohort inherited from Phases 157–159 is too sparse to reconstruct initial filing anchors from within-sample history.

- 180 rows reconcile by accession between the Phase 159 role table and Phase 157 legacy-HTML audit; all 180 per-submission raw SHA-256 values match.
- Phase 159 classifies 112 rows as amendment candidates (108 index-coded /A, four non-/A cover-numbered candidates) and 68 non-/A forms whose initial status remains unconfirmed.
- Of the 55 non-/A, non-numbered rows with extracted Item 4, 46 have a checksum-valid CUSIP, 53 have a body-derived issuer-name candidate, and all 55 have a first reporting-person candidate and filer CIK.
- **Zero of those 55 Item 4 candidates has an earlier in-sample filing with the same normalized body issuer name, checksum-valid CUSIP and filer CIK.** This is not evidence that they are initial filings: the 180 rows are a sample of the 497 legacy HTML filings, not the complete issuer filing history.
- Among all 112 amendment candidates, only two have a unique earlier in-sample record matching normalized body issuer name, checksum-valid CUSIP, filer CIK and first reporting-person candidate. Both candidate predecessors are themselves SC 13D/A, and neither has an earlier same-key base filing inside the sample. They are candidate chain observations, not verified parent links.
- No legacy row in this cohort carries a populated previous_accession value in the Phase 159 role table.

## Two in-sample candidate pairs

| Candidate predecessor | Later amendment candidate | Interpretation |
|---|---|---|
| 0000921895-18-001641 (2018-05-11, /A) | 0001011438-19-000110 (2019-08-21, /A) | Same body-issuer hash, valid CUSIP, filer CIK and first-owner hash; parent/chain role unverified. |
| 0000807249-18-000020 (2018-02-07, /A) | 0000807249-20-000135 (2020-06-02, /A) | Same body-issuer hash, valid CUSIP, filer CIK and first-owner hash; parent/chain role unverified. |

Both candidate predecessor filings are themselves amendments. The sample contains no earlier same-key initial filing for either pair. Therefore neither pair identifies an initial anchor or an immediate predecessor.

## Method

1. Reuse the latest Phase 159 artifact from run 42353084525, artifact 13565349554, and the matching Phase 157 artifact from run 42353084472, artifact 13566915807; no new SEC request was made.
2. Join the 180 Phase 159 rows to Phase 157 by accession and verify raw-document SHA-256 equality for all 180.
3. Create a compact fixture containing accession, filing date, role code, filer CIK, CUSIP, 96-bit prefixes of SHA-256 over normalized body issuer and first reporting-person candidates, Item 4 presence, and previous-accession presence. Raw names and Item 4 excerpts are not stored.
4. Normalize names by uppercasing and retaining ASCII alphanumeric characters, then hash. Require nonempty issuer/owner hashes, a valid CUSIP check digit, filer CIK and strict earlier filing date. Missing identity fields never act as wildcards.
5. Search only within the 180-row sample. Do not treat the result as a global predecessor search.

## Decision

- **PASS:** the in-sample candidate screen is reproducible and finds two narrowly defined amendment-to-amendment candidates.
- **FAIL for parent reconstruction:** zero of 55 Item 4 non-/A, non-numbered candidates has an in-sample predecessor; the two amendment candidate pairs do not reach an initial anchor.
- Keep all 55 Item 4 rows as INITIAL_STATUS_UNCONFIRMED; do not call them initial disclosures.
- Keep the two pairs as CANDIDATE_ONLY_UNVERIFIED; do not create amendment-state edges, backdate text, deduplicate holdings, or infer transaction flow.
- A full historical predecessor search needs the complete issuer filing history and independently validated body issuer/CUSIP/owner identity. The current sample cannot supply it.
- No features, forward returns, bootstrap/LOO, chronological OOS or final-holdout tests. No SEC requests, vendor contact/purchase or production change. F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen.

## Reproducibility

- Input source Phase 159 CSV SHA-256: bb6411e78fc3eca1ca8c7aae6c76a1b26e6ef03138bb5eb622d8747cf330cfa4.
- Input source Phase 157 CSV SHA-256: 154b628436d6c438e54bb953f7d77b0a82f89b5c19373e9f1b642a5140f20072.
- Compact gzip fixture SHA-256: 4d14030c8b176065f40f10537d34d4de9491c71183200ab3480f27469085cb05.
- Decompressed compact CSV SHA-256: 4370ba9645d8184101fd8230cdcf274c99c68cd9561387aee898fc4cb7063d07.
- Helper: research/phase178_sec13d_legacy_parent_candidate_audit.py.
- Tests: research/test_phase178_sec13d_legacy_parent_candidate_audit.py.
- Metadata: research/phase178_sec13d_legacy_parent_candidate_audit.json.
- Input: research/phase178_sec13d_legacy_parent_input.csv.gz.
