# Phase 317 — N-PORT filing-clock and amendment-lag adjudication

**Status:** PASS — offline adjudication of the repeated Phase 316 raw sample.

## Sample and repeatability

- 280 accessions across 28 quarters and 56 quarter/form strata; five distinct registrants per stratum.
- 212 distinct registrant CIKs; 140 NPORT-P and 140 NPORT-P/A filings.
- Phase 316 independent repeat: 280/280 raw accession SHA-256 hashes identical.
- Phase 310 purposive positive controls: 5; overlap with the Phase 316 expansion sample: 0.
- This is a deterministic hash-ranked QA sample, not a probability sample or prevalence estimate.

## Filing clock: acceptance time is not the public clock

- FILED AS OF DATE equals the SEC master-index filing date in 280/280 filings.
- Acceptance calendar date equals filed date in 266/280.
- 14 filings have acceptance date before the official filed date; all 14 have acceptance time at or after 17:30 ET. Calendar-day shifts: {'1': 12, '3': 2}.
- 1 additional filing was accepted after 17:30 ET but retains the same filed date; its transmission-start/public-dissemination time is unresolved.
- The SEC's December 2024 EDGAR Filer Manual says ordinary filings received after 5:30 p.m. ET normally receive the next business day's filing date and are not disseminated until that next business day. Its enumerated 10 p.m. exceptions include Forms 3/4/5, 144 and Schedules 13D/G; N-PORT is not listed.
- Source: [SEC EDGAR Filer Manual, Version 72, December 2024](https://www.sec.gov/files/edgar/filermanual/archive/efmvol2-v72.pdf), section 3.2, filing-date guidance; see also 17 CFR 232.13.
- The acceptance timestamp is not a verified first-public-receipt timestamp. Use the official FILED AS OF DATE / master-index filing date as the date-level public anchor, then allow use only from the first full XNYS session strictly after that date. Do not use REPORT_DATE or ACCEPTANCE-DATETIME alone as the knowledge clock.

## Report-to-filing lag

- NPORT-P: n=140, median 57.0 days, range 37–62.
- NPORT-P/A: n=140, median 119.0 days, range 49–1114; 85 of 140 at least 90 days, 49 at least 180 days, 16 at least 365 days, and 5 at least 730 days.
- These are report-date-to-filing-date lags, not the elapsed time from the original filing to an amendment. Amendments remain state corrections, not new trading events.

## Short-holding coverage

- 194 sign-concordant short rows in 2 NPORT-P filings.
- 173 unique CUSIPs and 174 unique ISINs; zero ticker values.
- CUSIP present on 193/194 rows; ISIN present on 194/194; ticker present on 0/194.
- Both filings are new registrants in this expansion sample, not the Phase 310 purposive controls. These rows are reported holdings snapshots, not trades or short-sale executions.

## Legacy Phase 27O result

- The old zero-share/zero-rank output is quarantined as an implementation defect, not a negative alpha result: the legacy code read UNITS while the SEC flattened schema field is UNIT. Phase 247 already confirmed this. Do not use Phase 27O's zero ranking as evidence against N-PORT.

## Decision

- Raw identity and parser coverage are reproducible, but the 194 short rows have no ticker values and require an effective-dated CUSIP/ISIN crosswalk.
- OpenFIGI's current mapping snapshot is not a standalone historical PIT security master; the prior audit left 19.7% of sampled CUSIPs unmatched and supplied no effective dates.
- Databento remains a potential commercial security-master route, but no purchase or vendor contact is authorized or performed.
- No return, alpha, bootstrap, LOO, chronological OOS or holdout test was run. F80 and production remain frozen.

## Execution records

- [Phase 316 run A](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43166221052) · [artifact 13919534524](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43166221052/artifacts/13919534524)
- [Phase 316 independent repeat](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43166231154) · [artifact 13920352803](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43166231154/artifacts/13920352803)
- [Phase 317 adjudication run](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43167767387) · [artifact 13920996169](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43167767387/artifacts/13920996169)

## Outputs

- phase317_nport_filing_clock_adjudication_result.json
- nport_clock_adjudication_rows.csv
- nport_acceptance_filed_date_mismatches.csv
