# Phase 171 — Cboe Option Trades date-time shape and blank-row audit

**Date:** 2026-11-07  
**Decision:** diagnostic-only. Phase 170's latest public sample has a valid 19/25-column schema and exact row widths, but no rows parse because the strict parser expects ISO dates. Phase 171 records sanitized date/time shape signatures and row-level blankness combinations without storing raw values.  
**Scope:** public Cboe sample only. No licensed history, vendor contact, purchase, return test or production change.

## 1. Why this phase exists

The Phase 170 final-head run [42323305956](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42323305956) completed successfully as a diagnostic workflow, not as a valid-sample gate. Its metadata artifact [13554320538](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42323305956/artifacts/13554320538) reports, for each of the two 2026-01-07 members:

- 98,579 rows with exact row widths (25 columns with Calcs; 19 without).
- 74,999 market_date values shaped as M/D/YYYY and 23,580 blanks.
- 74,999 nonblank quote_datetime values classified only as other, plus 23,580 blanks.
- Zero parsed contracts, underlyings, timestamps or trade keys.
- No evidence of extra or short CSV fields.

The parser must not be loosened until the actual timestamp structure and blank-row semantics are understood.

## 2. Phase 171 diagnostic design

- Reuse Phase 170's bounded ZIP-member reader and official header-schema check.
- Parse market-date candidates only for diagnostic comparison (M/D/YYYY, ISO, or YYYYMMDD); do not admit rows.
- Try a finite, explicit list of quote-datetime formats. Unknown suffixes/timezones remain unparsed.
- Record sanitized character-class signatures (digits become 9, letters become A, punctuation remains), string lengths and shape counts. No raw date/time string is persisted.
- Cross-tab both fields' blankness and count whether non-date core fields remain complete when both date fields are blank.
- Compare parsed market dates with the date embedded in the filename and, when both parse, compare quote-date with market-date.
- Preserve per-member hashes and aggregate counts only.

## 3. Admission rules

A Phase 171 success means only that the diagnostic ran and produced a metadata-only artifact. It does not validate the Cboe sample or admit it to research.

Do not:
- infer market date from quote time when market_date is blank;
- impute missing timestamps;
- treat execution time as first-publication/knowledge time;
- sign prints whose quote/time/condition semantics are unresolved;
- build forward-return features or run alpha/OOS tests.

Even if every nonblank timestamp parses, 23,580 blank-date/time rows per member remain quarantined until their economic meaning is established. The public sample is not a substitute for a complete, contemporaneously delivered historical panel.

## 4. Official source references

- [Cboe Option Trades product page](https://datashop.cboe.com/option-trades)
- [Option Trades File Specification v1.3](https://datashop.cboe.com/documents/Option_Trades_File_Specification.pdf)
- [Cboe DataShop FAQ](https://datashop.cboe.com/faqs)

## 5. Result

Hosted result pending. The report and state file will be amended with the actual metadata-only artifact outcome. No alpha, OOS, holdout or production conclusion is claimed. F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen.
