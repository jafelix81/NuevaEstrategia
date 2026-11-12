# Phase 320 — SEC bulk-to-daily-index accession join audit

**Date:** 2026-11-12 UTC  
**Status:** PASS — 72/72 deterministic accessions joined to the official filed-date daily index and 72/72 original headers reconciled.  
**GitHub Actions:** [run 43176308146](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43176308146) — success, 10/10 Phase 320 regression tests.  
**Artifact:** [13924636727](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43176308146/artifacts/13924636727)  
**Artifact ZIP SHA-256:** `995f114e641443df2f6f32bc8f8cc0509fbf7efa3aeef18cc3bfd7d940aef150`  
**Source artifact:** Phase 294 run `43083625013`, artifact `13884014630`; all six source ZIP hashes and CRC checks passed.

## Executive decision

The Phase 281 SEC daily-index route successfully joined all 72 deterministic Form 4 / Form 4/A sample accessions from six historical SEC bulk archives to their official `FILED AS OF DATE` daily indexes. All 72 original submission headers reconciled on accession, form, filed date and filing-entity CIK; no accession was missing, no next-business-day fallback was needed, and no parser or retrieval errors occurred.

This is a successful **date-level historical join feasibility result**, not strict intraday point-in-time proof. The daily index does not identify the exact first-public receipt timestamp, and `ACCEPTANCE-DATETIME` is not transmission commencement. Keep the conservative rule: do not make an event tradable before the first full XNYS session strictly after the official filed/index date.

## 1. Immutable source archives and sample design

Reused the immutable Phase 294 artifact. Six quarterly Form 3/4/5 archives were verified by exact SHA-256, ZIP CRC and expected manifest digest:

| Quarter | SEC bulk Form 4 / 4-A rows |
|---|---:|
| 2006 Q1 | 71,679 |
| 2012 Q1 | 63,678 |
| 2023 Q1 | 63,844 |
| 2023 Q2 | 51,791 |
| 2025 Q3 | 32,127 |
| 2026 Q3 | 34,148 |
| **Total** | **317,267** |

The sample contains 12 accessions per quarter: eight Form 4 and four Form 4/A. Selection is deterministic and spread across filing-date bins; 32 previously examined accessions were excluded. The 72 accessions have 72 distinct filing dates and 72 distinct issuer CIKs.

**The sample is not a probability sample.** All 72 selected accessions have one reporting owner. This means Phase 320 does not yet validate live multi-owner/header behavior; that is an explicit next gate, not an assumption.

The six full archives contain 6,706 multi-owner accessions (2.11% of the 317,267 Form 4/4-A rows), with quarter counts 1,174 / 1,134 / 1,124 / 1,327 / 1,093 / 854. Owner counts reach ten in the source archives. These cases were not represented in the 72-header sample.

## 2. Daily-index scan and parser integrity

Downloaded 72 distinct SEC daily form indexes covering 72 sample filing dates, totaling **58,389,807 bytes**. Every file used the legacy fixed-width layout.

Aggregated across those 72 files:

| Parsed content / control | Count |
|---|---:|
| Rows after index header | 354,742 |
| Form 4 / Form 4-A entity rows | 124,741 |
| Other-form rows correctly ignored | 230,001 |
| Multi-entity accession instances | 60,222 |
| Exact duplicate rows collapsed | 19 |
| Malformed rows | 0 |
| Issuer-CIK / path-CIK mismatches | 0 |
| Conflicting duplicate accessions | 0 |

The parser preserved multiple CIK rows per accession rather than assuming one entity row or treating different issuer/owner CIKs as conflicting identities.

## 3. Bulk accession-to-index results

| Check | Result |
|---|---:|
| Bulk accessions sampled | 72 |
| Found on exact bulk `FILING_DATE` index | **72/72** |
| Found only on next EDGAR business day | 0 |
| Not found | 0 |
| Form/date conflicts | 0 |
| Issuer CIK present among index entity rows | 72/72 |
| Multi-entity index accessions | 72/72 |
| Index entity CIK rows per sampled accession | 2 |

All sampled index dates equaled the bulk filing date. Every accession had both issuer and reporting-owner CIK rows in the index.

## 4. Original-header and entity-path crosscheck

Downloaded and parsed 72 original EDGAR submission headers:

- 72/72 had matching accession, form type and `FILED AS OF DATE`.
- 72/72 contained `ACCEPTANCE-DATETIME`; all 72 acceptance calendar dates equaled the bulk filing date.
- 72/72 header CIKs were present among the daily-index entity CIKs.
- 72/72 issuer CIKs were present among the daily-index entity CIKs.
- Header CIK identified a reporting owner in 66 cases and the issuer in six cases.
- 21/72 acceptance timestamps were at or after 17:30 ET.

The final implementation distinguishes genuinely independent path comparisons from same-path identity checks:

| Path test | Result |
|---|---:|
| Independent issuer-path vs. reporting-owner-path SHA-256 comparisons | **66/66 equal** |
| Independent path hash mismatches | 0 |
| Header CIK already equals issuer CIK (same path, not an independent comparison) | 6 |
| Total headers with either an independent path comparison or same-path identity check | 72/72 |

The first run's aggregate label counted the six same-path cases as “dual-path” checks. That wording was corrected in code, tests and the workflow gate. The final artifact reports 66 independent comparisons and six same-path identity checks; it does **not** claim 72 independent comparisons.

## 5. Availability and PIT interpretation

The 72 daily-index dates match the bulk filed dates, but the index is date-granular. It does not establish the exact time at which a filing first became publicly retrievable. The 21 after-17:30 ET acceptance timestamps reinforce why acceptance time must not be used as a substitute for transmission commencement or first-public receipt.

**Conservative date-level rule:** use the official SEC `FILED AS OF DATE` / daily-index date as an anchor only; allow strategy use no earlier than the first full XNYS session strictly after that date. Do not backdate Form 4/A corrections to the original filing or transaction date.

Strict PIT remains **not admitted**. No transmission-start timestamp was observed and no exact first-public receipt time was inferred.

The sample also preserves the raw `AFF10B5ONE` values. The field is absent in the 2006Q1 and 2012Q1 schemas, appears in 2023Q1 onward, and can contain blanks or textual/numeric representations. Blank remains UNKNOWN; do not coerce it to false or broadcast a filing-level flag to individual transaction rows without the original filing/footnote scope.

## 6. Decision and next gate

**Promote the SEC daily-index join from a format smoke test to a validated date-level join method for the six-quarter sample. Do not promote the Form 4 signal or strict PIT.**

Next:
1. Run a complete accession census over all 317,267 Form 4 / Form 4/A rows in the six immutable quarterly archives, downloading each unique filing-date daily index once (377 distinct quarter-date slots in the current archives).
2. Compare accession, form, filed date, issuer CIK and every reporting-owner CIK against the full set of daily-index entity rows; quantify missing, delayed, duplicate and conflicting cases by quarter/form/owner-count.
3. Select original-header samples stratified by quarter, Form 4 vs. 4/A, single-owner, two-owner, 3–5-owner and 6–10-owner cohorts. Validate header identity and independent path hashes without inferring transaction-to-owner attribution.
4. Only after the full join, resolve effective-dated issuer/security-class identity and coverage of a survivorship-aware broad universe, including delisted securities and multiple classes.
5. Keep the Form 4 hypothesis quarantined until event/owner/security identity and conservative availability are admitted. Then preregister an incremental test versus frozen LTM/F80 with identical eligible universe, exposure and costs, chronological OOS, clustered bootstrap/LOO, multiplicity control and a new prospective holdout.

## 7. Controls

- `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen.
- No return/alpha, bootstrap/LOO, chronological OOS or holdout test was run.
- Strict PIT was not admitted.
- No production, universe, capital or parameter change.
- No raw SEC index or filing bytes were uploaded; the artifact contains parsed metadata, SHA-256 hashes and crosschecks only.
- No vendor was contacted, no data purchased and no email sent. The SEC contact secret was used only in the request User-Agent.

