# Phase 35 — SEC 13D/13G PIT gate — 2026-10-30

## Status
**REPAIR STAGED — parser/event-date extraction + SEC rate limiting. No alpha authorized.**

## Latest reproducible audit
Run `41065549739`, job `124095815524`, completed successfully on 2026-10-30. Artifact: `phase35-13dg-pit-event-crosswalk-audit` (artifact `12989758455`).

The audit used the frozen 335-name universe and resolved 19,706 filings across 303 issuers. It selected 307 CIKs and left 27 universe tickers unresolved. There were 560 document-resolution errors, all attributable to SEC HTTP 429 responses in the sampled errors.

### Critical finding
The generated CSV contains **0/19,706 non-null `event_date` values**. This is not evidence that SEC 13D/13G filings lack an event date. The parser required the date to appear immediately after the field label and therefore missed common parenthetical formats such as `(MM/DD/YYYY)`. The audit summary also contained a reporting bug: `field_coverage` counted `False` booleans as present, making the prior `event_date_available` field misleading; the authoritative count was 0.

## Repair staged
Branch: `phase35-13dg-parser-repair`

Commit: `e904f0d77db561dc8c566291a83c5316634e384c`

The repair:
- accepts optional parenthetical date-format labels and common separators;
- accepts both MM/DD/YYYY and ISO dates;
- serializes SEC requests through a global throttle so concurrent workers cannot bypass the rate limit;
- honors `Retry-After` on HTTP 429 and uses exponential backoff with jitter;
- reduces network concurrency while preserving parallelism at the job level;
- fixes the `field_coverage` boolean-counting bug;
- adds regression tests for parenthetical, colon, ISO, and missing-date cases.

The main-branch audit record was updated to trigger the existing Phase 35 runner. That runner fetches the repaired audit script from the repair branch, so no separate duplicate workflow was launched.

## PIT interpretation
`filing_date` remains the conservative knowledge date for information contained in the filing. `event_date` is useful for event characterization and lag analysis, but it must never be substituted for the PIT knowledge date.

## Gate required before alpha
The repaired full audit must demonstrate high coverage for both filing dates and parsed event dates, acceptable unresolved-ticker coverage, and no material silent loss from SEC rate limiting. Only then may pre-specified 13D/13G signals be tested for incremental information versus frozen LTM/F80 using chronological OOS validation.

## Decision
**Do not run alpha from the prior artifact. Do not modify `F80_TOP20_PARTIAL50_BASELINE_C20`. Do not interpret 13D/13G as predictive until the repaired parser and coverage gate pass.**

This remains a data-quality gate, not an alpha result.
