# Phase 179 — SEC legacy 13D/G 497-row predecessor coverage and relaxed-key collision audit

**Date:** 2026-11-07  
**Status:** COMPLETED — expanded in-sample screen remains insufficient; no parent edge or alpha feature admitted.

## Executive result

Phase 178 tested the 180 legacy 13D rows in the Phase 159 role table. Phase 179 expanded the same conservative predecessor screen to **all 497 legacy HTML filings** in the Phase 157 cohort (180 13D and 317 13G), using only immutable artifacts already present in the repository. No new SEC request was made.

- The Phase 157 source CSV contains 497 unique accessions. The 180 13D rows reconcile one-to-one to the Phase 159 role table; all 180 raw-document SHA-256 values match.
- Role counts after applying the four verified Phase 159 cover-numbered 13D amendment candidates: 316 amendment candidates (108 index-coded 13D/A, 204 index-coded 13G/A, four cover-numbered 13D candidates) and 181 non-/A forms whose initial status remains unconfirmed.
- Under the strict key — normalized body-issuer hash, checksum-valid CUSIP, filer CIK and first-reporting-person hash — only **two** amendment-to-amendment candidate pairs appear in the full 497-row sample. Both are 13D/A-to-13D/A, both parent candidates are themselves amendments, and neither has an earlier strict-key anchor in the full sample.
- The 55 non-/A, non-numbered 13D Item 4 candidates still have **zero** in-sample predecessors; 46 have a complete strict key. None can be called an initial filing from this sample.
- Relaxing the key to issuer+CUSIP creates six additional collisions: three within 13G and three cross-family 13G-to-13D. Every one of these six fails both filer and first-owner continuity. They are false-match controls, not parent candidates.

## Quantitative results

| Screen | Eligible children | Children with candidate | Ambiguous | Interpretation |
|---|---:|---:|---:|---|
| Strict 4-key, amendment candidates, same family | 276 | 2 | 0 | Two candidate-only 13D/A pairs |
| Strict 4-key, non-/A forms, same family | 161 | 0 | 0 | No in-sample predecessor found |
| Strict 4-key, 55 Item 4 13D candidates | 46 | 0 | 0 | Initial status remains unconfirmed |
| 3-key without first owner | 278 | 2 | 0 | No additional candidate |
| 3-key without filer | 276 | 2 | 0 | No additional candidate |
| Issuer+CUSIP, same family, amendment candidates | 278 | 5 | 0 | Two strict plus three 13G collisions |
| Issuer+CUSIP, all families, amendment candidates | 278 | 8 | 0 | Five same-family plus three cross-family collisions |

The two strict candidate pairs are unchanged from Phase 178:

| Candidate predecessor | Later amendment candidate | Status |
|---|---|---|
| 0000921895-18-001641 (2018-05-11) | 0001011438-19-000110 (2019-08-21) | 13D/A → 13D/A; candidate only; no earlier strict anchor |
| 0000807249-18-000020 (2018-02-07) | 0000807249-20-000135 (2020-06-02) | 13D/A → 13D/A; candidate only; no earlier strict anchor |

The six relaxed-key collisions are deliberately retained in the metadata with accessions, dates, form family and continuity flags. They share issuer/CUSIP but have neither the same filer CIK nor the same first-owner hash. Three are 13G-to-13G collisions; three are 13G-to-13D collisions. This demonstrates why issuer/CUSIP alone cannot establish a beneficial-owner or amendment relationship.

## Method and controls

1. Reuse the current-head Phase 157 legacy HTML field audit (497 rows) and Phase 159 13D cover-amendment role table (180 rows); verify the source CSV SHA-256 values.
2. Reconcile the 180 Phase 159 rows to the 13D subset of Phase 157 by accession and verify raw-document SHA-256 equality for all 180.
3. Use the four Phase 159 positive cover-numbered 13D rows as amendment candidates. For 13G, only the index `/A` code is used; non-/A 13G forms remain unconfirmed because no equivalent cover-number audit was performed.
4. Normalize issuer and first reporting-person candidate strings to uppercase ASCII alphanumerics, then persist only 96-bit SHA-256 prefixes. The first reporting-person field is a parser candidate, not a verified beneficial-owner identity. No raw names, Item 4 text or ownership amounts are persisted.
5. Require strictly earlier filing date, exact family where specified, nonempty identifiers and a valid 9-character CUSIP check digit. Missing values never act as wildcards. Relaxed-key results are diagnostic collisions only.

## Decision

- **PASS:** the expanded 497-row sample audit is reproducible and confirms two narrow amendment-to-amendment candidates.
- **FAIL for parent reconstruction:** the 497-row sample still does not reach an initial anchor; all 55 Item 4 non-/A 13D candidates remain unconfirmed.
- Do not create parent/state edges, deduplicate ownership, infer buys/sells, train an intent classifier, backdate Item 4 text or run returns tests from these sample matches.
- Do not relax identity requirements to issuer+CUSIP: the six extra matches fail both filer and first-owner continuity.
- Full historical issuer filing histories, role-correct beneficial-owner groups, effective-dated issuer/security identity and a reliable EDGAR knowledge-time panel remain necessary.

## Reproducibility

- Phase 157 current-head run [42354802427](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42354802427), artifact [13567167891](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42354802427/artifacts/13567167891).
- Phase 159 current-head run [42354802447](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42354802447), artifact [13566809056](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42354802447/artifacts/13566809056).
- Phase 157 source CSV SHA-256: `154b628436d6c438e54bb953f7d77b0a82f89b5c19373e9f1b642a5140f20072`.
- Phase 159 source CSV SHA-256: `bb6411e78fc3eca1ca8c7aae6c76a1b26e6ef03138bb5eb622d8747cf330cfa4`.
- Compact hash-only input payload: gzip SHA-256 `b4549ba063b07df34ba89c1a874a8cbe9f96340d8af05e3f86dcf9664560fcda`; decompressed CSV SHA-256 `6d0cc2a0841dc58a362be1e2b61d055a4e300da53ff157dedb9df5096d919626`.
- Helper: `research/phase179_sec13dg_legacy_497_predecessor_audit.py`.
- Tests: `research/test_phase179_sec13dg_legacy_497_predecessor_audit.py`.
- Metadata: `research/phase179_sec13dg_legacy_497_parent_summary.json`.
- The compact hash-only input is rebuilt in memory from the pinned Phase 157/159 artifacts; source CSV SHA-256 values, the 180-row 13D accession/raw-document reconciliation, and the derived compact CSV/gzip SHA-256 values are all verified. The source artifacts expire 2026-12-07; after that, rerunning the full 497-row audit requires refreshed, independently verified upstream artifacts.

No forward-return, bootstrap/LOO, chronological OOS or final-holdout test was run. No SEC requests, vendor contact/purchase, production change or F80 modification. `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen.


## Hosted CI fixture-integrity correction (2026-11-07)

- Current-head run [42359960357](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42359960357) passed compilation but failed in test class setup before any of the 14 tests ran. The decoder raised `Incorrect padding` for the committed base64 fixture; metadata generation and artifact upload were skipped. This is a corrupted/truncated fixture, not evidence against the audit logic or the SEC source data.
- Replaced the single-file fixture dependency with deterministic in-memory reconstruction from the two immutable upstream artifacts: Phase 157 run 42354802427 / artifact 13567167891 and Phase 159 run 42354802447 / artifact 13566809056. The reconstruction checks both source CSV hashes, all 180 13D accessions and raw-document hashes, then verifies the exact derived compact CSV SHA-256 `6d0cc2a0841dc58a362be1e2b61d055a4e300da53ff157dedb9df5096d919626` and deterministic gzip SHA-256 `b4549ba063b07df34ba89c1a874a8cbe9f96340d8af05e3f86dcf9664560fcda`.
- The PR-only workflow now downloads those pinned artifacts with read-only Actions permission, reconstructs the fixture on the runner, and only then runs the offline regression suite and metadata gate. The corrupt base64 fixture is removed. No new SEC request, source download, raw-name persistence or change to Phase 179 findings.
- Upstream artifacts currently expire 2026-12-07. This CI replay is reproducible while those immutable artifacts remain retained; after expiry, the upstream Phase 157/159 artifacts must be refreshed and re-hash-verified before rerunning. The committed summary/report remain the permanent record of this sample result.
