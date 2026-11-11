# Phase 277 — FINRA ATS/off-exchange stratified multi-year coverage and row-integrity audit

**Audit date:** 2026-11-10  
**Status:** implementation and hosted retrieval pending  
**Scope:** eight new quarterly-spaced historical weeks, both T1/T2 tiers; full synchronous pagination; response-page hashes; symbol-token, publication/revision and duplicate-grain diagnostics. No raw rows are persisted by the new artifact.

## Research question

Do the Phase 264 FINRA Weekly Summary findings generalize beyond its five purposively selected weeks, or were the two missing-symbol rows and two conflicting LND aggregate-key groups isolated to those partitions?

This is a source-feasibility and historical-coverage audit only. It does not infer beneficial-owner identity, aggressor direction, informed trading, or alpha.

## Selection

New weeks (all Monday week-starts, each distinct from Phase 264):

- 2022-04-04 and 2022-10-03
- 2023-04-03 and 2023-10-02
- 2024-04-01 and 2024-10-07
- 2025-04-07 and 2025-07-07

Both T1 and T2 are requested: 16 partitions. Together with Phase 264's five weeks, the stratified evidence spans 13 sampled weeks. It is not a continuous weekly panel, random sample, or broad-universe coverage census.

## Retrieval contract

- Reuse Phase 100's synchronous pagination implementation, including response Record-Total, page-count/offset checks, bounded retry and per-page SHA-256.
- No FINRA API token is supplied, matching the specific public synchronous path that succeeded in Phase 264. This does not establish entitlement for other FINRA products.
- Every page must have a contiguous page number/offset, a stable partition Record-Total, a valid SHA-256 and exact requested week/tier.
- All pages must reconcile to the partition total. No truncated first-page result is accepted.
- Raw symbol rows are processed in memory only; the artifact stores counts, page hashes and aggregate metadata, not raw rows.

## Diagnostics

For each week/tier:
- API record total versus retrieved rows and page count;
- known/unknown summary types and missing symbols in symbol-bearing row types;
- ATS/OTC unique symbol-token counts and their overlap;
- missing/invalid/negative share and trade quantities;
- initialPublishedDate, lastUpdateDate, lastReportedDate completeness and relative timing;
- row-level current-snapshot revisions (lastUpdateDate > initialPublishedDate);
- duplicate groups under the Phase 109 base candidate key and the mechanical lastReportedDate-extended sensitivity.

The extended key is a diagnostic only. FINRA documentation does not declare lastReportedDate a natural or primary key. Conflicting rows are retained and quarantined; never sum, choose, or deduplicate them mechanically.

Phase 264's prior five-week sample is included only as a metadata-level comparator after verifying its artifact ZIP digest. Combined counts are descriptive and do not resolve the natural grain.

## PIT and economic limits

FINRA's historical endpoint is intended for older historical periods; the current historical snapshot exposes publication/update date fields but does not provide immutable values as first published or our own historical first-receipt log. A current revised value cannot be backdated to initialPublishedDate.

Even if this stratified sample passes row/pagination checks:
- strict PIT remains **not admitted**;
- ticker strings are not permanent security identifiers;
- inactive/delisted/reused-symbol continuity remains unverified;
- T1/T2 and ATS/OTC symbol counts are activity diagnostics, not coverage of the frozen 335-name list or a survivorship-free universe;
- no return, alpha, bootstrap/LOO, chronological OOS or holdout test is authorized.

## Decision rule

Retain FINRA ATS/OTC as context-only unless all of the following can be resolved: symbol-bearing row integrity, natural aggregate grain, original publication/revision vintages, first-receipt evidence and effective-dated security identity. Do not create a generic Smart Money score from ATS/OTC activity.

F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen. The legacy holdout remains CONSUMED_NOT_PRISTINE and unused.

## Reproducibility

- Code: research/phase277_finra_ats_stratified_coverage_audit.py
- Tests: research/test_phase277_finra_ats_stratified_coverage_audit.py
- Workflow: .github/workflows/phase277_finra_ats_stratified_coverage_audit.yml
- Prior Phase 264 comparator: research/phase264_finra_ats_final_artifact_adjudication_result.json
- Official FINRA docs: https://developer.finra.org/docs
- FINRA historical dataset introduction: https://developer.finra.org/news/q12021
