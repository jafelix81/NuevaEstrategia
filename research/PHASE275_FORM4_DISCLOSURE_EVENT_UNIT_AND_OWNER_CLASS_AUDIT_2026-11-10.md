# Phase 275 — Form 4 disclosure-event unit, owner-proxy and security-class audit

**Date:** 2026-11-10 UTC  
**Status:** Completed descriptive audit; no return/alpha test and no strict historical PIT admission.  
**Source:** Phase 39 immutable Form 345 artifact, run 40606706518, artifact 12781850078; outer SHA-256 203d7b1d2e29c999da318456af72e621cb30ef9a470d8f1610d088f9bebecb66.

## Executive finding

Phase 274 found 11 same-issuer / same-filing-date / same-transaction-date multi-owner clusters in the 2026 Q3 endpoint sample. Those are nested trade-date clusters, not 11 independent public disclosure events.

For a daily strategy, the public information batch is more naturally represented by one issuer CIK × date-only EDGAR FILING_DATE event. Reapplying the exact Phase 271 purchase screen and grouping at that level produces:

- 9 multi-owner disclosure events across 8 issuers;
- 20 unique accessions and 20 unique reporting-owner CIKs;
- 27 candidate transaction rows;
- 11 nested same-trade-date, same-security multi-owner clusters;
- 5 disclosure events containing more than one transaction date;
- 4 events in which at least one owner transacted on multiple dates;
- 8 of 9 events with one normalized mailing address among their owners;
- all 9 events have one normalized security-title value.

The event unit correction prevents multiple trade dates disclosed in the same issuer / filing-date batch from being counted as independent public signals. It does not establish independent beneficial owners, informed trading or alpha.

## 1. Canonical event unit

The event key is issuer CIK plus date-only FILING_DATE.

The exact Phase 271 row-level eligibility rules are reused unchanged. Multiple Form 4 accessions and multiple transaction dates in the same issuer / filing-date batch remain attributes of one disclosure event. Same-trade-date clusters are retained as nested descriptors.

For a daily EOD study, the conservative execution boundary remains the close of the first XNYS session strictly after FILING_DATE. This avoids same-day close and next-session-open lookahead when acceptance time is unavailable in the bulk data. It is an execution bound, not proof of complete historical first-receipt vintages.

## 2. Results

| Diagnostic | 2012 Q1 sensitivity | 2026 Q3 primary endpoint |
|---|---:|---:|
| Phase 271 candidate rows | 102 | 85 |
| Multi-owner issuer / filing-date events | 2 | 9 |
| Issuers represented in events | 2 | 8 |
| Unique accessions in events | 5 | 20 |
| Unique reporting-owner CIKs | 5 | 20 |
| Candidate rows in events | 8 | 27 |
| Events with multiple transaction dates | 1 | 5 |
| Events with any owner transacting on multiple dates | 1 | 4 |
| Nested same-trade-date multi-owner clusters | 1 | 11 |
| Events with one normalized mailing address | 1 | 8 |
| Security-title mismatches | 0 | 0 |
| Plan indicator | Unknown / pre-checkbox era | AFF10B5ONE=false screen |

The 2012 Q1 cohort is sensitivity-only because AFF10B5ONE was unavailable/unknown. It is not pooled with the 2026 primary endpoint.

### 2026 Q3 issuer / filing-date event ledger

| Ticker | Filing date | Rows | Accessions | Owners | Transaction dates | Nested same-date clusters |
|---|---|---:|---:|---:|---:|---:|
| ACCS | 2026-08-17 | 2 | 2 | 2 | 1 | 1 |
| SNBH | 2026-08-18 | 4 | 2 | 2 | 2 | 2 |
| BIVI | 2026-08-28 | 4 | 4 | 4 | 2 | 1 |
| GPUS | 2026-09-02 | 3 | 2 | 2 | 2 | 1 |
| GPUS | 2026-09-08 | 2 | 2 | 2 | 1 | 1 |
| RLMD | 2026-09-11 | 3 | 2 | 2 | 2 | 1 |
| DOMH | 2026-09-14 | 4 | 2 | 2 | 2 | 2 |
| MCFT | 2026-09-16 | 3 | 2 | 2 | 1 | 1 |
| VFF | 2026-09-22 | 2 | 2 | 2 | 1 | 1 |
| **Total** |  | **27** | **20 unique** | **20 unique** |  | **11** |

There are 9 filing-date events but only 8 issuers because GPUS has two separate filing-date events. SNBH and DOMH each have two transaction-date subclusters within one filing-date disclosure event. These must not be treated as separate public information arrivals.

## 3. Owner and security metadata

- All 9 2026 Q3 event groups have one normalized security-title value. The implementation splits nested same-date clusters by normalized security title; mixed-class rows cannot be pooled into one same-security cluster.
- Eight of nine event groups have a single normalized reporting-owner mailing address; one GPUS filing-date group has two. These are administrative/mailing fields, often company or counsel addresses. They are not evidence of common beneficial ownership, affiliation or coordination.
- Distinct reporting-owner CIKs and names are not proof of economically independent beneficial owners. The audit explicitly leaves owner independence unproven.
- The reporting-owner relationship and title fields are preserved as descriptive metadata, not converted into an insider-conviction score.
- AFF10B5ONE=false is only the existing screen condition. It does not prove the absence of every non-Rule-10b5-1 arrangement or discretionary intent.

## 4. Decision

Use issuer CIK × filing date as the primary public disclosure-event unit for any future daily study. Keep transaction dates and same-date owner clusters nested inside the event. Do not count the 11 nested clusters as 11 independent observations.

Retain the multi-owner hypothesis as a low-sample candidate only. The endpoint sample contains just 9 filing events across 8 issuers, is not a continuous quarterly panel, and has no verified complete accession acceptance/vintage history. No forward returns, alpha, bootstrap/LOO, chronological OOS, or holdout test was run.

## 5. Remaining gates

1. Complete original accession acceptance-time and immutable-byte coverage for all candidate Form 4 filings.
2. Resolve Form 4/A parent accession and line-level amendment state across adjacent quarters.
3. Establish continuous quarterly and delisted-security coverage against a survivorship-aware universe.
4. Verify owner/affiliate identity only from filing evidence; do not infer it from address equality.
5. Only after the above gates pass, preregister event-level return hypotheses and compare them incrementally with frozen LTM/F80 using identical exposure, costs, bootstrap/LOO and chronological OOS.

F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen. The consumed legacy holdout remains unused. No production, universe, capital or parameter changes were made.

## Reproducibility

- Phase 39 source artifact: run 40606706518, artifact 12781850078.
- Phase 271 exact eligibility logic is reused.
- Code: research/phase275_form4_disclosure_event_unit_audit.py.
- Tests: research/test_phase275_form4_disclosure_event_unit_audit.py.
- Workflow: .github/workflows/phase275_form4_disclosure_event_unit_audit.yml.
- The workflow recomputes from the hash-pinned Phase 39 artifact and uploads a metadata-only result.
