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


## 2026-11-05 — Phase 99: broad point-in-time universe charter

- User clarified that Smart Money Research must not be restricted to the current 335 F80 tickers. Adopted this distinction: **335 is the frozen F80 comparability universe, not the research universe ceiling**.
- Authorized a separate broad-universe research line while preserving F80 unchanged. Parallel tracks: (1) broad US primary-listed operating equities built from historical listing/security records; (2) Russell 3000 effective historical membership; (3) Nasdaq Composite effective historical membership; (4) frozen 335-name F80 control.
- Broad primary universe retains active and inactive securities, delistings, bankruptcies, mergers, relistings, IPOs after a fixed data/listing-age gate, ticker changes and multiple share classes. Common shares, ADRs, REITs and BDCs remain explicitly classified; ETFs/ETNs, funds, preferreds, warrants, rights, units, debt, options and OTC-only names are excluded from the primary operating-equity set unless studied as separate universes.
- Required identity model distinguishes effective time, record-known/publication time, retrieval time, event time and public-availability time. Ticker-only joins and current index membership applied retrospectively are prohibited.
- Added staged gates for historical coverage, two-clock PIT provenance, delisting/return integrity, reproducibility/licensing and final universe preregistration. **No forward-return or alpha test is authorized before all gates and a separate preregistration pass.**
- Source roles remain conditional: CRSP for inactive/delisted return validation; Databento for two-clock security identity; Norgate for historical index membership and delisted cross-check; AlgoSeek ASID as a lifecycle crosswalk pending record-known vintage proof. No vendor contact, purchase or data acquisition authorized.
- Phase 99 report: `research/PHASE99_BROAD_PIT_UNIVERSE_CHARTER_2026-11-05.md`.
- Next: recover Phase 70/71 artifacts/code to establish whether the original 335 selection rule is reproducible; if not, mark it unrecoverable and proceed only with the separately specified broad-universe feasibility gates.


### 2026-11-05 — User clarification: original 335 selection was arbitrary

- User confirms the 335 tickers were selected manually and arbitrarily; there was no formal selection methodology and the user does not recall a rule.
- Supersedes the earlier Phase 99 next step to recover/reconstruct the 335 selection rule. **Do not spend further effort trying to reverse-engineer it.**
- The 335-name list is a legacy F80 comparability set only. It is not a statistically defined sample, not a representative market universe, and not the primary universe for Smart Money Research.
- F80 historical performance must be described as conditional on the manually selected 335 names. Preserve the set only for exact legacy comparison; build the broad research universe independently from point-in-time security/listing records with explicit eligibility rules and delisted coverage.
- Phase 99 report corrected accordingly. No F80 change, data purchase, vendor contact, data acquisition or alpha test.


---

## 2026-11-05 — Phase 99/100 reconciliation and source triage

This section supersedes older forward-looking notes in this file where they conflict with the latest user clarification or the Actions evidence below.

### Universe correction (Phase 99)

The user clarified that the legacy 335 tickers were manually and arbitrarily selected; no formal selection methodology existed and none should be reconstructed. Stop attempting to recover Phase 70/71 logic for those 335. Keep the list only for exact F80 legacy comparability. It is not representative, statistically designed, or the ceiling for Smart Money research. The Phase 99 broad point-in-time universe charter remains on PR #13; PR #13 is open and not merged.

### Phase 20C — FINRA daily short-flow decision

Run 40098425254 completed successfully. The diagnostic used 329 valid names, 20 eligible training signals, 12 pseudo-OOS dates and left six final holdout signals unused. Results were horizon-unstable and weak:

- 5 sessions: mean replacement-minus-blocked delta +0.141%, median -0.050%, 5/12 positive, standard deviation 5.27%.
- 10 sessions: mean -1.687%, median -1.837%, 3/12 positive, standard deviation 7.50%.
- 20 sessions: mean -0.858%, median -0.333%, 5/12 positive, standard deviation 16.53%.
- Training-selected factor frequency: SHORT_RATIO_Z20 6 dates, SHORT_EXEMPT_RATIO 5, SHORT_RATIO_PERSIST20 1.

No bootstrap/issuer-clustered inference or LOO stability was reported. The denominator 1,382/2,020 file requests is not a valid coverage rate because the requested-date denominator includes weekends and holidays. The sample is conditional on the arbitrary legacy 335-name list.

**Decision:** kill this current FINRA daily short-volume-ratio feature-selection/replacement implementation for stock selection. Do not spend the six final holdout dates after the pseudo-OOS failure. This does not kill every possible FINRA mechanism: weekly ATS/non-ATS activity is a distinct source under separate audit. Phase 31 flow × short-interest divergence remains killed as independent alpha. See research/PHASE100_FINRA_SHORTFLOW_WALKFORWARD_DECISION_2026-11-05.md.

### FINRA weekly ATS / non-ATS OTC (Phase 38 and Phase 100)

Phase 38 run 40466439768 completed successfully: 959,997 rows, 17,221 unique symbols, 333/335 legacy names observed across the five sampled weeks and T1/T2 tiers, no request errors, and the initialPublishedDate field was present. This is promising public security-level off-exchange data, but Phase 38 pooled coverage across weeks and counted any symbol-bearing row; it did not establish per-week coverage for symbol-level aggregates or row-level partition integrity.

Phase 100 corrected revalidation was committed to the Phase 99 branch. The first run failed only an offline parser test; the error-object parser was corrected. The second run, 41969978743, passed all seven offline tests and was in progress on the live historical-partition audit at the latest check. Do not duplicate it while active. Phase 100 separately checks ATS_W_SMBL / OTC_W_SMBL aggregates, exact week/tier integrity, per-week combined legacy coverage, quantities, duplicates, publication lags and post-publication update dates. No forward returns are used.

FINRA documentation describes initialPublishedDate as the first Monday or next business day after the reporting delay (two weeks for T1, four weeks for T2/OTC). weeklySummaryHistoric exposes a rolling four-year window between one and five years prior to the current date; it is not a complete 2016-present archive. Current historical values do not by themselves prove original-vintage preservation. Even if Phase 100 passes coverage/schema gates, PIT revision history and permanent security identity remain separate gates. ATS/OTC activity is not aggressor direction, beneficial ownership, or proof of informed trading.

### Options source triage

- OCC Daily Open Interest Phase 53 actual endpoint audit failed: eight sample dates produced only 2–23 parsed rows, zero recognized underlying symbols, and zero usable legacy-universe coverage. Do not use this endpoint as a daily OI panel without a materially corrected endpoint/schema.
- OCC Volume Query Phase 53B is a separate source and returned usable recent account-type volume for 645/670 ticker-date probes (96.27%) across two recent sample dates. It is limited to approximately 24 months, does not provide buy/sell direction or open/close classification, and its historical publication timestamp is unverified. Retain only as a recent, secondary feasibility candidate; no long-OOS alpha test.
- Cboe Open-Close EOD sample Phase 54 contained 23,179 rows in a 20% C1 sample and reached 288/335 legacy tickers (85.97%) on the sampled date. It has materially richer participant-capacity/open-close fields but is not full OPRA coverage and requires licensed commercial data. This remains the strongest options information-density candidate, but no vendor contact, purchase, or data acquisition is authorized.
- Phase 95 DOOD units/history/PIT audit remains unresolved; no exact independent replication or return test is authorized.

### Other public candidates and execution status

- FINRA blocksSummary remains killed for stock selection because its live schema has no security/ticker identifier; aggregate market-regime use is a different, lower-priority hypothesis.
- SEC FTD remains a public candidate with documented half-month publication conventions, but the actual-file workflow exists without a corresponding completed Actions run in the latest audit. Treat the actual-file gate as pending, not completed.
- SEC MIDAS remains a promising public daily market-structure source, but actual quarterly-file coverage and conservative PIT release timing have not passed.
- Phase 69 Form 144 incremental scan completed with zero new candidates for the ten newly mapped fund CIKs; its offline regression run passed 45 tests. No further scan is warranted without a materially changed candidate set.
- Phase 93 13D/G parsing and Phase 94 DOOD formula regression tests completed successfully; these are parsing/formula validations, not alpha evidence.
- Phase 35 and Phase 22C runs are no longer active: the latest relevant runs were cancelled and their guarded replacements skipped. There is no reason to duplicate them.

### Current priority and permissions

1. Finish the already-running Phase 100 FINRA weekly ATS revalidation. If it passes, proceed to a preregistered PIT/security-identity gate, not an immediate alpha test.
2. Continue the broad PIT security-master design beyond the arbitrary 335 names. CRSP remains the preferred inactive/delisted return benchmark; Databento Security Master remains a two-clock identity candidate; Norgate remains an index-membership cross-check. Public documentation is not proof of licensed coverage.
3. Keep Cboe Open-Close + option EOD as the highest-information options candidate pending explicit authorization for licensed access.
4. Keep OCC Volume Query as recent-only and SEC FTD/MIDAS as public candidates pending their actual-file/PIT gates.

F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen. No production change, alpha claim, vendor contact, purchase, or data acquisition has occurred.


### 2026-11-05 correction — SEC FTD actual-file gate now passed

The prior note that the SEC FTD actual-file gate was pending is superseded. Phase 101 re-ran the existing Phase 43 parser audit successfully in Actions run 41970505481 (artifact 13389273464):

- January 2018 first-half file: 43,567 valid records, 9,824 unique symbols, settlement dates 2018-01-02 through 2018-01-12.
- September 2026 second-half file: 66,693 valid records, 13,394 unique symbols, settlement dates 2026-09-15 through 2026-09-30.
- Both files passed header/schema checks, date/quantity/price validation, and exact trailer record-count and total-quantity reconciliation. The two trailer lines are metadata, not malformed data rows.

SEC FTD is now a **public actual-file/schema feasibility pass**, not an alpha pass. The series is a cumulative net fail balance, not daily fails flow; the SEC warns it can arise from both long and short sales. Pre-2008-09-16 coverage has a 10,000-share threshold; later data includes all positive balances. The stated release schedule is approximate (first half at month-end; second half about the 15th of the next month) and the SEC does not guarantee exact posting dates. Next gates are multi-period continuity, CUSIP/symbol lifecycle mapping, PIT publication timing, and inactive-security return linkage. No forward-return test is authorized yet.

The Phase 100 FINRA ATS revalidation run 41969978743 remained active at the last status check; its seven offline tests passed and its live historical partition audit had not yet completed. Do not duplicate it.


## 2026-11-05 — Phase 102 SEC FTD multi-period actual-file audit

- Phase 102 run 41974948169 passed all seven representative archive downloads/schema checks. It sampled 2004Q2, 2008Q3/Q4, 2009Q2, July 2009 first half, January 2018 first half, and September 2026 second half. Artifact: phase102-sec-ftd-multiperiod-audit (13391072776).
- Seven samples passed; 1.50M+ FTD rows were parsed with zero malformed rows, invalid/negative quantity/price fields, duplicate (settlement date, CUSIP, symbol) keys, or trailer reconciliation failures. CUSIP was 100% nonblank; symbol was 100% except one blank in the 2026 sample (99.9985%).
- The 2008Q3 archive empirically confirms the 2008-09-16 threshold break: 171,520 pre-break rows had a minimum of 10,000 shares and zero below-threshold rows; 113,823 post-break rows included 76,712 balances below 10,000, down to one share. Do not combine the regimes without explicit treatment.
- The catalog's earliest listed quarterly archive is 2004Q2 even though the SEC landing page describes coverage from February 2004; Feb–Mar 2004 remains unverified. The September 2026 “second half” file includes settlement date 2026-09-15.
- FTD CUSIP↔ticker is not one-to-one across a quarter. The current audit counts mappings across dates, not same-date conflicts; a per-date lifecycle crosswalk remains necessary. FTD rows are fails balances, not short-sale flow or investor identity. No alpha test.
- Full report: research/PHASE102_SEC_FTD_MULTIPERIOD_AUDIT_2026-11-05.md.

### Phases 100 and 103 — current execution state

- Phase 100 run 41974948327 is running the asynchronous FINRA historic revalidation after the prior synchronous run remained active for over 25 minutes and was cancelled. Offline tests passed. The new implementation polls no more than once per minute and reconciles retrieved rows to FINRA's Record-Total header. Do not launch another Phase 100 run while it is active.
- Phase 103 run 41974948247 exposed a documentation-versus-file schema mismatch, not a failed SEC download: all six quarterly files were retrieved, but the actual CSV headers use LitVol('000), OrderVol('000), HiddenVol('000), TradeVolForHidden('000), TradesForOddLots, OddLotVol('000), and TradeVolForOddLots('000), rather than the landing page's advertised Trades, TradeVol, LitVol, OrderVol, etc. The parser was corrected to the actual header and now records this discrepancy plus the explicit “thousands” units.
- Phase 103 run 41975080361 is testing the corrected parser against six quarters (2012Q1, 2016Q1, 2017Q2, 2019Q4, 2025Q4, 2026Q2). It also measures legacy-335 overlap, whether the Security field is CUSIP-like, and HTTP Last-Modified metadata. PIT release vintage and inactive-security coverage remain unproven.
- Phase 100/103 are feasibility audits only; no forward-return test or F80 change is authorized.


### 2026-11-05 — Phase 103/104 SEC MIDAS actual-file and PIT decision

- Phase 103 run 41975686235 completed successfully; artifact 13391039377 (SHA-256 `2f144b95b11badef40498d168bc1ee5297f07b58f1b4061bd68317cd3fb34d89`). Six official quarterly files (2012Q1, 2016Q1, 2017Q2, 2019Q4, 2025Q4, 2026Q2) downloaded and passed actual-schema/date checks.
- Sample size ranged 306,238–542,295 rows; 5,064–9,216 unique tickers. Legacy-335 overlap ranged 54.33%–83.28%, but this is only a diagnostic against the user's arbitrary/manual legacy list, not broad-universe coverage.
- Actual file schema has Ticker/Date/Security (Stock/ETF), no CUSIP-like permanent identifier. Historical security identity and inactive/delisted coverage remain unverified.
- Duplicate audit: 2016Q1 two and 2019Q4 six duplicate keys differ only in rank fields; activity volumes/counts match in inspected rows. 2025Q4 has 355 and 2026Q2 19 exact duplicate groups. No silent deduplication; a deterministic rank-only resolution rule must be preregistered.
- HTTP Last-Modified is not a valid PIT anchor: 2012Q1/2016Q1 files report 2020-12-19, 2017Q2 reports 1970-01-01, 2019Q4 reports 2020-12-19, 2025Q4 2026-07-17, and 2026Q2 2026-08-06. ETag absent in all six. Data.gov dataset modified date 2017-10-30 is stale; SEC page's current update date is not original quarter release time.
- SEC methodology: stock/ETP universe sourced from CRSP daily stock records and refreshed monthly with a 3–4 week lag; 2017-05-01 NYSE Ultrabook→NIF change affects hidden-trade measures; 2025-11-03 new round-lot definition affects odd-lot measures; on-exchange continuous-trading aggregates generally exclude off-exchange volume, auctions and off-hours. MIDAS remains a microstructure hypothesis, not investor identity or signed flow.
- Some contemporaneous SEC Market Structure bulletins establish release dates for Q3 2021 (2021-11-02), Q1 2023 (2023-05-02), and Q4 2023 (2024-01-31), but not a complete 58-quarter ledger. Phase 104 report records exact results and gates.
- Decision: schema/sample PASS only; PIT, permanent identity and inactive/delisted gates not passed. No returns test authorized. F80 unchanged.

### 2026-11-05 — Phase 100 synchronous FINRA pagination correction

- Latest Phase 100 run 41975745942 failed after offline tests passed. Live FINRA responses supplied Record-Total/Record-Limit/Record-Offset but omitted Total-Records-On-Page; the implementation incorrectly required that optional/absent header, so all sampled partitions were marked errors before coverage was measured. One additional partition request returned HTTP 500.
- The workflow had no FINRA_API_TOKEN secret and therefore used synchronous mode. The failure is an implementation/response-header mismatch, not evidence that ATS coverage failed.
- Corrected synchronous pagination to use Total-Records-On-Page when present, otherwise the actual parsed response-body row count; require Record-Total, validate Record-Offset when supplied, advance by actual returned rows, and continue until exact Record-Total reconciliation. Added bounded retries for transient 408/429/5xx/network failures and regression tests. A single new live run will validate this correction; do not duplicate while active.
- Phase 100 remains data-feasibility only. No returns, alpha test, vendor purchase, or F80 change.


### 2026-11-05 — Phase 105/106 SEC FTD same-day identity and availability result

- Phase 105 successful run 41977069080; artifact 13391249428 (SHA-256 `2ea3a0d365fb8d264c23531a942d5d092b43e3fffbdbd0ecfc15d87ac3218e25`). The first attempt failed only because Actions ran a script path that omitted the repository root from Python import search; path was corrected and the second run passed all offline tests and seven live SEC archive downloads.
- Seven archives from 2004Q2 through 2026-09 second half parsed successfully. CUSIP was nonblank and valid nine-character format in all sampled rows; one blank ticker symbol in the 2026 sample; zero duplicate (settlement date, CUSIP, symbol) keys.
- Same-day mapping: zero CUSIPs mapped to multiple symbols in all seven samples; only one symbol mapped to multiple CUSIPs, DPW on 2018-01-02 (CUSIPs 253862106 and 26140E105; descriptions Digital Power Corp and DPW Holdings Inc.). This aligns with the issuer's 2017-12-29 announced name/reincorporation transition while retaining DPW ticker. Preserve both CUSIPs as effective-dated keys; do not collapse by ticker.
- Cross-date pooled many-to-many counts remain, confirming effective-dated lifecycle changes. Same-day mapping is mostly clean, materially reducing—but not eliminating—the FTD identity risk.
- HTTP HEAD/GET succeeded for all seven; ETag absent. Last-Modified for the current 2026-09 second-half file is 2026-10-15 (matches approximate SEC release convention), but older files show 2020-12-19 migration timestamps or 1970-01-01. Do not use these as historical PIT vintages.
- SEC states first-half data are available at month-end and second-half about the 15th of next month, but explicitly does not guarantee posting by a particular date. PIT gate remains NOT ESTABLISHED.
- FTD still needs CUSIP-to-permanent return-source ID crosswalk, inactive/delisted coverage and a defensible historical knowledge-date rule. No returns or alpha test authorized; F80 unchanged.

### 2026-11-05 — Phase 100 corrected FINRA ATS run

- Corrected live run 41976736121 was launched from commit f1914c30 after 15 offline tests passed. At the time of this state update it remained in progress; do not launch a duplicate. The previous failure was an absent Total-Records-On-Page response header plus one transient HTTP 500, not a data-coverage rejection.



### 2026-11-05 — Phase 100 corrected live FINRA ATS revalidation (preliminary)

- First corrected live run 41976736121 retrieved all 10 sampled week/tier partitions; each partition's row count exactly matched FINRA Record-Total. Offline tests passed 15/15. Total 968,139 rows; 108,444 symbol-level aggregates (52,007 ATS; 56,437 OTC); zero invalid/negative quantity fields.
- The run failed only at output serialization: page_hashes.csv fieldnames were stale relative to new sync pagination metadata. Partial artifact 13392981544 preserves partition_summary.csv but no final summary.json or page hashes.
- Partial audit shows 100% non-null initialPublishedDate; lags 21 days T1 / 35 days T2; 1,882/108,444 (1.735%) symbol aggregates had lastUpdateDate later than initialPublishedDate.
- Two conflicting duplicate aggregate keys for LND, 2025-01-06 T2 (ATS_W_SMBL and OTC_W_SMBL), with different values and lastReportedDate. One T2 partition (2022-01-03) has two row-level mismatches, including one OTC_W_SMBL row with no symbol; full mismatch examples pending corrected output.
- Removed the 90% legacy-335 coverage gate because 335 was manually/arbitrarily selected and is not representative. Overlap remains diagnostic only. Added page-hash schema and Record-Total tests, corrected duplicate counting, and separated source coverage from aggregate integrity.
- Corrected run 41978867803 is in progress. Do not launch a duplicate. See research/PHASE107_FINRA_ATS_PRELIMINARY_LIVE_REVALIDATION_2026-11-05.md.
- Official FINRA documentation: weeklySummary production is rolling 12 months; weeklySummaryHistoric is rolling four years beginning one year before the current date; historical data older than one year is static. Source: https://developer.finra.org/docs#query_api-equity-weekly_summary and https://developer.finra.org/news/q12021.
- No returns, alpha test, vendor purchase/contact, data acquisition or F80 change.




### 2026-11-05 — Phase 100 final FINRA ATS live result (supersedes prior in-progress notes)

- Corrected Phase 100 run 41978867803 completed successfully; artifact 13394110956, SHA-256 `803c58a5301df8b505b487c5367a449696c6bc467cab39121c50eda762d1f3e9`. All 10 week/tier partitions and 199 pages completed; every partition reconciled exactly to FINRA `Record-Total`.
- 968,139 rows retrieved; 108,444 symbol-level aggregates (52,007 ATS; 56,437 OTC). All sampled week/tier partitions had both ATS and OTC symbol aggregates; no negative/invalid quantity fields.
- Research gates did **not** pass fully: two missing-symbol rows in 2022-01-03/T2 (one `OTC_W_SMBL_FIRM`, one `OTC_W_SMBL`); two LND coarse-key collision groups in 2025-01-06/T2 (ATS and OTC `_SMBL` rows) have different quantities and `lastReportedDate` values. The current audit key omitted MPID, firmCRDNumber and lastReportedDate, so these are not yet proven true duplicates.
- The Phase100 validator incorrectly labels missing-symbol rows as `ROW_PARTITION_MISMATCH`; its exact-week/tier gate conflates separate checks. The returned examples do not show actual week/tier disagreement. This needs a targeted correction, not a false assertion of partition mismatch.
- `initialPublishedDate`, `lastUpdateDate`, and `lastReportedDate` were 100% populated; publication lags were 21 days T1 / 35 days T2. 1,882/108,444 (1.735%) symbol aggregates had `lastUpdateDate` later than first publication. Current values do not prove original historical vintages; PIT remains conditional.
- Legacy 335 overlap is diagnostic only (the names were arbitrary/manual); broad-universe coverage is not established. FINRA historic weeklySummaryHistoric is a rolling four-year window one to five years before the current date, combined with a 12-month production window—not a complete 2016-present series.
- Full decision: `research/PHASE107_FINRA_ATS_FINAL_LIVE_REVALIDATION_2026-11-05.md`. No forward returns or alpha test; F80 unchanged.

### 2026-11-05 — Phase 108 targeted FINRA ATS anomaly resolution

- Added `research/phase108_finra_ats_anomaly_resolution.py`, offline tests and workflow `.github/workflows/phase108_finra_ats_anomaly_resolution.yml`.
- The targeted probe re-queries only 2022-01-03/T2 and 2025-01-06/T2 with expanded FINRA fields: MPID, firmCRDNumber, marketParticipantName, issueName, tierDescription and lastReportedDate.
- It separates week/tier mismatches from missing-symbol anomalies and compares coarse collisions with a candidate key including participant identifiers and lastReportedDate. This expanded key is diagnostic only until FINRA's natural-key/revision semantics are confirmed.
- Latest run 41983989795 is in progress. Do not duplicate while active.
- No forward returns, alpha test, vendor purchase/contact, data acquisition or F80 change.


### 2026-11-05 — Phase 108 completed: FINRA ATS anomaly resolution

This section supersedes the earlier Phase 108 note that said the run was in progress.

- Actions run 41983989795 completed successfully; job `audit` passed, the seven offline regression tests passed, and artifact 13395870951 was retained. No Actions runs were in progress at the next status check.
- Re-queried 2022-01-03/T2 (139,176 rows, 28 pages) and 2025-01-06/T2 (136,362 rows, 28 pages) with expanded participant/publication fields. All 56 pages reconciled exactly to FINRA Record-Total; zero week/tier mismatches and zero request errors.
- Coarse-key collision groups were 9,653 and 8,964, but the diagnostic expanded key (symbol, week, tier, summary type, product type, MPID, firmCRDNumber, lastReportedDate) had zero collision groups in either partition. The expanded key is still not proven to be FINRA's definitive natural key.
- The earlier LND “conflicting duplicates” are distinct participant/report-date rows, not duplicates. The symbol-level ATS/OTC and symbol-firm levels overlap; do not add them together. LND OTC symbol-only values match De Minimis Firm values by lastReportedDate. ATS symbol-only rows have a cohort/cumulative relationship that needs a full ten-partition reconciliation before deciding the correct aggregation rule.
- The two missing-symbol rows in 2022 are correctly week/tier-partitioned but unallocatable OTC rows: one De Minimis Firms (`firmCRDNumber=0`, no MPID/symbol) and one UTP product row with no symbol. Keep them in completeness accounting; exclude them from security-level features.
- In the two targeted partitions, 129/35,210 symbol aggregate rows (0.366%) had `lastUpdateDate > initialPublishedDate`. Do not backfill current values to first-publication dates as if the original vintage were known. PIT/revision handling remains conditional.
- Full result: `research/PHASE108_FINRA_ATS_ANOMALY_RESOLUTION_RESULT_2026-11-05.md`. Spec status updated in `research/PHASE108_FINRA_ATS_ANOMALY_RESOLUTION_SPEC_2026-11-05.md`.

### Current decision after Phase 108

1. Phase 100 broad sample is complete; Phase 108 targeted anomaly objective passed.
2. FINRA ATS is still not authorized for returns/alpha testing. Next gate is a full expanded-field re-audit of the ten Phase 100 partitions, reconciling symbol-only aggregates to symbol-firm contributions by lastReportedDate, establishing natural-key/revision semantics, and then permanent-ID/PIT linkage to the broad historical equity universe.
3. If those semantics cannot be established, park FINRA ATS rather than force a signal. Its four-year historic rolling window is a material limitation.
4. Continue broad Smart Money research in parallel: SEC FTD needs PIT + CUSIP-to-permanent-return-ID/inactive-security linkage; SEC MIDAS needs release-vintage and permanent-identity gates; Cboe Open-Close remains the richest options candidate but requires explicit user authorization before vendor contact, purchase or acquisition. Existing negative/conditional decisions for FINRA short-flow selection, Form 4 standalone alpha, 13F, CFTC stock-level use and N-PORT remain unchanged.
5. No prices/forward returns used in Phase 108; no alpha claim, vendor contact/purchase or F80 change. `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen.


## 2026-11-05 — Phase 109 full FINRA ATS aggregation reconciliation (queued)

- Reviewed the latest 100 GitHub Actions runs (653 total); no run was queued/in progress before Phase 109 was submitted. Phase 108 run 41983989795 completed successfully: job audit passed, seven offline tests passed, and artifact 13395870951 was retained. Phase 100 run 41978867803 completed successfully; all ten partitions and 199 pages reconciled to Record-Total.
- Downloaded and inspected Phase 100 and Phase 108 artifacts. Phase 108's LND example indicates symbol-only rows are not to be added to symbol-firm rows. In that sample, symbol-only ATS rows for 2025-01-08 and 2025-01-10 reconcile to successive intervals of firm lastReportedDate values (Jan 7–8, then Jan 10); summed symbol-only totals equal summed firm-level totals. This is a candidate cohort convention, not a proven FINRA specification.
- Preregistered Phase 109 to re-query all ten Phase 100 week/tier partitions using the Phase 108 expanded fields and compare symbol-only rows against symbol-firm rows by successive lastReportedDate intervals, plus full-week totals. The audit preserves missing symbols/dates, duplicates, unmatched firm rows, invalid/negative values and page-level hashes. It does not use prices or returns.
- Added research/phase109_finra_ats_full_reconciliation.py, offline regression tests, specification and workflow. Run 42003973132 is queued; do not duplicate while it runs. Artifact will include compressed raw rows, page hashes, per-partition summaries and per-symbol/cohort reconciliation.
- Phase 109 can establish only sample-level aggregation consistency. It cannot establish original publication vintages, permanent security identity, inactive/delisted coverage, broad-market coverage, or informed trading. No alpha test is authorized.
- F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen; no vendor contact, purchase or data acquisition.
