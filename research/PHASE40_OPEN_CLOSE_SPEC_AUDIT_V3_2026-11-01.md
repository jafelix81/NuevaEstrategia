# Phase 40 — Open-Close EOD specification/PIT audit V3 — 2026-11-01

## Status
**FEASIBILITY STRENGTHENED; ACTUAL HISTORICAL SAMPLE/COVERAGE GATE STILL OPEN. No alpha authorized.**

## Fresh vendor verification
Cboe DataShop's current Open-Close Volume Summary page and EOD specification confirm that the product is directly relevant to the Smart Money hypothesis because each option series is bucketed by participant capacity, action, and opening/closing position. The current product page states coverage across C1, C2, BZX and EDGX and provides EOD plus intraday products.

Current documented EOD historical starts:
- C1: 2005-01-03
- BZX/C2/EDGX: 2018-01-02

The EOD product is delivered overnight after midnight U.S. Eastern. The EOD specification states that subscriptions normally receive a preliminary file around 00:30–01:00 ET and a final file shortly thereafter; the final file uses OCC-sourced authoritative values for open interest and total industry volume. Therefore, for a next-session trading rule, the final EOD file has a defensible PIT availability timestamp. It must not be used for a same-session close decision unless a separate historical delivery timestamp proves availability before that decision.

## Field-level confirmation
The current v1.3 EOD specification contains:
- underlying_symbol, option symbol, expiry, strike, call/put, DTE and series type;
- total exchange volume, total industry volume, open interest, previous open interest and previous close;
- Firm buy/sell opening/closing quantities and volume;
- Broker/Dealer buy/sell opening/closing quantities and volume;
- Market Maker buy/sell quantities and volume;
- Customer opening/closing buy/sell quantities and volume split into <100, 100–199, and >=200 contracts;
- Professional Customer opening/closing buy/sell quantities and volume split into the same size buckets.

The specification maps capacity codes as follows: Customer=C; Professional=U/W; Broker-Dealer=B; Market Maker=M/N; Firm=F/L/J.

This is materially better than a generic call/put ratio because it permits pre-specified tests of directional new positioning by participant class and size without inferring participant identity from trade size alone.

## Critical PIT/data-version controls
1. C1 has a pre-2011 legacy file format; the parser must branch explicitly at the documented 2011 format break.
2. C1 open-interest/previous-open-interest values are documented as shifted one day ahead through 2019-10-04; C2 through 2018-05-11. BZX/EDGX use a consistent start-of-day convention. These breaks must be corrected before feature construction.
3. The preliminary file may differ from the final file because OPRA values can later be replaced by OCC-authoritative open interest and total-industry-volume values. Historical research must use the final file whenever it was available before the simulated decision timestamp.
4. The product page states that raw data are proprietary/internal-use and may not be redistributed. The repo should therefore store only derived research outputs/metadata unless licensing permits raw retention.
5. The vendor page currently exposes a downloadable sample, but the web client cannot retrieve the ZIP sample because it is served as application/x-zip-compressed. This is a tooling limitation, not evidence that the historical dataset is unavailable.

## Pre-specified candidate features for the first eventual alpha test
These are hypotheses only and must not be optimized on OOS results:

A. **Directional opening imbalance by Customer/Pro-Customer**
`open_buy_vol - open_sell_vol`, normalized by total industry volume or underlying ADV.

B. **New-position imbalance**
Use opening buy/sell volume for Customer and Pro-Customer, separately from closing flow, to test whether newly initiated directional exposure predicts subsequent underlying returns.

C. **Large-contract professional/customer opening flow**
>=200-contract buckets, normalized by total participant opening volume and underlying liquidity. This is not assumed to be “smart money”; it is a test of whether the size bucket adds incremental information.

D. **Flow + OI confirmation**
Combine opening imbalance with prior/start-of-day OI changes, using only OI that is demonstrably available ex ante.

E. **Participant disagreement**
Customer/Pro-Customer directional flow versus Market Maker directional flow, tested as a possible liquidity-taking versus liquidity-provision state rather than as an assumption about informed trading.

All candidate features must first be residualized/controlled for underlying return, volatility, volume and option activity so apparent predictiveness is not simply return-chasing.

## Required data-purchase/coverage audit
Before any alpha test:
1. Obtain actual historical EOD files for multiple windows, including at least one pre-2011 C1 period and multiple post-2018 periods.
2. Map underlying symbols to the frozen 335-name universe using historical ticker/name-change mappings.
3. Quantify per-symbol and per-date coverage, including delisted names where the vendor provides them.
4. Verify that final-file timestamps are reproducible and precede the intended simulated next-session decision.
5. Validate the 2011 C1 schema break and historical OI convention corrections on known series.
6. Freeze the feature schema and normalization rules before looking at returns.

## Decision
Open-Close EOD remains the highest-priority options data candidate. The new vendor specification strengthens the economic and PIT case, but **no predictive claim has been made and no alpha test is authorized** until actual delivered historical files pass the universe-coverage and timestamp audit.

`F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen.
