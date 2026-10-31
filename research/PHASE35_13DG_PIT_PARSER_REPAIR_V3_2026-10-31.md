# Phase 35 — 13D/13G PIT parser repair V3 (2026-10-31)

## Finding
The Phase 35 run #52 resolved 20,266 candidate filings with zero resolver errors, but extracted `event_date` for 0/20,266. The wrapper was executing correctly; inspection showed the parser only recognized label→date layouts.

SEC Schedule 13D/13G cover pages can also present the event date before the label, e.g. `10/17/2025 (Date of Event Which Requires Filing of this Statement)`. Therefore the previous parser repairs did not cover the actual document layout.

## Repair
The parser now recognizes both:
- label → date
- date → label

It supports MM/DD/YYYY, ISO YYYY-MM-DD, and month-name dates within a tight context window around the distinctive event-date label. `filing_date` remains the conservative PIT knowledge date.

Regression tests now include both layouts and month-name dates.

## Gate decision
13D/13G remains **DATA/PARSER FAIL — no alpha test authorized** until the new audit demonstrates non-zero event-date coverage and adequate historical/universe coverage.

## Execution
The main workflow was changed only to force-fetch the latest `phase35-13dg-parser-repair` branch and print its exact head SHA before execution. This prevents stale branch materialization.

Baseline `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen and untouched.
