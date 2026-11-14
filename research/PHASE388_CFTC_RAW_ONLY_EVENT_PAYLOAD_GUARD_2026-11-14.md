# Phase 388 — CFTC prospective event payload is raw-only

**Date:** 2026-11-14  
**Status:** corrective implementation; no return test, alpha test or signal admission.  
**Parent:** Phase 384 prospective first-receipt capture; Phase 387 prospective crowding-risk preregistration.

## Finding

A code review found that scheduled Phase 384 events included derived features computed by the full current CFTC archive snapshot. That archive is explicitly unverified for historical first-publication availability. The event also copied observed cadence and weekly feature gates calculated over the archive. Although the event kept signal_eligible=false, attaching archive-derived fields created a path for historical backfill to contaminate Phase 387's prospective-only feature history.

This contradicted Phase 387's preregistered rule that only prospectively first-seen reports may form feature thresholds and feature history.

## Correction

- Scheduled event records now contain the raw canonical source row, contract/report key, first-receipt timestamp, hashes, event classification and explicit eligibility flags only.
- Removed archive-derived feature values and archive-derived cadence labels from scheduled event payloads.
- Added explicit metadata: historical_backfill_derived_features_included=false and feature_engineering_policy=RECOMPUTE_FROM_PROSPECTIVE_FIRST_SEEN_EVENTS_ONLY.
- The historical baseline may still contain diagnostic normalized fields, but they are not attached to prospective events and remain signal-ineligible.
- Phase 387 must calculate all rolling ranks, thresholds, changes and cadence gates from the append-only sequence of eligible prospective first-seen events only. Revisions and late arrivals remain excluded and cannot be backdated.

## Validation

Two regression tests assert that event payloads contain raw source fields only, omit archive-derived feature/cadence fields, and keep revisions ineligible. Existing tests continue to cover OI reconciliation, hashes, late arrivals, revisions, manual mode and cadence guards.

This phase does not fetch new CFTC observations, calculate returns, run alpha/OOS/bootstrap/LOO, touch the legacy holdout, or change F80/production.

## Disposition

This is a data-lineage correction, not a research result. Merge only after the hosted regression workflow passes. The first scheduled capture remains on main; this branch does not modify or duplicate the scheduled capture workflow.
