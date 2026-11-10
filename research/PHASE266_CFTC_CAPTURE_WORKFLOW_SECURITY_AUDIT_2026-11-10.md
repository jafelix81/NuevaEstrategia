# Phase 266 — CFTC BPR/TFF Capture Workflow Security and Deployment Audit

**Date:** 2026-11-10  
**Scope:** Static security review and hardening of the prospective CFTC capture workflow included in PR #14. No live capture was executed.

## Decision

The CFTC capture workflow is suitable for a controlled, research-only deployment **after the stacked PR chain is reviewed and merged in the correct order**, subject to the safeguards below. It is not active on main, and no data capture has occurred.

## Findings and changes

| Finding in the pre-hardening workflow | Risk | Change made |
|---|---|---|
| workflow_dispatch could be selected on a non-main branch while the job had contents:write | A feature-branch version of the capture scripts could run with a write-capable token | Job now runs only when github.ref is refs/heads/main |
| actions/checkout persisted credentials throughout parser and network steps | Write token was available to every process in the job | persist-credentials is now false; GH_TOKEN is exposed only to the commit/push step |
| BPR capture workflow ran the TFF tests but not the BPR capture test suite immediately before capture | BPR parser/state regressions could reach the live capture step | Both BPR and TFF compile/test suites now run before either capture |
| git add -A staged the data folders without rejecting a modified or deleted historical file | A defect could silently rewrite or delete an allegedly append-only PIT archive | Staged changes are checked; anything other than additions fails before commit |
| 10-minute job timeout | Sequential polling of retained BPR reports could exhaust the job budget | Timeout increased to 20 minutes |

The workflow retains only the contents:write permission needed to append snapshots to the repository. The job-level main-branch guard prevents a manual dispatch from running feature-branch code with that permission. The push uses the checked-out main ref, and the token is not present in the checkout's persistent git configuration.

## Static regression contract

Added:

- research/test_phase266_cftc_capture_workflow_security.py
- .github/workflows/phase266_cftc_capture_workflow_security.yml

The seven static tests verify:
1. schedule/manual-only trigger surface (no pull_request or pull_request_target);
2. main-only execution guard;
3. checkout credentials are not persisted;
4. the GitHub token is scoped to the commit step;
5. both BPR and TFF test suites precede network capture;
6. archive commits are additive-only;
7. timeout supports the retained-report polling workload.

Phase 240 was also extended so its next applicable push regression includes the Phase 266 static contract. The earlier Phase 240 run 42878203544 predates the final workflow hardening and is not claimed as validation of these changes. The dedicated Phase 266 workflow is the validation gate for the hardened version.

## Remaining controls and limitations

- The capture workflow remains on the research branch and is not active on main.
- The first scheduled run after deployment must be treated as a baseline state, not a historical event; manual workflow_dispatch remains non-PIT.
- Subsequent new report URLs may become event candidates only from their actual scheduled pipeline receipt time. Revisions remain separate state updates.
- The capture code stores original source responses and hashes under data/cftc_bpr and data/cftc_tff; it does not infer participant identity from CFTC categories.
- The mutable action-tag residual was closed in Phase 273: checkout, setup-python and upload-artifact are pinned to full 40-character commit SHAs. Each SHA was resolved from the official action repository tag and its commit signature was verified. The static contract now rejects unpinned action references. This improves supply-chain reproducibility but does not replace review of upstream action code or a controlled deployment.
- No live BPR/TFF data was captured; no API/vendor purchase, external contact, or terms acceptance occurred.

## Deployment sequence

1. Review PR #13, which targets main.
2. Merge PR #13 only after its full code/research review.
3. Retarget PR #14 from the now-integrated phase99 branch to main, verify its diff is only the follow-on phases, and review the new checks.
4. Merge PR #14 only after explicit user authorization.
5. Confirm the CFTC workflow is present on main and inspect its permissions before allowing the first scheduled baseline.

No PR was merged, no workflow was manually dispatched, and F80/production/universe/capital/holdout remain unchanged.


## Hosted validation

- [Phase 240 CFTC regression run 42878203544](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42878203544): compile, Phase 266 security contract, BPR capture regression, and TFF capture regression steps all succeeded.
- Initial dedicated Phase 266 run 42880706312 passed 7/7 static security tests.
- Latest-head dedicated [Phase 266 run 42881264991](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42881264991), job 130057840322: 7/7 static security tests passed.
- No live CFTC workflow_dispatch or scheduled capture was executed.


## Phase 273 — immutable GitHub Action pinning (2026-11-10)

The only write-capable CFTC workflow was using mutable major-version tags. Pinned its three actions to the commit currently resolved by the official repository tags:

| Action | Ref | Verified commit |
|---|---|---|
| actions/checkout v4 | `11d5960a326750d5838078e36cf38b85af677262` | Signed/verified |
| actions/setup-python v5 | `a26af69be951a213d495a4c3e4e4022e16d87065` | Signed/verified |
| actions/upload-artifact v4 | `ea165f8d65b6e75b540449e92b4886f43607fa02` | Signed/verified |

The Phase 266 static security test now requires exactly these three references and enforces 40-character hexadecimal commit pins for every `uses:` entry. No parser, data-capture, token, permissions, schedule or archive behavior changed.

The update is on the research branch only. It has not been deployed to `main`; no manual or scheduled CFTC capture was executed. Hosted validation is pending the existing Phase 240/266 workflows.