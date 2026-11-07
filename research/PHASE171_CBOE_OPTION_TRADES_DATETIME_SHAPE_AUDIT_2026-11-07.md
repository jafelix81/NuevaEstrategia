# Phase 171 — Cboe Option Trades date-time shape and blank-row audit

**Date:** 2026-11-07  
**Decision:** diagnostic completed; sample still rejected for flow research. The 74,999 populated rows have a separate market date and a seven-character time-only quote_datetime signature that is not documented by the current v1.3 specification. The other 23,580 rows have both date fields blank and all ten non-date core fields blank. Phase 172 checks whether those records are empty across every column and where they occur.  
**Scope:** public sample only. No licensed history, vendor contact, purchase, return test or production change.

## 1. Hosted result

Phase 171 run [42327762664](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42327762664) completed successfully, passing compilation, **9/9 offline tests**, public sample download, metadata-only artifact upload and the diagnostic-only output contract. Artifact [13556500580](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42327762664/artifacts/13556500580).

For each of the two members (25-column Calcs and 19-column no-Calcs), the 98,579 DictReader records split identically:

| Diagnostic | Rows |
|---|---:|
| Both market_date and quote_datetime blank | 23,580 |
| Both date fields nonblank | 74,999 |
| Only one date field blank | 0 |
| Both date fields blank and all ten non-date core fields blank | 23,580 |
| Both date fields blank but core fields complete | 0 |

For the 74,999 populated records:
- market_date shape is M/D/YYYY; all parse as 2026-01-07.
- All 74,999 parsed market dates match the date in the member filename.
- quote_datetime is nonblank but has length 7 for every row; sanitized signature is 99:99.9.
- All 74,999 quote_datetime values remain unparsed by the explicit full-datetime candidates.
- No raw clock values, rows, symbols or contracts were persisted.

The 23,580 blank date/time rows also have all ten core fields blank. Phase 171 did not inspect every optional field or row position; they are not called empty/padding rows until Phase 172 confirms this.

## 2. Specification conflict

The current [Cboe Option Trades v1.3 specification](https://datashop.cboe.com/documents/Option_Trades_File_Specification.pdf) says market_date is yyyy-mm-dd and quote_datetime is yyyy-mm-dd hh:mm:ss.000 (U.S. Eastern, millisecond precision). The public sample instead has M/D/YYYY market dates and a seven-character time-only shape. This is a material sample/specification mismatch, not a reason to infer missing seconds or silently combine fields.

The current [product page](https://datashop.cboe.com/option-trades) advertises history from January 2012 and all-symbol historical purchase choices, but that does not establish historical first-receipt timestamps or complete per-symbol availability.

## 3. Admission decision

- Keep all 23,580 both-date-blank rows quarantined.
- Do not interpret 99:99.9 as HH:MM plus fractional seconds until Cboe confirms its semantics or a versioned specification/sample demonstrates it.
- Do not synthesize quote_datetime by concatenating market_date and the time-only field.
- Do not use the execution timestamp as feature knowledge time.
- No signed flow, feature panel, forward-return, bootstrap/LOO, chronological OOS or final-holdout test is authorized.

F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen.
