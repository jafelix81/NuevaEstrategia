# Phase 211 — Form 144/Form 4 EDGAR acceptance clock and PIT feasibility audit

**Date:** 2026-11-08  
**Disposition:** filing-level event clock feasible in a verified five-pair pilot; full-panel PIT, feature admission and alpha remain **NOT ADMITTED**.  
**Control:** `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen.

## Executive decision

Phase 210 established 521 exact date-and-share Form 144/Form 4 document links in one 2026 Q3 sample. Phase 211 resolves an important part of the event-timing question: SEC EDGAR filing-detail/header records expose `ACCEPTANCE-DATETIME`, and current SEC guidance states that Form 144 is transmitted concurrently with placing the broker sell order or executing directly with a market maker. No waiting period is required when the form is transmitted concurrently with the order (CFI 136.05, updated September 25, 2026); the separate CFI 136.09 interpretation (March 4, 2011) explains that “concurrently” means the same day.

This changes the economic interpretation. Form 144 is not merely a remote intention to sell. It is a **contemporaneous sell-order or direct-execution notice candidate**. The two legal routes must be separated: a broker route is filed when the sell order is placed and may precede execution; a direct market-maker route is filed at execution and may be contemporaneous with an already completed sale. The current `broker_or_market_maker` field does not itself encode which route applies. Form 144 still does not prove that the proposed quantity was ultimately sold: SEC staff explicitly says no amendment is required solely because the person does not sell the securities.

A five-pair cross-issuer pilot traced exact Phase 210 links to SEC filing-detail/header pages:

- All five Form 144 filings were accepted on the approximate sale date.
- Three were accepted during the regular session and two after the 16:00 ET close.
- In all five cases, the matched Form 4 was accepted after the first subsequent regular-session open.
- Therefore Form 4 is an ex-post confirmation/label, not information available at the first conservative trading opportunity after Form 144.

The practical no-lookahead rule is to parse the EDGAR `ACCEPTANCE-DATETIME` and use the **first regular-session open strictly after that timestamp** as the earliest conservative executable event time. Do not use the acceptance second as an intraday fill timestamp: SEC guidance establishes same-day dissemination, but the pilot does not establish exact dissemination latency or actual order execution venue.

This is a filing-level PIT feasibility result, not panel admission. The five examples are not a representative coverage audit, and the repository still lacks acceptance-header vintages for every Form 144/Form 4 accession.

## 1. Regulatory/event semantics

Official SEC sources establish the following:

1. SEC Corporation Finance Interpretation 120.01 says Form 144 must be transmitted concurrently with either placement of a sell order for a brokerage transaction or execution directly with a market maker; adoption of a 10b5-1 plan itself is not the trigger. The notice is effective for a maximum of three months. [SEC Exchange Act Rules — CFI 120.01](https://www.sec.gov/rules-regulations/staff-guidance/corporation-finance-interpretations/exchange-act-rules)
2. SEC Securities Act Rules CFI 136.05, updated September 25, 2026, says no waiting period is required between placing the broker order and execution if Form 144 is transmitted concurrently. CFI 136.09 says “concurrently” means on the same day. [SEC Securities Act Rules — CFI 136.05/136.09](https://www.sec.gov/rules-regulations/staff-guidance/corporation-finance-interpretations/securities-act-rules)
3. CFI 136.01 says no amendment is required solely because the person does not sell the securities. Thus a missing Form 4 match cannot be classified as an unexecuted notice without additional evidence.
4. SEC's electronic Form 144 guide says electronic filing became mandatory for Form 144s relating to reporting-company issuers on April 13, 2023; EDGAR accepts filings from 06:00 to 22:00 ET on business days, and Form 144 submissions accepted in that window are deemed filed and disseminated the same day. [SEC File Form 144 Electronically](https://www.sec.gov/submit-filings/filer-support-resources/how-do-i-guides/file-form-144-electronically)
5. The SEC EDGAR Filer Manual Volume II (March 2025, v74) explicitly lists Forms 3/3-A, 4/4-A, 5/5-A, 144 and 144/A among submission types that retain the received-date filing date after 17:30 ET and are disseminated until 22:00 ET. [SEC EDGAR Filer Manual Volume II v74](https://www.sec.gov/files/edgar/filermanual/archive/efmvol2-v74.pdf)
6. The SEC Form 144 guide distinguishes the reporting-person CIK (Filer CIK) from the issuer CIK, and says not to use the filing-agent CIK as the issuer CIK. It also says the form identifies each broker or market maker expected to participate, with a separate entry for each broker/market maker. [SEC File Form 144 Electronically](https://www.sec.gov/submit-filings/filer-support-resources/how-do-i-guides/file-form-144-electronically)

Consequences for feature design:

- Event time is the Form 144 acceptance/public-disclosure event, not the plan-adoption date.
- The proposed units, class, broker/market maker and seller relationship are event-time attributes, subject to parsing and class validation.
- A 10b5-1 adoption date is historical context; it does not mean the current sell order was public at plan adoption.
- Form 4 code S and exact share/date matches are ex-post validation. Form 4 must not be backfilled into the Form 144 feature row.
- No Form 4 match is not equivalent to no sale: Form 144 need not be amended when a sale does not occur, and Form 4 coverage is not identical to Form 144 filer coverage.

## 2. Five-pair SEC acceptance-time pilot

The five exact links below were selected across five issuers from the 521-edge Phase 210 exact graph and individually traced to SEC EDGAR filing-detail/header records. All timestamps are displayed in Eastern Time; the sample dates are during EDT (UTC-04:00).

| Issuer | Approx. sale date | Shares | Named intermediary (route not classified) | Form 144 accepted (ET) | First subsequent session open (ET) | Matched Form 4 accepted (ET) |
|---|---:|---:|---|---|---|
| Pinterest (PINS) | 2026-07-01 | 46,875 | Charles Schwab & Co., Inc. | 2026-07-01 16:07:20 | 2026-07-02 09:30 | 2026-07-02 19:56:02 |
| Charles Schwab (SCHW) | 2026-07-29 | 95,450 | The Charles Schwab Corporation | 2026-07-29 11:10:09 | 2026-07-30 09:30 | 2026-07-30 20:57:55 |
| Snowflake (SNOW) | 2026-07-21 | 10,315 | Fidelity Brokerage Services LLC | 2026-07-21 10:15:46 | 2026-07-22 09:30 | 2026-07-22 19:51:39 |
| Arista Networks (ANET) | 2026-08-25 | 13,809 | Fidelity Brokerage Services LLC | 2026-08-25 11:44:04 | 2026-08-26 09:30 | 2026-08-27 18:21:50 |
| Sunrun (RUN) | 2026-08-03 | 50,000 | Charles Schwab & Co., Inc. | 2026-08-03 16:08:54 | 2026-08-04 09:30 | 2026-08-04 10:33:00 |

### Sample-level controls

- Form 144 accepted on approximate sale date: **5/5**.
- Form 144 accepted between 09:30 and 16:00 ET: **3/5**.
- Form 144 accepted after the 16:00 ET regular close: **2/5**.
- Matched Form 4 accepted after the first subsequent regular-session open: **5/5**.
- Matched Form 4 available by that conservative first-session open: **0/5**.

The SEC filing detail pages show the `Accepted` time for the pairs. For the Pinterest pair, the raw SEC header files also expose the exact `ACCEPTANCE-DATETIME` field directly:

- [PINS Form 144 header](https://www.sec.gov/Archives/edgar/data/1506293/000192109426000697/0001921094-26-000697-index-headers.html)
- [PINS Form 4 header](https://www.sec.gov/Archives/edgar/data/1506293/000177391426000012/0001773914-26-000012-index-headers.html)

Other SEC filing-detail pages in the sample:

- [SCHW Form 144](https://www.sec.gov/Archives/edgar/data/316709/000194984626000451/0001949846-26-000451-index.htm) · [SCHW Form 4](https://www.sec.gov/Archives/edgar/data/316709/000092373826000031/0000923738-26-000031-index.htm)
- [SNOW Form 144](https://www.sec.gov/Archives/edgar/data/1640147/000195917326005295/0001959173-26-005295-index.htm) · [SNOW Form 4](https://www.sec.gov/Archives/edgar/data/1640147/000140234826000016/0001402348-26-00016-index.htm)
- [ANET Form 144](https://www.sec.gov/Archives/edgar/data/1596532/000195917326006426/0001959173-26-006426-index.html) · [ANET Form 4](https://www.sec.gov/Archives/edgar/data/1596532/000159653226000216/0001596532-26-000216-index.htm)
- [RUN Form 144](https://www.sec.gov/Archives/edgar/data/1469367/000192109426000789/0001921094-26-000789-index.htm) · [RUN Form 4](https://www.sec.gov/Archives/edgar/data/1469367/000146936726000055/0001469367-26-000055-index.html)

This is a feasibility pilot, not an estimate of the full-panel timing distribution. It does not show that all Form 144s execute, nor that the notice remains unfilled until the next session.

## 3. Conservative PIT policy

For every Form 144 accession:

1. Retrieve the immutable SEC `index-headers.html` (or the filing header record) and parse `ACCEPTANCE-DATETIME`.
2. Store the original header bytes and SHA-256; never overwrite a prior vintage.
3. Interpret the timestamp in `America/New_York` (EDGAR Eastern Time), preserving daylight-saving rules.
4. Do not assume the acceptance second equals the exact first public dissemination second.
5. For a daily strategy, use the first regular-session open strictly after acceptance as the conservative event execution boundary. If acceptance occurs after the open, this will ordinarily be the next trading session; if it occurs premarket, the same day's open can be used only after calendar and dissemination controls pass.
6. Keep Form 4 acceptance as a separate later event. It may validate a proposed-sale notice ex post but must never be used to make the Form 144 feature available earlier.
7. Treat amendments as new events at their own acceptance times. Do not overwrite the original notice or backdate corrected fields.

The included parser (`phase211_edgar_acceptance_clock.py`) extracts the EDGAR accession, submission type and acceptance timestamp, and maps it to a supplied exchange-session calendar. Its tests cover Form 144, Form 4/A, missing timestamps, premarket, intraday and at-open boundary cases.

## 4. Revised economic hypothesis

The primary hypothesis is now split by route:

> **H1 — Broker order placement:** when the named intermediary is a broker and Form 144 is transmitted with order placement, does the notice predict incremental supply pressure or negative abnormal returns after the first executable session open, conditional on proposed size relative to point-in-time liquidity, class, seller type, 10b5-1 status and prior return/volume?

> **H2 — Direct market-maker execution:** when the notice is transmitted with direct execution to a market maker, does it behave as a contemporaneous completed-trade disclosure rather than a forward supply signal? This route should be analyzed separately and may have little or no post-event lead.

Required controls before testing:

- Resolve each named intermediary to broker versus direct market-maker route before testing; quarantine ambiguous entities.
- Separate plan and non-plan notices; do not infer discretion from a missing plan date.
- Use point-in-time ADV, float and shares outstanding; reject the Form 144 `shares outstanding` field until its scale anomalies are independently resolved.
- Separate exact class-family links, unresolved/conflicting classes and fallback matches.
- Do not call the 521/570 document links a universal conversion rate. Form 144 filers are not identical to Form 4 reporting owners, and no-sale notices need not be amended.
- Control for pre-event returns and volatility to distinguish incremental supply information from return-chasing or routine diversification.
- Use the next-session-open clock, then evaluate multiple holding horizons without a pre-imposed minimum or maximum.
- Compare incremental information against frozen LTM/F80 with identical exposure, costs, turnover and risk constraints. Use chronological validation, bootstrap/LOO and a new prospective final holdout after all feature and model-selection rules are frozen.

## 5. Admission decision and blockers

**Admitted:** filing-level acceptance-clock method as a feasible PIT reconstruction path; Form 144 event semantics as a contemporaneous sell-order notice hypothesis.

**Not admitted:** full-panel PIT, feature, alpha or production use.

Remaining gates:

- Bulk-recover and SHA-256 every Form 144 acceptance header in the 21,634-row panel, with explicit missing/error counts and amendment chains.
- Recover adjacent-quarter Form 4 data and acceptance headers so the one-quarter matching result can be replicated chronologically.
- Validate EDGAR dissemination policy and any exceptional/rejected/suspended filings at the accession level.
- Resolve effective-dated issuer/security-class identifiers and point-in-time universe membership.
- Add an exchange calendar and reproducible next-session-open mapping.
- Preserve all vintages; do not use current corrected filings to reconstruct what was known historically without their original timestamps.

The automated SEC retrieval workflow remains blocked because repository secret `SEC_CONTACT_EMAIL` is absent. No SEC requests were made by that blocked workflow. An authorized contact email must be configured in GitHub Actions before the bulk header-recovery workflow is dispatched.

## 6. Controls

- No forward-return, event-study, alpha, bootstrap/LOO or OOS return test was run.
- No holdout was used. The legacy holdout remains `CONSUMED_NOT_PRISTINE`.
- `F80_TOP20_PARTIALL50_BASELINE_C20` is frozen.
- No production, universe or portfolio change was made.
- No data were purchased and no vendor was contacted.

## Reproducibility

- Sample and accession manifest: `research/phase211_form144_form4_acceptance_clock_pilot.json`
- Parser: `research/phase211_edgar_acceptance_clock.py`
- Tests: `research/test_phase211_edgar_acceptance_clock.py`
- Local test result: **8/8 passed**.
- Phase 210 linkage source: `research/phase210_form144_form4_permutation_placebo_audit_result.json` (521 exact links; 481 class-family agreements; 40 class conflicts/unresolved).
