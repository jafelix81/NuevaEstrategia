# Phase 39 — Form 4 PIT parser correction

Date: 2026-10-27

## Findings
The prior Phase 39 feasibility audit contained two distinct parser issues that must not be interpreted as data-source failures.

### 1. EDGAR acceptance timestamp
The prior acceptance-time extractor searched for the wrong literal form. SEC EDGAR filing headers expose:

`<ACCEPTANCE-DATETIME>YYYYMMDDHHMMSS</ACCEPTANCE-DATETIME>`

Therefore the earlier 0/12 acceptance-timestamp result was a parser false negative, not evidence that EDGAR lacks a reproducible PIT timestamp.

### 2. SEC quarterly dataset delimiter
The representative SEC insider-transaction files are TSV, not comma-delimited CSV. The previous schema audit used Python `csv.reader` with the default comma delimiter. Consequently the 2012 Q1 audit reported all required SUBMISSION fields as missing even though the ZIP download and file members were valid.

The workflow has now been corrected to parse headers with `delimiter='\t'`.

## Consequence
The Phase 39 actual-file schema/history gate is not yet passed because the corrected workflow must execute successfully before the schema result is accepted.

The PIT gate remains conceptually feasible through EDGAR acceptance datetime. However, the frozen-universe security-coverage constraint remains binding: prior research measured approximately 54.6% (2016 Q1), 65.4% (2020 Q1), 76.4% (2024 Q1), and 83.3% (2026 Q3) coverage. Those figures are insufficient for a clean frozen-universe alpha test if the missing coverage is changing through time.

## Required resurrection test
1. Run the corrected TSV schema audit on representative historical periods.
2. Reconstruct accession-level EDGAR acceptance timestamps on a historical sample.
3. Re-measure frozen-universe issuer/CIK/security coverage.
4. Require stable, ex-ante coverage before any return/OOS test.
5. If coverage fails, archive/kills the hypothesis for the frozen universe rather than testing a changing subset.

## Status
**ACTUAL-FILE SCHEMA GATE — RETRY PENDING.**
No strategy change authorized. F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen.
