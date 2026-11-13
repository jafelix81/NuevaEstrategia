# Phases 361–362 — FINRA five-week bridge and LND duplicate-grain diagnostic

**Date:** 2026-11-13 UTC  
**Branch:** `phase363-finra-last-reported-date-grain-audit`  
**Baseline:** `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen.

## Executive result

Phase 361 completed all ten requested partitions (five historical weeks × T1/T2): **968,139 rows across 199 pages**, with every API `Record-Total` matching the retrieved row count. Retrieval passed; the data-grain gate remains `FAIL_OR_REVIEW` because two aggregate symbol/product groups for LND in 2025-01-06/T2 contain multiple rows.

Phase 362 re-fetched that complete partition (136,362 rows, 28 pages) and isolated 28 LND rows. The two aggregate rows in each family have different `lastReportedDate` values. Across all LND rows in each family, the combined aggregate shares/trades equal the combined firm-row shares/trades. Per-date firm-to-aggregate reconciliation remains untested. This is evidence that `lastReportedDate` may be part of the row grain; it is not yet proof that rows can be combined or used as a feature.

## Phase 361 — five-week bridge

Weeks: 2022-01-03, 2023-01-09, 2024-01-08, 2025-01-06 and 2025-10-20. Both T1 and T2 were retrieved for each week.

| Family | Aggregate symbol-week rows | Unambiguous bridges | Bridge coverage | Ambiguous | Duplicate aggregate rows | Concentration-ready partitions |
|---|---:|---:|---:|---:|---:|---:|
| T1 ATS | 10,637 | 10,637 | 100.0000% | 0 | 0 | 5/5 |
| T1 OTC non-ATS | 10,668 | 10,668 | 100.0000% | 0 | 0 | 0/5 |
| T2 ATS | 41,364 | 41,358 | 99.9855% | 6 | 1 | 1/5 |
| T2 OTC non-ATS | 45,756 | 45,744 | 99.9738% | 12 | 1 | 0/5 |

OTC non-ATS concentration is censored by De Minimis Firms rows in every sampled partition: 22.95%–34.12% of firm-grain shares in T1 and 12.11%–31.06% in T2. These aggregates reconcile arithmetically but do not identify the underlying firms.

T1 and T2 are security-universe tiers, not participant quality labels: FINRA describes T1 as S&P 500, Russell 1000 and selected ETP securities, and T2 as other NMS stocks. The sample did not include the separate OTC-equity tier (shown in FINRA metadata as OTCE); full source coverage is therefore not established.

- [Phase 361 workflow](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43427833220)
- [Phase 361 metadata artifact](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43427833220/artifacts/14040200536)

## Phase 362 — LND duplicate diagnosis

The complete 2025-01-06/T2 partition was retrieved: 136,362/136,362 rows, 28 pages. The 28 LND rows comprised two ATS aggregate rows, 22 ATS firm rows, two OTC aggregate rows and two OTC firm rows.

| Family | Aggregate row 1 | Aggregate row 2 | Combined aggregate | Combined firm-row sum |
|---|---:|---:|---:|---:|
| ATS | 6,224 / 37 (2025-01-10) | 5,226 / 144 (2025-01-08) | 11,450 / 181 | 11,450 / 181 |
| OTC | 28,543 / 137 (2025-01-10) | 67,210 / 320 (2025-01-08) | 95,753 / 457 | 95,753 / 457 |

*Shares / trades. The firm-row totals are across both reporting dates; the per-date comparison is the Phase 363 test.*

Combined ATS totals were 11,450 shares / 181 trades; combined OTC totals were 95,753 shares / 457 trades. Both matched the sums across firm rows. ATS had 22 firm rows and 13 unique participant identities; OTC had two firm rows and one unique participant identity. Repeated participant keys across the full week may be expected if rows are split by reporting date, but Phase 362 did not retain firm-row `lastReportedDate` in its anonymized artifact. No deduplication or summing rule is approved.

- [Phase 362 workflow](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43431642444)
- [Phase 362 anonymized artifact](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43431642444/artifacts/14038968681)

## Data-vintage and PIT implications

FINRA's official metadata defines `lastReportedDate` as the last time a firm sent an update to data contributing to the aggregate; `lastUpdateDate` as the most recent date on which total trades were updated from ATS/OTC data; and `initialPublishedDate` as the first publication date after the reporting delay (two weeks for T1, four weeks for T2/OTC). The historical endpoint has a rolling four-year window beginning one year before the current date; only week/month and tier partition filters are supported, and data older than one year is static. The 2025-01-06/T2 partition is therefore retrieved and filtered locally rather than using a symbol filter.

Official documentation: https://developer.finra.org/docs (Weekly Summary metadata and Dataset Details).

`lastReportedDate` is a candidate row-grain key, **not** the knowledge/availability date. For PIT, the conservative candidate remains the later of `initialPublishedDate` and `lastUpdateDate`, followed by the next tradable session; exact first-receipt timestamps and interim vintages remain unavailable in this audit.

## Phase 363 — candidate date-grain key rejected

The complete 2025-01-06/T2 partition was re-fetched (136,362 rows / 28 pages). Grouping by `(issueSymbolIdentifier,lastReportedDate)` removed duplicate aggregate keys but did not reconcile the participant data universally:

- ATS: 1,338/7,907 exact share-and-trade matches (16.92%); 6,569 mismatches and 11,948 firm-only symbol/date groups.
- OTC non-ATS: 8,608/8,770 exact matches (98.15%); 162 mismatches and 175 firm-only groups.
- No missing `lastReportedDate`, duplicate aggregate symbol/date keys, multi-product symbol/date keys or duplicate participant keys within a date were found.

LND OTC reconciled on both dates. LND ATS reconciled on 2025-01-10, but 2025-01-08 was short by 400 shares and 7 trades (aggregate 5,226/144 versus firm sum 4,826/137). The combined Phase 362 totals had masked this date-level mismatch.

**Decision:** kill `lastReportedDate` as a universal symbol-to-firm join key. Do not aggregate or deduplicate on it. T2 ATS is not admitted for concentration features. The five clean T1 ATS samples remain a conditional venue-level candidate, not an informed-flow or directional signal.

- [Phase 363 workflow](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43432380794)
- [Phase 363 metadata artifact](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43432380794/artifacts/14041685255)
- [Phase 363 report](PHASE363_FINRA_LAST_REPORTED_DATE_GRAIN_AUDIT_2026-11-13.md)

## Decision and controls

- Keep FINRA ATS as a **conditional venue-level market-structure candidate**, with T1 ATS the cleanest observed slice in these five samples. This is not evidence of informed investors, direction, or predictive value.
- Keep OTC non-ATS concentration censored; do not treat De Minimis Firms as named participants.
- Do not promote T2 until the reporting-date grain test and broader historical audit pass.
- Next source-coverage gate must include all available historical weeks and the separate OTCE tier, not only T1/T2.
- No forward returns, signal, alpha, OOS, bootstrap, LOO or holdout tests were performed. No holdout was used. No F80 parameters, universe, capital or production logic changed.
