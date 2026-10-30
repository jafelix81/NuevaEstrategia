# Phase 52 — Cboe options trade-by-trade (TBT) feasibility

## Objective
Evaluate whether Cboe's trade-by-trade options report can provide a materially better Smart Money signal than the public aggregate options datasets already killed for insufficient historical coverage.

## Source finding
Cboe's 2026 rule filing describes a TBT Report containing one row per options trade event with transaction time, underlying symbol, OSI contract fields, trade size/price, NBBO context, buy/sell side, opening/closing status, and participant origin: customer, professional customer, broker-dealer, or market maker. The filing states historical availability begins **2019-10-07** and describes subscription/ad-hoc access rather than a public free historical feed.

## Research value
This is materially richer than aggregate public option volume because it permits pre-registered measures such as:
- professional/customer directional imbalance;
- opening-vs-closing activity;
- participant-origin imbalance;
- premium/notional concentration;
- contract-level IV/strike/expiry context when reconstructable from the contract fields;
- interactions with subsequent underlying returns and volatility.

These measures could test an economically specific hypothesis about informed positioning rather than assuming that high option volume means smart money.

## Feasibility constraint
The SEC/FINRA/public Cboe datasets currently used in the project do not provide an equivalent historical participant-level options flow panel. Cboe's filing states a proposed subscription fee of **$12,000/month ($144,000/year)** and **$8,000/month** for ad-hoc historical requests, with availability beginning 2019-10-07. Therefore this candidate is **commercially feasible but not currently data-access feasible within the project**.

## Gate
STATUS: PARKED — COMMERCIAL DATA ACCESS REQUIRED

No alpha testing is authorized. Do not approximate TBT participant-origin flow with inferior aggregate public option-volume data.

## Reopen condition
Reopen only if licensed historical TBT access becomes available, or an independent dataset with equivalent participant-origin, side, open/close, contract and timestamp fields becomes available with adequate PIT coverage.

## Source
Cboe rule filing SR-CBOE-2026-010, describing the TBT Report and historical availability from 2019-10-07.
