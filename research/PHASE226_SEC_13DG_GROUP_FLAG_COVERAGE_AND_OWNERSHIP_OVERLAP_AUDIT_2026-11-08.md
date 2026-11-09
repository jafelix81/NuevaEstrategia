# Phase 226 — SEC Schedule 13D/G group-flag coverage and non-additive ownership overlap audit

**Date:** 2026-11-08  
**Status:** COMPLETED — group-flag semantics recovered; no owner-group graph or alpha feature admitted.  
**Research class:** hash-pinned source-semantics audit only.

## Executive decision

Phase 156 correctly found that reporting-person ownership rows are not safely additive, but its parser did not extract the reporting-person group checkbox. Phase 226 adds that field to the audit and shows that it provides limited contextual information, not a unique group identifier.

The structured XML uses different field names by family: **memberOfGroup** for 13D and **memberGroup** for 13G. The observed values map to the SEC cover-page row 2: **a** expressly affirms group membership; **b** disclaims group membership or describes a relationship without affirming a group. A missing value is **unreported/unknown**, not “no group”; the Schedule instructions state that row 2(b) may not be necessary in a joint filing under Rule 13d-1(k)(1). See 17 CFR 240.13d-101 and 240.13d-102.

## 1. Immutable source and integrity

- Phase 124 run: 42073725379
- Artifact: 13436764625
- Artifact ZIP SHA-256: 85f69e083b5af65731c9bcfe24e8c75821fc0f2c2476bfa8ba573e2e884570dc (verified in this run)
- CSV SHA-256: be2c592c6c26d9f1ea49bda5d29d20e944004b2e2f4a3c3f4fe1f732319c55d5 (verified)
- Index rows: 600; actual 13D/G filings: 599; one index alias remains quarantined.
- Structured XML: 102 filings (34 13D, 68 13G), across 2024Q4–2026Q3.
- All 102 XML-bearing raw submission SHA-256 values were reverified before parsing.

This is the existing stratified Phase 124 sample, not a random population census. The counts below are sample descriptions only.

## 2. Group flag coverage

| Family | Owner blocks | a affirmed | b disclaimer/relationship | Missing / unreported | Filings with a | Filings with b only | All group flags missing |
|---|---:|---:|---:|---:|---:|---:|---:|
| 13D | 152 | 31 | 65 | 56 | 4/34 | 10/34 | 20/34 |
| 13G | 158 | 2 | 43 | 113 | 1/68 | 12/68 | 55/68 |
| **Total** | **310** | **33** | **108** | **169** | **5/102** | **22/102** | **75/102** |

There were zero unexpected group-flag values. The 13G group flag is particularly sparse: 113/158 owner blocks are unreported and 55/68 filings have no group flag on any reporting-person block.

The 13G reporting-person CIK field was absent in all 158 owner blocks in this sample; 13D had a reporting-person CIK in 90/152 blocks. Group flags do not repair the permanent-identity gap.

## 3. Repeated ownership signatures remain non-additive

A repeated signature is an exact match on the six Phase 156 fields: aggregate amount, percent of class, sole/shared voting power, and sole/shared dispositive power. It is a repeated reported tuple, not a proven unique economic position.

| Family | Filings with repeats | Repeated signature groups | Owner rows inside repeated groups | Groups containing a | Groups containing b | Groups with missing flag | Mixed flags within a repeated tuple |
|---|---:|---:|---:|---:|---:|---:|---:|
| 13D | 21/34 | 26 | 94 | 5 | 9 | 12 | 0 |
| 13G | 27/68 | 32 | 95 | 1 | 11 | 20 | 0 |

All reporting-person blocks had identical ownership signatures in 9/34 13D filings and 22/68 13G filings. No repeated-signature group in this sample mixed the observed a, b and missing statuses across its member rows.

This does **not** prove that the repeated rows are one legal group, nor that different rows are independent. a is a checkbox assertion, not a group identifier; b is not an affirmative group flag; missing is not a negative. No position rows were summed.

## 4. Binding measurement rules

1. Preserve the raw family-specific group field (memberOfGroup / memberGroup) and its source value.
2. Normalize only to AFFIRMED_GROUP, DISCLAIMED_OR_RELATIONSHIP_WITHOUT_AFFIRMATION, UNREPORTED, or INVALID_OR_UNEXPECTED.
3. Never map missing to NO_GROUP.
4. Never use the group flag as a unique group key or as a reason to sum reporting-person ownership rows.
5. Keep filing-level ownership snapshots separate from reporting-person identity resolution.
6. Require a role-aware graph built from reporting-person identifiers, joint-filing agreements, relevant exhibits/comments, prior documents and effective-dated security identity before deduplicating economic ownership.
7. Preserve 13D and 13G separately; the structured sample is short and does not solve legacy HTML coverage.

## 5. Decision and next gate

**PASS:** the two group-flag fields can be extracted deterministically from the hash-pinned 102-XML sample and add a useful uncertainty label.

**NOT PASSED:** a unique reporting-person/group graph, additive ownership state, effective-dated security identity, broad historical coverage or predictive usefulness.

Next work should adjudicate a small, source-linked set of filings with joint-filing agreements and owner footnotes/comments, while preserving the raw filing and accession. The target is to learn when identical reporting-person rows are overlapping attribution versus distinct positions. Do not train an owner-resolution classifier or run returns until identity/lineage and universe gates pass.

No forward returns, alpha test, bootstrap/LOO, final-holdout use, vendor purchase, production change or F80 change occurred. F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen; the legacy holdout remains CONSUMED_NOT_PRISTINE.

## Reproducibility

- Auditor: research/phase226_13dg_group_flag_overlap_audit.py
- Tests: research/test_phase226_13dg_group_flag_overlap_audit.py
- Result: research/phase226_13dg_group_flag_overlap_audit_result.json
- Local validation: 14/14 tests passed, including full integration against the downloaded Phase 124 artifact and its SHA-256.
- No hosted Phase 226 Actions run is claimed; files are committed with skip-ci to avoid repeating the broad PR workflow fan-out.

## Official references

- SEC, [Schedule 13D & 13G Technical Specifications](https://www.sec.gov/submit-filings/technical-specifications), version 2.3 dated April 15, 2026.
- [17 CFR 240.13d-101](https://www.ecfr.gov/current/title-17/chapter-II/part-240/section-240.13d-101), cover-page row 2 instructions.
- [17 CFR 240.13d-102](https://www.ecfr.gov/current/title-17/chapter-II/part-240/section-240.13d-102), cover-page row 2 instructions and joint-filing exception.
