# Phase 35 — SEC 13D/13G PIT gate — 2026-10-30

## Status
**BLOCKED — parser/event-date extraction + SEC rate limiting. No alpha authorized.**

## Latest reproducible audit
Run `41065549739`, job `124095815524`, completed successfully on 2026-10-30. Artifact: `phase35-13dg-pit-event-crosswalk-audit` (artifact `12989758455`).

The audit used the frozen 335-name universe and resolved 19,706 filings across 303 issuers. It selected 307 CIKs and left 27 universe tickers unresolved. There were 560 document-resolution errors, all attributable to SEC HTTP 429 responses in the sampled errors.

### Critical finding
The generated CSV contains **0/19,706 non-null `event_date` values**. This is not evidence that SEC 13D/13G filings lack an event date. Inspection of the current parser shows the extraction rule is too narrow:

```text
DATE OF EVENT WHICH REQUIRES FILING\s*:?\s*([0-9]{1,2}/[0-9]{1,2}/[0-9]{4})
```

It does not allow the common intervening parenthetical label `(MM/DD/YYYY)` or equivalent whitespace/separator variants. The audit summary also contains a reporting bug: `field_coverage` counts `False` booleans as present, so `event_date_available: 19706` in `field_coverage` is misleading; the authoritative `event_date_available` count is 0.

## PIT interpretation
`filing_date` remains a defensible conservative knowledge date for information contained in the filing. `event_date` is economically useful for event characterization and lag analysis, but it must not be substituted for the PIT knowledge date. No alpha test should use an event date as though it were known before filing.

## Required repair before alpha
1. Replace the event-date regex with a robust pattern that permits optional parenthetical text and separators between the field label and the date, e.g. conceptually:
   `DATE OF EVENT WHICH REQUIRES FILING(?:\s*\([^)]*\))?\s*[:\-]?\s*(MM/DD/YYYY)`
2. Add unit tests covering HTML/XBRL/plain-text variants and at least one known 13D and one known 13G filing.
3. Implement SEC request throttling/backoff with persistent caching so the 560 HTTP 429 errors do not become silent coverage loss.
4. Re-run the full PIT audit and require high coverage for both `filing_date` and parsed event date before proceeding.
5. Only after the data gate passes, construct pre-specified 13D/13G signals and test incremental information versus frozen LTM/F80 with chronological OOS validation.

## Decision
Do **not** run alpha from the current artifact. Do **not** modify `F80_TOP20_PARTIAL50_BASELINE_C20`. Do **not** interpret 13D/13G as predictive until the repaired parser and coverage gate pass.

This result is a useful kill/gate finding: the apparent lack of event dates is a parser failure, not evidence against the source itself.
