# Phase 318 — N-PORT next-EDGAR-business-day adjudication

**Date:** 2026-11-12 UTC  
**Status:** PASS — offline re-adjudication of all 280 immutable Phase 316 filings through the Phase 317 artifact.  
**GitHub Actions:** [run 43169018518](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43169018518) — success, 10/10 regression tests.  
**Artifact:** [13921710493](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43169018518/artifacts/13921710493)  
**Artifact ZIP SHA-256:** `5b3dadc58e7cc9d657c670dd883bec0dd429ef582376a1491233b79114989e5b`

## 1. Result

- 280/280 accession rows re-read; all accessions unique and all master-index filing dates match the Phase 317 FILED AS OF DATE.
- 15 filings have ACCEPTANCE-DATETIME at or after 17:30 ET.
- 14 have a later master-index filing date; all 14 equal the next EDGAR business day after the acceptance calendar date.
- The 14 date shifts comprise 12 one-calendar-day shifts and two Friday-to-Monday three-calendar-day shifts.
- One filing was accepted after 17:30 ET but retains the same filed date. It remains unresolved; this is not classified as a rule violation.

## 2. Critical clock distinction

17 CFR 232.13(a)(2) keys the 17:30 cutoff to when direct transmission **commences**, not to ACCEPTANCE-DATETIME. The SEC's filing-status guidance says most filings that begin transmission after 17:30 receive the next business day's filing date and are not disseminated until that next business day. Its listed 10 p.m. exceptions do not include N-PORT.

Therefore the 14 rows are **consistent with** next-business-day treatment, but acceptance time does not prove transmission start. The one same-date/after-17:30 row could have commenced transmission before the cutoff and been accepted later; its transmission start is not in this sample.

The offline calendar implements EDGAR's Monday–Friday operating schedule excluding observed U.S. federal holidays. Good Friday is not treated as a federal holiday. Regression tests cover weekend, Thanksgiving, Juneteenth, observed New Year's Day and Good Friday.

## 3. Point-in-time decision

- Keep official FILED AS OF DATE / master-index filing date as a **date-level public filing anchor**, not an exact first-public timestamp.
- For any later event study, allow use only from the **first full XNYS session strictly after the filed date**.
- Do not backdate to REPORT_DATE or use ACCEPTANCE-DATETIME alone as the first-public clock.
- N-PORT remains delayed holdings snapshots, not trade flow. Amendments are state corrections, not new trades.
- The 280-filing sample is deterministic hash-ranked QA, not a probability sample or prevalence estimate.

## 4. Implications for the N-PORT hypothesis

Phase 316 sampled five distinct registrants in each of 56 quarter/form strata across 2019Q4–2026Q3. The 194 sign-concordant reported short rows occurred in only two filings, with 173 unique CUSIPs, 174 unique ISINs and zero reported tickers. This is not a prevalence estimate. The rows are reported holdings, not executions; a historical, effective-dated security crosswalk and a defensible public-availability vintage remain mandatory before an event study.

N-PORT-P report-date-to-filing-date lag was median 57 days (n=140). N-PORT-P/A was median 119 days, with 85/140 at least 90 days and 49/140 at least 180 days. These are report-date-to-filing-date lags, **not** amendment delay from the original parent.

## 5. Sources and limitations

- SEC EDGAR filing-status guidance: https://www.sec.gov/submit-filings/filer-support-resources/how-do-i-guides/determine-status-my-filing
- 17 CFR 232.13: https://www.ecfr.gov/current/title-17/chapter-II/part-232/section-232.13
- No transmission-start timestamp or exact first-public-receipt timestamp is available in the sampled submission headers.
- No return, alpha, bootstrap, LOO, chronological OOS or holdout test was run.
- F80, production, universe, capital and parameters remain frozen.
- No vendor contact, data purchase or email was made.

## 6. Source and output integrity

- Source Phase 317 run: [43167767387](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43167767387), artifact [13920996169](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43167767387/artifacts/13920996169).
- Phase 318 output artifact ZIP SHA-256: `5b3dadc58e7cc9d657c670dd883bec0dd429ef582376a1491233b79114989e5b`.
- CSV SHA-256: `685ff130acf5057f6b14e662af7eb1e42eec15e9c285705e526057e5ebc0e598`.
- JSON SHA-256: `7e072b03d297bfe24d2b59b6976be3cc464fd123b0b51df8d0cada6047effa56`.

## Outputs

- `nport_edgar_business_day_adjudication.csv` (artifact)
- `phase318_nport_next_business_day_result.json`
- `PHASE318_NPORT_NEXT_BUSINESS_DAY_ADJUDICATION_2026-11-12.md`
