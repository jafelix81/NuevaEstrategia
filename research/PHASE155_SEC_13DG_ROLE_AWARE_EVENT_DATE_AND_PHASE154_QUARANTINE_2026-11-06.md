# Phase 155 — Role-aware SEC 13D/G event-date audit and Phase 154 source quarantine

**Date:** 2026-11-06  
**Status:** Completed offline, hash-pinned source reanalysis; no return or alpha test.

## Executive decision

Phase 154's form-level date analysis identified a useful difference between Schedule 13D and 13G, but its source was not a subject-issuer event panel. The Phase 35/28D artifact used by Phase 154 is generated from CIK-specific submissions queries. A known positive control in that exact artifact assigns a filing about abrdn Global Infrastructure Income Fund to Morgan Stanley (\`MS\` / CIK \`0000895421\`), the submitting filer. The SEC role-aware correction identifies the subject issuer as CIK \`0001793855\`. Therefore the 303 CIK/ticker pairs reported by Phase 154 cannot be called validated issuer identities.

Phase 155 re-ran the event-date question on the independent, globally sampled Phase 124 artifact, where SEC-header subject/filer roles and structured XML identities were reconciled. In the 102 role-validated structured XML rows with event dates:

- **13G:** 53/68 event dates (77.94%) are calendar quarter-ends; sample-weighted descriptive rate is 79.12% within this observed XML subset.
- **13D:** 0/34 event dates are quarter-ends.
- 28/34 13D and 23/68 13G acceptances occurred after 16:00 ET, reinforcing that date-only filing fields are insufficient for an end-of-day decision boundary.

This independently supports keeping 13D and 13G event-date semantics separate. It does **not** establish a predictive or economic edge.

## 1. Phase 154 source-provenance correction

Phase 154 used Phase 35 run **41575083622**, artifact **13212292743**. The source CSV has 20,265 rows, but its \`issuer_cik\` and \`ticker\` fields are inherited from the CIK-specific submissions query, not validated subject-issuer identity.

The exact row for accession \`0000895421-24-000178\` is:

| Field | Phase 35/28D row |
|---|---|
| ticker | MS |
| source/query CIK | 0000895421 |
| form | SC 13G |
| filing date | 2024-02-12 |
| primary document | \`abrdnGlobalASGI.txt\` |
| event date | 2024-12-31 |

The independent SEC role-aware positive control in Phase 96 identifies:
- submitting filer CIK: \`0000895421\` (Morgan Stanley);
- subject issuer CIK: \`0001793855\` (abrdn Global Infrastructure Income Fund);
- the 2025 amendment points back to this 2024 accession.

This is a confirmed filer-versus-subject mismatch in the exact Phase 154 input artifact. It invalidates issuer-level attribution for the entire Phase 35/28D panel unless every row is rebuilt and role-validated. The artifact remains useful only as a CIK-submissions discovery/filer-side diagnostic.

Additional Phase 35/28D defects:
- \`report_date\` is missing in **20,265/20,265** rows.
- \`filing_lag_business_days\` contains only \`-1\` (19,538), \`0\` (139), and missing (588); it is not a valid nonnegative business-day lag and remains quarantined.
- The 303 distinct source CIK/ticker values are not 303 verified subject issuers.

**Phase 154 disposition:** preserve its form-level date counts only as descriptive statistics of the filer-query sample. Do not use its CIK/ticker assignments for issuer joins, security returns, model features, or alpha tests. Its 13G quarter-end concentration is not a subject-issuer result.

## 2. Independent role-aware sample

Reused Phase 124's deterministic hash-stratified global master-index sample:
- Run: \`42073725379\` (the run conclusion was the intentional index-alias quarantine gate; the immutable artifact completed and downstream phases consumed it).
- Artifact: \`13436764625\`, \`phase124-global-sec-13dg-stratified-submission-audit\`.
- Artifact ZIP SHA-256: \`85f69e083b5af65731c9bcfe24e8c75821fc0f2c2476bfa8ba573e2e884570dc\`.
- CSV SHA-256: \`be2c592c6c26d9f1ea49bda5d29d20e944004b2e2f4a3c3f4fe1f732319c55d5\`.
- 600 sampled index rows: 599 actual 13D/G submissions plus one quarantined SC TO-T/A alias.
- 102 structured XML rows; all 102 have subject and filer CIKs concordant with the SEC header.
- The event-date field is populated on those 102 structured XML rows; this is only 102/599 (17.03%) of the actual sample. Legacy HTML event-date extraction is not validated by this phase.

The sample is stratified by quarter, family, and amendment status. It is not a complete security universe, active/delisted membership ledger, or an inferential sample with formal confidence intervals.

## 3. Role-validated event-date results

Only rows with a nonempty event date, structured XML, and subject/filer/header concordance were included.

| Family | Event dates | Quarter-end dates | Unweighted rate | Sample-weighted rate within observed XML subset | Median filing-event lag |
|---|---:|---:|---:|---:|---:|
| 13D | 34 | 0 | 0.00% | 0.00% | 3.5 calendar days |
| 13G | 68 | 53 | 77.94% | 79.12% | 37 calendar days |

13D event-date lags range from 0 to 111 calendar days before filing; six are same-day. 13G event-date lags range from 1 to 126 days before filing; none are same-day. No future event dates occur in this role-validated subset.

### 13G rule-designation split

| Structured rule designation | Rows | Quarter-end rows | Unweighted rate | Sample-weighted rate within observed XML subset |
|---|---:|---:|---:|---:|
| Rule 13d-1(b) | 44 | 38 | 86.36% | 85.80% |
| Rule 13d-1(c) | 15 | 10 | 66.67% | 73.84% |
| Rule 13d-1(d) | 9 | 5 | 55.56% | 55.60% |

These rule-level counts are small. The weights correct the original stratified sample only within the observed XML subset; because event-date availability is schema/regime-dependent, they are not population-wide estimates.

### Original filings versus amendments

- 13G originals: 21/29 quarter-end (72.41%); weighted descriptive rate 73.57%.
- 13G amendments: 32/39 quarter-end (82.05%); weighted descriptive rate 82.27%.
- 13D originals and amendments: 0/14 and 0/20 quarter-end, respectively.

An amendment is a filing-time update, not a new accumulation event. Parent accession and changed ownership facts remain necessary before event normalization.

## 4. Public-knowledge timing

Among the 102 event-date rows, EDGAR acceptance was after 16:00 ET for:
- 13D: 28/34 (82.35%).
- 13G: 23/68 (33.82%).

Acceptance datetime is the earliest public-knowledge boundary available in this sample, not proof of exact public dissemination. For a regular-session end-of-day strategy, an after-16:00 ET acceptance must not be backdated to the same session; use the next tradable session unless a more precise dissemination/decision-time model is established.

The SEC's 2023 beneficial-ownership amendments distinguish 13D and 13G filing regimes and set September 30, 2024 as the compliance date for revised 13G filing deadlines. These rules help explain why 13G reporting can be anchored to quarter-end, but the sample does not establish that the rule change caused the observed distribution or that every 13G filer follows the same timing path.

## 5. Research interpretation

1. **13G event_date is not a trade date.** In the role-validated XML sample it is heavily quarter-end concentrated, consistent with periodic/threshold reporting anchors. It must not be used as the date of accumulation or as the signal's public-knowledge timestamp.
2. **13D event_date is more event-like in this sample, but not the knowledge time.** Retain it only as a reported trigger-date candidate after filer/subject validation and stale-date checks. It is not proof of the exact acquisition date.
3. **Acceptance datetime governs PIT.** Use the accession's accepted timestamp and the next tradable session for conservative execution. Date-only filing_date is insufficient for after-close filings.
4. **Filer category matters.** Preserve Rule 13d-1(b), (c), and (d) separately; do not pool 13G populations without a predeclared economic reason.
5. **Amendment lineage matters.** Preserve original and amendment accessions, previousAccessionNumber, and structured ownership changes. Never count every amendment as new buying.
6. **Identity is a separate gate.** The Phase 35/28D filer-query panel remains quarantined. The Phase 124 sample is role-validated but does not establish historical active-universe membership or broad subject-security coverage.

## 6. Next gate

The next no-purchase step is a global structured-XML panel that preserves, for every accession:
- subject issuer CIK and filer CIK as separate roles;
- \`acceptance_datetime\` and filing form/regime;
- event date as a distinct field, not knowledge time;
- exact Rule 13d-1(b)/(c)/(d) designation;
- \`previousAccessionNumber\`, amendment number, reporting-person/group relations;
- ownership fields and security class/CUSIP;
- effective-dated subject-security mapping and historical active/delisted membership.

Do not restart the Phase 35 CIK-specific crawl. Do not run forward returns until these identity, lineage, and historical-universe gates pass.

No alpha test, no final holdout use, no vendor contact/purchase, and no production change. \`F80_TOP20_PARTIAL50_BASELINE_C20\` remains frozen.

## Official references
- SEC, [Adopts Amendments to Rules Governing Beneficial Ownership Reporting](https://www.sec.gov/newsroom/press-releases/2023-219), October 10, 2023.
- SEC, [Final Rule 33-11253](https://www.sec.gov/files/rules/final/2023/33-11253.pdf).
- Repository, [Phase 96 — Phase 35 subject-identity revalidation](PHASE96_PHASE35_SUBJECT_IDENTITY_REVALIDATION_2026-11-05.md).
- Repository, [Phase 124 — global 13D/G stratified submission audit](PHASE124_GLOBAL_SEC_13DG_STRATIFIED_SUBMISSION_AUDIT_2026-11-05.md).
- Repository, [Phase 154 — event-date semantics audit](PHASE154_SEC_13DG_EVENT_DATE_SEMANTICS_AND_REPORTING_REGIME_AUDIT_2026-11-06.md), superseded for issuer-level interpretation by this phase.
