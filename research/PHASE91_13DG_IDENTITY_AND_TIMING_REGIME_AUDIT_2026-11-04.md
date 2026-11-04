# Phase 91 — SEC 13G first-person CIK semantics and 13D/13G timing-regime audit

**Date:** 2026-11-04  
**Branch:** `phase91-13dg-implicit-cik-and-regime-audit`  
**Input:** immutable Phase 84 raw-submission artifact, run 41914491120 / artifact 13364856424  
**Mode:** offline only; no SEC requests, no forward returns

## Why this phase exists

Phase 90 correctly observed that the 121 sampled Schedule 13G XML documents contained no explicit `reportingCik` or `reportingCikNotPresentInEdgarFlag` tags in the reporting-person nodes. It then described all 210 13G reporting-person rows as name/type-based. That conclusion is too strong without considering EDGAR's form-entry semantics.

The SEC EDGAR Filer Manual, Volume II (March 16, 2026), says:
- The Filer CIK pre-populates the CIK and name of the first Schedule 13G reporting person.
- For additional reporting persons, the filer enters each additional CIK if available.
- The no-CIK checkbox is not applicable to the first reporting person.

Official source: https://www.sec.gov/files/edgar/filermanual/efmvol2-c8.pdf (Schedule 13G, around pp. 8-38 to 8-40; lines 1052-1083 in the SEC HTML text).

Therefore, absence of a dedicated CIK tag in the first 13G reporting-person node does **not** prove that the first person has no CIK. It may be represented by the filing's Filer CIK. However, the Filer CIK is not automatically promoted to a person identity: this phase labels it a candidate only when the SEC-HEADER FILED BY name exactly matches the first reporting-person name after conservative case/punctuation normalization. The candidate remains unresolved pending independent entity verification. Additional persons never inherit the Filer CIK.

## Regulatory timing regime correction

The SEC's 2023 final rule (Release 33-11253 / 34-98704) creates different effective dates and filing deadlines:
- Rule amendments effective February 5, 2024.
- Schedule 13D initial deadline shortened to five business days; material amendments to two business days.
- Revised Schedule 13G deadlines did not apply until September 30, 2024; the legacy 13G deadlines continued through September 29, 2024.
- Structured 13D/G XML became mandatory December 18, 2024; voluntary compliance began December 18, 2023.

Official source: https://www.sec.gov/file/33-11253 (especially the summary/table and compliance-date section).

The Phase 90 pooled medians (13D 3 days versus 13G 34 days) are not comparable as if they represented a stable difference in investor information speed. They mix different legal regimes, 13G rule designations, original/amendment filings, and a stratified candidate/control sample. Phase 91 reports filing-minus-reported-event lags separately by family, regulatory regime, amendment status, 13G rule designation, and candidate class. These are unweighted sample diagnostics only; no population inference or confidence interval is claimed.

## Preregistered diagnostics

1. Re-read all 600 raw submissions from the immutable Phase 84 artifact and verify SHA-256 against its header-validation manifest.
2. Reparse the 200 structured XML filings; reconcile XML subject/filer CIK and form family against SEC-HEADER.
3. For each 13G reporting person, distinguish explicit CIK, explicit no-CIK, first-person Filer-CIK candidate with exact name concordance, first-person unresolved, and additional-person unresolved.
4. Preserve the first-person candidate CIK as a candidate field only; do not mark it resolved and do not use it as an economic-group key.
5. Recompute event-date lag from XML event date and SEC header filing date; verify the stored sample timing regime against filing-date cutoffs.
6. Report lag distributions by family × timing regime × original/amendment × 13G rule designation × candidate class.
7. Preserve SEC-HEADER ACCEPTANCE-DATETIME as the knowledge timestamp. Event date is never the public-knowledge timestamp.

## Regime boundaries encoded

| Family | Legacy deadline regime | Revised deadline, pre-mandatory XML | Mandatory XML |
|---|---|---|---|
| 13D | Before 2024-02-05 | 2024-02-05 to 2024-12-17 | From 2024-12-18 |
| 13G | Before 2024-09-30 | 2024-09-30 to 2024-12-17 | From 2024-12-18 |

"Pre-mandatory XML" may include voluntary XML filings; it does not mean the source was necessarily unstructured.

## Interpretation limits

- A Filer-CIK candidate is not an independently verified reporting-person CIK.
- No CIK from the submission filer is assigned to additional reporting persons.
- Rule designation is a filing category, not proof of institutional sophistication or informed trading.
- Filing-minus-event lag is descriptive and affected by legal deadlines and event-date semantics.
- Candidate-class quotas make pooled medians sample-design-dependent; no unweighted pooled result is described as a population estimate.
- No forward returns, feature construction, predictive hypothesis, economic test, purchase, or production change is authorized.
- Historical F80 issuer/security lineage and point-in-time universe membership remain unresolved.

## Expected outputs

- `phase91_summary.json`
- `phase91_filing_lag_strata.csv`
- `phase91_reporting_person_identity.csv`

The workflow is offline and consumes only the immutable Phase 84 artifact.
