# Phase 268 — SEC Form SHO public-data availability, aggregation and PIT gate

**Audit date:** 2026-11-10 UTC  
**Repository:** `jafelix81/NuevaEstrategia`  
**Branch:** `phase231-cboe-option-quotes-full-row-reparse`  
**Scope:** Exchange Act Rule 13f-2 / Form SHO, with Rule 10c-1a as a separate adjacent future source.

## Executive decision

**Keep Form SHO on the future-source watchlist; do not build a capture workflow or run an alpha test now.**

The SEC's current temporary exemption delays compliance with Rule 13f-2 and Form SHO until **2028-01-02**. The first reporting period is January 2028, with the first filing deadline on **2028-02-14**. The SEC's original final rule says aggregated public dissemination begins three months after the compliance date; applying the current compliance date implies an initial public-data window around **April 2028**, but the exact first publication date has not been announced and must be rechecked closer to implementation.

The public output is **aggregated by equity security**, not manager-attributed. Individual Form SHO submissions are deemed subject to confidential treatment under Rule 83. The public aggregate is therefore not a direct institutional-identity feed. It may still be useful as a delayed measure of large-manager short crowding and daily net position activity.

No historical public Form SHO panel exists to backfill as of this audit. There is no historical PIT sample, no return test, and no alpha admission.

## 1. Current legal and publication calendar

- SEC Order, Release 34-104303, dated 2025-12-03, grants temporary exemptive relief from Rule 13f-2/Form SHO compliance through **2028-01-02**.
- The first reporting period is January 2028. Rule 13f-2 requires filing within 14 calendar days after month-end, yielding a first filing deadline of **2028-02-14**.
- The 2023 final rule says the SEC will begin publishing aggregated data three months after the compliance date. The precise first public release date is not yet verified; do not treat 2028-04-02 as a guaranteed publication date.
- Under the regular cadence, the SEC expects aggregated data within one calendar month after the end of each reporting month. The final rule's example is October data published no later than November 30.
- Form SHO publication may be amended/restated; the SEC planned to publish the latest period plus prior 12 months updated for amendments.

## 2. What the public data would and would not reveal

The form contains gross end-of-month short-position information and daily net activity by settlement date during the reporting month. The SEC plans to aggregate across all reporting managers for each reported equity security.

It does **not** publish manager names or individual manager positions. All information included in Form SHO is deemed subject to a confidential treatment request under 17 CFR 200.83. The SEC notes that in rare cases, where only one manager contributes to an aggregate, market participants might infer identity from outside information; that is not a reliable identity field and must not be treated as one.

The feature concept is therefore:
- aggregate large-manager gross short crowding;
- aggregate daily net position changes;
- potential downside-risk, crowding or squeeze-vulnerability context.

It is not:
- a named hedge-fund position feed;
- a complete measure of all short interest;
- a daily trade-by-trade short-sale feed;
- a substitute for FINRA short interest or short-volume data.

## 3. Threshold-censored universe

Reporting-company securities are reportable when a manager's monthly average gross short position is at least **$10 million OR 2.5% of shares outstanding**.

For non-reporting-company securities, the threshold is a gross short position of at least **$500,000 on any settlement date** during the month.

This is not a complete universe panel. A missing security-month can mean no manager met the threshold, not zero short interest. Thresholds and reporting-manager participation can change from month to month. Any future dataset must preserve explicit absence separately from numeric zero.

## 4. Timeliness, staleness and data quality

Managers file within 14 calendar days after month-end; the SEC expects public aggregation within one calendar month after month-end. The SEC's final-rule analysis found that historical Form SH positions meeting the relevant thresholds remained above threshold for an average of 9.85 days after month-end, with methodological caveats. The SEC expects most, but not all, positions leading to Form SHO reports to have closed by the time aggregated data are released.

That makes Form SHO a delayed state/activity feature. It may be more useful for persistent crowding or risk context than for identifying a fresh entry signal. The hypothesis must be tested rather than assumed.

The SEC also states that EDGAR's filing validations check technical errors, not economic accuracy. Managers must amend and restate when they discover errors, and the SEC planned to republish the latest period with prior 12 months updated for amendments. A future capture must preserve every public vintage, first-receipt timestamp and raw hash; never overwrite a prior release.

## 5. Adjacent Rule 10c-1a securities-lending data

The same SEC exemptive order delays Rule 10c-1a reporting compliance until **2028-09-28** and public dissemination compliance until **2029-03-29**. This is a separate future securities-lending source, not Form SHO. Its publication semantics and fields need a separate audit before any feature is proposed.

## 6. Research disposition

| Gate | Decision |
|---|---|
| Public data available as of 2026-11-10 | No |
| Historical public backfill | No |
| Manager identity available publicly | No |
| Security-level aggregate | Planned |
| Universe coverage | Threshold-censored |
| Strict historical PIT | Not possible |
| Prospective PIT after first public receipt | Potentially possible |
| Historical alpha / OOS | Not tested |
| Production / F80 change | None |

**Future hypotheses (not admitted):**
1. Large-manager aggregate short crowding may add information about subsequent downside risk or squeeze vulnerability.
2. Daily net changes may contain incremental information beyond FINRA short interest and short-volume features.
3. The signal may be more useful as a risk/volatility overlay than as a directional stock selector.

When data become public, test only from the actual first-publication receipt time, with raw immutable vintages, effective-dated security identity, threshold/missingness handling, and chronological OOS. Compare against frozen LTM/F80 and existing FINRA features under identical exposure and costs, with bootstrap/LOO and independent OOS. Do not reuse the consumed legacy holdout.

**Decision:** `FUTURE_AGGREGATE_SHORT_SIDE_CANDIDATE_NOT_YET_AVAILABLE`. No capture workflow, backtest, purchase, vendor contact, production change, universe change, capital change, or F80 change.

## 7. Official sources

1. SEC, Order Granting Temporary Exemptive Relief, Release 34-104303 (2025-12-03): https://www.sec.gov/files/rules/exorders/2025/34-104303.pdf
2. SEC, Final Rule 34-98738, *Short Position and Short Activity Reporting by Institutional Investment Managers* (2023-10-13; Federal Register 2023-11-01): https://www.sec.gov/files/rules/final/2023/34-98738.pdf

Relevant final-rule sections:
- publication startup and cadence: pp. 140 and 67–70;
- confidential treatment: pp. 103–105;
- EDGAR validation and amendments: pp. 102–106;
- staleness and threshold duration: pp. 211–214;
- reporting thresholds: pp. 36–45 and 299–304.

## 8. Reproducibility

- Code: `phase268_sec_form_sho_future_publication_gate.py`
- Tests: `test_phase268_sec_form_sho_future_publication_gate.py`
- Hosted workflow: `.github/workflows/phase268_sec_form_sho_future_publication_gate.yml`
- Output: deterministic JSON artifact from the hosted workflow.

This phase is a legal/source-feasibility gate only. It contains no market data, return labels, alpha calculation or holdout use.
