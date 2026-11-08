# Phase 201 — SEC MIDAS README and derived-ratio semantics audit

**Date:** 2026-11-08  
**Hosted run:** [42436111867](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42436111867)  
**Artifact:** [phase201-sec-midas-readme-ratio-semantics, 13599821005](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42436111867/artifacts/13599821005)  
**Disposition:** documentation versions and ratio semantics recovered; negative raw numerators are plausibly feed-reconciliation residuals, but are not explicitly documented as permitted values.

## 1. Embedded README versions

The six disputed archives contain three distinct README versions:
- 2014 Q2: README2_q.txt.
- 2016 Q1–Q4: a shared README.txt version.
- 2019 Q4: a later README.txt version.

None of the three README versions explicitly mentions negative values, negative sentinels or correction handling. Their hashes and full text are preserved in the JSON artifact.

## 2. Correct field semantics

The README confirms that the CSV fields are raw numerators and denominators:
- Hidden is the hidden-trade count numerator; TradesForHidden is its denominator. Hidden Rate is 100 × Hidden / TradesForHidden.
- HiddenVol('000) is the hidden-volume numerator in thousands of shares; TradeVolForHidden('000) is its denominator. Hidden Volume is 100 × HiddenVol / TradeVolForHidden.

This corrects the earlier shorthand that treated Hidden and HiddenVol themselves as ratios. Negative raw numerators are not ordinary missing values; the derived ratios are excluded whenever a numerator is negative or a denominator is zero/missing.

## 3. Derived-ratio results

| Quarter | README member | Valid Hidden Rate ratios | Negative Hidden numerators | Zero Hidden denominators | Hidden Rate >100% | Valid Hidden Volume ratios | Negative HiddenVol numerators | Hidden Volume >100% | Maximum Hidden Volume share |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 2014 Q2 | README2_q.txt | 305,881 | 75 | 12,533 | 0 | 305,880 | 76 | 2 | 2.267144319344933 |
| 2016 Q1 | README.txt | 304,426 | 82 | 18,800 | 0 | 304,324 | 184 | 0 | 1 |
| 2016 Q2 | README.txt | 317,080 | 77 | 21,026 | 0 | 317,010 | 147 | 0 | 1 |
| 2016 Q3 | README.txt | 316,895 | 70 | 21,134 | 0 | 316,812 | 153 | 0 | 1 |
| 2016 Q4 | README.txt | 312,105 | 78 | 19,692 | 0 | 311,939 | 244 | 0 | 1 |
| 2019 Q4 | README.txt | 348,126 | 4 | 21,303 | 0 | 348,121 | 9 | 0 | 1 |

- The Hidden Rate ratios were within [0,1] for all six quarters; none exceeded 100%.
- Hidden Volume share was within [0,1] for five quarters. 2014 Q2 had two observations above 100%, with a maximum share of 2.2671.
- Negative numerator counts match Phase 200. Every negative numerator in these samples had a positive, non-missing denominator.
- Zero denominators are excluded, not imputed or clipped.

## 4. Structural measurement breaks in the README

The README versions describe a changing exchange-coverage and feed methodology:

- **Before May 1, 2017:** for NYSE and Amex, hidden-trade counts and hidden volume are derived as differences between consolidated SIP data and direct-feed data. A negative residual is therefore plausible as a feed-reconciliation artifact, but the documentation does not explicitly authorize negative values or specify how to treat them.
- **May 1, 2017:** NYSE changes from the NYSE Ultra feed to the NYSE Integrated Feed (NIF). The 2019 Q4 README describes hidden and odd-lot measures using NIF rather than the earlier subtraction method.
- **May 21, 2018:** NSX begins reporting hidden trades and odd lots.
- **November 4, 2019:** CHX begins reporting hidden trades and odd lots.

The 2016 sample contains 70–82 negative Hidden numerators and 147–244 negative HiddenVol numerators per quarter. The 2019 Q4 sample contains 4 and 9, respectively. This is consistent with a measurement-regime change, but it is not causal evidence: the exchange coverage also changed, and only six quarters were inspected.

## 5. Research ruling

MIDAS Hidden activity cannot be treated as one homogeneous time series without explicit venue/feed regime controls. The quarterly individual-security aggregate does not provide an exchange field, so it cannot isolate the NYSE/Amex subtraction component.

The SEC separately publishes **Metrics by Individual Security and Exchange**, with 58 quarterly archives from January 2012 through June 2026 and each security partitioned by exchange. This is now the preferred next audit: inspect the archive member layout and determine whether the exchange partition is encoded in filenames or separate data members, then reconcile selected aggregate rows against exchange-level rows.

PIT remains NOT ADMITTED: first-publication vintages, permanent historical identity and inactive/delisted coverage remain unresolved. No alpha/return test or holdout use.

## Official references

- SEC [Metrics by Individual Security](https://www.sec.gov/data-research/sec-markets-data/marketstructuredata-security).
- SEC [Metrics by Individual Security and Exchange](https://www.sec.gov/data-research/sec-markets-data/market-structure-data-security-exchange) — 58 quarterly ZIPs, January 2012–June 2026; per-security metrics partitioned by exchange.
- SEC [Market Activity Report Methodology](https://www.sec.gov/featured-topics/market-structure-analytics/market-activity-report-methodology).
