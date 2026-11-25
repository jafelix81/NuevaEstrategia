# Phase 611 — SEC 13F Stratified Acceptance-Timestamp Coverage Audit
**Date:** 2026-11-25  
**Status:** PASS — bounded timestamp-feasibility sample; 12/12 offline regression tests passed  
**PR:** [#228](https://github.com/jafelix81/NuevaEstrategia/pull/228)  
**Workflow:** [Run 45535351139](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45535351139)  
**Artifact:** [14986657502](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45535351139/artifacts/14986657502)

## Objective

Expand Phase 610's six-filing pilot into a deterministic, stratified audit of the SEC filing-detail page's timestamp and identity fields. The sample spans submission form, cover-page report type, and filing-date bins in two already-audited public datasets.

## Result

| Dataset | 13F accessions with cover page | Sample | Page checks |
|---|---:|---:|---:|
| 2018 Q1 | 6,570 | 24 | 24/24 PASS |
| 2026 Jun–Aug | 11,852 | 24 | 24/24 PASS |
| **Total** | **18,422** | **48** | **48/48 PASS** |

Each dataset sample covers six observed form/report-type strata, with up to four deterministic selections per stratum across filing-date bins. This is a feasibility sample, not a random sample and not an estimate of population error rates.

Checks passed for:
- SEC accession number on the filing-detail page;
- canonical archive path using the filer CIK from the SEC SUBMISSION table;
- submission form type;
- filing date after normalization of the SEC TSV date format;
- period of report;
- presence and parsing of the Accepted timestamp;
- reconciliation of Accepted time to the legal filing date under the SEC filing-date rule.

The SEC filing-detail page did not expose a consistently parseable filer-CIK text label across older layouts. The audit therefore uses the filer CIK from the official SUBMISSION table, verifies that it is the CIK used in the archive path, and independently matches the accession displayed by the filing-detail page. No issuer/owner identity is inferred from the accession prefix.

## Timestamp and filing-date findings

| Clock classification | 2018 Q1 sample | 2026 Jun–Aug sample | Total |
|---|---:|---:|---:|
| Pre-market weekday (<09:30 ET) | 3 | 3 | 6 |
| Regular-session clock (09:30–15:59:59 ET) | 17 | 15 | 32 |
| After close (>=16:00 ET) | 4 | 6 | 10 |
| Weekend acceptance | 0 | 0 | 0 |

Legal filing-date reconciliation:

| Reconciliation | 2018 Q1 | 2026 Jun–Aug | Total |
|---|---:|---:|---:|
| Same calendar/business day | 22 | 22 | 44 |
| Accepted after 17:30 ET; deemed filed next SEC business day | 2 | 2 | 4 |
| Unresolved mismatch | 0 | 0 | 0 |

### Important methodological correction

Four sampled filings were accepted after 17:30 Eastern on one calendar date, while the SEC index displayed the next SEC business day as the filing date. This is not a data error.

Under **17 CFR §232.13(a)(2)**, most direct-transmission filings received after 5:30 p.m. Eastern are deemed filed on the next business day. The enumerated 10 p.m. exceptions include specified forms such as Forms 3/4/5, Form 144, and Schedules 13D/13G; Form 13F is not among those exceptions. SEC submissions are not accepted on Saturdays, Sundays, or federal holidays under **17 CFR §232.12**.

The audit now reconciles the two clocks rather than requiring their calendar dates to be identical. The federal-holiday/next-business-day logic is covered by offline regression tests, including Friday rollover, Christmas rollover, before-cutoff mismatch, and non-business-day rejection.

Official references:
- [17 CFR §232.13 — Date of filing; adjustment of filing date (GovInfo)](https://www.govinfo.gov/content/pkg/CFR-2025-title17-vol3/pdf/CFR-2025-title17-vol3-sec232-13.pdf)
- [17 CFR Part 232 — filing days and §232.13 (eCFR/GovInfo text)](https://www.govinfo.gov/content/pkg/CFR-2024-title17-vol3/xhtml/CFR-2024-title17-vol3-part232.html)

## Implementation and controls

- Exact Accepted time retained as Eastern and converted to UTC using `America/New_York`, preserving EST/EDT transitions.
- SEC dataset dates normalized from both ISO and `DD-MMM-YYYY` formats.
- Filer CIK is sourced from the SEC SUBMISSION table, not inferred from the accession prefix.
- Deterministic sample selection spans form type, report type and filing-date bins.
- SEC page requests are rate-limited; HTML is hashed and not committed to the repository.
- The live SEC audit is gated behind an explicit workflow dispatch input for subsequent use.
- The Actions secret `SEC_USER_AGENT` was not present in the run environment; the existing shared project contact fallback was used successfully. No user action is required.

## Limitations — not a signal or backtest

- Only 2018 Q1 and 2026 Jun–Aug were sampled; this is not full-quarter or all-history timestamp coverage.
- The stratified sample is deterministic, not random; it cannot support a population error-rate estimate.
- Historical collector first-seen timestamps are unavailable. EDGAR Accepted is the submission-acceptance timestamp, not proof of the exact moment the document became observable to every data consumer.
- No XNYS market-session calendar or first fully tradable daily bar has yet been joined.
- No complete effective-dated CUSIP/FIGI-to-F80 security master exists yet.
- `signal_eligible=false`; no alpha, OOS, return, risk, bootstrap or leave-one-out test was run.

## Next gate

1. Expand timestamp validation across additional historical 13F quarters and schema eras.
2. Preserve both EDGAR Accepted time and the prospective collector's first-seen time; use the later verified knowledge time.
3. Validate the first fully completed XNYS daily bar after that knowledge time.
4. Complete the historical CUSIP/FIGI-to-security crosswalk and universe-coverage audit.
5. Only then construct point-in-time 13F ownership/persistence features and test incremental value versus frozen F80/LTM under chronological OOS, identical exposure and costs.

**Baseline:** `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen. No production, universe, capital, exposure or parameter changes. Options/data-purchase budget remains USD 0.


## Operational erratum — live workflow trigger (2026-11-25)

A post-run review of the workflow YAML and Actions job logs found that the original live-job condition also allowed every branch push to run the bounded SEC download. This contradicted the intended dispatch-only control described above. Run [45535351139](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45535351139) was a `push` event and did execute the live SEC sample; the subsequent PR run [45535594622](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45535594622) correctly skipped the live job.

**Correction:** the live job now runs only when `github.event_name == 'workflow_dispatch'` and `run_live_audit == true`. Push and pull-request events retain offline regression only. A regression test asserts this workflow contract. The already completed 48-page sample remains valid; no new live SEC run is initiated by this correction.
