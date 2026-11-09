# Phase 240 — CFTC BPR/TFF prospective PIT state-machine hardening

**Date:** 2026-11-09  
**Branch:** `phase231-cboe-option-quotes-full-row-reparse`  
**Scope:** Correctness audit of the prospective CFTC capture state machines. This is not an alpha study.

## Executive decision

Two defects could have produced false event labels if the prospective capture workflow were activated unchanged:

1. **BPR corrections were incorrectly labelled as new PIT events.** The BPR capture code distinguished a revision in `receipt_kind`, but its shared metadata builder still set `event_signal_eligible=True` for every scheduled post-baseline observation. A changed hash for an already-seen report date could therefore appear to be a fresh event.
2. **TFF rollback observations could reset the scheduled comparison state.** The TFF `_latest_scheduled` selector included all scheduled metadata, even a report-date rollback explicitly classified as non-PIT. If the previously current report later reappeared, it could be misclassified as a new report and generate a duplicate event.

Both issues affect PIT integrity, not just labels in a report. They are corrected before the CFTC capture workflow is activated.

## Corrections

### BPR — revisions are state-only

- Added an explicit `revision` input to the metadata classifier.
- A scheduled revision after the initial baseline is now `NEW_REVISION_STATE_ONLY`.
- The corrected version is preserved and may update the observed state after pipeline receipt.
- `event_signal_eligible` and `pit_eligible_from_pipeline_receipt` remain false for revisions.
- Manual revisions remain non-PIT.
- The regression test now checks the stored event type, receipt kind, state usability and non-event classification.

### TFF — invalid rollback cannot replace the last usable state

- `_latest_scheduled` now selects only scheduled records with `state_usable_after_receipt=True`.
- Rollback observations remain append-only and auditable, but cannot become the comparison baseline.
- Added a regression sequence: initial baseline → new report → older-date rollback → restoration of the already-known report. The restoration must be `UNCHANGED`, not a second PIT event.

## Regression coverage

- BPR capture suite: 13 test cases, including the revised revision-state assertion.
- TFF capture suite: 30 test cases, including the rollback/restoration sequence.
- Added a focused GitHub Actions workflow to compile both modules and run both suites on this PR.
- Hosted execution is pending at the time this report was authored; no test pass is claimed until the run is inspected.

## Research and operating controls

- No CFTC raw capture was performed in this phase.
- No historical PIT admission or alpha admission.
- No return, bootstrap, LOO, walk-forward or holdout test.
- No data purchase, vendor contact, production change or universe change.
- `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen.
- The legacy holdout remains `CONSUMED_NOT_PRISTINE`.
- The shared BPR/TFF workflow remains inactive on `main` until the stacked PR chain is reviewed and merged by the repository owner.

**Disposition:** retain both CFTC sources as prospective measurement candidates only. These fixes remove two known PIT state-machine hazards; they do not establish predictive value.
