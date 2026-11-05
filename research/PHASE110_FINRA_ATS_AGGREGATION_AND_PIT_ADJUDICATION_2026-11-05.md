# Phase 110 — FINRA ATS/OTC aggregation and PIT adjudication

**Date:** 2026-11-05  
**Input:** Phase 109 live artifact, run https://github.com/jafelix81/NuevaEstrategia/actions/runs/42003973132, artifact https://github.com/jafelix81/NuevaEstrategia/actions/runs/42003973132/artifacts/13405295714  
**Artifact SHA-256:** f1bb176b2bee66d0d736b21e1e6ed64f28053c98aa47baebdd0d48f7a82cfe2d  
**Raw rows SHA-256:** 45b6b169c1d57a1874438362295a656c5bc6499b2c29d6e3be8bd10a48425231  
**Mode:** offline adjudication of immutable raw rows; no network requests, prices, forward returns, or vendor data.

## 1. Decision in one sentence

**FINRA weekly ATS/OTC symbol totals and participant-level detail reconcile exactly at the symbol/week/tier/family level in all 10 sampled partitions; the 16 apparent Phase 109 cohort failures are a defect in the cohort diagnostic, not a failure of the underlying totals.** PIT remains conditional because final values can be revised long after first publication, and permanent-security mapping and broad historical universe are not yet established.

## 2. Artifact-level integrity

| Check | Result |
|---|---:|
| Partitions completed | 10/10 |
| Raw records | 968,139 |
| Downloaded pages with SHA-256 | 199 |
| FINRA Record-Total reconciliations | 10/10 exact |
| Week/tier mismatches | 0 |
| Unknown summary types | 0 |
| Invalid numeric values | 0 |
| Negative quantities/trade counts | 0 |
| Expanded candidate-key collision groups | 0 |

The Phase 109 job completed successfully. Its logs show all ten partitions completed, no partition errors, and the raw artifact was uploaded. The artifact is retained in GitHub Actions; it is not copied into the repository because it is a large immutable source extract.

## 3. Correct aggregation rule

The raw artifact contains:

- 108,444 symbol-aggregate rows, including one row without an attributable symbol;
- 857,833 symbol-firm rows, including one row without an attributable symbol;
- 108,425 symbol/week/tier/family groups after excluding only rows with a genuinely blank symbol.

Across those 108,425 groups:

- all 108,425 have both aggregate and firm-detail levels;
- all 108,425 match exactly on total shares;
- all 108,425 match exactly on total trade count;
- there are zero aggregate-only or firm-only symbol groups.

The correct reconciliation is therefore:
1. group by week, tier, family (ATS or OTC non-ATS), and symbol;
2. sum all symbol-aggregate product rows;
3. sum all symbol-firm participant rows;
4. compare the two weekly totals.

### Why Phase 109 reported 16 cohort failures

Phase 109 additionally tested a diagnostic rule that attempted to allocate firm rows to aggregate rows by intervals of lastReportedDate. Sixteen symbol groups failed that date-bucket test, even though their total shares and total trades reconciled exactly.

That diagnostic assumption is not supported by FINRA's field definitions:

- productTypeCode identifies the SIP trade feed or OTC-equity feed;
- lastReportedDate is the last date a firm sent an update to underlying data contributing to an aggregate;
- the firm-level records do not carry the same product-feed dimension needed to allocate each firm row to a CTS or UTP aggregate row.

Thus, lastReportedDate is not a participant-report cohort key. The 16 cases are not evidence of missing or contradictory volume. The Phase 109 field fully_reconciled is too strict for this unsupported cohort allocation and must not be used as the source-level acceptance metric. The 100% total-level reconciliation is the relevant result.

Official field definitions: https://www.finra.org/sites/default/files/OTC-transparency-website-user-guide-v5.pdf, especially the product, publication, update, and last-reported-date definitions.

## 4. Unallocated rows and symbol parsing

Exactly two rows have a genuinely blank symbol. Both belong to 2022-01-03 / T2 / OTC and each carries 100 shares and one trade:

- one OTC symbol-aggregate UTP row;
- one De Minimis Firms symbol-firm row.

They reconcile to each other, but cannot be assigned to a security. Preserve them in market-level completeness checks and exclude them from ticker-level features.

A separate parsing hazard was identified: the literal ticker NA is valid and appears in 61 raw rows. CSV readers must not silently convert it to a null value (for pandas, use keep_default_na=False). The Phase 110 regression tests preserve this symbol.

## 5. Publication and revision timing

All 108,444 symbol-aggregate rows in the sample have the relevant publication/update date fields.

| Tier | Aggregate rows | Updated after first publication | Share revised | First-publication lag from week start |
|---|---:|---:|---:|---:|
| T1 | 21,305 | 1,428 | 6.703% | 21 calendar days |
| T2 | 87,139 | 454 | 0.521% | 35 calendar days |
| Total | 108,444 | 1,882 | 1.735% | — |

Among rows updated after first publication, the delay from initial publication to the latest update was:

| Tier | Median | 90th percentile | 95th percentile | Maximum |
|---|---:|---:|---:|---:|
| T1 | 148 days | 316 days | 316 days | 324 days |
| T2 | 134 days | 302 days | 302 days | 331 days |

The first-publication lags are consistent with FINRA's two-week T1 and four-week T2/OTC reporting delays when measured from the end of the reporting week to the next publication Monday/business day.

**PIT rule for a current final-value extract:** do not backdate a revised value to initialPublishedDate. Use lastUpdateDate as the latest underlying-data update marker and make the value eligible no earlier than the next regular trading session after that date. Test a further one- and five-session buffer as sensitivity cases. This is deliberately conservative, but it is still a candidate rule rather than proof of an exact historical dissemination timestamp: the guide defines lastUpdateDate as the later of last-reported and initial-published dates and says files/updates are available no earlier than 6:00 AM ET on business days. It does not provide a complete historical timestamp for each public update.

For an unrevised row, lastUpdateDate equals the first-publication date. For a revised row, the API's current final value must not be used at the earlier first-publication date.

## 6. Historical coverage: an important archive lead

The FINRA Developer Center says the API's weeklySummaryHistoric dataset is a rolling four-year historical window, while weeklySummary contains the latest rolling 12 months. Therefore, the API route alone offers at most roughly five years when the two datasets are combined. See https://developer.finra.org/news/q12021.

However, FINRA's OTC Transparency Website User Guide (2019) says the Download page's Year selector provides access to all historical published weekly reports within the selected year, and its screenshots show 2016 reports. That raises a separate, testable possibility: the website's downloadable archive may preserve weekly files older than the API's rolling historical window.

This is not yet a verified 2016+ data-coverage claim. The current UI's historical download path and its machine-readable endpoint still need to be tested. The next phase should retrieve one old T1 and one old T2 weekly file (preferably 2016/2017), compare the schema and values with an overlapping API week, and verify the current archive's actual earliest available date.

## 7. Research interpretation and remaining gates

FINRA ATS/OTC data are venue/member-firm aggregates, not beneficial-owner identities or buyer/seller-initiated flow. MPID/CRD concentration can describe the reporting venue/member structure, but it does not prove that an institution or informed investor was on one side of a trade.

Potential hypotheses, only after the remaining gates pass:

- ATS versus non-ATS volume and share-of-volume changes;
- concentration and turnover of ATS MPIDs;
- concentration and turnover of non-ATS member firms;
- changes in De Minimis versus attributed volume;
- interaction with liquidity, volatility, and price-impact regimes.

Before any return test:

1. verify the older website archive and current production/API continuity;
2. establish a reproducible publication/update availability rule;
3. map historical symbols to permanent security IDs, including inactive, delisted, renamed, and acquired securities;
4. validate broad-universe coverage and denominator volume;
5. preregister a mechanism and compare against frozen LTM/F80 under identical exposure/costs, chronological OOS, bootstrap, and LOO rules.

**No alpha test is authorized by Phase 110.** No forward returns were used. No vendor was contacted or purchased. F80 remains frozen.

## 8. Reproduction

Run the offline adjudicator against the Phase 109 artifact ZIP:

    python -m unittest -v research/test_phase110_finra_ats_artifact_adjudication.py
    python research/phase110_finra_ats_artifact_adjudication.py phase109-finra-ats-full-reconciliation.zip --output phase110_summary.json

The four regression tests cover product-feed total reconciliation, the valid NA ticker, genuinely missing symbols, and use of the latest update date for a final revised value.
