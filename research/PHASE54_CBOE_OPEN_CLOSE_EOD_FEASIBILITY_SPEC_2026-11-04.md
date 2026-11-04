# Phase 54 — Cboe Open-Close EOD feasibility
Date: 2026-11-04
Branch: phase54-cboe-open-close-eod-feasibility
Status: promising candidate; sample schema validation pending.

## Why this is distinct from the parked Cboe TBT line

The Cboe Open-Close EOD Summary is not the $12,000/month trade-by-trade feed. It is a contract-level EOD aggregation that classifies option activity by participant category, buy/sell action, and opening/closing position. This could expose a more direct and testable hypothesis about position initiation than aggregate options volume or OI alone.

Official product page:
https://datashop.cboe.com/cboe-options-open-close-volume-summary

Official EOD specification v1.3 (2025-11-10):
https://datashop.cboe.com/documents/Open_Close_EOD_Spec_v1.3.pdf

Official Cboe fee schedule (April 21, 2026):
https://cdn.cboe.com/resources/membership/Cboe_FeeSchedule.pdf

## Documented data properties

- Exchanges: C1, C2, BZX, EDGX.
- EOD history: C1 from 2005-01-03; BZX/C2/EDGX from 2018-01-02.
- Final subscription files are typically delivered 00:30–01:00 US Eastern the next morning.
- One zipped CSV per trade date per exchange.
- Contract-level fields include underlying, option root, expiration, strike, call/put, total exchange volume, total industry volume, open interest, previous open interest, and participant-specific buy/sell/open/close volume and trade counts.
- Participant categories: Firm, Broker/Dealer, Market Maker, Customer and Professional Customer. Customer and Professional Customer are further divided into trade-size buckets (<100, 100–199, >=200 contracts).
- The EOD report includes both sides of each exchange trade in total_exchange_vol.
- The dataset is proprietary; raw data is internal-use only. Redistribution of raw data is prohibited; external distribution of derived data requires additional licensing/approval.

## Important historical conventions

- C1 OI values were shifted one day ahead through 2019-10-04.
- C2 OI values were shifted one day ahead through 2018-05-11.
- BZX and EDGX OI use a consistent start-of-day convention.
- C2 total industry volume was doubled through 2018-05-11.
- C1 Global Trading Hours coverage starts 2023-12-11.
- Total industry volume and OI are sourced from third-party vendors as best-effort value-adds, not directly from Cboe exchanges.

These conventions must be normalized or excluded before building any OI-derived feature. A clean initial research window should begin after 2019-10-04 if using C1 OI, and after 2018-05-11 for C2 OI.

## Cost feasibility

The April 21, 2026 Cboe fee schedule lists EOD Open-Close historical download pricing at $600 per month for 1–4 years and $300 per month for 5+ years; daily updates are listed at $600/month. The schedule also lists a free trial of up to six months of EOD historical data for eligible first-time users. The fee table's exact total for a 335-symbol pick-list and a multi-year order must be confirmed in the DataShop cart or directly with Cboe; do not assume the full-market figure scales linearly.

## Hypotheses to preregister only after data gates

- Firm opening net buy volume (open buys minus open sells), scaled by contract OI, underlying ADTV, and total industry volume.
- Professional-customer opening imbalance, separated from retail-sized customer buckets.
- Large customer opening imbalance (>=200 contracts) versus smaller customer activity.
- Closing flow as a distinct unwind/cover signal rather than mixing with opening flow.
- Whether participant imbalances lead underlying returns or simply chase prior price moves / volatility.

Do not label Firm or Professional Customer as institutional smart money by default. They are exchange capacity classifications. Treat every interpretation as a hypothesis.

## Required next gates

1. Download and inspect public sample ZIP; verify headers and non-null coverage of buy/sell/open/close fields.
2. Obtain a six-month first-time trial or price quote for the frozen 335 symbols (or a representative stratified subset) and measure ticker/date coverage.
3. Quantify Cboe exchange share versus total industry volume by ticker/date, with caveats for the third-party total-industry field.
4. Reconstruct exact KnowledgeDate. For subscription EOD files use next-session availability conservatively; verify historical delivery conventions.
5. Build a historical point-in-time ticker/option-root map, including delisted securities and corporate-action roots.
6. Only then test incremental information versus frozen LTM/F80 with chronological OOS, identical exposure/costs, bootstrap, issuer-clustered inference and LOO.

No forward returns or alpha test is authorized by this sample-schema pilot. F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen.
