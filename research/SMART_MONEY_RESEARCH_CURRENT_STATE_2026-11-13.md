# Smart Money Research — current state (2026-11-13 UTC)

## Objective and controls

Develop a strategy with a real statistical and economic edge, validated chronologically out of sample, with attractive return relative to risk. No imposed CAGR or holding-period target.

**Frozen baseline:** `F80_TOP20_PARTIAL50_BASELINE_C20`. Do not change it absent robust incremental OOS evidence.  
**Legacy holdout:** `CONSUMED_NOT_PRISTINE`; do not reuse.  
**Current economic status:** no new Smart Money feature has demonstrated incremental, cost-adjusted OOS edge. No signal admitted. No forward-return, alpha, OOS, bootstrap, LOO or holdout test has been run in Phases 361–367.

## Latest FINRA work — Phases 361–363

### Phase 361 — five-week bridge completed

Five historical weeks × T1/T2 = 10 complete partitions, **968,139 rows / 199 pages**. Every API `Record-Total` matched. Retrieval gate PASS; data-grain gate FAIL_OR_REVIEW because two LND aggregate symbol/product groups in 2025-01-06/T2 contain multiple rows.

| Family | Aggregate symbol-week rows | Unambiguous bridges | Coverage | Ambiguous | Duplicate aggregate rows | Concentration-ready partitions |
|---|---:|---:|---:|---:|---:|---:|
| T1 ATS | 10,637 | 10,637 | 100.0000% | 0 | 0 | 5/5 |
| T1 OTC non-ATS | 10,668 | 10,668 | 100.0000% | 0 | 0 | 0/5 |
| T2 ATS | 41,364 | 41,358 | 99.9855% | 6 | 1 | 1/5 |
| T2 OTC non-ATS | 45,756 | 45,744 | 99.9738% | 12 | 1 | 0/5 |

OTC non-ATS De Minimis Firms rows censor concentration in all sampled partitions: 22.95%–34.12% of shares in T1 and 12.11%–31.06% in T2. T1/T2 are security-universe groups, not participant labels. FINRA defines T1 as S&P 500, Russell 1000 and selected ETP securities; T2 as other NMS stocks. The separate OTC-equity tier (OTCE in metadata) was not sampled.

[Phase 361 run](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43427833220) · [artifact](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43427833220/artifacts/14040200536).

### Phase 362 — LND diagnostic completed

Re-fetched the full 2025-01-06/T2 partition: **136,362 rows / 28 pages**. It contained 28 LND rows: two ATS aggregate rows, 22 ATS firm rows, two OTC aggregate rows and two OTC firm rows.

The two ATS aggregate rows share symbol/product but have different `lastReportedDate` values:
- 2025-01-10: 6,224 shares / 37 trades
- 2025-01-08: 5,226 shares / 144 trades

Combined ATS aggregates = **11,450 shares / 181 trades**, exactly matching the combined ATS firm rows. ATS had 22 firm rows / 13 unique participant identities / 9 repeated participant keys across the full week.

The two OTC aggregate rows:
- 2025-01-10: 28,543 shares / 137 trades
- 2025-01-08: 67,210 shares / 320 trades

Combined OTC aggregates = **95,753 shares / 457 trades**, exactly matching the combined OTC firm rows (two rows, one participant identity repeated). Phase 362 did not retain firm-row `lastReportedDate` in its anonymized artifact, so per-date matching remains unproven. No deduplication or summing rule is approved.

[Phase 362 run](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43431642444) · [anonymized artifact](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43431642444/artifacts/14038968681).

### Phase 363 — universal reporting-date key rejected

The full 2025-01-06/T2 partition was retrieved again (136,362 rows / 28 pages). Grouping by `(issueSymbolIdentifier,lastReportedDate)` removed duplicate aggregate keys but did not reconcile firm rows universally:

| Family | Exact share/trade matches | Mismatches | Firm-only symbol/date groups |
|---|---:|---:|---:|
| ATS | 1,338/7,907 (16.92%) | 6,569 | 11,948 |
| OTC non-ATS | 8,608/8,770 (98.15%) | 162 | 175 |

No missing `lastReportedDate`, duplicate aggregate symbol/date keys, multi-product symbol/date keys or duplicate participant keys within a date were found. However, the large ATS mismatch rate and residual OTC mismatches reject `lastReportedDate` as a universal join key.

For LND, OTC matched on both reporting dates. ATS matched on 2025-01-10, but 2025-01-08 was short by 400 shares and 7 trades (aggregate 5,226/144 versus firm sum 4,826/137). Combined totals had masked this mismatch.

**Decision:** do not sum or deduplicate by `lastReportedDate`. T2 ATS is not admitted for concentration features. The five clean T1 ATS samples remain a conditional venue-level candidate only.

[Phase 363 run](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43432380794) · [artifact](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43432380794/artifacts/14041685255) · [report](PHASE363_FINRA_LAST_REPORTED_DATE_GRAIN_AUDIT_2026-11-13.md) · [branch](https://github.com/jafelix81/NuevaEstrategia/tree/phase363-finra-last-reported-date-grain-audit).

### Phase 364 — full partition-inventory census

- Official metadata/partitions endpoints returned 1,045 historic pairs (209 weeks × five tiers) and 1,031 current pairs; union 1,235 pairs / 258 weeks; historic/current overlap 841 pairs.
- Historic inventory spans 2021-11-15 through 2025-11-10 with 209 consecutive weekly anchors in each of NA, NMS, OTCE, T1 and T2.
- Current inventory is irregular: NA, OTCE and T2 each have 253 pairs (2021-12-06 to 2026-10-05); T1 has 255 (to 2026-10-19); NMS has only 17 (2023-06-05 to 2023-11-06) and six missing weekly anchors.
- FINRA metadata documents T1/T2/OTCE but does not define NA/NMS. Both values remain quarantined pending actual-row semantics.
- The current `weeklySummary` partition catalog extends far beyond its documented twelve-month rolling window. This is a catalog anomaly only; it does not prove old rows remain queryable. Both metadata/partition field orders agree, and `totalNotionalSum` is present in metadata.
- Run [43444007387](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43444007387), artifact [14046932092](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43444007387/artifacts/14046932092), 7/7 tests passed. Report: [Phase 364](PHASE364_FINRA_WEEKLY_PARTITION_INVENTORY_CENSUS_2026-11-13.md).

### Phase 365 — actual-row probe completed with expected-absence gate defect

- 33/50 planned probes returned rows. The other 17 were combinations absent from the Phase 364 partition inventory: five historic probes after the historic inventory end; five current probes before its earliest partition; three current NMS probes outside its 17-week 2023 inventory; and four current 2026-10-19 combinations for T2/OTCE/NA/NMS when only T1 was listed.
- The Phase 365 workflow failed because it required all 50 Cartesian-product probes to succeed. The absent current partitions returned empty bodies (recorded as JSON decode errors); historic out-of-range probes returned HTTP 400. These are expected absent partitions, not evidence of a general FINRA outage.
- Crucial finding: current `weeklySummary` returned nonzero rows for 12 old partitions across 2022-01-03, 2025-10-20 and 2025-11-10 (T1/T2/OTCE/NA). All 12 Record-Total values matched the corresponding historic dataset. This establishes that some old current-dataset partitions are queryable despite the documentation describing a rolling 12-month window; it does not establish complete historical coverage.
- Eleven of twelve ten-row sample signatures matched. The only mismatch was 2025-10-20/OTCE: both datasets had 24,292 records and identical sampled row/type/tier/date counts, but the historic sample had participant identifiers on 10/10 De Minimis rows while the current sample had 0/10. The ten-row probe cannot distinguish sample ordering from a real row-vintage difference.
- NA samples contained six summary-statistic rows (3 ATS_W_VOL_STATS + 3 OTC_W_VOL_STATS) with tier description Not Applicable; treat NA as summary-only, not a stock universe. Historic NMS samples mixed NMS Tier 1, NMS Tier 2 and Not Applicable descriptions; current NMS is sparse (17 inventory weeks in 2023). Keep NMS quarantined rather than mapping it to T1/T2.
- Run [43444391496](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43444391496), artifact [14047148064](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43444391496/artifacts/14047148064), 7/7 offline tests passed. Full report: [Phase 365 result](PHASE365_FINRA_ACTUAL_ROW_PROBE_RESULT_2026-11-13.md).
- No raw rows were retained; no returns or alpha test were used.

### Phase 366 — full-row vintage reconciliation completed with T1 mismatch review

- Fully retrieved four partitions (2025-10-20 T1/OTCE × current/historic): 178,816 rows, 38 pages, zero retrieval errors; 7/7 offline tests passed.
- OTCE: 24,292/24,292 rows matched over the 16 canonical fields used. The Phase 365 first-page participant-ID discrepancy was sampling/order: full-partition participant-ID rows were 13,425 in both datasets, De Minimis rows 7,834 in both, and unique symbols 8,229 in both.
- T1: 65,092/65,116 selected-field rows matched; 24 current-only and 24 historic-only rows, with 24 mismatched identity-key groups (0.0369%). Summary-type, tier-description and product-type counts, unique symbols (2,420), participant-ID rows (60,282) and De Minimis rows (2,420) matched.
- Audit caveat: Phase 366 omitted `summaryStartDate` from its canonical row hash; the historic endpoint also returns a query-helper field `historicalweek`. OTCE exact match is therefore limited to the selected 16 fields, not every field in the schema. Numeric aggregate equality also used string formatting and falsely flagged trailing-zero differences for OTCE. T1 aggregate notional sums differ by only a few millionths; the 24 row-level field differences are not yet identified.
- Run [43455306406](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43455306406), artifact [14054525109](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43455306406/artifacts/14054525109). Full report: [Phase 366](PHASE366_FINRA_FULL_ROW_VINTAGE_RECONCILIATION_2026-11-13.md).
- No raw rows or identifiers were retained. No return or alpha test was run.

### Phase 367 — T1 field-level vintage diagnostic completed

- Re-fetched the full 2025-10-20 T1 partition from both datasets: 65,116 rows each, 14 pages each, zero errors; offline tests passed.
- 65,092/65,116 rows matched exactly. The other 24 differed only in `totalNotionalSum`; no mismatch occurred in `totalWeeklyShareQuantity`, `totalWeeklyTradeCount`, `lastReportedDate`, `summaryStartDate`, symbols, participant identifiers, publication/update dates or other canonical fields.
- Current-minus-historic signed notional difference across the 24 rows: +$0.000003; absolute differences sum to $0.000039; maximum absolute per-row difference $0.000005. No key-only or duplicate groups.
- This is an economically negligible decimal-precision discrepancy, but source values remain unrounded and the difference is documented. It is not evidence of an alpha signal.
- Run [43456024316](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43456024316), artifact [14053738587](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43456024316/artifacts/14053738587). Full report: [Phase 367](PHASE367_FINRA_T1_FIELD_LEVEL_VINTAGE_DIAGNOSTIC_2026-11-13.md).

### Phase 368 — FINRA revision-lag / PIT availability audit is the next gate

- Quantify row-level lags from `initialPublishedDate` to `lastUpdateDate` and `lastReportedDate` on the fully retrieved 2025-10-20 T1/OTCE partitions, with older and newer week controls if coverage permits.
- Measure the fraction of final rows whose update dates postdate initial publication, distribution of update lags, and whether any field is a genuine publication/knowledge timestamp.
- Do not backdate final historical values to `initialPublishedDate`. If update-vintage availability cannot be reconstructed, FINRA historical signal use remains inadmissible; retain it for descriptive/current monitoring only.
- No signal, return or alpha test is authorized.

## Cross-source re-ranking — SEC Form 4 identity gate (Phases 345–346)

- Phase 345 replicated six purposive historical cohorts: 413 candidate transaction rows across 262/262 retrieved Form 4 accessions. In the 2023+ cohorts, event-time identity was 273/301 rows (90.70%); stricter transaction-date identity was 263/301 (87.38%). Both remain below the preregistered 95% admission gate. The 2006Q1/2012Q1 legacy cohorts had 0/112 rows resolved by the current same-context XBRL target-fact method.
- Phase 346 tested legacy periodic HTML as a bridge. Among 96 transaction-date-eligible older-cohort rows, 53 had issuer-specific ticker prose matching Form 4, but only one unique same-row class/exchange table anchor group (two candidate rows) was usable and strictly pre-transaction. The method is not a universal historical security master.
- Decision: stop expanding the legacy HTML parser as a universal solution; retain only candidate-level evidence with explicit venue distinctions. No insider return study or security master admission. See [Phase 345](https://github.com/jafelix81/NuevaEstrategia/blob/phase346-form4-legacy-html-identity-bridge/research/PHASE345_SEC_FORM4_MULTIQ_COHORT_IDENTITY_REPLICATION_2026-11-12.md) and [Phase 346](https://github.com/jafelix81/NuevaEstrategia/blob/phase346-form4-legacy-html-identity-bridge/research/PHASE346_FORM4_LEGACY_HTML_IDENTITY_BRIDGE_AUDIT_2026-11-12.md).

## PIT and source limitations

Official FINRA metadata defines:
- `lastReportedDate`: last time a firm sent an update contributing to the aggregate;
- `lastUpdateDate`: most recent date on which total trades were updated from ATS/OTC data;
- `initialPublishedDate`: first publication date after the reporting delay (two weeks for T1, four weeks for T2/OTC).

`lastReportedDate` is **not** an approved universal join key and is not the knowledge/availability date. Conservative candidate availability remains the later of `initialPublishedDate` and `lastUpdateDate`, then the next tradable session. Exact first-receipt timestamps and interim vintages are not reconstructed.

FINRA's `weeklySummaryHistoric` is a rolling four-year dataset beginning one year before the current date. It supports week/month and tier partition filters only; no symbol filter or sorting. Data older than one year is static. Full partitions must be retrieved and filtered locally. Official docs: https://developer.finra.org/docs (Weekly Summary).

## Source dispositions

| Source | Disposition |
|---|---|
| FINRA ATS | Conditional venue-level market-structure candidate. T1 ATS is the cleanest sampled slice; T2 ATS failed the tested `lastReportedDate` join (16.92% exact in one partition) and is not admitted. Not beneficial-owner identity, direction, or proof of informed activity. |
| FINRA OTC non-ATS | Context only; De Minimis Firms bucket censors firm concentration. |
| FINRA short flow / short interest | Weak/incomplete or timing/pagination defects; not promoted. |
| Cboe Open-Close EOD / Option EOD Summary | Conditional options-flow/context candidate; sample schemas/accounting pass, but full historical/inactive coverage, first-receipt/correction vintages, session alignment and licensing remain unresolved. |
| Cboe TBT | Conditional C1 microstructure candidate; sample row-grain, selection, missing open/close, side mapping and segment issues remain open. |
| SEC Form 4 | Bulk history and daily-index PIT route feasible; owner attribution and effective-dated security identity incomplete. |
| SEC 13D/G | CUSIP and predecessor audits improved identity; broad event/security panel not admitted. |
| SEC 13F / N-PORT | Delayed context only; acceptance/amendment timing and security mapping remain open. |
| CFTC TFF/COT | Historical strict PIT rejected; release-date ledger incomplete and outage/funding gaps invalidate synthetic availability proxies. |
| CFTC BPR | Monthly broad-index context only; short public retention and no historical first-receipt ledger. |
| Form 144 | Filing/role and document-linkage work only; no execution or return edge established. |

## Human-action blocker

SEC 13D/G retrieval remains blocked until repository secret `SEC_USER_AGENT` is configured with a monitored contact address. Do not retry without it; do not expose the address in code or logs.

## Next gates

1. Use FINRA's partitions endpoint to census the full available history in both historic and current weekly datasets, including the separate OTCE tier.
2. Sample a wider set of T1 ATS weeks; measure symbol/week coverage, participant identity continuity, concentration readiness, and representation of inactive/delisted securities.
3. Build conservative PIT availability from publication/update dates; do not backdate or treat final snapshots as original vintages.
4. Only after coverage/PIT pass, consider descriptive T1 ATS venue-concentration features. Test incremental information versus frozen LTM/F80 with identical exposure/costs, strict chronological splits, a new untouched holdout, clustered bootstrap, LOO and multiplicity controls.
5. Continue Cboe and SEC work in parallel when a data-feasibility gate is ready; do not assume FINRA is the only viable source.

## Controls

No signal admitted. No economic test, no holdout use, no parameter/universe/capital/production change. No PR merged. `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen.
