# Phase 50 — Global Form 144 index performance and repair audit

Date: 2026-11-04  
Branch: `phase50-sec-form144-feasibility`  
Status: corrected runner executing; source-coverage gate pending.

## Runs and artifacts inspected

- [Run 41761510120](https://github.com/jafelix81/NuevaEstrategia/actions/runs/41761510120), job `126350027887`: parser tests passed. The 2025Q1 global-index pilot reached the last logged checkpoint of 8,250 / 9,104 filing-detail pages (90.62%) with zero retrieval errors, then was cancelled at the 4-hour job limit. Artifact `13301099862` contains the official `master.idx.gz` only; the original runner wrote the detailed census only after completing all page requests.
- [Run 41761577180](https://github.com/jafelix81/NuevaEstrategia/actions/runs/41761577180): failed before network work because a new sample-selection test accessed `row["form"]`, while real index rows carry `master_index_form`. This was a test-schema defect, not a filing-data defect.
- [Run 41787228798](https://github.com/jafelix81/NuevaEstrategia/actions/runs/41787228798): triggered by the script commit before the test correction reached the branch; it failed at the same stale test.
- [Run 41787233183](https://github.com/jafelix81/NuevaEstrategia/actions/runs/41787233183): includes both corrections. All nine parser/PIT tests passed; the 2025Q1 global-index pilot is running. No further execution was started. The GitHub job-log blob was temporarily unavailable while the job was active, so progress must be checked from the run/job status until logs become available.

## Independent recomputation of the partial master-index artifact

The downloaded official 2025Q1 `master.idx.gz` was decompressed and parsed locally.

| Measure | Count |
|---|---:|
| Raw master-index rows for 144 / 144-A | 18,208 |
| Raw 144 rows | 18,028 |
| Raw 144/A rows | 180 |
| Unique accessions after grouping | 9,104 |
| Unique original 144 accessions | 9,014 |
| Unique 144/A accessions | 90 |
| Form-conflict accessions | 0 |
| Accessions with two master-index entity rows | 9,104 |

The two raw master-index rows per accession are retained as separate CIK/name observations and must not be double-counted as two notices. This global census confirms that the earlier v2 CIK-query sample (196 unique accessions, all 144/A) was severely amendment-biased.

The partial page-fetch run's last progress log showed 8,250 / 9,104 pages parsed and zero errors. This is not a completed coverage audit: 854 pages remained at the last checkpoint, and Subject/Reporting/accepted-timestamp rates are not yet computed.

## Runner repair

The pilot was taking too long because 9,104 independent filing-detail pages were fetched sequentially. The corrected runner now:

- Uses five worker threads to hide network latency.
- Reserves SEC request slots through a shared lock at a conservative 0.20-second minimum interval (maximum planned rate approximately five requests per second, below the SEC's published ten-request-per-second ceiling).
- Writes resumable partial census/error CSV checkpoints every 500 completed accessions.
- Sorts sampled rows using `master_index_form` with a backward-compatible `form` fallback.
- Corrects the unit test to assert against the actual `master_index_form` field.

The partial checkpoint is diagnostic/recovery output only; it does not turn an incomplete run into a PASS. The next completed run must still satisfy the preregistered page retrieval, Subject CIK, accepted timestamp, form/date agreement, and separate original/amendment XML gates.

## Decision

- The 2025Q1 master index demonstrates a substantial original-notice population: 9,014 original accessions versus 90 amendments.
- Form 144 remains conditional until the full detail-page census and stratified XML checks complete.
- No forward returns or alpha tests are authorized.
- Current CIK mapping is discovery-only, not historical PIT F80 membership.
- `approxSaleDate` remains descriptive only; it is not evidence of execution or a KnowledgeDate.
- `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen.
