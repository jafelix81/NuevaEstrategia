> **Superseded for issuer-level interpretation by Phase 155 (2026-11-06).** The Phase 35/28D input is a CIK-submissions query sample, not a subject-issuer-validated panel. Its 303 distinct CIK/ticker pairs are source/query identities. The exact positive control `0000895421-24-000178` is keyed to Morgan Stanley (filer CIK `0000895421`, ticker `MS`) although the SEC-validated subject is abrdn Global Infrastructure Income Fund (CIK `0001793855`). Retain Phase 154's date counts only as descriptive form-level statistics of that filer-query sample; do not use its issuer/ticker joins, event panel, or returns. See [Phase 155](PHASE155_SEC_13DG_ROLE_AWARE_EVENT_DATE_AND_PHASE154_QUARANTINE_2026-11-06.md).

# Phase 154 — SEC Schedule 13D/G event-date semantics and reporting-regime audit

**Date:** 2026-11-06  
**Status:** Completed offline audit of the immutable Phase 35/28D artifact; no return or alpha test.

## Executive decision

Do not pool Schedule 13D and 13G event_date values into one event-time feature. In the pinned sample, quarter-end dates account for **82.71% of valid 13G event dates (15,119/18,279)** but only **1.57% of valid 13D event dates (22/1,400)**. The 13G concentration is strongly consistent with a reporting-period anchor rather than a common trade/accumulation timestamp. The exact filer subtype and underlying report still need to be parsed before assigning a more specific meaning.

The legacy filing_lag_business_days column is unusable: all non-missing values are either **-1 (19,538 rows)** or **0 (139 rows)**, with 588 missing. A negative business-day lag cannot be accepted as valid. Quarantine the column; do not repair it by guessing a calendar convention.

Use actual EDGAR acceptance timestamp as the earliest public-knowledge boundary. The date-only filing_date and reported event_date are not substitutes for acceptance time.

## Immutable source and reproducibility

Reused corrected Phase 35 run **41575083622**, artifact **13212292743** (phase35-13dg-pit-event-crosswalk-audit). No SEC download or new API request was made.

- GitHub artifact ZIP digest (API metadata): 1ba55129f8a2f2365b37e20f557759fbccd2ab2f22781f03930065c11f16337f
- Inner phase28d_events.csv SHA-256: 4a1b40cf7e104be0dc5bad4d579cd65ef78ab4783a4f525f19a299b50f3efa14
- Rows: 20,265; unique accessions: 20,265; duplicate accession rows: 0.
- Filing-date range: 2020-10-01 through 2026-09-30.
- Unique source/query CIKs: 303; unique source/query tickers: 303. These are not validated subject-issuer identities.

## Filing mix: raw filing counts are not independent events

| Form | Rows | Share of sample |
|---|---:|---:|
| SC 13D | 215 | 1.06% |
| SC 13D/A | 1,209 | 5.96% |
| SC 13G | 5,509 | 27.18% |
| SC 13G/A | 13,332 | 65.79% |
| **Total amendments** | **14,541** | **71.75%** |

A raw count is dominated by amendments, especially 13G/A. An amendment is a new filing-time disclosure/update, not automatically a new acquisition or independent accumulation event. Parent accession, filer identity, filer subtype and changed ownership facts must be resolved before creating event flow.

## Event-date semantics

### Quarter-end concentration

| Form / filing type | Before 2024-09-30 | From 2024-09-30 | Interpretation |
|---|---:|---:|---|
| 13G original | 72.77% (1,387/1,906) | 95.34% (3,272/3,432) | Strong reporting-period signature |
| 13G/A | 73.04% (4,548/6,227) | 88.05% (5,912/6,714) | Strong reporting-period signature |
| 13D original | 1.23% (2/163) | 1.96% (1/51) | No comparable quarter-end concentration |
| 13D/A | 1.82% (13/713) | 1.27% (6/473) | No comparable quarter-end concentration |

September 30, 2024 is the SEC compliance date for revised Schedule 13G filing deadlines. The SEC's 2023 amendments generally moved QII/exempt initial 13G reporting to 45 days after the quarter in which the threshold is crossed and moved material 13G amendments to 45 days after the quarter in which the change occurs; special rules remain for passive investors and certain positions above 10%. The table is descriptive and does **not** establish that the rule change caused the observed mix shift: this artifact does not reliably classify every filer under Rule 13d-1(b), (c), or (d).

The SEC distinguishes 13D (control intent) from 13G (exempt/non-control categories). Therefore, the same event_date field must not be treated as economically equivalent across the two forms. For 13G, quarter-end concentration is a strong warning that the field often represents a reporting-period anchor. For 13D, it is more plausibly a reported triggering-event date, but it is still not the market-knowledge time.

### Filing-to-event calendar lag diagnostics

- All valid event dates: median 30 days; p90 44; p99 70; minimum -326; maximum 4,721.
- 13D originals: median 10 calendar days before 2024-02-05 (136 valid rows) and 7 days from that date onward (78 valid rows). The p90 falls from 25.5 to 10.6 days, but p99 remains extreme because of stale/legacy dates.
- 13D/A: median 3 calendar days before 2024-02-05 (546 valid rows) and 2 days from that date onward (640 valid rows); the later-sample p90 is 26.4 and p99 is 4,504.8 because of extreme stale/legacy dates. Do not use the mean or raw lag without adjudication.
- 13G originals: median 39 days before and 35 days after the 2024-09-30 compliance break.
- 13G/A: median 40 days before and 24 days after the break.
- Two 13G original rows have event_date later than filing_date; quarantine them. 139 rows are same-day; acceptance timestamp is still required to determine whether information was available before a trading decision.

These are calendar-day diagnostics, not legal timeliness calculations. They do not establish when a filer acquired, sold, or crossed a threshold.

## Other extraction limits

| Field | Coverage in this artifact |
|---|---:|
| report_date | 0.00% (all 20,265 missing) |
| reporting_person | 17.28% populated |
| reporting_person_type | 49.55% populated |
| purpose_text | 1.29% populated |
| shares_beneficially_owned | 82.71% populated |
| percent_class | 98.59% populated |

The current extraction is not adequate to identify every reporting person, reliably classify filer subtype, reconstruct groups, or build a complete 13D activist-purpose feature. The purpose_text field is particularly sparse; missing text does not mean no activist intent.

The mapping_source field is sec_current for 20,068 rows and historical_mapper for 197. These labels do not establish historical share-class identity or active-universe membership. The 27 unresolved names and fixed-335 universe limitation remain open.

## PIT and modeling rules

1. Keep 13D and 13G in separate populations and separate hypotheses.
2. Keep originals and amendments separate. Resolve previousAccessionNumber/parent accession and diff structured ownership facts before calling an amendment incremental.
3. For 13G, do not use event_date as trade date or a common signal date. Parse filer subtype, cover-page fields, reporting period and applicable rule regime.
4. For 13D, retain event_date only as a reported trigger-date candidate; use acceptance time for knowledge and quarantine stale/extreme or future event dates.
5. Retrieve actual acceptance timestamps and use the next tradable session after acceptance as the conservative executable boundary unless a more precise public-dissemination timestamp is proven.
6. Quarantine the legacy filing_lag_business_days field. Do not substitute an unverified calendar approximation.
7. Do not expand one filing across multiple reporting persons as if each person independently filed the same event. Preserve group/reporting-person relations separately.
8. Do not run returns until historical subject issuer, security class, active-universe membership, amendment lineage and point-in-time acceptance are independently validated.

## Decision and next gate

Phase 154 is a data-semantics audit, not an alpha test. The corrected Phase 35 artifact supports a reproducible descriptive audit, but the extracted panel is **not approved for economic testing**. The most promising distinct 13D hypothesis remains a filing-time activist/control-intent disclosure, while 13G should be treated as periodic/threshold ownership-state disclosure. Both require structured XML parsing and role-aware identity, but they should not share a generic event-date feature.

Next no-purchase step: extend the existing complete-submission parser to extract Schedule 13D/13G filer subtype, exact previousAccessionNumber, all reporting persons/group relations, ownership fields and accession acceptance timestamps from already authorized sample artifacts. Do not restart the broad SEC bulk download until the repository's authorized contact identity is configured. Historical active-universe reconstruction remains a separate prerequisite.

No return test, alpha claim, final-holdout use, vendor contact/purchase, or production change. F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen.

## Official references

- SEC, [Adopts Amendments to Rules Governing Beneficial Ownership Reporting](https://www.sec.gov/newsroom/press-releases/2023-219) (October 10, 2023): form purpose distinctions, shortened 13D/13G deadlines, and September 30, 2024 compliance date for revised 13G deadlines.
- SEC, [Final Rule 33-11253](https://www.sec.gov/files/rules/final/2023/33-11253.pdf): revised initial and amendment deadlines by filer category.
- Federal Register, [88 FR 76896](https://www.govinfo.gov/app/details/FR-2023-22678): final rule publication and effective dates.
