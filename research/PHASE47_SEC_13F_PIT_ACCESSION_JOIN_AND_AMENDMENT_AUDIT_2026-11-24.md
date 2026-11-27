# Phase 47 — SEC 13F accession, amendment and conservative availability audit

**Status: PASS — representative structured join and amendment metadata validated.**  
**Audit cutoff:** 2026-11-24 23:13 UTC  
**Workflow:** [Run 45507919882](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45507919882)  
**Artifact:** [14974051376](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45507919882/artifacts/14974051376)  
**Branch:** `phase47-sec-13f-pit-accession-join-audit`

## Executive result

The SEC's 13F structured datasets are feasible for accession-level manager/holdings reconstruction across both a pre-FIGI historical sample and a current sample:

| Metric | 2018 Q1 | 2026 Jun–Aug |
|---|---:|---:|
| SUBMISSION rows / unique accessions | 6,570 / 6,570 | 11,852 / 11,852 |
| INFOTABLE rows | 1,879,731 | 3,830,274 |
| INFOTABLE → SUBMISSION join rate | 100% | 100% |
| Unique manager CIKs, all submissions | 6,239 | 10,807 |
| Unique manager CIKs with holdings | 4,683 | 8,872 |
| Unique CUSIPs | 25,816 | 34,951 |
| Unique FIGIs | 0 | 22,519 |
| Missing CUSIP rows | 0 | 0 |
| Missing accession joins | 0 | 0 |
| Negative-value rows | 0 | 0 |
| Manager-period groups with multiple submissions | 163 | 189 |

The all-submission manager count includes 13F-NT notice filers. Those notices do not contain the manager's holdings; the separate count of managers with holdings is the more relevant coverage measure for position features.

## Submission types and amendment state

| Submission type | 2018 Q1 | 2026 Jun–Aug |
|---|---:|---:|
| 13F-HR | 4,713 | 9,501 |
| 13F-HR/A | 285 | 399 |
| 13F-NT | 1,564 | 1,946 |
| 13F-NT/A | 8 | 6 |

The cover-page join adds one amendment in each sample whose SUBMISSIONTYPE is 13F-HR but whose cover page has ISAMENDMENT=Y, AMENDMENTNO=1 and AMENDMENTTYPE populated. This is not automatically a data error. The 2026 accession 0001376474-26-000479 is independently verified on EDGAR: the filing detail lists Form 13F-HR and accepted time 2026-07-13 13:41:20; its cover page checks “Amendment,” number 1, and “adds new holdings entries.” Therefore, **COVERPAGE.ISAMENDMENT plus amendment number/type is the authoritative amendment state**, while SUBMISSIONTYPE is retained as a separate form classification.

| Amendment metric | 2018 Q1 | 2026 Jun–Aug |
|---|---:|---:|
| Amendments including cover-page flagged 13F-HR | 294 | 406 |
| RESTATEMENT | 189 | 262 |
| NEW HOLDINGS | 105 | 144 |
| Missing amendment numbers | 0 | 0 |
| Missing amendment types | 0 | 0 |
| Form-type / cover-page amendment discordance | 1 | 1 |
| Explicit amendment-flag contradictions | 0 | 0 |

The SEC data-set specification describes the data as filed, includes amendments, and warns of possible redundancies/inconsistencies. It also distinguishes the two amendment treatments: a restatement supersedes the prior report; a new-holdings amendment supplements it. The code records these categories rather than flattening all amendments into full replacement portfolios.

## Filing lag — submission-weighted, not holding-row-weighted

The previous Phase 47 prototype computed filing lag inside the INFOTABLE loop, which overweighted large portfolios. This version computes exactly one lag per accession.

| Submission type | 2018 median / p75 days | 2026 median / p75 days |
|---|---:|---:|
| 13F-HR | 43 / 45 | 38 / 45 |
| 13F-HR/A | 78 / 231 | 135 / 410 |
| 13F-NT | 44 / 45 | 44 / 45 |
| 13F-NT/A | 73 / 321 | 50 / 50 |
| All submissions | 44 / 45 | 41 / 45 |

The large maximum lags (1,125 days in 2018 and 9,101 days in 2026) reflect very late filings/amendments relative to the report period. They are retained, not winsorized away. The typical first report arrives near the 45-day filing deadline; amendments can be substantially later. This makes 13F a slow ownership-change feature, not an intraday flow source.

## Availability and no-lookahead contract

- SUBMISSION.tsv provides FILING_DATE in DD-MON-YYYY format, at date precision. It does **not** include the exact EDGAR acceptance timestamp.
- For a conservative daily backtest, the earliest eligible session is the first full regular session strictly after FILING_DATE. Do not use PERIOD_OF_REPORT as the signal date.
- The SEC data set is published quarterly. The SEC states that submissions filed after 5:30 p.m. Eastern on the last business day of a quarter are included in the next quarterly posting. The quarterly data-set posting date is not the original filing's first public availability.
- The original EDGAR filing detail can provide an exact accepted timestamp. The 2026 validation example reports 2026-07-13 13:41:20; accession-level retrieval should be done for the F80-relevant subset before signal admission.
- The SEC warns that the structured data may contain redundancies, inconsistencies or extraction errors; original filings remain the authority for adjudication.

## Operational validation

- GitHub Actions [Run 45507919882](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45507919882) succeeded.
- Six offline regression tests passed.
- Both SEC ZIP datasets downloaded and parsed using the shared project contact fallback. The SEC_USER_AGENT repository secret environment variable was empty; no secret change was needed.
- ZIP SHA-256 hashes and byte sizes are included in the artifact.
- No production collector, F80 universe, portfolio, parameters, exposure, costs or capital were changed.

## Decision and next gate

**PASS** for accession-level SUBMISSION/COVERPAGE/INFOTABLE joins, amendment metadata completeness, and conservative date-only availability metadata in these two samples.

**NOT PASS** for a signal-ready point-in-time institutional holdings panel. Remaining work:

1. Historical CUSIP/FIGI-to-F80 crosswalk and date-effective security identity. FIGI is absent in 2018; CUSIP is the common long-history key.
2. As-of manager-period amendment state machine. RESTATEMENT replaces prior state; NEW HOLDINGS supplements it.
3. Resolve 13F-NT notices through OTHERMANAGER / OTHERMANAGER2; do not interpret notices as zero positions.
4. Retrieve exact EDGAR acceptance times for F80-relevant accessions or enforce the next-full-session rule.
5. Test incremental information only after these gates, versus frozen F80/LTM, with identical exposure/costs, chronological OOS, bootstrap and LOO.

No predictive signal, return edge, OOS, bootstrap or LOO result is established. `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen.
