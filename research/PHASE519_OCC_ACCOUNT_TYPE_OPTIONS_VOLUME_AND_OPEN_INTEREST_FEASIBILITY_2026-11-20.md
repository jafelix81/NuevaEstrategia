# Phase 519 — OCC options account-type volume / open-interest feasibility audit

**Audit date:** 2026-11-20 UTC  
**Preflight main:** `2f50cd7d92ca08b2d0c27aaa0baff6e4debf3a19`  
**Disposition:** OCC Volume Query is a potentially useful 24-month account-type / call-put participation dataset, but **automated access through the public website is not authorized by the published Website Terms**. Do not build or run a collector unless OCC provides a suitable written license/permission. No sample data were requested or downloaded; no signal or return test is admitted.

## 1. Repository / Actions preflight

- Reviewed the latest 100 GitHub Actions runs, jobs, artifacts, branches, open PRs and relevant research files before starting this audit.
- Main HEAD was `2f50cd7d92ca08b2d0c27aaa0baff6e4debf3a19`.
- The separate Phase 518 FINRA T1 production-window extension was already running at [Run 44698665308](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44698665308): offline tests passed; `live-audit` remained in progress. No duplicate dispatch was started.
- Phase 517 remains a separate draft PR #170. This OCC audit does not modify the Phase 518 branch or the frozen baseline.

## 2. What OCC exposes

OCC's public market-data pages document a 24-month lookback for Daily Volume, Open Interest, Volume by Account Type and Volume Query.

### Volume Query

The official Options Volume Query record layout contains:

- Quantity;
- underlying symbol and option symbol;
- account type: C = Customer, F = Firm, M = Market Maker;
- call/put indicator;
- exchange;
- activity date;
- series/contract date.

The batch-processing specification supports daily, weekly and monthly queries, filters for account type and product type, calls/puts, and either underlying or option-symbol selection. This is more useful than a simple aggregate put/call ratio because it permits account-category composition by underlying and call/put.

### Volume by Account Type

The separate Volume by Account Type report supports daily, weekly, monthly, yearly and rolling-12-month views, with all-symbol, option-symbol or underlying-symbol selection. Its record layout reports Customer, Firm, Market-Maker and Total volume by symbol/exchange.

### Open interest

OCC exposes a daily Open Interest report and a batch-processing download route. The public page states a 24-month availability window. The exact daily release timestamp and the complete current options-OI record layout were not established in this audit.

Official references:
- [OCC Volume Query](https://www.theocc.com/market-data/market-data-reports/volume-and-open-interest/volume-query)
- [Options Volume Query record layout](https://www.theocc.com/getmedia/50cf357d-6ec6-436e-a96b-c4710313a472/options-volume-query-record-layout.pdf)
- [Volume Query batch processing](https://www.theocc.com/market-data/market-data-reports/other-market-data-info/batch-processing/volume-query-batch-processing)
- [Volume by Account Type](https://www.theocc.com/market-data/market-data-reports/volume-and-open-interest/volume-by-account-type)
- [Volume by Account Type batch processing](https://www.theocc.com/market-data/market-data-reports/other-market-data-info/batch-processing/volume-by-account-type-download-batch-processing)
- [Open Interest](https://www.theocc.com/market-data/market-data-reports/volume-and-open-interest/open-interest)
- [Daily Open Interest batch processing](https://www.theocc.com/market-data/market-data-reports/other-market-data-info/batch-processing/daily-open-interest)

## 3. Critical access / licensing gate

OCC's [Website Terms and Conditions](https://www.theocc.com/specialpages/legal/terms-and-conditions), updated 2025-02-05, govern access to the website and its Data. They expressly prohibit use or launch of automated systems, including robots, spiders and offline readers, and prohibit reproducing, copying, reselling or otherwise exploiting the Services/Data for commercial purposes.

OCC separately publishes [Data Subscriber Terms](https://www.theocc.com/data-subscriber-terms). Those terms contemplate a subscriber agreement and require compliance with restrictions imposed by third-party data providers; a separate third-party license may be required.

**Decision:** public batch URLs are not equivalent to permission for an unattended GitHub Actions collector. No automated OCC request, scrape, sample download or backfill was attempted. A suitable written license/permission for automated internal research is a prerequisite. This is a human/legal authorization gate, not a parser problem.

## 4. What the fields do — and do not — mean

- C/F/M are OCC clearing-account categories, not named investors, funds or beneficial owners.
- Customer volume is not synonymous with retail flow; it can include professional customers.
- Firm volume is not a census of institutional investors.
- Market-Maker volume primarily describes clearing activity in the market-maker range, not directional informed demand.
- The Volume Query layout has no buyer/seller aggressor side and no opening/closing designation. A call/put imbalance by account type is therefore a participation-composition proxy, not signed directional flow.
- Daily open-interest changes are net contract-level changes after clearing. They do not identify which account type opened or closed a position and cannot be assigned to the same day's account-type volume without a separate, valid linkage.

Accordingly, any later hypothesis must be described as **account-type participation mix / options-market structure**, not “smart money buying.”

## 5. PIT, history and universe feasibility

| Gate | Current evidence | Disposition |
|---|---|---|
| Historical window | Public pages state past 24 months | Conditional; short relative to long regime coverage |
| Granularity | Daily/weekly/monthly query options | Promising |
| Account categories | C/F/M | Useful, but not investor identity |
| Direction | Calls/puts only; no buy/sell side | No signed flow |
| Open/close | Not in Volume Query layout | Not observed |
| OI | Daily report/download route; exact release time unresolved | Conditional |
| First public availability | A 2025 exchange filing says OCC customer-volume numbers are available each morning; no exact timestamp or version/correction ledger was established | Prospective first-seen capture required if licensed |
| F80 coverage | Not measured against the frozen 335-name diagnostic universe | Fail-closed |
| Historical security/series identity | Underlying and option symbols appear; effective-dated series/adjustment crosswalk not audited | Fail-closed |
| Revisions / corrections | No first-public, correction or replacement-vintage policy verified | Fail-closed |
| Automated use rights | Website terms prohibit automated systems absent suitable authorization | **Blocked** |

A 24-month panel may support a limited prospective/pilot comparison if the licensed sample has broad coverage, but it is not automatically enough for robust independent OOS evidence. Weekly observations and 5/10/20-session returns overlap; effective sample size and block dependence must be handled explicitly.

## 6. Conditional research design if access is authorized

Only after license/permission and a lawful sample:

1. Obtain a small authorized sample covering several liquid, medium-liquidity and option-sparse names, plus adjusted/delisted cases.
2. Measure daily coverage against point-in-time F80 membership and preserve inactive symbols.
3. Reconcile account-type totals and call/put totals against OCC aggregate volume; identify whether quantities are cleared sides or unique contracts before normalizing.
4. Establish actual first-received timestamps, report date, corrections, file hashes and next-executable-session rules.
5. Align OI as a post-clearing observation only after the exact publication convention is verified; never attribute OI changes to C/F/M without evidence.
6. Pre-register a small set of hypotheses: changes in Firm share, Customer share, Market-Maker share, and call/put composition may explain future volatility, liquidity or returns beyond prior returns, volume, volatility, market beta and LTM/F80.
7. Test whether apparent prediction is only contemporaneous activity or return-chasing. Use identical exposure/costs versus frozen LTM/F80, chronological train/evaluation, non-overlapping or block-aware inference, bootstrap and LOO. Do not select signs or horizons from the final holdout.

## 7. Final disposition

- **Candidate:** retain as a conditional account-type options-participation source.
- **Collector:** not authorized; no code or scheduled workflow created.
- **Historical backfill:** not performed.
- **PIT / F80 universe coverage:** not passed.
- **Signals admitted:** 0.
- **Backtests / OOS / bootstrap / LOO:** 0.
- `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen.

This audit does not change the Phase 518 FINRA run already in progress and does not change any strategy or production setting.
