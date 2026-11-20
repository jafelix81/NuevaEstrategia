# Phase 521 — FINRA historical symbol-domain filter probe

**Audit timestamp:** 2026-11-20 09:31:35 UTC  
**Run:** [44711398973](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44711398973)  
**Artifact:** [14617172938](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44711398973/artifacts/14617172938)  
**Disposition:** DOMAIN FILTER REJECTED BY HISTORICAL ENDPOINT (HTTP 400); no rows or features admitted.

## 1. Why this probe was run

Phase 518 validated 259 consecutive weekly aggregate observations, but its aggregate HHI sample-size gates failed for all pre-coded 5/10/20-session maturity plans. Phase 375 separately counted 432,804 revision-stable symbol-week groups across 209 historical weeks, suggesting a symbol-week panel could have more statistical observations.

The Phase 375 and Phase 518 artifacts retained weekly aggregates only; they do not contain the underlying per-symbol feature rows. Before repeating a large historical extraction, Phase 521 tested whether FINRA's historical endpoint could filter a predeclared 10-symbol subset from the frozen 335-name snapshot in one request.

## 2. Probe design

- Dataset: `otcmarket/weeklySummaryHistoric`.
- Week: 2024-05-20 (a known historical T1 partition and Phase 518 overlap date).
- Tier: T1.
- Requested symbols: 10 predeclared names from the frozen 335-name snapshot; raw names were not persisted.
- Request: partition compare filters plus `domainFilters` for `issueSymbolIdentifier` and the two ATS symbol summary types.
- Requested only the fields required for aggregate/participant reconciliation, publication/revision checks and concentration eligibility.
- No raw rows, MPIDs, CRDs, participant names, symbol strings or per-symbol features were retained. The artifact contains only counts, a requested-symbol manifest hash and the HTTP status.

## 3. Result

- Offline regression tests: passed.
- Live probe job: completed successfully as a diagnostic.
- HTTP response: **400**.
- Probe status: `DOMAIN_FILTER_REJECTED_BY_HISTORICAL_ENDPOINT`.
- `domain_filter_supported`: false.
- No historical rows returned; no symbol coverage or aggregate/firm bridge could be measured.
- Research-observation eligible rows: 0.
- Signal-eligible rows: 0.

The workflow is green because it correctly recorded the expected unsupported-filter result and uploaded the aggregate-only artifact; green does not mean the filter itself was accepted.

The result is consistent with FINRA's official Query API documentation, which warns that historical datasets have restricted filtering: only specific compare-filter fields are supported, compare type must be EQUAL, and only one time-based field may be filtered. The docs do not promise that `domainFilters` are supported for historical datasets. https://developer.finra.org/docs

## 4. Decision and next gate

Do not retry the same `domainFilters` request and do not launch a broad extraction.

The next bounded probe should test the documented historical compare-filter path: one request per symbol using `issueSymbolIdentifier = EQUAL`, alongside `weekStartDate = EQUAL` and `tierIdentifier = EQUAL`, for the same 10-name manifest and one historical week. This is only 10 requests. If that field is not an allowed historical compare filter, stop and document the endpoint limitation rather than scaling to hundreds of symbols or thousands of partitions.

If symbol equality filtering passes, the next gate is a modest multi-week coverage pilot. Only after that should the team estimate the full 335-name extraction cost. Exact ticker matches remain a coverage diagnostic, not a historical security identity or active-universe proof. Databento's effective/record-time identity bridge and a survivorship-aware return source remain separate prerequisites.

## 5. Authorization and strategy controls

- No returns, labels, model fit, alpha, OOS, bootstrap, LOO or holdout used.
- No vendor data, paid data or API subscription acquired.
- No signal admitted.
- `F80_TOP20_PARTIAL50_BASELINE_C20`, its universe, parameters, exposure, costs, holdout and production remain unchanged.
