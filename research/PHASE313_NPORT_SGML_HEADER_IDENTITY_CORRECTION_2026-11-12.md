# Phase 313 — SEC N-PORT SGML header identity correction and raw-artifact re-audit

**Audit date:** 2026-11-12 UTC  
**Source Phase 312 run:** [43157888685](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43157888685)  
**Source artifact:** [13915839847](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43157888685/artifacts/13915839847)  
**Source artifact SHA-256:** 78586bd1dbbbd12473ce6d0f75cdee360991541e99a9e2eb45641005f81a4287  
**Disposition:** parser correction verified against all 56 immutable raw submissions; Phase 312 series/class identity labels are superseded. No return or alpha test.

## Executive finding

Phase 312's raw submissions and holding rows were not corrupted. Its **series/class identity parser was wrong**.

SEC complete-submission headers use SGML-style tags without closing tags, for example:

    <SERIES-ID>S000043717
    <SERIES-NAME>Otter Creek Long/Short Opportunity Fund
    <CLASS-CONTRACT-ID>C000135565

The Phase 312 parser searched for both an opening and closing tag. It therefore missed identifiers that were present in the original SEC header and then classified the XML copy as XML_ONLY.

Phase 313 parses only the SEC header block before the first DOCUMENT, accepts the SGML value up to whitespace or the next "<", and compares the resulting identifier sets with the primary XML. It reuses the Phase 312 raw bytes; it does not request the SEC again or alter any source file.

## Corrected identity result

| Check | Corrected result |
|---|---:|
| Raw submissions re-read | 56/56 |
| Raw SHA-256 hashes re-verified | 56/56 |
| Series header/XML state MATCH | **53/56** |
| Series identifiers missing in both | 3/56 |
| Class header/XML state MATCH | **53/56** |
| Class identifiers missing in both | 3/56 |
| Series mismatches | 0 |
| Class mismatches | 0 |
| Series names present | 56/56 |

The three filings with no series or class identifier in either source are:

- Putnam Managed Municipal Income Trust — accession 0000869392-25-001170
- Saba Capital Income & Opportunities Fund II — accession 0001049169-25-001153
- Alpha Alternative Assets Fund — accession 0001049169-26-000832

Each has a fund/series name, but no persistent seriesId or classId in either header or XML. They remain at fund/CIK/name level; no identifier is inferred.

**Superseded Phase 312 statement:** the earlier 53 XML_ONLY / 3 MISSING_BOTH series-state count was a parser artifact. The corrected count is 53 MATCH / 3 MISSING_BOTH. The same correction applies to class IDs. The underlying raw documents and holding-row values are unchanged.

## Short-position sample: descriptive only

The 56-filing sample contains 176 sign-concordant rows under the narrow definition (payoffProfile=Short, assetCat=EC, issuerCat=CORP, invCountry=US, units=NS, and negative balance/value/%NAV). All 176 rows have CUSIP and ISIN check digits that validate.

All 176 rows are concentrated in two filings:

| Filing | Report date | Filed date | Report-to-filing lag | Short rows | Ticker rows | Identity |
|---|---|---|---:|---:|---:|---|
| Otter Creek Long/Short Opportunity Fund, NPORT-P/A | 2022-07-31 | 2022-10-03 | 64 days | 20 | 20 | Series S000043717, header/XML MATCH |
| Saba Capital Income & Opportunities Fund II, NPORT-P | 2025-10-31 | 2025-12-30 | 60 days | 156 | 0 | No series/class ID in either source |

Across the two filings there are 173 unique CUSIPs, 173 unique ISINs and 20 reported tickers. Three CUSIPs appear in both filings (67066G104, 88160R101, 942622200, corresponding to NVIDIA, Tesla and Watsco). These are cross-fund observations at different report dates, not evidence of one fund maintaining a position.

The 2022 Otter Creek amendment shares series ID S000043717 with a separate 2023 Otter Creek filing already audited in Phase 310. That permits a future series-level comparison, but the 2022 amendment's original parent accession is still unresolved. The amendment must be treated as a corrected as-filed vintage, not as a new trade or a new position event.

## Legacy F80 ticker-string diagnostic

The exact 335-ticker set was recovered from the Phase 21C signal-panel artifact (run 39362237089, artifact 12238056805) and preserved as phase313_f80_legacy_ticker_snapshot_2026-10-20.csv.

- Snapshot: 335 unique tickers.
- SHA-256: 6da092b65946b7681e5eea1e215dd71cea3493bf33f2df50f4c51bc26edac087.
- Of the 20 ticker-reported short rows, 6 have an exact string match to the 335-name set and 14 do not.
- The other 156 rows do not report a ticker and remain UNKNOWN_NOT_REPORTED, not non-matches.

This is **not** an effective-dated security-coverage result. It is only a ticker-string intersection against the frozen legacy comparison list. CUSIP/ISIN-to-listing identity, ticker changes, share classes, ADRs and delistings remain unresolved. The 335 names were manually selected and are not a statistically designed broad universe (Phase 99).

## Point-in-time and disclosure constraints

The SEC's current Form N-PORT data-set page covers October 2019–September 2026, says the data sets are updated quarterly, and states that they include only information from filings disseminated by the Commission. The data sets exclude money-market funds and SBICs. They are not a live, complete record of every institution's holdings.

As of this audit date, the operative public-disclosure regime remains quarterly: funds report monthly holdings to the SEC, but only the third month of each fiscal quarter is public; the first two months remain confidential. The SEC's 2024 amendments would make monthly reports public 60 days after each month, but the SEC delayed their effective/compliance dates in April 2025 to November 17, 2027 for larger fund groups and May 18, 2028 for smaller groups. The SEC's February 18, 2026 Form N-PORT proposal is still a **proposal**, not an effective rule.

The two positive filings in this sample were filed 60 and 64 calendar days after their report dates. This is consistent with a delayed quarterly snapshot, not timely trading flow. The SEC acceptance timestamp is filing metadata, not a verified first-public-receipt timestamp. Any later event study must use a conservative post-acceptance execution boundary and preserve the filing/amendment vintage.

Official sources:
- [SEC Form N-PORT Data Sets](https://www.sec.gov/data-research/sec-markets-data/form-n-port-data-sets)
- [SEC 2024 Form N-PORT amendments](https://www.sec.gov/newsroom/press-releases/2024-110)
- [SEC April 2025 delay of Form N-PORT amendments](https://www.sec.gov/rules-regulations/2025/04/s7-26-22)
- [SEC February 18, 2026 proposed Form N-PORT reporting rule, IC-35962](https://www.sec.gov/files/rules/proposed/2026/ic-35962.pdf)
- [SEC small-entity guide to the current reporting regime](https://www.sec.gov/resources-small-businesses/small-business-compliance-guides/investment-company-reporting-modernization-rules)

## Research decision

**Keep N-PORT as a conditional slow-positioning/context source, not a trade-flow signal.**

What is now better:
1. Series/class identity is confirmed in 53/56 raw documents, rather than 0/56 header matches under the old regex.
2. Three no-ID cases are explicitly quarantined at fund/CIK/name level.
3. The original Phase 312 raw bytes and their hashes are unchanged and re-verified.
4. The short-position sample is described at accession level, without interpreting positions as trades.

What is still missing:
1. Original-parent linkage for the Otter Creek 2022 NPORT-P/A.
2. Effective-dated CUSIP/ISIN-to-listing/security mapping, including inactive and changed securities.
3. Representative historical coverage by fund/series, security type, year and universe.
4. A verified first-public timestamp and complete amendment/correction vintage history.
5. A point-in-time fund/series continuity panel and broad-universe coverage.

Next: resolve the original Otter Creek filing by scanning the 2022 Q3 NPORT-P candidates for registrant CIK 811030, report date 2022-07-31 and series S000043717; compare the original and amended position rows. Then expand the stratified sample before estimating short-position prevalence. Do not mix the Phase 310 purposive positive-control filings into a prevalence estimate.

## Validation and controls

- 8/8 new offline regression tests passed locally.
- 56/56 raw-file hashes matched the Phase 312 reconciliation ledger.
- 53/56 series IDs and 53/56 class IDs matched header to XML; zero mismatches.
- No new SEC request was made; no raw bytes were modified.
- No return/alpha test, bootstrap, LOO, chronological OOS or holdout use.
- No vendor contact or purchase; no email sent.
- F80_TOP20_PARTIAL50_BASELINE_C20, production, universe, capital and parameters remain unchanged.
