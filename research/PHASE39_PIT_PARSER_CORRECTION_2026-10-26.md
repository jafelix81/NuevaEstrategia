# Phase 39 — Form 4 PIT parser correction

Date: 2026-10-26

## Finding
The prior Phase 39 feasibility audit reported 0/12 recovered SEC acceptance timestamps. This must **not** be interpreted as evidence that EDGAR lacks a reproducible point-in-time acceptance timestamp.

Current SEC EDGAR submission-header examples expose:

`<ACCEPTANCE-DATETIME>YYYYMMDDHHMMSS</ACCEPTANCE-DATETIME>`

The prior extractor searched for a different literal format (`ACCEPTANCE-DATETIME:`), producing a false negative.

## Consequence
The PIT gate remains technically feasible in principle, but Form 4 is still **not production-feasible for frozen-universe stock selection** under the current evidence because historical security coverage was only approximately 54.6% (2016 Q1), 65.4% (2020 Q1), 76.4% (2024 Q1), and 83.3% (2026 Q3).

Do not run a return/OOS test on the reduced and changing universe merely to obtain an alpha result.

## Required resurrection test
1. Correct acceptance-header parsing and verify on a historical sample.
2. Re-measure frozen-universe coverage after issuer/CIK mapping.
3. Keep transaction-level PIT based on EDGAR acceptance time, not quarterly dataset publication time.
4. Only proceed to alpha testing if coverage passes the frozen-universe gate.

## Status
PIT issue corrected conceptually; coverage gate remains the binding feasibility constraint. No strategy change authorized.
