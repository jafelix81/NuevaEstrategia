# Phase 599 — Options-source licensing, historical PIT and executable-research re-ranking

**Audit cutoff:** 2026-11-24 15:56 UTC  
**Main HEAD at preflight:** 6a0362c2af1a9f76f935663d9698be8ca5c66e6c  
**Disposition:** Databento OPRA is now the leading conditional route for an independently reconstructed, market-wide options-flow panel, subject to a commercial/non-display license determination, a bounded sample, 335-name historical coverage and prospective first-receipt capture. Cboe DataShop's standard license is not actionable for strategy creation without a separate written and executed carve-out. No data, license, signal or alpha is admitted.

## 1. Repository and Actions preflight

The repository was checked before source work:

- Actions runs: 8,109 total.
- Latest 100: 90 successful / 10 failed; all 100 completed.
- Explicit in-progress and queued queries: 0 / 0.
- Schedule-triggered inventory: 59 runs.
- Branches: 380; open PRs: 72; workflow files: 96; research directory entries: 492.
- Main HEAD remained 6a0362c2af1a9f76f935663d9698be8ca5c66e6c at the final pre-write check.
- No workflow was dispatched, rerun, cancelled, merged, rebased or duplicated.

Latest relevant natural schedule runs:
- FINRA Reg SHO: 45339067236 at 06:15:11 UTC.
- CFTC TFF: 45338400329 at 06:09:53 UTC.
- SEC Form 4: 45332760566 at 05:21:36 UTC.
- SEC Form 144: 45330252226 at 05:00:27 UTC.

At the 15:56 UTC cutoff, the Form 144 15:47 UTC nominal slot had not appeared (nine minutes late); Form 4's next 16:17 UTC slot had not yet become due. A single delayed slot is not enough to classify as a new failure. The read-only GitHub connection still does not expose individual workflow enabled/paused state. No new comment was added to Issue #194 on this short delay.

## 2. Latest jobs, logs and artifacts rechecked

The latest FINRA, CFTC, Form 4 and Form 144 jobs and artifacts were inspected and the artifacts were downloaded and parsed.

| Source | Run / artifact | Verified result |
|---|---|---|
| FINRA Reg SHO | 45339067236 / 14895571787 | Six HTTP-200 CNMS files rejected; BCPC and TPC each repeated in all six dates; 12 extra rows; zero exact-row duplicates; zero valid files, first-seen observations or eligible signals. Raw rows and volume values were not persisted. |
| CFTC TFF | 45338400329 / 14895036288 | 3,043 historical rows; no new reports or revisions; four index futures contracts; 17 offline tests passed; no historical signal-eligible rows. |
| SEC Form 4 | 45332760566 / 14892950135 | Both watermarks found; 516 new canonical accession events; 1,239 feed observations; 24 transaction-detail rows and 11 owner rows appended; 2,273 transaction backfills and 20 owner accessions remain; zero signal-eligible rows. |
| SEC Form 144 | 45330252226 / 14891955642 | 118 new accessions/XML resolutions; 801 detail rows added; 477 accessions / 3,360 detail rows; 238 backfills remain; 113 of 118 acceptance reconciliations added and five unresolved; zero signal-eligible filings. |
| Form 144 10b5-1 refresh | 45330252226 / 14891416912 | 16 sell-to-cover/tax-withholding accessions in the ledger; none admitted as a signal. |

The FINRA workflow's success conclusion means the fail-closed diagnostic completed, not that the six files were accepted. The CFTC run's success means the prospective poll completed with no new report; it does not authorize historical backfill as a point-in-time signal. SEC first-seen values remain bounded receipt upper limits, not exact public-release clocks.

## 3. Branch and PR review: license constraints change the ranking

Relevant open draft PRs remain divergent and were not merged:

- PR #200, Phase 547 Cboe OPRA/Open-Close: 5 commits ahead / 111 behind main. Its existing review comment records Phase 527's discovery that the standard Cboe LiveVol DataShop License Agreement, Section I.1(e)(viii), requires a separate written and executed agreement to use Data or related methodology to create an index, indicator, benchmark, investment strategy or similar value. This is a direct blocker for the proposed strategy research under standard terms.
- PR #188, Massive Options: 5 ahead / 155 behind. The current individual terms restrict use to the subscriber's personal, non-business and non-commercial activity and prohibit employer/organization use and sharing of Information, including certain derived data. Not suitable for this public-repository/organizational workflow without a different written license and controlled private data handling.
- PR #186, ThetaData: personal-use, derivative-work, retention/expungement and OPRA non-display terms remain unresolved. Not cleared.
- PR #164, OptionMetrics implied-dividend gap: a separate volatility/dividend-risk hypothesis, not direct smart-money flow.
- PR #8 and #6, SEC 13F: remain draft; their old workflows still require the SEC_USER_AGENT secret contract and offline-only PR/push behavior before any live retrieval.

No old branch was merged or replayed. The existing PR #200 comment is already explicit that Cboe DataShop is not actionable under the standard license; this phase does not repeat that comment.

## 4. New candidate: Databento OPRA.PILLAR

Current official Databento documentation identifies OPRA.PILLAR as consolidated US equity-options market data. The dataset page advertises history from 2013-04-01 and the docs describe 20 options venues as of September 2026. The product page currently says 18 venues, so the vendor's product summary and detailed venue metadata are not fully synchronized; the actual sample's versioned publisher list must be retained.

Official documentation:
- Dataset: https://databento.com/datasets/OPRA.PILLAR
- Feed specifications: https://databento.com/docs/datasets/opra-pillar
- OPRA history/schema announcement: https://databento.com/blog/opra-improvements-coming-soon
- OPRA pricing plans: https://databento.com/blog/introducing-new-opra-pricing-plans
- Pricing / historical credits: https://databento.com/pricing/
- Live data and venue licensing: https://databento.com/docs/portal/live-data
- OPRA fee schedule: https://api.databento.com/v0/licensing/documents/opra/OPRA_Fee_Schedule.pdf

### 4.1 Useful data and timestamps

- Trade records provide the venue, price, size, conditions and OPRA timestamps. OPRA itself does not publish aggressor side; Databento documents that the side field is always N.
- TCBBO provides the consolidated NBBO immediately before each trade, enabling a quote-relative aggressor proxy. It does not reveal beneficial owner, account type, institutional identity, opening/closing intent or private information.
- CMBP-1 is the consolidated BBO update stream. It is substantially larger than a trade-only panel and should not be the first bulk download.
- The 2025 schema migration introduced CMBP-1 and TCBBO in place of the prior regional top-of-book schemas.
- The 2025 history expansion documents trades and CBBO-1m from 2013-04-01, while CMBP-1 and TCBBO begin 2023-03-28.
- Before 2023-03-28, the historical data were subsampled rather than generated from packet captures. TCBBO/CMBP-1 are unavailable; CBBO-1m is the highest BBO granularity; ts_recv is set to the event timestamp and F_BAD_TS_RECV is always set. This is a material data-regime break, not a cosmetic schema change.
- From 2023-03-28, ts_recv is the Databento capture-server receive time and ts_event is the consolidator-processed event time. Neither is our subscriber's first receipt.
- OPRA publishes open interest around 06:30 ET. Since 2023-03-28, the same instrument's OI quantity can appear separately under multiple venue publisher IDs. Deduplicate by effective instrument/date/quantity; do not sum venue copies. Before that date OI is published once at OPRA aggregate level.
- Historical access is described as available one hour delayed or by the next day at 09:30 ET, depending on access method. This is a vendor release schedule, not a historical subscriber-first-receipt ledger. Start a prospective immutable first-receipt log before any signal test.

### 4.2 Contract identity and quality risks

OPRA raw option symbols use 21-character OSI symbology. The parent symbol can change after corporate actions (for example, adjusted roots such as MSFT1/MSFT2). Historical instrument_id-to-raw_symbol mappings can change and are not identical to live mappings. Expiration is date-granularity only.

The sample gate must therefore preserve raw symbol, instrument_id, parent symbol, definition record, effective date, multiplier/deliverable, expiry, strike, call/put, venue publisher, trade conditions, correction flags and all timestamps. A current ticker join or a universal 100-share multiplier is not acceptable. The exact historical 335-name F80 coverage, inactive/delisted coverage and adjusted-contract lineage are not established by the public coverage headline.

### 4.3 Licensing and cost

Databento advertises usage-based historical access and $125 in new-user historical credits. Exact OPRA historical cost per GB and the total 335-name sample cost are not established by the public summary and require the dataset estimator or a quote.

The current 2026 Databento live-license table lists OPRA commercial non-display at $2,000 per firm, with separate distribution and user fees; the same table lists $1.25 per personal device. This is a live-data license table, not a definitive quote for a historical-only purchase. Do not apply the live fee to a historical-only order without written confirmation. Any prospective non-display feed or automated internal analytics must be classified with Databento/OPRA before use.

No account was opened, no credentials were requested, no vendor was contacted, no license was accepted and no data were downloaded.

## 5. Updated options-source ranking

| Source | Role after this audit | Main gate |
|---|---|---|
| Databento OPRA trades + TCBBO | **First conditional sample/quote candidate** for market-wide signed-flow reconstruction from 2023-03-28 onward | Commercial/non-display rights, exact historical cost, 335-name/delisted coverage, sample integrity, first-receipt ledger |
| OptionMetrics IvyDB TradeFlow | **Best direct directional-flow hypothesis** in the existing research plan | Vendor sample, signed-side methodology, participant-proxy stability, license, permanent IDs, first-receipt/revision history and OOS beyond the vendor paper's 2022 endpoint |
| ORATS Near-EOD | Volatility-state context: IV surface, skew, term structure, OI and Greeks | Sample coverage is one date only; no signed aggressor or participant identity; historical first receipt, delisted retention and professional-use terms remain unverified |
| IVolatility | Potential consolidated alternative for EOD and trade-level data with stable IDs/adjusted deliverables | Current intraday schema/availability and commercial quote needed; indicative retail NBBO/Raw-IV cost is high |
| Cboe DataShop direct | **NO-GO under standard terms** for strategy creation | Separate written and executed strategy-use carve-out required |
| Massive Options individual plan | **NO-GO for this organizational/public workflow** under individual terms | Written professional/commercial license and private data environment required |
| ThetaData individual plan | Not cleared | Written professional/non-display and derivative-data rights required |

ORATS' current official page describes Near-EOD full-chain data from 2007, approximately 6,000 symbols, with Greeks/IV about 14 minutes before close; the recurring data is ready at night. The public sample audit on the existing Phase 61 branch contained 716,822 rows and 5,787 underlyings for 2024-01-03, with 324/335 current candidate tickers (96.72%). This is one-date current-list reach, not historical F80 coverage. ORATS does not supply independent stock prices in its option chain, and the sample did not expose a validated multiplier/deliverable. Use it only as a volatility-context candidate until those gates pass.

OptionMetrics' vendor DOOD paper remains a prior hypothesis, not independent validation. Its reported Jan 2016–Mar 2022 high-minus-low result does not establish 2023–2026 OOS or incremental net performance against frozen F80. Vendor retail/institutional categories must remain proxies, not account identity.

## 6. Pre-registered Databento/TradeFlow test design — not yet authorized

If a licensed sample passes, keep separate data regimes and hypotheses:

1. **Modern high-resolution flow (2023-03-28 onward):** use OPRA trades plus TCBBO. Infer side only from trade price versus the immediately preceding valid NBBO. Keep midpoint/inside-spread, stale, locked/crossed, missing, auction, multi-leg, late, corrected and otherwise ambiguous trades as separate/unknown categories. Do not force them into buyer/seller flow.
2. **Longer-history coarse proxy (2013-04-01 to 2023-03-27):** trades plus CBBO-1m may support a separate lower-granularity sensitivity. It is not the same signal as TCBBO and must not be silently concatenated into one homogeneous panel.
3. **Primary feature candidate:** signed option premium/notional imbalance by underlying, separated by calls/puts, DTE and moneyness, normalized by independent underlying share ADV and option liquidity. Do not call it delta demand unless a point-in-time IV/Greek and effective-dated deliverable source is available.
4. **OI:** use only after the actual next-morning receipt and deduplicate repeated venue copies. OI changes do not identify who opened or closed a position.
5. **Volatility context:** use ORATS/another independently licensed source for IV level, skew and term structure only after exact timestamp, coverage and license gates. Do not substitute ORATS option-implied underlying prices for the independent stock-price source.
6. **PIT:** record request start/end, actual first successful receipt, exact file/API version, raw hash, symbol manifest, schema, correction/bust lineage and parser version. Historical archive timestamps are not subscriber receipt. Execute at the first full regular session after actual receipt/validation; use a conservative next-session rule for any historical proxy and label it as a proxy, not strict PIT.
7. **Incremental test:** compare against frozen LTM/F80 with identical universe, exposure, costs, missing-data treatment and execution. Control prior 1/5/20/60-session returns, realized volatility, market/sector moves, earnings, liquidity, option volume, DTE, moneyness and IV regime. Use chronological development/validation/locked OOS, block bootstrap, issuer-clustered uncertainty, LOO and multiple-testing control. Distinguish prediction from return-chasing.
8. **Kill criteria:** reject if license/coverage/PIT fails; if the signal disappears after prior-return controls; if results rely on a few names/events; if realistic spreads/turnover erase the effect; or if incremental OOS performance versus F80 is not robust.

The modern TCBBO regime begins in 2023 and therefore has a shorter high-resolution history than the full 2013 archive. The longer CBBO-1m proxy is not equivalent. A robust test must report these regimes separately and must not claim a long homogeneous TCBBO history.

## 7. Decision

- Databento OPRA is promoted only to the next **documentation/sample-quote gate**, not to data acquisition or alpha testing.
- OptionMetrics TradeFlow remains the best direct-flow research hypothesis, subject to a sample and license.
- ORATS remains context-only, not a smart-money identity feed.
- Cboe DataShop, Massive individual and ThetaData individual routes remain blocked under their current terms for the intended use.
- No licensed data, raw market records or data-derived observations were added to the public repository.
- No signal, event study, backtest, OOS, bootstrap or LOO test was run.
- No workflow, production, universe, exposure, parameter, cost or holdout setting changed.

F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen.
