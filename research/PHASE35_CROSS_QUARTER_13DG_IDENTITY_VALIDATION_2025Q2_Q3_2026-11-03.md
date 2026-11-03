# Phase 35 — Cross-quarter 13D/13G identity validation (2025Q2–Q3)

Date: 2026-11-03  
Canonical branch: `phase35-13dg-issuer-attribution-repair`  
Canonical workflow: [41729360514](https://github.com/jafelix81/NuevaEstrategia/actions/runs/41729360514)  
Job: `126242359519` (`quarterly_identity`, all steps successful)  
Artifact: `phase35-global-subject-census-crossquarter-identity-2025q2-q3`, ID `13277920675`, SHA-256 `3ab744ca033ec1af94c7586004bbe3ce9dd0bed9b5d8677cfd5e27a41c06c5b4`  
Code commit used by run: `a73e60621fbe9abb76a2b98cc600c82fabc637ef`

## Decision

**PASS — cross-quarter structured-XML subject/filer identity and candidate filer-to-person link feasibility.**  
**NOT PASSED — 13G link precision, complete reporting-group identity, amendment-chain reconstruction, historical F80 membership, legacy pre-structured-XML identity, or economic testing.**

The canonical run completed all parser, master-index, XML identity, and crosswalk tests; both 2025Q2 and 2025Q3 censuses and the crosswalk audit completed successfully. A duplicate prototype-branch run (41729228829; artifact 13276720759) also completed, but this report uses only the canonical-branch artifact. No workflow remains in progress.

## Global subject-census results

| Metric | 2025Q2 | 2025Q3 |
|---|---:|---:|
| Master-index rows | 15,057 | 14,443 |
| Unique 13D/G accessions | 7,530 | 7,222 |
| Candidate-relevant discovery accessions | 1,561 | 1,099 |
| Non-target validation sample | 203 | 201 |
| XML requested | 1,764 | 1,300 |
| XML parsed | 1,761 | 1,299 |
| XML fetch errors | 3 | 1 |
| Subject CIK coverage, target-relevant | 100.00% | 100.00% |
| Submission-filer CIK coverage, target-relevant | 100.00% | 100.00% |
| Subject CIK coverage, non-target sample | 98.52% | 99.50% |
| XML form agreement | 99.83% | 99.92% |
| Target-subject filings | 289 | 252 |
| Target-submission-filer filings | 1,374 | 899 |
| Filer-only cross-issuer filings | 1,272 | 847 |

The 1,561/1,099 discovery counts are unions based on candidate CIKs appearing on either side of the master-index accession pair. They are not target-subject counts. The subject-side counts are 289 and 252, respectively. Filer-only cross-issuer records must not be assigned to the subject issuer.

The seven XML download errors across both quarters were all in the deterministic non-target validation samples, not in the target-relevant samples. Current mapping still resolves 307/335 candidate tickers; 27 ETF-like tickers remain unresolved. This is not a point-in-time historical security master or historical F80 membership panel.

## Frozen name crosswalk: coverage

The pre-frozen rule normalizes Unicode/case/punctuation, strips a fixed list of legal suffixes, permits token-order invariance only for persons explicitly typed as individuals, preserves entity token order, and accepts only one exact canonical-name match between the master-index submission-filer name and a reporting person. It does not read explicit CIKs to make the match and does not overwrite source fields.

| Sample | Family | Q2 matches | Q3 matches | Combined |
|---|---|---:|---:|---:|
| Target-subject | 13D | 23/25 (92.00%) | 34/36 (94.44%) | 57/61 (93.44%) |
| Target-subject | 13G | 252/264 (95.45%) | 209/216 (96.76%) | 461/480 (96.04%) |
| Non-target validation | 13D | 90/100 (90.00%) | 90/100 (90.00%) | 180/200 (90.00%) |
| Non-target validation | 13G | 95/100 (95.00%) | 96/100 (96.00%) | 191/200 (95.50%) |

No ambiguous multi-person matches occurred in the Q2/Q3 crosswalk samples. Unmatched target-subject 13G records were 12/264 in Q2 and 7/216 in Q3. Unmatched validation 13G records were 5/100 and 4/100. These remain unresolved; no fuzzy or post-hoc alias expansion was applied. Common unmatched patterns include “PRICE T ROWE ASSOCIATES INC /MD/” versus “T. Rowe Price Associates, Inc.”, trustee names with long fiduciary capacity text, and multi-person filings where the submission filer is not an exact canonical-name match to one cover-page person.

## Held-out identity check using explicit 13D CIKs

A separate validation script joins each unique name match back to the source XML-derived `reporting_persons_json` using the selected reporting-person index. The name matcher does not consume the explicit CIK. In 13D filings where the matched reporting person has an explicit XML CIK, the candidate CIK (submission-filer CIK) was compared with that explicit CIK:

- Target-subject 13D: 57/57 matched candidates agreed (23 Q2, 34 Q3).
- Non-target 13D validation: 180/180 matched candidates agreed (90 Q2, 90 Q3).
- Combined: **237/237 exact CIK matches; zero mismatches**, across 197 distinct candidate CIKs (33 in target-subject matches and 165 in non-target matches).

This is a meaningful validation of the frozen exact-name link in the tested 13D subset. It is not proof that all 13G candidate links are correct, and it is not an economic-group key. The 13G schema's `reportingCik` field was absent for all 480 target-subject 13G filings and all 200 non-target 13G validation filings in these quarters; consequently 13G match rates above are **coverage only**, not measured precision. In a multi-person filing, a matched filer identifies at most one reporting person; it does not identify the remaining persons or prove a common beneficial-ownership group.

The CIK validation is conditional on unique name matches and the available explicit-CIK subset. It does not validate unmatched records or establish historical stability before these quarters. The crosswalk remains an identity candidate with provenance, not a production economic-group resolver.

## Reporting-group and amendment limitations

- Among the 480 target-subject 13G filings, 337 had all `memberGroup` markers missing, 134 had all persons marked “b”, and 9 had all persons marked “a”. No mixed/partial marker pattern appeared in this sample. This does not establish a common economic group; the marker is not used as a substitute for a verified relationship.
- Target-subject amendments: Q2 had 226 amendments (22 13D/A + 204 13G/A), with 93 explicit `previousAccessionNumber` pointers; Q3 had 180 amendments (30 13D/A + 150 13G/A), with 104 pointers. Combined: 197/406 (48.52%) have an explicit pointer and 209/406 do not.
- `amendmentNo` was present for all 406 target-subject amendments. It is useful metadata but does not by itself identify the immediately preceding filing. A `previousAccessionNumber` may point to the root/original accession rather than the immediately prior amendment.
- The filing date from the global master index remains KnowledgeDate. Signal date must be strictly later. `event_date_raw` is not KnowledgeDate; accepted timestamps are not used.

## Reproducibility

Added:
- `research/phase35_13dg_crosswalk_precision_validation.py`
- `research/test_phase35_13dg_crosswalk_precision_validation.py`

The validator checks the selected person index against source XML JSON, validates explicit CIK equality only for 13D, and reports 13G as coverage-only. Five unit tests pass. The Q2/Q3 artifact analysis produced `PASS`, 941 audited crosswalk rows, 237 explicit 13D CIK comparisons, 237 matches, and zero mismatches.

## Next gates

1. Keep the crosswalk algorithm frozen and validate it on 2025Q4 and 2026Q1. Do not add aliases or fuzzy rules after observing these results.
2. Preserve unique name matches as candidate person-level links with provenance; unresolved matches remain null. Do not infer complete groups from the matched filer.
3. Reconstruct amendments using exact predecessor pointers where available; for missing pointers, only use a separately pre-registered issuer + security class/CUSIP + person identity rule when exactly one predecessor exists. Otherwise mark unresolved/left-censored.
4. Build a point-in-time historical ticker/CIK/CUSIP/listing-status panel; resolve or explicitly exclude the 27 current ticker-map gaps without survivorship filtering.
5. Extend legacy HTML/TXT subject-issuer parsing for filings before structured XML became mandatory, with separate validation against SEC filing detail metadata.
6. Only after identity, lineage, historical-universe, and ex-ante KnowledgeDate gates pass, test 13D and 13G hypotheses separately against frozen LTM/F80 using chronological OOS, identical costs/exposure, bootstrap, and LOO.

No forward returns were used. No alpha is claimed. `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen.
