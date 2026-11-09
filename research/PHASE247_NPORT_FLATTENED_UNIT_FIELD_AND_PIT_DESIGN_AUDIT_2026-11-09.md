# Phase 247 — SEC N-PORT flattened UNIT field defect and PIT design audit

**Audit date:** 2026-11-09  
**Status:** LEGACY_NPORT_FLOW_PILOT_SCHEMA_DEFECT_CONFIRMED_NO_ALPHA  
**Control:** F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen.  
**Scope:** Audit of the existing Phase 27K–27O N-PORT line against the current SEC Form N-PORT data-set schema and filing rules. No dataset ZIP was downloaded, no vendor was contacted, no return test was run, and no production or universe change was made.

## Executive finding

The legacy Phase 27O workflow calls Nueva_Estrategia_Fase27N_SEC_NPORT_PIT_FlowPilot.py, which reads the SEC flattened FUND_REPORTED_HOLDING TSV table and then looks up h.get("UNITS"). The SEC N-PORT Data Sets readme defines the flattened column as UNIT (singular), alongside BALANCE. The raw XML element is <units> (plural), but that XML tag spelling is not the column name in the SEC flattened TSV.

The legacy code therefore reads an empty value for every official flattened-table row. Its condition units == "NS" never succeeds, so the share-balance accumulator remains zero. The downstream ranker requires positive prior and current share balances; it cannot form valid share-growth candidates from the documented SEC TSV schema.

**This is a confirmed implementation defect, not evidence for or against the economic hypothesis.** The Phase 27O branch remains quarantined. No Phase 27N/27O return output is accepted as a valid share-flow test until the parser is corrected and independently validated.

## 1. Repository audit and existing N-PORT work

The repository already contains a substantial separate Phase 27 N-PORT line; Phase 247 does not restart source feasibility.

- Phase 27K attempted an institutional-flow OOS screen. Its output had eight snapshots and seven transitions but zero tickers because it filtered on ticker identifiers only.
- Phase 27L found 267–324 distinct tickers from the frozen 335-name universe across eight annual snapshots. These are distinct ticker coverage counts, not a complete security-level coverage census.
- The Phase 27N plan pre-registered a 75-calendar-day knowledge cutoff and share-growth ranking.
- Phase 27O was intended to correct the earlier share-flow pilot. Its workflow calls the Phase 27N script on the separate phase27o-nport-pit-flow-correction branch. The code still reads UNITS, so the flattened-schema defect remains.
- The Phase 27O workflow file exists, but its execution output was not independently verified in this audit. No run or artifact is represented as passing.

The earlier Phase 27M plan reported same-snapshot candidate CUSIP links and ticker diagnostics. Those are candidate mappings, not a fully effective-dated security master. They do not remove the need for historical identity validation.

## 2. Official SEC data availability

The SEC Form N-PORT Data Sets page currently lists coverage from October 2019 through September 2026 and 28 quarterly archives (2019 Q4 through 2026 Q3). The listed ZIPs range from approximately 228.89 MB to 690.83 MB. The SEC updates the compiled data sets quarterly; they contain only publicly disseminated filing information.

The official readme says:
- The flat-file data is extracted from the submitted N-PORT XML.
- The data are taken as filed.
- Amendments are included.
- The data can contain redundancies, inconsistencies and discrepancies.
- The compiled files do not include all filing metadata and are not a substitute for original filings.
- SUBMISSION carries ACCESSION_NUMBER, FILING_DATE, SUB_TYPE and REPORT_DATE.
- FUND_REPORTED_HOLDING carries ACCESSION_NUMBER, HOLDING_ID, ISSUER_CUSIP, BALANCE, UNIT, CURRENCY_VALUE, PERCENTAGE, PAYOFF_PROFILE and ASSET_CAT.
- IDENTIFIERS carries ticker and ISIN identifiers linked by holding ID.

The raw SEC XML uses the lowercase <units> element. The SEC's flattened table renames this to the singular column UNIT. The Phase 27O script conflated the two schemas.

## 3. Public disclosure cadence and strict PIT

As of 2026-11-09, the current N-PORT regime still applies:
- Reports cover monthly portfolio holdings, but are filed quarterly.
- Only the third month of each fund's fiscal quarter is publicly available upon filing.
- First- and second-month reports that identify a fund/adviser remain nonpublic.
- Reports are due no later than 60 days after the end of the fiscal quarter.
- A fund may file an amendment to a prior report at any time.

The SEC's 2024 amendments would move to monthly filing and make monthly reports public after a 60-day delay, but the SEC delayed compliance to November 17, 2027 for large fund groups and May 18, 2028 for smaller groups. Those future rules must not be back-applied to the 2019–2026 history.

The quarterly compiled ZIP is a discovery and coverage resource, not a real-time PIT feed. It is updated quarterly and includes amendments. A strict historical panel must:
1. Preserve each accession and exact original bytes/hash.
2. Retain every NPORT-P and NPORT-P/A accession as a separate vintage.
3. Join accession-level SEC filing index metadata for accepted time and filing date; the flat SUBMISSION table does not contain the full acceptance timestamp.
4. Use actual public dissemination/receipt time, not REPORT_DATE, as the knowledge time.
5. Treat an amendment as a correction to the previously known state, not as fresh portfolio trading.
6. Use the first regular trading session after actual public dissemination for the earliest strategy use.

A public EDGAR example, accession 0001145549-25-044643, reports period end 2025-04-30 and an acceptance time of 2025-06-27 17:01:51 ET. It illustrates why the report date and knowledge date are distinct. EDGAR's general filing guidance also states that most submissions accepted after 5:30 p.m. ET receive the next business day's filing date and are not disseminated until that next business day; the N-PORT form is not among the listed after-hours exceptions.

## 4. Corrected row-level contract

For a long-equity share-count feature, accept a row only when:
- ASSET_CAT == "EC";
- PAYOFF_PROFILE == "LONG" (unknown/blank is not assumed long);
- UNIT == "NS" (number of shares);
- BALANCE is numeric, finite and positive.

Reject principal-amount units (PA), other units (OU), non-equity assets, short/unknown payoff profiles, missing values, non-finite values and nonpositive balances. Keep short exposure as a separate future feature; do not net it into the long series without a separate preregistered definition.

The new Phase 247 helper implements this fail-closed contract and explicitly demonstrates that the old UNITS lookup returns zero on an official flattened row.

## 5. Research design correction before any new return test

The earlier annual snapshots are not enough to support a robust chronological OOS claim. The next N-PORT panel should use the full set of public quarterly archives and each fund series' own fiscal reporting cadence:

- Build an accession-level panel for all public NPORT-P and NPORT-P/A filings.
- Identify the fund by CIK + SERIES_ID; identify each holding by ACCESSION_NUMBER + HOLDING_ID.
- Resolve securities by CUSIP/ISIN using an effective-dated PIT crosswalk. Ticker is corroborative, never a permanent security key.
- For each series, compare a newly disseminated original report with that same series' previous public report; do not force all funds onto a September 30 calendar snapshot.
- Calculate share changes separately for explicit long and short equity positions. Adjust for splits, corporate actions, CUSIP changes, fund mergers and share-class/series changes before aggregating.
- Preserve amendments as state corrections. Never count an amendment as a new purchase/sale event.
- Aggregate fund-reported changes only after actual public dissemination; use the next eligible regular session.
- Separate quantity changes from market-value changes to avoid confusing price appreciation with accumulation.
- Control for fund subscriptions/redemptions and fund returns where available; otherwise the result may simply capture fund inflows or performance chasing.
- Compare any candidate overlay against frozen LTM/F80 with identical eligible names, signal dates, exposure, turnover and costs. Use chronological walk-forward, issuer/fund/period clustered bootstrap, fund and security LOO, multiplicity control and a genuinely prospective confirmation. Do not reuse the consumed holdout.

N-PORT covers registered management investment companies and eligible ETFs, not all hedge funds, pension funds, sovereign funds or every institutional investor. It is a quarterly, delayed holdings source, not transaction-level order flow. Its best role is a slow-moving ownership/positioning feature or contextual control, not an assumed short-term signal.

## 6. Phase 247 disposition

| Gate | Result |
|---|---|
| Official flattened schema verified | PASS |
| Legacy Phase 27O unit-field mismatch | CONFIRMED |
| Corrected fail-closed share parser added | PASS — unit tests |
| Full 28-archive raw-data audit | NOT RUN |
| Effective-dated 335-name security coverage | NOT ESTABLISHED |
| Strict accession-level PIT vintages | NOT ESTABLISHED |
| N-PORT alpha / return test | NOT AUTHORIZED |
| Independent OOS | NOT AUTHORIZED |
| F80 baseline | FROZEN |

**Decision:** quarantine the legacy Phase 27N/27O share-flow output. Do not reopen the same annual return test yet. First correct the flattened field contract, then build the full accession-level asynchronous panel and audit its security coverage. Only after those gates pass should a new preregistered test be considered.

## Sources

- SEC Form N-PORT Data Sets: https://www.sec.gov/data-research/sec-markets-data/form-n-port-data-sets
- SEC N-PORT Data Sets Readme: https://www.sec.gov/files/nport_readme.pdf
- SEC Form N-PORT and public availability instructions: https://www.sec.gov/files/formn-port.pdf
- SEC raw N-PORT XML example with <units>NS</units>: https://www.sec.gov/Archives/edgar/data/1100663/000100472626010078/primary_doc.xml
- SEC filing index with period end and accepted timestamp: https://www.sec.gov/Archives/edgar/data/1424958/0001145549-25-044643-index.htm
- SEC EDGAR filing-date/dissemination guidance: https://www.sec.gov/submit-filings/filer-support-resources/how-do-i-guides/determine-status-my-filing
- SEC 2025 N-PORT amendment compliance-date delay: https://www.federalregister.gov/documents/2025/04/22/2025-06861/form-n-port-and-form-n-cen-reporting-guidance-on-open-end-fund-liquidity-risk-management-programs-delay-of
