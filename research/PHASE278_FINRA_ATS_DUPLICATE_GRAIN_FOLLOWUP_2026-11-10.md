# Phase 278 — FINRA ATS duplicate-grain targeted follow-up

**Date:** 2026-11-10  
**Status:** CSV/JSON transport parser hardened; 20 deterministic tests pass; hosted re-fetch pending.

## Purpose

Phase 277 found two conflicting groups under the candidate key in the 2025-07-07/T2 FINRA weeklySummaryHistoric partition. Phase 264 previously found two LND groups in 2025-01-06/T2. The current historical sample does not establish whether `lastReportedDate` is a natural key.

This phase re-fetches only the Phase 277 exception partition (2025-07-07/T2). It records the conflicting candidate-key rows, differing fields, row hashes and page hashes. It does not save the full partition, choose a row, sum values, or promote `lastReportedDate` to a natural key.

## Initial hosted attempts and transport diagnosis

The first attempts [42956112212](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42956112212) and [42956424647](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42956424647) passed compilation and the original offline tests but failed when Phase 100 called `response.json()`.

The metadata-only diagnostic artifact [13827521824](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42956809614/artifacts/13827521824) resolves the issue: FINRA returned HTTP 200 with `Content-Type: text/plain`, 519,822 bytes, `Record-Total: 147725`, `Record-Offset: 0`, and body SHA-256 `4829a7d1a3f50ba6e50e19050755a82375b13e04eb9f4c8f89fbe509a30c4e1e`. The first 23-character JSON string token followed by a comma is consistent with the quoted CSV header `"issueSymbolIdentifier",...`, not a malformed JSON data payload. The raw body was not stored.

The Phase 278 fetcher now:
- parses CSV only when the header exactly matches Phase 100's requested field list;
- accepts a single JSON value or a stream of adjacent recognized JSON values;
- rejects unknown formats, header mismatches, missing/extra CSV fields and arbitrary trailing content;
- records page response format, byte hashes, offsets and Record-Total;
- never persists the raw response body or full partition rows.

**20/20 deterministic tests pass locally**, including exact CSV schema, wrong-header rejection, JSON arrays/envelopes, redacted transport diagnostics, duplicate-key semantics, page offsets, page hashes, Record-Total and partition gates.

## Targeted retrieval contract

- Week: 2025-07-07; tier: T2.
- Synchronous pagination through Phase 100's retry/request/header functions; no FINRA API token.
- Require stable Record-Total, contiguous offsets, exact CSV field list or recognized JSON format, valid SHA-256 for every page and exact row-count reconciliation.
- Group only ATS_W_SMBL and OTC_W_SMBL symbol aggregates using the same candidate key as Phase 277.
- Preserve every conflicting group; do not select, sum or deduplicate.
- Treat `lastReportedDate` as a diagnostic sensitivity only, not an admitted natural key.

## Admission boundary

Strict PIT remains **not admitted** because current snapshots do not reconstruct immutable as-first-published values or first receipt. No forward returns, alpha, bootstrap/LOO, chronological OOS or holdout test is authorized. `F80_TOP20_PARTIAL50_BASELINE_C20`, production, universe and capital remain unchanged.

## Reproducibility

- Code: `research/phase278_finra_ats_duplicate_grain_followup.py`
- Tests: `research/test_phase278_finra_ats_duplicate_grain_followup.py`
- Workflow: `.github/workflows/phase278_finra_ats_duplicate_grain_followup.yml`
- Target partition: 2025-07-07 / T2


## Hosted targeted retrieval result — completed 2026-11-11 UTC

The final hosted re-fetch completed successfully:

- Run: [42957193574](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42957193574)
- Job: `130317000980`, `targeted-audit`, conclusion `success`
- Tests: **20/20** deterministic tests passed.
- Artifact: [13828171716](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42957193574/artifacts/13828171716)
- Artifact ZIP SHA-256: `f899a5f7c50bcb811ad4996f3fdadb1d5d5ce1ead6f70bf5346b5c9de16f68d4`
- Retrieval: **147,725 rows across 30 pages**; all 30 page hashes recorded; all offsets contiguous; FINRA `Record-Total` reconciled exactly. Pages 0–28 contained 5,000 rows each and page 29 contained 2,725.
- Response format: all 30 pages were returned as `text/plain` CSV and passed the exact requested-field header check. The raw response bodies and full partition rows were not persisted.

### Exact conflicting rows

Both candidate-key conflicts are for symbol `BQ`, week `2025-07-07`, tier `T2`, product `CTS`. Each pair has the same `initialPublishedDate=2025-08-11` and `lastUpdateDate=2025-08-11`, but different `lastReportedDate` and different quantities:

| Summary type | lastReportedDate | Shares | Trades |
|---|---|---:|---:|
| ATS_W_SMBL | 2025-07-11 | 134,042 | 3,592 |
| ATS_W_SMBL | 2025-07-10 | 8,958 | 138 |
| OTC_W_SMBL | 2025-07-11 | 1,413,022 | 13,792 |
| OTC_W_SMBL | 2025-07-10 | 48,214 | 827 |

The candidate key therefore has two conflicting groups, zero exact-duplicate groups. Adding `lastReportedDate` separates the two rows in each group, but that is only a mechanical diagnostic: the official documentation does not declare it a primary/natural key, a venue identifier, or a version identifier. No row was selected, summed, or deduplicated.

### Official semantic cross-check

FINRA's [Weekly Summary documentation](https://developer.finra.org/docs#query_api-equity-weekly_summary) describes weekly aggregate OTC/ATS data and states that `weeklySummaryHistoric` is a rolling historical dataset, with data older than one year static. Its [2019 API specification](https://www.finra.org/sites/default/files/OTC-Transparency-Data-File-Download-API-v04.pdf) defines `lastReportedDate` as the date a firm last sent an update to underlying data contributing to an aggregate; `lastUpdateDate` is the later of that date and the initial publication date. Those descriptions explain the field's provenance role but do not establish a unique row grain for the two symbol-summary conflicts.

This closes the targeted transport/data-integrity question, not the source-admission question. The conflicts remain quarantined. Strict PIT is still not admitted because the current historical snapshot does not reconstruct immutable as-first-published values or our own first-receipt timestamps. FINRA ATS/OTC remains context-only; no feature or alpha test is authorized.
