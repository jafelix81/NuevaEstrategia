# Phase 98 — Phase 69 Form 144 incremental scan: no new candidates

**Date:** 2026-11-05  
**Run:** https://github.com/jafelix81/NuevaEstrategia/actions/runs/41959603351  
**Artifact:** https://github.com/jafelix81/NuevaEstrategia/actions/runs/41959603351/artifacts/13385365595  
**Artifact SHA-256:** `f84644200a8925c6fc190a823ca0dcd6b40c7bee127a8d2740a5ea67cae56519`  
**Mode:** 14-quarter SEC master-index scan and strict baseline merge; no forward returns.

## Executive result

The Phase 69 extension completed. The ten newly mapped current fund-registrant CIKs produced **zero Form 144 / 144-A candidate accessions** in the 14-quarter 2023Q2–2026Q3 master-index census. There were no overlaps, no new issuer events and no XML errors because no incremental candidate XML required retrieval.

The expanded panel is unchanged from Phase 67. The source-extension hypothesis is closed for these ten CIKs and this period; do not repeat the same scan without a materially changed CIK set, period or source.

## 1. Results

| Measure | Phase 67 baseline | Phase 69 expanded result |
|---|---:|---:|
| Current ticker mapping | 308/335 | 335/335 |
| Candidate registrant CIKs | 309 | 319 |
| Candidate accessions | 21,648 | 21,648 |
| Issuer-event rows | 21,634 | 21,634 |
| Filer-only false positives excluded | 14 | 14 |
| Unresolved rows | 0 | 0 |
| XML fetch/processing errors in candidate set | 0 | 0 |
| Zero-candidate controls | 280 | 280 |
| Control pair concordance | 100% | 100% |

Incremental scan:
- Ten preregistered new fund-registrant CIKs were present in the 319-CIK map.
- New CIK candidate accessions: **0** in every quarter from 2023Q2 through 2026Q3.
- New accessions: 0; overlapping accessions: 0; identity conflicts: 0.
- Incremental issuer events: 0; filer-only rows: 0; unresolved rows: 0; XML errors: 0.
- Expanded event panel remains 21,634 rows across 289 unique XML issuer CIKs.

The 280 controls retained 100% master-pair concordance. The 335/335 current ticker map passed with zero mapping-source errors.

## 2. Important denominator qualification

The original run reports `data_gate=PASS`. Because there were zero incremental candidates, its XML fetch, role-resolution, pair-concordance and form-match checks had zero denominators and were therefore vacuously true. They must **not** be described as an XML validation of the ten new CIKs.

After the run, the Phase 69 branch was corrected so a zero-candidate result is explicitly labelled:
- `incremental_identity_validation_status=NOT_APPLICABLE_NO_CANDIDATES`;
- `data_gate=PASS_NO_INCREMENTAL_CANDIDATES`;
- XML-specific gates are `null` rather than false-positive passes.

Two offline regression tests were added for empty-denominator handling. This code-only correction does not repeat the SEC scan and does not alter the immutable artifact or original run result.

## 3. Interpretation and limitations

- The ten new CIKs were current fund registrants, not historical security identifiers.
- The absence of master-index candidate pairs means this extension adds no Form 144 issuer events for those registrants during the tested period. It does not prove that the associated funds did not hold securities or that no other filings describe their positions.
- Fund series/class-to-security-class attribution remains untested. A trust-level CIK must not be assigned to every ETF or ticker mapped to that registrant.
- Historical F80 membership, delisted predecessor issuers, accepted/publication timestamps and full amendment lineage remain untested.
- Form 144 is a proposed sale-order notice, not proof of an executed sale. Form 144/A remains an update, not a new event by default.

## 4. Decision

1. Keep the Phase 67/69 panel as a current-CIK, 2023Q2–2026Q3 Form 144 feasibility dataset with the 14 filer-only false positives excluded.
2. Close the ten-CIK incremental extension as **no incremental coverage**; do not run it again for the same set and period.
3. Do not run forward returns or construct supply-pressure features yet.
4. Move research effort to the binding PIT historical-universe/security-master gate described in Phase 97.

No alpha test, feature selection, portfolio comparison, vendor purchase or production change occurred. F80 remains frozen.
\n\n## 2026-11-05 code-only validation addendum\n\n- Corrected Phase 69 zero-candidate denominator semantics on branch `phase69-incremental-form144-fund-registrants` (script commit `c12e9631344d52f609743eed58599c08e36a7784`; test commit `9ef816fd4346f85edccdf3c2c542a8192afab8b8`). XML identity sub-gates now show `null` when no incremental candidate exists, and the summary reports `NOT_APPLICABLE_NO_CANDIDATES` / `PASS_NO_INCREMENTAL_CANDIDATES`.\n- Hosted offline regression run 41959973317 passed **45 tests**; the live incremental-scan job was skipped. No SEC rescan was performed.\n