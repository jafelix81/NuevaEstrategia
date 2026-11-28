# Phase 680 — AMS Capital 13F full 15-row value-scale reconciliation

**Audit date:** 2026-11-28 UTC  
**Repository base:** `32f993f6a2846e4022e10de4059ccf7f032d9c43`  
**Disposition:** all 15 filed positions are consistent with a 1,000× scale candidate in a retrospective same-date close screen; no source value was normalized and no signal was admitted.

## 1. Primary filing facts

SEC accession [0001717977-26-000005](https://www.sec.gov/Archives/edgar/data/1717977/000171797726000005/0001717977-26-000005-index.html) is an original 13F-HR filed by AMS Capital Ltda on **2026-11-27**, accepted at **14:32:31 ET**, for the report period ended **2026-09-30**. The SEC-rendered cover page states 15 information-table entries and a value total of **289,276**, explicitly rounded to the nearest dollar. The SEC-rendered information table shows 15 rows, each with a nearest-dollar value, and the 15 row values sum exactly to the cover-page total of 289,276.

The SEC's current Form 13F FAQ, Question 36, says the nearest-dollar requirement replaced the prior nearest-thousand-dollar convention effective **2023-01-03**. Thus a 1,000× interpretation is an as-filed unit anomaly candidate, not an alternative permitted convention. The SEC's 2026 filing calendar gave the Q3 2026 Form 13F deadline as **2026-11-16**; AMS filed 11 days later. The holdings are dated 2026-09-30 and were not public until the filing was accepted on 2026-11-27. This is not a contemporaneous flow observation.

Primary sources:
- [SEC filing detail](https://www.sec.gov/Archives/edgar/data/1717977/000171797726000005/0001717977-26-000005-index.html)
- [SEC-rendered cover page](https://www.sec.gov/Archives/edgar/data/1717977/000171797726000005/xslForm13F_X02/primary_doc.xml)
- [SEC-rendered information table](https://www.sec.gov/Archives/edgar/data/1717977/000171797726000005/xslForm13F_X02/FILEAMS09302026V1.xml)
- [SEC Form 13F FAQ — Question 36 and nearest-dollar rule](https://www.sec.gov/rules-regulations/staff-guidance/frequently-asked-questions-about-form-13f)

## 2. Full information-table reconciliation

All 15 positions were mapped to the listed US-traded security indicated by the issuer and class description. The reference is the 2026-09-30 unadjusted close (or close adjusted for splits only, not dividend-adjusted close) from the linked secondary historical-price page. The implied price is filed value × 1,000 divided by reported shares.

| Ticker | CUSIP | Class as filed | Filed value | Shares | 2026-09-30 close | Implied price ×1,000 | Abs. error |
|---|---|---|---:|---:|---:|---:|---:|
| AMZN | 023135106 | COM | 38,015 | 152,578 | $249.15 | $249.151254 | 0.000503% |
| ASML | N07059210 | N Y REGISTRY SHS | 17,450 | 9,632 | $1,811.67 | $1,811.669435 | 0.000031% |
| CPNG | 22266T109 | CL A | 8,914 | 642,657 | $13.87 | $13.870541 | 0.003898% |
| FICO | 303250104 | COM | 9,544 | 16,109 | $592.47 | $592.463840 | 0.001040% |
| GOOGL | 02079K305 | CAP STK CL A | 32,618 | 94,798 | $344.08 | $344.078989 | 0.000294% |
| IVV | 464287200 | CORE S&P500 ETF | 50,318 | 65,702 | $765.85 | $765.851877 | 0.000245% |
| META | 30303M102 | CL A | 11,378 | 15,690 | $725.18 | $725.175271 | 0.000652% |
| MSFT | 594918104 | COM | 25,021 | 48,783 | $512.90 | $512.904085 | 0.000797% |
| NU | G6683N103 | ORD SHS CL A | 13,527 | 1,068,474 | $12.66 | $12.660112 | 0.000881% |
| Q | 74743L100 | COMMON STOCK | 6,800 | 54,082 | $125.74 | $125.734995 | 0.003980% |
| SE | 81141R100 | SPONSORD ADS | 8,884 | 91,254 | $97.36 | $97.354637 | 0.005509% |
| SPGI | 78409V104 | COM | 11,532 | 29,233 | $394.47 | $394.485684 | 0.003976% |
| TDG | 893641100 | COM | 8,043 | 7,429 | $1,082.60 | $1,082.649078 | 0.004533% |
| TSM | 874039100 | SPONSORED ADS | 35,982 | 78,874 | $456.19 | $456.195958 | 0.001306% |
| V | 92826C839 | COM CL A | 11,250 | 31,309 | $359.33 | $359.321601 | 0.002337% |

**Result:** 15/15 rows (100%) are within the Phase 671 reference tolerance of 0.5% under factor 1,000. Median absolute relative error is **0.001040%**; maximum is **0.005509%**. Under factor 1, zero rows pass and median absolute relative error is approximately **99.9000%**.

The aggregate check is also tight:
- Filed row values × 1,000: **$289,276,000.00**
- Shares × same-date closes: **$289,275,024.30**
- Difference: **$975.70**, or **0.000337%** of the scaled filed total.

The row values themselves sum to 289,276, exactly matching the SEC cover page. The scaled total is an *implied diagnostic amount*, not a corrected as-filed total.

### Price-reference links

- AMZN: [Yahoo Finance](https://finance.yahoo.com/quote/AMZN/history/)
- ASML: [TipRanks](https://www.tipranks.com/stocks/asml/historical-prices)
- CPNG: [Yahoo Finance](https://ca.finance.yahoo.com/quote/CPNG/history/)
- FICO: [Yahoo Finance](https://au.finance.yahoo.com/quote/FICO/history/)
- GOOGL: [Yahoo Finance](https://finance.yahoo.com/quote/GOOGL/history/)
- IVV: [Yahoo Finance](https://es-us.finanzas.yahoo.com/quote/IVV/history/)
- META: [StockAnalysis](https://stockanalysis.com/stocks/meta/history/)
- MSFT: [Yahoo Finance](https://es.finance.yahoo.com/quote/MSFT/history/)
- NU: [Yahoo Finance](https://finance.yahoo.com/quote/NU/history/)
- Q: [Yahoo Finance](https://finance.yahoo.com/quote/Q/history/)
- SE: [Macroaxis](https://www.macroaxis.com/sea-stock-price-history)
- SPGI: [Yahoo Finance](https://au.finance.yahoo.com/quote/SPGI/history/)
- TDG: [Yahoo Finance](https://finance.yahoo.com/quote/TDG/history/)
- TSM: [Quiver Quant](https://www.quiverquant.com/stock/TSM/historical-prices/)
- V: [ChartExchange](https://chartexchange.com/symbol/nyse-v/historical/)

## 3. Relationship to the Phase 671 detector

The existing Phase 671 detector remains unchanged and deliberately narrow: it admits only `COM` and `COMMON STOCK` rows with `SH`, blank put/call, valid CUSIP, positive values and a same-report-date price. Therefore only seven rows are in its current common-stock scope. The other eight positions are not detector failures: they are Class A, registry shares, sponsored ADS, or an ETF and were included here only in a manual full-table economic reconciliation.

This phase does **not** broaden the production detector, change thresholds, or certify a general mapping rule for all share classes. It establishes that the previously identified seven-row signal is not driven by an incomplete seven-row sample: the complete 15-row table independently points to the same 1,000× scale.

## 4. Important limitations

- The SEC filing index lists the raw information-table XML as 8,610 bytes, but the raw XML bytes were **not** downloaded and no raw-XML SHA-256 was computed. The audit uses SEC's rendered primary cover/table views.
- Historical prices are secondary references, not an approved production price panel. Provider sources may share upstream data and are not treated as fully independent confirmations.
- CUSIP-to-ticker/share-class mapping is a manual retrospective mapping, not a certified point-in-time security-master join.
- The SEC FAQ says Form 13F reports long positions; short positions are not included. This filing is therefore not a complete portfolio or a transaction tape.
- No conclusion is made about intent, negligence, or why the scale mismatch occurred.

## 5. Research and production decision

- Classification remains **`LEGACY_THOUSANDS_CANDIDATE`** for this filing only.
- Preserve all source values exactly as filed; no multiplication or normalization has been applied.
- Do not change the Phase 671 parser or production pipeline.
- No return/event study, alpha test, OOS, bootstrap, LOO, or holdout use.
- No trading signal is promoted; `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen.
- No vendor was contacted and no data was purchased; spend remains USD 0.

## 6. Next gates

1. Retrieve the raw 8,610-byte SEC information-table XML through the existing authorized SEC User-Agent path and record its SHA-256.
2. Run the raw XML parser against all 15 entries and reconcile each CUSIP, class, shares and value to the SEC-rendered table.
3. Expand the positive/negative unit-control sample to at least 20 independent managers, with multiple share classes and multiple post-2023 quarters; keep the thresholds provisional until that calibration is complete.
4. Keep any normalization reversible and separate from as-filed storage; require a reviewed mapping/override record before any downstream use.
5. Only after independent data-quality and PIT/security-master gates pass should any 13F-derived feature be considered. The 58-day report-to-publication lag and 45-day filing window must remain explicit in every event study.

**Conclusion:** the full filing-level audit strengthens the data-integrity diagnosis from a seven-row subset to all 15 holdings. It does not turn 13F into a timely or predictive smart-money signal.
