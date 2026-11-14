## Phase 397 — Form 144 PIT clock and event-payload integrity (2026-11-14)

- Offline audit of Phase 67 run 41828179718 / artifact 13334881835 (ZIP SHA-256 939d5564b14ce0f41df23a2c9ab681977cfde141cd0ea2b3c1213b1c5bfaf613; issuer_event_raw.csv SHA-256 fd20e338bd3624e7c1e85c39ab911f9fd5d1d78e8a20ed185e42db299a868b20). The 21,634-row panel contains 21,438 Form 144 originals and 196 144/A amendments.
- 168/21,634 notice_date values differ from SEC filing_date (141 earlier, 27 later); notice_date is rejected as a PIT clock. The Phase 67 CSV contains no accepted timestamp. SEC guidance supports a conservative next-regular-session-after-filing-date daily clock for Form 144/144-A, including filings submitted 5:30–10 p.m. ET; no intraday or same-day use is authorized because exact first public receipt is not recorded.
- Found 291 multi-candidate ticker rows (290 Z/ZG, one AMT/ASTS filer-versus-issuer case), 188 multi-tranche events, two zero/invalid proposed-unit rows, three zero/invalid proposed-value rows, seven zero/invalid shares-outstanding rows, and one 144/A parent reference not found in the 14-quarter census. Use tranche-level security-class mapping and explicit validity masks.
- Form 144 is treated only as a selective proposed insider-supply/order hypothesis, not a confirmed execution or “smart money” label. Historical F80 membership, security-class/ticker mapping, delisted/predecessor coverage and full amendment lineage remain blocking gates. No returns, alpha, OOS, bootstrap, LOO or holdout test; no purchase or SEC crawl; F80/production unchanged.
- Reproducible offline audit script, 3 unit tests and aggregate summary are in the Phase 397 report. See research/PHASE397_FORM144_PIT_CLOCK_AND_EVENT_INTEGRITY_2026-11-14.md.

# Current Smart Money Research State — 2026-11-14

## Phase 396 — CFTC TFF cadence implementation recheck (2026-11-14)

- Fresh official-page recheck confirms the CFTC's 2026-10-27 release 9316-26 is a plan for semiweekly COT by year-end, not proof that the TFF Futures Only Socrata dataset has transitioned. The COT landing page still describes Tuesday data / generally Friday release and still says once weekly; the 2026 release calendar lists 2026-11-16 as the next holiday-delayed release. The landing page displays reports dated 2026-11-03; the TFF data-hub page says last updated 2026-11-06. No second weekly TFF report date has been observed. Sources: https://www.cftc.gov/PressRoom/PressReleases/9316-26 ; https://www.cftc.gov/MarketReports/CommitmentsofTraders/index.htm ; https://www.cftc.gov/MarketReports/CommitmentsofTraders/ReleaseSchedule/index.htm ; https://publicreportinghub.cftc.gov/Commitments-of-Traders/TFF-Futures-Only/gpe5-46if.
- Run 43525140200 was a push-baseline run, not a scheduled prospective poll. The mainline state still has `last_capture_mode=branch_push_baseline`, latest report date 2026-11-03, and only baseline_manifest.json / historical_backfill.csv / state.json; no prospective events ledger exists yet.
- Phase 384's weekday cron is 22:15 UTC. The first weekday scheduled poll after this audit is Monday 2026-11-16 at 22:15 UTC, after the official 3:30 p.m. ET release. A report first observed then is usable no earlier than the next regular NYSE session. The actual first-seen timestamp, not the public schedule, remains the pipeline knowledge clock.
- PR #72 is merged. Initial Phase 395 CI run 43582784605 failed from a test import-path/cwd error; corrected run 43582818511 passed all 16 tests. Both are offline-only; no live capture or artifact. Actions has zero queued/in-progress runs as of 2026-11-14 10:21 UTC.
- Phase 387 remains frozen weekly. No semiweekly stitching, historical-backfill warm-up, forward outcome, alpha/OOS/bootstrap/LOO/holdout test or signal admission. F80 and production unchanged. See `research/PHASE396_CFTC_TFF_CADENCE_IMPLEMENTATION_RECHECK_2026-11-14.md`.

## Phase 395 — CFTC semiweekly transition readiness and atomic-batch guard (2026-11-14)

- Official CFTC press release 9316-26 (2026-10-27) announces a move to twice-weekly COT publication by year-end: Monday positions on Wednesday and Wednesday positions on Friday, both at 3:30 p.m. ET. The current official release schedule still lists the weekly calendar; its next release is Monday 2026-11-16 at 3:30 p.m. ET for positions as of 2026-11-10. The specific TFF Futures Only Socrata dataset gpe5-46if has not yet demonstrated the transition; verify actual report dates prospectively. Sources: https://www.cftc.gov/PressRoom/PressReleases/9316-26 and https://www.cftc.gov/MarketReports/CommitmentsofTraders/ReleaseSchedule/index.htm.
- Phase 384 weekday polling at 22:15 UTC is after the 3:30 p.m. ET release in both standard and daylight time and can observe either future release day. The first-seen timestamp remains the actual pipeline observation, not an inferred publication time.
- Found and fixed an atomic-batch edge case: if one scheduled API response contains multiple previously unseen report dates for the same contract, all share one first-seen timestamp and must not be treated as sequential observations. The newest new report per contract is the only research_observation_eligible row; older same-batch rows are retained as same_batch_catchup and ineligible. Revisions/late arrivals remain ineligible; contracts are handled independently; hashes still advance append-only.
- Added three offline regression tests and a dedicated no-network Phase 395 workflow. Raw-only Phase 388 event payload policy is preserved.
- Phase 387 remains a frozen weekly preregistration. No weekly/semiweekly stitching, count reinterpretation, threshold/horizon/sample-size changes or semiweekly model is authorized. Any semiweekly study requires confirmed TFF cadence and a separate preregistration with economic-time windows and overlap-aware inference.
- No live capture, return/alpha/OOS/bootstrap/LOO/holdout test, vendor contact, purchase or production change. F80 remains frozen. See research/PHASE395_CFTC_SEMIWEEKLY_TRANSITION_READINESS_2026-11-14.md.

## Phase 394 — Nasdaq Data Link Equities 360 / Bars price feasibility (2026-11-14)

- Official Nasdaq Data Link documentation describes Equities 360 as a Premium/custom API with 16,000+ U.S. companies across Nasdaq, NYSE, NYSE American and regional listings, including pricing, reference data and corporate actions. Its product page shows overall history from January 1998; the price-specific Bars/Charting family is separately described as historical since 2008. Do not conflate the overall product history with the Bars start.
- This is a stronger conditional price-history candidate than the public Nasdaq quote endpoint closed in Phase 393, but no authenticated sample, account, trial, key, price quote or vendor contact has been used.
- Unknown/failing gates: explicit inactive/delisted coverage, effective-dated security identity, record-known/first-delivery and correction vintages, exact seven-symbol coverage, field-level corporate-action adjustment policy, business-use rights and price.
- Decision: documentation-only candidate; no Phase 20C fallback admitted. If a lawful sample becomes available, first audit the seven missing names plus positive and inactive/delisted controls. Keep the 335-name universe/window unchanged; no ticker deletion, imputation or provider splicing.
- Official sources: [Equities 360](https://data.nasdaq.com/databases/E360), [Nasdaq Data Link Bars overview](https://www.nasdaq.com/es-es/products/data/data-link/api), [Nasdaq Basic context](https://www.nasdaq.com/products/data/equities/nasdaq-basic). Nasdaq Basic is not the same historical product.
- No prices, forward returns, alpha/OOS/bootstrap/LOO or holdout tests. F80 and production unchanged.

## Phase 393 — FINRA Phase 20C Nasdaq public endpoint retest (2026-11-14)

- Hosted run [43573077044](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43573077044) passed all 6 unit tests and research-only controls; artifact [14105217368](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43573077044/artifacts/14105217368), SHA-256 `407e9b5b42567e317d27139a5a95c4d0766d0dab978481d7020907325858d712`.
- ISO date parameters produced valid history for AAPL/MSFT/NVDA (2,499 rows each, 2016-11-14 to 2026-10-23) with very high daily-return concordance to Yahoo on common dates. Nasdaq omitted the first 15 sessions in the fixed 2016-10-24 start window; price adjustment/corporate-action equivalence remains unproven.
- All seven missing names (AVB, EA, EQR, LPRO, ROKU, WBD, WBS) returned application-level `rCode=400 / Symbol not exists` and zero rows despite HTTP 200. This is a symbol-resolution failure, not evidence that the securities have no historical data.
- SPY was incorrectly queried with `assetclass=stocks`; treat it as an invalid ETF control, not as a stock endpoint failure. No ETF-class retest was run. Three equity controls succeeded, but the preregistered all-four control flag remained false.
- **Decision:** stop using this public Nasdaq quote-history endpoint as a Phase 20C fallback; do not repeat the same request. The ISO-date defect was contributory for supported controls but did not resolve any of the seven missing names. No prices persisted, no returns/alpha/fallback/holdout test, no universe or production changes. Phase 20C remains blocked at 328/329 valid price histories.
- Next price-source candidate for feasibility-only review: official Nasdaq Data Link Equities 360 / Bars. Nasdaq describes 16,000+ U.S. companies across Nasdaq/NYSE/NYSE American/regional listings, premium custom API, and Bars history from 2008. This does **not** establish inactive/delisted coverage, historical record-known PIT, or complete adjustment lineage; no account, trial, sample or purchase has been used. Official references: [Equities 360](https://data.nasdaq.com/databases/E360), [Nasdaq Data Link Bars overview](https://www.nasdaq.com/es-es/products/data/data-link/api). Treat as conditional paid-source candidate only.

## Phase 392 — FINRA ATS scope reconciliation and OptionMetrics TradeFlow lineage (2026-11-14)

- **Phase 385 latest rerun is complete, not in progress.** Run [43536490386](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43536490386), job 132311996238, completed successfully at 2026-11-14 05:40:14 UTC. It retrieved 209/209 T1 partitions, 10,917,933 full T1 rows across 2,292 pages, and 438,822 raw `ATS_W_SMBL` aggregate rows. All 209 partitions had one valid `initialPublishedDate`, all matched the documented 21/22-day NYSE calendar (186 at 21 days; 23 at 22 days), and each mapped to the first NYSE regular session strictly after publication. Artifact [14100393795](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43536490386/artifacts/14100393795), ZIP SHA-256 `3630ce815040a2487ebfc86369552f21da3ee1b58e235f169cd0f604cffc3a46`. The earlier run 43536354917 also passed. As of 2026-11-14 06:08 UTC, no Actions runs are queued or in progress.
- **PIT boundary remains explicit:** Phase 385 sets `intraday_first_receipt_certified=false`, `effective_dated_security_master_gate_passed=false`, and `historical_return_test_authorized=false`. This is a conservative date-level availability bound, not an exact receipt ledger and not an alpha admission.
- **Count-grain reconciliation:** Phase 385 counts raw `ATS_W_SMBL` product-grain rows (438,822; 432,828 with `lastUpdateDate == initialPublishedDate`; 5,994 updated later). Phase 375 counts unioned symbol-week groups after reconciling distinct CTS/UTP product rows (438,798 groups; 432,804 stable; 5,994 revised). The 24-row difference is consistent with the distinct grains and Phase 374's product-type consolidation logic; no row-level crosswalk was retained. Keep these denominators separate and do not describe them as a failed reconciliation.
- **FINRA semantic correction:** FINRA Rule 4552 requires each ATS to report its weekly equity volume/trade count and use a unique MPID; FINRA publishes the reported volume for each security for each ATS and week. Therefore the 38 MPID/CRD-derived keys in Phase 375 are ATS/firm reporting entities (venues), not customers, traders, beneficial owners or verified institutions. The HHI/top-share measures are **off-exchange ATS venue concentration**, not institutional-investor or “smart money” concentration. Reclassify FINRA T1 ATS as a market-structure/venue-concentration candidate. It may be investigated for liquidity, venue fragmentation or concentration hypotheses only after security identity, historical-universe and price/delisting gates pass. Official sources: FINRA [Rule 4552 overview in the OTC Transparency User Guide](https://www.finra.org/sites/default/files/OTC-transparency-website-user-guide.pdf) and [Weekly Summary API](https://developer.finra.org/docs/api-explorer/query_api-equity-weekly_summary).
- **OptionMetrics product lineage is now confirmed at the product-family level:** the official TradeFlow page states that TradeFlow is an evolution of IvyDB Signed Volume. The September 28, 2026 methodology paper documents four relational tables (`Signed_Volume`, `Trade_Conditions`, `Market_Structure`, `Signed_Exchange`) keyed by option symbol, security identifier and date. The new paper confirms five proprietary flow buckets (Retail 1–3; Institutional 1–2); Institutional 1 is contained within Institutional 2 and must not be added to it. Institutional 2 is specifically aggressive liquidity demand at/through the quote and excludes passive execution, midpoint prints, patient position-building and market-making. These are execution-style proxies, not beneficial-owner identities or total institutional participation. The paper's worked example is one SPY/FOMC session, not an independent accuracy or predictive validation.
- **Remaining TradeFlow gates:** current product lineage is clear, but exact field-level backward compatibility with the repository's earlier four-table schema, methodology/version vintages, historical first-delivery/correction ledger, business-use license, broad F80/inactive-underlying coverage and sample reconciliation remain unproven. The advertised January 2016 history is backfill; it is not proof the current TradeFlow classifier or fields were available in 2016. Treat pre-prospective history as retrospective research only unless vendor vintages establish otherwise. No vendor contact, trial, account, sample acquisition or purchase occurred. Official sources: [TradeFlow product page](https://optionmetrics.com/ivydb-tradeflow/), [TradeFlow methodology paper](https://optionmetrics.com/research/g-desimone-a-gupta-ivydb-tradeflow-a-framework-for-options-volume-classification-and-microstructure-analytics/), [TradeFlow brochure](https://optionmetrics.com/wp-content/uploads/2026/08/TradeFlow-Brochure-1-1.pdf).
- No return, alpha, OOS, bootstrap, LOO or holdout test was run. No signal is admitted; F80, production, universe, capital, exposure and parameters remain unchanged. See [Phase 392 report](research/PHASE392_FINRA_SCOPE_AND_OPTIONMETRICS_TRADEFLOW_LINEAGE_2026-11-14.md).

## Phase 391 — ThetaData / OPRA options PIT feasibility (2026-11-14)

- Official ThetaData v3 subscriptions now document options tick history from 2012-06-01 at Pro (2016-01-01 Standard), OPRA trade_quote, quote, OI, IV and trade Greeks. trade_quote can pair each OPRA trade with a quote timestamp strictly earlier than the trade via exclusive=true; requests are bounded to one month and require an expiration. This is a strong independent raw-OPRA reconstruction candidate, but no sample, F80 coverage, inactive/delisted coverage, contract-adjustment, correction-vintage or first-receipt audit has been run.
- ThetaData OI is normally reported around 06:30 ET and represents the previous trading day's close. Its generated EOD report is created at 17:15 ET; created is a generation timestamp, not a first-receipt ledger. No historical file may be treated as strict PIT without verified first receipt/correction vintages.
- Retail Pro is listed at $160/month for individual personal use only; commercial use is separate. No account, key, trial, contact or purchase occurred.
- OptionMetrics IvyDB Signed Volume's current official page confirms buyer-/seller-initiated daily volume, 5m/30m snapshots and EOD, with advertised history for every option since 2016. It remains the primary conditional signed-flow candidate, but the exact relationship to the repository's four-table TradeFlow schema must be verified; 2016 backfill is not proof of contemporaneous availability.
- Cboe Open-Close covers BZX/C1/C2/EDGX, not all OPRA; it provides capacity × buy/sell × open/close and has venue/date-specific OI and volume convention breaks. Keep it complementary, not a substitute for consolidated raw flow. Databento OPRA remains a shorter-history independent timestamp/coverage check from 2023.
- Decision: no options source is PIT-, universe- or alpha-admitted. See [Phase 391 report](research/PHASE391_THETADATA_OPRA_OPTIONS_PIT_FEASIBILITY_2026-11-14.md). No forward-return test, OOS, bootstrap, LOO or holdout use. F80 remains frozen.


## Phase 390 — FINRA security-master/public-source feasibility (2026-11-14)

- FINRA T1's 209-week date-level publication clock and Phase 375 revision-stable panel are necessary but not sufficient for returns research: the weekly symbol field is not a permanent listing/security ID.
- SEC's public ticker/CIK/exchange files are periodically updated EDGAR search associations, with no guarantee of accuracy/scope and no historical record-vintage clock.
- Massive All Tickers is a newly ranked secondary effective-date cross-check (historical-date endpoint from 2003-09-10, active/inactive records), but Massive explicitly says the historical list is not a copy of the record as known then; old records can have later last_updated_utc, identifiers are incomplete/variable, and free-plan reference history is only two years. It fails strict record-known PIT.
- Databento remains the best-documented two-clock candidate (ts_record / ts_effective, listing/security/issuer IDs); CRSP remains the preferred active/inactive return/delisting benchmark; Norgate remains a separate index-defined universe candidate. No vendor sample, contact, purchase or API-key use occurred.
- Decision: no ticker-only FINRA joins and no historical FINRA return test until permanent/effective-dated identity, historical eligibility, inactive prices and terminal/delisting returns pass. See [Phase 390 report](research/PHASE390_FINRA_PUBLIC_SECURITY_MASTER_FEASIBILITY_2026-11-14.md).

## SEC source reconciliation — 2026-11-14

- **SEC Form 4 candidate identity (draft branches / PRs #31–#35):** the six non-contiguous archive cohorts contain 413 screened candidate rows. The 2023Q1–2026Q3 subset reaches 263/301 rows (87.38%) and 152/173 issuer-date event units (87.86%) with an identity anchor strictly before the transaction. The 2006Q1/2012Q1 XBRL route resolves 0/112; the legacy-HTML bridge salvages only a small candidate-level subset (one usable same-row class/exchange anchor group, two rows). The 95% identity gate is not met. No insider event study is authorized; do not continue expanding the same legacy HTML parser as a universal security master. See [PR #34](https://github.com/jafelix81/NuevaEstrategia/pull/34) and [PR #35](https://github.com/jafelix81/NuevaEstrategia/pull/35); both remain draft and unmerged.
- **SEC Schedule 13D/G identity/lineage (draft PR #36):** Phase 347's 200-filing structured sample has 197/200 valid nonzero CUSIP rows, 179 unique checksum-valid nonzero CUSIPs and no cross-subject collision in this purposive sample; four subject CIKs have multiple CUSIPs, so issuer-to-single-security collapse is prohibited. Phase 348 validated 2/2 explicit legacy-HTML parent references. Phase 349 produced 44 unique explicit parent targets (25 13D / 19 13G; 41 subject CIKs; 43 valid nonzero child CUSIPs; one zero sentinel quarantined). These are identity/lineage feasibility results, not alpha.
- **Human dependency — SEC parent retrieval:** Phase 350 [PR #37](https://github.com/jafelix81/NuevaEstrategia/pull/37) passed 10 offline tests but its first SEC Archives request returned HTTP 403; 0/44 parent documents were retrieved. The next retrieval requires a repository Actions secret named `SEC_USER_AGENT` containing a project identifier and monitored contact email. Do not put the email in source control or chat. Until the secret is configured, Phase 350/351 cannot verify parent CUSIP continuity and reporting-person overlap. PR #36 and PR #37 remain draft and unmerged; no historical security master or event study is admitted.
- **N-PORT / 13F disposition:** Phase 386's documentation-only [PR #62](https://github.com/jafelix81/NuevaEstrategia/pull/62) was merged to `main` on 2026-11-14 (commit `34384afcbf88a0888c2c4eaf9962d3048c5ad424`). The current N-PORT share-growth dose-response is archived/killed; broad-universe 13F remains parked pending deterministic historical security identity and PIT coverage.

No SEC source above changes the frozen F80 control or authorizes a return test. The Form 4 six-cohort sample is non-contiguous and purposively selected; the 13D/G 200-filing CUSIP sample is purposive. Do not interpret either as a population coverage estimate.


## Frozen control and promotion status
- `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen. No production, capital, universe, parameter or exposure changes.
- No Smart Money signal is admitted. No new alpha/OOS, bootstrap, LOO or holdout test has been run in this research cycle.
- The legacy holdout remains consumed and unavailable. No CAGR target or fixed portfolio holding-period limit is imposed.

## Active source work
- **FINRA T1 ATS:** Phase 375's 209-week revision audit passed (10,917,933 full T1 rows; 98.633996% revision-stable symbol-week coverage; 96.943175% stable share-volume coverage). Phase 385 run [43536354917](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43536354917) then validated the date-level publication clock for 209/209 weeks: one valid `initialPublishedDate` per partition, 209/209 schedule matches, 186 lags of 21 days and 23 holiday-adjusted lags of 22 days; first eligible session is the first NYSE session strictly after publication. Artifact [14096455337](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43536354917/artifacts/14096455337). This is a conservative date-level availability bound, not exact intraday first receipt. The second push-triggered run [43536490386](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43536490386) also completed successfully and produced artifact [14100393795](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43536490386/artifacts/14100393795). No further retrieval is needed. Phase 375 concentration is ATS/firm venue concentration, not investor or beneficial-owner concentration. Effective-dated security identity and historical universe membership remain unpassed, so no return/alpha test is authorized. See [Phase 385 result](research/PHASE385_FINRA_T1_PUBLICATION_CLOCK_RESULT_2026-11-14.md).
- **CFTC TFF:** Phase 384 prospective first-receipt capture is active on `main` after PR #60 merged. The 3,035-row static archive remains diagnostic only and is not PIT-certified. Weekday capture is scheduled for 22:15 UTC. The first scheduled capture has not yet occurred; the next relevant CFTC release is scheduled for 2026-11-16 at 3:30 p.m. ET.
- **Phase 387 hypothesis:** the prospective ES/NQ Leveraged Money crowding/downside-risk preregistration is merged to `main` through [PR #65](https://github.com/jafelix81/NuevaEstrategia/pull/65), commit `43919cdb8de49b7804a8d9a973ae9393e4e45cff`. It is not a directional COT return strategy. The protocol fixes the prior-52 prospective mid-rank percentile, a single 80th-percentile high-crowding indicator, expanding OLS baseline using only fully matured prior outcomes, 20-session drawdown severity, OOS residual effect and paired MAE. Evaluation requires at least 52 matured training observations including 20 high/40 non-high, then 150 evaluation observations per contract; bootstrap seed is fixed at 20261114. Static CFTC backfill cannot supply features or training history. No test has started.
- **Phase 388 data-lineage correction:** merged to `main` in commit `9a57acb005f6496f707bfc6faf685925553930d4`. Scheduled CFTC event payloads now contain raw source rows, first-receipt metadata, hashes and eligibility flags only; archive-derived features and cadence labels are no longer attached. Hosted regression passed 13/13 tests ([43539923574](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43539923574)). Downstream Phase 387 features must be recomputed from prospectively first-seen eligible events only.
- **Options:** OptionMetrics TradeFlow remains the leading historical signed-flow candidate, but access, licensing, historical-vintage/PIT and broad-universe gates remain unresolved. Cboe Open-Close EOD sample accounting passed, but one-day C1 sample coverage is not a historical PIT or alpha pass. No vendor contact or purchase.
- **FINRA Short Flow / Phase 20C:** corrected economic retest remains blocked by seven unresolved original price histories. Do not alter the original universe to force a run.
- **SEC:** standalone Form 4 and the tested N-PORT share-growth/dose-response hypothesis are killed. 13F remains parked for security-identity/PIT coverage. 13D/G remains in identity/event-normalization feasibility, not alpha-ready.

## Immediate gates
1. Phase 385 date-level publication clock is complete on runs 43536354917 and 43536490386; do not repeat retrieval. The next FINRA gate is effective-dated security identity and historical universe membership.
2. Verify the first scheduled CFTC capture and preserve its actual first-receipt timestamp.
3. Accumulate at least 52 valid prospective weekly CFTC observations before computing the Phase 387 crowding reference; no archive substitution.
4. Require at least 52 fully matured prior prospective outcomes before Phase 387 evaluation, then at least 150 evaluation observations per contract with the preregistered event counts.
5. Resolve historical security identity and point-in-time universe membership before any FINRA ATS return test.
6. Keep candidate tests chronological, net of realistic costs, exposure-matched to frozen LTM/F80, and subject to dependence-aware bootstrap/LOO before promotion.

---

# Smart Money Research State

Updated: 2026-11-04

## Frozen control
- F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen.
- MOM120 is a validated control candidate but not promoted: realized portfolio metrics slightly exceeded LTM, but incremental daily excess was small and the block-bootstrap CI included zero.

## Phase 31 — FINRA short-flow × short-interest divergence
- Status: KILLED as independent alpha.
- Valid OOS run: 40164323397.
- PIT: short flow through signal close; short interest only after conservative knowledge date.
- Result: horizon-dependent sign reversal; economic spreads' bootstrap intervals included zero. Do not tune horizons to rescue.

## Phase 21C — SEC Form 4 insider transactions
- Status: KILLED as a standalone signal in the current frozen-universe diagnostic.
- Run 39369692938 completed successfully with 24 training signal dates and 6 untouched final OOS dates (2025-02-25 through 2026-09-29).
- Official SEC dataset coverage is strong from 2016Q1 through 2026Q3; 301/335 universe CIKs mapped in the current implementation. KnowledgeDate uses filing date and downstream requires KnowledgeDate < SignalDate; same-day filings are excluded.
- Training-selected features were BUY_DAYS20 (H5), BUY_EVENTS60 (H10), and BUY_ADTV20 (H20). Final OOS mean top-minus-bottom was -0.12% (H5), +0.65% (H10), and -0.46% (H20); all bootstrap 95% CIs included zero. Residualized Spearman means were negative at all three horizons (-6.33%, -2.54%, -2.99%).
- Decision: do not tune insider features/horizons to rescue this implementation. The dataset remains reusable for other hypotheses only if a materially different, pre-registered mechanism is justified.

## Phase 22C — SEC 13F feasibility
- Status: NOT PRODUCTION-READY; continue identity-resolution research only if it can materially improve coverage without lookahead.
- Run 40064660452 / artifact phase22c-sec-13f-mapping-audit-v6: name/former-name mapping coverage ranged from 70.4% (2016Q1) to 93.0% (2024Q1) across the frozen candidate universe; conclusion was INSUFFICIENT_COVERAGE_FOR_PRODUCTION.
- Run 40081509388 / artifact phase22c-pit-issuer-cusip-audit-v8: report-date 13F issuer/CUSIP mapping restricted to non-derivative common equity produced minimum coverage 54.8% (2016Q1); conclusion 13F_IDENTITY_MAPPING_NEEDS_FURTHER_RESOLUTION.
- Important: this is a data-identity feasibility result, not evidence against 13F economically. The direct PIT CUSIP route is preferable to name fuzzy matching, but still has material class/ADR/legacy-CUSIP ambiguity.
- Next decision gate: only pursue another 13F mapping iteration if it uses deterministic security identity resolution and materially improves the worst-quarter coverage while preserving PIT. Otherwise park 13F.

## Phase 23C — CFTC COT positioning
- Status: KILLED for the tested equity-index positioning hypothesis.
- Run 39375172026 completed successfully with 12 walk-forward test dates for NASDAQ and S&P 500 families.
- NASDAQ mean strategy return was +0.192% at H5 versus +0.890% unconditional and -0.460% at H20 versus -3.370% unconditional. S&P 500 mean strategy return was -0.049% at H5 versus +1.024% unconditional and -3.058% at H20 versus -1.443% unconditional; H20 hit rate was only 16.7% for S&P 500.
- Decision: no evidence of a robust incremental equity-selection edge. Archive rather than optimize feature/direction choices.

## Phase 24B — listed-options historical feasibility
- Status: current public OCC endpoint path is insufficient for event-level historical option-flow research.
- Run 39398787569 tested 11 historical sample dates. Contract-volume, DLP HTTP, and trade-volume endpoints returned effectively empty payloads; daily volume statistics were substantive, while volume-by-account-type was substantive on only 2/11 samples despite successful HTTP responses.
- Decision: do not infer historical options flow/open-interest/IV/skew from these endpoints. A future options experiment requires a source with stable historical contract-level identifiers, PIT availability timestamps, and broad coverage.

## Phase 27O — SEC N-PORT institutional holdings dose-response
- Status: KILLED in the tested dose-response form.
- Run 39503800069 completed successfully across six annual formation periods (2020Q4–2025Q4) using the PIT 27N2 share-accumulation signal and a fixed 63-trading-day forward return.
- Top-minus-bottom decile returns were -11.77%, -5.56%, +12.03%, +6.12%, -4.78%, and -1.74% across the six periods. The sign is not stable and the sequence does not establish a monotonic institutional-flow effect.
- Decision: do not optimize the dose threshold or holding horizon. N-PORT remains archived unless a genuinely different pre-registered mechanism is proposed.

## Phase 32 — market microstructure
- Feasibility audit indicates event-level historical order/quote data would be valuable, but reproducible execution currently requires a licensed historical dataset. Do not synthesize microstructure from inadequate aggregates.

## Phase 35/49 — SEC 13D/13G subject-issuer identity
- Superseding status: FILER-SIDE RETRIEVAL/PARSER PIPELINE PASSED FOR ITS SAMPLE; SUBJECT-SIDE UNIVERSE COVERAGE NOT PROVEN; ECONOMIC TESTING NOT AUTHORIZED.
- Corrected run 41575083622 completed successfully on 2026-11-03 using the repaired Phase 35 branch and published artifact `phase35-13dg-pit-event-crosswalk-audit` (SHA-256 `1ba55129f8a2f2365b37e20f557759fbccd2ab2f22781f03930065c11f16337`).
- Audit: 335 frozen-universe names; 307 selected CIKs; 27 unresolved tickers; 20,266 candidate filings; 20,265 resolved filings; 303 unique issuers; 14,541 amendments; 19,679/20,265 filings with event_date (97.11%); zero submission errors; one isolated SEC HTTP 503 resolution error.
- Resolved rows contain issuer_cik, filing_date and accession. KnowledgeDate is filing_date. The resulting dataset is now suitable for the next identity/event-normalization gate; it must not yet be treated as alpha evidence.
- Important correction to the old Phase 49 diagnosis: the old primary-document parser was invalid, but the repaired Phase 35/28D pipeline now provides issuer-level identity. The repository state should no longer describe 13D/13G as currently blocked by the old parser.
- Remaining gates: deterministic amendment/original-event consolidation; 13D vs 13G mechanism separation; reporting-person/group normalization; historical active-universe membership; coverage analysis of the 27 unresolved F80 names; and only then a pre-registered economic hypothesis versus frozen LTM/F80.
- No F80/LTM changes and no 13D/13G alpha claims are permitted until those gates pass.

## Current priority
- Keep the frozen F80/LTM control unchanged.
- Do not spend further cycles rescuing FINRA, the existing Form 4 standalone hypothesis, CFTC COT, or the current N-PORT dose-response hypothesis.
- Advance 13D/13G from identity/PIT feasibility into event normalization and historical active-universe validation.
- In parallel, prioritize Smart Money sources that can deliver genuinely different information with reliable PIT timestamps: reproducible institutional/options microstructure and deterministic institutional-ownership sources. Options remain conditional on broad historical coverage, stable contract-level identifiers, access/licensing and reproducibility.

## Research principle
"Smart money" is a hypothesis, not an assumption. Candidate sources must pass historical coverage, ex-ante availability, timestamp/PIT, universe overlap, incremental-information, chronological OOS, bootstrap and LOO tests before portfolio promotion.


## 2026-11-04 update — Phase 71–82 feasibility and scope corrections

### Historical universe is still a hard research limitation
- Phase 71 traced the original 335-name universe through Phase 0/5/6/8/9 and the recovered Phase 9D CERE script. The same 335 unique tickers are present, but no reproducible screening rule, source date, inclusion/exclusion criteria, replacement ledger or historical membership snapshots were recovered.
- The Phase 68 current SEC ticker map now resolves 335/335 names to 319 distinct candidate CIKs. Six CIKs are shared by multiple tickers and two tickers have multiple CIK candidates. Fund series/class IDs are retained, but current mapping is not historical security identity.
- Consequence: historical tests on the fixed 335 remain conditional on a present-day curated list. Do not describe them as a fully PIT, survivorship-bias-free eligible cross-section. A PIT security master cannot restore omitted securities or historical membership.

### 13D/13G: role-correct parser passes, subject discovery remains open
- Phase 72 structured XML parser and schema tests passed; 13D and 13G use distinct schemas, and amendments carry direct previousAccessionNumber links.
- Phase 73/77 corrected 80-filing complete-submission pilot: 80/80 files parsed; XML issuer = SEC header SUBJECT COMPANY in 80/80; XML filer = header FILED BY in 80/80; accession/form/filing-date concordance 80/80. Acceptance timestamp matched submissions API for 54/54 records where that secondary API metadata existed. Reporting-person rows: 147. This is a small filer-side validation sample, not a global subject-issuer census.
- Important identity correction: accession-prefix CIK is the submitting account and can differ from the beneficial owner named in FILED BY. Keep submitter, filer, subject issuer and reporting-person identities separate.
- Phase 74/76 found the global SEC quarterly master index as a candidate discovery route. FOXA control 0000950157-25-000788 is archived under subject CIK 0001754301 while the accession prefix is a different submitting account. The index CIK and archive-path CIK remain candidates until the SEC header/XML confirms role.
- Phase 78 exact-CIK EFTS queries did not recover the four cross-filer positive controls. Phase 79's unit tests passed, but its live query diagnostic was not triggered; no live EFTS pass is established.
- Phase 80 raw Entity Landing Page audit: five pages returned HTTP 200, but none of six known accessions appeared in raw HTML. The SEC JavaScript exposed legacy own-disp links; Phase 81 corrected the interpretation: getissuer/getowner are tied to insiderTransaction flags and Forms 3/4/5, not a cross-filer 13D/13G subject index. The 13D/G beneficialOwnership display is filtered from the issuer page's own submissions. Phase 81 is archived as a source-scope false lead; no live SEC request was made.
- Phase 82 prepares a 43-quarter (2016Q1–2026Q3) global master-index-only audit, with raw index snapshots, retrieval timestamps/hashes, form counts and overlap against the 319 current candidate CIKs. Offline CI runs 41877316897 (Phase 81) and 41877957909 (Phase 82) are queued with no runner assigned; neither live SEC crawl has been triggered. The Phase 82 workflow still needs to pass the frozen candidate-CIK file into the index-only command before its explicit live trigger.

### Options data: best candidates are stronger, but no economic gate passed
- Phase 61 ORATS public Near-EOD sample: one date, 716,822 rows, 5,787 underlyings, 324/335 current tickers (96.72%). Core schema present; volume/OI/IV fields contain many true zeros. Snapshot is approximately 14 minutes before close, OI is prior-night, and file publication/PIT, delisted retention and contract multipliers remain unverified. ORATS is context (quotes/OI/IV/Greeks), not signed flow.
- Phase 54 Cboe Open-Close EOD public sample: C1 20% sample, 23,179 contract rows, 288/335 current tickers (85.97%), all required participant/open-close fields present. Cboe capacity labels are not investor identities; Customer includes retail and institutions. Venue coverage is not full OPRA; full history, price, PIT delivery and contract mapping remain conditional.
- Phase 55 Cboe Option EOD Summary sample passed schema only on four underlyings (SPX, SPY, TSLA, VIX); 335-name coverage was not tested. Cboe Option EOD is context, not participant flow.
- Phase 59–63 vendor screen: OptionMetrics IvyDB + Signed Volume is the highest-priority historical signed-volume candidate (advertised from 2016); IVolatility EOD/trade-level OPRA is a potentially richer alternative (EOD advertised from 2005, trade guide history from 2014 but current schema/coverage must be reconfirmed); ThetaData OPRA trade_quote offers transparent trade/NBBO reconstruction but historical corrections, delisted coverage and business licensing are unresolved. Databento OPRA is a conditional independent reconstruction route. MIAX Open-Close is a later venue replication candidate.
- No data purchase, vendor entitlement, PIT-vintage proof, historical F80 optionability coverage, or alpha test has been completed. No source is promoted as "smart money".

### Current next actions
1. Complete the Phase 82 43-quarter master-index coverage audit only after offline CI passes and the queued jobs clear; preserve raw indexes and candidate overlap but do not infer subject role from CIK overlap.
2. If Gate A passes, run only a deterministic stratified complete-submission sample and measure subject/filer identity, candidate recall and filer-only false positives before any broad filing download.
3. In parallel, seek a written sample/quote and exact business-use/PIT terms for OptionMetrics Signed Volume and/or IVolatility/ThetaData raw trade+NBBO; no purchase without explicit authorization.
4. Keep Cboe Open-Close as the strongest existing public-sample participant-capacity candidate, but do not spend on MIAX or multi-year history until a Cboe hypothesis has a data gate and preregistered test plan.
5. Keep the fixed-335 universe limitation visible in all OOS interpretation; reconstruct historical membership separately before claiming a general cross-sectional edge.

F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen. No forward-return or alpha test was run in Phases 71–82, and no production feature or portfolio parameter was changed.

## 2026-11-04 superseding correction — Phase 87 filer/subject identity audit

- **Phase 35 run 41878429289 / artifact 13363886486 is rejected as a subject-issuer event panel.** Its code queries `data.sec.gov/submissions/CIK{cik}.json` for each target ticker CIK and assigns that queried CIK to `issuer_cik`; it does not consistently resolve the structured 13D/13G `issuerCik` / SEC header `SUBJECT COMPANY` role. The 20,266 rows are a CIK-submissions/filer-side extraction diagnostic, not 20,266 validated subject-issuer events.
- Confirmed SEC positive control: artifact row accession `0000895421-24-000178` was labelled `MS` / CIK 895421. The SEC XML for linked accession `0000895421-25-000185` identifies `previousAccessionNumber=0000895421-24-000178`, subject issuer CIK 1793855 (abrdn Global Infrastructure Income Fund), and reporting persons Morgan Stanley / Morgan Stanley Smith Barney LLC. It also says the prior 2024 filing misstated its event date. See [official SEC XML](https://www.sec.gov/Archives/edgar/data/895421/000089542125000185/primary_doc.xml).
- Additional artifact defects: `filing_lag_business_days` is invalid (19,539 rows equal -1 due to a negative-range bug); one row per accession plus first-match regex helpers does not preserve all reporting persons; old-submissions JSON exceptions are swallowed. The 97.11% event-date field coverage is not subject-issuer coverage.
- Phase 35 is therefore **filer-side diagnostic only** until rebuilt from global index discovery + role-aware complete submission/XML parsing. No Phase 35 rows may enter alpha tests.
- Detailed audit: [Phase 87 report](https://github.com/jafelix81/NuevaEstrategia/blob/phase87-13dg-filer-subject-correction/research/PHASE87_13DG_FILER_SUBJECT_IDENTITY_CORRECTION_2026-11-04.md).

### Phase 84 live role-aware pilot

- Offline tests passed on run 41914491120; the disjoint 600-filing SEC role-aware pilot is currently running after the frozen Phase 82 index artifact (run 41892370262 / artifact 13353118959) downloaded successfully.
- Do not launch another SEC retrieval workload until Phase 84 completes. Phase 69's Form 144 live scan was skipped and remains unexecuted.
- Phase 83's original 120-filing preregistered gate failure remains unchanged. Phase 84 can authorize only the next subject-coverage/event-normalization gate, not alpha or production.

### Options source work — Phases 85–86

- Cboe Open-Close EOD remains the first practical participant-capacity/open-close sample candidate; OptionMetrics IvyDB Signed Volume remains the parallel historical signed-aggressor-flow candidate. Neither has passed historical F80 optionability coverage, point-in-time delivery, licensing and sample gates.
- Full Cboe Trade-by-Trade history is not economically justified at current quoted prices; no vendor was contacted or purchased.
- Phase 86's preregistered design separates Cboe participant capacity/position-side flow from OptionMetrics aggressor-signed volume and explicitly controls for return-chasing, leverage, volatility and dealer-hedging explanations. See [Phase 86 design](https://github.com/jafelix81/NuevaEstrategia/blob/phase85-cboe-options-flow-source-feasibility/research/PHASE86_OPTIONS_FLOW_ECONOMIC_HYPOTHESES_AND_PIT_DESIGN_2026-11-04.md).

F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen. No forward-return test or production change was made in this update.

## 2026-11-04 — Phase 88 CFTC TFF feasibility and source triage

- Phase 88 screens CFTC Traders in Financial Futures (TFF) as a **broad equity-index regime** input, not stock-level alpha. Official archives include S&P 500 and Nasdaq-100 contracts and public weekly position data by Dealer/Intermediary, Asset Manager/Institutional, Leveraged Funds, and Other Reportables.
- Historical data are available back to 2006, but early classifications are backcast. The CFTC explicitly states that historical publication dates are not centrally available beyond the latest 13 months. The 2025 funding lapse caused a report dated 2025-09-30, originally due 2025-10-03, to be published 2025-11-19. Therefore a standard Friday-after-Tuesday PIT rule is invalid in that period.
- Decision: retain TFF only as a secondary macro-regime candidate. Strict PIT gate fails until a reproducible historical publication calendar is reconstructed; no return test is authorized. See [Phase 88 feasibility audit](https://github.com/jafelix81/NuevaEstrategia/blob/phase88-cftc-tff-index-positioning-feasibility/research/PHASE88_CFTC_TFF_EQUITY_INDEX_POSITIONING_FEASIBILITY_2026-11-04.md).
- Other public microstructure candidates remain gated: SEC FTD has broad raw coverage but Phase 45 could not prove historical active-universe identity; SEC MIDAS has long daily coverage but no reliable per-quarter historical release timestamps; Cboe market-center volume is aggregate by market center and is suitable only as a possible market-regime control, not a stock-selection signal.
- Form 144 remains a more concrete event-panel candidate than the invalidated Phase 35 13D/G extraction: Phase 67 validated XML subject/filer roles and 21,634 issuer-event rows in a 2023Q2–2026Q3 census, but historical F80 membership, security-class/ticker mapping, acceptance-time availability and amendment-chain semantics still block alpha. Phase 69's ten-CIK incremental scan remains unexecuted pending completion of Phase 84 SEC retrieval.

### Current execution

- Phase 84 live disjoint 600-filing 13D/13G role-aware pilot: run 41914491120; offline tests succeeded, Phase 82 artifact downloaded, live SEC retrieval still in progress at the latest check. No additional SEC scan has been launched.
- Phase 87 invalidates Phase 35 run 41878429289 as a subject-issuer panel; preserve it only as filer-side diagnostic.
- No forward-return test, feature tuning, vendor purchase, or production change. F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen.


## 2026-11-05 — Research governance and source-gate supersession

### Research objective and model-selection policy
- Adopted `research/RESEARCH_OBJECTIVE_AND_MODEL_SELECTION_POLICY_2026-11-05.md`.
- The objective is robust net return relative to risk, drawdown/tail control, capacity, liquidity and execution feasibility; **no CAGR target** and no fixed holding-period limit.
- F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen as a benchmark/control, not a protected incumbent. A standalone challenger may replace it; F80 may be retired. No forced blend or ensemble. Independent, complementary and regime-specialized models are all eligible, but each must pass the same chronological OOS and economic gates.
- Research priority is based on expected value of information and source feasibility, not on novelty, vendor marketing or a single user observation. No vendor contact or purchase without explicit consent.

### Phase 96 — Phase 35 subject-issuer identity revalidation
- Run 41915300321 completed successfully and produced artifact 13378568483 (ZIP SHA-256 `db1be2f91f10aab72e6e13dd1f3f10105d40800c7f3ea04b6e1c7d7b0256b55f`). Offline inspection of its 20,253-row `phase28d_events.csv` found that accession `0000895421-24-000178` and linked amendment `0000895421-25-000185` are assigned to ticker MS / CIK 0000895421.
- The official SEC XML for the 2025 amendment identifies Morgan Stanley (CIK 0000895421) as the submitting filer and abrdn Global Infrastructure Income Fund (subject issuer CIK 0001793855) as the issuer; the amendment references the 2024 accession and says the prior filing misstated its event date. The Phase 35 row also retains 2024-12-31 as event date despite a 2024-02-12 filing date.
- Decision: Phase 35 run 41915300321/artifact 13378568483 is **diagnostic only, not a subject-issuer panel**. Exclude its rows from issuer event studies, returns, features and model training unless rebuilt and role-validated row by row. See `research/PHASE96_PHASE35_SUBJECT_IDENTITY_REVALIDATION_2026-11-05.md`.
- Do not repeat the CIK-specific crawl to reconfirm this known failure. Keep it separate from the role-aware Phase 84/89/91/93 sample.

### SEC 13D/G role-aware feasibility — corrected status
- Phase 84 live retrieval run 41914491120 retrieved and hashed 600/600 complete submissions with zero fetch errors. Its original workflow status remains **FAIL** because the first mandatory-XML denominator incorrectly counted one SC TO-T/A tender-offer record as Schedule 13D/G.
- Phase 89 corrected the denominator using actual SEC-HEADER form/date; 192/192 actual mandatory Schedule 13D/G XML documents were present. Phase 91 independently replayed 600/600 hashes and timestamps, parsed 200/200 structured XML filings, and reconciled XML subject/filer/form to SEC-HEADER 200/200 with zero errors. Do not rewrite the original Phase 84 run conclusion.
- Phase 84 candidate audit: 367 target-CIK candidate accessions; 89/232 unique-candidate rows resolved to target subject (38.36%); 135/135 ambiguous rows resolved to target subject; 143/367 (38.96%) were filer-only false positives. Candidate-population estimate is descriptive and not an inferential population estimate.
- Phase 93 reparsed 200/200 structured filings with zero hash/identity errors and 17 regression tests passed. Of 97 amendments, 51 lacked explicit previousAccessionNumber; only two unique parent candidates were emitted and neither was confirmed. Event tags are keyword triage, not investor intent. No returns test authorized.

### Form 144 — incremental current-CIK extension
- Phase 67 completed current-CIK census for 14 quarters (2023Q2–2026Q3): 21,648 candidates, 21,634 issuer-event rows, 14 filer-only false positives excluded, zero unresolved rows, zero XML processing errors, and 280/280 controls concordant.
- Phase 68 expanded the current map to 335/335 tickers and 319 candidate registrant CIKs; fund series/class identity must not be fanned out across every ticker under a trust.
- Phase 69 run 41959603351 is currently in progress on branch `phase69-incremental-form144-fund-registrants`; offline regression tests passed. The incremental ten-CIK SEC scan is running. Do not launch a duplicate while this run is active. No economic test is authorized.

### Binding blocker and current priority
- Phase 70/71 did not recover the original 335-name universe-selection rule or dated historical membership. Fixed-335 results remain conditional on a present-day curated set; a security master alone cannot restore omitted delisted/failed names.
- After Phase 69 completes, prioritize a PIT broad-universe/security-master feasibility decision (Databento/AlgoSeek/CRSP/Norgate candidates already audited) and a separate broad-universe research line if the original F80 rule cannot be recovered. Do not silently replace F80's universe.
- Keep FINRA short-flow × short-interest, tested standalone Form 4, CFTC equity-index positioning and tested N-PORT dose-response killed. CFTC TFF remains regime context only pending historical publication-time reconstruction.
- DOOD is **conditional, not automatically prioritized**: Phase 94 arithmetic tests passed 12/12, but Phase 95 did not pass units/history/PIT gates. No vendor contact, purchase, data acquisition or return test.
- No F80/LTM production changes, no forward-return test, and no strategy promotion were made in this update.


### Phase 97 — PIT security-master and broad-universe source re-ranking
- Added `research/PHASE97_PIT_SECURITY_MASTER_AND_BROAD_UNIVERSE_SOURCE_RERANK_2026-11-05.md` after a fresh official-documentation review.
- Current ranking: CRSP is the preferred active/inactive return and delisting benchmark if accessible; Databento is the best-documented two-clock PIT reference layer (`ts_record` / `ts_effective`, listing/security/issuer IDs), but public docs disagree on history start (2005 vs 18 years) and US class-share symbology needs careful joins; Norgate offers daily exact index membership and stable `assetid` for a separate Russell/Nasdaq universe but its trial is only two years and its index membership lacks announcement dates; AlgoSeek ASID is a useful lifecycle crosswalk but record-known vintages remain unproven.
- If the original F80 335-name selection rule remains unrecoverable, build a separate broad-universe line (index-defined or all eligible major-exchange common equities). Freeze the eligibility/security-type/lagged-liquidity rules before return inspection. Do not silently replace F80's universe.
- No vendor contact, purchase, data acquisition or returns test occurred.


### Phase 98 — Phase 69 Form 144 incremental scan completed
- Run 41959603351 / artifact 13385365595 completed successfully; artifact SHA-256 `f84644200a8925c6fc190a823ca0dcd6b40c7bee127a8d2740a5ea67cae56519`.
- The 14-quarter 2023Q2–2026Q3 scan found **zero candidate accessions** involving the ten newly mapped current fund-registrant CIKs. New/overlap accessions: 0; incremental issuer events: 0; no XML errors or unresolved rows. The expanded panel remains unchanged: 21,648 candidates, 21,634 issuer events, 14 filer-only false positives excluded, 289 unique issuer CIKs, and 280/280 controls concordant.
- Qualification: the original run reported `data_gate=PASS`, but XML-specific checks had zero denominators and were vacuous. The Phase 69 branch was corrected after the run to mark XML identity validation `NOT_APPLICABLE_NO_CANDIDATES` and the overall result `PASS_NO_INCREMENTAL_CANDIDATES`; two offline regression tests were added. No SEC rescan was performed for this code-only correction.
- Decision: close this ten-CIK extension as no incremental coverage for the tested period. Do not repeat without a materially changed candidate set/period. No forward returns or supply-pressure feature test.
- See `research/PHASE98_PHASE69_FORM144_NO_INCREMENTAL_CANDIDATES_2026-11-05.md`.
\n\n## 2026-11-05 code-only validation addendum\n\n- Corrected Phase 69 zero-candidate denominator semantics on branch `phase69-incremental-form144-fund-registrants` (script commit `c12e9631344d52f609743eed58599c08e36a7784`; test commit `9ef816fd4346f85edccdf3c2c542a8192afab8b8`). XML identity sub-gates now show `null` when no incremental candidate exists, and the summary reports `NOT_APPLICABLE_NO_CANDIDATES` / `PASS_NO_INCREMENTAL_CANDIDATES`.\n- Hosted offline regression run 41959973317 passed **45 tests**; the live incremental-scan job was skipped. No SEC rescan was performed.\n

### 2026-11-05 — Legacy workflow trigger guard
- Main commit `b4bd844b567d4779b474a212c73ef37f7928c30a` changed the Phase 22C 13F audit to manual-dispatch only (unrelated pushes no longer launch it) and disabled the Phase 35 CIK-specific 13D/G crawler after the Phase 96 subject/filer failure.
- An unrelated main-branch state update had already triggered legacy push-on-any-commit workflows before this guard landed. Phase 22C run 41960053553 was cancelled. Phase 35 run 41960053552 remains reported in progress; guarded replacement run 41960188506 is pending with the audit job disabled. The available GitHub connector does not expose a direct cancel action, so this run may require manual cancellation if it does not clear. No further Phase 35 crawl was intentionally dispatched.
- Future research-state commits do not match the new workflow path filters and should not trigger these SEC jobs.
