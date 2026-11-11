# Phase 298 — SEC Form 4/A cross-quarter parent-lineage live audit

**Date:** 2026-11-11 UTC  
**Branch:** `phase298-form4a-crossquarter-lineage-live-audit`  
**Workflow:** [43101285104](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43101285104) — success  
**Artifact:** [13891901486](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43101285104/artifacts/13891901486), SHA-256 `f7c630b8e0cbabba5fd41f25fc09777fbed8fbaa49c309fc8003b14cb880ae0e`, 20,464,785 bytes  
**Method:** rerun the existing Phase 153 candidate-parent and multiset line-diff auditor against a complete immediate-prior-quarter window for each endpoint sample. No model or return test.

## Executive result

The previous Phase 153 preflight was blocked because the adjacent-quarter SEC ZIPs could not be retrieved with the then-missing User-Agent contact. The repository secret `SEC_CONTACT_EMAIL` is now injected successfully by GitHub Actions. The live workflow retrieved and CRC-checked both adjacent-quarter archives:

| Quarter | Form 4 / 4-A accessions | ZIP bytes | SHA-256 |
|---|---:|---:|---|
| 2011Q4 | 39,760 | 8,958,649 | `47f35cc68de7c43c7ab7dd86f00a8c9e5f5aa1f4bca0ea859b903d17f198e0b8` |
| 2026Q2 | 50,545 | 11,498,860 | `11f1b2bbbdcbe6347a34437c02d04202fda0eca1dbb023726e4b56504b802e27` |

The endpoint-quarter inputs 2012Q1 and 2026Q3 were taken from the immutable Phase 294 artifact and their previously recorded SHA-256 hashes were verified before analysis.

**Candidate-parent coverage increased materially when the immediately preceding quarter was included:**

| Target amendment quarter | Form 4/A count | Same-quarter unique candidates | Added prior-quarter candidates | Total unique candidates | Candidate coverage | Ambiguous | No candidate in two-quarter window |
|---|---:|---:|---:|---:|---:|---:|---:|
| 2012Q1 | 1,862 | 1,146 | 209 (2011Q4) | **1,355** | **72.7712%** | 44 | 463 |
| 2026Q3 | 627 | 341 | 177 (2026Q2) | **518** | **82.6156%** | 8 | 101 |

Relative to the same-quarter-only Phase 152/153 baselines, the immediate prior-quarter data add 209 unique candidates in 2012Q1 (+11.2245 percentage points) and 177 in 2026Q3 (+28.2296 percentage points).

The search windows are complete only for the target quarter plus its immediately preceding quarter. They are not complete accession histories: an original filed earlier than that window can still explain a no-candidate case.

## Owner-set diagnostics

Of the unique candidate links:

| Target | Exact reporting-owner set | Partial owner overlap |
|---|---:|---:|
| 2012Q1 | 1,349 | 6 |
| 2026Q3 | 511 | 7 |

The candidate rule is unchanged: same issuer CIK, `DATE_OF_ORIG_SUB` equal to an original Form 4 `FILING_DATE`, at least one shared reporting-owner CIK, and parent filing date no later than amendment filing date. Form 4/A filings are not eligible as parents.

An exact owner-set match improves plausibility but does not establish a parent-accession foreign key. A shared owner can appear in more than one filing, and the flat bulk tables still do not identify which owner owns each transaction line.

## Candidate-only transaction-line differences

The existing multiset comparison excludes footnote references and row surrogate keys. Exact matches are counted as repeated candidate rows; same-coarse unmatched rows remain ambiguous; different-coarse-key rows are only candidate additions. Parent rows not repeated are not called deleted.

| Target | Table | Parent rows | Amendment rows | Exact repeated | Same-coarse unmatched | Distinct-coarse candidate additions | Parent rows not repeated |
|---|---|---:|---:|---:|---:|---:|---:|
| 2012Q1 | Table I | 2,251 | 1,713 | 453 | 980 | 280 | 823 |
| 2012Q1 | Table II | 1,229 | 884 | 326 | 385 | 173 | 519 |
| 2026Q3 | Table I | 929 | 791 | 226 | 306 | 259 | 404 |
| 2026Q3 | Table II | 370 | 323 | 84 | 144 | 95 | 145 |

These totals cover only the unique heuristic candidate links. They are not final amendment-state or event-flow counts. In particular, a distinct-coarse candidate addition is not yet a confirmed new trade, and a same-coarse unmatched row may be a changed line or a new line.

## Positive control

The known Eton Pharmaceuticals pair remains correctly linked:

- Original Form 4: `0001437749-26-029196`
- Form 4/A: `0001437749-26-029308`
- Table I: four exact repeated candidate rows and one same-coarse unmatched row.
- Table II: one exact repeated candidate row and one same-coarse unmatched row.

The same-coarse rows are deliberately not forced into “new transaction” classification.

## Validation and controls

- Existing Phase 153 regression suite: **17/17 tests passed**.
- The final hosted Phase 298 workflow completed successfully.
- First attempt stopped before any SEC request because a locally authored SHA-256 checksum line had an invalid length. The digest was corrected, and the successful rerun verified the immutable Phase 294 artifact plus both endpoint-quarter hashes before making SEC requests.
- The configured SEC contact secret was present in the workflow environment and used only in the SEC User-Agent. No email was sent.
- Raw 2011Q4 and 2026Q2 ZIPs and the JSON result are preserved in the Phase 298 artifact. The 2012Q1 and 2026Q3 raw ZIPs remain in Phase 294 artifact [13884014630](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43083625013/artifacts/13884014630).

## Decision

**The adjacent-quarter download blocker is resolved, and cross-quarter matching materially improves candidate coverage. Form 4/A parent lineage is still not admitted for event-flow modeling.**

The remaining 463 and 101 no-candidate cases may have parents earlier than the one-quarter lookback; 44 and 8 cases remain ambiguous. Even a unique candidate can be wrong because the SEC bulk dataset has no authoritative parent accession foreign key and the owner relationship is accession-level, not transaction-line-level.

Next gate: select a deterministic, stratified sample of same-quarter and adjacent-quarter candidate pairs; retrieve the original and amended EDGAR submissions; validate issuer, accession, original-submission date and reporting-owner identities against the filing headers/XML; then manually adjudicate line-level repeats, changes, additions and retractions. Do not build event flow from the candidate diff until this validation passes.

No forward returns, alpha, strict-PIT admission, bootstrap/LOO, chronological OOS or holdout test was run. `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen. Production, universe, capital and parameters are unchanged. No PR was opened or merged.
