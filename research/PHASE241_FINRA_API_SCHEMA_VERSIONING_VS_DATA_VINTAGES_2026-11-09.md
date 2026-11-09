# Phase 241 — FINRA Query API schema versioning is not historical data-vintage versioning

**Audit date:** 2026-11-09  
**Status:** `NO_HISTORICAL_ROW_VINTAGE_RECOVERY_FROM_API_VERSIONING`  
**Scope:** Documentation-only PIT feasibility check. No API calls, new data retrieval, returns, holdout use, vendor contact, purchase, or production change.  
**Control:** `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen.

## Executive decision

FINRA's Query API **Data Versioning** feature does not provide historical snapshots of previously published dataset values. It versions the API's field structure and data representation for backward compatibility. It cannot recover the original FINRA ATS/OTC values that were visible before a later row update.

This closes a plausible but incorrect route for resolving the Phase 117 revision problem. The existing FINRA ATS/OTC decision remains unchanged: current final-value rows must not be backdated to their initial publication date.

## Official documentation adjudication

FINRA announced Data Versioning for all Query endpoints on **2025-10-16**. Its announcement describes backward compatibility, controlled transitions, a `data-version` request header, and at least six months of support for API schema versions.

The current Developer Center documentation is explicit:

- Data Versioning governs **field structure and data representation** for API consumers.
- Existing Query datasets start at version 1; version increments occur for breaking changes.
- Examples of a breaking change include renaming/removing fields, changing data types or field logic, and modifying payload structure.
- The response includes the dataset version and a versioned schema URI.
- The documentation does not describe an as-of parameter, historical response archive, record-level revision chain, or a way to retrieve the payload as it existed at an earlier publication time.

The separate `weeklySummaryHistoric` endpoint is a historical-period dataset (older reporting periods). The word `HISTORIC` does not mean historical *payload vintages*. Historical-period access and schema-version selection are different mechanisms.

## Consequence for FINRA ATS/OTC PIT

Phase 117's five-week, ten-partition sample found:

- 1,882 of 108,444 symbol-aggregate rows were marked revised (1.735%).
- Those rows represented 10.08% of aggregate shares and 11.44% of aggregate trades.
- Revisions were concentrated in T1 OTC non-ATS; dropping rows based on their eventual revision status would itself introduce future-known selection.
- Median delay from initial publication to the latest observed update was 148 days for T1 and 134 days for T2.

The API's schema-version mechanism does not restore the missing original values. The following shortcuts remain invalid:

1. Assigning the current final value to `initialPublishedDate` when `lastUpdateDate` is later.
2. Dropping rows because the current extract shows they were revised later.
3. Treating `data-version: 1` as a historical data-vintage selector.
4. Treating `lastReportedDate` as the exact public dissemination timestamp.

Phase 100 already killed the tested FINRA daily short-volume stock-selection implementation after weak and unstable pseudo-OOS results. Phase 117 separately left FINRA ATS/OTC as a conditional market-structure source, not an alpha-ready panel. Phase 241 does not reopen either hypothesis.

## Disposition

| Question | Result |
|---|---|
| Does FINRA API Data Versioning preserve earlier row values? | **No documented capability** |
| Does `weeklySummaryHistoric` mean historical payload vintages? | **No** |
| Can the original values for revised historical ATS/OTC rows be reconstructed through `data-version`? | **No** |
| Can current final values be backdated to first publication? | **No** |
| Is a new FINRA return test authorized? | **No** |
| Is prospective capture useful? | **Yes, for future observations only** |

A future PIT-capable FINRA study would need immutable raw responses captured from the first observed publication onward, with retrieval timestamp, source request/partition, response headers, raw-byte hash, and every later response retained as a separate state. Prospective capture cannot repair missing historical vintages.

The existing FINRA API token is already used by the historical revalidation workflows. No new credential or user action is needed for this documentation finding. No capture workflow was created or dispatched in this phase.

## Sources

1. FINRA Developer Center, [Introducing Data Versioning for Query API Datasets](https://developer.finra.org/news/introducing-data-versioning-query-api-datasets), 2025-10-16.
2. FINRA Developer Center, [API documentation — Data Versioning](https://developer.finra.org/docs), especially the Query API Data Versioning section (field structure/data representation, version headers, schema URIs and version-change criteria).
3. Repository, [Phase 100 — FINRA short-flow walk-forward decision](PHASE100_FINRA_SHORTFLOW_WALKFORWARD_DECISION_2026-11-05.md).
4. Repository, [Phase 117 — FINRA ATS/OTC revision-impact and PIT eligibility audit](PHASE117_FINRA_ATS_PIT_REVISION_IMPACT_2026-11-05.md).

**Research boundary:** documentation adjudication only. No data-version history was requested or inferred; no raw market data, prices or returns were accessed. No feature, universe, portfolio, holdout, or production setting was changed.
