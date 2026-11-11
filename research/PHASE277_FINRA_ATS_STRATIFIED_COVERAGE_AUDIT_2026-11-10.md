# Phase 277 — FINRA ATS/off-exchange stratified multi-year coverage and row-integrity audit

**Audit date:** 2026-11-10  
**Status:** completed; hosted retrieval succeeded with two conflicting candidate-key groups.  
**Hosted run:** [42947083397](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42947083397)  
**Job:** 130282347652, conclusion `success`  
**Artifact:** [13824782108](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42947083397/artifacts/13824782108)  
**Artifact ZIP SHA-256:** `5e8cbf2d4d923ae655d648f01c9d71f223723484c5b177dc50ae70ea1ee3bb4f`

## Research question and sample

The audit tested whether Phase 264's FINRA Weekly Summary findings generalize beyond five purposively selected weeks. Eight additional quarterly-spaced weeks were retrieved for both T1/T2 tiers:

- 2022-04-04 and 2022-10-03
- 2023-04-03 and 2023-10-02
- 2024-04-01 and 2024-10-07
- 2025-04-07 and 2025-07-07

All 16 requested partitions completed. The new sample contains **1,512,008 rows**, **172,073 symbol-level ATS/OTC aggregate rows**, and **310 response pages**. Every API Record-Total reconciled and every page hash was recorded and validated.

This is a stratified sample, not a continuous weekly panel, random sample, or broad-universe coverage census.

## Results

| Diagnostic | New Phase 277 sample |
|---|---:|
| Partitions completed | 16/16 |
| API Record-Total reconciliations | 16/16 |
| Page hashes | 310/310 valid |
| Symbol-bearing rows missing symbol | 0 |
| Unknown summary types | 0 |
| Invalid/negative quantity fields | 0 |
| Initial publication date populated | 100% |
| Rows with lastUpdateDate later than initialPublishedDate | 3,836 / 172,073 (2.2293%) |
| Conflicting base candidate-key groups | 2 |
| Exact duplicate groups | 0 |

Both conflicting groups occur in **2025-07-07 / T2**. Adding `lastReportedDate` to the Phase 277 candidate key mechanically separates both groups; the extended key has zero remaining duplicate groups in this partition. That is a sensitivity only: FINRA documentation has not established `lastReportedDate` as a natural or primary key. Phase 278 performs a targeted re-fetch and records the exact conflict rows without selecting, summing, or deduplicating them.

The rows with a later `lastUpdateDate` are current-snapshot update indicators, not proof that each field value changed by that date. Revision rates vary materially by partition: for example, T1 was 10.6147% in 2022-04-04, 14.4756% in 2023-10-02, and 19.5531% in 2024-10-07. This reinforces that current historical snapshots cannot be treated as immutable first-published values.

Initial publication lag medians were 21 calendar days for T1 and 35 for T2. No sampled aggregate row was published earlier than the tier's minimum delay used by the audit.

## Combined Phase 264 + 277 evidence

Across 13 sampled weeks and both tiers:

- 2,480,147 total rows;
- 280,517 symbol-level ATS/OTC aggregate rows;
- 5,718 rows with `lastUpdateDate > initialPublishedDate` (2.0384%);
- four conflicting base candidate-key groups: two LND groups in Phase 264's 2025-01-06/T2 partition and two additional groups in Phase 277's 2025-07-07/T2 partition;
- the two missing-symbol exceptions from Phase 264's 2022-01-03/T2 partition remain unresolved; Phase 277 found none in its new sample.

The combined sample does not establish a natural key or resolve the historical missing-symbol exceptions.

## PIT, identity and economic limits

Strict PIT remains **not admitted**. The current historical endpoint exposes `initialPublishedDate` and `lastUpdateDate`, but it does not reconstruct immutable as-first-published values or our own historical first-receipt archive. A current revised value must not be backdated to `initialPublishedDate`.

Ticker strings are not permanent security identifiers. Inactive/delisted/reused-symbol continuity and broad-universe coverage remain unverified. T1/T2 and ATS/OTC symbol counts are activity diagnostics only, not coverage of the frozen 335-name list or a survivorship-free universe.

No forward returns, alpha, bootstrap/LOO, chronological OOS or holdout test was run or authorized. FINRA ATS/OTC remains off-exchange activity/context only; no generic Smart Money score or stock-selection feature is admitted.

## Decision

Retain FINRA ATS/OTC as context-only. Keep all conflicting groups quarantined. Do not sum, select, or deduplicate rows using `lastReportedDate` without authoritative natural-grain semantics and original publication vintages. Resolve missing-symbol exceptions and point-in-time security identity before feature construction.

`F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen. The legacy holdout remains `CONSUMED_NOT_PRISTINE` and unused. Production, universe, capital and vendor/licensing status are unchanged.

## Reproducibility

- Code: `research/phase277_finra_ats_stratified_coverage_audit.py`
- Tests: `research/test_phase277_finra_ats_stratified_coverage_audit.py`
- Workflow: `.github/workflows/phase277_finra_ats_stratified_coverage_audit.yml`
- Prior Phase 264 comparator: `research/phase264_finra_ats_final_artifact_adjudication_result.json`
- Official FINRA docs: https://developer.finra.org/docs
- FINRA historical dataset introduction: https://developer.finra.org/news/q12021


## Transport-format sensitivity observed in Phase 278

A later request for the 2025-07-07/T2 partition returned HTTP 200 with `Content-Type: text/plain`, a 519,822-byte body, `Record-Total: 147725`, offset 0, and a body SHA-256 recorded in the Phase 278 transport artifact. The JSON decoder parsed the first 23-character quoted token and then encountered a comma at character 23. That token length matches the quoted first requested field name, `"issueSymbolIdentifier"`, indicating a CSV header rather than malformed JSON. The raw body was not retained.

The Phase 278 fetcher now accepts CSV only when its parsed header exactly matches the requested Phase 100 field list; it also accepts recognized JSON response shapes. It rejects header mismatches and malformed rows. This shows the FINRA endpoint's representation may vary across requests; the Phase 277 artifact itself used the JSON path, and its original response-format metadata was not recorded. Future full-panel revalidation should record and validate the response format for every page.
