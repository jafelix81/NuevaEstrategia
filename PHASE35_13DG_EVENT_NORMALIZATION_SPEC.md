# Phase 35 — 13D/13G Event Normalization Specification

Updated: 2026-11-03

## Purpose
Convert the completed SEC 13D/13G issuer-level PIT audit into a deterministic event dataset before any return test. This document is a preregistration guardrail: it defines what counts as an event and what must be excluded before looking at forward returns.

## Data gate already passed
- Frozen universe: 335 names.
- Selected issuer CIKs: 307.
- Candidate/resolved filings in the corrected artifact: 20,266.
- Unique issuers: 303.
- Amendments: 14,542 in the current artifact.
- Event date available: 19,680 / 20,266 (97.11%).
- SEC submission/resolution errors: 0 in the completed artifact.
- KnowledgeDate = `filing_date`; no field from a filing may be used before that timestamp.
- Artifact: `phase35-13dg-pit-event-crosswalk-audit`.

## Immediate normalization observations
- Forms: SC 13G = 5,509; SC 13G/A = 13,333; SC 13D = 215; SC 13D/A = 1,209.
- 71.76% of rows are amendments, so filing-count signals would materially double-count economic positions.
- `reporting_person` is populated on only 3,502 rows and `purpose_text` on only 261 rows; therefore those fields cannot be the sole grouping keys.
- `report_date` is not populated in the current extracted table and must not be substituted for KnowledgeDate.

## Event construction rules
1. **Separate 13D and 13G families.** Never pool them in the primary hypothesis.
2. **Treat each accession as an observation of a beneficial-owner disclosure, not automatically as a new economic event.**
3. **Original/amendment chain:** an amendment is linked to the same issuer + reporting group/filing lineage where deterministically identifiable. If lineage cannot be established, retain it as a disclosure but exclude it from the first event-level alpha test rather than guessing.
4. **First-observable event:** for a reporting group/issuer pair, the first filing whose KnowledgeDate is in the active universe is eligible as the first observable disclosure event. Later amendments are not separate events unless they create a materially different ownership-state transition under a predeclared threshold.
5. **Ownership-state transition:** candidate transitions require a change in beneficial ownership percentage or voting/dispositive position that is observable in the filing. Do not infer a buy/sell from price movement, market cap, or subsequent filings.
6. **Direction:** increase/decrease/no-change must be derived only from two sequential observable ownership states for the same deterministic group/issuer identity. If the prior state is missing or ambiguous, classify as `unknown` and exclude from directional tests.
7. **13D mechanism split:** retain a separate `activist/control` hypothesis only when purpose/control information is actually available. Missing purpose text is not evidence of activism.
8. **13G mechanism split:** retain a separate passive/institutional hypothesis; do not assume that every 13G filer is informed or that every increase is bullish.
9. **Same-day leakage guard:** an event can enter a signal only after its `filing_date`; a signal evaluated on the same date must exclude that filing unless the portfolio framework explicitly models intraday filing timestamps.
10. **Active-universe guard:** issuer must be a member of the historical investable F80 universe as of the signal date. Current ticker membership is insufficient.
11. **Forward return isolation:** no return, volatility, rank, threshold, or feature selection may use information after KnowledgeDate.

## First economic hypothesis (pre-registered)
The initial test will not be a generic “smart money buys” score. It will test whether **newly disclosed 13D ownership/control events**, separated from 13G events, contain incremental cross-sectional information about subsequent equity returns after controlling for the frozen LTM/F80 signal.

Primary comparison:
- treatment = first observable qualifying 13D ownership/control transition;
- control = otherwise eligible F80 names on the same signal date;
- baseline = frozen LTM/F80 ranking without the 13D variable;
- identical exposure, transaction costs and portfolio construction for baseline and augmented variants.

The 13G family will be tested independently only if 13D coverage is adequate. No sign/direction or holding horizon will be chosen from the final OOS sample.

## Validation protocol
- Chronological train/validation/final-OOS split.
- Any threshold or feature choice is made only in training/validation.
- Final OOS is touched once.
- Report raw spread and incremental spread versus F80/LTM.
- Use block bootstrap appropriate for overlapping holding periods.
- Include LOO/stability diagnostics and cross-period sign consistency.
- Distinguish announcement-day/short-window effects from persistent post-disclosure behavior.
- If the signal only works in the announcement window and disappears thereafter, classify it as event/price-reaction rather than persistent portfolio alpha.
- If incremental confidence intervals include zero and there is no economically stable mechanism, kill the hypothesis rather than tune it.

## Explicit exclusions
- No use of event_date as KnowledgeDate.
- No use of amendment filing counts as a proxy for conviction.
- No fuzzy reporting-person aggregation when multiple plausible groups exist.
- No optimization of holding period after observing OOS results.
- No modification of `F80_TOP20_PARTIAL50_BASELINE_C20` without robust independent OOS evidence.

## Next gate
Before any forward-return calculation, produce an audit containing:
1. deterministic original/amendment lineage coverage;
2. deterministic reporting-group coverage;
3. issuer-level active-universe coverage by historical period;
4. counts of eligible 13D and 13G first-observable events;
5. percentage of events classified as increase/decrease/unknown;
6. exclusion counts and reasons.

Only if these gates pass will the economic test be executed.
