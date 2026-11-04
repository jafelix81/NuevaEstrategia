# Phase 56 — Cboe Open-Close + Option EOD integration specification
Date: 2026-11-04
Branch: phase54-cboe-open-close-eod-feasibility
Status: preregistered research design; data acquisition and PIT gates not yet passed.

## Objective

Test whether exchange-observed participant-specific option position initiation contains incremental information about underlying returns, volatility and skew beyond frozen LTM/F80. Do not assume that Firm, Pro Customer or Customer activity is "smart money". Treat each participant category as an observed exchange capacity label.

## Data pair

1. **Cboe Open-Close EOD** — contract-level, Cboe exchanges BZX/C1/C2/EDGX, buy/sell and open/close by participant type and customer/pro-customer size buckets. EOD delivered overnight after midnight ET. C1 history starts 2005-01-03; BZX/C2/EDGX starts 2018-01-02.
2. **Cboe Option EOD Summary** — full OPRA options quotes, NBBO/size, OHLC, volume, VWAP, OI, plus optional 15:45 IV and Greeks. Product page states Jan 2012 onward. Pick-symbol selection is supported.

## Join keys and point-in-time rule

- Join on quote date, underlying symbol, option root, expiration, strike and option type. Retain exchange for Open-Close observations.
- Normalize corporate-action/adjusted option roots using a historical OCC symbology map; do not fuzzy-map roots.
- KnowledgeDate for daily EOD files is the next trading session after the file's overnight delivery. Do not use the trade date itself as the signal availability date.
- Verify actual subscription delivery timestamps before production. The public product page says overnight after midnight ET; use next-session conservative availability.
- Use Option EOD OI as the primary OI measure. Cboe Open-Close OI/total-industry fields have documented historical convention shifts and third-party provenance.

## Candidate features (pre-registered hypotheses)

For each contract and participant category (p):
- `open_net_contracts_p = open_buy_vol_p - open_sell_vol_p`
- `close_net_contracts_p = close_buy_vol_p - close_sell_vol_p`
- `net_opening_delta_p = delta_1545 * (open_buy_vol_p - open_sell_vol_p)`
- `net_closing_delta_p = delta_1545 * (close_buy_vol_p - close_sell_vol_p)`

Aggregate separately by calls/puts, expiry buckets and delta buckets. Do not combine opening and closing activity. Compute separate features for Firm, Pro Customer, Broker/Dealer, Market Maker, Customer and customer/pro-customer size buckets.

Normalize using full-OPRA option volume, OI and underlying ADTV only after field units and exchange/OPRA conventions are reconciled. Zero or invalid IV/Greek values must be excluded from volatility calculations, not treated as real zero volatility.

## Hypotheses

H1. Firm opening net delta predicts subsequent underlying returns after controlling for prior returns, volume, IV, earnings and liquidity.

H2. Pro Customer opening net delta predicts subsequent underlying returns or changes in IV/skew.

H3. Large Customer opening imbalance (>=200 contracts) differs from smaller Customer activity in predictive content.

H4. Closing flow is an unwind/cover signal and has information distinct from opening flow.

H5. Combining participant-specific opening flow with full-OPRA OI/IV/skew improves prediction beyond either source alone.

H6. Any apparent predictive relation survives controls for prior 1/5/20-day returns and volatility, distinguishing prediction from return-chasing.

These are hypotheses only. Customer includes both retail and institutional clients; Pro Customer includes professional traders and institutional participants. Neither category identifies a specific institution.

## Validation protocol

- First build a daily point-in-time panel for the exact historical F80 universe, including delisted names and ticker/root changes.
- Use 2018 onward for the four-exchange Open-Close panel. C1-only 2005–2017 may be analyzed separately, never silently pooled with all-exchange coverage.
- Chronological train/validation/OOS; no random split. Reserve at least two non-overlapping OOS regimes.
- Compare baseline F80/LTM versus F80 plus each feature, using identical exposure, rebalance timing, position sizing, costs, liquidity constraints and corporate-action treatment.
- Test fixed feature definitions and limited pre-registered parameter choices; no repeated threshold/horizon fishing.
- Evaluate risk-adjusted return, drawdown, turnover, tail loss, hit rate, calibration and incremental IC; no CAGR target.
- Use block bootstrap (time dependence), ticker-clustered inference and leave-one-ticker-out / leave-one-sector-out checks.
- Control or stratify by earnings windows, volatility regime, liquidity, optionability, market beta and prior returns.
- If an edge appears only in one participant category or one market regime, treat as fragile until replicated independently.

## Data and licensing gates before any return test

1. Obtain a Cboe quote or eligible historical sample for the frozen 335 symbols; exact pricing for pick-symbol EOD and Option EOD Calcs is not yet known.
2. Verify historical coverage by ticker/date and all required participant fields.
3. Reconcile Cboe exchange volume against full-OPRA volume; do not use total-industry ratio until units and historical conventions are validated.
4. Correct C1 OI shift through 2019-10-04, C2 OI shift through 2018-05-11, C2 total-industry-volume doubling through 2018-05-11, and C1 total-exchange-volume convention through 2019-10-04.
5. Use conservative next-session KnowledgeDate and audit missing/late files.
6. Confirm internal-use and derived-data licensing; do not redistribute raw data.

## Decision

Cboe Open-Close EOD and Option EOD Summary are the highest-priority options-data candidates after sample-schema passes. They are not yet alpha signals. OCC Volume Query remains a recent 24-month, account-type call/put aggregate with no buy/sell/open/close; it is secondary only. No forward-return test is authorized until all data, PIT, coverage and licensing gates pass.

F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen.
