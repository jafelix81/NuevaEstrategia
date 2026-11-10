# Phase 273 — CFTC capture workflow immutable-action pinning

**Date:** 2026-11-10 UTC  
**Scope:** Supply-chain hardening of the only write-capable CFTC BPR/TFF capture workflow in PR #14. No live capture or deployment.

## Finding

Phase 266 had already reduced the write-token exposure: the job is restricted to `main`, checkout does not persist credentials, the GitHub token is scoped to the final commit/push step, and raw archive commits are additive-only. One residual remained: the three official GitHub Actions were referenced by mutable major-version tags.

A tag can be moved. For a workflow with `contents: write`, pinning the exact reviewed action commit makes the dependency used by a future run reproducible and prevents a later tag movement from silently changing the action code.

## Change

The official action repository tags resolved to these commits at audit time:

| Action | Official tag | Pinned commit | Signature |
|---|---|---|---|
| actions/checkout | v4 | `11d5960a326750d5838078e36cf38b85af677262` | Verified |
| actions/setup-python | v5 | `a26af69be951a213d495a4c3e4e4022e16d87065` | Verified |
| actions/upload-artifact | v4 | `ea165f8d65b6e75b540449e92b4886f43607fa02` | Verified |

The workflow now uses those full 40-character SHAs. The Phase 266 static contract was extended to:
- require exactly three action references in the write-capable workflow;
- require each reference to end in a full 40-character hexadecimal SHA;
- require the three exact verified commits above.

No data-capture parser, URL, filename, timestamp, schedule, permission, token exposure, append-only rule or PIT classification was changed.

## Validation

- The existing Phase 240 workflow exercises the CFTC BPR/TFF parser/state tests and the Phase 266 security contract.
- The existing Phase 266 workflow exercises the static workflow-security contract.
- Both are expected to trigger from the research-branch update; no duplicate workflow was created.
- Hosted results are pending at report creation. This report must be amended with actual run IDs and conclusions before claiming hosted validation.

## Decision

**Supply-chain tag-mutation residual closed at the workflow-reference layer; deployment gate remains closed.**

This does not prove that upstream action code is vulnerability-free, nor does it replace review of transitive dependencies. The workflow remains inactive on `main`. No manual dispatch, scheduled capture, merge, external contact, data purchase, production change, universe change or holdout use occurred.

`F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen.
