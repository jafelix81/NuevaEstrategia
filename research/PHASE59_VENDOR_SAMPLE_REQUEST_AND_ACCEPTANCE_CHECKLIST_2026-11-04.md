# Phase 59 — Vendor sample request and acceptance checklist

Date: 2026-11-04  
Purpose: standardize no-cost samples and quotations before any options-data purchase.

## A. ORATS Near End-of-Day

Request/inspect the public full sample and, if vendor support is needed, a small historical sample covering:
- 2015, 2018, 2020, 2022, 2024, and 2026 sessions.
- A fixed cross-section of current F80 candidates plus known delisted/predecessor names.
- Full chain: every strike and expiration, including expired contracts and adjusted roots.
- Fields: trade date, ticker, root, expiration, strike, call/put, volume at snapshot, OCC OI timestamp, bid/ask and sizes, smoothed IV, Greeks, deliverable/multiplier or an explicit contract-reference join.
- Corrections/patches, file publication timestamps, and historical retention policy.
- Written confirmation that delisted underlyings remain present from 2007 and that expired contracts are not removed from historical archives.
- Individual versus professional/institutional license terms for the intended research use.

Acceptance gates:
1. At least 95% of historically optionable F80 issuer-days covered in each tested period, measured on historical membership rather than today's 335 names.
2. At least 95% of expected contract-day records have stable identifiers, expiry, strike, type, and usable quote/IV fields after documented filters.
3. Expired contracts and delisted underlyings survive sample queries.
4. OI is explicitly tagged as prior-night OCC data; no same-day OI lookahead.
5. Delivery/KnowledgeDate can be reconstructed; default to next trading session until proved otherwise.
6. No hidden survivorship restriction in ticker/contract endpoints.

## B. OptionMetrics IvyDB US + TradeFlow

Request a quote and sample covering the same dates and underlying set as ORATS. Ask for 5-minute, 30-minute, and EOD data, plus the linked IvyDB US permanent IDs.

Required vendor answers:
- Exact field dictionary and grain (trade, contract, underlying, interval).
- Definition of buyer-initiated/seller-initiated; handling of midpoint, locked/crossed markets, complex/multi-leg trades, auctions, trade conditions, corrections and late reports.
- Exact retail/institutional classification variables and thresholds; whether any label uses actual participant identity or is inferred from lot size, trade description, venue, or execution characteristics.
- Whether classification methodology is stable and point-in-time consistent back to 2016; identify any historical restatements or methodology changes.
- Whether TradeFlow includes legacy Signed Volume fields; do not buy both if redundant.
- Permanent contract/security IDs, adjusted deliverables, expired options, delisted underlyings and ticker history.
- 5/30-minute interval boundaries, snapshot timestamp, EOD file delivery time, patch/correction policy and acceptance timestamps.
- Exchange/OPRA coverage and any excluded venues/conditions.
- Professional/institutional license and internal-use restrictions.

Acceptance gates:
1. At least 95% historical F80 optionable issuer-days in each sample period.
2. At least 95% of directional volume is classifiable or explicitly labeled unknown; never coerce unknown/midpoint to buyer/seller.
3. Bid/ask/midpoint and trade-condition classifications reconcile to the supplied totals within documented tolerances.
4. Retail/institutional proxy labels have stable definitions and are never represented as account identity.
5. Next-session KnowledgeDate can be assigned without lookahead.

## C. Databento OPRA optional independent reconstruction

Use the $125 new-account historical credits only after checking current entitlement and estimated cost in the OPRA catalog. Sample:
- One liquid large-cap and one thinly traded name.
- One ETF and one delisted/predecessor symbol if available.
- One ordinary session and one high-volatility/earnings session.
- Trades plus TCBBO/CBBO-1m or other schema appropriate to the date range.

Acceptance gates:
- Trade/quote timestamp and sequence semantics documented.
- Historical degraded/gap status retained.
- OPRA symbology resolves contracts through expiry and adjustments.
- Historical data can be costed by selected schema/date before any paid request.
- This source is treated as market-wide flow reconstruction, not participant identity.

## D. Cboe Open-Close follow-up

Request a quote and a complete EOD sample for the frozen universe. Confirm:
- Exchange coverage and whether historical files cover only Cboe venues.
- Final versus preliminary data semantics.
- OCC OI and OPRA industry-volume timestamps.
- Header correction for `cust_gt_199_clsoe_buy_qty`.
- Explanation of rows where total exchange volume exceeds total industry volume.
- Historical continuity for C1 legacy formats and newer C2/BZX/EDGX series.

## E. Cross-vendor comparison protocol

Use the same trade dates, issuer set, optionable history, and contract mapping. Compare only overlapping contracts and preserve raw vendor fields. Do not compare Cboe venue-only volume to full OPRA volume without an explicit venue-share denominator.

For any later signal test:
- KnowledgeDate = next session unless a stronger historical publication timestamp is evidenced.
- Signal execution at the next session close, matching frozen F80 execution.
- Separate signed aggressor flow, opening/closing flow, participant-origin buckets, OI changes, IV/skew and raw volume.
- Control for prior returns, realized volatility, liquidity, earnings and market/sector moves.
- Identical exposure, transaction costs and missing-data rules versus F80.
- Chronological OOS, block bootstrap, issuer-clustered uncertainty and leave-one-out.
- No target CAGR; no forced positive result.

No purchase, vendor contact, forward-return calculation or strategy change is authorized by this checklist.
