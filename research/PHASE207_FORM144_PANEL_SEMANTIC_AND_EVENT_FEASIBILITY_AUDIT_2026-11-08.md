# Phase 207 — SEC Form 144 issuer-event panel semantic and event-feasibility audit

**Audit date:** 2026-11-08 UTC  
**Disposition:** conditional event-supply candidate; **not strict-PIT admitted, no feature or alpha test authorized**.  
**Input:** immutable Phase 69/98 GitHub Actions artifact 13385365595 from run 41959603351. No SEC request, no raw-document retrieval, no vendor contact, no purchase, no forward-return test, no holdout use, and no production change.

## Executive result

The existing Form 144 panel is materially more useful than the earlier ten-CIK incremental extension suggested. The extension itself correctly found zero new events for those ten fund-registrant CIKs; it did not invalidate the existing issuer-event panel.

The archived panel contains **21,634 issuer-side candidate rows** across 14 quarters, 2023 Q2–2026 Q3, with 21,634 unique accessions, 289 issuer CIKs and 289 current-universe tickers. Against the 335-name current mapping, 289 names had at least one event (86.27% event incidence). This is event incidence, not historical security-master completeness or a claim that every zero is a true no-event for the full historical universe.

The data are rich enough to justify further PIT and execution-validation work: the panel contains proposed units, aggregate market value, security class, broker, exchange, seller name, free-text relationship, acquisition lots, prior-three-month sales, approximate sale date, amendments and structured 10b5-1 plan-adoption dates. But several fields are not safe to turn directly into signal magnitudes.

## 1. Reproducible panel inventory

| Measure | Result |
|---|---:|
| Issuer-event rows | 21,634 |
| Unique accessions / duplicate accessions | 21,634 / 0 |
| Quarters | 14 (2023 Q2–2026 Q3) |
| Unique issuer CIKs | 289 |
| Current tickers with at least one event | 289 / 335 = 86.27% |
| Original Form 144 | 21,438 |
| Form 144/A amendments | 196 |
| 144/A with previous accession present | 196 / 196 |
| 144/A previous accession inside the 14-quarter census | 195 / 196 |
| Issuer-match rows | 21,633 |
| Ambiguous issuer-match rows | 1 |
| Filer-only false positives excluded from issuer-event panel | 14 |
| Control rows / pair concordance | 280 / 100% |

The original scan's 14 filer-only false positives remain excluded. The single ambiguous_pair_issuer_match row remains quarantined for issuer-level inference; it is not silently promoted to a clean issuer event.

The ten additional fund-registrant CIKs in Phase 69 contributed zero incremental accessions in the tested 2023 Q2–2026 Q3 period. That result closes only that CIK extension; it does not close the broader Form 144 source.

## 2. Proposed-sale timing: mostly contemporaneous, not a forward schedule

Using the minimum approximate sale-date gap across each notice's tranches:

| Approximate sale date relative to filing date | Events | Share |
|---|---:|---:|
| Same calendar day | 20,641 | 95.41% |
| Earlier than filing date | 552 | 2.55% |
| Later than filing date | 441 | 2.04% |

The event-level gap ranges from -366 to +15 calendar days. The negative-date cases and long offsets need source-document review; do not reinterpret them as execution dates or silently shift them.

Rule 144 requires the notice to be transmitted concurrently with placing the broker order or executing directly with a market maker. Form 144's approximate sale date is not an execution confirmation. Because 95.4% of notices have a same-day approximate sale date, the useful hypothesis is **near-event supply/price pressure after public availability**, not a long lead-time forecast. The event clock must be EDGAR acceptance/first-public-availability, not the filing date alone; conservatively begin at the next full regular session after the verified acceptance date unless a stronger public-receipt record exists.

## 3. Amendments are state updates, not new independent sales

The panel contains 196 144/A rows. All 196 have previous_accession; 195 point to an accession inside the 14-quarter census. Treat amendments as append-only versions of the original notice. They can revise amount, date or other details, but must not be counted as a fresh independent sale event by default. The one predecessor outside the census needs an external anchor before its state can be reconstructed.

## 4. 10b5-1 plan-date field: use the structured date, not text search

A structured plan-adoption date is present on 12,130 rows (56.07%), containing 12,132 individual dates. The median date-to-filing lag is 193 days and the 90th percentile is 383 days. One record has a plan date one day after filing (accession 0001495896-23-000010); quarantine it pending source review.

The parser's free-text mentions_10b5_1 flag is not a substitute for the structured field:

- 1,375 rows have both a text mention and a structured date;
- 49 have a text mention but no structured date;
- 10,755 have a structured date but no text mention;
- 9,455 have neither.

The structured plan-adoption date should be validated against the XML schema and source document. It is disclosed at Form 144 filing time; **never backdate the market's knowledge to the plan-adoption date**. Plan age can be a pre-registered stratification hypothesis, not evidence that a sale is informed or discretionary.

## 5. Proposed-sale amount fields: one material denominator failure

The panel has 21,863 sale tranches across 21,634 notices; 188 notices contain multiple tranches. Median proposed units are 9,261 and median aggregate market value is USD 961,955.69. These are notice amounts, not verified executed quantities or proceeds. Form 144 instructions define aggregate market value as of a specified date within ten days before filing.

The filer-entered noOfUnitsOutstanding field is **not safe as a shares-outstanding/float denominator**. In a primary SEC Workday Form 144 XML example, noOfUnitsOutstanding is 261, while the filing's remarks state that it should say 261M. The panel's mechanical proposed-units/reported-outstanding ratio consequently reaches 16.18x; two tranches exceed 100%, and 13 exceed 10%. These are data-quality flags, not evidence that the sale exceeds the issuer's actual shares outstanding. Do not use this denominator for float impact, sizing or signal strength. Use an independently sourced, point-in-time share-count/float series after security identity is resolved.

## 6. Coverage and interpretation limits

- Electronic Form 144 reporting for reporting-company securities became mandatory on **2023-04-13**. Earlier EDGAR records are incomplete because paper filing was permitted/common. The current panel therefore starts at the electronic-coverage boundary; do not treat earlier EDGAR absence as no notice.
- Rule 144 notice thresholds are more than 5,000 shares or aggregate sale price over USD 50,000 during a three-month period. This is threshold-censored activity, not every affiliate sale.
- A Form 144 is an intended/proposed sale notice. It is not proof the sale completed. Form 144/A is an amendment, not a new sale by default.
- Seller names and relationship fields are free text; 4,162 distinct seller-name strings are not 4,162 verified people. Do not equate the XML filer CIK with the person whose account is being sold.
- The current 335-ticker mapping is not a survivorship-free historical F80 universe. Delisted issuers, ticker/class transitions and seller-to-Form-4 identity links remain unresolved.
- The panel has filing dates but no ACCEPTANCE-DATETIME or first-public-receipt timestamp. The SEC's 2023 rule allows Form 144 filing through 10 p.m. ET on a Commission business day and changes deemed filing treatment after 5:30 p.m.; therefore filing-date-only timing is insufficient.

An independent third-party open-data snapshot (GetCoattail, 2026-10-17) reports 63,013 electronically filed Form 144 notices across 1,455 issuers from 2023-04-13 through 2026-10-13, with 29,456 structured plan-adoption dates. It is a useful scale cross-check, not a replacement for primary SEC records; its stated reuse terms require attribution and a link. The current panel's 21,634 rows are the subset found in the 335-name current mapping, not a full-market census.

## 7. Decision and next gates

**Keep Form 144 as a conditional event-supply candidate, not a Smart Money direction signal.** Its value is a timely notice of a proposed affiliate sale, with role, size, plan-date and broker/exchange context. The competing hypotheses are supply/temporary price pressure, information/selection effects, and planned-sale/no-incremental-information. Do not assume one mechanism.

Before any return test:

1. Join every accession to SEC filing-index ACCEPTANCE-DATETIME; preserve original and amended versions append-only. Do not use filing_date as the PIT clock.
2. Resolve seller identity separately from filer identity and map issuer/class to a dated security master, including delisted and predecessor securities.
3. Cross-match subsequent Form 4 executions only with robust seller, issuer, class and date-aware identity; measure the fraction of proposed notices that are followed by executed sales.
4. Replace noOfUnitsOutstanding with independent PIT shares outstanding/float and use proposed value/units only with explicit field semantics.
5. Freeze the eligible universe and all event definitions before inspecting returns. Then preregister distinct hypotheses (e.g., proposed value / ADV, officer/director/10% holder, structured 10b5-1 plan age, repeat seller, amendment revision, same-day vs future approximate sale date), controlling for prior returns, momentum, liquidity, earnings/events and concurrent Form 4 transactions.
6. Only after the data gates pass, compare incremental value against frozen LTM/F80 with identical exposure/costs, chronological walk-forward, label-maturity embargo, date-block bootstrap and leave-one-ticker-out. Use a new prospective final holdout; the legacy holdout remains CONSUMED_NOT_PRISTINE.

No feature, forward-return, bootstrap/LOO, OOS or final-holdout test is authorized by Phase 207. F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen.

## 8. Reproducibility

- Prior artifact: [Phase 69/98 run 41959603351](https://github.com/jafelix81/NuevaEstrategia/actions/runs/41959603351), artifact 13385365595.
- Artifact ZIP SHA-256: f84644200a8925c6fc190a823ca0dcd6b40c7bee127a8d2740a5ea67cae56519.
- expanded_issuer_event_raw.csv SHA-256: 7a54ee09e8d4520e1ec14cf22f2c0d1c62d077798b14d3db596826e3360a3659.
- Audit code used Python standard library; raw seller names and raw filing text are not copied into this phase's committed result. Seven offline regression tests passed locally.

## Sources

- SEC Investor.gov, Form 144 overview and electronic filing date: https://www.investor.gov/introduction-investing/investing-basics/glossary/form-144
- SEC Form 144 (official form and instructions): https://www.sec.gov/about/forms/form144.pdf
- SEC Release 33-11159, Extending Form 144 EDGAR Filing Hours, effective 2023-03-20: https://www.sec.gov/files/rules/final/2023/33-11159.pdf
- Rule 144, 17 CFR 230.144: https://www.ecfr.gov/current/title-17/section-230.144
- Data.gov, SEC EDGAR Form 144 dataset metadata: https://catalog.data.gov/dataset/edgar-form-144
- SEC primary Workday Form 144 XML example showing 261 and remarks correcting it to 261M: https://www.sec.gov/Archives/edgar/data/1787944/000197236223000452/primary_doc.xml
- GetCoattail, Open Data snapshot 2026-10-17 (third-party scale cross-check; attribution/link terms): https://getcoattail.com/datasets

## 9. Compact machine-readable summary

    {
      "phase": 207,
      "source": "SEC Form 144 / 144-A",
      "panel": {
        "rows": 21634,
        "unique_accessions": 21634,
        "duplicate_accessions": 0,
        "quarters": 14,
        "period": "2023Q2-2026Q3",
        "unique_issuer_ciks": 289,
        "current_universe_event_incidence": "289/335 = 86.27%",
        "original_144": 21438,
        "144A": 196,
        "144A_previous_accession_in_census": "195/196",
        "filer_only_false_positives_excluded": 14,
        "ambiguous_issuer_rows": 1
      },
      "sale_timing_min_gap_by_event": {
        "same_day": 20641,
        "past": 552,
        "future": 441,
        "minimum_days": -366,
        "maximum_days": 15
      },
      "plan_dates": {
        "rows_with_structured_date": 12130,
        "individual_dates": 12132,
        "median_age_days": 193,
        "p90_age_days": 383,
        "negative_age_rows": 1,
        "text_mention_true": 1424,
        "text_mention_without_structured_date": 49,
        "no_text_mention_with_structured_date": 10755
      },
      "amounts": {
        "tranches": 21863,
        "multi_tranche_events": 188,
        "median_proposed_units": 9261,
        "median_aggregate_market_value_usd": 961955.69,
        "reported_outstanding_ratio_gt_100pct_tranches": 2,
        "reported_outstanding_ratio_gt_10pct_tranches": 13,
        "reported_outstanding_ratio_max": 16.1800766284,
        "reported_outstanding_ratio_admitted": false
      },
      "strict_pit_admitted": false,
      "feature_admitted": false,
      "alpha_test_authorized": false,
      "holdout_used": false,
      "production_changed": false,
      "f80_frozen": true,
      "legacy_holdout_status": "CONSUMED_NOT_PRISTINE"
    }
