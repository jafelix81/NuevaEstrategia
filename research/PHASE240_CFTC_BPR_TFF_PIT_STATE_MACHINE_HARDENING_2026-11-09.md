# Phase 240 — CFTC BPR/TFF prospective PIT state-machine hardening

**Date:** 2026-11-09  
**Branch:** `phase231-cboe-option-quotes-full-row-reparse`  
**Hosted validation:** [Run 42643306313 — success](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42643306313)  
**Scope:** Correctness audit of the prospective CFTC capture state machines. This is not an alpha study.

## Executive decision

The hosted regression audit exposed and corrected three defects that could compromise prospective point-in-time (PIT) capture:

1. **BPR revisions were incorrectly labelled as new PIT events.** The BPR capture code distinguished a revision in `receipt_kind`, but its metadata builder still set `event_signal_eligible=True` for every scheduled post-baseline observation. A changed hash for an already-seen report date could therefore appear to be a fresh event.
2. **TFF rollback observations could reset the scheduled comparison state.** The TFF `_latest_scheduled` selector included all scheduled metadata, even a report-date rollback explicitly classified as non-PIT. If the previously current report later reappeared, it could be misclassified as a new report and generate a duplicate event.
3. **BPR metadata JSON was not valid after the first write.** Two metadata writers appended the literal characters `\n` instead of a real newline. The first hosted run caught this as JSON `Extra data` when a later capture attempted to read existing metadata. The writer was corrected and the regression suite now reads the stored metadata successfully.

These are PIT/data-integrity issues, not evidence of predictive alpha. The CFTC capture workflow is still inactive on `main`.

## Corrections

### BPR — revisions are state-only

- Added an explicit `revision` input to the metadata classifier.
- A scheduled revision after the initial baseline is now `NEW_REVISION_STATE_ONLY`.
- The corrected version is preserved and may update the observed state after pipeline receipt.
- `event_signal_eligible` and `pit_eligible_from_pipeline_receipt` remain false for revisions.
- Manual revisions remain non-PIT.
- Fixed both BPR metadata writers to append a real newline, keeping every stored JSON document parseable.
- The regression test checks the stored event type, receipt kind, state usability and non-event classification.

### TFF — invalid rollback cannot replace the last usable state

- `_latest_scheduled` now selects only scheduled records with `state_usable_after_receipt=True`.
- Rollback observations remain append-only and auditable, but cannot become the comparison baseline.
- Added a regression sequence: initial baseline → new report → older-date rollback → restoration of the already-known report. The restoration must be `UNCHANGED`, not a second PIT event.
- Corrected the test fixture's report-type labels to the CFTC values `FutOnly` and `Combined`.

## Hosted regression result

<badge color="success">43/43 passed</badge>

- BPR capture: **13/13** tests passed.
- TFF capture: **30/30** tests passed.
- Both modules and both test files compiled successfully.
- The final hosted run is [42643306313](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42643306313).
- Earlier runs failed first on the malformed BPR JSON terminator and then on the TFF test fixture's stream label. Both were corrected; the final run passed both complete suites.

## Research and operating controls

- No CFTC raw capture was performed in this phase.
- No historical PIT admission or alpha admission.
- No return, bootstrap, LOO, walk-forward or holdout test.
- No data purchase, vendor contact, production change or universe change.
- `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen.
- The legacy holdout remains `CONSUMED_NOT_PRISTINE`.
- The shared BPR/TFF scheduled capture workflow remains inactive on `main` until the stacked PR chain is reviewed and merged by the repository owner.

**Disposition:** retain both CFTC sources as prospective measurement candidates only. The state-machine and persistence defects are corrected and regression-tested; predictive value remains untested.
