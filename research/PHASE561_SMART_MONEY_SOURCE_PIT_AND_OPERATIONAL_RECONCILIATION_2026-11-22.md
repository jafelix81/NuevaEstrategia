# Phase 561 — Smart Money source re-ranking and live-ledger reconciliation

**Audit cutoff:** 2026-11-22 19:53 UTC  
**Main at preflight:** `4b09dfc9f47b7491e2ca5b396e3ca5c83c72e864`  
**Disposition:** operational/source audit only; no new signal, event-return test, alpha or OOS result.

## 1. Repository and Actions preflight

- Actions API: 8,069 total runs; latest 100 = 96 success / 4 failure; zero active, queued, waiting or requested.
- Branches: 372 across four pages; open PRs: 72; workflow files: 94.
- Main includes Phase 560 PR #205, merged at 18:40:50 UTC. Merge commit: `7cd077ff8254ce2bcec7221ecf6b5fffdb322e58`; post-merge state commit: `4b09dfc9f47b7491e2ca5b396e3ca5c83c72e864`.
- Latest Phase 560 Phase 403 PR check [45056358699](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45056358699) passed 74/74 offline tests; live-capture was skipped as designed. Related Phase 460/461 checks also passed. Aggregate classifier artifact [14767855406](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45056179069/artifacts/14767855406) was downloaded and inspected.
- No active run was duplicated, dispatched, rerun, cancelled or modified.

## 2. Latest natural captures and artifact review

### SEC Form 144 — Phase 403 / Phase 560

Natural run [45052961790](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45052961790): both `offline-regression` and `live-capture` succeeded. Artifact [14765739720](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45052961790/artifacts/14765739720) was downloaded and inspected.

- 51 Form 144 + 2 Form 144/A feed entries; both feeds paginated completely, prior watermarks were found, no feed errors and no possible feed-window gap.
- No new accession/event. Ten already-known accessions were parsed; 42 detail rows appended.
- Ledger: 285 accessions / 2,114 detail rows; 278 accessions remain in the bounded backfill queue.
- Parse errors 0; source-hash mismatches 0; public-availability-certified filings 0; signal-eligible filings 0.
- Phase 560 recomputed the unchanged Phase 549 classifier on the current ledger: 9 positive explicit, 4 negative explicit, 1 ambiguous, 271 no mention; 103 accessions have formal plan dates across 64 distinct dates. One termination is separately flagged. The four negative cases are mechanical Fermi sell-to-cover/tax-withholding notices, not discretionary bearish sales.
- Important grain distinction: Phase 516's `research_observation_eligible_filing_headers=285` is a header-level descriptive field; Phase 403's poll summary still reports zero research-observation-eligible feed/event rows and zero signal-eligible rows. Do not describe the 285 headers as 285 usable signals or public-availability-certified observations.
- Form 144 is a proposed-sale notice, not execution confirmation. The plan date and first-seen poll receipt are not exact public-availability clocks.

### SEC Form 4 — Phase 476 / Phase 525

Latest natural run [44846461134](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44846461134): both jobs succeeded. Artifact [14683520646](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44846461134/artifacts/14683520646) was downloaded and inspected.

- 474 new accession observations; 988 accession-observation rows persisted. Feed pagination/watermarks succeeded.
- Bounded transaction-detail backfill parsed 10 accessions and appended 24 rows; 1,758 remain. Owner enrichment parsed 10 filings and appended 15 owner rows; 20 accessions remain in the owner queue. No parse/fetch errors.
- The strict Form 144/Form 4 crosswalk now has 3 descriptive rows: 2 proposed-sale matches and 1 prior-sale match, all for Atea Pharmaceuticals. The two proposed-sale matches map to distinct single owners (Bruce Polsky and Bruno Lucidi), each with Form 4 code S and disposal code D.
- Both Form 4 remarks contexts mention option exercise, exercise-price payment and tax planning/withholding; neither says open-market. The Form 144 was accepted before the Form 4, but execution intraday time is unknown. Historical F80 membership is unverified. All three crosswalk rows remain `signal_eligible=false`; this is an identity/semantic match, not evidence of informed discretionary selling or a predictive signal.

### FINRA Reg SHO — Phase 469

Latest natural run [44860690600](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44860690600): both jobs succeeded, but the live audit is not a data-quality pass. Artifact [14688803921](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44860690600/artifacts/14688803921) confirms 8 HTTP 200 responses, 8 invalid files, 0 valid files, 0 first-seen eligible rows and 0 signal-eligible rows. No raw market data was persisted. The capture predates the required natural post-Phase-539 validation; short volume must remain separate from short interest.

### CFTC TFF — Phase 384

Latest natural run [44860341977](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44860341977) passed its seven offline tests and the prospective capture. Artifact [14689726870](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44860341977/artifacts/14689726870) was downloaded and inspected.

- Four new report events were appended; total ledger 3,043 rows.
- DJIA, E-mini S&P 500 and Nasdaq Mini each have 853 weekly observations from 2010-07-20 through 2026-11-17; Russell E-mini has 484 from 2017-08-15 through 2026-11-17.
- First receipt was 2026-11-21 03:17:36 UTC. Metadata was stable; no revisions/late arrivals in this batch.
- Four new prospective vintages are not a return sample. No equity-level signal, forward return or alpha test is authorized. Treat TFF as a possible broad positioning/regime covariate, not security-level institutional flow.

## 3. Broader source re-ranking

| Source | Historical/coverage evidence | PIT and interpretation | Disposition |
|---|---|---|---|
| SEC MIDAS — Metrics by Individual Security | Official page lists 59 quarterly ZIPs, 2012 Q1–2026 Q3, 4,800+ securities and daily rows with trades, lit/odd-lot/hidden activity, cancels and order/trade volume | Public/free and broad, but page-level update date (2026-09-30) is not a per-quarter release/first-public timestamp. Daily observation date is not the package availability date. Ticker-only identity and historical F80 overlap still need audit. Market-structure metrics do not identify beneficial owners. | **Best next low-cost public market-structure candidate**, but no PIT/alpha admission until release-clock, ZIP integrity and universe-identity audits pass. |
| FINRA T1 ATS | 209 weekly partitions, 10,917,933 full T1 records and 438,822 target-grain rows; 209/209 publication dates map to the first NYSE session after actual publication | Date-level conservative publication clock validated. Firm/MPID concentration is venue concentration, not customer or institutional ownership. Effective-dated security master, historical universe and delisted returns remain open. | Conditional liquidity/venue-concentration control, not “smart money.” |
| Cboe OPRA Option Trades + Quotes | Official product documentation advertises common history from Jan 2012 and trade-level prints with prevailing NBBO; companion quotes/OI | Next-day SFTP delivery varies; historical first receipt, revisions/cancels/busts and per-symbol coverage are unverified. OI is start-of-day. Business-use rights and a lawful sample are unresolved. | Strongest conditional independent options-flow reconstruction candidate; no data or alpha admission. |
| OptionMetrics IvyDB TradeFlow | Advertises all U.S. options since Jan 2016 | Participant buckets are execution-style proxies, not beneficial-owner IDs. 2026 TradeFlow methodology versus historical recomputation/version and first-delivery vintages remain unresolved. | Conditional signed-flow candidate; do not treat “institutional” buckets as verified institutions. |
| SEC 13D/G | 13D remains the higher-priority ownership-event hypothesis versus delayed 13F/N-PORT | Existing 20,266-row panel remains quarantined pending SUBJECT COMPANY vs FILED BY repair, event-date adjudication and PIT availability. SEC retrieval requires a valid monitored `SEC_USER_AGENT`. | High research priority after identity/access gate; no event panel admitted. |
| FINRA Reg SHO | Latest live batch 8/8 invalid | No valid first-seen rows. Short volume is not short interest. | Rejected pending a natural post-fix capture. |
| CFTC TFF | 3,043 rows; four new prospective events in latest batch | Weekly futures positioning, not equity security flow; first-receipt ledger is prospective only. | Continue collecting; no signal test yet. |
| Phase 20C prices | 328/335 valid histories; seven inactive/acquired/renamed names | Terminal prices, successor consideration and corporate-action total returns remain unreconstructed. | No rerun/promotion with incomplete panel. |

Official MIDAS sources:
- https://www.sec.gov/data-research/sec-markets-data/marketstructuredata-security
- https://www.sec.gov/data-research/market-structure-data
- https://www.sec.gov/securities-topics/market-structure-analytics/midas-market-information-data-analytics-system

## 4. Operational blockers

- Phase 403 still declares cron `47 * * * *`. The latest schedule run was created at 18:04 UTC; no scheduled run is visible for the 18:47 or 19:47 UTC slots as of 19:53 UTC. This is an observed schedule-delivery gap, not proof that the workflow is administratively disabled. Issue #194 remains the tracking record; do not change cron or manually dispatch until the Actions enabled-state is checked.
- Form 4, FINRA Reg SHO and CFTC schedules are weekday-only; no Sunday run is expected for those workflows.
- PR #204 (Phase 559 SEC FTD credentials) remains Draft/open. The branch is 11 commits ahead and 3 behind current main; compare status is diverged. Refresh against main before any merge. The repository Actions secret `SEC_USER_AGENT` cannot be read or set through the connected interface. It must contain a project identifier and monitored contact email before the bounded two-file SEC sample. No live SEC FTD request was made.
- No SEC 13D/G bulk retrieval, Databento pilot, options subscription, API key, vendor purchase or licensed sample was initiated.

## 5. Research decision and frozen controls

The Atea Form 144/Form 4 crosswalk is a useful identity/semantic validation improvement, but the two matches describe option-exercise/tax-planning disposals with unknown execution time and unverified F80 membership. They are not an informed-flow signal. SEC MIDAS is the best next public, no-vendor-cost market-structure candidate, subject to a per-quarter availability-clock and identity audit.

- New signals admitted: **0**.
- Incremental evidence versus frozen LTM/F80: **none**.
- New return/event/OOS/bootstrap/LOO/holdout test: **0**.
- No changes to universe, costs, exposure, holding-period policy, holdout or production.
- `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen.

**Next valid work:** (1) preserve the Phase 560 classifier as descriptive only; (2) audit SEC MIDAS per-quarter publication/availability and actual 335-universe identifier coverage before downloading/backtesting; (3) obtain the natural post-Phase-539 FINRA capture; (4) keep collecting CFTC vintages; (5) do not merge PR #204 until it is refreshed and the SEC User-Agent prerequisite is satisfied.
