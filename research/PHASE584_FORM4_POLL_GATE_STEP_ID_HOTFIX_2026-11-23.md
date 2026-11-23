# Phase 584 — Form 4 poll-quality gate step-ID hotfix

**Audit cutoff:** 2026-11-23 21:16 UTC  
**Base main:** `e48413a21c6eb40aa3ca06e2aa2080562b425b13`  
**Disposition:** workflow-wiring correction to Phase 583; no data request or research change.

## Finding

A post-merge workflow-file review found that Phase 583's new final quality-gate step referenced `steps.sec_capture.outcome`, but the preceding "Capture Form 4 / 4-A first-seen metadata" step did not yet declare `id: sec_capture`. Without that ID, the condition could evaluate false and skip the intended visible failure on an incomplete feed.

## Correction

Added `id: sec_capture` to the capture step. The final gate now evaluates the actual capture-step outcome and, when capture succeeded, reads `phase476_output/poll_summary.json` after the persistence and artifact-upload steps. It fails the live-capture job if either feed is incomplete.

## Validation and controls

- PR CI is offline-only; the live-capture job remains skipped.
- The Phase 583 regression suite remains the required code gate.
- No manual dispatch, live SEC request, credential access, data mutation or cron change.
- The 50-page bound and fail-closed watermark semantics are unchanged.
- No public-availability certification, signal, event study, alpha or OOS result.
- `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen.
