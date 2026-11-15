# Phase 418 — Historical denominator correction for options sample coverage

**Audit time:** 2026-11-15 14:06 UTC  
**Disposition:** Correct the interpretation of Phase 417's one-date ORATS and Cboe sample reach metrics. The ORATS 324/335 figure used a current-symbol denominator against a 2024-01-03 sample; at least seven current symbols had not yet begun public trading, and the current ticker XYZ was still SQ. After only those date/alias corrections, the descriptive reach is 325/328 (99.09%), but this is still **not** historical F80 membership, optionability, or PIT coverage. Cboe's 2025-03-28 20% contract sample is not a full-universe coverage test. No source or signal admitted; no return test.

## 1. Repository preflight

- Rechecked the latest 100 Actions runs (7,658 total reported), latest 100 PR search results (56 open), branch search, Phase 417 state/report, and relevant SEC/Cboe/ORATS run jobs, logs and artifacts.
- Latest 100 runs: 62 success, 37 failure, 1 cancelled; zero queued and zero in-progress at 2026-11-15 14:06 UTC.
- Latest SEC scheduled run remains [43709012759](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43709012759). Both jobs passed. Live capture receipt: 2026-11-15 11:28:22 UTC; 55 feed observations (50 Form 144 + 5 Form 144/A), zero new accessions/events/candidate matches/XML resolutions, no detected feed-window gap, and no research/signal-eligible events. The latest 100 runs show no later schedule event by this audit. Do not manually dispatch or duplicate polling.
- CFTC TFF Phase 384 remains on its existing weekday 22:15 UTC schedule; next expected prospective capture is Monday 2026-11-16 22:15 UTC, after the official 20:30 UTC release. No Sunday schedule slot is due.
- No new run was started. No trading code, workflow, parameter, universe, holdout, capital or production setting was changed.

## 2. ORATS 2024-01-03 denominator audit

Phase 417's canonical sample is the ORATS SMV Strikes file for **2024-01-03**:
- Raw sample archive: 66,808,802 bytes; SHA-256 `e04a37310b0f453fedc03a000c55adfc517a119279150173916ebdc5fb514570`.
- 716,822 option-series rows, 5,787 underlyings, 39 columns.
- Original Phase 417 descriptive comparison: 324/335 current diagnostic tickers (96.72%); the eleven unmatched current symbols were ALAB, AMTD, DJT, GEV, HAPN, LOT, RDDT, TELFY, TEM, WAY and XYZ.
- Downloaded and inspected the retained Phase 61 artifact [13301409440](https://github.com/jafelix81/NuevaEstrategia/actions/runs/41787946992/artifacts/13301409440). It contains `summary.json`, `download_metadata.json` and `ticker_coverage.csv` (the original 66.8 MB raw sample itself is not in this small audit artifact). The coverage CSV confirms that **SQ is present with 599 rows**, while XYZ is absent.

### 2.1 Seven symbols did not yet trade publicly under their current symbols

| Current symbol | First public trading / listing date | Evidence |
|---|---:|---|
| ALAB | 2024-03-20 | [Astera Labs IPO announcement](https://www.asteralabs.com/news/astera-labs-announces-pricing-of-initial-public-offering/) |
| LOT | 2024-02-23 | [Lotus Technology listing announcement](https://media.lotuscars.com/en/news-articles/lotus-technology-celebrates-public-listing-on-nasdaq.html) |
| RDDT | 2024-03-21 | [Reddit SEC filing](https://www.sec.gov/Archives/edgar/data/1713445/000171344525000018/R10.htm) |
| DJT | 2024-03-26 | [Nasdaq listing announcement](https://www.nasdaq.com/press-release/trump-media-technology-group-stock-to-begin-trading-under-ticker-symbol-djt-2024-03) |
| GEV | 2024-04-02 | [GE spin-off announcement](https://www.ge.com/news/press-releases/ge-board-of-directors-approves-spin-off-of-ge-vernova-ge-vernova-and-ge-aerospace-to) |
| WAY | 2024-06-07 | [Waystar IPO announcement](https://www.waystar.com/news/waystar-announces-pricing-of-initial-public-offering/) |
| TEM | 2024-06-14 | [Tempus IPO announcement](https://investors.tempus.com/news-releases/news-release-details/tempus-announces-pricing-initial-public-offering-0) |

Those seven names cannot be counted as missing ORATS coverage on 2024-01-03 under the current symbols: their public common/ADS trading under those symbols began later. DJT's predecessor DWAC was a separate SPAC security before the business combination; do not silently treat its option series as the same DJT common-stock contract history.

### 2.2 One current ticker is a post-sample symbol alias

Block's Class A shares traded as **SQ** on 2024-01-03. The company announced the change to **XYZ**, effective 2025-01-21. The ORATS coverage CSV contains SQ (599 rows), so the missing XYZ row is a ticker-vintage mismatch, not evidence that the issuer was absent from the sample. Source: [Block/Nasdaq ticker-change announcement](https://www.nasdaq.com/press-release/block-announces-ticker-symbol-change-xyz-report-fourth-quarter-results-2025-01-09).

After excluding the seven not-yet-public current symbols and mapping XYZ to SQ:
- Comparable current-symbol denominator: 335 - 7 = 328.
- Matched issuers/aliases: 324 + 1 = 325.
- Corrected **descriptive sample reach**: 325/328 = **99.09%**.
- Three remaining unmatched names: AMTD, HAPN, TELFY. Their historical listing, share-class, and optionability status is unresolved here; do not label them provider misses or non-optionable without evidence.

**Important:** 99.09% is not an admission-grade coverage statistic. It still compares a current 2026 diagnostic universe to one historical date. It does not prove that all 328 names were F80 members on 2024-01-03, were optionable on that date, or had all strikes/expiries represented. It is only a corrected reconciliation of the sample's symbol labels.

## 3. Cboe Open-Close 2025-03-28 sample: sampling design limits coverage inference

The retained Phase 54 artifact [13291147097](https://github.com/jafelix81/NuevaEstrategia/actions/runs/41762583602/artifacts/13291147097) contains the public C1 EOD sample dated 2025-03-28. It is explicitly a **20% contract-row sample**, not the full C1 EOD file:
- 23,179 sampled contract rows and 1,553 underlyings.
- 288/335 current diagnostic tickers appeared in the sampled rows (85.97%).
- The sample's participant-volume accounting reconciled exactly to `total_exchange_vol` on all 23,179 sampled rows in the later Phase 355 audit.

Because sampling is at the contract-row level, a ticker with few eligible series can be absent by chance even if it is present in the complete daily file. Conversely, a ticker appearing in the 20% sample does not prove all its series are covered. Therefore 288/335 is **sample reach only**, not a universe-coverage estimate. A valid coverage audit requires the complete file or a vendor-supplied full-universe coverage manifest, with historical optionability and F80 membership at the relevant date.

## 4. Cboe historical regime matrix — no undocumented transformations

Inspected the retained Phase 355 and Phase 356 artifacts:
- Phase 355 accounting artifact [14018077659](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43385933110/artifacts/14018077659), SHA-256 `d7b8088bd20f711a18b142e672d8a4415c340d60a9a0fa7cd3a17cd927b74b11`.
- Phase 356 policy matrix artifact [14021956576](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43392705559/artifacts/14021956576), SHA-256 `17916ac2e40cedaf3d0f9c40a39acebb591e3843ed6daaed862877affc550073`.

The matrix is explicitly documentation-only, not historical data validation. It records material convention changes:
- C1: legacy pre-2011 format; candidate 2x normalization for `total_exchange_vol` through 2019-10-04 pending sample validation; OI documented as shifted one day ahead until 2019-10-04; start-of-day OI from 2019-10-07; GTH included from 2023-12-11.
- C2: candidate 0.5 normalization for `total_industry_vol` through 2018-05-11 pending sample validation; shifted OI through 2018-05-11; start-of-day OI from 2018-05-14.
- BZX and EDGX have different documented start dates and venue histories.
- The matrix says participant-side volume scaling is unverified; do not infer it from the total-exchange-volume rule.
- Exact first receipt and historical correction vintages are not proven for any matrix row.

No normalization factor is applied in this phase. A policy/documentation break is not evidence that the raw historical files actually exhibit the stated numeric discontinuity. Each candidate adjustment needs paired raw samples on both sides of the boundary and independent reconciliation before use.

## 5. Revised options-source gate

1. ORATS remains a broad context candidate for volume snapshots, OI, IV and Greeks, but Phase 417's 96.72% figure is superseded by the 99.09% **descriptive-only** denominator correction above.
2. Cboe Open-Close remains a capacity/open-close proxy. Its one-date 20% C1 sample proves parser/schema and arithmetic feasibility only; it does not prove historical-universe coverage or informed-trader identity.
3. Do not calculate a signal from either source until a historical F80 membership × optionability panel, adjusted-contract/OCC deliverable joins, exact file first-receipt/vintage and business-use licensing are established.
4. Any future signal test must use next-session availability/entry unless a stronger first-receipt clock is evidenced, and must compare against frozen LTM/F80 at identical exposure/costs with chronological validation, block bootstrap, issuer-clustered uncertainty, LOO and untouched holdout.
5. Keep return-chasing controls: prior underlying return, prior option volume/OI, volatility, liquidity, earnings/event proximity and market/sector exposure. Participant labels are execution-capacity proxies, not beneficial-owner identity.

## 6. Final disposition

- Phase 417's ORATS raw 324/335 current-symbol reach is superseded as a denominator-mismatched descriptive metric.
- Corrected current-symbol reach is 325/328 (99.09%) after seven post-date listings are excluded and XYZ is mapped to SQ; AMTD/HAPN/TELFY remain unresolved.
- Cboe 288/335 from a 20% contract sample remains sample reach only, not coverage.
- Phase 355's one-date arithmetic PASS remains valid only for that C1 sample; Phase 356 remains a documentation-only regime matrix.
- No options source admitted to alpha; no forward-return/OOS/bootstrap/LOO/holdout test authorized.
- `F80_TOP20_PARTIAL50_BASELINE_C20`, universe, parameters, holdout, capital, exposure and production remain unchanged.
- No data purchase, vendor contact, API key or additional workflow was initiated.
