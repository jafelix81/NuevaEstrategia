# Phase 274 — Form 4 conservative date-only PIT boundary and multi-owner purchase clusters

**Date:** 2026-11-10 UTC  
**Status:** Descriptive event-structure result; no return/alpha test and no strict historical PIT admission.  
**Source:** Phase 39 immutable Form 345 artifact, run 40606706518 / artifact 12781850078; outer SHA-256 `203d7b1d2e29c999da318456af72e621cb30ef9a470d8f1610d088f9bebecb66`.

## Executive finding

The unchanged Phase 271 high-specificity purchase screen contains a small but potentially interesting group of same-issuer, same-filing-date, same-transaction-date purchases reported through multiple distinct reporting-owner CIKs.

- **2026 Q3:** 11 clusters across 8 issuers, containing 19 unique accessions, 19 unique reporting-owner CIKs and 24 candidate transaction rows.
- **2012 Q1:** one 3-accession/3-owner cluster, but the 10b5-1 indicator is unknown in that historical sample and it is excluded from the primary cohort.

These are candidate disclosure clusters, not proof of independent beneficial owners, coordinated purchases, informed trading or predictive alpha. Reporting owners may be affiliated, and one accession/owner can appear in more than one transaction-date cluster.

## 1. Conservative date-only execution boundary

The SEC Insider Transactions Data Sets README defines SUBMISSION.FILING_DATE as the filing date with the Commission, sourced from EDGAR, in date-only form. The same README states that the bulk data are published quarterly and include as-filed submissions and amendments, with possible redundancies/inconsistencies.

For a daily EOD strategy, the exact acceptance time is not needed to create a conservative *execution bound* if we refuse to trade until the close of the first XNYS session strictly after FILING_DATE:

1. Never use the filing-date close.
2. Never use the next-session open.
3. Use only the next XNYS session's actual close, including early-close sessions.
4. Apply the same rule to every filing in a same-date cluster; the event is not available until the common next-session close.

This is intentionally later than the earliest possible tradable moment. It handles an intraday or after-close acceptance without guessing the time. Phase 152's verified ETON example was accepted at 16:51:30 ET on 2026-08-28, after the close; the next XNYS session was 2026-08-31. The Phase 274 rule maps that filing date to the 2026-08-31 close.

**Important limitation:** this date-only boundary is a conservative event-time policy, not proof that the quarterly bulk extract itself was available on the filing date. A strict historical panel still requires the original accession content, first-receipt/acceptance evidence, amendment vintages and continuous coverage. The quarterly bulk posting date is not used as the event time.

## 2. Cluster definition

A cluster requires all three:
- same issuer CIK;
- same SEC filing date; and
- same reported transaction date.

It must also contain at least two distinct accessions and at least two distinct reporting-owner CIKs. Transaction rows are not counted as separate insiders. Distinct CIKs are not automatically independent beneficial owners.

The broad same-issuer/same-filing-date grouping yields 9 multi-owner groups in 2026 Q3. Splitting those groups by transaction date produces 11 stricter clusters.

## 3. Results

| Diagnostic | 2012 Q1 | 2026 Q3 |
|---|---:|---:|
| Candidate transaction rows | 102 | 85 |
| Unique accessions | 47 | 59 |
| Unique issuers | 16 | 31 |
| Broad issuer/filing-date multi-owner groups | 2 | 9 |
| Same issuer/filing/transaction-date clusters | 1 | 11 |
| Unique accessions in strict clusters | 3 | 19 |
| Unique reporting-owner CIKs in strict clusters | 3 | 19 |
| Unique issuers in strict clusters | 1 | 8 |
| Candidate rows in strict clusters | 3 | 24 |
| AFF10B5ONE status | Unknown | False required by screen |

The 2026 Q3 strict clusters contain **23 accession/cluster memberships but only 19 unique accessions and 19 unique owners**. Two issuers (DOMH and SNBH) each have two transaction dates within one filing-date cluster, so the same accessions/owners appear in multiple cluster memberships. These repeated memberships must not be counted as independent observations.

The 24 rows in clusters are 28.24% of the 85 screened candidate rows. Filing-to-transaction lag across the 11 clusters ranges from 0 to 4 calendar days, with median 2.

### 2026 Q3 cluster ledger

| Ticker | Filing date | Transaction date | Accessions | Owners | First tradable close |
|---|---|---|---:|---:|---|
| ACCS | 2026-08-17 | 2026-08-14 | 2 | 2 | 2026-08-18 |
| SNBH | 2026-08-18 | 2026-08-14 | 2 | 2 | 2026-08-19 |
| SNBH | 2026-08-18 | 2026-08-17 | 2 | 2 | 2026-08-19 |
| BIVI | 2026-08-28 | 2026-08-28 | 3 | 3 | 2026-08-31 |
| GPUS | 2026-09-02 | 2026-09-02 | 2 | 2 | 2026-09-03 |
| GPUS | 2026-09-08 | 2026-09-04 | 2 | 2 | 2026-09-09 |
| RLMD | 2026-09-11 | 2026-09-09 | 2 | 2 | 2026-09-14 |
| DOMH | 2026-09-14 | 2026-09-10 | 2 | 2 | 2026-09-15 |
| DOMH | 2026-09-14 | 2026-09-11 | 2 | 2 | 2026-09-15 |
| MCFT | 2026-09-16 | 2026-09-15 | 2 | 2 | 2026-09-17 |
| VFF | 2026-09-22 | 2026-09-22 | 2 | 2 | 2026-09-23 |

The 2012 Q1 cluster is IDCC on 2012-01-26: three accessions, three reporting-owner CIKs and three candidate rows; first tradable session/close is 2012-01-27. AFF10B5ONE was not available/known in that sample, so this is a sensitivity observation, not part of the primary cohort.

## 4. Interpretation and limits

- The 11 2026 clusters are a promising event-screen hypothesis, not 11 independent issuer replications: they cover only 8 issuers, and repeated accessions/owners appear across separate transaction dates.
- The SEC's AFF10B5ONE=false field is a screen condition, not proof that every other prearranged or affiliated arrangement is absent.
- Distinct reporting-owner CIKs do not prove independent beneficial ownership, independent decision-making or lack of family/affiliate relationships.
- The screen uses original Form 4 only. Phase 152 shows that Form 4/A may repeat unchanged lines; amendments require confirmed parent accession and line-level diff before updating event flow.
- Only two endpoint quarters are present. There is no continuous quarterly sample, no full-universe coverage measurement and no delisted-security identity census.
- No stock returns, forward-return test, bootstrap/LOO, chronological OOS, capacity/cost analysis or holdout use was performed.

## Decision

Retain same-issuer/same-filing-date/same-transaction-date multi-reporting-owner purchases as a candidate event hypothesis. Use the next-XNYS-session-close boundary for any daily-EOD study. Do not admit the quarterly bulk extract as strict historical PIT or claim alpha until original accession/vintage, amendment-lineage, continuous coverage and effective-dated security identity gates pass.

F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen. Production, universe, capital and parameters are unchanged.

## Reproducibility

- Phase 39 source artifact: run 40606706518 / artifact 12781850078.
- Phase 272 exact eligibility screen is reused unchanged.
- Phase 274 code: `research/phase274_form4_conservative_date_only_pit_clusters.py`.
- Tests: `research/test_phase274_form4_conservative_date_only_pit_clusters.py`.
- Workflow: `.github/workflows/phase274_form4_conservative_date_only_pit_clusters.yml`.
- The hosted workflow recomputes the result from the hash-pinned source and uploads a metadata-only JSON artifact.
