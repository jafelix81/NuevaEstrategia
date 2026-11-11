# Phase 276 — PR #14 GitHub Actions supply-chain and permission audit

**Date:** 2026-11-10 UTC  
**Status:** Completed; hosted audit passed 10/10 deterministic tests.  
**Scope:** All workflow files introduced by PR #14. No research data was downloaded, no vendor was contacted, and no return/alpha test was run.

## Executive finding

The initial inventory found 27 workflow files in PR #14. Only the write-capable CFTC capture workflow and the two latest Form 4 workflows used immutable action commit references; the other 24 workflow files used mutable major-version tags.

The mutable references did not create a demonstrated compromise, but they weakened reproducibility and left the workflows exposed to tag movement. This was unnecessary supply-chain risk, particularly for workflows that download source artifacts and run research code.

## Changes

Pinned every action reference in the 24 affected workflow files to a full 40-character commit SHA resolved from the corresponding official action repository tag and verified as signed by GitHub:

| Action | Immutable commit | Signature |
|---|---|---|
| actions/checkout v4 | 11d5960a326750d5838078e36cf38b85af677262 | Verified |
| actions/setup-python v5 | a26af69be951a213d495a4c3e4e4022e16d87065 | Verified |
| actions/download-artifact v4 | d3f86a106a0bac45b974a628896c90dbdf5c8093 | Verified |
| actions/upload-artifact v4 | ea165f8d65b6e75b540449e92b4886f43607fa02 | Verified |

The initial Phase 276 static auditor inventoried 28 PR #14 workflow files and 94 action references. After Phases 277 and 278 added two read-only workflows, a follow-up expanded the allowlist and tests to 30 workflows / 100 action references. The re-audit found zero mutable/unverified references, zero workflows missing explicit permissions, zero pull_request_target workflows, and exactly one write-capable workflow. It verifies that the CFTC capture workflow has its main-branch, non-persistent-credential, scoped-token and additive-only guards.

## Security boundary

- The only contents:write workflow remains phase234_cftc_bpr_prospective_capture.yml.
- Its job is restricted to refs/heads/main; it has no pull-request trigger.
- Checkout credentials are not persisted.
- The GitHub token is exposed only in the commit/push step.
- The raw CFTC archive rejects modifications, renames and deletions.
- No workflow uses pull_request_target.
- All PR #14 workflow files declare explicit permissions.
- All action references use the four verified immutable commit SHAs above.

SHA pinning improves reproducibility and prevents tag movement; it does not replace review of the pinned action source, dependency transitive behavior, or workflow changes.

## Validation

The Phase 276 push run [42937883538](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42937883538) and PR check [42937891407](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42937891407) both passed 10/10 deterministic tests. The push run emitted metadata-only artifact [13819496221](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42937883538/artifacts/13819496221), ZIP digest SHA-256 99fd2668941bc047d3f5ed0a3d75916fd0f28c6035d5f2694818545645e16a16. The first two Phase 276 attempts exposed defects in the new audit parser/tests (list-item prefix and line-boundary handling), not in the workflow action pins; both were corrected before the successful runs.

## Follow-up inventory revalidation

The original hard-coded inventory did not include the subsequently added Phase 277 and Phase 278 workflows. The allowlist and deterministic tests now include both; the hosted re-audit confirms the expanded 30-workflow / 100-reference inventory. The Phase 277 and Phase 278 workflows are read-only and introduce no additional write path.

## Research controls

No live CFTC capture, manual dispatch, SEC request, data purchase, vendor contact, PR merge, production/universe/capital change, return test, alpha admission or holdout use occurred. F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen; the legacy holdout remains consumed and unused.


## Follow-up inventory expansion — Phases 277–278

The original Phase 276 allowlist and hosted result covered 28 PR #14 workflow files and 94 action references. Phases 277 and 278 subsequently added two read-only workflows, so the original hard-coded inventory was no longer exhaustive.

The auditor and deterministic tests have now been extended to include both new workflows. The expected inventory is **30 workflows / 100 action references**. Hosted revalidation is pending; until it passes, the original 28-workflow result must not be described as covering the newer Phase 277/278 workflows.
