# Phase 677 — SEC 13F AMS Capital Q3 2026 value-unit anomaly audit

**Audit date:** 2026-11-28 UTC  
**Repository base:** `2a0d92463cc8a9b5915b673aa61e4f7d2cebba3f`  
**Disposition:** strong retrospective legacy-thousands candidate; no normalization or signal admission

## 1. Primary filing identity and table reconciliation

The SEC filing detail page identifies accession `0001717977-26-000005` as an original **13F-HR** filed on 2026-11-27 and accepted at 14:32:31 ET, for the report period ending 2026-09-30. The SEC-rendered cover page identifies AMS Capital Ltda, 15 information-table entries, and a value total of **289,276**, explicitly labeled “round to nearest dollar.”

The SEC-rendered information table also labels Column 4 as **VALUE (to the nearest dollar)**. Its 15 displayed row values sum exactly to 289,276, matching the cover-page total. This internal arithmetic is consistent but does not establish that the values are economically scaled correctly.

SEC FAQ 36 says the nearest-dollar convention applies to both the summary value total and individual information-table values from January 3, 2023, replacing the prior nearest-thousand-dollar convention. The filed values therefore should not be multiplied by 1,000 merely because the manager is small or because a third-party portfolio page labels the portfolio differently.

## 2. Same-report-date implied-price test

Seven rows meet the existing Phase 671 detector's current eligibility rules: unique nine-character CUSIP, `COM` or `COMMON STOCK`, `SH`, blank put/call, positive values, and a 2026-09-30 close reference. The references below are secondary historical-price pages used only for a retrospective integrity screen; they are not an approved production price panel.

| Ticker | CUSIP | Filed value | Shares | 2026-09-30 close | Implied price ×1,000 | Absolute error |
|---|---|---:|---:|---:|---:|---:|
| AMZN | 023135106 | 38,015 | 152,578 | $249.15 | $249.1513 | 0.000503% |
| FICO | 303250104 | 9,544 | 16,109 | $592.47 | $592.4638 | 0.001040% |
| MSFT | 594918104 | 25,021 | 48,783 | $512.90 | $512.9041 | 0.000797% |
| SPGI | 78409V104 | 11,532 | 29,233 | $394.47 | $394.4857 | 0.003976% |
| TDG | 893641100 | 8,043 | 7,429 | $1082.60 | $1082.6491 | 0.004533% |
| V | 92826C839 | 11,250 | 31,309 | $359.33 | $359.3216 | 0.002337% |
| Q | 74743L100 | 6,800 | 54,082 | $125.74 | $125.7350 | 0.003980% |

**Detector-rule result:** 7/7 unique CUSIPs (100%) are within the existing 0.5% relative-error tolerance under factor 1,000. Median absolute relative error is **0.002337%** and maximum is **0.004534%**. Under factor 1, zero of seven rows pass; median absolute relative error is **99.9000%**. The sample therefore meets the current Phase 671 thresholds (at least four unique CUSIPs, at least 80% consensus, median error no greater than 0.5%) and classifies as `LEGACY_THOUSANDS_CANDIDATE`.

## 3. Interpretation and limits

This is a strong, independent second manager-level example of a post-2023 13F information table whose reported values appear to retain the legacy thousands scale despite the SEC nearest-dollar labels. The seven price checks strongly support a 1,000× scale candidate. The as-filed 15-row total remains 289,276; **289,276,000 is only the implied total if the same factor applies to every row**, not a verified corrected portfolio value.

The full raw information-table XML was not downloaded and no SHA-256 was calculated. The evidence uses the SEC's XSL-rendered primary filing pages, the complete 15-row rendered table, and secondary same-date close references. Only seven of the 15 rows were eligible for the existing detector; the remaining rows were not used to establish the filing-level scale. No conclusion is made about intent, negligence, or why the unit mismatch occurred.

## 4. Controls

- No as-filed value was changed, multiplied, or overwritten.
- No production parser or data pipeline was modified.
- No holdings were promoted to a research signal.
- No return/event study, OOS, bootstrap, LOO, or holdout analysis was run.
- No vendor was contacted and no data was purchased; spend remains USD 0.
- `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen.

## 5. Next gates

1. Retrieve and SHA-256 hash the complete raw SEC information-table XML through the repository's authorized `SEC_USER_AGENT` path.
2. Parse all 15 rows and reconcile the raw XML to the cover-page entry/value totals.
3. Validate every row against same-date, security-matched prices from a reproducible and approved historical source.
4. Expand positive and negative controls to at least 20 independent managers across multiple post-2023 quarters.
5. Keep normalization out of production until the full filing is reconciled and a reviewed, reversible normalization layer preserves every as-filed value.

## Sources

- SEC filing detail: https://www.sec.gov/Archives/edgar/data/1717977/000171797726000005/0001717977-26-000005-index.html
- SEC-rendered cover page: https://www.sec.gov/Archives/edgar/data/1717977/000171797726000005/xslForm13F_X02/primary_doc.xml
- SEC-rendered information table: https://www.sec.gov/Archives/edgar/data/1717977/000171797726000005/xslForm13F_X02/FILEAMS09302026V1.xml
- SEC Form 13F FAQ (Question 36, nearest-dollar rule): https://www.sec.gov/rules-regulations/staff-guidance/frequently-asked-questions-about-form-13f
- AMZN historical close reference: https://finance.yahoo.com/quote/AMZN/history/
- FICO historical close reference: https://uk.finance.yahoo.com/quote/FICO/history/
- MSFT historical close reference: https://es.finance.yahoo.com/quote/MSFT/history/
- SPGI historical close reference: https://au.finance.yahoo.com/quote/SPGI/history/
- TDG historical close reference: https://finance.yahoo.com/quote/TDG/history/
- V historical close reference: https://es.finance.yahoo.com/quote/V/history/
- Q historical close reference: https://finance.yahoo.com/quote/Q/history/
