# Smart Money Research — current state (2026-11-13 UTC)

## Objective and controls

Develop a strategy with a real statistical and economic edge, validated chronologically out of sample, with attractive return relative to risk. No imposed CAGR or holding-period target.

**Frozen baseline:** `F80_TOP20_PARTIAL50_BASELINE_C20`. Do not change it absent robust incremental OOS evidence.  
**Legacy holdout:** `CONSUMED_NOT_PRISTINE`; do not reuse.  
**Current economic status:** no new Smart Money feature has demonstrated incremental, cost-adjusted OOS edge. No signal admitted. No forward-return, alpha, OOS, bootstrap, LOO or holdout test has been run in Phases 361–363.

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
