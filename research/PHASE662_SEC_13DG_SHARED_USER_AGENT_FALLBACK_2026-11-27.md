# Phase 662 — SEC 13D/G shared User-Agent fallback

**Audit cutoff:** 2026-11-27 11:07 UTC  
**Base:** `main` at `a26af600c05823d5379741a7b0f55918c37891a5`  
**Branch:** `phase662-sec13dg-shared-user-agent-fallback`  
**Disposition:** operational blocker corrected in code; live 44-header sample remains manual-dispatch-only.

## 1. Why this phase was necessary

Phase 616's bounded 44-accession global-index sample called `validate_user_agent(os.environ.get("SEC_USER_AGENT"))` directly. If the repository secret was absent or placeholder-like, the workflow stopped before its first SEC request.

This was inconsistent with the established SEC transport resolver already adopted in Phase 635 / Phase 614: prefer a valid `SEC_USER_AGENT` secret, otherwise reuse the existing project contact `research.phase401_form144a_full_parent_identity_census.SEC_UA`. The fallback is not a new credential and is not printed or persisted.

## 2. Correction

- Added `configure_user_agent()` to Phase 616.
- A valid secret takes precedence.
- Missing or placeholder-like secret falls back to the existing Phase 401 project contact.
- If both are invalid, the function fails closed before any request.
- The live sample continues to use the same 5 preregistered quarterly master indexes, deterministic 44-header sample, request delay, identity gates and artifact outputs.
- The workflow remains manual-dispatch-only. No schedule, trigger, rate, sample size or permission change was made.

## 3. Regression coverage

The hosted Phase 616 PR workflow [run 45988359829](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45988359829) completed successfully: **34/34 combined Phase 616 + Phase 485 tests passed**. The offline job succeeded and the live-sample job was skipped as designed for a pull-request event; no artifact or SEC request was expected.

Four new tests cover missing-secret fallback, placeholder-secret fallback, valid-secret precedence, and fail-closed behavior when both values are invalid. The existing validation tests remain in place.

## 4. Research controls

This phase only resolves transport configuration. It does not retrieve SEC data or change the sample's interpretation.

- No SEC request or live workflow dispatch was made.
- No primary schedules, holdings, ticker mapping, historical F80 membership, prices or returns were downloaded or inferred.
- No event study, alpha, OOS, bootstrap, LOO or holdout test was run.
- `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen.
- No vendor contact or purchase; data budget USD 0.

## 5. Next gate

After this PR's offline regression passes, the remaining operation is one bounded maintainer-initiated workflow dispatch with `run_live_sample=true`. The existing Phase 616 workflow is intentionally manual-only; the available GitHub integration can inspect runs and artifacts but cannot dispatch workflows. Do not run the legacy F80-filer-only Phase 49 workflow.

## 6. Merge

- PR [#252](https://github.com/jafelix81/NuevaEstrategia/pull/252) passed hosted regression and was squash-merged into `main` as commit [`8a095a8`](https://github.com/jafelix81/NuevaEstrategia/commit/8a095a8675f28c29da923254d6c809d06f294b1c).
