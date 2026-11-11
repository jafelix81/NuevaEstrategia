# Phase 276 — PR #14 GitHub Actions supply-chain and permission audit

**Date:** 2026-11-10 UTC  
**Status:** Action-reference hardening implemented; hosted audit pending.  
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

The Phase 276 static auditor inventories all 28 PR #14 workflow files, rejects mutable or unreviewed action references, checks explicit permissions, rejects pull_request_target, and verifies that the only write-capable workflow is the CFTC capture workflow with its main-branch, non-persistent-credential, scoped-token and additive-only guards.

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

The Phase 276 workflow runs deterministic static tests and emits a metadata-only inventory artifact. Hosted validation is pending after this commit. No hosted result is claimed in advance.

## Research controls

No live CFTC capture, manual dispatch, SEC request, data purchase, vendor contact, PR merge, production/universe/capital change, return test, alpha admission or holdout use occurred. F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen; the legacy holdout remains consumed and unused.
