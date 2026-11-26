# Phase 352 — SEC 13D/G parent identity and security continuity crosswalk

**Date:** 2026-11-26 UTC  
**Inputs:** immutable Phase 349 manifest artifact `13992528474`; completed Phase 350 retrieval artifact `15100039658`.  
**Mode:** offline parsing only; no SEC request.

## 1. Preliminary artifact audit

The 43 retrieved parent submissions were inspected against the child filing manifest. Phase 350 had already validated exact parent accession, subject issuer CIK, form family and strictly earlier acceptance for all 43.

The preliminary crosswalk found:

| Gate | Preliminary result |
|---|---:|
| Parent documents retrieved and identity-validated | 43/43 |
| Structured parent `reportingPersonName` tags available | 21/43 |
| Structured parent names overlapping child names | 21/21 available |
| Child rows with explicit reporting-person CIKs | 25/44 |
| Parent `FILED BY` CIK overlapping child reporting-person CIKs | 25/25 available |
| Parent `FILED BY` exact-name overlap with child names | 31/43 |
| Additional `FILED BY` substring candidates | 3 |
| Exact CUSIP matches among valid child CUSIPs | 31/42 |
| CUSIP mismatches | 5 |
| Parent CUSIP unavailable | 6 |
| Invalid child CUSIP sentinel | 1 |
| Parent accession unresolved | 1 |

The 25/25 CIK result compares the parent's `FILED BY` entity with child reporting-person CIKs. It is a submitter proxy, not a complete reporting-person crosswalk. Likewise, the `FILED BY` name comparison is a proxy. Structured `reportingPersonName` tags are stronger; they are available in 21 documents and all 21 have at least one exact normalized name overlap with the child manifest. The parsed `FILED BY` CIK equals the accession prefix in only 21/43 documents, further confirming that accession prefix, archive-path CIK and reporting-person identity must remain separate fields.

## 2. CUSIP mismatches requiring separate security mapping

The five retrieved parent/child pairs with a CUSIP present on both sides but no exact match are:

| Child accession | Child CUSIP | Parent CUSIP |
|---|---|---|
| `0000038777-24-000179` | `08205P209` | `08205P100` |
| `0001104659-24-129092` | `91060H108` | `25278L105` |
| `0001104659-25-014195` | `67022C205` | `67022C106` |
| `0001398344-25-002939` | `Y8900D108` | `891092108` |
| `0001445546-26-005159` | `33740F458` | `33740F854` |

These differences are not automatically errors or corporate actions. They may reflect share-class changes, reorganizations, amendments, or extraction/filing differences. No mapping is inferred. These rows remain quarantined for security-level event analysis until a point-in-time issuer/security master and corporate-action crosswalk independently resolve them.

The six valid child-CUSIP rows with no parent CUSIP in the retrieved parent document also remain unverified. One additional child row carries the all-zero CUSIP sentinel and is excluded from the valid-CUSIP denominator.

## 3. Reproducible audit

Phase 352 adds an offline parser and artifact workflow to reproduce:
- SEC-HEADER subject and FILED BY identity extraction;
- structured `reportingPersonName` extraction;
- XML `issuerCUSIP` and HTML cover-page CUSIP extraction;
- child/parent CIK and name overlap labels;
- exact CUSIP continuity classifications;
- raw-document SHA-256 references.

The workflow downloads the two immutable artifacts and does not contact SEC or any data vendor.

## 4. Reproducible run

- [Phase 352 run 45788746680](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45788746680) completed successfully.
- Offline parser regression: **9/9 tests passed**.
- Artifact: [15101047906](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45788746680/artifacts/15101047906), SHA-256 `512412e6cbabdb6e409d4ffb53574f3847b19436fb33b5c857dc60fd05bd9146`.
- The artifact reproduces 43 identity-pass parent rows and the counts above. No SEC request or vendor access occurred in Phase 352.

## 5. Research disposition

This improves lineage and security identity quality, but does not establish that the 13D/G disclosures predict returns.

- The explicit parent reference is not necessarily the immediate predecessor.
- One parent remains unresolved after two evidence-based archive-path attempts.
- First-publication timestamps remain unavailable; acceptance time alone does not certify first public availability.
- CUSIP continuity is incomplete and no corporate-action mapping is admitted.
- No forward returns, event study, alpha, chronological OOS, bootstrap, LOO or holdout test was run.
- No signal is admitted to production.
- `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen.
