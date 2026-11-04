# Phase 50 v2 post-run audit — 2026-11-04

## Executions inspected

- Canonical latest run: [41754622148](https://github.com/jafelix81/NuevaEstrategia/actions/runs/41754622148), branch `phase50-sec-form144-feasibility`, commit `edde37eef89b228ba4c8836c170cf4f19ba59459`.
- Job: `126329159465`, completed successfully.
- Artifact: `13287867124`, `phase50-form144-pit-feasibility-v2`.
- Eight parser/PIT regression tests passed.
- Earlier run [41754580436](https://github.com/jafelix81/NuevaEstrategia/actions/runs/41754580436) also completed successfully with the same six-file artifact structure. The latest run is treated as canonical; the earlier run is not an independent sample.
- No Actions runs were in progress at the time of inspection.

## Recomputed artifact facts

| Metric | Result |
|---|---:|
| Frozen candidate tickers | 335 |
| Current CIK-mapped tickers | 301 |
| CIK queries | 301 |
| Query errors | 0 |
| Tickers with at least one hit | 91 |
| Distinct candidate CIKs with hits | 90 |
| Retrieved hits (including duplicates) | 198 |
| Unique accessions | 196 |
| Unique original Form 144 | 0 |
| Unique Form 144/A | 196 |
| XML validation sample | 50 |
| Sample Form 144 | 0 |
| Sample Form 144/A | 50 |
| XML parse / subject match / accepted timestamp / form agreement | 50/50 each |
| Required XML field presence | 100% in this sample |
| previousAccessionNumber present | 50/50 |

The v2 query path returned amendments only. Its `data_gate=PASS` is therefore reinterpreted as a technical pass for the sampled 144/A amendment documents, not a source-wide Form 144/144-A coverage pass.

## Date-parser defect found in artifact review

The v2 `classify_sale_date` accepted ISO dates only. Form 144 XML in the artifact uses MM/DD/YYYY. Consequently, all 50 rows were incorrectly marked `unknown`.

Independent re-parsing of the raw artifact values:

- `approxSaleDate`: 34/50 before filing date; 16/50 same day.
- `noticeDate`: 48/50 same day; 2/50 one day before filing.
- No sampled approximate sale date was after filing.

This does not establish that a sale was executed. It demonstrates that the 144/A sample often carries a proposed/approximate date that predates the amendment filing. Those observations must not be treated as prospective supply signals without reconstructing the original notice and actual-sale evidence.

## Decision

- Do not use v2 candidate-query hit rate as historical subject-issuer coverage.
- Do not accept v2 `data_gate=PASS` as a source-level pass.
- Keep the 144/A XML parser components as useful technical work, but replace CIK-query discovery with a global SEC master-index census.
- New pilot: `research/phase50_form144_global_index_pilot.py`, with stratified original/amendment and target/non-target XML validation.
- No forward returns or alpha tests. Historical PIT F80 membership remains mandatory.
- F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen.
