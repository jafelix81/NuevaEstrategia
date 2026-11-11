# Phase 301 — 2023Q2 Form 4/A intermediate-era lineage and XML source audit

**Date:** 2026-11-11 UTC  
**Branch:** `phase301-form4a-intermediate-era-lineage-audit`  
**Final workflow:** [43121592821](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43121592821) — success  
**Artifact:** [13901611120](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43121592821/artifacts/13901611120), 33,283,603 bytes, SHA-256 `5840790fac1d411f95dad60737e68d9a6bc26d08380a7be9b8d1d18d74b51333`  
**Scope:** extend Phase 300 XML validation to the intermediate 2023Q2 cohort, include the 2022Q4 parent-search quarter, and deliberately sample ambiguous, no-owner-overlap and no-parent cases. No return or alpha test.

## Executive result

The final run downloaded three official SEC Form 345 bulk archives directly from EDGAR, validated their ZIP CRCs and required tables, and reconciled 102 original EDGAR submission documents against the bulk rows.

**All 102 documents downloaded, parsed, passed header/XML identity checks, and matched bulk/XML transaction-row counts. All 102 also matched the Phase 300 core transaction signature.** The broader signature matched 98/102 documents; the four exceptions are confined to `NATURE_OF_OWNERSHIP` and/or `TRANS_TIMELINESS`, not transaction economics or direction.

The target 2023Q2 population contains 937 Form 4/A accessions with a usable original-submission date and at least one reporting owner:

| Linkage status within 2022Q4–2023Q2 search window | Count | Share |
|---|---:|---:|
| Unique issuer/date/owner-overlap candidate | **719** | **76.73%** |
| Multiple owner-overlap candidates | 24 | 2.56% |
| Same issuer/date candidate(s), no owner overlap | 15 | 1.60% |
| No Form 4 parent candidate in loaded quarters | 179 | 19.10% |
| **Total** | **937** | **100.00%** |

Adding 2022Q4 to the 2023Q1–Q2 window increased unique candidates from 697 to 719 (+22; +2.35 percentage points) and reduced the no-parent-in-window count from 202 to 179. One additional case fell into the same-issuer/date but no-owner-overlap category. This is a meaningful coverage improvement, not proof that every candidate is the true parent.

## Source archive audit

| Quarter | Form 4 / 4-A accessions | Bytes | SHA-256 |
|---|---:|---:|---|
| 2022Q4 | 35,550 | 8,400,983 | `6c6a909bd2eaaa0a24ccf5f0071b404670c115845d2939bc592bf3ce420dcdb9` |
| 2023Q1 | 63,844 | 13,882,049 | `0b476188f52a0862e71886eb31a81f6345fc6616403b52188484aef0438cfcfb` |
| 2023Q2 | 51,791 | 10,742,628 | `7e636787231ae0f00accf5c3627298402dedd1aefffd7c50fb48292e5d3a8fbb` |

All three downloads returned HTTP 200 on the first attempt. The archives passed ZIP CRC and required-table checks. The 2023Q1 and 2023Q2 SHA-256 hashes match the immutable Phase 294 samples.

## Deterministic EDGAR XML sample

The 52 selected cases comprise:

| Case type | Sample cases | Result |
|---|---:|---|
| Unique owner-overlap candidates | 24 | **24/24** corroborated by original/amended XML metadata |
| Ambiguous multiple owner-overlap candidates | 8 | 8/8 remain ambiguous after XML checks |
| Same issuer/date, no owner overlap | 8 | 8/8 reproduce no overlap among the sampled parent documents |
| No parent in loaded quarters | 12 | 12 remain unresolved within the three-quarter window |

The 24 unique sample pairs span all three parent quarters: six from 2022Q4, ten from 2023Q1 and eight from 2023Q2. They include exact-only, same-coarse, distinct-coarse and mixed candidate line-difference strata, with exact and partial owner-set cases represented.

The no-parent sample includes five original dates older than 2022Q4, five within 2023Q1/Q2 and two within 2022Q4. “No parent” means no matching Form 4 was found in the loaded 2022Q4–2023Q2 archives; it does not mean no parent exists elsewhere in EDGAR.

Two of the eight no-owner-overlap sample cases had 15 same-issuer/date candidate documents. To bound the document sample, the workflow downloaded the first 12 deterministic candidates for each and marked those cases as truncated. Their result is therefore a sampled-candidate check, not an exhaustive review of all 15 documents.

## XML-to-bulk fidelity

| Check | Result |
|---|---:|
| Documents downloaded | 102/102 |
| XML parse success | 102/102 |
| Header/XML identity pass | 102/102 |
| Table I / Table II row counts match | 102/102 |
| Core transaction multiset match | **102/102** |
| Full transaction signature match | 98/102 |

The four full-signature exceptions were inspected against the raw EDGAR XML and bulk TSV rows:

- `0000805676-23-000087`: one Table I document; differences in `NATURE_OF_OWNERSHIP` and `TRANS_TIMELINESS`.
- `0001474506-23-000225`, `0001474506-23-000232`, `0001474506-23-000277`: three Table II documents; differences in `NATURE_OF_OWNERSHIP` (including “See footnote” text).

The underlying transaction rows, including transaction dates, codes, shares, prices/values, acquired/disposed direction and derivative underlying fields, match the core signature. These metadata fields remain visible in the full comparison and are not silently normalized away.

## Interpretation

1. The 2022Q4 lookback materially improves 2023Q2 candidate coverage.
2. The 24/24 unique sample links are corroborated by issuer identity, date-of-original-submission, owner overlap, form type and acceptance chronology in the original EDGAR documents.
3. Eight deliberately sampled ambiguous cases remain ambiguous. XML metadata does not create an authoritative parent-accession key.
4. Owner identity remains accession-level, not transaction-line-level. Multi-owner and partial-owner cases cannot be assigned to an individual transaction without additional evidence.
5. Candidate line differences are not confirmed new trades, deletions, reversals or executions.
6. Acceptance datetime is a knowledge-clock field, not exact first-public availability.

**Decision:** Form 4/A lineage is more credible for a broad historical event panel, but it is still not admitted for event-flow modeling or strict PIT. The next gate is to reconcile the 2023 sample against SEC daily-index first appearances and PAC/correction history, while extending the lookback for selected no-parent cases and preserving the unresolved/ambiguous states. Effective-dated issuer/security-class identity and frozen-universe price coverage remain required before any return test.

## Validation, controls and audit trail

- Regression tests: 17 Phase 153 + 6 Phase 299 + 6 Phase 300 + 6 Phase 301 = **35 passing tests**.
- First Phase 301 attempt [43121407654](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43121407654) stopped at the GitHub artifact-download endpoint with HTTP 401 before any SEC request. The final workflow was made self-contained by downloading the three SEC archives directly; final run 43121592821 succeeded.
- `SEC_CONTACT_EMAIL` was injected only into the SEC User-Agent. No email was sent.
- The raw quarterly ZIPs, 102 raw EDGAR submissions, sample manifest and machine-readable result are preserved in artifact 13901611120 (90-day retention).
- No alpha, forward-return, bootstrap/LOO, chronological OOS or holdout test was run. Strict PIT remains false.
- `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen. Production, universe, capital, parameters and the consumed legacy holdout are unchanged.
- No PR was opened or merged for Phase 301. PR #13 and PR #14 remain open.

## Reproducibility

- Auditor: `research/phase301_form4a_intermediate_validation.py`
- Tests: `research/test_phase301_form4a_intermediate_validation.py`
- Workflow: `.github/workflows/phase301_form4a_intermediate_validation.yml`
- Result and raw inputs: [Phase 301 artifact](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43121592821/artifacts/13901611120)
