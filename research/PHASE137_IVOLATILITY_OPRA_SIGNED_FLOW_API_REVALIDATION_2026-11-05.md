# Phase 137 — IVolatility OPRA signed-flow API revalidation

**Date:** 2026-11-05  
**Status:** **PROMOTE TO TOP-TIER CONDITIONAL SIGNED-FLOW CANDIDATE**. Current product and historical-depth claims are publicly documented; actual sample integrity, point-in-time vintages, broad PIT universe coverage, methodology details, licensing and bulk feasibility remain unverified. No API account/trial, vendor contact, purchase, return test or production change.

## 1. Material new development

IVolatility announced on **2026-10-14** three new API endpoints for US equity options:

- `/equities/intraday/options-net-flow`: OPRA trades signed against NBBO at execution, with midpoint trades left unclassified; daily or minute aggregates; call/put buys and sells; net premium and net delta; customer gamma and vega; filters for sweeps, trade size, 0DTE, multi-leg and execution type. Advertised history begins in **2015**.
- `/equities/intraday/options-exposure`: current option-chain-derived dealer/exposure levels, including gamma flip, call/put walls, net dealer gamma, DEX, vanna and charm.
- `/equities/intraday/options-exposure-series`: minute or daily history of those derived levels, advertised from **2014**.

The announcement says the new endpoints are included in every API plan and that daily flow/levels are available the same evening. Official announcement: https://www.ivolatility.com/news/3169.

This is a material update to the older Phase 59–63 vendor screen and Phase 86 design: the signed-flow endpoint is now publicly described as an available current API feature, rather than only an older trade-level database guide.

## 2. Source feasibility and what is actually established

| Gate | Public evidence | Current adjudication |
|---|---|---|
| Historical depth | Signed-flow endpoint advertised from 2015 | PASS — advertised history only |
| Market source | OPRA trades signed against NBBO at execution | PASS — vendor description |
| Directional fields | Call/put buys and sells, net premium/delta | PASS — vendor description |
| Midpoint handling | Midpoint trades remain unclassified; classified-volume share returned | Positive design feature; exact rules still pending |
| Granularity | Minute and daily aggregates | PASS — advertised |
| Delivery | Same-evening availability | Conditional; no exact historical release timestamp |
| Broad universe | US equity options / OPRA stated | Conditional; per-symbol and inactive-name coverage not demonstrated |
| PIT identity | No endpoint-specific permanent-ID/corporate-action specification inspected | FAIL pending sample and dictionary |
| Revisions | No endpoint-specific correction/vintage policy disclosed | FAIL pending written specification |
| Methodology | NBBO signing described, but trade-condition, stale/locked/crossed quote, cancel/correction and complex-order rules not disclosed | FAIL pending full dictionary |
| Bulk feasibility | API plans and rate limits published; retail plans explicitly not designed for downloading all market data | FAIL pending authorized sample and bulk terms |
| License | Personal plans are for personal non-professional single use; professional use requires a separate arrangement | FAIL pending applicable license |

Public API page: https://www.ivolatility.com/data-cloud-api/  
Current FAQ: https://www.ivolatility.com/faq/

The public API page currently lists retail Builder, Quant and Lab plans with 20,000, 100,000 and unlimited monthly requests respectively, at one request per second (burst five); the page lists annual-billed prices of $63/$159/$239 per month and a seven-day trial. The FAQ separately shows $79/$199/$299 monthly prices. Treat the price difference as a billing-period/display discrepancy to resolve before any access. The FAQ explicitly warns that retail plans are not designed for downloading all market data and that attempts may lead to account suspension. Professional usage requires a separate license. No account, trial or purchase was initiated.

## 3. Important PIT distinction

The advertised **2015 history is not proof that the derived signed-flow series was available to investors in 2015**. The endpoint was announced in October 2026 and may expose a retrospective backfill. The statement that current daily files are available the same evening does not establish the first-publication timestamp or revision history of every historical date.

For any future test, preserve at least:
- `TradeEventTime`: underlying OPRA execution time;
- `QuoteEventTime`: NBBO time used to sign the trade;
- `VendorKnowledgeTime`: when the aggregate/response first became available;
- `RetrievalTime`, schema/methodology version and raw-response hash;
- correction/revision lineage.

Until historical first-publication vintages or delivery logs are demonstrated, the vendor aggregate is **not strict historical PIT**. A next-session knowledge/execution sensitivity is acceptable only as a labelled conditional analysis, not as proof of historical availability. If vendor vintages cannot be obtained, a separately reconstructed raw OPRA trade+NBBO panel may be considered, but it must have its own archive, condition and licensing audit.

## 4. Interpretation constraints

- NBBO-side signing is an inference from execution price relative to the quote, not an exchange-provided beneficial-owner identity or proof of informed trading.
- Midpoint volume must remain unclassified; do not force it into buy/sell. Track classified-volume share and require a preregistered minimum coverage threshold.
- The vendor's `customer gamma` / `customer vega` fields are derived measures until their definitions and participant taxonomy are documented. Do not equate them with named customers, institutions or verified customer accounts.
- Sweep, size and multi-leg filters are vendor-defined classifications. Their exact stitching, trade-condition and correction logic must be audited before use.
- GEX/dealer levels are model-derived from option-chain inputs, not reported dealer inventories. They are a separate regime/context hypothesis and must not be merged into signed flow or called observed dealer positions.

## 5. Relationship to existing options candidates

| Source | Construct | Role after Phase 137 |
|---|---|---|
| IVolatility new OPRA signed-flow API | NBBO-signed call/put trade demand | **Top-tier conditional broad signed-flow candidate** |
| OptionMetrics IvyDB Signed Volume | Buyer/seller-initiated volume, midpoint classification; advertised every option daily since Jan 2016 | Parallel vendor/methodology robustness candidate |
| Cboe Open-Close EOD | Cboe-venue capacity × buy/sell × open/close | Complementary position-side/capacity candidate |
| Cboe Volatility Surfaces | IV/skew/term structure | Volatility-context candidate |
| IVolatility GEX series | Derived dealer-gamma regime/levels | Secondary context hypothesis only |
| Cboe Options PITCH | Venue-specific visible order-book lifecycle | Conditional microstructure candidate |

IVolatility and OptionMetrics both describe OPRA-sourced options data. Cross-vendor agreement is therefore a **methodology/vendor robustness comparison**, not independent raw-market confirmation. Cboe Open-Close is a different construct and venue subset; it can complement signed flow but does not turn the two vendor outputs into independent full-market sources.

OptionMetrics current public materials: https://optionmetrics.com/signed-volume/ and https://optionmetrics.com/united-states/. The Signed Volume brochure states 5- and 30-minute snapshots, EOD data, and lot-size fields beginning in 2021; lot size is a size proxy, not account identity.

## 6. Preregistered economic questions — not results

Keep signed-flow and GEX hypotheses separate.

1. Does net signed delta demand (calls and puts with economically correct delta signs) predict subsequent underlying returns after controlling for prior 1/5/20/60-session returns, contemporaneous underlying move, IV/skew changes, liquidity, market/sector exposure and event windows?
2. Does signed premium flow add information beyond signed contract volume, prior OI and option/underlying liquidity?
3. Does the classified-volume share explain when the signal is reliable, or does conditioning on it merely select high-activity days?
4. Do sweeps, large-size and multi-leg filters add incremental information after their definitions and selection effects are frozen?
5. Does the signal predict realized volatility or volatility repricing more reliably than return direction?
6. Separately, do historical GEX regime changes add risk/context information after controlling for IV, realized volatility and market trend?

Do not label any flow bucket “smart money.” Separate information, return-chasing, leverage, dealer inventory/hedging and mechanical execution explanations.

If data gates pass, follow Phase 86 discipline: first freeze vendor definitions and filters; require at least 95% coverage of historically optionable F80 issuer-days in each tested period; preserve per-year/per-name missingness; use chronological development 2016–2019, validation 2020–2022 and locked OOS 2023–2026; compare against frozen LTM/F80 with identical exposure, next-session execution after verified availability, costs and missing-data treatment; test horizons 1/2/5/10/20/40 sessions without imposing a holding-period target; use issuer-clustered block bootstrap, ticker/sector leave-one-out and multiple-testing control. No test is authorized before the data and PIT gates pass.

## Decision

Promote the new IVolatility OPRA signed-flow endpoint to the **highest-priority conditional broad signed-flow candidate**, ahead of the older OptionMetrics Signed Volume implementation because it advertises 2015 history, explicit NBBO signing, midpoint exclusion, classified-volume coverage and current daily/minute API delivery. This is a source-priority decision, not an alpha result. OptionMetrics remains the parallel robustness candidate; Cboe Open-Close remains complementary for capacity/open/close.

Next gates: obtain/inspect the full endpoint dictionary and a representative authorized sample; validate all response fields, symbol/security IDs, delisted/adjusted options, trade conditions, corrections, classified-volume denominator, historical coverage by year and per-symbol, exact request limits and applicable license; establish historical knowledge-time or retain the strict PIT failure.

No vendor was contacted, no trial/account was opened, no data was purchased, no terms were accepted, no forward returns were tested and no production settings changed. `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen.


## 7. Repository execution preflight

- Working branch: `phase99-broad-pit-universe-charter`; current Phase 137 head: `1dd8c69bc7e83f5d29c728b591dc3999161c2045`.
- PR [#13](https://github.com/jafelix81/NuevaEstrategia/pull/13) remains open, unmerged and mergeable. It is 250 commits ahead of the merge base and one commit behind the current `main` head; GitHub reports mergeable=true.
- The latest run-specific Actions execution directly inspected was Phase 136 run [42115525546](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42115525546). Its job log shows compile, six offline tests, public-sample retrieval and aggregate artifact upload completed successfully; artifact [13455975956](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42115525546/artifacts/13455975956) exists. The job is completed, not running.
- The current head has no combined-status entries and no PR-triggered workflow runs attached. The available GitHub integration exposes run-specific jobs/logs/artifacts but not a repository-wide Actions-run listing, so this is the latest verifiable run rather than an exhaustive all-runs census. No workflow was dispatched or duplicated. Phase 136's workflow is path-filtered to its own script/tests/spec/workflow; this documentation-only Phase 137 update does not match those paths.
