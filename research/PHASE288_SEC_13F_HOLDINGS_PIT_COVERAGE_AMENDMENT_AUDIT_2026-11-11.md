# Phase 288 — SEC Form 13F historical holdings and PIT feasibility
Date: 2026-11-11  
Status: high-priority public-data candidate; source audit only. No raw SEC ZIP was acquired and no signal was tested.

## Executive decision

**Admit SEC Form 13F to the next sample-acquisition and coverage-audit stage. Do not admit it to signal modeling yet.**

This is a materially more economical institutional-holdings candidate than the paid exchange products audited in Phase 287:

- SEC structured 13F data sets are public and free.
- The SEC download page currently lists 54 quarterly/monthly packages from 2013 Q2 / July 2013 through August 2026, with individual ZIPs mostly about 34–96 MB.
- The underlying structured submissions contain manager, filing, report-period, CUSIP, optional FIGI, share/principal amount, market value, put/call, investment-discretion and voting-authority fields.
- The original filing accession is available, so the holdings can be joined to EDGAR filing/index dates rather than treating quarter-end as the public-information date.

The main limitation is material: Form 13F is a **quarter-end snapshot disclosed up to 45 days later**, not a transaction tape. It omits short positions and some confidential holdings, and it covers only Section 13(f) securities and qualifying institutional managers. It may measure slow-moving ownership changes, but must not be described as contemporaneous institutional flow.

## 1. Historical coverage and delivery

The SEC Form 13F Data Sets page currently states July 2013–August 2026 and lists 54 downloadable packages, including 2013 Q2 onward and 2026 June/July/August. The SEC readme says the structured XML data set consists of submissions from May 2013 onward. The page also notes that all historical data sets were refreshed on March 12, 2024 to align their format with the 2023 data sets and apply processing fixes.

The data sets are published quarterly. Documents filed after 5:30 p.m. Eastern on the last business day of a quarter are included in the subsequent quarterly posting. Therefore, the bulk ZIP publication date is not the right PIT timestamp for a particular holding. Use the individual EDGAR accession and its first public index appearance.

Form 13F filings are due within 45 days after quarter-end. As of 2026-11-11, Q3 2026 Form 13F is not yet due: the SEC's current deadline table gives **2026-11-16**. The bulk data page currently ends at August 2026. Do not infer Q3 holdings before actual filings appear.

## 2. Fields and usable identifiers

The SEC readme documents seven flat, tab-delimited UTF-8 tables. Important keys and fields:

- `SUBMISSION`: `ACCESSION_NUMBER` (primary key), `FILING_DATE`, `SUBMISSIONTYPE`, `CIK`, `PERIODOFREPORT`.
- `COVERPAGE`: amendment flag/number/type, confidential-treatment flags/dates, filing-manager name, report type and Form 13F file number.
- `OTHERMANAGER` / `OTHERMANAGER2`: included-manager identifiers and names.
- `INFOTABLE`: issuer, class, 9-character CUSIP, optional FIGI, value, share/principal amount and type, put/call, investment discretion, other-manager sequence, voting authority.

The SEC data set is explicitly “as filed” and includes amendments. It also warns that extracted data can contain inaccuracies and does not include all filing metadata. Treat the bulk tables as an acquisition/normalization convenience, not as the authoritative filing record.

### Important schema and unit breaks

1. Before **2023-01-03**, `VALUE` is in thousands; from that date it is rounded to the nearest dollar. Normalize units by filing date before calculating weights or ownership.
2. FIGI is optional and was added to the XML schema with EDGAR Release 22.4.1 / January 2023. Do not assume complete FIGI coverage before then.
3. The SEC data page says the historical files were refreshed in March 2024; preserve the original accession and filing date, and do not treat the current ZIP as a contemporaneous historical snapshot.
4. EDGAR Form 13F XML schema version 2.0 was published September 14, 2026; the documented cover-page element `provideInfoForInstruction5` changed to `provideInfoForInstruction`. The next quarterly cohort may therefore cross another schema boundary.

## 3. PIT reconstruction and amendment logic

A valid PIT panel must be built from each accession as it became public, not from the latest version of a quarter's holdings:

- Join `ACCESSION_NUMBER` to EDGAR submissions and the daily index. Retain the filing/acceptance metadata and first daily-index sighting. Do not backdate to `PERIODOFREPORT` or quarter-end.
- For a close-to-close strategy, a conservative first usable timestamp is the next full executable session after the verified public appearance, unless the exact availability time is established.
- `13F-HR` is an initial holdings report. `13F-HR/A` is an amendment. `13F-NT` / `13F-NT/A` are notice reports and do not constitute a zero-holdings observation.
- SEC FAQ 58b says a restatement resubmits the entire filing and supersedes the original; FAQ 58c says an amendment adding new holdings supplements the original. Preserve each version and apply the amendment type only from its own public filing date. Never rewrite the earlier historical information set.
- Confidential treatment can omit holdings from the original public filing. Denial or expiry can lead to later amendments that add holdings. Use `CONFDENIEDEXPIRED`, `DATEDENIEDEXPIRED`, `DATEREPORTED` and the actual amendment accession to make a holding visible only when disclosed. Some personal-holdings exemptions may remain confidential indefinitely.
- Combination reports can include other managers. Use the other-manager sequence and filing instructions to avoid counting the same economic holdings multiple times across a reporting manager and included managers.

## 4. What 13F does and does not measure

**Useful hypotheses**
- Change in shares held by a manager, normalized for splits/corporate actions.
- Breadth of managers adding/reducing a name.
- Concentration-weighted additions and reductions, with manager-level persistence.
- New-manager entry and manager exit, after accounting for reporting and identifier coverage.
- Separate reported put/call holdings as a distinct, sparse options feature, not as total options exposure.

**Hard limitations**
- The SEC says short positions must not be reported and must not be netted against longs. 13F therefore cannot provide net institutional exposure or short positioning.
- Only securities on the Section 13(f) list are reportable; not every global security or every instrument is covered.
- A qualifying institutional investment manager generally has at least $100 million in Section 13(f) securities under the rule. Smaller managers are absent.
- Reported positions are quarter-end snapshots; the filing can arrive up to 45 days later. The holdings may have changed materially by publication.
- Put/call reporting is limited to qualifying Section 13(f) options; the information table does not provide a full option-chain trade tape with intraday timestamps.
- Manager names and filing categories do not prove skill, informed trading or “smart money.” Passive index holdings, custody, shared discretion and regulatory reporting all affect the data.

## 5. Coverage audit required before modeling

The next raw-data audit must measure, by quarter and by the historical point-in-time universe:

1. Percentage of universe names with a resolvable CUSIP/FIGI-to-ticker mapping, including share classes, ticker changes, mergers, spin-offs and delisted securities.
2. Number of distinct reporting managers, valid 13F-HR holdings reports, notice reports, amendments and confidential-treatment additions.
3. Holdings-table coverage by issuer/class, shares vs principal amount, put/call, discretion and other-manager attribution.
4. Reconciliation of `VALUE` units across 2023-01-03, and share counts across corporate actions.
5. Duplicate and restatement/addition behavior by accession, amendment number and report quarter.
6. First public appearance and executable date for each filing, including after-hours and weekend filings.
7. Missingness from confidential treatment and late amendments; do not fill missing holdings with zero.
8. Coverage stability and reporting-manager survivorship. Do not use today's manager list to define historical membership.

If ticker mapping, amendment chronology or filing availability cannot be reconstructed reliably, kill the source for PIT modeling and archive the reason.

## 6. Candidate test design — only after the raw audit passes

13F is a slow-frequency ownership hypothesis, not an intraday signal. Potential features should be frozen before testing:
- manager breadth change;
- aggregate shares/value change with consistent units and corporate-action adjustment;
- concentration-weighted additions/reductions;
- persistence of manager ownership across consecutive quarters;
- disagreement/dispersion across managers;
- separate options-reporting feature where data coverage permits.

The critical null is return-chasing: holdings reported for quarter-end may simply reflect prior price appreciation. Regress or stratify against prior 1/3/6-month returns, market capitalization, liquidity, volatility, sector, index membership and momentum. Compare only after the actual filing became public. Test incremental information over frozen LTM/F80 with chronological train/validation/OOS, identical exposure and costs, bootstrap/LOO, multiple-testing controls and an untouched holdout. No positive result is presumed.

## 7. Decision and next step

- Keep 13F as a **high-priority free-data candidate** for quarterly ownership features.
- Acquire the smallest available official ZIP first (2013 Q2 and one recent quarter), then validate the current schema, amendment cases and accession join before downloading the full 2013–2026 panel.
- The container environment could not resolve SEC/Nasdaq hosts during this run, so no ZIP bytes were downloaded. `SEC_CONTACT_EMAIL` remains unconfigured for automated SEC retrieval; no request was made.
- No model, signal, return series, bootstrap, LOO or OOS test was run. No production, F80, universe, capital, parameters or holdout changed.

## Sources (official / primary)

- SEC Form 13F Data Sets and current download inventory: https://www.sec.gov/data-research/sec-markets-data/form-13f-data-sets
- SEC Form 13F Data Sets readme (table definitions and units): https://www.sec.gov/files/form_13f_readme.pdf
- SEC Form 13F FAQs (45-day filing deadlines, amendments, confidential treatment, short positions): https://www.sec.gov/rules-regulations/staff-guidance/frequently-asked-questions-about-form-13f
- Investor.gov Form 13F overview: https://www.investor.gov/introduction-investing/investing-basics/glossary/form-13f-reports-filed-institutional-investment
- SEC EDGAR technical specifications (Form 13F schema history): https://www.sec.gov/submit-filings/technical-specifications
- Data.gov SEC Form 13F dataset catalog: https://catalog.data.gov/dataset/form-13f-data-sets
