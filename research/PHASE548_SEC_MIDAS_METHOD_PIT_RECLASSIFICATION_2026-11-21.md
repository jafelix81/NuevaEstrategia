# Phase 548 — SEC MIDAS public metrics: methodology, off-exchange scope and PIT reclassification

**Audit cutoff:** 2026-11-21 16:51 UTC  
**Base main:** `cb9aab722f905e2df54e349091e42ae7d9bf243a`  
**Disposition:** SEC MIDAS is a viable *public, daily-grain exchange-market-structure dataset* for conditional slow risk/liquidity research, but it is **not an off-exchange-flow or participant-identity source**. Historical PIT release times, exact frozen-335 coverage, file integrity and effective-dated identity remain unverified. No alpha test or signal is authorized.

## 1. Repository and Actions preflight

- Inspected the latest 100 Actions runs, first-page branch inventory, open PRs, issue #194, PR #200, main research state and relevant source audits before starting this phase.
- Latest 100 runs: **88 success, 11 failure, 1 cancelled**; zero in-progress, queued, waiting, requested or pending.
- Main HEAD remains `cb9aab722f905e2df54e349091e42ae7d9bf243a` (Phase 543). PR [#200](https://github.com/jafelix81/NuevaEstrategia/pull/200), Phase 547, remains Draft and mergeable on `phase547-cboe-opra-options-pit-feasibility`.
- Latest PR checks [44911635742](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44911635742) and [44911635727](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44911635727) both passed their offline Form 4 regression jobs. They produced no artifacts and are **not** tests of Cboe data or SEC MIDAS.
- Latest natural Form 144 capture remains [44886726541](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44886726541), successful at 08:50:10 UTC, artifact [14700173280](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44886726541/artifacts/14700173280). Its workflow declares `47 * * * *`. At 16:51 UTC, scheduled slots 09:47 through 16:47 UTC (eight hourly slots) were not present in the latest 100 runs. The last capture's successful feed poll does not establish scheduler continuity. Issue [#194](https://github.com/jafelix81/NuevaEstrategia/issues/194) remains open.
- FINRA [44868239322](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44868239322) is a Phase 539 PR run: offline regression passed, but `live-capture` was skipped. Main's [44860690600](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44860690600) predates the Phase 539 merge. Thus no natural post-merge live capture has validated the duplicate-symbol diagnostics.
- CFTC [44860341977](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44860341977) completed successfully with artifact [14689726870](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44860341977/artifacts/14689726870). Phase 541 still documents only two prospectively received TFF report vintages; historical backfill is not PIT eligible.
- Form 4 [44846461134](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44846461134) completed successfully with artifact [14683520646](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44846461134/artifacts/14683520646). No new owner-attributed eligible signal was established.
- No existing workflow was dispatched, rerun, cancelled or duplicated.

## 2. Official SEC MIDAS public data catalog

The current SEC **Metrics by Individual Security** page lists 59 quarterly ZIP files from **2012 Q1 through 2026 Q3** and says the data cover more than 4,800 securities. Its fields include Ticker, Date, Security, market-cap/turnover/volatility/price ranks, cancellations, trades, lit trades, odd lots, hidden trades, trades for hidden orders, order volume, trade volume, lit volume, odd-lot volume, hidden volume and the denominator volume for hidden trades.

The companion **Metrics by Individual Security and Exchange** series has the same quarterly span and partitions the measures by exchange. The current Q3 2026 files are listed at 24.42 MB for the individual-security series and 201.18 MB for the security-and-exchange series. The public pages establish catalog history and daily observation fields, not complete per-symbol availability or a historical PIT release clock.

Official sources:
- https://www.sec.gov/data-research/sec-markets-data/marketstructuredata-security
- https://www.sec.gov/data-research/sec-markets-data/market-structure-data-security-exchange
- https://www.sec.gov/data-research/market-structure-data

## 3. Critical scope correction: this is not off-exchange flow

The SEC's MIDAS system collects proprietary exchange feeds and off-exchange executions. That does **not** mean every public MIDAS download includes both.

The SEC's own MIDAS feedback explains that its published volume metrics generally exclude off-exchange trading, opening/closing auctions and off-hours activity. Therefore the per-security market-activity files must not be described as ATS, dark-pool, off-exchange or total-market flow.

The SEC defines a **hidden trade** as an exchange execution in which a marketable order matches an undisplayed/hidden resting order. This is not a dark-pool execution and does not identify the buyer, seller or beneficial owner.

Hidden-volume coverage is also partial: the SEC says the metric can be calculated for only 8 of 13 equity exchange feeds. The hidden-volume denominator excludes venues for which the SEC cannot definitively classify hidden executions (including NYSE, Amex, CHX and NSX). A hidden-volume ratio is therefore not a complete all-exchange measure.

Official sources:
- https://www.sec.gov/securities-topics/market-structure-analytics/midas-feedback
- https://www.sec.gov/about/hidden-volume-ratios
- https://www.sec.gov/securities-topics/market-structure-analytics/midas-market-information-data-analytics-system

**Hypothesis disposition:** kill the interpretation “MIDAS hidden volume = dark/off-exchange institutional accumulation.” The public metrics do not support that construct. Retain only an exchange-market-structure interpretation.

## 4. Methodology and historical regime breaks

The SEC's Market Activity Report Methodology states:

- The measured continuous-market window is 09:35–16:00 ET. The methodology filters special trades, intraday crosses and IPO halts; opening/closing auctions and off-hours are not represented as ordinary continuous-market activity.
- The security universe is sourced from CRSP daily stock data and updated monthly with a **3–4 week lag** from the previous month's final trading day. This is not the frozen F80 universe and must not be mistaken for contemporaneous historical membership.
- Hidden trades are executions against undisplayed resting orders. The SEC's ability to identify these executions differs by exchange.
- Beginning **2014-01**, odd-lot trades reported to the SIP enabled a fuller reconciliation for NYSE and Amex.
- Beginning **2017-05-01**, MIDAS switched from NYSE Ultrabook to the NYSE Integrated Feed; the hidden-order identification regime changed.
- Beginning **2025-11-03**, the SEC adopted new four-tier round-lot definitions, updated semiannually. Odd-lot and order-book-related features must be checked against the applicable methodology regime; do not splice a single unqualified series across this boundary.

Other limitations in the SEC methodology explain why exchange feeds are not perfectly comparable. In particular, certain cancel-to-trade and odd-lot measures were not included for NYSE/Amex before the Integrated Feed change. Missingness and exchange eligibility must be explicit, not silently imputed.

Official methodology:
- https://www.sec.gov/featured-topics/market-structure-analytics/market-activity-report-methodology

## 5. Feasibility matrix

| Gate | Evidence | Disposition |
|---|---|---|
| Advertised historical span | 59 quarterly files, 2012 Q1–2026 Q3 | Pass at catalog level |
| Daily security-level observation grain | Date and per-security market-activity fields | Pass at schema-description level |
| Exact 335-name/date coverage | No frozen-universe availability matrix | **Unverified / fail closed** |
| Historical inactive/delisted identity | Ticker/name fields do not establish effective-dated security identity | **Unverified / fail closed** |
| Per-quarter first-public timestamp | Only page-level review/update date is visible; no per-file publication clock established | **Fail for historical strict PIT** |
| File integrity and row continuity | ZIP payloads were not downloaded or parsed in this audit | **Unverified** |
| Off-exchange/ATS scope | Published volume metrics generally exclude off-exchange | **Fail for off-exchange hypothesis** |
| Participant identity / opening vs closing | No beneficial-owner or participant-capacity fields | **Fail for “smart money” identity** |
| Hidden-volume completeness | 8 of 13 feeds; denominator excludes venues without reliable hidden-order classification | Partial only |
| Methodological continuity | 2014, 2017 and 2025 regime changes | Requires segmentation and field-level validation |
| Vendor licensing | Public SEC download pages; no commercial vendor subscription identified | No vendor purchase required; preserve SEC source attribution and verify applicable reuse terms before redistribution |

The page-level “Last Reviewed or Updated: September 30, 2026” is not a publication timestamp for each quarterly ZIP. A quarter label, observation Date, current listing or file modification time must not be backdated into a historical knowledge clock.

A retrieval attempt of the current ZIP was rejected by the web retrieval layer as an unsupported binary content type, and the container download attempt failed. This phase therefore validates the official catalog and methodology, not the payload itself.

## 6. Permissible research role and preregistered gates

If a future file-level and PIT audit passes, MIDAS may be considered for **slow market-quality / liquidity-state context**, not informed-investor identity. Candidate features to evaluate separately are:

1. Hidden-volume rate, with the SEC-defined restricted denominator and exchange-coverage mask.
2. Odd-lot volume/rate, segmented by the applicable historical round-lot methodology.
3. Cancel-to-trade ratio, only on comparable exchange/feed regimes.
4. Trade-to-order volume, only after exchange-specific order-book reporting comparability is established.

Before any return test:
- obtain and validate actual ZIPs for multiple eras (pre/post 2014, pre/post 2017 and pre/post 2025-11-03);
- build an exact symbol/date availability matrix against the historical F80 membership and an effective-dated security master, retaining acquired and delisted names;
- capture first-seen quarterly index/file timestamps prospectively, with URL, UTC receipt, byte count, SHA-256, schema and revision events;
- use only the first complete session after actual file receipt; quarterly backfill rows remain unavailable until the relevant quarter file was actually public;
- distinguish a slow risk/liquidity effect from return-chasing by controlling for prior return, volatility, turnover, market cap and other frozen LTM/F80 inputs;
- pre-register feature definitions and test incremental information against frozen LTM/F80 at identical exposure and costs, with chronological OOS, block bootstrap and leave-one-event/time-block-out controls.

Because quarterly files may become usable only after the quarter has ended, this source may be too stale for short-horizon stock selection. That is an empirical question; no holding period is imposed, but no same-quarter use is permitted.

## 7. Cboe options license gate reconciliation

The earlier Phase 527 audit already identified a material restriction in the published Cboe LiveVol DataShop License Agreement, Section I.1(e)(viii): using Data or related methodology to create an index, indicator, benchmark or investment strategy requires a separate written and executed agreement expressly permitting that use.

Phase 547's OPRA-wide Option Trades/Option Quotes and Open-Close findings remain useful source-feasibility work, but **they are not actionable for strategy research under the standard license alone**. Before any sample, order, subscription or model test, obtain written authorization covering investment-strategy/indicator/model-development use, third-party OPRA rights, retention and derived-data use. No sample, purchase, vendor contact or license acceptance occurred.

Official policy location:
- https://datashop.cboe.com/data-policies
- https://datashop.cboe.com/documents/Cboe_LiveVol_DataShop_License_Agreement.pdf

## 8. Decision and frozen controls

- Reclassify SEC MIDAS as a **conditional public exchange-market-structure / liquidity-state candidate**.
- Kill the off-exchange / dark-pool / institutional-accumulation interpretation of the public MIDAS metrics.
- Keep FINRA ATS as venue-concentration data, FINRA Reg SHO as short-sale-volume data, and MIDAS as exchange-market-structure data; do not merge them into a synthetic “smart money” label.
- Keep Cboe options data blocked for strategy research until the separate written license carve-out is obtained.
- New signals admitted: **0**.
- New backtests / event studies / OOS / bootstrap / LOO: **0**.
- No changes to universe, holdout, parameters, holding-period rules, costs, exposure or production.
- `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen.

The next defensible MIDAS step is a file-level coverage/schema and prospective first-receipt audit, not an alpha test. The next FINRA step is a natural post-Phase-539 capture; the next SEC operational step is human verification of Form 144 scheduled-workflow enablement/delivery.
