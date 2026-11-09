# Phase 102 — SEC Fails-to-Deliver multi-period archive continuity audit

Date: 2026-11-05  
Status: **PASS — representative archive/schema continuity samples**  
Run: [41974948169](https://github.com/jafelix81/NuevaEstrategia/actions/runs/41974948169)  
Artifact: [phase102-sec-ftd-multiperiod-audit](https://github.com/jafelix81/NuevaEstrategia/actions/runs/41974948169/artifacts/13391072776)

## Scope

Downloaded seven official SEC archives spanning the earliest quarterly archive listed in the federal catalog, the September 2008 threshold change, the quarterly-to-half-monthly archive transition in 2009, and modern files. Parser tests passed. No forward returns or alpha tests were performed.

## Actual-file results

| Archive | Valid rows | Settlement dates | Unique CUSIPs | Unique symbols | Trailer checks |
|---|---:|---:|---:|---:|---|
| 2004 Q2 | 173,436 | 63 | 8,993 | 9,209 | 6/6 pass |
| 2008 Q3 | 285,343 | 64 | 14,857 | 14,987 | 4/4 pass |
| 2008 Q4 | 454,860 | 62 | 16,037 | 16,270 | Not present |
| 2009 Q2 | 422,893 | 63 | 14,729 | 15,019 | Not present |
| July 2009 first half | 57,537 | 9 | 10,556 | 10,563 | 2/2 pass |
| January 2018 first half | 43,567 | 9 | 9,820 | 9,824 | 2/2 pass |
| September 2026 second half | 66,693 | 12 | 13,397 | 13,394 | 2/2 pass |

All seven files downloaded. Every sample passed the six-column pipe-delimited schema, date/quantity/price checks, and expected date-range checks. There were zero malformed records, zero invalid/negative field counts, zero duplicate (settlement date, CUSIP, symbol) key groups, and zero trailer reconciliation failures. CUSIP was nonblank in 100% of sampled rows; symbol was 100% except one blank symbol in the September 2026 file (99.9985%).

## Structural break confirmed

The 2008 Q3 archive spans the SEC's 2008-09-16 reporting-threshold change:

| Settlement regime | Rows | Minimum fail quantity | Rows below 10,000 shares |
|---|---:|---:|---:|
| Before 2008-09-16 | 171,520 | 10,000 | 0 |
| On/after 2008-09-16 | 113,823 | 1 | 76,712 |

The 2004 Q2 sample also had no pre-break row below 10,000 shares. The post-break 2008 Q4 and 2009 Q2 samples contain many positive balances below 10,000. This confirms a material measurement discontinuity: a raw FTD threshold, count, or prevalence feature cannot be treated as homogeneous across 2008-09-16 without regime handling.

## Identity and history findings

- The SEC landing page describes overall coverage beginning in February 2004, but the Data.gov SEC distribution catalog's first listed quarterly archive is 2004 Q2. February–March 2004 was not verified in this audit.
- The July 2009 first-half archive contains settlement dates July 1–14. The September 2026 second-half archive begins on September 15, not September 16. Archive labels must not be converted into assumed date boundaries.
- CUSIP and ticker are both present in nearly all sampled rows, but they are not one-to-one over an entire quarter: CUSIPs with multiple symbols ranged from 11 to 301 by sample; symbols with multiple CUSIPs ranged from 5 to 37 in the modern/half-month samples and higher in older quarterly samples. These are cross-period counts and may reflect ticker changes, share classes, or ticker reuse; they do **not** establish same-day ambiguity. Effective-dated CUSIP-symbol resolution is still required.
- FTD files contain fail records, not a complete listing universe. A security absent from a file is not evidence that it was not listed; it may simply have had no reportable fail balance.
- The SEC's release schedule is approximate, not an exact per-file public-availability ledger. The current files do not provide original historical vintages or a correction history.

## Interpretation and decision

FTD is a settlement-date **balance of shares failing to deliver**, not daily short-sale volume, aggressor-side order flow, or investor identity. Fails can arise from long sales, short sales, operational and settlement processes. The data does not by itself establish naked short selling, manipulation, institutional activity, or informed trading.

**Decision:** retain SEC FTD as a feasible public event/settlement-pressure candidate, but do not call it a “smart money” signal and do not run an alpha test yet. File/schema and the 2008 threshold gate pass; point-in-time publication vintage, permanent security identity, inactive/delisted return linkage, and broad-universe coverage remain unpassed.

## Next gates

1. Add per-date CUSIP↔symbol diagnostics to distinguish same-day many-to-many cases from ticker changes/reuse across dates.
2. Establish a conservative and reproducible file-availability date, including whether corrections overwrite prior vintages.
3. Join CUSIP to a permanent, effective-dated security identifier with inactive/delisted coverage (CRSP remains the preferred return/delisting benchmark if accessible; no vendor purchase is authorized).
4. Only after those gates, preregister FTD level/change/persistence features and any interaction with short interest. Do not treat FTD as short-sale flow.

F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen. No forward returns, alpha test, vendor contact, purchase, or data acquisition occurred.
