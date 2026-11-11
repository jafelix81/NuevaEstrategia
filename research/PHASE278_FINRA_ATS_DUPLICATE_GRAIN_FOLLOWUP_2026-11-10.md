# Phase 278 — FINRA ATS duplicate-grain targeted follow-up

**Date:** 2026-11-10  
**Status:** transport parser hardened; 18 deterministic tests pass; hosted re-fetch pending.

## Purpose

Phase 277 found two conflicting groups under the candidate key in the 2025-07-07/T2 FINRA weeklySummaryHistoric partition. Phase 264 previously found two LND groups in 2025-01-06/T2. The current historical sample does not establish whether `lastReportedDate` is a natural key.

This phase re-fetches only the Phase 277 exception partition (2025-07-07/T2). It records the conflicting candidate-key rows, differing fields, row hashes and page hashes. It does not save the full partition, choose a row, sum values, or promote `lastReportedDate` to a natural key.

## Initial hosted attempts and correction

The first run [42956112212](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42956112212), its failed-job retry, and the PR-triggered run [42956424647](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42956424647) all passed compilation and the original 13 deterministic tests, but the live fetch stopped in Phase 100's `response.json()` with `JSONDecodeError: Extra data` at character 23. No partition rows or artifact were produced. The raw response body was not retained, so its exact contents are unknown; this is not yet classified as an API outage or a FINRA data defect.

The Phase 278 fetcher now uses Phase 100's retry, request and header-metadata functions but has a stricter stream decoder:
- accepts one JSON response or multiple adjacent valid JSON values (arrays, recognized response envelopes, or row objects);
- rejects arbitrary trailing content rather than silently truncating;
- records only status/content-type/header diagnostics, response byte count and SHA-256, parser position and first/trailing character;
- never persists the raw response body or full partition rows.

**18/18 deterministic tests pass locally**, including single and concatenated JSON responses, redacted parse diagnostics, duplicate-key semantics, page offsets, page hashes, Record-Total and partition gates.

## Targeted retrieval contract

- Week: 2025-07-07; tier: T2.
- Synchronous pagination through the Phase 100 request helper; no FINRA API token.
- Require stable Record-Total, contiguous offsets, valid SHA-256 for every page and exact row-count reconciliation.
- Group only the ATS_W_SMBL and OTC_W_SMBL symbol-aggregate rows, using the same candidate key as Phase 277.
- Preserve every conflicting group and its field values; do not select, sum, or deduplicate.
- Keep `lastReportedDate` as a diagnostic sensitivity only. It is not an admitted natural key.

## Admission boundary

Strict PIT remains **not admitted** because current snapshots do not reconstruct immutable as-first-published values or first receipt. No forward returns, alpha, bootstrap/LOO, chronological OOS or holdout test is authorized. `F80_TOP20_PARTIAL50_BASELINE_C20`, production, universe and capital remain unchanged.

## Reproducibility

- Code: `research/phase278_finra_ats_duplicate_grain_followup.py`
- Tests: `research/test_phase278_finra_ats_duplicate_grain_followup.py`
- Workflow: `.github/workflows/phase278_finra_ats_duplicate_grain_followup.yml`
- Target partition: 2025-07-07 / T2
