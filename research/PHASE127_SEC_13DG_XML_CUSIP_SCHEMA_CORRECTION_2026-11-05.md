# Phase 127 — SEC 13D/G XML CUSIP schema correction

**Date:** 5 November 2026  
**Status:** PASS — artifact-only re-adjudication validated by GitHub Actions.

## Root cause

Phase 125's XML extractor recognized only the `issuerCusip` element. A newer SEC 13D/G XML structure stores the value as `issuerCusips/issuerCusipNumber` under `issuerInfo`. The old extractor therefore treated populated XML fields as missing. This was a schema-parser defect, not missing SEC data.

The corrected extractor supports both tags, scopes extraction to `issuerInfo`, deduplicates identical values, and marks multiple distinct CUSIPs as ambiguous rather than choosing one. Zero placeholders, bad check digits and malformed lengths remain separate statuses.

## Corrected sample results

The same immutable Phase 124 artifact was reprocessed; no new SEC requests were made. There are 599 actual 13D/G filings after one non-13D/G index alias is quarantined.

| Population | Checksum-valid CUSIPs | Post-stratified weighted valid rate |
|---|---:|---:|
| Legacy HTML | 473/497 | 96.84% |
| Structured XML | 98/102 | 97.38% |
| All actual 13D/G filings | 571/599 | 96.94% |

Corrected statuses across 599 actual filings:

- 571 unique checksum-valid CUSIPs.
- 23 missing values, all in legacy HTML.
- 2 explicit zero placeholders (`000000000`).
- 2 unique values with invalid check digits.
- 1 malformed 10-character value.
- 0 ambiguous multi-CUSIP rows.

The 32 XML rows previously labelled missing are now resolved: 30 have unique checksum-valid values; one is a zero placeholder; one is a malformed 10-character value. The corrected weighted XML valid rate is 97.38%, replacing Phase 125's 66.71%; the overall weighted rate is 96.94%, replacing 91.36%.

The post-stratified weight mass across the 599 actual filings is 323,804; the weighted valid-CUSIP mass is approximately 313,896.44. These are descriptive sample estimates across 172 quarter × form × amendment strata, not a formal confidence interval or proof of full-universe coverage.

## Limits and decision

A valid check digit does not prove that the CUSIP is the correct security identifier, that it was valid at the filing date, or that it maps to a currently traded ticker. CUSIP is not permanent. Effective-dated issuer, share-class, ADR, successor, corporate-action and delisting-aware crosswalks remain required. The sample is drawn from the filing index, not a historical eligible-security universe. No forward-return or alpha test was performed.

**Decision:** pass the structured/legacy CUSIP extraction feasibility gate for this sample; keep permanent security identity, historical universe membership, reporting-person/group normalization and dissemination-time validation open. Do not start returns testing yet. `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen.

## Reproducibility

- [Phase 124 immutable sample run](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42073725379)
- [Phase 125 prior audit run](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42077788015)
- [Corrected auditor](phase125_sec_13dg_exact_cusip_audit.py)
- [Regression tests](test_phase125_sec_13dg_exact_cusip_audit.py)


- [Phase 127 Actions run](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42079517644)
- Artifact: `13438903901` (90-day retention).
- Final CI: 15 Phase 124 tests and 21 Phase 125 tests passed; 600/600 raw submission hashes/identity checks verified; no audit errors.

- Artifact ZIP SHA-256: `b80d15d736ba6c45f4f3c5dd569604175e221414b31a28fd58a62010a805c166`.
