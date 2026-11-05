# Phase 100 — FINRA weekly ATS/off-exchange revalidation

Date: 2026-11-05  
Status before execution: **corrected actual-file validation pending**  
Scope: data feasibility only; no returns, alpha test, vendor contact, or purchase.

## Why revalidate Phase 38

Phase 38 retrieved 959,997 rows across five historical weeks and both NMS tiers, with 333/335 frozen-list symbols seen in aggregate and no API errors. That is promising, but its coverage statistic pooled all weeks and counted any row carrying a symbol. It did not establish per-week coverage of symbol-level aggregate records, verify every returned row against the requested week/tier, report summary-type composition, or quantify publication/update-date quality. Phase 100 closes those specific audit gaps; it is not a duplicate of a running job (Phase 38 is complete).

## Fixed sample

Historical weeks, all within FINRA's documented rolling historic window (one to five years before the current date):

- 2022-01-03
- 2023-01-09
- 2024-01-08
- 2025-01-06
- 2025-10-20

Query both NMS tiers, T1 and T2. Preserve exact issueSymbolIdentifier; do not strip share-class suffixes or fuzzy-map tickers.

## Required validations

1. Exact row-level agreement between requested historicalWeek / tierIdentifier and returned weekStartDate / tierIdentifier.
2. Per-partition row counts, unique symbols, summary-type composition and pagination hashes.
3. Separate symbol-level aggregates (ATS_W_SMBL, OTC_W_SMBL) from firm-level and volume-statistic rows. Do not use firm-level rows as if they were independent securities.
4. Measure legacy F80-335 overlap separately for ATS, non-ATS OTC and their union, for each week and tier. This is a comparability diagnostic only; 335 is not the Smart Money research-universe ceiling.
5. Validate non-negative share/trade quantities and duplicate keys.
6. Parse initialPublishedDate and lastUpdateDate; report publication lags by tier and how often the latest data-update date is later than first publication.
7. Keep first-publication date separate from latest-update date. A current historical response with no archived original vintages/correction ledger is not automatically point-in-time safe.

## Pre-registered data gates

- No request errors or row-level partition mismatches.
- Symbol-level aggregate rows exist in every sampled week/tier.
- At least 90% exact 335-name union coverage in each sampled week (legacy comparison only; coverage is combined across T1 and T2).
- At least 99% of symbol-level rows have valid initialPublishedDate.
- Publication lag is not earlier than 14 calendar days for T1 or 28 calendar days for T2; later dates are retained and reported.
- Duplicate keys and post-publication update dates are reported, not silently discarded.

Passing these gates means **coverage/schema feasibility**, not full PIT-vintage proof. If current values were updated after first publication and original vintages are unavailable, the economic test remains conditional.

## Economic interpretation

FINRA weekly ATS and non-ATS OTC aggregates measure reported off-exchange activity, not trade aggressor direction, beneficial owner, or investor sophistication. ATS activity is not automatically institutional information. A later hypothesis may examine changes in ATS share within reported off-exchange volume, abnormal weekly activity, and venue concentration, but only after the PIT and security-identity gates.

## Separate FINRA short-flow decision

Phase 20C's completed walk-forward diagnostic is reviewed in the accompanying Phase 100 report. The existing short-volume-ratio feature-selection implementation is not promoted; the six final holdout dates remain unused because the pseudo-OOS evidence is weak and horizon-unstable.

## Frozen control and scope

F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen. The 335-name list is used here only to reproduce the legacy coverage statistic. No forward returns, strategy changes, broad-universe claims, vendor purchase, or data acquisition are authorized by this phase.


## Implementation clarification from the FINRA schema audit

The FINRA API schema distinguishes four symbol-bearing summary types
(\`ATS_W_SMBL\`, \`ATS_W_SMBL_FIRM\`, \`OTC_W_SMBL\`, \`OTC_W_SMBL_FIRM\`)
from firm-level and volume-statistic types
(\`ATS_W_FIRM\`, \`OTC_W_FIRM\`, \`ATS_W_VOL_STATS\`, \`OTC_W_VOL_STATS\`).
The latter legitimately omit \`issueSymbolIdentifier\`; their absence of a
symbol is not a row-integrity error. Unknown summary types remain a hard error.

The historic endpoint is large. The implementation uses FINRA asynchronous
requests, polls no more than once per minute, downloads the expiring result
immediately, and reconciles retrieved rows to the API \`Record-Total\` header.
This avoids silently treating a 3 MB synchronous payload truncation as a
complete page. The historic endpoint's supported query keys remain only the
historical-week and tier partition values; no sorting or additional filters
are introduced.

\`lastReportedDate\` is the date a firm last sent an update to underlying data
contributing to the aggregate. It is not a trade/activity date. It is reported
separately from \`initialPublishedDate\` and \`lastUpdateDate\`.
