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
- `phase91_filing_events.csv` (filing-level accession, event date, lag, acceptance UTC and identity fields; used to review long-lag outliers)
- `phase91_reporting_person_identity.csv`

The workflow is offline and consumes only the immutable Phase 84 artifact.


## Phase 91 first execution — run 41933908787 (failed gate, diagnostic retained)

- The 9 new unit tests and the existing parser regression suites passed.
- The first audit script incorrectly attempted XML extraction from all 600 13D/13G submissions. Four hundred legacy HTML/TXT submissions correctly had no primary_doc.xml; the script misclassified those expected legacy rows as parse errors. This is an implementation defect, not a source-coverage failure.
- Despite the false failure status, 200 structured XML filings were parsed and all 470 reporting-person rows were retained. Diagnostic results: 86/121 first 13G reporting-person names (71.07%) exactly matched SEC-HEADER FILED BY after conservative normalization; 35/121 did not. All 89 additional 13G reporting-person rows remained unresolved because no explicit CIK/no-CIK tag was present. The 86 CIKs remain candidates, not verified identities.
- The first run's 19 lag strata are descriptive only. They show why the pooled Phase 90 medians should not be interpreted as comparable signal latency: in mandatory-XML 13G Rule 13d-1(b) originals, sample medians were 31–38 days by candidate class; Rule 13d-1(c) originals had a control-sample median of 7 days (n=7); mandatory-XML 13D amendments had medians of 1–2 calendar days (n=19 per candidate class). These cells are small, unweighted, and not compliance tests or alpha evidence.
- Root cause fixed in the next commit: skip non-XML legacy 13D/G after verifying their raw hash and SEC header; only parse rows marked XML-present by the immutable Phase 84 header-validation manifest. The corrected replay also checks 600/600 raw hashes/header timestamps, 192/192 mandatory XML by actual SEC-HEADER form/date, and 200/200 XML subject/filer/form concordance.


## Corrected replay result — run 41934097112

<badge>DATA REPLAY COMPLETE</badge>

The corrected workflow explicitly skips legacy HTML/TXT filings after validating their raw hash and SEC header. It does not attempt to parse XML where the Phase 84 header-validation manifest records no XML.

| Control | Result |
|---|---:|
| Raw submissions and SHA-256 verified | 600/600 |
| SEC acceptance timestamps converted | 600/600 |
| Mandatory XML, using actual SEC-HEADER form/date | 192/192 |
| Structured XML filings parsed | 200/200 |
| XML subject vs SEC-HEADER SUBJECT COMPANY | 200/200 |
| XML filer vs SEC-HEADER FILED BY | 200/200 |
| XML form vs SEC-HEADER form | 200/200 |
| Reporting-person rows retained | 470 |
| Lag strata produced | 19 |
| Errors | 0 |

The original Phase 84 live run remains a failed run under its original denominator (192/193). Phase 89 corrected the denominator using the actual SEC-HEADER form/date, and Phase 91 independently revalidated the 192/192 mandatory-XML population. Do not rewrite the original run's conclusion.

### 13G reporting-person CIK semantics

The 121 Schedule 13G filings contain 210 reporting-person rows. No explicit `reportingCik` or `reportingCikNotPresentInEdgarFlag` elements were present in the sampled person nodes. The SEC Filer Manual (Volume II, 2026-03-16) states that the Filer CIK pre-populates the first reporting person's CIK/name; additional persons enter their own CIKs if available, and the no-CIK checkbox does not apply to the first person.

The Phase 91 audit therefore distinguishes:

| 13G reporting-person status | Count |
|---|---:|
| First person; FILED BY name exactly matches | 86 |
| First person; FILED BY name does not exactly match | 35 |
| Additional persons; CIK unresolved | 89 |
| **Total** | **210** |

- Exact normalized FILED BY/first-person name match: 86/121 (71.07%).
- The 86 Filer CIKs are **candidates**, not independently verified reporting-person identities. They are not marked resolved and are not used as economic-group keys.
- The 35 first-person mismatches remain unresolved.
- The 89 additional persons do not inherit the Filer CIK and remain unresolved unless a separate explicit CIK/no-CIK field is available.

This supersedes Phase 90's broader phrase that all 210 13G persons are name/type-only. The accurate statement is: no explicit person-level CIK/no-CIK tags appeared in this sample; the first-person CIK may be inherited from the Filer CIK under the SEC form-entry convention, but our conservative parser only records a candidate after exact name concordance.

### Filing-minus-event lag by legal regime

The Phase 90 pooled medians (13D 3 days; 13G 34 days) are not comparable as a stable difference in information speed. The SEC rule changed at different dates for the two families:
- 13D rule amendments effective 2024-02-05; initial Schedule 13D within five business days and material amendments within two business days.
- Revised 13G deadlines applied only from 2024-09-30; before then, legacy deadlines remained in force.
- Structured XML became mandatory 2024-12-18 (voluntary from 2023-12-18).
- Under revised 13G rules, Rule 13d-1(b)/(d) initial filings generally use a 45-day quarter-end deadline, with accelerated threshold provisions; Rule 13d-1(c) passive initial filings use five business days. Amendments have a 45-day quarterly rule plus faster threshold-specific rules.

Official final rule: https://www.sec.gov/file/33-11253 (effective/compliance dates and amended Rules 13d-1/13d-2).

Selected unweighted sample medians (calendar days), split by candidate class:

| Filing stratum | Candidate class | n | Median lag |
|---|---|---:|---:|
| 13D mandatory-XML originals | Control | 20 | 7 |
| 13D mandatory-XML originals | Unique candidate | 20 | 6 |
| 13D mandatory-XML amendments | Control | 19 | 1 |
| 13D mandatory-XML amendments | Unique candidate | 19 | 2 |
| 13G mandatory-XML Rule 13d-1(b) originals | Control | 9 | 31 |
| 13G mandatory-XML Rule 13d-1(b) originals | Ambiguous | 19 | 38 |
| 13G mandatory-XML Rule 13d-1(b) originals | Unique candidate | 19 | 36 |
| 13G mandatory-XML Rule 13d-1(c) originals | Control | 7 | 7 |
| 13G mandatory-XML Rule 13d-1(d) originals | Control | 3 | 13 |
| 13G mandatory-XML Rule 13d-1(b) amendments | Control | 13 | 21 |
| 13G mandatory-XML Rule 13d-1(b) amendments | Ambiguous | 19 | 27 |
| 13G mandatory-XML Rule 13d-1(b) amendments | Unique candidate | 18 | 23.5 |
| 13G mandatory-XML Rule 13d-1(c) amendments | Control | 3 | 48 |
| 13G mandatory-XML Rule 13d-1(d) amendments | Control | 3 | 45 |

The 13D original control stratum contains one 290-calendar-day outlier (n=20); the unique-candidate maximum is 14 days. That outlier requires document-level review before any event-lag feature is considered. Rule designation alone also does not reveal whether a faster threshold trigger applied. These are not legal-compliance tests.

### Decision

- Phase 91 data replay: **PASS**.
- 13G first-person CIK: partially recoverable as a candidate, not fully resolved.
- 13G additional-person identity: unresolved.
- 13D/13G event-date lag: legal-regime-confounded; do not use pooled lag as an information-speed signal.
- Amendment-chain completeness: still fails the Phase 90 feasibility threshold (51/97 amendments lacked explicit previousAccessionNumber).
- No forward returns, no alpha test, no economic inference, no purchases, no production changes.


## Filing-level outlier review preparation

The corrected replay now exports `phase91_filing_events.csv` in addition to grouped lag strata. This is required to identify and inspect the 290-day 13D original control outlier and the 13G long-lag observations without inferring their accessions from aggregate statistics. The export preserves accession, subject/filer CIK, event date, filing date, acceptance UTC, rule designation and candidate class. No outlier is dropped or winsorized.
