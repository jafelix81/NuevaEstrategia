# Phase 278 — FINRA ATS duplicate-grain targeted follow-up

**Date:** 2026-11-10  
**Status:** implementation and 13 deterministic tests complete; hosted re-fetch pending.

## Purpose

Phase 277 found two conflicting groups under the candidate key in the 2025-07-07/T2 FINRA weeklySummaryHistoric partition. Phase 264 previously found two LND groups in 2025-01-06/T2. The current historical sample does not establish whether `lastReportedDate` is a natural key.

This phase re-fetches only the Phase 277 exception partition (2025-07-07/T2) using Phase 100's synchronous pagination implementation. It records the conflicting candidate-key rows, differing fields, row hashes and page hashes. It does not save the full partition, choose a row, sum values, or promote `lastReportedDate` to a natural key.

## Controls

- No FINRA API token supplied.
- Full Record-Total and page-offset reconciliation required.
- Every page SHA-256 recorded and validated.
- Only the two symbol-level aggregate types used by the Phase 277 candidate-key audit are grouped.
- Full partition rows are processed in memory and not persisted.
- Conflicting rows remain quarantined.
- Strict PIT and alpha remain unadmitted; no returns, bootstrap/LOO, OOS or holdout use.
- F80, production, universe and capital remain unchanged.

## Reproducibility

- Code: `research/phase278_finra_ats_duplicate_grain_followup.py`
- Tests: `research/test_phase278_finra_ats_duplicate_grain_followup.py`
- Workflow: `.github/workflows/phase278_finra_ats_duplicate_grain_followup.yml`
- Target partition: 2025-07-07 / T2
