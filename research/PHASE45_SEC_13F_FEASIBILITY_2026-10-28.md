# Phase 45 — SEC Form 13F historical feasibility gate

**Status:** PASS for structured accession/holdings linkage; NOT PASS for signal-ready point-in-time identity.  
**Updated:** 2026-11-24  
**Scope:** data feasibility only; no alpha test.

## Why 13F remains a candidate

The SEC publishes quarterly structured Form 13F datasets extracted from EDGAR XML. The SEC's current data-set documentation says the source spans May 2013 through the current period, is published quarterly, includes as-filed submissions and amendments, and can contain redundancies or discrepancies relative to original filings. Filings received after 5:30 p.m. Eastern on the last business day of a quarter are included in the next quarterly posting. See the [SEC Form 13F Data Sets specification](https://www.sec.gov/files/form_13f.pdf).

The signal hypothesis is slow institutional ownership change, not presumed informed trading. Report-quarter-end is not the availability date.

## Phase 47 result — accession and amendment audit

See the detailed [Phase 47 report](PHASE47_SEC_13F_PIT_ACCESSION_JOIN_AND_AMENDMENT_AUDIT_2026-11-24.md).

Two independent SEC samples passed the structured join:

| Sample | Submissions | INFOTABLE rows | Join rate | Managers with holdings | CUSIPs | FIGIs |
|---|---:|---:|---:|---:|---:|---:|
| 2018 Q1 | 6,570 | 1,879,731 | 100% | 4,683 | 25,816 | 0 |
| 2026 Jun–Aug | 11,852 | 3,830,274 | 100% | 8,872 | 34,951 | 22,519 |

No unmatched accessions, missing CUSIPs or negative-value rows were found. All six offline regression tests passed. The accession join is therefore structurally feasible in both a pre-FIGI and a current sample.

The submission-level filing lag (one observation per accession, not weighted by holding rows) has median 44 days and p75 45 days in 2018 Q1; median 41 days and p75 45 days in 2026 Jun–Aug. Amendments are materially later: median 78 days / p75 231 days for 2018 13F-HR/A, and median 135 days / p75 410 days for 2026 13F-HR/A. These are descriptive sample statistics, not a universal statutory-lag estimate.

### Amendment semantics

The SEC dataset has a separate COVERPAGE table. The cover-page ISAMENDMENT flag and AMENDMENTNO/AMENDMENTTYPE must be joined by ACCESSION_NUMBER; SUBMISSIONTYPE alone is not sufficient. Each sample contains one filing whose SUBMISSIONTYPE is 13F-HR while its cover page marks it as an amendment. The 2026 example, accession 0001376474-26-000479, is directly confirmed on the [SEC filing detail page](https://www.sec.gov/Archives/edgar/data/2051980/000137647426000479/0001376474-26-000479-index.htm) and [cover page](https://www.sec.gov/Archives/edgar/data/2051980/000137647426000479/xslForm13F_X02/primary_doc.xml): Form 13F-HR, amendment number 1, “adds new holdings entries.” The parser now treats the cover-page amendment flag as authoritative and records form-type discordance separately.

The samples contain 294 and 406 amendments, respectively, with no missing amendment numbers or types. Observed amendment types are RESTATEMENT and NEW HOLDINGS. A restatement supersedes the prior report; a new-holdings amendment supplements it. The next stage must implement this state machine in filing order, rather than treating each accession as an independent full portfolio.

### Point-in-time clock

SUBMISSION.tsv supplies FILING_DATE at date precision; it does not contain the exact EDGAR acceptance timestamp. The conservative eligibility rule is the first full regular session strictly after FILING_DATE. For a target-universe event study, the accession-level accepted timestamp should be retrieved from the original EDGAR filing detail where feasible. The SEC data-set publication date is not the filing's first public availability.

## Remaining gates

1. Build historical CUSIP/FIGI-to-F80 security identity, including identifier changes, corporate actions and date-effective membership. FIGI is absent in the 2018 sample, so CUSIP remains the common long-history key.
2. Build an as-of manager-period amendment state machine: RESTATEMENT replaces the prior state; NEW HOLDINGS adds only the reported incremental entries.
3. Resolve 13F-NT notice filers to the actual reporting manager(s) via OTHERMANAGER / OTHERMANAGER2; a notice is not a zero-holdings signal.
4. Retrieve exact accession acceptance times for the F80-relevant subset, or use the conservative next-session date rule.
5. Only then test holdings changes, new positions, concentration and exits against frozen F80/LTM with identical exposure, costs, chronological OOS, bootstrap and LOO.

**Disposition:** retain 13F as a low-frequency research candidate. The data is structurally joinable but delayed and not yet point-in-time security-identity complete. No signal, alpha, OOS or economic edge is established. No production or capital changes; F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen.
