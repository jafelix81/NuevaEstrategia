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

### Phase 368 — FINRA revision-lag / PIT availability audit completed

- Retrieved 5/5 full partitions: **258,787 rows / 55 pages**, with every Record-Total reconciled and zero missing/invalid values in the four date fields.
- For the four T1 partitions, positive lastUpdateDate minus initialPublishedDate gaps were 964/46,834 (2.0583%) in 2022-01-03, 100/56,895 (0.1758%) in 2025-01-06, 31/65,116 (0.0476%) in 2025-10-20 and 111/65,650 (0.1691%) in 2025-11-10. The maximum gaps were 282, 248, 324 and 303 days respectively. OTCE 2025-10-20 had 0/24,292 positive gaps.
- Crucial refinement: every positive T1 update-date gap occurred in OTC_W_FIRM, OTC_W_SMBL or OTC_W_SMBL_FIRM. The sampled ATS_W_FIRM, ATS_W_SMBL and ATS_W_SMBL_FIRM rows had zero post-initial update-date gaps across all four T1 weeks. This is a narrow candidate, not a universal PIT pass.
- initialPublishedDate was exactly 21 calendar days after weekStartDate for all sampled T1 rows and 35 days for OTCE, consistent with FINRA's two-week/four-week reporting-delay descriptions plus the week-end/next-Monday schedule.
- FINRA's API Data Versioning documentation governs schema/field representation, not row-vintage history. No complete intermediate public-vintage ledger is available from the current API response. Generic weekly-summary PIT therefore remains NOT ESTABLISHED.
- Decision: expand T1 ATS only. Test more weeks, exact symbol/product aggregate-to-firm reconciliation, symbol/participant coverage and next-session availability before any historical signal test. Quarantine OTC rows with post-initial update dates.
- Run [43460727228](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43460727228), artifact [14056611466](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43460727228/artifacts/14056611466). Full report: [Phase 368](PHASE368_FINRA_REVISION_LAG_PIT_AVAILABILITY_AUDIT_2026-11-13.md).
- No return or alpha test was run in Phase 368.

## Cross-source re-ranking — SEC Form 4 identity gate (Phases 345–346)

- Phase 345 replicated six purposive historical cohorts: 413 candidate transaction rows across 262/262 retrieved Form 4 accessions. In the 2023+ cohorts, event-time identity was 273/301 rows (90.70%); stricter transaction-date identity was 263/301 (87.38%). Both remain below the preregistered 95% admission gate. The 2006Q1/2012Q1 legacy cohorts had 0/112 rows resolved by the current same-context XBRL target-fact method.
- Phase 346 tested legacy periodic HTML as a bridge. Among 96 transaction-date-eligible older-cohort rows, 53 had issuer-specific ticker prose matching Form 4, but only one unique same-row class/exchange table anchor group (two candidate rows) was usable and strictly pre-transaction. The method is not a universal historical security master.
- Decision: stop expanding the legacy HTML parser as a universal solution; retain only candidate-level evidence with explicit venue distinctions. No insider return study or security master admission. See [Phase 345](https://github.com/jafelix81/NuevaEstrategia/blob/phase346-form4-legacy-html-identity-bridge/research/PHASE345_SEC_FORM4_MULTIQ_COHORT_IDENTITY_REPLICATION_2026-11-12.md) and [Phase 346](https://github.com/jafelix81/NuevaEstrategia/blob/phase346-form4-legacy-html-identity-bridge/research/PHASE346_FORM4_LEGACY_HTML_IDENTITY_BRIDGE_AUDIT_2026-11-12.md).

## PIT and source limitations

Official FINRA metadata defines:
- `lastReportedDate`: last time a firm sent an update contributing to the aggregate;
- `lastUpdateDate`: most recent date on which total trades were updated from ATS/OTC data;
- `initialPublishedDate`: first publication date after the reporting delay (two weeks for T1, four weeks for T2/OTC).

`lastReportedDate` is **not** an approved universal join key and is not the knowledge/availability date. For generic weekly rows, no complete PIT availability ledger is established. In the Phase 368 sample, T1 ATS summary types had no post-initial update-date gaps, while some OTC summary types did. Only if the wider T1 ATS audit passes will the next tradable session after initialPublishedDate be considered as a conservative date-level candidate. Exact intraday first-receipt timestamps and interim vintages are not reconstructed.

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
2. Phase 369: sample a wider set of T1 ATS weeks and reconcile aggregate symbol/product rows to firm-level rows; measure symbol/week and participant coverage.
3. Only if the T1 ATS update-date and grain gates pass, define a conservative next-tradable-session availability rule and consider descriptive venue-concentration features.
4. Re-audit Phase20C execution timing on the 12 pseudo-OOS dates with next-session open entry; never reuse the six consumed Phase20B final-OOS dates.
5. Test any admitted feature versus frozen LTM/F80 only after data/PIT gates pass, with identical exposure/costs, strict chronology, a new untouched holdout, clustered bootstrap, LOO and multiplicity controls. Continue Cboe and SEC work in parallel when a data-feasibility gate is ready.

## Controls

No signal admitted. No economic test, no holdout use, no parameter/universe/capital/production change. No PR merged. `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen.

## FINRA daily short-flow review — Phase 20C artifact re-audit

- Phase 20C completed 12 rolling pseudo-OOS training-era test dates from 2021-05-03 to 2024-10-30. The final six signal dates remained untouched. The factor selected by the walk-forward rule changed across SHORT_RATIO_PERSIST20 (1 date), SHORT_RATIO_Z20 (6) and SHORT_EXEMPT_RATIO (5), so selection stability was weak.
- Replacement-minus-blocked deltas: H5 mean +0.141%, median -0.049%, 5/12 positive; H10 mean -1.686%, median -1.837%, 3/12 positive; H20 mean -0.858%, median -0.333%, 5/12 positive. A post-hoc date-resampling 95% interval included zero at all three horizons. Twelve dates and four blocked/four replacement names per date are insufficient for promotion.
- Critical execution timing: FINRA states daily Reg SHO files are posted no later than 6:00 p.m. ET on trade date, with rare later corrections. Phase20C used close-to-close forward returns from close t. Since the data arrive after the regular close, close t is not an executable entry. Re-evaluate only the 12 pseudo-OOS dates using next-session open entry and a fixed close exit; do not reuse the six consumed Phase20B final-OOS dates.
- Official FINRA timing/correction policy: https://www.finra.org/finra-data/browse-catalog/short-sale-volume-data/daily-short-sale-volume-files. Phase20C run/artifact: https://github.com/jafelix81/NuevaEstrategia/actions/runs/40098425254.



## Latest FINRA update — Phases 369–370 (2026-11-13)

- Phase 369 retrieved 19 full T1 historic partitions (Nov 2021–Nov 2025): **1,022,474 rows / 215 pages**, zero errors, all Record-Total values reconciled. The original strict date and grain gates jointly passed 17/19.
- Phase 370 diagnosed both exceptions. The 2021-11-15 boundary week has 2,411 ATS rows revised 225–284 days after initial publication; exclude it from PIT candidate use. The 2025-11-10 strict bridge exception is one symbol with separate CTS and UTP aggregate rows; the combined aggregate (6,977,436 shares / 100,079 trades) exactly matches 28 firm rows. Firm rows lack productTypeCode, so only combined symbol-level attribution is permitted; tape-specific participant attribution is not.
- Revised sampled evidence: 18/18 non-boundary weeks pass the ATS update-date candidate gate; 19/19 symbol-week totals reconcile when the explicit multi-product combined-symbol fallback is used. This is still a stratified sample, not exhaustive history or proof of exact intraday PIT. lastReportedDate remains rejected as a universal join key.
- Phase 369 run [43462182950](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43462182950), artifact [14056609868](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43462182950/artifacts/14056609868). Phase 370 run [43473406924](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43473406924), artifact [14061977572](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43473406924/artifacts/14061977572). Reports: [Phase 369](PHASE369_FINRA_T1_ATS_EXPANDED_PIT_GRAIN_AUDIT_2026-11-13.md), [Phase 370](PHASE370_FINRA_T1_ATS_BOUNDARY_AND_DUPLICATE_DIAGNOSTIC_2026-11-13.md).
- Decision: retain T1 ATS as a **conditional broker-dealer reporting-concentration candidate**, not an institutional/beneficial-owner signal. Proceed to monthly historical coverage and descriptive concentration feasibility only. Do not run returns until the broader PIT, security identity, universe coverage and historical revision gates pass.
- FINRA short-flow Phase 20C remains diagnostic-only. Its 12 pseudo-OOS dates were originally evaluated close-to-close despite files arriving after the close. A separate corrected next-session-open evaluation remains required; do not use the six consumed Phase 20B final-OOS dates.
- No new Smart Money feature has demonstrated incremental cost-adjusted OOS edge. No new signal admitted. No holdout use, no parameter/universe/capital/production change. F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen.


## Latest update — Phases 371–374 (2026-11-13)

### Phase 371 — 47-month T1 ATS monthly sample

- FINRA historic inventory contains 209 T1 weekly partitions. Phase 371 selected one week per month (closest to day 15) for Jan-2022–Nov-2025: 47/47 full partitions retrieved, **2,469,987 rows / 517 pages**, zero retrieval errors, all Record-Total values matched.
- Sample union: 3,092 symbols and 37 participant keys. This is a monthly stratified sample, not a census of all 209 weeks.
- Aggregate symbol/product rows reconciled to firm rows in **47/47** sampled months; descriptive broker-dealer reporting concentration gate passed 47/47.
- Strict date gate passed **38/47**. Five other months had a 22-calendar-day initial-publication lag but zero post-publication update gaps; the exact-21-day check was overly strict for holiday-shifted dates. Four months contained actual post-initial revisions: 2023-11-13 (2,103 rows), 2024-02-12 (3), 2025-05-12 (1,831), 2025-06-16 (3). Total positive-update rows: 3,940/2,016,703 ATS symbol-level rows (0.1954%).
- All HHI/top-share statistics are descriptive reporting-intermediary concentration, not beneficial-owner or institutional-flow identification and not an alpha signal.
- Full report: [Phase 371](PHASE371_FINRA_T1_ATS_MONTHLY_COVERAGE_CONCENTRATION_AUDIT_2026-11-13.md); run [43474430280](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43474430280), artifact [14065151518](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43474430280/artifacts/14065151518).

### Phase 372 — FINRA daily short-flow next-open retest blocked

- The original Phase 20C used close-to-close returns from the close when the daily FINRA file is posted after the regular session. Phase 372 pins the original price window (2016-10-24 to 2026-10-24), preserves the 335 configured tickers and requires the same 329 valid names before any return calculation.
- Both hosted attempts failed the pre-analysis data gate: 328/329 valid; seven unresolved symbols (AVB, EA, EQR, LPRO, ROKU, WBD, WBS). A targeted ROKU retry from its first trading date (2017-09-28) did not recover data. Do not drop ROKU, alter the universe, or mix vendors without reconciliation. No next-open pseudo-OOS returns were calculated; no holdout was used.
- Full blocker report: [Phase 372](PHASE372_FINRA_SHORT_FLOW_NEXT_OPEN_RETEST_BLOCKER_2026-11-13.md); runs [43481196468](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43481196468) and [43481200906](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43481200906).
- Decision: suspend full Phase 20C reruns until a targeted, source-consistent ROKU price retrieval diagnostic succeeds. The 12-date Phase 20C result remains weak and non-promotable.

### Phase 373 — Cboe source ranking updated

- Cboe Option Trades is now the highest-priority broad options-flow candidate: OPRA-wide U.S. stock/ETF/index options, advertised history from Jan-2012, trade timestamp to milliseconds, trade price/size, NBBO and optional trade-time IV/Greeks. It does not directly expose participant capacity, open/close or beneficial-owner identity; aggressor side must be estimated with trade-condition/NBBO controls.
- Options PITCH is a conditional four-venue depth-of-book/execution/auction microstructure source (C1/C2/BZX/EDGX), with archive from Oct-2019 and proprietary licensing. TBT remains C1-only and retrospective before the conservative public-launch documentation floor.
- Public sample ZIP bytes could not be retrieved; no parser/sample validation, trial, vendor contact, purchase or card authorization.
- Report: [Phase 373 Option Trades/PITCH ranking](https://github.com/jafelix81/NuevaEstrategia/blob/phase373-cboe-tbt-source-feasibility-audit/research/PHASE373_CBOE_OPTION_TRADES_AND_OPTIONS_PITCH_SOURCE_RANKING_2026-11-13.md). Draft [PR #48](https://github.com/jafelix81/NuevaEstrategia/pull/48) updated.

### Phase 374 — revision-stable T1 ATS symbol panel completed

- Full retrieval of the 47 monthly T1 partitions passed: **2,469,987 rows / 517 pages**, all Record-Total counts reconciled, 47/47 symbol bridges passed.
- Across 98,887 symbol-week groups, **96,919 were revision-stable and concentration-ready (98.0098%)**. The remaining 1,968 groups (1.9902%) were excluded because at least one aggregate or firm row had a post-initial update or date/schedule issue.
- Revision exclusions were concentrated in 2023-11-13 (1,051 symbol groups) and 2025-05-12 (915); one group each was affected in 2024-02-12 and 2025-06-16.
- Stable concentration coverage represented **95.3829% of mapped aggregate share volume** in the 47-month sample. This is descriptive broker-dealer reporting-participant concentration, not beneficial-owner or institutional-flow identification.
- All 47 monthly sample partitions passed exact aggregate-to-firm symbol-level shares/trades reconciliation. The sample remains one selected week per month, not a census of all 209 historic weekly partitions.
- Correction: Phase 374 summary field unique_participant_keys_union_count is erroneous (it counts distinct per-week count/week pairs, not unique participants). Do not use it. Phase 375 recomputes the union count in memory with hashed keys and persists only the count.
- Run [43481384832](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43481384832), artifact [14067403379](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43481384832/artifacts/14067403379).
- Exact PIT remains unestablished: initialPublishedDate is date-only and the API does not expose a complete intermediate-vintage/first-receipt ledger. No historical return test is authorized.

### Phase 375 — exhaustive weekly T1 ATS revision audit in progress

- Expands from the 47-month sample to all **209 consecutive T1 historic weekly partitions**, 2021-11-15 through 2025-11-10.
- Reuses the Phase 374 symbol-week revision and aggregate-to-firm reconciliation rules; reports anonymized weekly coverage, revision, share-volume, participant-union and concentration statistics only.
- Corrects the Phase 374 participant-union count defect by hashing MPID/CRD-derived keys in memory; no raw identifiers or hashes are persisted.
- The first preflight run [43493288658](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43493288658) failed only because a synthetic test fixture omitted rows/pages; the fixture was corrected. The corrected run [43493465495](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43493465495) passed compilation and all five offline tests and is now retrieving the 209 partitions. Do not start a duplicate.
- This remains data-feasibility only; exact intraday PIT, forward returns, alpha, OOS, bootstrap, LOO and holdout are not authorized.

### Cross-source reconciliation — OptionMetrics TradeFlow vs Cboe Option Trades

- Repository audit confirmed Phases 142/143/180/181 already rank **IvyDB TradeFlow as the primary conditional all-venue signed-flow candidate**. Phase 181 preregistered five competing mechanisms and nine blocked admission gates; no raw data, feature, or backtest has been admitted.
- TradeFlow advertises all U.S. options across exchanges from 2016-01, 5m/30m/EOD, and four tables (Signed_Volume, Trade_Conditions, Market_Structure, Signed_Exchange). Its 2026-09-30 launch means the 2016 history is a backfill claim, not proof of live 2016 availability. Participant fields are execution-style proxies; Institutional 2 is aggressive liquidity demand, not total institutional activity or beneficial-owner identity.
- Cboe Option Trades (2012-01 advertised OPRA archive) is now classified as the **independent raw trade/NBBO validation candidate**, not a replacement or higher-priority signal source. Cboe Open-Close is complementary for capacity × side × open/close on four Cboe venues; PITCH is a separate order-book microstructure source.
- Corrected Phase 373 report and PR #48 to remove the contradictory ranking. No sample bytes or independent classification validation obtained; no vendor contact, trial, purchase, alpha or OOS test.
- Phase 181's nine gates remain blocked: representative active/inactive sample, interval semantics, first receipt, corrections/vintages, classifier version/backfill, per-field participant/lot-size history, independent classification accuracy, effective-dated identity, and price/license/derived-data rights.

### Phase 376 — CFTC TFF index positioning source feasibility completed

- Added CFTC Traders in Financial Futures (TFF), Futures Only, as a conditional weekly **macro regime / positioning** candidate. Public dataset gpe5-46if advertises about 47.3k rows / 90 columns, history from 2006-06-13, and categories Dealer, Asset Manager, Leveraged Money, Other Reportables and Non-Reportables.
- Public history includes E-mini S&P 500 (13874A), Nasdaq-100 Mini (209742), Russell E-Mini (239742) and DJIA x $5 (124603); codes remain provisional pending full-history continuity audit.
- CFTC confirms positions are as of Tuesday and normally released Friday 3:30 p.m. ET; actual release dates are available only for the latest 13 months. Historical data is static after publication, but the release-date gap prevents strict historical PIT before the verified window. The 2025 shutdown backlog requires actual special-announcement dates; the 2026-11-10 report is scheduled for 2026-11-16 due Veterans Day.
- CFTC categories are self-reported predominant-business-purpose classifications, not trader identities or verified trade intent. Markets can disappear below the 20-large-trader threshold; missing weeks must not be forward-filled.
- Phase 376 is documentation/source feasibility only. Phase 377 should audit the full public TFF Futures Only dataset, natural keys, index-contract coverage, category continuity, actual recent release dates and historical schedule proxy. No alpha or return test is authorized.
- [Phase 376 report](research/PHASE376_CFTC_TFF_INDEX_POSITIONING_FEASIBILITY_AUDIT_2026-11-13.md).

## Controls reaffirmed

No new Smart Money signal admitted. No economic/OOS test from Phases 371–374, no holdout use, no production/universe/capital/parameter change. `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen. No PR merged.


## Phase 377 — CFTC TFF full coverage and contract-key audit (2026-11-13)

- Added a read-only full-snapshot audit for the official TFF Futures Only Socrata dataset (gpe5-46if), with metadata/count checks before and after retrieval, schema/position-field discovery, report-date/code duplicate tests, weekly gaps, candidate contract-code/name continuity, missingness and open-interest reconciliation diagnostics.
- Candidate series are tested separately: 13874A E-mini S&P 500, 209742 Nasdaq-100 Mini, 239742 Russell 2000 Mini, and 124603 DJIA x $5. The related 13874+ S&P 500 Consolidated line is surfaced as a separate non-additive comparison, not combined with 13874A.
- Missing contract-weeks remain missing, never zero or forward-filled. CFTC ID is tested for duplicates but is not treated as a natural primary key.
- Only anonymized summary output is retained; no raw rows or IDs, no return/alpha/OOS/bootstrap/LOO/holdout test.
- Phase 377 branch workflow has been added and is expected to run on its branch push. The result is pending; no data gate is claimed yet.
- Phase 375 full 209-week FINRA T1 ATS retrieval remains active in run 43493465495 / job 132120346426 (step 6, full retrieval). No duplicate FINRA run was started.
- Phase 376 remains a conditional macro-positioning source only. Actual release dates beyond the latest 13 months are unavailable per CFTC FAQ; older release calendars are schedule proxies, not strict PIT.
- F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen; legacy holdout remains consumed and unused.

## Latest update — Phases 377–378 (2026-11-13)

### CFTC TFF — full coverage and Russell contract-era audit

- Phase 377 completed successfully: 47,322 TFF Futures Only rows / 90 columns, row count and metadata snapshot reconciled, zero duplicate candidate (report date, contract code) keys.
- Phase 378 completed successfully: 1,236 Russell rows across codes 239742, 239741 and 23977A; zero duplicate keys, zero invalid dates, stable metadata snapshot.
- Critical contract identity correction: CFTC code 239742 is not one continuous Russell series. It has 119 old Russell 2000 Mini observations (2006-06-13–2008-09-16, $100 multiplier) and 482 later E-mini observations (2017-08-15–2026-11-03, $50 multiplier), separated by 3,255 days. Use only the post-2017 E-mini era as the current Russell candidate.
- 239741 is a separate $500 Russell contract and is entirely pre-TFF-launch backcast. 23977A is a separate ICE Russell Mini series, ending 2018-06-05; do not splice or merge it with CME 239742.
- CFTC's TFF explanatory notes say pre-2010-07-22 historical category labels were backcast using recent trader classifications. Exclude those rows from primary TFF research. Actual historical release dates beyond the verified recent window remain unavailable; strict historical PIT is not established.
- Correction to Phase 377 coverage reporting: holiday-shifted Monday/Wednesday report dates were counted as missing Tuesday anchors. Phase 378's interval method treats 6–8 day gaps as normal weekly reporting and confirms no internal >8-day gap in the two 239742 episodes or the 239741/23977A samples. The 3,255-day 239742 break remains a separate contract-era break.

Run [Phase 377](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43497266092), artifact [14071613332](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43497266092/artifacts/14071613332). Run [Phase 378](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43498339093), artifact [14071808959](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43498339093/artifacts/14071808959). Draft PR [#53](https://github.com/jafelix81/NuevaEstrategia/pull/53).

**Disposition:** CFTC TFF remains a conditional broad-market positioning/crowding candidate, not a stock-specific smart-money signal. No feature or return test is authorized yet.

### FINRA T1 ATS census

Phase 375 remains the only active FINRA retrieval; its full 209-week T1 audit step is still running in [run 43493465495](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43493465495). Do not start another copy. The latest job inspection showed compile/tests passed and the full historic-partition retrieval step in progress; no final artifact is available yet.

### Economic and production controls

- F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen.
- No new Smart Money feature admitted; no forward-return, alpha, OOS, bootstrap, LOO or fresh holdout test from Phases 377–378.
- Legacy holdout remains consumed and unavailable.
- No production, capital, exposure, universe or parameter changes.
- Phase 20C remains blocked on reproducible recovery of the original 329 valid price histories; do not change the 335-symbol universe to force completion.
- OptionMetrics TradeFlow remains a conditional data-access/availability candidate; no purchase or vendor contact.

**Economic progress remains 35%** because no incremental, cost-adjusted OOS edge has been demonstrated.

## CFTC archive timestamp audit — Phase 379 (2026-11-13)

- Phase 379 corrected run [43499068179](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43499068179) passed; artifact [14072598314](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43499068179/artifacts/14072598314).
- The CFTC static TFF archive's final Updated date was not earlier than the official publication date in 23/23 recent official-schedule samples; 22 exact, one +2 days (2025-12-23 report: official Dec29, archive Updated Dec31).
- Six older archive-only samples from 2017/2020/2022/2023/2024 were all retrieved and showed Updated dates three days after report dates; they lack independent release-date verification.
- First Phase 379 run [43498878730](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43498878730) failed only because the initial acceptance rule demanded exact equality. The corrected conservative rule (Updated >= official publication date) passed.
- Archive Updated is a candidate conservative availability bound, not a formally certified first-publication timestamp. Candidate execution rule: first regular market session after Updated; never same-day close. Strict PIT and alpha remain unauthorized pending a full post-launch weekly archive census and correction/migration review.
- Draft PR [#54](https://github.com/jafelix81/NuevaEstrategia/pull/54).

## CFTC TFF full archive census — Phase 380 (2026-11-13)

- First contemporaneous TFF report date corrected to 2010-07-20 (positions as of July 20; static archive Updated July 23), not the July 22 announcement date. Prelaunch/backcast report dates are before July 20.
- Phase 380 retrieved 846/851 post-launch static archive pages (99.4125%); 214 report dates before first TFF report are backcast and excluded.
- Five pages failed: 2011-06-14, 2013-12-31, 2014-11-25, 2014-12-02, 2019-12-24.
- One page heading mismatch: report date 2018-09-25 requested, archive file says positions as of 2018-09-18.
- Two stale Updated fields predate report dates: 2011-05-10 page says Updated 2010-05-13; 2012-10-16 page says Updated 2007-06-29.
- Recent official schedule crosschecks remain 23/23 not earlier than release (22 exact, one +2 days), but the historical anomalies invalidate a global Updated-date PIT assumption.
- Median archive lag 3 days, p90 4, max 70 days. First TFF report page check: 2010-07-20 positions, Updated 2010-07-23.
- Decision: no global CFTC PIT acceptance. Per-page date/heading exclusions and targeted anomaly repair required; no TFF alpha test authorized. Phase 380 report includes a workflow key mismatch note (first_report_page_gate key).
- [Phase 380 run](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43499455469), [artifact](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43499455469/artifacts/14074090576), draft PR #55.

## Russell E-mini TFF archive panel — Phase 383 (2026-11-13)

- Phase 383 passed: [run 43500752903](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43500752903), [artifact 14074056247](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43500752903/artifacts/14074056247).
- CFTC code 239742 post-2017 E-mini series: 482 API rows, 2017-08-15–2026-11-03; count reconciled before/after, metadata stable, zero duplicate report-date/code keys.
- 480/482 static archive pages valid (99.5851%). Exclude 2018-09-25 (page heading is 2018-09-18) and 2019-12-24 (404); CFTC API has one 239742 row on each exception date. Never forward-fill.
- Valid-page archive lag: median 3 days, p90 6, maximum 50. All 23 official-schedule crosschecks in the series were not earlier than publication.
- Candidate for exploratory macro positioning/crowding research using first regular session after archive Updated; not a certified first-publication timestamp. No alpha or return test yet.
- Draft PR [#58](https://github.com/jafelix81/NuevaEstrategia/pull/58).

## FINRA Phase 20C price-provider blockage — Phase 381

- Phase 381 completed in [run 43500356535](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43500356535), artifact [14073108228](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43500356535/artifacts/14073108228).
- Yahoo query1/query2 returned 2,514 daily rows for all four controls (AAPL/MSFT/NVDA/SPY), but HTTP 200 with zero timestamps for all seven missing names (AVB, EA, EQR, LPRO, ROKU, WBD, WBS).
- Stooq did not return a parseable Date/Close series; Nasdaq API returned empty rows for all 11 symbols including controls, so its current endpoint/parameters are not validated.
- No fallback admitted. Phase 20C remains blocked at 328/329; do not change the original 335-symbol universe or mix price sources. Draft PR #57.

## CFTC archive exception repair — Phase 382

- Phase 382 completed in [run 43500470656](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43500470656), artifact [14073179326](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43500470656/artifacts/14073179326).
- Only 2/8 anomaly targets had exact-heading pages, both with stale Updated dates. No adjacent exact page found for six others.
- The two missing/misaligned dates inside Russell 239742 are 2018-09-25 and 2019-12-24; each has one API row. The other archive exceptions affect older ICE 23977A or unrelated report weeks.
- HTTP Last-Modified did not repair stale historical dates; many older pages show a 2018-01-17 migration date. Draft PR #56.

## Still running

FINRA Phase 375 remains the only active full 209-week T1 ATS retrieval in [run 43493465495](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43493465495). Compile/tests passed; the historic-partition retrieval step is still running. Do not duplicate it.

**Controls:** F80 remains frozen. No new signal admitted, no holdout used, no production/capital/universe/parameter changes. Phase 20C remains blocked pending reliable prices for all 329 required names.


## Phase 384 — CFTC TFF prospective first-receipt capture bootstrap (2026-11-13)

- Added an append-only prospective capture design for four CFTC TFF Futures Only index contracts: E-mini S&P 500 (13874A), Nasdaq-100 Mini (209742), DJIA $5 (124603), and only the post-2017 E-mini Russell era (239742).
- Historical CFTC rows are stored as a feature warm-up baseline only and are explicitly signal_eligible=false; archive Updated dates are not retroactively certified as first publication.
- Scheduled captures run Fridays at 22:15 UTC. The pipeline receipt timestamp is the conservative knowledge clock. New report-date/code rows first observed by a scheduled run may be eligible only from the next regular equity session after receipt. Manual runs, late arrivals and revisions are never signal-eligible.
- The capture records selected aggregate positions, open interest, source hashes and normalized features. Spread positions remain separate from directional net; OI reconciliation includes spreads on both long and short sides. Missing weeks are not forward-filled.
- Legacy Phase 23C is not being repeated: it selected among eight features/directions at each of only 12 pseudo-OOS dates, omitted transaction costs and identical-exposure F80 comparison, and produced weak 20-session results (NASDAQ -0.460%, S&P 500 -3.058% mean strategy returns). No new alpha test is authorized.
- Phase 384 is research-only. The scheduled workflow will not activate until this draft branch is merged. No F80, production, universe, capital, parameter, exposure or holdout changes.
