# Phase 213 — SEC 13D/G legacy event-date and amendment-marker audit

**Date:** 2026-11-08  
**Disposition:** completed document-normalization audit; no alpha admission.

## Executive result

A hash-pinned, stratified sample of 599 actual Schedule 13D/G submissions was reprocessed from the original SEC submission text. Recovering event dates from the primary legacy HTML cover pages increased usable event-date coverage from the 102 structured-XML rows to **553/599 (92.32%)**. The sample-weighted descriptive coverage is 91.69%; because missingness is format-dependent, this is not a complete population estimate.

The key finding is semantic, not predictive: **13D and 13G event dates behave differently and neither is the public-knowledge timestamp.** Schedule 13G event dates are frequently quarter-end reporting references. Schedule 13D dates are much less often quarter-end, but can be stale by many months. Both must be separated from the SEC acceptance clock.

## Provenance and integrity

- Source run: 42073725379; artifact: 13436764625; GitHub artifact digest: SHA-256 85f69e083b5af65731c9bcfe24e8c75821fc0f2c2476bfa8ba573e2e884570dc.
- The source workflow concluded **failure (exit code 2)** even though its summary status was PASS_WITH_INDEX_ALIAS_QUARANTINE. The summary records 599 actual 13D/G submissions validated, one non-13D/G index alias quarantined and zero download/mirror failures. The artifact was uploaded despite the failed job.
- This phase independently verified the CSV SHA-256, all 600 raw-submission SHA-256 values, all 600 SEC-header accession/acceptance/filing-date fields and all 599 primary 13D/G documents.
- The 102 structured XML event dates match the Phase 124 event-date field exactly (102/102). Structured amendment-number presence/value also matches the Phase 124 field exactly, including absent values (102/102).
- The legacy HTML extraction was manually spot-checked across 24 documents spanning SC 13D, SC 13D/A, SC 13G and SC 13G/A. The rule is deliberately conservative: extract the date nearest the cover-page event-date label; do not infer from a standalone date near a CUSIP.

## Event-date recovery

| Family | Actual sample | Parsed | Unweighted coverage | Sample-weighted coverage | Quarter-end event date, weighted among parsed | Median filing minus event date | Maximum lag |
|---|---:|---:|---:|---:|---:|---:|---:|
| 13D | 214 | 205 | 95.79% | 96.04% | 2.63% | 4 days | 921 days |
| 13G | 385 | 348 | 90.39% | 90.73% | 76.44% | 31 days | 379 days |
| Total | 599 | 553 | 92.32% | 91.69% | — | — | — |

Methods: 451 HTML cover-page dates, 34 structured 13D dateOfEvent tags and 68 structured 13G eventDateRequiresFilingThisStatement tags. Forty-six actual submissions remain unresolved: 35 have no recognized label and 11 have a label but no unambiguous four-digit-year date. These are not imputed.

The 13D tail matters: 19/205 parsed dates are more than 30 calendar days before filing, 12 are more than 90 days before filing and two are more than 365 days before filing. The 13G sample has 175/348 over 30 days, seven over 90 days and one over 365 days. The event-date field therefore cannot be treated as a trade date or a reliable acquisition timestamp.

## Filing-rule regime is a measurement break

The SEC's 2023 beneficial-ownership reporting amendments shortened initial Schedule 13D filing to five business days and Schedule 13D amendments to two business days. Revised Schedule 13G deadlines began September 30, 2024; structured-data compliance began December 18, 2024. QIIs and exempt investors generally report against quarter-end, while passive investors have a different event-driven deadline. See the [SEC adopting announcement](https://www.sec.gov/newsroom/press-releases/2023-219), [Release 33-11253](https://www.sec.gov/files/rules/final/2023/33-11253.pdf) and [SEC Regulation 13D-G interpretations](https://www.sec.gov/rules-regulations/staff-guidance/corporation-finance-interpretations/exchange-act-sections-13d-13g-regulation-13d-g-beneficial-ownership-reporting).

Descriptive sample results around the compliance cutoffs:

- 13D filings before February 5, 2024: 154/162 event dates parsed; median filing/event gap 5 days. On/after the cutoff: 51/52 parsed; median 4 days.
- 13G filings before September 30, 2024: 272/308 parsed; weighted quarter-end share 74.80%; median gap 25.5 days. On/after the cutoff: 76/77 parsed; weighted quarter-end share 81.73%; median gap 38 days.

These are small-sample descriptions, not tests of compliance, causal effects or alpha. For the 68 structured-XML 13G records only, rule designations were 44 Rule 13d-1(b), 15 Rule 13d-1(c) and nine Rule 13d-1(d); their sample-weighted quarter-end shares were 85.80%, 73.84% and 55.60%, respectively.

## Amendment identity is not a single field

The index form suffix, the cover-page amendment number and the structured XML amendmentNo are separate observations.

- 371 submissions have an index form suffix ending in /A.
- A positive cover-page/XML amendment number was recovered on 376 rows; four explicit zero values and 219 missing values remain separate.
- Legacy HTML yielded 321 numeric amendment numbers, 123 amendment labels without a numeric value and 53 documents without a recognized amendment label.
- Structured XML contains amendmentNo on 59 rows and no such tag on 43; all 102 agree with the Phase 124 field.
- Eleven submissions whose index form lacks /A nevertheless show a positive cover-page amendment number. Six /A submissions have no positive cover-page/XML amendment number.

Missing is not zero. Do not collapse the index suffix and document-level amendment marker into a single original/amendment flag. This is especially important before reconstructing ownership state or interpreting stale event dates.

## PIT and research decision

- The cover-page event date is not the public-knowledge timestamp.
- Retain SEC-header ACCEPTANCE-DATETIME as the filing-availability clock; it is preserved as the header wall-clock, with no timezone conversion or claim of exact dissemination time.
- For a daily strategy, do not use the same session. The earliest candidate is the next full regular session after acceptance, pending separate dissemination and security-identity validation.
- Keep 13D and 13G separate. Do not treat a 13G quarter-end date as an institutional purchase date.
- Preserve index /A and document amendment markers separately. Do not infer immediate amendment lineage from previousAccessionNumber; Phase 160/163 did not validate it as an immediate-predecessor edge.
- CUSIP still requires effective-dated issuer/class/corporate-action mapping, and the historical active/delisted investable universe remains unbuilt.

**No forward returns, features, alpha tests, bootstrap/LOO, OOS tests or holdout were used.** No production or universe changes were made. F80 remains frozen.

## Reproducibility

- Auditor: research/phase213_13dg_legacy_event_date_recovery.py
- Tests: research/test_phase213_13dg_legacy_event_date_recovery.py
- Result: research/phase213_13dg_event_date_recovery_result.json
- Hosted workflow: .github/workflows/phase213_sec_13dg_legacy_event_date_recovery.yml
- The workflow downloads the immutable Phase 124 artifact by run ID and artifact name, verifies CSV/raw hashes, reruns the audit and uploads the row-level event-date output plus summary JSON.
