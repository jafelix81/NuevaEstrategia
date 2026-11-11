# Phase 243 — CFTC raw/metadata partial-commit PIT guard

**Date:** 2026-11-09  
**Branch:** `phase231-cboe-option-quotes-full-row-reparse`  
**Status:** `IMPLEMENTED_HOSTED_VALIDATION_PASSED`  
**Control:** `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen.

## Executive finding

The prospective BPR/TFF workflow has source-specific capture steps marked `continue-on-error: true`, followed by a shared commit step that commits any files written under `data/cftc_bpr` and `data/cftc_tff`. Both capture implementations write raw bytes before receipt metadata. If a process fails between those writes, the workflow can still commit a raw-only file even though the source step is marked failed.

Before this phase, a later scheduled run could see no matching metadata and incorrectly classify that already-observed report as a new first scheduled event. That would manufacture a PIT event from a partial prior capture.

## Changes

### BPR
- Verify the full SHA-256 of any pre-existing raw HTML file.
- If the expected raw file exists but no matching report/hash metadata exists, mark the version as previously observed and state-only. It cannot be promoted to a new event.
- If matching receipt metadata exists but its raw file is missing, restore the raw bytes from the current response while preserving the original receipt metadata and event classification.
- A path/hash collision or corrupt pre-existing raw file fails closed.

### TFF
- Read metadata across protocol versions when checking whether a report date was previously observed; the current-protocol filter remains in place for selecting the latest scheduled state.
- Verify pre-existing gzip content against the full raw SHA-256.
- A raw-only orphan is treated as previously observed and state-only, never as a new event.
- If matching metadata exists but its raw file is missing, restore the gzip archive without rewriting the original receipt.
- A corrupt gzip or hash mismatch fails closed.

## Regression coverage

Six tests were added to the existing Phase 240 regression suites:

| Suite | Previous hosted count (Phase 242) | Added | Final hosted count |
|---|---:|---:|---:|
| BPR | 16 | 3 | 19 |
| TFF | 31 | 3 | 34 |
| **Total** | **47** | **6** | **53** |

The new tests cover:
1. Raw-only orphan files are state-only and never promoted to new PIT events.
2. A corrupt or hash-mismatched orphan file fails closed.
3. A missing raw file is repaired from matching receipt metadata without creating a new event.

**Hosted validation passed:** Phase 240 regression run [42676258774](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42676258774), job `129358311974`, commit `d2d86a0e187cd8979979c19450d53fc10fd4a250`. The job log confirms **19/19 BPR + 34/34 TFF = 53/53 tests**. The first attempts in this series exposed failures and were corrected before this final passing run.

The same head also passed the independent Phase 231 Cboe reparse run [42676263668](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42676263668), 9/9 regression tests, with metadata-only artifact [13701350271](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42676263668/artifacts/13701350271) (2,422 bytes; ZIP SHA-256 `b40b613aa0efb5b0fcf1f17451d19e457e7ad9426eb5a499193605c9913a82b9`).

## Commit trail

- BPR capture code: `9aa8c01f7012e9ad58bd7b9379e898850de2d4e1`
- BPR tests: `1e2b6ad2e9fe2f43d8dc9b5cbd370c2e17dc0d0e`
- TFF capture code: `a019b923d62c46cf54d4d4d849ce9defdc25e01d`
- TFF tests / latest code-test commit: `d2d86a0e187cd8979979c19450d53fc10fd4a250`

## Research disposition

- No live CFTC capture or historical PIT admission.
- No forward-return/alpha test, bootstrap/LOO, chronological OOS or holdout use.
- No vendor contact or purchase.
- No production, universe or strategy parameter changes.
- The legacy holdout remains `CONSUMED_NOT_PRISTINE`.
- `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen.

**Decision:** the raw-only partial-commit promotion path is closed and regression-validated. Keep BPR/TFF predictive use blocked until actual scheduled captures establish prospective receipt history. Hosted unit tests validate state transitions; they do not establish CFTC first-publication timestamps or economic value.
