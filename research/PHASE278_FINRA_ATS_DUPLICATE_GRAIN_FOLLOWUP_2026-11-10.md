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
