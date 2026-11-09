# Phase 232 — Cboe Option Sentiment historical coverage and PIT feasibility audit

**Date:** 2026-11-09  
**Status:** Conditional data-source candidate; not admitted for PIT or alpha  
**Scope:** Public product documentation only. No sample data was purchased or downloaded.

## Executive finding

Cboe Option Sentiment is a stronger daily-flow candidate than a simple put/call ratio or a single-exchange open/close feed. The public specification describes an 80-field daily dataset built from OPRA trade-level information, with directional premium/volume fields, net option delta, open interest, IV/skew, implied borrow, trade-size buckets, days-to-expiration buckets, and OCC clearing categories.

Cboe's FAQ lists historical availability beginning **January 2012**. The product specification (v1.4, 05/25) says subscriptions provide a preliminary file after the same day's close (target 8–9 p.m. ET) and a complete file by 5–6 a.m. ET the next morning. On the first day of a subscription order, the preliminary file may arrive around the same time as the complete file and contain the same content. Historical orders are delivered as complete files at the end of the order's processing day.

This is enough to justify a data-feasibility candidate, but not enough to admit the historical series as strict point-in-time data. Historical backfill does not establish original first-receipt times, correction vintages, or the exact symbol universe present on each date. A forward subscription with immutable receipt logs would be needed to validate delivery behavior.

## Documented coverage and schema

- Historical start date: **January 2012** (Cboe DataShop FAQ).
- Frequency: daily, Monday–Friday except U.S. market holidays.
- Historical file grouping: one file per trading day.
- Product-specific subscription timing: preliminary after close on trade date, target 8–9 p.m. ET; complete file by 5–6 a.m. ET next morning.
- First subscription day: preliminary and complete may be generated around the same time with the same content.
- Historical orders are delivered as complete files at the end of the order-processing day.
- Public specification: 80 fields, version 1.4 (05/25).
- Documented options universe: U.S.-listed stock, ETF, and index options disseminated over OPRA; options on futures and non-U.S. markets are excluded.
- The FAQ says “All Symbols” includes proprietary indices such as ^SPX and ^VIX.
- Delisted-symbol continuity, complete historical symbol coverage, and the availability of every symbol in every daily file remain unverified.

### Field families

| Family | Fields | Research use | Important limitation |
|---|---|---|---|
| Basic volume/activity | call/put/total volume, trades, underlying volume | Activity surprise and participation | Not a position change |
| Directional flow | net_option_delta; call/put premium bought/sold; calls/puts bought/sold; directional_pct | Primary directional-flow hypothesis | Direction is inferred relative to midpoint; not opening/closing |
| Open interest | oi_calls, oi_puts, otm_call_oi, otm_put_oi | Position concentration/context | OCC prior-night OI; static during trade date |
| Participant category | cust_volume, firm_volume, mkt_mkr_volume | Participant-mix context | OCC clearing category, not beneficial owner or “smart money” identity |
| Trade size / tenor | size1 through size1001up; dtx1 through dtx360up | Small/large and near/far tenor decomposition | Size does not identify investor sophistication |
| Volatility / borrow | iv30, iv90, hv20, norm_25d_skew_30, vega_total, implied_borrow | Volatility, skew, borrow-stress hypotheses | Exact as-of calculation conventions need confirmation |
| Price / adjustment | spot_close, split_adj_close, spot_chg | Underlying context | Split-adjusted history may be restated; prefer raw close or independently PIT-adjusted prices |
| Exchange mix | exchange-volume fields | Venue concentration/context | Does not identify the initiating investor |

The specification says directional classifications use the trade's position relative to the midpoint: above midpoint is classified as a buy and below midpoint as a sell. Spread, late, and tied trades are excluded from the cited directional metrics. This is a vendor classification, not an independently observed beneficial-owner identity.

Cboe's own research warns that deep-ITM exercise-related activity can distort simple put/call ratios and may be nondirectional. It discusses excluding ITM volume or using customer totals for certain analyses. This is a required control, not an optional robustness check.

## PIT assessment

| Requirement | Evidence | Decision |
|---|---|---|
| Historical depth | FAQ: Jan 2012 | Documented, subject to actual backfill coverage |
| Daily cadence | Product specification | Pass |
| Same-day preliminary timing | Target 8–9 p.m. ET | Documented target, not guaranteed receipt |
| Complete-file timing | Target 5–6 a.m. ET next day | Documented target, not immutable receipt evidence |
| First subscription-day timing | Preliminary may arrive with complete file | Additional operational caveat |
| Historical first-receipt timestamps | Not supplied in public spec | Blocked |
| Correction/revision vintages | Not specified | Blocked |
| Historical active/delisted coverage | General OPRA universe description only | Partial / unverified |
| Schema sample and field completeness | Public specification only; no raw sample | Pending |
| Price and redistribution license | Not verified from public documentation | Blocked; no purchase |

The FAQ's general SFTP guidance says daily equity/option files are typically uploaded 00:05–03:00 ET the following day, but delays can push delivery into the next day after the market opens. The Option Sentiment product specification provides a more specific preliminary/complete schedule, with an additional first-subscription-day caveat. Neither document supplies actual historical first-receipt logs. Therefore, historical trade_date must not be treated as the information-availability timestamp.

**Conservative research policy:** if historical backfill is later obtained, do not use it for a strict PIT test until Cboe confirms whether backfill is identical to the originally delivered complete file and how corrections are handled. A provisional lag sensitivity of trade date +1, +2, and +3 trading sessions may be used for exploratory diagnostics only; it does not replace receipt-vintage evidence. A live subscription, if ever authorized, must log file name, hash, server timestamp, first successful receipt timestamp, and any replacement/correction.

## Pre-registered research hypotheses (not tested)

1. **Primary:** daily directional net-option-delta imbalance, normalized by underlying share volume and/or option notional, contains incremental information about 1-, 5-, and 20-session residual returns beyond prior returns, volatility, size, sector, earnings, and frozen LTM/F80.
2. **Secondary:** large-size versus small-size directional premium/volume imbalance contains incremental information after controlling for total activity and prior price movement.
3. **Secondary:** non-ITM and customer-volume measures are more robust than raw put/call ratios because exercise-related ITM volume can be nondirectional.
4. **Exploratory risk-state:** changes in 25-delta skew, IV30/IV90, and implied borrow may forecast volatility, downside risk, or squeeze risk; these are separate targets, not presumed equity-direction signals.

Do not interpret \`cust_volume\`, \`firm_volume\`, or \`mkt_mkr_volume\` as a cross-tab of the directional buy/sell fields unless the provider confirms that relationship. The public schema presents them as separate aggregates. “Customer” is not synonymous with retail, and “firm” is not synonymous with informed institutional capital.

## Modeling and validation rules

- Use only fields whose calculation timestamp and as-of convention are verified.
- Recompute rolling baselines from prior observations; do not trust the vendor's 20-day averages until inclusion/exclusion of the current day is documented.
- Do not use \`split_adj_close\` in PIT tests until adjustment vintages are established.
- Keep OI as prior-night context, not same-day opening flow.
- Control for prior 1/5/20/63-session returns, volatility, underlying volume, size, sector, earnings/events, day of week, moneyness mix, and total option activity.
- Explicitly test whether flow follows a price move (return-chasing) rather than predicts a later residual move.
- Compare against frozen \`F80_TOP20_PARTIAL50_BASELINE_C20\` / LTM with identical exposure and costs.
- Chronological train/validation/OOS only; bootstrap by time blocks and leave-one-symbol/sector-out diagnostics.
- No tuning against \`CONSUMED_NOT_PRISTINE\`; no production change absent robust independent OOS evidence.

## Decision

**Keep Option Sentiment as a high-priority conditional data candidate. Do not purchase data, do not admit it to the PIT panel, and do not claim alpha.** The documented 2012 start and rich daily field set justify obtaining a sample and written answers on receipt/revision semantics before any paid historical order is considered.
