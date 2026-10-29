# Phase 45 — SEC FTD PIT identity gate

## Objective
Determine whether the public SEC FTD files alone can support a date-appropriate active-universe panel and deterministic CUSIP identity without treating missing observations as zero.

## Rule
A missing ticker/CUSIP in an FTD file is **not** interpreted as zero fails. Presence in an FTD file proves only that an observation exists; it does not prove continuous listing or active-universe membership between files.

## Planned decision
The audit will report observable coverage, repeated observation coverage, and CUSIP continuity, but will not authorize alpha unless historical activity/listing status is independently reproducible with PIT-effective dates.

## Protection
No FTD return test is authorized in this phase. `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen.
