# Smart Money Research — Phase 538 operational and prospective-data reconciliation

**Audit cutoff:** 2026-11-21 03:25 UTC  
**Main HEAD before this note:** `9a8ae93f3ec20eb42e4cd9d33293ba0448334fea`  
**Disposition:** new prospective CFTC observations captured; FINRA Reg SHO live collector still fails closed on duplicate symbols. No signal admitted.

## 1. Preflight

- Reviewed the latest 100 Actions runs, jobs, logs, artifacts, open PRs, branches and current research files.
- At the cutoff there were **0 in-progress, 0 queued and 0 waiting runs**. No workflow was dispatched, rerun, cancelled or duplicated.
- Latest scheduled runs were FINRA Phase 469 [44860690600](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44860690600) and CFTC TFF Phase 384 [44860341977](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44860341977).
- Phase 537 documentation PR [#196](https://github.com/jafelix81/NuevaEstrategia/pull/196) remains Draft. No production or baseline change.

## 2. FINRA Reg SHO — live capture remains blocked

Run [44860690600](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44860690600) completed both offline and live jobs successfully. The 59-test offline suite passed. The live job requested eight recent trade dates (2026-11-20, 19, 18, 17, 16, 13, 12 and 11):

| Result | Count |
|---|---:|
| HTTP 200 | 8 |
| Valid files | 0 |
| Invalid files | 8 |
| HTTP errors | 0 |
| First-seen / research-eligible observations | 0 |
| Signal-eligible observations | 0 |

All eight responses were rejected as `duplicate_symbol_in_consolidated_file`. The append-only poll ledger records response hashes and byte counts (542,484–566,746 bytes), but the raw files are not persisted. The state remains empty (`files: {}`); therefore there is no FINRA first-seen observation to label.

This is a different validation failure from the earlier `market_code_invalid` result. The parser now accepts comma-separated Market facility lists and fractional volumes, but still assumes a consolidated security-grain file has unique symbols. Do **not** simply sum or deduplicate duplicate rows: without seeing their row-level facility overlap and values, either action could double-count or erase real activity.

**Next technical gate:** add a metadata-only duplicate diagnostic to the collector (duplicate symbol count, per-symbol row count, distinct/overlapping facility-token sets, and exact-row duplicate indicator), while keeping the file ineligible and not persisting raw rows. Only after a scheduled capture reveals the duplicate structure should an aggregation or quarantine rule be considered.

FINRA describes Reg SHO Daily Short Sale Volume as daily short-sale volume aggregated by security for trades reported to FINRA facilities ([FINRA Developer Center](https://developer.finra.org/docs/api-explorer/query_api-equity-reg_sho_daily_short_sale_volume)). This is executed short-sale flow, not outstanding short interest or net directional positioning. The [OTC Markets comment to FINRA Regulatory Notice 21-19](https://www.finra.org/sites/default/files/NoticeComment/Daniel%20Zinn%20and%20Cass%20Sanford_12.3.2021_21-19%20-%20OTC%20Markets%20Group%20Comments%20to%20RN%2021-19%20%28Short%20Sale%20Reporting%29.pdf) also cautions that market-maker liquidity activity can make daily short-volume ratios misleading as a measure of directional short conviction. Even after parser recovery, this source must be tested as a flow feature, not labelled “institutional selling” by default.

## 3. CFTC TFF — second prospective weekly observation captured

Scheduled run [44860341977](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44860341977) passed all 16 offline tests and captured four new reports, each with report date **2026-11-17** and first receipt **2026-11-21 03:17:36 UTC**. The total historical panel now has 3,043 rows (853 each for E-mini S&P 500, Nasdaq Mini and DJIA; 484 for Russell E-mini). Historical backfill rows remain ineligible; no signal was generated.

Comparing the latest report with the prior prospectively captured report dated 2026-11-10 gives mixed positioning changes:

| Contract | Open interest change | Asset-manager net change | Dealer net change | Leveraged-money net change |
|---|---:|---:|---:|---:|
| E-mini S&P 500 | +79,271 (+3.93%) | -19,081 | -52,087 | +68,082 |
| Nasdaq Mini | +7,706 (+2.67%) | +10,115 | +10,421 | -24,895 |
| DJIA x $5 | +283 (+0.34%) | -9,788 | +8,196 | +2,134 |
| Russell E-mini | +19,154 (+4.35%) | +11,008 | -9,798 | +2,076 |

Net changes are contracts (long minus short); the source's raw long/short/spread categories are retained in the event ledger. The directions are not uniform across indices or trader categories. With only two prospectively observed reports per contract, this is a data-quality/feature-construction checkpoint, **not** a positioning signal or evidence of predictive skill. The latest first receipt occurred after Friday's equity close; the earliest executable equity session is Monday 2026-11-23. Do not backdate the report to its Tuesday report date.

## 4. SEC insider data — operationally useful, not yet signal-ready

- Form 4 run [44846461134](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44846461134) completed: 474 new accession observations; 10 structured filings parsed into 24 detail rows; the owner backfill processed 10 accessions and appended 15 owner rows.
- The strict Form 4/Form 144 crosswalk returned three descriptive matches: two proposed Atea sales (Bruce Polsky, 8,750 shares; Bruno Lucidi, 22,619 shares) and one prior-sale-history match.
- Both proposed Atea sales were tied in the Form 4 remarks to option-exercise costs and tax planning. They are a useful negative control against naive bearish insider-sale counting, not a bearish signal.
- Form 144 run [44847230610](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44847230610) completed with 91 events and 91/91 acceptance reconciliations.
- Crosswalk disposition remains descriptive only: zero signal-eligible matches. Exact public-availability time, transaction-line owner attribution, intraday execution time and historical F80 membership are not certified.

## 5. Phase 20C and broader-source gates

- The latest full-universe Phase 20C price census remains 328/335 valid histories. Seven configured names (AVB, EA, EQR, LPRO, ROKU, WBD and WBS) are inactive, renamed or acquired. Their terminal/successor total returns and corporate actions remain unreconstructed; no ticker drop, price-provider fallback or imputation is admitted. See [Phase 474](PHASE474_PHASE20C_DELISTED_UNIVERSE_CORPORATE_ACTION_RECONCILIATION_2026-11-18.md).
- Phase 487 rejected the Phase 20B continuous replacement rule and Phase 20C adaptive rule for promotion; Phase 20A residual IC remains exploratory only. The historical FINRA close-to-close labels lack a verified first-receipt clock. See [Phase 487](PHASE487_FINRA_PHASE20A_20B_20C_ADJUDICATION_2026-11-18.md).
- FINRA ATS Query API history remains 259 weeks (2021-11-15–2026-10-26); its aggregate HHI sample gate failed, and a security-level panel still needs PIT identity/universe reconciliation. The separate archive endpoint's HTTP 530 remains a stop condition for automated retries.
- FINRA Consolidated Short Interest still requires authorized credentials and a complete asynchronous snapshot. Options vendors remain conditional on licensing and PIT/coverage confirmation; no data was purchased or imported.

## 6. Decision and next work

1. Keep FINRA Reg SHO fail-closed; obtain row-level duplicate diagnostics before changing the parser's aggregation semantics.
2. Continue scheduled SEC and CFTC prospective captures; do not use historical backfill as a substitute for first-seen timestamps.
3. For CFTC, accumulate a materially longer prospective series before testing a market-regime feature; normalize category net positions by open interest and compare incremental value against the frozen baseline.
4. Keep all insider classifications conditional on transaction code, footnotes, plan status, owner linkage and availability time.
5. Keep Phase 20C price/corporate-action reconstruction as a hard gate.

No event study, backtest, OOS, bootstrap, LOO or return claim was made in this phase. No feature or signal was admitted. `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen; universe, parameters, exposure, costs, holding-period policy and production are unchanged.
