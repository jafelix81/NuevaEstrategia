# Phase 531 — Obscura multi-source PIT feasibility and OCC reconciliation

Date: 2026-11-20  
Branch: `phase531-obscura-multisource-pit-audit`  
Status: source-feasibility audit only; no vendor data queried; no alpha test.

## 1. Repository and Actions preflight

Main HEAD at audit start: `49bf4c2a6529fa1eb4b64e7a1f22a147952071f9` (commit time 2026-11-20 15:35:39 UTC).

The latest 100 Actions runs, the schedule-filtered run inventory, explicit in-progress/queued queries, open PRs, relevant jobs/logs/artifacts, current workflow YAML and research state were checked before any change.

- In-progress runs: 0.
- Queued runs: 0.
- Latest SEC Form 4 scheduled run: [44716430351](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44716430351), created 2026-11-20 10:06:51 UTC, completed 10:07:24 UTC.
- Latest SEC Form 144 scheduled run: [44720422923](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44720422923), created 2026-11-20 10:34:45 UTC, completed 10:35:10 UTC.
- Form 4 schedule in main: `17 * * * 1-5`; Form 144 schedule: `47 * * * *`.
- At 17:23 UTC, the 16:47 Form 144 and 17:17 Form 4 slots had passed without a corresponding scheduled run. The 17:47 Form 144 slot was still in the future.
- The Form 4 workflow on main contains the Phase 525 reporting-owner and crosswalk steps, but the latest live Form 4 run predates Phase 525. The file `research/data/sec_form4_first_seen/reporting_owners.csv` is still absent.
- The Form 4 run log reports 33 new accession metadata rows, 37 structured transaction rows, 1,213 bounded accessions remaining, and zero research-/signal-eligible rows. The Form 144 run reports 52 feed rows, no new accession, 64 detail rows appended from its bounded backfill, and 358 accessions remaining.
- After PR #189 was opened, the two triggered offline checks completed successfully: [44783867533](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44783867533) (Phase 460) and [44783866875](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44783866875) (Phase 461). Both had zero artifacts and were not live captures.
- The latest successful PR checks [44764768726](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44764768726) and [44764768625](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44764768625) are Phase 529 pull-request checks, not live SEC captures.
- Issue [#185](https://github.com/jafelix81/NuevaEstrategia/issues/185) was updated with this evidence. No manual dispatch, rerun or duplicate poll was made. The repository connector does not expose the administrative enabled/disabled state of each workflow, so that state remains unverified.

Relevant open research PRs remain separate and were not merged: #188 Massive, #186 ThetaData, #171 OCC, and #159 FINRA Short Interest. The old `phase53-occ-daily-open-interest-audit` branch is 16 commits ahead and 360 behind main, with no associated PR; it is retained as an archived audit branch and must not be merged wholesale.

## 2. Reconciliation of the archived OCC Phase 53 audit

The prior branch contains actual completed runs and artifacts; this audit inspected their logs rather than repeating OCC requests.

### 2.1 Daily Open Interest endpoint

- Run: [41762027453](https://github.com/jafelix81/NuevaEstrategia/actions/runs/41762027453)
- Job: `126351668278`
- Artifact: `13290557109` (`phase53-occ-daily-open-interest-audit`)
- Six parser tests passed.

The dedicated OCC Daily Open Interest download returned a monthly market-wide report with asset-class totals (Equity, Index/Other, Debt, Futures and OCC Total), not contract-level open interest by underlying/option series. Some historical probes returned short error/empty payloads. It therefore fails the required per-security OI grain and is **not** a per-stock positioning source. At most, the monthly market-wide totals could be considered a broad regime control, but they do not justify a new collection pipeline.

### 2.2 Volume Query full-universe audit

Canonical corrected run: [41763113005](https://github.com/jafelix81/NuevaEstrategia/actions/runs/41763113005), job `126356693552`, artifact `13292225481`.

- 670 ticker/date requests completed with zero HTTP/query errors.
- 645/670 responses were schema-valid (96.27%).
- 2025-01-03: 325/335 tickers (97.01%).
- 2026-11-02: 320/335 tickers (95.52%).
- The 2024-01-03 boundary probes returned OCC's explicit two-year retention error.

The all-series response contains quantity, underlying, option root/symbol, account type (Customer/Firm/Market Maker), call/put, exchange and activity date. It does **not** contain buy/sell aggressor side, strike, expiry/contract date, open/close status or actual OI. Account type is not beneficial-owner identity; call/put volume is not directional positioning.

Decision: recent schema/universe coverage passes, but historical depth and PIT publication-time gates fail. Retain only as a short-window descriptive hypothesis, not as a standalone Smart Money signal. No forward-return test was performed.

### 2.3 OCC access constraint

OCC's current [Website Terms and Conditions](https://www.theocc.com/specialpages/legal/terms-and-conditions), updated 2025-02-05, prohibit automated systems (including robots, spiders and offline readers) from accessing its Services. They also restrict reproduction and commercial exploitation. The archived Phase 53 results are not permission for future automated collection.

Decision: no further automated OCC access unless an appropriate written data-subscriber agreement or authorization expressly covers the intended collection and research use. No new OCC requests were made in this phase.

## 3. Obscura — newly identified multi-source candidate

[Obscura](https://obscura.trade/) publishes a catalog of 125 datasets through a typed API and Parquet export. Its public pages describe a common `available_date` field intended to represent the day the source data became public. This is a potentially useful data-delivery layer, not proof that every dataset has a correct PIT clock or economic edge.

Published plan information:
- Standard: USD 199/month, described for individuals and non-professional use.
- Professional: USD 600/month, billed annually; the site says professional traders require this tier.
- Enterprise: custom terms; the only tier advertised as carrying redistribution rights.

Standard and Professional are described as internal-use only. Therefore raw data and licensed derived data must not be committed to this public repository, emitted into public Actions logs/artifacts, or otherwise redistributed. A private data store/runtime would be required. The correct plan depends on the actual use; no plan was selected or purchased.

### 3.1 Highest-priority dataset candidate: `flow_metrics`

Public schema page: https://obscura.trade/datasets/flow-metrics/

Published description:
- One daily row per symbol/session.
- The dataset-specific page lists 126 columns and approximately 119 derived factors; the homepage worked example says 127 fields. This field-count discrepancy must be resolved against the actual schema before integration.
- Aggressor-side classification using quote rule with tick-rule fallback.
- Taker buy/sell volume and counts, order-size composition, price/tick distributions, volatility, impact/slippage, run structure and order-flow imbalance.
- Refresh cadence advertised as every six hours.
- PIT documentation conflicts: the dataset-specific page defines `available_date = date(event_time)` (session date) and says a prior +1-day rule was corrected; the homepage worked example still shows `date(event_time) + 1 calendar day` and describes next-day availability. Treat the formula as unresolved until the vendor confirms the current schema/migration.

Feasibility gaps:
- Exact earliest history date and date-by-date coverage of the frozen 335-symbol universe are not stated on the public page.
- Raw source/venue coverage, trade-condition filters, quote staleness/locked-crossed handling, corrections/cancels, odd-lot handling, and the exact aggressor-classification implementation need a technical data dictionary.
- No independent validation of the vendor's factors or historical revision policy has been performed.
- A date-only `available_date` does not provide an intraday publication time. Since the factor is a full-session daily aggregate, it must not be used for a same-day closing execution. Until the conflicting formula and a timestamped availability SLA are evidenced, use the next regular session as the earliest eligible session; for a close-based execution policy, test next-session close, not same-day close.

Interpretation: potentially useful equity order-flow/microstructure data, not options flow and not institutional identity. Large-print buckets must not be labelled institutional without independent evidence. The key hypothesis is whether signed flow adds information beyond LTM/F80 after controlling for momentum, turnover, volatility and return-chasing.

### 3.2 SEC MIDAS per-security metrics

Public schema page: https://obscura.trade/datasets/sec-midas-security-metrics/

The vendor describes daily per-security SEC MIDAS metrics (20 columns) covering market-structure ranks, lit/hidden volume and order/trade measures. The SEC's own [Market Structure Data Downloads](https://www.sec.gov/data-research/market-structure-data) lists individual-security datasets through June 2026; the Data.gov catalog reports a 2012-01-01 to 2026-06-30 period and 58 resources. The specific Data.gov `Metrics by Individual Security` metadata page is stale (dataset last updated 2017-10-30) despite listing a 2026 Q2 resource, so its catalog-level modified date cannot establish per-file release timing. Obscura says six quarters are absent at source (2014 Q2, all four quarters of 2016, and 2019 Q4); that missing-quarter claim has not been independently reconciled to the archive files.

PIT limitation: Obscura's general `available_date` definition is not, by itself, evidence of the first public release day of each SEC quarterly file. The Data.gov metadata's `modified` timestamp is 2024-10-31 even though the resource list includes 2026 Q2, so that metadata field cannot be used as a per-file publication timestamp. The SEC page reports a June 2026 update but does not provide per-quarter release dates in the reviewed page.

Decision: promising market-structure feature set, but PIT release dates, missing-quarter details, exact 335-universe overlap, ticker continuity and delisted-security coverage must be verified before a backtest. Treat as a liquidity/market-structure feature, not smart-money identity.

### 3.3 FINRA datasets in the catalog

Public schema pages:
- https://obscura.trade/datasets/finra-short-volume/
- https://obscura.trade/datasets/finra-short-interest/

`finra_short_volume` is described as daily per-symbol Reg SHO volume from FINRA CNMS daily files. Its schema separates short volume, short-exempt volume and total volume. The vendor states same-day availability and approximately 17:18 ET publication. FINRA's own [short-sale-volume explanation](https://syndication.finra.org/content/short-interest-what-it-what-it-not) distinguishes this executed off-exchange short-sale volume from short interest; the official rule material says the daily file is posted after regular trading hours, within a reasonable amount of time. Thus a full-day file cannot be used for the same-day close; use a later session. It is not a net short-position measure and does not identify the short seller.

`finra_short_interest` is described as twice-monthly settlement positions with `available_date` set to settlement plus seven business days. The schema is ticker-only (no CUSIP/CIK). This rule and the vendor's revision handling need to be reconciled against FINRA's official publication calendar and actual first-seen records. It may be a data-delivery alternative, but does not create a new hypothesis; the previously tested FINRA short-flow × short-interest signal remains killed unless a materially different mechanism is preregistered.

### 3.4 SEC insider transactions

Public schema page: https://obscura.trade/datasets/edgar-insider-transactions/

The vendor describes transaction-line rows from Forms 3/4/5 and derives `available_date` by joining the filing path to its EDGAR dissemination index. This could be an independent cross-check for Phase 525's Form 4 owner/transaction ledger.

Before use, test:
- one-owner versus multiple-owner filings and transaction-to-owner attribution;
- Form 4 amendments and duplicate accession handling;
- derivative versus non-derivative units and underlying shares;
- codes P/S/M/F/A and footnote/remarks context;
- exact agreement of `available_date` with the SEC daily dissemination index.

Do not replace the transparent SEC pipeline or treat the vendor's normalized rows as correct without row-level reconciliation.

## 4. Source ranking and next gates

1. `flow_metrics`: first candidate for a small, private, aggregate-only coverage/methodology pilot **only after** written confirmation of history start, 335-name coverage, source/venue lineage, revisions/corrections, aggressor classification, exact availability semantics and permitted use.
2. `sec_midas_security_metrics`: second candidate; first resolve per-quarter public release dates, missing quarters, universe overlap and ticker continuity.
3. `edgar_insider_transactions`: optional independent cross-check of the Phase 525 SEC ledger, not a new signal.
4. FINRA short-volume/short-interest tables: optional data-delivery cross-check only; do not resurrect the killed signal without a distinct preregistered hypothesis.
5. OCC Volume Query: park for automated use absent written authorization; limited two-year history and no trade direction/open-close/OI.
6. OCC Daily Open Interest endpoint: reject as per-security OI; it returned market-wide monthly totals.

No Obscura account, API key, subscription, API query, bulk download or data sample was obtained. No OCC request was repeated. No vendor was contacted. This is a public-documentation audit only.

## 5. Preregistered research discipline if access is later authorized

For `flow_metrics`, freeze a small feature family before looking at returns:
- signed taker-volume imbalance / total volume;
- signed notional imbalance;
- size-bucket imbalance, without labelling buckets as institutions;
- buy/sell trade-count imbalance;
- persistence and divergence between signed flow and contemporaneous return.

Residualize or control for prior returns/momentum, turnover, volatility, market/sector effects and liquidity to distinguish prediction from return-chasing. Use the same 335-name point-in-time universe and identical exposure/cost assumptions as LTM/F80. Use chronological train/validation/OOS, untouched holdout, block bootstrap and leave-one-period-out. A signal must show incremental net economic value; standalone correlations or vendor z-scores are not sufficient. For a daily full-session factor, no same-day-close execution is permitted without a documented pre-close publication timestamp.

For MIDAS, first test whether hidden/odd-lot/trade-size/liquidity measures predict subsequent liquidity or risk, separately from return direction. Do not infer institutional intent from aggregate market-structure statistics.

## 6. Strategy protection

- `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen.
- New signals admitted: 0.
- New OOS results: 0.
- Backtests performed in this phase: 0.
- Exposure, costs, universe and holdout: unchanged.
- No production changes.

This phase ends at data feasibility. It does not establish alpha.
