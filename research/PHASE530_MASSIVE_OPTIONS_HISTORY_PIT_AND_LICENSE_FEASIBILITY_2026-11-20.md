# Phase 530 — Massive Options historical coverage, PIT and license feasibility audit

**Audit date:** 2026-11-20 UTC  
**Main HEAD at preflight:** `49bf4c2a6529fa1eb4b64e7a1f22a147952071f9` (Phase 529)  
**Disposition:** **BEST CURRENT CONDITIONAL OPTIONS DATA CANDIDATE; NOT LICENSE-CLEARED FOR THIS PUBLIC REPOSITORY, NOT STRICT-PIT ADMITTED, NOT 335-NAME COVERAGE VERIFIED, NO DATA OR ALPHA ADMITTED.**

## 1. Preflight — current repository state

Before this source audit:

- Main HEAD was `49bf4c2a6529fa1eb4b64e7a1f22a147952071f9`; the latest main commits were the three Phase 529 commits.
- The latest 100 Actions runs contained no queued or in-progress run. The event=schedule inventory contained 38 runs; latest SEC scheduled captures remained Form 4 [44716430351](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44716430351), completed 10:07 UTC, and Form 144 [44720422923](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44720422923), completed 10:35 UTC. No later SEC scheduled run was visible at 16:15 UTC.
- Form 4 run 44716430351 passed both jobs and its live job appended 33 bounded metadata rows, parsed 10 accessions into 37 detail rows, left 1,213 bounded accessions, and reported zero signal-eligible rows. Its job did **not** run the Phase 525 owner-enrichment or crosswalk steps because it preceded the Phase 525 merge.
- Form 144 run 44720422923 passed both jobs, migrated 448 rows, appended 52 feed-observation rows, found no new accessions, and completed without parser/feed errors. It also preceded Phase 525 and does not validate the Form 4 owner crosswalk.
- The Form 4 workflow YAML on main contains the scheduled Phase 525 owner-enrichment and crosswalk steps. The expected `reporting_owners.csv` has not yet been created on main.
- FINRA Reg SHO run [44669121290](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44669121290) completed successfully as a workflow, but its live poll returned 8 HTTP 200 files, 8 invalid files, 0 valid files and 0 eligible observations. This remains the first post-Phase-515 live validation gap; parser success is not data validity.
- CFTC run [44668300202](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44668300202) retained 3,039 rows and 0 historically signal-eligible rows.
- Draft PR #186 (ThetaData feasibility) remains open. No workflow was dispatched, rerun, cancelled or duplicated.

Issue [#185](https://github.com/jafelix81/NuevaEstrategia/issues/185) remains the existing human check for SEC scheduled-workflow enablement. This audit does not repeat or close it.

## 2. Why Massive was evaluated

Phase 528 identified ThetaData as a conditional OPRA source, but its historical API is contract/symbol-specific and the published individual-use terms plus OPRA non-display classification need clarification. Massive's current documentation exposes a useful combination of:

- a contract reference index that includes **active and expired** contracts and supports an `as_of` date;
- daily historical Open Interest by contract;
- daily historical Greeks and implied volatility with disclosed snapshot time and model inputs;
- tick-level OPRA trades;
- top-of-book OPRA quotes/NBBO.

Official sources reviewed on 2026-11-20:

- Options product and market coverage: https://massive.com/options
- Options API overview and endpoints: https://massive.com/docs/rest/options
- Historical coverage matrix: https://massive.com/knowledge-base/article/how-much-historical-stock-data-does-massive-have
- Open Interest by Contract: https://massive.com/docs/rest/options/analytics/open-interest-by-contract
- Historical Greeks & IV: https://massive.com/docs/rest/options/analytics/greeks-iv
- Trades: https://massive.com/docs/rest/options/trades-quotes/trades
- Quotes flat files: https://massive.com/docs/flat-files/options/quotes
- Trades flat files: https://massive.com/docs/flat-files/options/trades
- Contract index: https://massive.com/docs/rest/options/contracts/contract-overview
- Current Market Data Terms (updated 2026-11-03): https://massive.com/legal/market-data-terms-of-service
- Current Individual Terms (updated 2026-11-03): https://massive.com/legal/individuals-terms-of-service

The product page advertises 1.67m+ options tickers, 7+ years and 100% coverage. The more specific endpoint history tables below govern this audit; headline counts are not evidence of coverage for our exact 335-stock universe.

## 3. Historical coverage and plan economics

The current individual **Options Advanced** plan is listed at USD 199/month. Its documented historical windows are:

| Dataset | Earliest documented history | Options Advanced access | Grain / key fields |
|---|---:|---|---|
| Contract reference | Active and expired contracts; point-in-time `as_of` query | Included | Underlying, OCC root, type, expiry, strike, multiplier, primary exchange, additional underlyings |
| Trades | 2014-06-02 | All history | Tick-level price, size, exchange, conditions, correction, participant timestamp, SIP timestamp, sequence number |
| Quotes | 2022-03-07 | All history | OPRA top-of-book quote/NBBO, sizes, exchange, nanosecond timestamps |
| Open Interest | 2022-09-01 | All history | Daily OI per contract, date, underlying, OCC root, call/put, expiry, strike |
| Historical Greeks / IV | 2022-09-01 | All history | Daily delta/gamma/theta/vega/rho and solved IV, plus underlying-price, dividend-yield and risk-free-rate inputs |

The API's Open Interest and Historical Greeks/IV endpoints can filter by `underlying_ticker` and date range. The Open Interest date is the trading session represented; the docs say new data arrives each morning for the prior session. The Greeks/IV snapshot is taken at 15:45 ET on a standard session or 12:45 ET on an early-close day. The flat-file documentation says daily trades/quotes files are updated around 11:00 ET for the previous day.

The contract index is documented to include active and expired listings. Contract Overview accepts an `as_of` date, which is a useful historical reference-state feature, but it is not itself proof of when a contract record first became publicly available.

### Data-volume constraints

- The 2026 daily options trades flat file is approximately 15 GB; the 2025 file is approximately 13.5 GB. Historical trades since 2014 are technically feasible for selective bulk research, but full-market storage and transfer still need a budget.
- The full-market options quote flat file is approximately 20–30 TB per year in recent years. A full-market quote archive is not a reasonable first step.
- A 335-underlying pilot should first use the filtered OI and Greeks/IV endpoints and a small, stratified contract-level trade/quote sample. Do not download the full quote archive.
- The exact request count, pagination, historical contract completeness and per-symbol coverage for the 335-name F80 universe remain unmeasured. The docs establish filters, not successful coverage for our list.

## 4. PIT and event-time controls

The source has useful event/report clocks, but it does **not** yet have a certified historical subscriber-first-receipt vintage.

1. **Trades:** preserve both `participant_timestamp` (exchange event generation) and `sip_timestamp` (SIP receipt). Neither is our subscriber first-receipt time. Options trades have no trade ID (the documented `id` field is empty); sequence numbers are unique per ticker but not consecutive. Preserve exchange, condition codes and correction indicator. Deduplication/correction handling must be audited before aggregation.
2. **Quotes:** preserve quote timestamps, exchange and bid/ask sizes. A trade-side estimate must use the last valid quote strictly before the trade; same-timestamp or stale quotes are ambiguous. Quote/trade side is an inferred aggressor proxy, not investor identity or a guaranteed buyer/seller label.
3. **Open Interest:** the record date refers to the prior trading session and the provider says the next session's figure arrives each morning. Use only after a prospectively observed receipt. OI changes do not reveal which side opened or closed and must not be described as net institutional buying.
4. **Greeks/IV:** the value is a 15:45 ET snapshot (12:45 ET early close), not a close-auction or next-session observation. Its inputs are exposed, which improves reproducibility. Historical first-public/first-subscriber receipt and correction vintages remain uncertified.
5. **Daily file delivery:** the published ~11:00 ET update statement is a provider schedule, not a historical per-file receipt log. Start an append-only first-seen ledger prospectively; record request start/end, first successful receipt, file hash, dataset/date, API version/plan and parser version. A backfilled timestamp must never be relabeled as first-seen.

For any historical event study before a prospective receipt ledger exists, the conservative fallback is to delay use until the next full trading-session close after the documented next-morning update, and to label that clock a provider-schedule proxy—not strict PIT. Do not admit it to a strict OOS test until the timing assumption is verified or a provider-certified vintage/availability SLA is obtained.

## 5. What this source can and cannot identify

**Can support:** contract-level activity, option prices and sizes, exchange, trade/quote conditions, top-of-book spread/depth, daily OI, IV and Greeks. It can support hypotheses about option-demand pressure, volatility repricing, skew/term-structure changes and options-implied risk state.

**Cannot directly identify:** beneficial owner, customer/firm/market-maker capacity, institutional identity, true opening/closing intent, or an unambiguous aggressor side for every trade. The absence of an options trade ID and the presence of multi-leg/complex activity require conservative exclusions and sensitivity analysis.

Treat "smart money" as a hypothesis only. Do not equate large premium, sweeps, OI increases or put/call ratios with informed institutional direction.

## 6. License and public-repository restriction — hard gate

The current Massive Market Data Terms (2026-11-03) state that individual information is licensed solely for the subscriber's own personal, non-business and non-commercial use; personal use expressly includes the subscriber's own research, analysis and investment activities using software/tools of their choice. The same terms prohibit sharing Information with anyone else, using it for an employer or organization, or using it in professional/commercial work.

The Terms define Information broadly to include third-party data and derived data that can identify, recalculate, reverse-engineer, decompile or create a substitute for source data. The OPRA Non-Professional Subscriber Agreement/Addendum further limits use to a natural person's personal investment activities and requires the subscriber to meet and continually attest to the non-professional criteria. Professional/non-professional classification is not inferred here.

**Implication for this repository:** NuevaEstrategia is public, and its Actions logs/artifacts and committed outputs may be publicly accessible. Do not place raw OPRA records, contract-level data, data-derived rows, or potentially reconstructable metrics in public GitHub commits, logs or artifacts. The fact that a workflow is technically able to call an API does not grant redistribution rights. Before using Massive from this public repository, obtain written clarification on (a) automated/cloud processing for the subscriber's personal investment research, (b) whether any derived model features/results may be stored or exposed in public code/Actions, (c) retention and deletion requirements, and (d) the exact OPRA non-professional classification. If public exposure is not permitted, keep all source data and data-derived outputs in a private controlled environment and publish code-only changes after legal review.

No terms were accepted, no account opened, no vendor contacted, no purchase made and no API request/sample downloaded.

## 7. Comparison with ThetaData (Phase 528)

| Dimension | Massive Options Advanced | ThetaData Options Pro (Phase 528) |
|---|---|---|
| Published price | USD 199/month | USD 160/month |
| Tick trades | Since 2014-06-02 | Advertised since 2012-06-01 |
| Historical quotes | Since 2022-03-07 | Tick-level quote access advertised since 2016-01-01 |
| Historical OI | Since 2022-09-01 | Historical OI endpoint advertised at Standard/Pro tiers |
| Historical IV/Greeks | Since 2022-09-01 | Historical IV/Greeks endpoints advertised at Standard/Pro tiers |
| Contract history | Active and expired index; `as_of` query | Contract-level API; PIT coverage still unverified |
| Access model | Individual Advanced plus OPRA non-professional agreement | Individual personal-use agreement; derivative-work/30-day expungement and non-display classification unresolved |
| Bulk scale | Daily trades files; quote files extremely large | Self-service flat files professional-only/7 days; historical bulk requires separate arrangement |
| Main unresolved issue | Public-repo disclosure and cloud/automated-use interpretation; exact 335-name coverage and first receipt | License/derived-work restrictions, OPRA non-display classification, bulk access and exact PIT coverage |

Massive is the **best current conditional candidate** for a filtered daily analytics pilot because its docs provide explicit historical endpoint windows, expired-contract lookup, underlying/date filters and a single Advanced individual plan. This is a source-feasibility ranking, not a recommendation to purchase or a claim that Massive has better data quality than ThetaData.

## 8. Preregistered research hypotheses — not yet tested

If legal, coverage and PIT gates pass, evaluate separately:

- **H1 — options-implied risk state:** IV level, skew and term-structure changes predict next-session/next-week realized volatility, downside tail risk or F80 drawdown. This may be a risk overlay, not a directional smart-money signal.
- **H2 — signed options pressure:** quote-conditioned trade imbalance, filtered by condition/exchange and measured only with a strictly prior NBBO, adds information about underlying residual returns beyond LTM/F80 and ordinary momentum/volume controls.
- **H3 — positioning confirmation:** changes in OI corroborate persistent flow, but OI alone has no directional sign. Test only as a separate interaction/confirmation hypothesis.
- **H4 — volatility risk premium:** option-implied versus subsequent realized volatility adds risk-sizing information after costs and liquidity controls.

Use the same 335-name point-in-time universe, identical exposure and costs versus frozen LTM/F80, chronological train/validation/test partitions, embargo for overlapping labels, no lookahead, delisting/corporate-action controls, bootstrap and leave-one-out stability, and untouched holdout. Distinguish prediction from return-chasing. Require incremental net economic value; kill and archive failed hypotheses. No signal is admitted by this source audit.

## 9. Decision and next gate

**Disposition: CONDITIONAL PRIORITY-1 OPTIONS CANDIDATE; DATA AND ALPHA NOT ADMITTED.**

1. Obtain written licensing/OPRA clarification before account, API key, cloud workflow or sample.
2. If permitted, run an authorized metadata-only/aggregate pilot across a stratified subset of the 335 universe, including liquid, less-liquid, renamed and delisted/expired-underlying cases. Do not expose licensed rows in public artifacts.
3. Verify contract coverage, option-root/class changes, corporate-action deliverables, OI/IV null rates, timestamps, corrections, condition codes, daily file receipt and revision stability.
4. Start prospective first-seen capture before using any daily feed as an ex-ante signal.
5. Only then construct a feature panel and test H1–H4 versus LTM/F80.

**No backtest, return test, OOS test, bootstrap, LOO, holdout access, signal admission or production change occurred.** `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen.
