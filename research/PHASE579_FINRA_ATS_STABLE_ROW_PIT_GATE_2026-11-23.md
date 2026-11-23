# Phase 579 — FINRA ATS stable-row PIT gate implementation

**Date:** 2026-11-23  
**Base:** `main` at `6febc8669e6ea5b0c045bddf60a91d190a2ddf04`  
**Branch:** `phase579-finra-ats-stable-row-pit-gate`  
**Disposition:** Implement a deterministic, fail-closed metadata gate from Phase 578's official field semantics. Synthetic tests only. No FINRA API calls, raw data, security-master sample, return test, alpha test or signal admission.

## Why this phase

Phase 578 resolved the public meaning of `initialPublishedDate`, `lastReportedDate` and `lastUpdateDate` but was documentation-only. The older Phase 374/375 implementation remains on a severely diverged branch and cannot be merged as-is. This phase creates a small independent mainline candidate that translates the corrected rule into tested executable logic without importing old branch dependencies.

## Implemented rules

For each symbol-week:
1. Require `ATS_W_SMBL` aggregate rows; accept only the two known symbol-grain summary types.
2. Require valid `weekStartDate`, `initialPublishedDate`, `lastReportedDate` and `lastUpdateDate`.
3. Require the publication lag to be 21 or 22 calendar days.
4. Enforce FINRA's documented `lastUpdateDate = max(initialPublishedDate, lastReportedDate)`.
5. Admit the initial-publication clock only if `lastReportedDate <= initialPublishedDate`, `lastUpdateDate = initialPublishedDate`, and all rows in the group share one publication date.
6. Choose the first supplied regular session whose date is strictly later than the publication date. Never use the publication date itself.
7. Treat security identity separately. A ticker mapping must be effective on the report week, record-known no later than the next session open, explicitly marked as having certified record-time semantics, and uniquely identify listing/security/issuer. A Databento `ts_record` value must not be marked certified until the vendor's semantics and update lag are confirmed in writing.
8. Calculate concentration eligibility separately: aggregate and firm totals must reconcile; MPID rows must be complete and unique; De Minimis buckets block participant concentration but do not automatically invalidate the stable aggregate PIT row.
9. Hard-code economic-test eligibility and signal admission to false. Historical universe membership and complete total-return/delisting coverage remain separate mandatory gates.

## Tests

The new offline test suite covers:
- Stable row / next-session boundary.
- Revised rows and update-date semantic mismatch.
- 21/22-day publication-lag guard.
- Common publication date across symbol-week rows.
- Duplicate product-type rows and missing aggregate rows.
- Uncertified or late identity record clocks.
- Unique, ambiguous and ineffective security mappings.
- Aggregate/firm reconciliation and MPID/De Minimis concentration gates.
- Missing future executable session.

The workflow is offline-only. It does not contain secrets, network access, a live FINRA step, raw source artifacts or vendor calls.

## Explicitly not established

- No current or historical FINRA rows were processed.
- No actual stable-row counts were recomputed.
- No Databento or CRSP identity mappings were acquired or certified.
- No historical F80 membership or original F80 selection rule was reconstructed.
- No prices, corporate actions, delisting returns or total-return labels were joined.
- No returns, alpha, OOS, bootstrap, LOO or holdout tests were run.

## Decision

This phase makes the PIT admission logic reproducible and testable; it does not unlock a FINRA economic test. The binding gates remain authorized effective-dated security-master coverage, historical universe membership, and complete active/inactive total-return history. Keep `F80_TOP20_PARTIAL50_BASELINE_C20` frozen. No production or portfolio changes.
