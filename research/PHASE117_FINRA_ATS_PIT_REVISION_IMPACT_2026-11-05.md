# Phase 117 — FINRA ATS/OTC revision-impact and PIT eligibility audit

**Date:** 2026-11-05  
**Input run:** [Phase 109](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42003973132)  
**Input artifact:** [13405295714](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42003973132/artifacts/13405295714)  
**Artifact SHA-256:** `f1bb176b2bee66d0d736b21e1e6ed64f28053c98aa47baebdd0d48f7a82cfe2d`  
**Raw `raw_rows.csv.gz` SHA-256:** `45b6b169c1d57a1874438362295a656c5bc6499b2c29d6e3be8bd10a48425231`  
**Mode:** offline analysis of immutable Phase 109 raw rows; no network requests, prices, forward returns, or vendor data.

## 1. Decision

**The final-value FINRA extract cannot be treated as a first-publication vintage.** Only 1.735% of symbol-aggregate rows are marked revised, but those rows account for 10.08% of shares and 11.44% of trades in this sample. Revisions are concentrated in T1 OTC non-ATS, where dropping revised rows would remove 33.24% of shares and 36.22% of trades.

Do not backdate current final values to `initialPublishedDate`. Also do not use the eventual revised/unrevised classification as a historical filter: that classification is only known after observing future updates and would itself create look-ahead selection.

## 2. Input integrity and field semantics

- Raw rows: 968,139.
- Symbol-aggregate rows (`ATS_W_SMBL` and `OTC_W_SMBL`): 108,444.
- Reporting weeks: five (2022-01-03, 2023-01-09, 2024-01-08, 2025-01-06, 2025-10-20), each sampled for T1 and T2.
- `lastUpdateDate == max(initialPublishedDate, lastReportedDate)` in **108,444/108,444** aggregate rows; zero mismatches.
- Revised rows are exactly those where `lastUpdateDate > initialPublishedDate`; 1,882 rows (1.735%). The remaining 106,562 rows have `lastUpdateDate == initialPublishedDate`.

FINRA's User Guide v6 describes `lastUpdateDate` as the most recent date on which aggregate shares/trades were updated based on data received from ATSs/member firms; it defines the underlying firm update date separately from first publication. It does not supply a timestamp for when each revised value became publicly disseminated. See the [FINRA OTC Transparency User Guide v6](https://www.finra.org/sites/default/files/2019-11/OTC-transparency-website-user-guide-v6.pdf), especially pp. 6–7, 12–13, 26–27, and the [FINRA Weekly Summary API documentation](https://developer.finra.org/docs#query_api-equity-weekly_summary).

## 3. Revision impact by tier and data family

| Tier / family | Aggregate rows | Revised rows | Revised % | Shares retained if revised rows dropped | Trades retained if revised rows dropped |
|---|---:|---:|---:|---:|---:|
| T1 ATS | 10,637 | 0 | 0.000% | 100.00% | 100.00% |
| T1 OTC non-ATS | 10,668 | 1,428 | 13.386% | 66.76% | 63.79% |
| T2 ATS | 41,370 | 2 | 0.005% | 99.98% | 99.98% |
| T2 OTC non-ATS | 45,769 | 452 | 0.988% | 96.24% | 93.91% |

| Tier | Revised rows | Revised % | Shares retained if revised rows dropped | Trades retained if revised rows dropped |
|---|---:|---:|---:|---:|
| T1 | 1,428 / 21,305 | 6.703% | 77.33% | 82.24% |
| T2 | 454 / 87,139 | 0.521% | 96.86% | 96.89% |
| Overall | 1,882 / 108,444 | 1.735% | 89.92% | 88.56% |

Dropping revised rows would remove 29 T1 OTC symbols and 17 T2 OTC symbols entirely from this five-week sample. This is a descriptive sample result, not an estimate for the full FINRA history.

## 4. Revision timing

Revisions appear in five of the ten week/tier partitions. Among revised rows:

| Tier | Count | Median days after first publication | 90th percentile | 95th percentile | Maximum |
|---|---:|---:|---:|---:|---:|
| T1 | 1,428 | 148 | 316 | 316 | 324 |
| T2 | 454 | 134 | 302 | 302 | 331 |

The delay is long enough that using current values at the first-publication date would create meaningful look-ahead exposure, particularly for T1 OTC.

## 5. PIT ruling

1. **Rejected:** current final values assigned to `initialPublishedDate` when `lastUpdateDate > initialPublishedDate`.
2. **Rejected as a PIT filter:** dropping rows because their current extract shows a later revision. Future revision status was not known at the initial publication date.
3. **Sensitivity only:** using current final values no earlier than `lastUpdateDate` plus one or five trading sessions. `lastUpdateDate` is an underlying firm-update marker, not a documented public dissemination timestamp; the buffer is not proof of availability.
4. **Preferred path:** preserve actual historical vintages or build immutable prospective snapshots with retrieval timestamps, then define availability as the first verified public capture. The FINRA website's affirmative user certification was not accepted; no attempt was made to bypass it.

The sample establishes data integrity and quantifies the revision problem. It does **not** establish a complete historical publication-vintage archive.

## 6. Research decision

FINRA ATS/OTC remains a conditional candidate, not an alpha-ready source. Before any forward-return test:

- verify actual public update timing or obtain historical vintages;
- establish historical security identity and delisted coverage;
- expand beyond the five sampled weeks;
- preregister whether the mechanism is ATS/non-ATS share, participant concentration/turnover, or another distinct feature;
- compare only after broad PIT universe and benchmark alignment pass.

No alpha test, feature selection, or portfolio change was made. No data were purchased and no provider was contacted. `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen.

## 7. Reproduction

```bash
python -m unittest -v research/test_phase117_finra_ats_pit_revision_impact.py
python research/phase117_finra_ats_pit_revision_impact.py phase109-finra-ats-full-reconciliation.zip
```

The auditor verifies the exact compressed raw-row SHA-256 before computing revision, tier/family, symbol-loss, share-volume, trade-count, and revision-delay metrics. Six offline regression tests pass.
