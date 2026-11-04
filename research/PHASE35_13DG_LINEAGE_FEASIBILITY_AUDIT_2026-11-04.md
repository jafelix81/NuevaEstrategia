# Phase 35 — 13D/13G amendment-lineage feasibility audit

**Date:** 2026-11-04  
**Inputs:** frozen SEC XML artifacts from 2025Q2, 2025Q3, 2025Q4 and 2026Q1.  
**Coverage:** 1,278 unique target-subject accessions (111 13D; 1,167 13G).  
**Code:** `phase35_13dg_lineage_feasibility_audit.py`; four helper tests are included. The local prototype test harness passed; the repository test file has not yet been run by GitHub Actions.

## Cross-quarter identity validation

The latest Q4/Q1 workflow [41742690656](https://github.com/jafelix81/NuevaEstrategia/actions/runs/41742690656) completed successfully. Its artifact is `13282921575`.

The Q1 pilot was the development sample. The frozen rule then passed the first Q2/Q3 held-out validation at 237/237 exact matches against explicit 13D reporting-person CIKs, followed by a second Q4/Q1 held-out validation at **231/231 exact matches** (zero mismatches). The pooled two-holdout count is 468/468. This is conditional precision among unique matched 13D cases, not a universal guarantee.

For 13G, target-sample name-match coverage was:
- 2025Q2/Q3: 461/480 (95.96%).
- 2025Q4: 219/224 (97.77%).
- 2026Q1: 457/463 (98.70%).
- Q4/Q1 held-out combined: 676/687 (98.40%).
- Combined development + held-out: 1,137/1,167 (97.43%).

The 13G figures are **coverage only**, not precision: the tested XMLs did not provide explicit reporting-person CIKs to validate the matches. Neither the crosswalk nor its candidate CIK is a reporting-group identity.

## Amendment-lineage audit

| Metric | 13D | 13G |
|---|---:|---:|
| Filings | 111 | 1,167 |
| Amendments | 98 | 925 |
| Amendments with `previousAccessionNumber` | 57 | 331 |
| Pointer coverage | 58.2% | 35.8% |
| Referenced accession found in four-quarter panel | 23 | 94 |
| Same subject CIK / form family | 23 / 23 | 94 / 94 |
| Same matched reporting-person name | 23 | 92 |
| CUSIP overlap | 23 | 92 |
| Comparable person + CUSIP references | 23 | 90 |
| Pointer equals latest earlier candidate | 19/23 | 75/90 |
| Pointer references an older candidate | 4/23 | 13/90 |
| Same-day pointer; ordering unresolved | 0/23 | 2/90 |

**Critical correction:** `previousAccessionNumber` must be preserved as an explicit prior-filing reference, but it is **not a guaranteed immediate-predecessor edge**. In the comparable in-panel subset, four 13D references and thirteen 13G references point to an older accession even though a later same-subject/person/CUSIP filing exists. Two additional 13G references are same-day and cannot be ordered using filing date alone. Two 13G cases have person/CUSIP identity conflicts and are quarantined.

For amendments with no explicit pointer, the bounded panel found:
- **13D:** 11 unique earlier candidates, 8 multiple-candidate cases, 19 with no in-panel candidate, 3 unmatched-person/missing-CUSIP cases.
- **13G:** 150 unique earlier candidates, 38 multiple-candidate cases, 400 with no in-panel candidate, 6 unmatched-person/missing-CUSIP cases.

These are not assignments. The panel is left-censored before 2025Q2; a zero-candidate result may simply mean the relevant original filing predates the panel. A unique candidate remains unassigned because the explicit-pointer audit demonstrates that a prior accession reference may point to the original/root filing rather than the latest amendment.

## Decision

- Keep `previousAccessionNumber` as a validated reference/chain anchor, not an assumed sequential edge.
- Reconstruct chronological snapshots separately by subject issuer, uniquely identified reporting person, security class/CUSIP and filing KnowledgeDate. Use accepted timestamps to resolve same-day filings; otherwise quarantine them.
- Use `amendmentNo` only as a diagnostic/order field after validating uniqueness and monotonicity within a fully reconstructed identity key.
- Do not infer multi-person groups from incomplete reporting-person CIK sets or name matches.
- Do not assign missing predecessor edges from a single candidate in this left-censored panel.
- **No forward returns, event-direction labels, thresholds, or alpha tests were run.** F80 remains frozen.
