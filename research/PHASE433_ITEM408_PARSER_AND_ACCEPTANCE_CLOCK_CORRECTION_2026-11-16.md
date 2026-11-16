# Phase 433 — Item 408 parser scaffold and EDGAR acceptance-clock correction

**Date:** 2026-11-16 UTC  
**Decision:** parser/regression scaffold and source-clock correction completed; Item 408 remains **NOT ADMITTED FOR ALPHA**.

## Executive summary

This phase corrects three material defects in the Phase 432 illustrative example and establishes a reproducible, dimension-preserving Inline XBRL extraction scaffold.

1. CIK 0001373715 is **ServiceNow, Inc.**, not “NOW Inc.”
2. The ServiceNow 2023 Q3 Form 10-Q discloses **three** Rule 10b5-1 arrangements (Gina Mastantuono, William R. McDermott and Paul E. Chamberlain), not only two.
3. The SGML <ACCEPTANCE-DATETIME> value 20231025192050 is an Eastern wall-clock value. It is **not** 19:20:50Z. On 2023-10-25 New York was on EDT (UTC−04:00), so the corresponding instant is 2023-10-25T23:20:50Z. The earlier Phase 432 wording that labelled the raw value UTC was incorrect.

A further PIT refinement is essential: EDGAR acceptance is not a guaranteed timestamp for first external availability of the filing content. The SEC says there is no timestamp identifying when content first becomes available on sec.gov; filings are often available 1–3 minutes after acceptance, but lag can be materially longer. For historical daily research, use the next regular trading session after the acceptance date unless an independently captured PDS/first-seen receipt establishes an earlier public-availability time.

No actual raw filing bytes were downloaded or hash-verified in this phase. The parser passed synthetic regression fixtures only. A raw-file integration test remains pending.

## 1. Operational preflight — checked before changes

Repository: jafelix81/NuevaEstrategia  
Default branch: main  
Main HEAD before Phase 433: 15c07c33b44d8ca2f8aed0788f8f2b8b1ab77a82.

- Latest 100 Actions runs: 62 success / 37 failure / 1 cancelled; 7,668 total runs reported.
- Active, queued, waiting or requested runs: zero. No running workflow was duplicated.
- All 267 branches were inspected across three pages.
- 56 open PRs were inspected; 65 workflow files were present.
- Latest Phase 431 regression run [43816138832](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43816138832): one offline-regression job succeeded. Compile passed and all 5 Phase 431 tests passed. No artifact was expected.
- Latest SEC Form 144 capture [43795660996](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43795660996): offline-regression and live-capture jobs succeeded. The live capture logged 55 feed observations, zero new accessions, zero new events and zero eligible observations. Artifact [14194203412](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43795660996/artifacts/14194203412), 1,183 bytes, SHA-256 40211212baf071dcc5eb232c923bebbcc4d65708b95eaa26264002363a782cb9. The capture job committed its append-only state before upload. The schedule still shows a delivery gap; no manual dispatch or cron change was made.
- Latest CFTC TFF run [43525140200](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43525140200): one prospective-capture job succeeded; 3,035 warm-up rows, zero signal-eligible rows and no persistent capture changes. Artifact [14084802705](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43525140200/artifacts/14084802705), 1,068 bytes, SHA-256 c7a652038336f852e3c51792d1bdc96ebc1368176bdafdae0693332fb4224eef. The first prospective poll remains scheduled for 2026-11-16 22:15 UTC after the 20:30 UTC release; it was not run early.

The latest 100-run listing contained no newer Form 144 or CFTC run. These were historical snapshots at the time of preflight, not claims about later execution.

## 2. Corrections to the Phase 432 ServiceNow example

The SEC filing directory and SGML header identify CIK 0001373715 as **ServiceNow, Inc.** (SIC 7372). The 10-Q was for the quarter ended 2023-09-30, accession 0001373715-23-000419.

The filing's Item 5 narrative lists three arrangements:

| Person | Role | Adoption date | Disclosed sale terms | Stated expiration |
|---|---|---:|---|---:|
| Gina Mastantuono | CFO | 2023-07-28 | 317 shares plus 100% of net shares from vesting of 8,019 gross shares | 2024-05-24 |
| William R. McDermott | CEO | 2023-08-31 | 30,489 shares plus 100% of net shares from vesting of 9,986 gross shares | 2025-02-18 |
| Paul E. Chamberlain | Director | 2023-08-21 | 540 shares | 2024-09-03 |

The prior Phase 432 report omitted the CFO arrangement. These quantities describe plan terms/capacity, not confirmed executions or a schedule of actual sales. Net shares are stated after tax withholding.

### 2.1 Correct acceptance clock

The filing's SGML header contains:

    <ACCEPTANCE-DATETIME>20231025192050
    FILED AS OF DATE: 20231026

The SEC's PDS Technical Specification labels the header acceptance time as EST. The governing EDGAR filing rules specify Eastern Standard Time or Eastern Daylight Saving Time, whichever is currently in effect. Therefore, interpret the header as Eastern civil time with a date-aware America/New_York zone, preserving the original 14 digits.

For 2023-10-25:
- Raw header wall clock: 2023-10-25 19:20:50 Eastern.
- Eastern offset: EDT, UTC−04:00.
- Converted instant: 2023-10-25T23:20:50Z.
- Official filing date: 2023-10-26, because a 10-Q accepted after the 5:30 p.m. Eastern cutoff is deemed filed the next business day.

The Phase 432 report's raw time was four hours too early when labelled UTC. The 90-calendar-day markers after the three adoption dates are 2023-10-26, 2023-11-29 and 2023-11-19, respectively. These are only 90-day reference dates; the Rule 10b5-1 cooling-off condition can be later because it is the later of 90 days after adoption or two business days after the relevant earnings disclosure, subject to a 120-day cap. Do not infer the actual first permissible trade or execution from these dates alone.

### 2.2 Acceptance is not exact public dissemination time

The SEC Webmaster FAQ explicitly states that there is no timestamp indicating when filing content first becomes available on sec.gov. It says filings are often available 1–3 minutes after the EDGAR system timestamp, with potentially longer delays.

Consequently:
- Keep ACCEPTANCE-DATETIME as an EDGAR acceptance event, not an exact external dissemination event.
- If a PDS receipt or prospective first-seen capture exists, preserve it separately with its own provenance and clock.
- For historical daily backtests without a public-receipt timestamp, make the information usable no earlier than the next regular trading session after the Eastern acceptance date. Do not trade at that day's close or backdate to plan adoption/quarter end.
- Keep the official FILED AS OF DATE separately. It is a legal filing-date field and can differ from the acceptance date.

This is deliberately conservative and avoids treating an internal acceptance timestamp as proof that a market participant could already read the content.

## 3. Reproducible parser scaffold

Added research/phase433_item408_ixbrl_parser.py.

The standard-library parser uses Python's HTMLParser to traverse Inline XBRL without relying on rendered text tables. It:
- reads ix:nonNumeric, ix:nonFraction and ix:fraction facts;
- recognizes the ECD namespace, including a declared namespace alias;
- preserves contextRef, unitRef, decimals, scale, format and nil state;
- resolves each xbrli:context and retains the IndividualAxis and TradingArrAxis members separately;
- retains context period and entity identifier;
- includes facts nested in ix:hidden;
- follows continuedAt / ix:continuation chains and excludes ix:exclude text;
- preserves duplicate facts and original context grain;
- normalizes numeric scale/sign while retaining the raw lexical value;
- treats unresolved contexts, nil facts and zero tagged facts as unknown states.

It intentionally does **not**:
- aggregate amounts across arrangements or people;
- infer that a plan is active because no termination was found;
- treat natural expiration as a reported termination;
- infer actual executions, buyer/seller intent, discretionary behavior or price impact;
- convert a plan-capacity amount into a forecast of shares sold.

### 3.1 Regression evidence

Added research/test_phase433_item408_ixbrl_parser.py.

**12/12 offline tests passed locally**, covering:
- daylight and standard-time conversion;
- missing/conflicting acceptance timestamps;
- namespace aliases;
- hidden facts and text-block continuation;
- ix:exclude;
- preservation of both Item 408 dimensions;
- scaled numeric values;
- nil and unresolved contexts;
- no aggregation across multiple arrangements;
- zero tagged facts remaining unknown, not “no plans.”

The fixture is synthetic and designed to exercise the parser contract. It is not a byte-for-byte extract of ServiceNow's raw filing. No claim is made that the parser has passed an integration test on the actual 2023 iXBRL bytes.

## 4. Data-feasibility and PIT gate

| Gate | Current decision |
|---|---|
| Official source and reproducible filing URL | PASS |
| ECD fact/context parser scaffold | PASS — synthetic regression only |
| Real raw-file hash and integration fixture | PENDING |
| EDGAR acceptance clock interpretation | PASS — Eastern wall time, DST-aware |
| Exact public dissemination timestamp | NOT PROVIDED by SEC archive; use captured PDS/first-seen or conservative next-session rule |
| Historical depth | LIMITED — staggered 2023 start |
| Issuer/security universe coverage | UNMEASURED |
| Person-to-Form-4 owner identity | UNRESOLVED |
| Plan execution/status completeness | LIMITED |
| Alpha/OOS admission | NOT AUTHORIZED |

The raw filing integration remains blocked on obtaining the SEC filing bytes under a properly declared SEC User-Agent. The repository's SEC contact secret is still an outstanding prerequisite for automated SEC retrieval; no secret was read or changed in this phase. Do not retry bulk retrieval until the compliant contact is configured.

## 5. Next work

1. After a declared SEC User-Agent is configured, fetch the ServiceNow primary Inline XBRL document and SGML header, save immutable raw bytes and SHA-256, and run the parser against the actual document.
2. Census a stratified sample of Item 408 10-Q/10-K filings across non-SRC/SRC, fiscal-year and amendment regimes. Report issuer coverage, fact coverage, event density and missing-vs-false-vs-unknown states.
3. Validate ECD contexts against the narrative table and amendments; do not sum facts across TradingArrAxis.
4. Link named people to Form 4 owner CIKs only with auditable deterministic match grades.
5. Build a prospective raw filing/PDS receipt ledger before any return test.
6. Only after PIT, coverage and identity gates pass, preregister the planned-supply hypothesis and test incremental information versus frozen LTM/F80 with identical exposure/costs, chronological OOS, block bootstrap and LOO.

No alpha, return, OOS, LOO or holdout test was run. No new source or signal was admitted. No data were purchased.

## 6. Production and strategy protection

F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen. No changes to the holdout, universe, parameters, capital, exposure, execution rules or production workflows. No scheduled workflow was manually dispatched or duplicated.

## Sources

- SEC EDGAR PDS Technical Specification (March 2025), §2.1: acceptance time is specified as EST: https://www.sec.gov/info/edgar/specifications/pds_dissemination_spec.pdf
- SEC Webmaster FAQ, “How can I understand EDGAR Timestamps?” and “What is the lag time…”: https://www.sec.gov/about/webmaster-frequently-asked-questions
- 17 CFR §232.12–.13, Eastern Standard Time or Eastern Daylight Saving Time whichever is in effect; 5:30 p.m. filing-date rule: https://www.govinfo.gov/content/pkg/CFR-2025-title17-vol3/pdf/CFR-2025-title17-vol3-sec232-12.pdf
- ServiceNow, Inc. 2023 Q3 Form 10-Q: https://www.sec.gov/Archives/edgar/data/1373715/000137371523000419/now-20230930.htm
- ServiceNow, Inc. EDGAR SGML header: https://www.sec.gov/Archives/edgar/data/1373715/000137371523000419/0001373715-23-000419-index-headers.html
- SEC filing detail page (shows accepted time and filing date): https://www.sec.gov/Archives/edgar/data/1373715/000137371523000419/0001373715-23-000419-index.htm


## 2.3 Exact Rule 10b5-1 cooling-off calculation for this sample

A further check of SEC C&DI Question 120.29 confirms that the filing date of the relevant 10-Q/10-K does **not** count as the first business day. If the form is filed Monday, the SEC says trading may commence Thursday (absent intervening holidays). For the ServiceNow 10-Q filed Thursday 2023-10-26, the two business days following the filing date are Friday 2023-10-27 and Monday 2023-10-30; the first potential trading date after that limb expires is Tuesday 2023-10-31.

Assuming no later plan modification or other restriction, the sample's earliest dates under the amended Rule 10b5-1 cooling-off formula are therefore:

| Person | 90-day date | Two-business-day-after-10-Q date | First potential trading date |
|---|---:|---:|---:|
| Gina Mastantuono | 2023-10-26 | 2023-10-31 | 2023-10-31 |
| William R. McDermott | 2023-11-29 | 2023-10-31 | 2023-11-29 |
| Paul E. Chamberlain | 2023-11-19 (Sunday) | 2023-10-31 | 2023-11-20 (next regular session) |

This refines the simple 90-day markers above. Under the conservative next-session PIT rule, the filing information becomes usable no earlier than the 2023-10-26 session. That is five calendar days before Gina's earliest potential trading date, 34 days before McDermott's and 25 days before Chamberlain's next regular session. This is a regulatory timing comparison only: it does not establish that any plan actually traded, that the disclosed capacity was sold, or that the plan was unmodified.

Source added: SEC Exchange Act Rules C&DI 120.29, “Does the filing date count as the first business day?” https://www.sec.gov/rules-regulations/staff-guidance/corporation-finance-interpretations/exchange-act-rules
