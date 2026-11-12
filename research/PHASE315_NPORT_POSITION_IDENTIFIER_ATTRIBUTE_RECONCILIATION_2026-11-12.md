# Phase 315 — N-PORT identifier-attribute reconciliation

**Date:** 2026-11-12 UTC  
**Workflow:** [run 43163123951](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43163123951) — PASS  
**Artifact:** [13919006564](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43163123951/artifacts/13919006564)  
**Artifact SHA-256:** `2073ea5b39578e0a5fec7b838561db7f5fb917f2c45a1ef9bbaf18d1529bd1b6`

## Defect found and corrected

Phase 314's short-position parser read the SEC N-PORT `<isin>` and `<ticker>` nodes as text. In actual SEC XML, these identifiers are encoded in a `value` attribute, for example `<ticker value="AAPL"/>`. The text-only parser therefore returned blank ISIN and ticker fields.

The Phase 314 comparison key used CUSIP, so the parent-candidate result and the 20-row original/amendment comparison were not changed by this omission. However, the blank identifiers would have blocked reliable security mapping and could have contaminated any later ticker-level analysis. The parser now reads `value` first and falls back to element text; the Phase 314 fixture now uses the actual SEC attribute form.

## Reconciliation result

The immutable Phase 314 raw artifact was downloaded and its SHA-256 digest verified. All 25 candidate raw submissions were hash-verified. The corrected Phase 314 parser was cross-checked against the Phase 312 reference parser on **27 documents**: the 25 candidate originals, the target amendment and the 2023 same-series control.

| Filing vintage | Short rows | CUSIP present / valid check digit | ISIN present / valid check digit | Ticker present |
|---|---:|---:|---:|---:|
| 2022 original | 20 | 20/20 | 20/20 | 20/20 |
| 2022 amendment | 20 | 20/20 | 20/20 | 20/20 |
| 2023 same-series control | 27 | 27/27 | 27/27 | 27/27 |

The corrected parser reproduces the Phase 312 reference parser's short-position rows across all 27 documents. The 25-filing 2022 Q3 cohort still contains one short-bearing filing with 20 rows; this is a one-registrant/one-quarter cohort, not a representative prevalence sample.

## Snapshot comparison retained

The original 2022 filing and its amendment still contain exactly the same 20 qualifying short rows. The 2022 amendment versus 2023 same-series snapshot remains 23 added, 4 modified, 16 removed and 0 unchanged rows. These are snapshot differences, not trade flow.

The sum of absolute reported short value is $49,202,870.08 (25.6799 reported NAV percentage points) in the 2022 snapshot and $46,452,054.22 (32.8880 points) in the 2023 snapshot. This descriptive change is not evidence of timing, conviction, or predictive skill.

## Engineering validation

- **12/12** offline regression tests passed (8 Phase 314 + 4 Phase 315).
- 25/25 candidate raw hashes verified.
- 27/27 documents reconciled against the Phase 312 reference parser.
- All 67 position rows in the 2022 original, 2022 amendment and 2023 control were emitted with CUSIP, ISIN and ticker.
- No new SEC request was made; only the immutable Phase 314 artifact was reprocessed.

Five preliminary Phase 315 attempts failed before producing a research artifact: four from an incorrectly escaped cross-run token expression and one because direct script execution lacked the repository root on the import path. The final run corrected both. The requests dependency was installed to reuse the Phase 312 parser; no SEC request was made in any Phase 315 attempt.

## Research disposition

N-PORT remains delayed holdings context, not trade flow. A unique amendment parent is still a metadata inference rather than a direct SEC accession link. Report date is not knowledge date, and the first-public timestamp remains unproven. No effective-dated CUSIP/ISIN-to-security master or frozen-F80 universe coverage has yet been established.

Next gate: expand the audit to a multi-registrant, multi-quarter sample with P and P/A handled as separate filing vintages; preserve CIK/series/class identity and raw hashes; measure short-row incidence and identifier completeness; then build an effective-dated security crosswalk before any event study. Do not treat report-period changes as trades.

No alpha, return, bootstrap, LOO or chronological OOS test was run. No holdout was used. F80, production, universe, capital and parameters remain unchanged.
