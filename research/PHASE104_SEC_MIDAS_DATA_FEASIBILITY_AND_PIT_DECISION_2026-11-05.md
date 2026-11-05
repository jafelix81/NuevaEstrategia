# Phase 104 — SEC MIDAS actual-file feasibility and PIT gate decision

**Date:** 2026-11-05  
**Status:** SAMPLE SCHEMA PASS; POINT-IN-TIME IDENTITY GATES NOT PASSED  
**Source run:** [Phase 103 Actions run 41975686235](https://github.com/jafelix81/NuevaEstrategia/actions/runs/41975686235)  
**Artifact:** [phase103-sec-midas-security-audit, artifact 13391039377](https://github.com/jafelix81/NuevaEstrategia/actions/runs/41975686235/artifacts/13391039377)  
**Artifact SHA-256:** `2f144b95b11badef40498d168bc1ee5297f07b58f1b4061bd68317cd3fb34d89`

## Executive decision

SEC MIDAS Metrics by Individual Security is a credible, public, long-history market-microstructure candidate. Phase 103 successfully downloaded and parsed six quarterly files spanning 2012Q1–2026Q2. The sample passed file, schema, date, quantity-field and row-shape checks.

**Do not run forward-return tests yet.** Historical public-availability vintages, permanent security identity, and inactive/delisted coverage are not established. The data are daily market-activity aggregates, not participant identity, buyer/seller aggressor flow, or proof of informed trading. Keep MIDAS in the candidate queue as a separate microstructure hypothesis, not a promoted Smart Money signal.

## 1. Actual-file sample results

| Quarter | Rows | Unique tickers | F80 legacy overlap | Duplicate-key groups |
|---|---:|---:|---:|---:|
| 2012 Q1 | 306,238 | 5,064 | 54.33% | 0 |
| 2016 Q1 | 323,454 | 5,393 | 60.30% | 2 conflicting rank-only |
| 2017 Q2 | 330,536 | 5,353 | 61.79% | 0 |
| 2019 Q4 | 369,433 | 5,902 | 68.96% | 6 conflicting rank-only |
| 2025 Q4 | 533,076 | 8,625 | 82.99% | 355 exact |
| 2026 Q2 | 542,295 | 9,216 | 83.28% | 19 exact |

All six downloads completed and all six sample schemas passed. The daily legacy-335 overlap was also measured; it is a diagnostic against the manually selected F80 comparability list only, not a broad-universe coverage estimate. The SEC landing page advertises 58 quarterly resources from January 2012 through June 2026 and more than 4,800 securities; Phase 103 did not download all 58 files.

### Duplicate handling

- The two 2016Q1 and six 2019Q4 conflicting duplicate groups differ only in rank fields (McapRank, TurnRank, PriceRank); the sample rows show the activity counts and volumes are identical.
- The 355 2025Q4 and 19 2026Q2 duplicate groups are exact duplicates.
- No duplicate is silently dropped in the current audit. A later panel builder must preregister a deterministic rule: exact-row deduplication; for rank-only duplicates, retain the row with the most complete rank fields only after asserting all non-rank activity fields match exactly. Keep a duplicate-resolution audit trail.

## 2. Identity and historical coverage

The actual file contains `Ticker`, `Date`, and `Security` (observed values: `Stock`, `ETF`). It does **not** contain a CUSIP-like security identifier. The Security field is an instrument classification, not a permanent ID. Ticker-only joins are therefore insufficient for a broad point-in-time return panel, especially across symbol changes, mergers, relistings and inactive securities.

The SEC methodology says the eligible stock/ETP list is sourced from CRSP daily stock records (SHRCD 10/11 for stocks and 73 for ETPs) and refreshed monthly with a 3–4 week lag from the prior month-end. That is a universe-construction feature, not a contemporaneous event-time identifier. The panel must preserve the SEC/CRSP inclusion lag and separately map historical tickers to permanent security IDs. No vendor access or purchase is authorized.

The sample's legacy overlap rose from 54.33% in 2012Q1 to 83.28% in 2026Q2. Because the 335 names were manually selected arbitrarily and are not representative, this change cannot be interpreted as market-wide coverage or survivorship evidence.

## 3. Publication-time / PIT gate

The actual-file audit recorded HTTP Last-Modified, ETag and retrieval Date metadata. Those fields do not establish original public-availability time:

| Quarter | HTTP Last-Modified | Days after quarter end |
|---|---|---:|
| 2012 Q1 | 2020-12-19 | 3,185 |
| 2016 Q1 | 2020-12-19 | 1,724 |
| 2017 Q2 | 1970-01-01 | -17,347 (invalid metadata) |
| 2019 Q4 | 2020-12-19 | 354 |
| 2025 Q4 | 2026-07-17 | 198 |
| 2026 Q2 | 2026-08-06 | 37 |

ETag was absent in all six samples. The Data.gov catalog's dataset-level modified timestamp is 2017-10-30 even though the SEC landing page lists resources through 2026Q2. The SEC page's current review/update date is not the original release timestamp of each historical quarter. These metadata cannot be used as row-level or quarter-level PIT anchors.

There is a possible independent reconstruction route: SEC Market Structure email bulletins provide contemporaneous release evidence for some quarters (e.g. Q3 2021 announced 2021-11-02; Q1 2023 announced 2023-05-02; Q4 2023 announced 2024-01-31). The current audit found examples, not a complete 58-quarter publication ledger. Do not infer one universal release lag from three bulletins. A future PIT gate may use archived SEC bulletins/RSS snapshots if coverage can be demonstrated for every quarter, with a conservative next-session rule.

## 4. Methodology regimes and economic meaning

Two documented structural breaks must be treated explicitly:

- **2017-05-01:** SEC MIDAS changed the NYSE input from Ultrabook level feed to NYSE Integrated Feed. The SEC states that this affects hidden-trade identification and related market-activity measures. Hidden-related metrics should be regime-separated or normalized; do not splice levels blindly.
- **2025-11-03:** the SEC's new round-lot definition took effect. Odd-lot counts and volumes must be regime-separated or normalized using the applicable security-specific round-lot tier.

The SEC says these market-activity metrics generally measure on-exchange continuous trading and exclude off-exchange volume, opening/closing auctions and off-hours activity. HiddenVol is trading against undisplayed resting orders; the denominator TradeVolForHidden excludes exchanges where the SEC cannot definitively identify hidden executions (including NYSE and Amex, and also CHX/NSX as described in the FAQ). Thus:
- hidden activity may be a proxy for interaction with undisplayed liquidity, not the identity or sophistication of the trader;
- odd-lot activity is sensitive to the 2025 round-lot rule change;
- cancel/trade and trade/order ratios are market-microstructure measures, not direct institutional accumulation;
- this source is not a substitute for FINRA ATS/off-exchange aggregates because the MIDAS metrics generally exclude off-exchange volume.

## 5. Gate status and next steps

| Gate | Result |
|---|---|
| Six representative official quarterly files download | PASS |
| Actual schema / date parsing | PASS |
| Volume units identified | PASS — relevant `('000)` columns are thousands of shares |
| Sample duplicate behavior measured | PASS — resolution rule still required |
| Full 58-quarter continuity and file-by-file validation | NOT TESTED |
| Permanent security identity / ticker lifecycle | FAIL / NOT ESTABLISHED |
| Inactive and delisted coverage | NOT ESTABLISHED |
| Complete historical public-availability ledger | FAIL / NOT ESTABLISHED |
| Forward-return / alpha test | NOT AUTHORIZED |

Next work, in order:
1. Correct the SEC release-time ledger using archived contemporaneous SEC bulletins/RSS or another reproducible official timestamp source; do not use current HTTP Last-Modified as a substitute.
2. Design a ticker-to-permanent-ID crosswalk with effective dates and record-known/publication dates, preserving delisted securities and corporate actions. A current ticker map is not enough.
3. Expand quarterly actual-file validation only after the identity and PIT routes look feasible; then freeze the metric definitions and structural-break treatment before any return inspection.
4. Only after all gates pass, preregister a market-microstructure hypothesis (e.g. changes in hidden-liquidity interaction or cancellation/order intensity), control for liquidity, volatility, size, price and return-chasing, and compare incremental information against LTM/F80 under chronological OOS, issuer-clustered bootstrap and LOO discipline.

No forward returns, alpha test, feature tuning, vendor contact, purchase, data acquisition or F80 change occurred in Phase 103/104.
