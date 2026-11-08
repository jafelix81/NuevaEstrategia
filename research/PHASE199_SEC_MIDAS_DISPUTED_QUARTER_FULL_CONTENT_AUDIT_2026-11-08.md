# Phase 199 — SEC MIDAS disputed-quarter full-content audit

**Date:** 2026-11-08  
**Disposition:** four previously unvalidated disputed-quarter archives pass full ZIP/CSV content checks; strict PIT, security identity and alpha remain **NOT ADMITTED**.  
**Hosted run:** [42435402228](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42435402228)  
**Artifact:** [phase199-sec-midas-disputed-quarter-content, 13599710929](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42435402228/artifacts/13599710929)

## 1. Question resolved

A third-party MIDAS catalog claimed six quarters were absent at source: 2014 Q2, all four quarters of 2016, and 2019 Q4. Phase 198 established that the SEC's current archive index lists all 58 quarters from 2012 Q1 through 2026 Q2 and that the six disputed ZIP URLs are reachable. Phase 103 had already downloaded and schema-validated 2016 Q1 and 2019 Q4.

Phase 199 fully downloaded and inspected the remaining four SEC-hosted assets: 2014 Q2 and 2016 Q2–Q4. Each archive passed ZIP CRC validation, contained a populated MIDAS data member, matched the required schema, and had no invalid dates, blank tickers, malformed rows or rows outside its declared quarter.

**Conclusion:** all six disputed quarters have actual SEC-hosted data content. This disproves the claim that those six assets are absent from the current SEC archive. It does not establish whether the third-party provider successfully ingested them; its own extraction pipeline was not inspected.

## 2. Full-content results

| Quarter | Valid rows | Unique tickers | Unique dates | Duplicate key groups | Negative Hidden values | Negative HiddenVol values |
|---|---:|---:|---:|---:|---:|---:|
| 2014 Q2 | 318,489 | 5,168 | 63 | 0 (0 exact / 0 conflicting) | 75 | 76 |
| 2016 Q2 | 338,183 | 5,393 | 64 | 61 (6 exact / 55 conflicting) | 77 | 147 |
| 2016 Q3 | 338,099 | 5,400 | 64 | 68 (0 exact / 68 conflicting) | 70 | 153 |
| 2016 Q4 | 331,875 | 5,365 | 63 | 43 (2 exact / 41 conflicting) | 78 | 244 |

All four quarters had zero invalid date rows, zero blank-ticker rows, zero malformed rows, zero out-of-quarter rows and zero non-numeric values in the audited numeric fields.

2014 Q2 uses a nested ZIP container: the outer archive contains individual_security_2014_q2.zip, which contains q2_2014_all.csv. The auditor now detects the data member by schema and recursively validates nested ZIPs. This packaging detail may explain why a simple one-level ZIP parser misses that quarter.

SHA-256:
- 2014 Q2 outer: 55b5d81438cca01f0451d6e4fcc3cad6efc4a345f4784e423ba2803403adc883; inner: 746ebefd33c82501367f09a133fee4800d93ab55d27c6921a2c7ff0467cdfc21.
- 2016 Q2: 0074161916f1aa11390f6d5da59d6de919baa1111df4d81f5fa81f63d499bf4b.
- 2016 Q3: b95521f684d9ee873080e14ffc95802607d6fae486ead051f169d6bfacf7cd97.
- 2016 Q4: 46b63d9b771a2b45cd03068142c3b317953e42ee269b9c90bb24ad88cb236e76.

## 3. Newly exposed data-quality gates

### Duplicate security-day keys

The audit key is (Ticker, Date, Security). Phase 199 found 61 duplicate groups in 2016 Q2, 68 in 2016 Q3 and 43 in 2016 Q4. Most are conflicting rather than exact duplicates. The earlier Phase 103 sample found two conflicting rank-only groups in 2016 Q1 and six conflicting rank-only groups in 2019 Q4.

Phase 199 deliberately does not drop or resolve these rows. It did not yet compare field-by-field whether the new conflicts are limited to McapRank/TurnRank/VolatilityRank/PriceRank or affect activity measures. A deterministic deduplication policy is not admitted until that comparison is complete.

### Negative values in hidden-trade and hidden-volume numerators

The SEC methodology defines Hidden Rate as hidden trades divided by trades and Hidden Volume as hidden trade volume divided by total trade volume. In the file, Hidden is the raw hidden-trade-count numerator and TradesForHidden is its denominator; HiddenVol('000) is the hidden-volume numerator in thousands of shares and TradeVolForHidden('000) is its denominator. Negative values in either numerator are not ordinary ratio values. The four archives contain the negative-value counts shown above in Hidden and HiddenVol('000); all other audited numeric fields had no negative values in these samples.

The Phase 199 metadata records counts, not the exact negative values or rows. Do not assume these are -1 sentinels. Phase 200 must inspect the value distribution, representative ticker/date rows and denominators, then determine whether they are missing-value codes, corrections or genuine source anomalies. Quarantine affected observations until resolved.

## 4. PIT, universe and semantic ruling

- The row's trading date is not its public-availability date. No original first-publication timestamp was established for these four quarters.
- HTTP Last-Modified, Date and ETag remain retrieval metadata, not historical first-publication evidence.
- The number of unique dates (63–64) is descriptive only; the audit did not reconcile every date against an authoritative exchange-session calendar.
- The Security field is a class label (Stock/ETF), not a permanent security identifier. Ticker lifecycle, delisted coverage and historical CRSP membership remain unresolved.
- SEC methodology defines Hidden Rate and Hidden Volume as ratios; it does not identify the beneficial owner, participant type or buyer/seller aggressor. Public MIDAS security metrics remain on-exchange market-structure aggregates, not off-exchange/dark-pool flow or direct institutional flow.

## 5. Decision and next gate

**Keep MIDAS as a conditional market-structure candidate, not a Smart Money label.** The archive-gap objection is resolved for the six disputed quarters, but strict PIT remains blocked by the incomplete 58-quarter release-vintage ledger. Historical identity and the newly detected duplicate/negative-value issues also remain open.

Phase 200 should:
1. compare duplicate rows field-by-field and classify rank-only versus activity-field conflicts;
2. capture exact negative values and representative rows for the Hidden and HiddenVol numerators, including their denominators;
3. test whether the negative values are stable sentinels or unexplained anomalies;
4. preserve every raw version/hash and prohibit silent deduplication;
5. continue the separate first-publication ledger for all 58 quarterly releases.

No forward returns, alpha test, feature tuning or holdout use occurred. No data were purchased, no provider was contacted, production was not changed, and F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen.

## Official references

- SEC [Metrics by Individual Security](https://www.sec.gov/data-research/sec-markets-data/marketstructuredata-security) — 58 quarterly resources, January 2012–June 2026.
- SEC [Market Activity Report Methodology](https://www.sec.gov/featured-topics/market-structure-analytics/market-activity-report-methodology) — definitions of Hidden Rate and Hidden Volume, CRSP universe refresh lag and feed/methodology breaks.
- SEC [MIDAS Feedback / FAQ](https://www.sec.gov/securities-topics/market-structure-analytics/midas-feedback) — exchange coverage and hidden-volume denominator.
