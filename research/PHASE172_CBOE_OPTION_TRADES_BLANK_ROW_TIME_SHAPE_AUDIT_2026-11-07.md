# Phase 172 — Cboe Option Trades blank-row and time-only audit

**Date:** 2026-11-07  
**Decision:** diagnostic-only. Phase 171 found 23,580 rows per member with both date fields and all ten core trade fields blank, plus 74,999 populated records whose quote_datetime has the sanitized shape 99:99.9. Phase 172 measures whether the blank records are empty across every column and where they occur in the file. It validates the time-only clock range without assigning seconds or constructing timestamps.  
**Scope:** public sample only; no licensed history, vendor contact, purchase, return test or production change.

## 1. Diagnostic questions

- Are the 23,580 rows empty across all 19/25 columns, or do optional/Calcs fields contain values?
- Are empty records contiguous at the end, one internal block, or interspersed?
- Does every nonblank quote_datetime match the exact shape HH:MM.d and fall within valid hour/minute ranges?
- Do all populated market_date values still match the date in the filename?

A trailing all-column-empty block is labelled only TRAILING_PADDING_CANDIDATE. The audit does not delete rows or admit them.

## 2. PIT and parser rules

The time-only field is not converted into a timestamp. The final digit's unit is unknown; no fractional-second or fractional-minute interpretation is assumed. market_date and quote_datetime remain separate raw fields. First receipt and immutable historical vintages remain unverified.

## 3. First hosted attempt and correction

Run [42328080147](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42328080147) compiled successfully but one of 7 offline tests failed before the public sample download. The fixture intended to contain only trade_price while both date fields were blank, but the shared row helper left the other core/quote fields populated. The assertion correctly exposed a fixture construction error; the audit's nonblank-field counter behaved as written. No public sample was downloaded and no artifact was produced. The fixture is corrected to start with every field blank and set only trade_price.

## 4. Result

Corrected hosted run pending. No alpha/OOS/holdout or production conclusion is claimed. F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen.
