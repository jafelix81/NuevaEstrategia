# Phase 35 — SEC 13D/13G PIT gate V2 — 2026-10-31

## Status
**PARSER/PIT EXTRACTION PASS; ECONOMIC DATA GATE NOT YET PASSED. No alpha authorized.**

## Latest reproducible audit
Run `41213759858`, job `124573917948`, completed successfully on 2026-10-31. Artifact: `phase35-13dg-pit-event-crosswalk-audit` (artifact `13053597414`).

The audit used the frozen 335-name universe, selected 307 CIKs, resolved 20,266 filings across 303 issuers, and left 27 universe tickers unresolved. There were **0 submission errors and 0 document-resolution errors**.

### Parser result
`event_date` is available for **19,680 / 20,266 filings (97.11%)**. This resolves the prior parser failure: the earlier audit had 0 event dates because the parser assumed the date followed the field label. The repaired parser now handles the common SEC form `DATE (Date of Event Which Requires Filing...)` as well as other supported formats.

`filing_date` is available for all 20,266 filings and remains the conservative PIT knowledge date. `report_date` remains unavailable in the current extraction and is not required for the initial PIT gate.

The filing/event lag is available for 19,678 filings and is never positive in the current artifact; this is consistent with the event date generally preceding the filing date. This field is for event characterization only and must not replace the PIT knowledge date.

### Amendments
The dataset contains **14,542 amendments (71.77%)** and 5,724 original filings. Event-date missingness is similar for originals (172 / 5,724 = 3.00%) and amendments (414 / 14,542 = 2.85%). Therefore, the high amendment share is not by itself a parser/data-loss defect, but amendments must be treated explicitly in any economic signal construction to avoid double-counting or using stale/updated ownership information incorrectly.

### Form composition
- SC 13D: 215
- SC 13D/A: 1,209
- SC 13G: 5,509
- SC 13G/A: 13,333

The current sample is therefore dominated by 13G/13G-A institutional/passive-style filings. 13D/13D-A is much smaller and should be analyzed separately rather than pooled blindly.

### Concentration diagnostic
Filings are highly concentrated by ticker (e.g. BLK 5,383; STT 2,380; MS 1,645). Any alpha test must therefore use issuer/ticker-level clustering and/or equalized exposure so that repeated institutional filings do not mechanically dominate the cross-sectional result.

## Remaining data gate
Before alpha testing, the following must be resolved:
1. Explain or control the 27 unresolved universe tickers; quantify whether they are historical ticker/issuer changes rather than survivorship loss.
2. Define a reproducible amendment policy. Preferred initial policy: treat each filing as a PIT information update, but avoid counting an amendment as an independent new event when it does not change economically relevant ownership information; test original-only and update-aware variants separately.
3. Separate 13D/13D-A from 13G/13G-A. Do not assume both represent the same economic behavior.
4. Validate reporting-person and ownership-field parsing on a stratified sample before using them as signal variables.
5. Preserve `filing_date` as the information-availability timestamp for all signal construction.

## Alpha authorization rule
No 13D/13G alpha test is authorized until the above data gates pass. Once passed, test only pre-specified signals against frozen LTM/F80 with chronological OOS validation, identical exposure/cost assumptions, bootstrap/LOO diagnostics, and explicit tests for return-chasing versus predictive information.

## Decision
**Phase 35 parser/PIT extraction: PASS. Economic-data gate: PENDING. No modification to `F80_TOP20_PARTIAL50_BASELINE_C20`.**
