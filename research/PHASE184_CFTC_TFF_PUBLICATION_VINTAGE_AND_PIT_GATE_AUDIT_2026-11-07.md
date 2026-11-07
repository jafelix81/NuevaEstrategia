# Phase 184 — CFTC TFF/COT publication-vintage and historical PIT gate audit

**Date:** 2026-11-07  
**Status:** `HISTORICAL_PIT_GATE_FAIL_PHASE23C_QUARANTINED`  
**Control:** `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen.  
**Scope:** Official CFTC publication-timing and correction notices; static audit of the legacy Phase 23C timing/label logic. No COT download, return test, holdout use, vendor contact, purchase or production change.

## Executive decision

CFTC TFF/COT remains useful only as a possible broad equity-index regime descriptor. It is not stock-level flow, does not identify individual traders, and does not establish that a category's positions are informed or directional bets.

The historical PIT gate fails for the existing 2016–2024 backtest window. The CFTC explicitly says it does **not** maintain a historical release-date list beyond the latest 13 months. Its ordinary Friday 3:30 p.m. ET schedule is a general rule, not a complete historical publication ledger. Official notices document material exceptions in 2021, 2023, 2025 and the 2018–2019 funding lapse.

A deterministic `ReportDate + 6 calendar days` proxy is not a publication timestamp. In the 21 documented date-level exceptions assembled here, that proxy places 20 reports before their actual publication date and places one on the publication date without an exact release time. The 2023 ION outage overlaps the Phase 23C training history and contaminates the 2023-03-27 walk-forward split.

**Disposition:** quarantine the Phase 23C historical walk-forward; do not rerun or retune it on the same dates. Do not admit historical CFTC features from 2016–2024 as strict PIT without an independent archived release/first-receipt ledger. Prospective shadow capture is possible only with a timestamped first-receipt logger, immutable vintages and next-session execution. No alpha test is authorized by this phase.

## 1. What CFTC actually publishes

COT reports describe positions as of Tuesday's close, generally released Friday at 3:30 p.m. Eastern. The report covers futures markets where at least 20 traders meet CFTC reporting thresholds. TFF categories are based on the predominant business purpose self-reported by traders on Form 40 and reviewed by CFTC staff; the CFTC does not publish individual trader identities or the specific reasons for positions.

Consequences:
- TFF is a market-level positioning/regime measure, not a stock-level Smart Money feed.
- Dealer/Intermediary, Asset Manager/Institutional and Leveraged Funds are business-purpose classifications, not verified beneficial owners or a clean long/short conviction ranking.
- Positions can change because traders enter/leave the reportable population or change classification, not only because they traded.
- Contract coverage can disappear when fewer than 20 reportable traders remain.

Official CFTC FAQ also states that historical release dates are listed only for the latest 13 months. This prevents a complete official reconstruction of release dates for the Phase 23C 2016–2024 training history.

## 2. Documented publication exceptions

The deterministic ledger contains 21 date-level report/publication pairs supported by CFTC special announcements. It deliberately does not invent an exact time-of-day or a first-received timestamp.

### 2023 ION reporting disruption — seven reports

| Data/report date | Originally scheduled | Documented publication date |
|---|---:|---:|
| 2023-01-31 | 2023-02-03 | 2023-02-24 |
| 2023-02-07 | 2023-02-10 | 2023-03-03 |
| 2023-02-14 | 2023-02-17 | 2023-03-08 |
| 2023-02-21 | 2023-02-24 | 2023-03-10 |
| 2023-02-28 | 2023-03-03 | 2023-03-14 |
| 2023-03-07 | 2023-03-10 | 2023-03-16 |
| 2023-03-14 | 2023-03-17 | 2023-03-21 |

The CFTC attributed the disruption to a third-party ION incident that prevented reporting firms from submitting timely and accurate data. The CFTC then released the backlog chronologically. Some reports also contained contract-specific position/open-interest corrections. This is directly relevant to the Phase 23C 2023-03-27 test split: a synthetic +6-day rule would have made delayed reports appear available before they were published.

### 2025 lapse in federal appropriations — 13 reports

The final CFTC schedule update dated 2025-12-09 is used where an earlier interim schedule differed.

| Data/report date | Originally scheduled | Final documented publication date |
|---|---:|---:|
| 2025-09-30 | 2025-10-03 | 2025-11-19 |
| 2025-10-07 | 2025-10-10 | 2025-11-21 |
| 2025-10-14 | 2025-10-17 | 2025-11-25 |
| 2025-10-21 | 2025-10-24 | 2025-12-02 |
| 2025-10-28 | 2025-10-31 | 2025-12-05 |
| 2025-11-04 | 2025-11-07 | 2025-12-09 |
| 2025-11-10 | 2025-11-14 | 2025-12-10 |
| 2025-11-18 | 2025-11-21 | 2025-12-12 |
| 2025-11-25 | 2025-12-01 | 2025-12-15 |
| 2025-12-02 | 2025-12-05 | 2025-12-17 |
| 2025-12-09 | 2025-12-12 | 2025-12-19 |
| 2025-12-16 | 2025-12-19 | 2025-12-23 |
| 2025-12-23 | 2025-12-29 | 2025-12-29 |

### 2021 holiday exception — one report

The report based on 2021-06-15 positions was scheduled for 2021-06-18 but published on 2021-06-21 because of the new federal holiday. The synthetic +6-day date is also 2021-06-21; without an exact release time, using that same day's close as an executable entry is not proven. The conservative entry is the next actual exchange session.

### 2018–2019 shutdown

CFTC announced that the last COT report before the shutdown was published on 2018-12-21. The next report (based on 2018-12-24 data) had been scheduled for 2018-12-28 and was expected to be published on 2019-02-01, followed by catch-up releases twice weekly. The cited notice describes an expected schedule, not a complete verified first-publication ledger for every missed report. This episode is therefore recorded as an unresolved outage window, not converted into invented row-level timestamps.

## 3. Static audit of legacy Phase 23C

The legacy script:
- sets `KnowledgeDate = ReportDate + 6 calendar days`;
- merges market returns on that synthetic date;
- selects feature/direction using 5-session Spearman;
- does not require each training label's end session to be strictly before the test entry session.

The +6-day proxy fails against the documented exceptions:
- 19/21 documented rows: synthetic date is earlier than actual publication date;
- 2/21: synthetic date equals the publication date, but exact time-of-day is absent;
- 2023-03-27 walk-forward training can therefore include several reports whose synthetic knowledge dates precede their actual publication dates.

Phase 182 independently found a second, separate defect: no horizon-specific label-maturity embargo. Six of twelve dates contained an immature 5-session training label; all twelve contained immature 20-session labels. These two defects are cumulative, not alternative explanations.

The original Phase 23C outputs are quarantined. Do not reuse the reported performance, feature selection, directions or date splits as confirmatory evidence.

## 4. Required rules for any future CFTC use

1. Preserve `report_date`, official scheduled date, actual publication date, exact publication timestamp (if available), first-received UTC timestamp, source URL, raw SHA-256, retrieval time and every later correction as separate fields.
2. Never infer publication time from `report_date + 6`, weekday arithmetic or the current release schedule.
3. If actual first-publication time cannot be reconstructed, classify the historical row as `PIT_UNKNOWN` and exclude it from strict PIT tests.
4. For date-only publication evidence, first eligible execution is the next actual exchange session after the publication date. Do not use the publication-date close.
5. Use an exchange calendar. A training label is mature only when `label_end_session < test_entry_session`; same-session maturity is not allowed.
6. Apply a horizon-specific embargo independently for H5, H10, H20, H60 and any other horizon. The longest label used in feature/direction selection must also be mature.
7. Store CFTC correction notices and downloaded vintages append-only. A later correction must not overwrite what was knowable earlier.
8. Keep TFF as broad regime context only; do not label the categories “informed money” or map them to individual equities.

## 5. Reproducibility and disposition

- Snapshot: `research/phase184_cftc_release_vintage_pit_audit.json`
- Auditor: `research/phase184_cftc_release_vintage_pit_audit.py`
- Tests: `research/test_phase184_cftc_release_vintage_pit_audit.py`
- Workflow: `.github/workflows/phase184_cftc_release_vintage_pit_audit.yml`

The auditor is offline and fail-closed. It validates the documented exception ledger and emits the PIT gate result. It does not download CFTC files or calculate returns.

**Final disposition:** `CFTC_TFF_HISTORICAL_PIT_NOT_ADMITTED`; `PHASE23C_QUARANTINED_NO_REUSE`; prospective shadow capture only after a real first-receipt logger is available. No alpha test, holdout use, vendor contact, purchase or production change. `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen.

## Official sources

- CFTC COT FAQ and methodology: https://www.cftc.gov/MarketReports/CommitmentsofTraders/index.htm
- CFTC current release schedule: https://www.cftc.gov/MarketReports/CommitmentsofTraders/ReleaseSchedule/index.htm
- CFTC historical special announcements (2021, 2023, 2025 and earlier exceptions): https://www.cftc.gov/MarketReports/CommitmentsofTraders/HistoricalSpecialAnnouncements/index.htm
- CFTC 2019 shutdown catch-up schedule, Press Release 7864-19: https://www.cftc.gov/PressRoom/PressReleases/7864-19
- Legacy Phase 23C implementation: https://github.com/jafelix81/NuevaEstrategia/blob/phase23c-cftc-cot-walkforward/Nueva_Estrategia_Fase23C_CFTC_COT_WalkForward.py
- Phase 182 label-maturity audit: https://github.com/jafelix81/NuevaEstrategia/blob/phase99-broad-pit-universe-charter/research/PHASE182_LEGACY_SMART_MONEY_EXPERIMENT_VALIDITY_AUDIT_2026-11-07.md
