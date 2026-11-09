# Phase 163 — SEC 13D/G previousAccessionNumber: original-anchor vs immediate-predecessor semantics

**Date:** 2026-11-06  
**Status:** COMPLETED — targeted document audit; field retained as provenance/reference, no automatic state edge  
**Scope:** Inspect six of the 32 unique previousAccessionNumber references from Phase 160 and compare the actual parent filing with sampled child filings, including issuer identity, security identity, amendment number and chronology.

## Executive finding

The previousAccessionNumber field must not be interpreted as an immediate predecessor edge.

Two independently inspected chains show an initial filing accession still referenced by a later, numbered amendment:
- Amdocs Limited: the 2026 SC 13G/A is Amendment No. 14 and points to the initial 2012 SC 13G accession 0000315066-12-002323.
- 89bio, Inc.: the 2025 SC 13G/A is Amendment No. 5 and points to the initial 2023 SC 13G accession 0001274173-23-000077.

These are empirical examples of an original/base filing anchor, not the immediately preceding amendment. The field may identify the original Schedule filing for an issuer/security chain; it does not, by itself, enumerate the intermediate amendments or prove which filing immediately preceded the current filing.

A separate counterexample remains important: eight First Trust child filings reuse 0001445546-21-002430, but the inspected 2021 parent covers CUSIP 33740F854. None of the eight children has that CUSIP; four also have a different issuer CIK. That reference cannot establish issuer/security continuity for those children.

## Six parent documents inspected

| Referenced accession | Parent issuer | Parent CUSIP | Parent filing | Child evidence | Result |
|---|---|---|---|---|---|
| 0000315066-12-002323 | Amdocs Limited (1062579) | G02602103 | Initial SC 13G; filed 2012-02-14, accepted 12:03:15 ET | 2026 child is Amendment 14; same issuer/CUSIP | Long-lived initial-anchor candidate |
| 0001274173-23-000077 | 89bio, Inc. (1785173) | 282559103 | Initial SC 13G; 2023-02-14, accepted 16:51:19 ET | 2025 child is Amendment 5; same issuer/CUSIP | Initial-anchor candidate, not immediate predecessor |
| 0001644956-25-000024 | Montrose Environmental Group (1643615) | 615111101 | Initial SCHEDULE 13G; 2025-05-09, accepted 16:13:10 ET | 2025 child Amendment 1; same issuer/CUSIP | Issuer/security continuity candidate |
| 0001193125-22-031137 | Endeavor Group Holdings (1766363) | 29260Y109 | Initial SC 13G; 2022-02-08, accepted 17:11:01 ET | Sampled 2025 child has same issuer CIK; child CUSIP not embedded in this compact fixture | Security continuity unresolved |
| 0001535610-24-000019 | Mobiquity Technologies (1084267) | 60743F508 | Initial SC 13G; 2024-01-03, accepted 09:26:06 ET | Sampled 2025 child has same issuer CIK; child CUSIP not embedded in this compact fixture | Security continuity unresolved |
| 0001445546-21-002430 | First Trust Exchange-Traded Fund VIII (1667919) | 33740F854 | Initial SC 13G; 2021-05-10, accepted 09:06:41 ET | Eight children: five issuer CIKs, eight CUSIPs; 0 exact CUSIP matches | Quarantine all eight state links |

The Amdocs acceptance timestamp is verified directly from the SEC submission header: 2012-02-14 12:03:15 ET. The child filing-detail page identifies the child as SCHEDULE 13G/A, Amendment No. 14, with the same issuer CIK and CUSIP.

## First Trust reused-reference control

The eight child filings that repeat 0001445546-21-002430 remain a direct counterexample to automatic parent linkage:
- 4/8 child rows have a different issuer CIK from the parent.
- 4/8 share the First Trust trust-level issuer CIK but report different CUSIPs.
- 0/8 match parent CUSIP 33740F854.
- 0/8 have exact issuer-CIK plus CUSIP continuity.

A shared registered-fund CIK does not make distinct ETF series the same security. No effective-dated series/CUSIP bridge was supplied.

## Revised interpretation and data-model rule

Store the field as:

- raw_previous_accession: exact as-filed value;
- canonical_previous_accession: normalized accession;
- reference_role: UNKNOWN_ORIGINAL_ANCHOR_OR_PREDECESSOR;
- parent_document_inspected: boolean;
- issuer_continuity: verified / mismatch / unresolved;
- security_continuity: verified candidate / mismatch / unresolved;
- immediate_predecessor_verified: false unless an independent full amendment-chain reconstruction proves it.

Do not:
1. collapse all filings sharing a previous accession;
2. treat the reference as the immediately prior amendment;
3. backdate a later disclosure to the referenced accession;
4. infer security continuity from filer CIK, trust-level issuer CIK, form family or date precedence alone.

A same issuer-CIK plus same CUSIP result is only a continuity candidate. It still requires effective-dated security identity and a complete amendment chronology before a state-machine edge is accepted.

## Coverage and limitations

- Phase 160 contained 32 unique previous-accession references in its 102-XML sample.
- This phase inspected six unique referenced documents and 13 linked child rows, including the eight First Trust counterexample children.
- The remaining 26 references are not adjudicated here.
- The sample is not random; no population prevalence estimate is possible.
- SEC documents were inspected through official EDGAR filing pages and primary documents. This repository fixture records the extracted facts and official URLs, but does not embed raw response bodies or per-document hashes.
- No returns, features, alpha tests, bootstrap/LOO, OOS validation or final holdout were used.

## CI and reproducibility

- Pure offline fixture and deterministic classifier.
- Regression tests cover initial-anchor semantics, both legacy and current Schedule form labels, verified acceptance timestamps, security mismatches, unknown CUSIPs, accession normalization, output generation and no-lookahead governance.
- No SEC bulk request was made by the workflow.
- No vendor contact/purchase or production change.

## Decision

**PASS for conservative reference semantics only.** Keep previousAccessionNumber as a raw provenance/reference field. Do not promote it to an immediate parent edge. Continue the remaining 26 parent-document checks only when a permitted, reproducible retrieval route is available.

F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen.
