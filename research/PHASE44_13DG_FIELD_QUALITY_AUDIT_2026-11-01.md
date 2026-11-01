# Phase 44 — 13D/13G field-quality audit — 2026-11-01

## Status
**DATA-QUALITY AUDIT COMPLETE; NO ALPHA TEST AUTHORIZED.**

## Source
Latest successful Phase 35 artifact `phase35-13dg-pit-event-crosswalk-audit` from GitHub Actions run `41281874239`, artifact `13079273599`, SHA-256 `0ff460eb2134566b704fd9ece410cc0b3c2dcd6363af80de31e7b27db008d1fc`.

The artifact contains 20,263 resolved rows across 303 tickers. The production gate remains based on `filing_date` as the conservative knowledge timestamp.

## Field completeness
- `percent_class`: 19,978 / 20,263 = 98.59% non-null.
- `shares_beneficially_owned`: 16,759 / 20,263 = 82.71% non-null.
- `reporting_person_type`: 10,041 / 20,263 = 49.55% non-null.
- `purpose_text`: 261 / 20,263 = 1.29% non-null.

### Interpretation
`percent_class` is sufficiently complete to be the primary ownership-state variable, subject to semantic validation. Shares and voting/dispositive fields are materially less complete and should not be the primary cross-form factor without additional parsing validation. `purpose_text` is too sparse for a general-purpose signal in this artifact.

## Form-specific ownership distributions
Median `percent_class`:
- 13D: 17.80%
- 13D/A: 13.14%
- 13G: 5.80%
- 13G/A: 7.10%

This supports keeping 13D and 13G families separate initially. It does **not** establish predictive power.

## Concentration warning
The panel is extremely concentrated by ticker: BLK 5,380 filings, STT 2,380, MS 1,645, JPM 840, GS 681. Therefore any event-level backtest can be dominated by repeated filings from a small number of financial issuers.

Required controls before alpha:
1. equalized issuer exposure;
2. issuer-clustered uncertainty / bootstrap;
3. event de-duplication at the reporting-group/issuer level;
4. separate results with and without the top concentrated issuers.

## Important semantic warning
A high `percent_class` is not an independent signal because the filing threshold itself creates mechanical selection around 5%. For example, among original filings with non-null `percent_class`, 5,396 of 5,660 observations are >=5%. This is expected from the regulatory trigger and must not be interpreted as evidence of informed buying.

Therefore the economically meaningful variables should be **changes in ownership state** and **new information relative to the prior state**, not the raw ownership percentage alone.

## Next pre-specified test design
After resolving the 27 missing universe tickers and validating reporting-person/ownership semantics:

1. Construct issuer/reporting-group state as of each `filing_date`.
2. Compute delta in `percent_class` versus the immediately preceding known state.
3. Separate 13D/13D-A from 13G/13G-A.
4. Treat original filings and amendments under the two already-approved constructions: PIT-update and original-only.
5. Exclude mechanically triggered threshold level as a standalone feature; test only state changes and economically interpretable transitions.
6. Run chronological OOS tests versus frozen F80/LTM with identical exposure and costs, issuer-clustered bootstrap/LOO, and explicit return-chasing controls.

## Decision
**KEEP / PROCEED.** The dataset is sufficiently complete for ownership-state reconstruction, but raw ownership levels are not an alpha signal by themselves. The next legitimate research object is the amendment-aware ownership-change panel. `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen.
