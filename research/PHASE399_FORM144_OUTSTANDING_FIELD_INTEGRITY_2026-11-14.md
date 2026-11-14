# Phase 399 — Form 144 outstanding-share denominator integrity and amendment-parent follow-up

**Date:** 2026-11-14  
**Scope:** Offline audit of the Phase 67 issuer_event_raw.csv artifact plus five point-in-time share-count cross-checks against SEC annual reports. No returns, prices, feature tests, or strategy changes.

## Executive decision

**Kill noOfUnitsOutstanding as a numeric denominator for Form 144 supply-pressure features.** Retain the raw source field only for version-to-version comparison inside a filing/amendment chain. The field has no scale metadata in the extracted panel, and its raw values do not reconcile consistently with contemporaneous published share counts.

This does not kill Form 144 as a possible event source. The proposed units and proposed aggregate market value may still be useful as raw event attributes. Any future size normalization should use an independently sourced, strictly lagged point-in-time dollar ADV or another validated denominator—not the Form 144 outstanding-share field.

## 1. Reproducible panel audit

Input: Phase 67 artifact 13334881835, file issuer_event_raw.csv.

| Measure | Result |
|---|---:|
| Issuer-event rows | 21,634 |
| Form 144 | 21,438 |
| Form 144/A | 196 |
| Sale tranches | 21,863 |
| Tranches with missing/nonpositive outstanding field | 7 |
| Tranches with computable raw units/outstanding ratio | 21,856 |
| Raw ratio greater than 1% | 99 |
| Raw ratio greater than 10% | 13 |
| Raw ratio greater than 100% | 2 |
| Maximum raw ratio | 16.1801 |
| Median raw ratio | 0.00002250 |

These ratios are **diagnostics only**. They are not economically meaningful percentages because the denominator's unit/scale is not established. The two raw ratios above 100% (WDAY and EXPE) would be impossible if numerator and denominator were consistently expressed in the same unit.

The script deliberately does not guess whether a value such as 261, 1,775, 7,422, 582,647, or 6,444 means shares, thousands, millions, a stale count, or a filing error.

## 2. Independent share-count cross-checks

The comparisons below use issuer annual reports available before the respective Form 144 filing dates. They are not used to backfill or rescale the Form 144 field.

| Ticker | Form 144 raw field | Published share count | Finding |
|---|---:|---:|---|
| WDAY | 261 | 204m Class A + 55m Class B (2023-01-31) | A millions-scale interpretation is plausible, but no scale metadata exists |
| EXPE | 1,775 | 117,011,421 common + 5,523,452 Class B (2026-01-30) | No unambiguous conversion |
| COST | 7,422 | 442,740,572 (2023-10-03) | No unambiguous conversion |
| WFC | 582,647 | 3,793,867,540 (2023-02-10) | No simple shares/thousands/millions conversion reconciles |
| MSFT | 6,444 | 7,427 million (2026-06-30) | Millions-scale is plausible but materially differs from the recent published count |

Sources:
- https://www.sec.gov/Archives/edgar/data/1327811/000110465923058436/tm233886d2_ars.pdf
- https://www.sec.gov/Archives/edgar/data/1324424/000132442426000008/expe-20251231.htm
- https://www.sec.gov/Archives/edgar/data/909832/000090983223000042/cost-20230903.htm
- https://www.sec.gov/Archives/edgar/data/72971/000007297123000071/wfc-20221231.htm
- https://www.sec.gov/Archives/edgar/data/789019/000119312526323660/msft-20260630.htm

The differences may reflect filer input errors, stale source values, class definitions, or inconsistent presentation scales. This audit does not choose among those explanations. It establishes that the raw field is not safe for a common denominator across issuers or time.

## 3. Amendment-parent follow-up

The Phase 398 raw artifact has three unmatched parent accessions:

| Amendment | Parent accession | Current status |
|---|---|---|
| WFC 0001766264-23-000004 | 0001766264-23-000002 | Outside current accession census or missing; original parent payload not retrieved |
| GIS 0001318751-23-000003 | 0001318751-23-000002 | Present in broader accession census, absent from candidate event panel; original payload not retrieved |
| BKR 0001959173-23-003500 | 0001959173-23-003484 | Present in broader census, absent from candidate panel; original parent payload not retrieved |

For Baker Hughes, the SEC amendment XML identifies issuer CIK 0001701605, name Baker Hughes Co and file number 001-38143, and its remarks state that the issuer name and SEC file number were corrected. A third-party mirror of the parent row reports issuer CIK 0000808362, Baker Hughes Holdings LLC and file number 001-09397. The CIK differs as well. This is a **versioned issuer-identity correction candidate**, not a resolved parent join: the original parent SEC XML has not been recovered. Preserve both versions; do not merge them by accession alone.

For General Mills and Wells Fargo, the parent accession references are now explicit, but their original parent payloads remain unretrieved. Do not infer the parent's fields from the amendment.

## 4. Feature and research consequences

1. Exclude noOfUnitsOutstanding from denominators, percentages, size scores and model features.
2. Preserve the raw field and its filing version for audit/change detection only.
3. Keep proposed units and proposed aggregate USD value as separate raw attributes; do not treat either as an executed sale.
4. If the event survives identity, coverage and PIT gates, evaluate proposed USD value relative to strictly lagged dollar ADV using independent historical prices/volume. The price/volume series must be available before the filing event's eligible session.
5. Continue to version every 144/A at its own filing date. Never backdate revised fields to the original 144.
6. No economic test is authorized by this audit.

## 5. Reproducibility and validation

- research/phase399_form144_outstanding_field_audit.py — standard-library audit script.
- research/test_phase399_form144_outstanding_field_audit.py — four synthetic regression tests.
- research/PHASE399_FORM144_OUTSTANDING_FIELD_SUMMARY_2026-11-14.json — complete counts, top raw-ratio cases, manual reference checks and parent follow-up.
- Command: python research/phase399_form144_outstanding_field_audit.py --input issuer_event_raw.csv --output phase399_summary.json
- No raw Phase 67 artifact was copied into the repository.

**Controls:** no forward returns, no LTM/F80 changes, no holdout access, no production changes, no vendor contact or purchase.
