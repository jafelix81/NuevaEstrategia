# Phase 35 — SEC 13D/13G PIT gate V3 — 2026-11-01

## Status
**PARSER/PIT EXTRACTION CONFIRMED; ECONOMIC-DATA GATE STILL PENDING. No alpha authorized.**

## Latest reproducible audit
GitHub Actions run `41346788365` completed successfully on 2026-11-01. Job `124968220154` completed all audit and upload steps successfully. Artifact: `phase35-13dg-pit-event-crosswalk-audit` (artifact `13107210885`). Artifact digest: `sha256:ed92141e1474036291df07c9676129f46a0d304a7a8c21eca425d051f3184236`.

The artifact reproduces the Phase 28D audit over the frozen 335-name universe: 307 CIKs selected, 20,266 filings resolved across 303 issuers, 27 universe tickers unresolved, 0 submission errors, and 0 document-resolution errors.

## PIT extraction result
- `filing_date`: 20,266 / 20,266 (100%).
- `event_date`: 19,680 / 20,266 (97.11%).
- `filing_lag_business_days`: 19,678 observations were reported by the audit, but the current audit summary is **not sufficient to certify that no event dates are after filing dates**.
- `report_date`: 0 / 20,266; not required for the initial PIT knowledge-date gate.
- `filing_date` remains the conservative information-availability timestamp for every signal.

### Correction identified from direct artifact inspection
Direct inspection of artifact `13107210885` found at least two rows where `event_date > filing_date` (both MS / SC 13G: filing dates 2024-02-09 and 2024-02-12 with event date 2024-12-31). The existing audit's `bd_lag()` logic returns a null value for future events, and the summary therefore fails to surface these rows as positive lags. This is a **validation bug in the audit/reporting layer**, not proof that the underlying filings are invalid.

Therefore `event_date` is **not PIT-certified**. It may still be retained for event characterization, but it must never replace `filing_date` for ex-ante signal construction. Before any economic test, the parser/audit must explicitly classify every non-null event date as before/on/after filing date and separately investigate future-event cases and large lags. The conservative knowledge boundary remains `filing_date`.

## Amendment structure
The sample contains 14,542 amendments (71.77%) and 5,724 originals. Event-date missingness is similar for originals (172 / 5,724 = 3.00%) and amendments (414 / 14,542 = 2.85%). The amendment share therefore creates an economic-design issue: an amendment can be a genuine new information update or merely a correction/restatement of an earlier filing.

**Required policy before alpha:** run two pre-specified constructions once the ownership-field validation gate is passed:
1. **PIT-update series:** every filing is an information update available on its filing date, but signal logic must compare the new ownership state with the most recent prior state for the same issuer/reporting group rather than treating every amendment as an independent event.
2. **Original-only event series:** use original 13D/13G filings for entry-event tests and treat amendments only as subsequent ownership-state updates.

The two constructions must be evaluated separately and never selected ex post based on returns.

## Form separation
The artifact contains:
- SC 13D: 215
- SC 13D/A: 1,209
- SC 13G: 5,509
- SC 13G/A: 13,333

The sample is therefore dominated by 13G/13G-A. 13D/13D-A and 13G/13G-A must be modeled separately initially; pooling is not economically justified without evidence that their behavior is comparable.

## Concentration / dependence
The filing distribution is highly concentrated by ticker (e.g. BLK, STT, MS). Future tests must therefore avoid letting repeated filings from a small number of issuers dominate results. Use issuer/ticker clustering and equalized exposure in addition to the frozen baseline's identical exposure/cost framework.

## Remaining economic-data gates
1. Resolve the 27 missing universe tickers and classify each as historical ticker/issuer mapping, true data gap, delisted/survivorship issue, or other.
2. Correct the audit's future-event classification and validate event-date semantics on a stratified sample before using event dates economically.
3. Validate reporting-person type and ownership fields on a stratified sample across 13D, 13D/A, 13G, and 13G/A before creating signal variables.
4. Build the amendment-aware ownership-state reconstruction described above.
5. Pre-specify economically interpretable candidate signals (e.g. new >5% stake, material ownership increase/decrease, concentration change, activist 13D vs passive 13G) before looking at OOS returns.
6. Only then compare incremental information against frozen LTM/F80 using chronological OOS validation, identical exposure/cost assumptions, bootstrap/LOO diagnostics, and explicit return-chasing controls.

## Decision
**Phase 35 extraction: PASS for document retrieval and filing-date PIT; event-date PIT certification: BLOCKED pending audit repair. Economic-data gate: PENDING. No change to `F80_TOP20_PARTIAL50_BASELINE_C20`.**
