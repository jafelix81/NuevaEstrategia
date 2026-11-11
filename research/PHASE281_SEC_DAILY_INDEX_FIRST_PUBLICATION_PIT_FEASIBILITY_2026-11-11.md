# Phase 281 — SEC daily-index first-publication-date reconstruction feasibility

**Date:** 2026-11-11 UTC  
**Status:** `CONDITIONAL_DAILY_PIT_ROUTE_IDENTIFIED_NO_RAW_DATA_OR_ALPHA`  
**Control:** `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen.  
**Scope:** read-only review of SEC EDGAR dissemination documentation and public directory inventories. No SEC archive/index bytes were downloaded and no automated SEC request was sent.

## Executive finding

Phase 279 identified the SEC Insider Transactions quarterly bulk files as a 2006Q1–2026Q3 transaction-history source, but the flattened SUBMISSION table has only date-level filing metadata and does not contain the public-availability clock.

This phase identifies a potentially workable daily-granularity PIT bridge: **join each bulk-dataset ACCESSION_NUMBER to the accession path in the SEC's historical daily `form.YYYYMMDD.idx` files, and use the earliest daily-index date as the conservative public-dissemination date.** The SEC documents daily-index archives from 1994Q3 through the present, says the indexes list form type, CIK, filing date and filing path, and explains that subsequent-business-day post-acceptance corrections do not rewrite prior daily indexes. Full and quarterly indexes, in contrast, are rebuilt weekly and incorporate those later corrections.

This is materially better than using `FILING_DATE` or current company submissions as the event clock. It is **not yet strict PIT admission**: the exact first-public timestamp is not published, same-day corrections can be incorporated before the nightly index is built, index-to-accession parsing has not been validated against raw files, and owner/security identity remains unresolved.

## 1. Official dissemination semantics

### 1.1 Daily indexes are historical daily snapshots

The SEC's *Accessing EDGAR Data* page states:
- daily-index files are available from 1994Q3 through the present;
- daily indexes are organized by year and quarter;
- company, form and master indexes contain the same filing information sorted differently;
- each filing entry includes company name, form type, CIK, date filed and the file path;
- indexes incorporating the current business day's filings are updated nightly, starting around 10 p.m. ET and usually completing within a few hours;
- some submissions after 5:30 p.m. ET (or after 10 p.m. for Ownership Forms 3/4/5) are disseminated on the next business day and appear in the following business day's index.

Most importantly for historical reconstruction, the SEC says a post-acceptance correction/removal processed on a later business day is **not reflected in any previous daily, feed or oldload index**. Full and quarterly indexes are rebuilt weekly and do incorporate those later PAC changes. Therefore the daily index—not a current company-submissions feed, full index or quarterly index—is the correct candidate for reconstructing what survived in the daily public index at that historical date.

A same-business-day PAC can be incorporated before that day's nightly index is generated. The daily index is consequently a conservative nightly snapshot, not a complete tape of every transient intraday publication. Missing same-day-removed filings would reduce recall; they must not be imputed.

### 1.2 Acceptance time is not first-public time

The SEC Webmaster FAQ confirms that the complete submission header can contain `ACCEPTANCE-DATETIME`, but explicitly says there is no timestamp identifying when filing content first became available on sec.gov. The SEC says availability is often 1–3 minutes after the EDGAR timestamp, but the lag can increase and is not guaranteed.

Accordingly:
- acceptance time is useful for chronology and reconciliation, but is not the observed first-public timestamp;
- the daily-index filename/date is the candidate public-dissemination day;
- for a daily end-of-day strategy, the conservative first execution point should be **the close of the next full XNYS session after the daily-index date**, not the filing date, acceptance time or same-day close;
- early closes, holidays and weekends must be resolved with the official XNYS calendar.

This is deliberately conservative and may sacrifice one session of potential signal value in exchange for a defensible daily knowledge boundary.

### 1.3 Oldloads is a possible content-recovery source, not yet an immutable-vintage guarantee

The SEC describes `/Archives/edgar/Oldloads/` as daily concatenated archives of public filing submissions, complete with filing headers. The public directory inventory lists years 1996–2026. The inspected 2006Q1 directory contains daily gzip files with listed sizes from roughly 64 MB to 424 MB; 2026Q3 files are roughly 0.7–2.7 GB.

These archives may help recover original filing bodies when an individual accession path is no longer accessible, but their PAC/correction semantics and practical targeted-extraction cost have not been validated. Do not download every oldload archive as a prerequisite. First use daily indexes to identify only relevant accessions; test individual filing retrieval and a small targeted oldload recovery case.

## 2. Cross-check against the Phase 279 bulk dataset

The SEC Insider Transactions data sets are published quarterly, contain as-filed Forms 3/4/5 and amendments, and the SEC readme says filings after 5:30 p.m. ET on the last business day of a quarter roll into the next quarterly posting. The quarterly archive is therefore a transaction-content delivery mechanism, not the public-availability clock.

Proposed join:
1. Preserve each quarterly archive and its SHA-256; parse `SUBMISSION.ACCESSION_NUMBER` and retain every Form 4 and Form 4/A as a distinct accession/vintage.
2. Parse the accession from the filing path in each daily `form.YYYYMMDD.idx` file. Preserve the original index file, its date, retrieval timestamp and SHA-256.
3. Build an accession-to-all-index-sightings ledger. The earliest verified daily-index date is the conservative daily dissemination date. Do not overwrite later sightings or collapse amendments.
4. Require a unique, valid accession join. Missing index match, malformed path, conflicting accession/date mapping or unrecognized form type means `UNKNOWN/EXCLUDE`, not a fallback to `FILING_DATE`.
5. Reconcile a stratified subset to the original submission header's `ACCEPTANCE-DATETIME` and filing body. Keep acceptance time as a diagnostic, not the public clock.
6. Execute no earlier than the next full XNYS session close after the first daily-index date.

The daily `form` index is preferable to downloading all daily `Oldloads` files: inspected 2006Q1 `form.*.idx` files are generally sub-megabyte to a few megabytes, while the corresponding Oldloads gzip archives are tens to hundreds of megabytes even in 2006 and much larger by 2026.

## 3. Observed directory coverage

| Inventory | Direct observation | Interpretation |
|---|---|---|
| SEC daily-index root | Year directories 1994–2026 and quarter directories | Long historical availability is documented and directory-visible |
| 2006Q1 daily-index | `company.*.idx`, `form.*.idx`, `master.*.idx` daily files; form files listed at roughly 0.4–3.2 MB | The earliest Phase 279 archive era has a corresponding daily-index directory |
| 2026Q3 daily-index | Daily `form.*.idx` files from 2026-07-01 through 2026-09-30; roughly 0.6–2.1 MB in the inspected listing | The latest Phase 279 archive era also has a corresponding daily-index directory |
| Oldloads root | Year directories 1996–2026 | Potential historical body-recovery path; not yet tested |
| 2006Q1 / 2026Q3 Oldloads | Daily gzip files visible; very large relative to index files | Avoid full-year or full-history Oldloads downloads |

The directory listing's server `Last Modified` field is not treated as a per-filing publication timestamp. The authoritative proposed availability field is the date encoded by the daily-index file containing the accession.

## 4. Required sample gate before scaling

Use the six Phase 279 archive strata (2006Q1, 2012Q1, 2023Q1, 2023Q2, 2025Q3 and 2026Q3). For each:
- validate the archive-specific schema and compound keys, including the AFF10B5ONE boundary;
- select a deterministic sample of Form 4 and Form 4/A accessions, including after-hours filings, weekends/holidays, amendments and any known PAC examples;
- fetch only the relevant daily `form` index files and verify accession/path parsing;
- verify every sampled accession's earliest index date and compare it with `FILING_DATE` and header acceptance time;
- measure unmatched, duplicate, multi-date and missing-content rates; preserve same-day PAC exclusions as a separate coverage diagnostic;
- reconcile original XML transaction rows, footnotes and joint/group owners; exclude any transaction-owner attribution that cannot be linked unambiguously;
- resolve issuer security class and effective-dated ticker/listing identity, including inactive and delisted names, before any return join.

No return test is allowed until these source, PIT, owner and security-identity gates pass. Any subsequent economic test must use a new untouched prospective holdout, identical eligible names/exposure/turnover/costs against frozen LTM/F80, chronological walk-forward, date/issuer/owner-clustered bootstrap, leave-one-issuer/owner-out and multiplicity controls.

## 5. Decision and blockers

| Gate | Phase 281 disposition |
|---|---|
| Historical daily-index directory exists | PASS — public directory inventory |
| Daily index has form/CIK/date/path metadata | PASS — SEC documentation |
| Prior daily indexes survive later-business-day PAC changes | PASS — SEC documentation |
| Daily accession-to-Phase 279 join | NOT RUN — no raw index/archive bytes |
| Exact first-public timestamp | NOT AVAILABLE from SEC documentation |
| Daily next-session-close PIT contract | CONDITIONAL CANDIDATE — requires raw join validation |
| Oldloads PAC/body-recovery behavior | NOT TESTED |
| Owner-level transaction attribution | NOT ESTABLISHED |
| Effective-dated security/class and inactive-universe coverage | NOT ESTABLISHED |
| Strict PIT admission / alpha | NOT ADMITTED |

Automated SEC retrieval still requires a declared User-Agent under the SEC fair-access policy. The authorized repository secret `SEC_CONTACT_EMAIL` remains absent; no email was guessed, no automated request was sent and no SEC bytes were downloaded. The sample gate should use a moderate request rate and only the needed daily index files/accessions once the authorized contact value is configured.

**Decision:** upgrade Form 4 from “no viable public-availability clock identified” to **“conditional daily-PIT reconstruction route identified.”** Do not call it strict PIT, do not run returns and do not promote the Form 4 hypothesis. The route can potentially recover a conservative daily public-knowledge date over the same 2006–2026 history while avoiding the enormous cost of downloading all Oldloads archives.

## Sources

- SEC, [Accessing EDGAR Data](https://www.sec.gov/search-filings/edgar-search-assistance/accessing-edgar-data) — daily-index coverage, index contents, nightly dissemination, after-hours handling, PAC treatment, Oldloads description and fair-access requirements.
- SEC, [Webmaster Frequently Asked Questions](https://www.sec.gov/about/webmaster-frequently-asked-questions) — acceptance timestamp, no first-public timestamp and non-guaranteed 1–3 minute availability lag.
- SEC, [Insider Transactions Data Sets readme](https://www.sec.gov/files/insider_transactions_readme.pdf) — quarterly as-filed archive cadence, quarter-end cutoff and accession/table keys.
- SEC, [daily-index directory](https://www.sec.gov/Archives/edgar/daily-index/) and [Oldloads directory](https://www.sec.gov/Archives/edgar/Oldloads/) — observed public directory inventory.

No raw data, filing bytes, returns, alpha, bootstrap/LOO, chronological OOS or holdout were used. No vendor contact, purchase, production change, universe/capital change or PR merge occurred.
