# Phase 636 — Smart Money Research: SEC 13D/G parent lineage results

**Date:** 2026-11-26 UTC  
**Implementation branch:** `phase350-sec-13dg-explicit-parent-retrieval`  
**Stacked PR:** [#37 — Phase 350–352](https://github.com/jafelix81/NuevaEstrategia/pull/37) (Draft; base `phase347-13dg-cusip-integrity-audit`)  
**Disposition:** major data-lineage milestone completed; no signal admission.

## 1. SEC 13D/G explicit-parent retrieval

The immutable Phase 349 manifest contained 44 explicit parent references. Phase 350 [run 45786611405](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45786611405) retrieved 43 parent submissions successfully at 2 requests/second. All 43 passed exact accession, subject issuer CIK, 13D/13G family and strictly-earlier acceptance validation. One explicit parent returned HTTP 404.

- Phase 350 artifact: [15100039658](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45786611405/artifacts/15100039658)
- Artifact SHA-256: `d1ad6a7110256cfe057729782b6c90e37d0729ced17b7f3e7e6b95c9203ff87d`
- Phase 350 offline tests: 15/15 passed.
- The established shared project-contact fallback was used because the repository `SEC_USER_AGENT` secret was empty. No User-Agent value was logged or persisted.

## 2. Unresolved parent

Child accession `0000886982-25-001416` is a 2025-11-10 Schedule 13G/A for Avis Budget Group (CIK 723612; CUSIP 053774105). Its SEC primary document explicitly references `0000769993-25-000432` as `previousAccessionNumber`. The child is independently listed on the issuer's SEC-filings page.

The parent could not be retrieved through either:
- subject-issuer archive path CIK `723612` (HTTP 404); or
- manifest/accession-prefix candidate CIK `769993` (HTTP 404).

Two one-request Phase 351 runs returned 404. The second was inadvertently triggered by a report-only update due an overly broad path filter; no raw data were saved. The workflow is now manual-dispatch-only, and no third path guess is authorized. The explicit parent remains quarantined. The child reference's existence does not prove the parent is publicly retrievable.

## 3. Phase 352 identity and security crosswalk

The offline parser [run 45788746680](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45788746680) passed 9/9 tests and produced artifact [15101047906](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45788746680/artifacts/15101047906), SHA-256 `512412e6cbabdb6e409d4ffb53574f3847b19436fb33b5c857dc60fd05bd9146`. A report-only reproducibility rerun [45788991215](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45788991215) also succeeded; Phase 350's corresponding PR run [45788991208](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45788991208) ran offline tests and skipped live retrieval.

Results across 44 target references:

| Identity / continuity check | Result |
|---|---:|
| Parent docs retrieved and identity-validated | 43/43 |
| Structured parent `reportingPersonName` fields available | 21 |
| Structured parent names overlapping child names | 21/21 |
| Child reporting-person CIKs available | 25 |
| Parent `FILED BY` CIK overlap among those 25 | 25/25 |
| Parent `FILED BY` exact-name overlap | 31/43 |
| Additional `FILED BY` substring candidates | 3 |
| `FILED BY` CIK equals accession prefix | 21/43 |

The `FILED BY` comparisons are submitter proxies, not complete reporting-person ground truth. The accession prefix is not a reliable identity key.

CUSIP continuity:
- 31/42 valid child CUSIPs match a CUSIP extracted from the parent.
- 5 pairs have different CUSIPs.
- 6 valid child CUSIPs have no parent CUSIP.
- 1 child uses an all-zero CUSIP sentinel.
- 1 parent is unresolved.

The five mismatches remain quarantined; no corporate action, share-class or security mapping is inferred. A point-in-time security master and corporate-action crosswalk are required before security-level event analysis.

## 4. Workflow and data controls

- Phase 350 pull-request updates now run offline tests only; full 44-reference retrieval requires explicit manual dispatch with `run_live_capture=true`.
- Phase 351 is manual-dispatch-only with `run_live_recovery=false` by default.
- Phase 352 is offline-only and consumes immutable artifacts.
- Raw SEC parent documents remain in Actions artifacts, not committed to the repository.
- No vendor contact or paid data. Options budget remains USD 0.

## 5. Quantitative disposition

This phase improves identity and lineage coverage but does not demonstrate predictive value.

- First-publication timestamps remain unavailable; acceptance time alone is not strict PIT.
- No immediate-predecessor inference.
- No forward-return/event study, alpha, chronological OOS, bootstrap, LOO or holdout test.
- No 13D/G signal admitted to production.
- `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen.
- No changes to universe, capital, exposure, costs, parameters or holding-period policy.

The Phase 350–352 implementation remains in Draft PR #37 until the Phase 347 parent identity-audit chain is reviewed.
