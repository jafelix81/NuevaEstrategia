# Phase 671 — SEC Form 13F value-unit detector control calibration

**Date:** 2026-11-27  
**Repository base:** \`main\` \`521cc3ff59aae222fe32c519fc024425bce6a777\`  
**Scope:** Offline data-integrity control only. No production parser integration and no trading signal.

## Executive result

The Canada Life Q3 2026 13F amendment's four indexed SEC information-table samples are consistently compatible with a 1,000× legacy-thousands scale. A separate same-quarter SEC filing from Home Federal Bank of Tennessee provides five ordinary common-stock rows that match contemporaneous closes at scale 1 (nearest-dollar convention). The controls therefore show why a universal 1,000× multiplier would be wrong.

The new detector classifies the four-row Canada Life amendment sample as \`LEGACY_THOUSANDS_CANDIDATE\`, the five-row Home Federal sample as \`NEAREST_DOLLAR_CANDIDATE\`, and the two-row Canada Life base sample as \`INSUFFICIENT_EVIDENCE\`. A deliberately mixed sample is \`MIXED_OR_UNRESOLVED\`.

**No source value is normalized.** The detector emits a human-review candidate only.

## Primary-source control cohort

### Positive anomaly control: Canada Life, Q3 2026 amendment

- CIK: \`0001046192\`
- Accession: \`0001046192-26-000018\`
- Report date: 2026-09-30
- SEC primary cover identifies a 13F-HR/A, NEW HOLDINGS amendment, 806 information-table entries, combination report and summary value 8,531,520.
- [SEC primary cover / amendment](https://www.sec.gov/Archives/edgar/data/1046192/000104619226000018/primary_doc.xml)
- [SEC primary information table](https://www.sec.gov/Archives/edgar/data/1046192/000104619226000018/13F_Filing_Sep26.xml)

Four common-stock rows exposed by the SEC-indexed XML:

| Ticker | CUSIP | Filed value | Shares | Implied price ×1,000 | 2026-09-30 close | Absolute deviation |
|---|---|---:|---:|---:|---:|---:|
| B | 06849F108 | 71,766 | 1,764,862 | $40.663803 | $40.67 | 0.0152% |
| BBWI | 070830104 | 2,214 | 139,134 | $15.912717 | $15.92 | 0.0457% |
| BLK | 09290D101 | 111,382 | 105,330 | $1,057.457514 | $1,058.29 | 0.0787% |
| MRVL | 573874104 | 223,843 | 848,130 | $263.925342 | $264.21 | 0.1077% |

These four rows are a purposive sample from the indexed primary XML, not a full audit of the 806 entries. The raw XML bytes have not been downloaded or SHA-256 hashed. Same-date close checks use secondary historical-price sources and are used only for scale validation.

### Negative control: Home Federal Bank of Tennessee, Q3 2026

- CIK: \`0001665446\`
- Accession: \`0001665446-26-000004\`
- Report date: 2026-09-30; signed 2026-10-15.
- Primary cover: [SEC primary_doc.xml](https://www.sec.gov/Archives/edgar/data/1665446/000166544626000004/primary_doc.xml). It identifies Home Federal Bank of Tennessee, a 13F Holdings Report, 178 table entries and summary value 465,253,420.
- Primary table: [SEC 13F information table](https://www.sec.gov/Archives/edgar/data/1665446/000166544626000004/xslForm13F_X02/13F_09.30.2026.xml).

Five ordinary common-stock rows from the SEC primary table:

| Ticker | CUSIP | Filed value | Shares | Implied price as filed | 2026-09-30 close | Absolute deviation |
|---|---|---:|---:|---:|---:|---:|
| AAPL | 037833100 | 9,869,714 | 29,637 | $333.020009 | $333.02 | 0.000003% |
| AMZN | 023135106 | 338,096 | 1,357 | $249.149595 | $249.15 | 0.000163% |
| MSFT | 594918104 | 7,341,139 | 14,313 | $512.900091 | $512.90 | 0.000018% |
| NVDA | 67066G104 | 1,224,116 | 5,360 | $228.379851 | $228.38 | 0.000065% |
| AVGO | 11135F101 | 823,542 | 2,345 | $351.190618 | $351.19 | 0.000176% |

This is a same-quarter negative control showing that post-2023 filings can and do use the nearest-dollar scale. It rejects any global rule that multiplies every 13F value by 1,000.

## Detector specification

File: \`research/phase671_13f_value_unit_detector.py\`

- Eligible rows: ordinary common stock (\`COM\` or \`COMMON STOCK\`), \`SH\` amounts, no put/call flag, valid 9-character CUSIP, positive value/shares/reference price, and exact report-date/reference-date match.
- Duplicate CUSIPs are aggregated so separate discretion rows do not overweight the same security. Conflicting reference prices are excluded.
- Minimum evidence: 4 unique CUSIPs.
- Candidate scales: 1 and 1,000.
- Candidate requires at least 80% of eligible CUSIPs within 0.5% relative price error and median absolute relative error no greater than 0.5%.
- Mixed, sparse or ambiguous samples fail closed.
- The result always includes \`normalization_applied=false\` and \`trading_signal_eligible=false\`.

The 4-CUSIP, 80%, and 0.5% values are conservative engineering guardrails for initial calibration, not statistically optimized thresholds. They must be evaluated on a broader, pre-specified positive/negative control cohort before production use. The classifier is not integrated into the holdings parser.

## Offline calibration

Expected classifications:

| Sample | Unique CUSIPs | Expected result |
|---|---:|---|
| Canada Life amendment | 4 | \`LEGACY_THOUSANDS_CANDIDATE\` |
| Home Federal control | 5 | \`NEAREST_DOLLAR_CANDIDATE\` |
| Canada Life base report | 2 | \`INSUFFICIENT_EVIDENCE\` |
| Mixed-scale synthetic sample | 4 | \`MIXED_OR_UNRESOLVED\` |

Regression tests also cover options, PRN amounts, non-common classes, reference-date mismatch, duplicate CUSIPs, invalid values, invalid thresholds and source immutability.

## Point-in-time and strategy controls

- Quarter-end prices are used only for retrospective unit-integrity checks; they are not predictive features.
- Form 13F positions remain quarter-end snapshots, not trade timestamps.
- The amendment's first public availability is not certified. No backdated event or position change is created.
- No holdings are normalized or written to the production ledger.
- No returns, event study, model, OOS, bootstrap or LOO analysis was run.
- No holdout data accessed.
- \`F80_TOP20_PARTIAL50_BASELINE_C20\` remains frozen.
- Data purchased: USD 0.

## Next gates

1. Retrieve and SHA-256 hash the full Canada Life amendment XML using the repository's established SEC User-Agent path.
2. Parse all 806 entries and compare with the base filing by CUSIP, class, put/call, shares, discretion and other-manager fields.
3. Add at least 20 independent positive and negative filing controls spanning several post-2023 quarters, including mixed/exception cases.
4. Only then consider production integration; keep normalization human-approved and preserve as-filed values.
5. Continue FINRA, Form 4, 13D/G and CFTC research independently; no signal is promoted from this unit audit.
