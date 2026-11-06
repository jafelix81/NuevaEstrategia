# Smart Money Research State

Updated: 2026-11-05

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
- Phase 82 completed its 43-quarter (2016Q1–2026Q3) global master-index-only audit on run 41892370262 (artifact 13353118959): 323,132 multi-CIK accessions, 34,261 unique master-index CIKs, zero duplicate accessions across quarters and zero unexplained index metadata conflicts. This was an index-only crawl, not a complete-submission download. Master-index and archive-path CIKs remain candidates only; the current 319-CIK map is not historical F80 membership or a PIT security master.

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

### Phase 84/118 — SEC 13D/13G role-aware identity pilot

- Phase 84 run 41914491120 completed; its original live gate returned FAIL only because the mandatory-XML denominator was 192/193 = 99.482%, just below the 99.5% threshold. All 600 submissions were retrieved and the offline tests passed.
- Phase 118 re-audited immutable Phase 84/82 artifacts. The single apparent missing-XML row, accession 0001104659-26-057293, is an index-only cross-form alias: the quarterly master index contains one SC 13D/A row for the accession, but the actual SEC submission header and all document types identify SC TO-T/A. It is not a 13D/G submission and is quarantined from the 13D/G event population.
- After that quarantine, all 599 actual 13D/G sample rows match the SEC header; mandatory XML is present on 192/192 actual mandatory-XML 13D/G rows. Phase 118 independently recomputed raw hashes, file sizes and acceptance UTC from SEC-HEADER for all 600/600 submissions; all 200 present XML subject/filer fields match the SEC header.
- Of 367 current-CIK candidate rows, SEC-HEADER roles resolve 224 to subject and 143 to filer-only. The post-stratified descriptive subject share is 52.06% of 34,400 candidate accessions, with no inferential confidence interval. The 224/224 subject coverage is conditional on the current 319-CIK candidate set, not global issuer recall.
- Decision: PASS_WITH_INDEX_ALIAS_QUARANTINE for the role-aware retrieval/parser gate; proceed only to deterministic reporting-group/amendment lineage and historical issuer-security identity. No forward returns or alpha test. Use next-session-after-acceptance as the conservative knowledge rule until public dissemination time is independently verified.
- Phase 69's ten-CIK Form 144 extension completed (run 41959603351) with zero incremental candidates; do not repeat the unchanged scan. Phase 83's original 120-filing preregistered gate failure remains unchanged.

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
- Phase 69 run 41959603351 completed successfully; artifact 13385365595. The ten newly mapped fund-registrant CIKs added zero Form 144/144-A candidates in the 14-quarter 2023Q2–2026Q3 census. Phase 98 closed this same-set/same-period extension; do not repeat without a materially changed CIK set, period, or source. XML identity sub-gates are not applicable on the zero-candidate denominator, not validated passes.

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


## 2026-11-05 code-only validation addendum

- Corrected Phase 69 zero-candidate denominator semantics on branch `phase69-incremental-form144-fund-registrants` (script commit `c12e9631344d52f609743eed58599c08e36a7784`; test commit `9ef816fd4346f85edccdf3c2c542a8192afab8b8`). XML identity sub-gates now show `null` when no incremental candidate exists, and the summary reports `NOT_APPLICABLE_NO_CANDIDATES` / `PASS_NO_INCREMENTAL_CANDIDATES`.
- Hosted offline regression run 41959973317 passed **45 tests**; the live incremental-scan job was skipped. No SEC rescan was performed.


### 2026-11-05 — Legacy workflow trigger guard
- Main commit `b4bd844b567d4779b474a212c73ef37f7928c30a` changed the Phase 22C 13F audit to manual-dispatch only (unrelated pushes no longer launch it) and disabled the Phase 35 CIK-specific 13D/G crawler after the Phase 96 subject/filer failure.
- An unrelated main-branch state update had already triggered legacy push-on-any-commit workflows before this guard landed. Phase 22C run 41960053553 was cancelled. Phase 35 run 41960053552 remains reported in progress; guarded replacement run 41960188506 is pending with the audit job disabled. The available GitHub connector does not expose a direct cancel action, so this run may require manual cancellation if it does not clear. No further Phase 35 crawl was intentionally dispatched.
- Future research-state commits do not match the new workflow path filters and should not trigger these SEC jobs.


## 2026-11-05 — Phase 99 broad-universe charter and user clarification
- The user clarified that the 335 F80 tickers were selected manually and arbitrarily; no formal selection methodology existed and there is no rule to reconstruct. Do not spend further effort reverse-engineering the list.
- F80_TOP20_PARTIAL50_BASELINE_C20 retains the exact 335-name set solely for legacy comparability. Its results are conditional on that manually curated list, not a representative or survivorship-free market sample.
- Smart Money Research must use a separate broad US equity universe with frozen eligibility/security-type/liquidity rules, permanent security identifiers, historical active/inactive/delisted coverage, and point-in-time membership. No silent replacement of F80.
- Phase 99 charter: research/PHASE99_BROAD_PIT_UNIVERSE_CHARTER_2026-11-05.md. PR #13 remains open and unmerged.

## 2026-11-05 — Phase 109/110 FINRA ATS/OTC full-sample adjudication
- Phase 109 run 42003973132 completed successfully: 10/10 partitions, 968,139 records, 199 page hashes, exact FINRA Record-Total reconciliation, no week/tier mismatches, and no numeric invalids/negatives. Artifact 13405295714; ZIP SHA-256 f1bb176b2bee66d0d736b21e1e6ed64f28053c98aa47baebdd0d48f7a82cfe2d; raw rows SHA-256 45b6b169c1d57a1874438362295a656c5bc6499b2c29d6e3be8bd10a48425231.
- Phase 110 independently adjudicated the immutable artifact. Across 108,425 symbol/week/tier/family groups, all had both symbol-aggregate and participant-detail levels, and all 108,425 reconciled exactly on total shares and trades. There were zero expanded-key collision groups.
- Phase 109's 16 per-date cohort failures are superseded: productTypeCode distinguishes SIP/OTC feeds and lastReportedDate is a last-underlying-update marker, not a firm-report cohort key. The firm-level rows do not carry the product dimension required for the attempted allocation. All 16 groups nevertheless match exactly at weekly total level.
- Two genuinely blank-symbol OTC rows (2022-01-03/T2) each contain 100 shares/one trade and reconcile to each other; keep for market-level completeness, exclude from ticker features. The literal ticker NA occurs in 61 rows and must not be parsed as null.
- Publication timing: initialPublishedDate is 21 calendar days after weekStartDate for T1 and 35 days for T2. Of 108,444 aggregate rows, 1,882 (1.735%) were updated after first publication: T1 1,428/21,305 (6.703%); T2 454/87,139 (0.521%). Revised rows were updated as late as 331 days after first publication.
- For the current final-value extract, never backdate revised values to initialPublishedDate. Use lastUpdateDate as the latest underlying-update marker and make the value eligible no earlier than the next regular trading session; test additional one- and five-session buffers. Exact historical dissemination timestamps are still not proven.
- FINRA API coverage is a four-year historical rolling dataset plus a 12-month production dataset (roughly five years total). A separate official 2019 website guide says the download page's Year selector exposes all historical weekly reports within the selected year, with 2016 examples. This suggests a possible older website archive, but current 2016 download access has not yet been verified.
- Decision: retain FINRA ATS/OTC as a conditional data candidate, not an alpha signal. Next gate is to verify one 2016/2017 T1 and T2 website download, compare schema and overlapping-week values against the API, and establish actual earliest archive coverage. Then map historical symbols to permanent IDs and validate the broad universe before any returns test.
- Phase 110 used no forward returns; no alpha test was authorized; no vendor was contacted or purchased; F80 remains frozen. Offline adjudicator and four regression tests are in research/phase110_finra_ats_artifact_adjudication.py and research/test_phase110_finra_ats_artifact_adjudication.py.

## Current branch/PR status after Phase 110
- PR #13 remains open, unmerged, and mergeable. The research branch was one commit behind main at the latest comparison; no merge was performed.


## 2026-11-05 — Phase 111 OCC options account-type feasibility
- Added an independent public-source audit for OCC Volume by Account Type / ONN daily data. The fixed-width raw report contains Group, Symbol, Exchange, Customer, Firm and Market-Maker volume; it does not contain buyer/seller direction, opening/closing status or beneficial-owner identity.
- First live run 42020488244 completed successfully; artifact 13411093545. The 2026-11-03 report returned 41,847 rows across 4,631 symbols and passed row-width, exchange-code, duplicate-key, numeric and nonnegative-volume checks. Account-volume sums: Customer 50,334,339; Firm 5,339,753; Market Maker 58,497,402.
- The 2016-05-31, 2019-05-31 and 2023-11-03 batch requests returned identical 41-byte non-data responses. The parser initially compared OCC's MMDDYYYY header with a YYYYMMDD request and incorrectly failed the 2026 date; corrected before the second run. Boundary run 42020739832 is in progress for 2024-11-04/05/06 plus 2026-11-03.
- Decision remains conditional. OCC's current UI says 24 months; official batch docs show a 2019 example, but live results have not yet established a long historical archive. No returns test.
- Cboe Option Sentiment is a higher-information conditional option-flow candidate: official FAQ lists Jan 2012 history and OPRA coverage for U.S. stocks, ETFs and indices; its spec describes midpoint-classified directional premium/volume, net option delta, OI, IV/skew, implied borrow and account-type fields. However the former product URL redirects to the DataShop home page and the current Options catalog omits it. Current orderability, price, sample and method continuity are unverified. No contact or purchase.
- No option source is yet authorized for alpha testing. Treat Customer/Firm/MM as account/capacity categories, not institutional or informed traders.

## 2026-11-05 — FINRA historical archive user-certification gate
- FINRA OTC Transparency Website User Guide v6.0 states the user must affirmatively certify on each visit and click "I AGREE" before accessing OTC Transparency data. The guide's screenshots show 2016 weekly data, but the current historical download route has not been verified.
- Do not automate the affirmative certification or accept terms on the user's behalf. FINRA's developer API remains the already-audited rolling historical/production path; older website archives are blocked until the user personally reviews and accepts the terms. No certification was made.


### Phase 111 completion — OCC Volume by Account Type
- Run 42020739832 completed successfully; artifact 13411995693. Four daily dates (2024-11-04/05/06 and 2026-11-03) passed fixed-width/header/exchange/key/numeric checks. Row counts: 37,750; 37,481; 42,266; 41,847. Unique option symbols: 4,207; 4,206; 4,537; 4,631. Group keys: 4,051; 4,069; 4,342; 4,393. Exchange counts: 18; 18; 18; 20.
- 2016-05-31, 2019-05-31 and 2023-11-03 returned identical 41-byte non-data responses. Valid daily data was found from 2024-11-04 through 2026-11-03. This is consistent with a rolling ~24-month window; exact earliest cutoff not exhaustively searched.
- Decision: park OCC as recent participant-composition context only. It lacks direction, opening/closing status and beneficial-owner identity, and does not supply the long daily history needed for a robust independent OOS test. No alpha test.
- Cboe Option Sentiment remains the most information-rich documented options candidate (FAQ says Jan 2012 and OPRA U.S. stock/ETF/index coverage), but the old URL redirects and the current Options catalog omits it. Do not assume orderability; no vendor contact or purchase.
- FINRA historical website archive remains blocked pending the user's affirmative certification. No acceptance was made.


## 2026-11-05 — Phase 112 Cboe Option Trades public sample completed
- Run 42022615770 completed successfully; artifact 13412861022 (7,095,447-byte ZIP; SHA-256 d5407f64e9e6b5bac6773293e6f760004de377282b9f240f2059d5e2bea69613). All 11 offline parser tests passed.
- Public sample HTTP 200; 3,561,778 bytes; SHA-256 a02504e156db28b3f007d9d25a534e4c88ffd8d24ac43f3bf84885583a3d10b8. It contains two nested variants (Calcs included/excluded), each 74,999 rows with identical sequence-key hashes; do not add them. The sample covers only AAPL (one underlying, 308 option series), not full-market coverage.
- Quote checks: 74,218 valid NBBO, 625 locked, 5 crossed, 151 zero/missing; zero duplicate sequence keys. All 15 observed trade-condition IDs and 18 exchange IDs matched the downloaded official mapping files.
- Critical discrepancy: all sample quote_datetime values use a two-component clock such as 21:30.4, while Cboe Option Trades v1.3 specifies full U.S. Eastern trade date/time to milliseconds. Do not infer a timezone or reconstruct intraday timestamps. The adjacent-row sequence/clock monotonicity counter is not a valid acceptance metric because source row order is not established as chronological or sequence-sorted.
- Decision: schema/quote checks pass, documented timestamp conformance remains unresolved, broad market coverage unproven. Retain only as conditional daily trade/quote/IV context; no signed-flow or intraday study. See research/PHASE112_CBOE_OPTION_TRADES_SAMPLE_SCHEMA_AUDIT_2026-11-05.md.

## 2026-11-05 — Phase 113 Cboe Enhanced Options TBT candidate
- Newly prioritized Cboe Enhanced US Options Trade-by-Trade Execution Detail (TBT), based on current official product page and v1.1 specification dated 2026-10-05. Unlike the broad OPRA Option Trades feed, TBT documents SIDE, OPEN_CLOSE, CAPACITY, TRADE_TYPE, EXEC_ID/COMPLEX_EXEC_ID, NBBO/BBO and transaction/floor timestamps.
- Published history starts 2019-10-07; currently C1 only (BZX/C2/EDGX planned), delivered T+1, typically 00:30–01:30 ET next morning. This is materially richer for participant-capacity/position-side hypotheses but is not whole-OPRA coverage and does not identify beneficial owners.
- Phase 113 public-sample audit workflow run 42023567791 is in progress after 8 offline tests were added. It downloads only the public sample and official spec; no purchase, subscription, contact, or authentication. Do not start a duplicate while it runs.
- Before any return test: sample schema and key semantics, actual historical archive boundary/completeness, broad PIT underlying coverage including inactive/delisted names, C1 TBT vs C1 Open-Close reconciliation, T+1/late-file knowledge time, and preregistered handling of complex/auction/floor/routed/provisional trades must pass.
- Official docs: https://datashop.cboe.com/enhanced-us-options-trade-by-trade-execution-detail and https://datashop.cboe.com/documents/TBT_Spec_v1.1.pdf.

F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen. Phases 112–113 are source-feasibility work only; no alpha test or production change.


## 2026-11-05 — Phase 113 Cboe TBT public sample completed
- Run 42023896730 completed successfully; all 9 offline tests passed; artifact 13413280759. Sample ZIP HTTP 200, 3,807,739 bytes, SHA-256 6c99e69e43d259e81bc31334574579cf9c623f5e77ff596cacf268712cd3262c. Current TBT v1.1 PDF HTTP 200, SHA-256 e70599e0829dc5d030ac2e47b73fbd12afd6b7b31047d3ae354bbd884e65dffa.
- Nested 2025-03-28 sample CSV has 113,018 rows, 1,250 underlyings, C1 only, sample filename says 3%. Required schema, transaction/trading-date parsing, positive sizes/prices, capacities and exact-row uniqueness passed. Gate is PASS_PARSE_WITH_UNRESOLVED_CONVENTIONS, not economic approval.
- The sample archive embeds v1.0 spec dated 2026-01-12; current v1.1 is dated 2026-10-05. Both specify SIDE B/S, OPEN_CLOSE O/C and trading segment examples 1=prior-evening/overnight, 2=daytime. Sample has SIDE=T on 69 rows (all also blank open_close), blank open_close on 20,180 rows (17.86%), and TRADING_SEGMENT=1 on every row including RTH. Do not infer T as buy/sell, impute O/C, or rely on trading_segment. T is observed only in Complex Add/Remove, COA Initiator/Responder and Opening Cross rows; blank O/C spans 19 trade types.
- 306 calendar-date mismatches between transact_time and TRADING_DT are all GTH; no RTH/Curb mismatch. NBBO: 111,756 valid, 45 locked, 12 crossed, 1,205 zero/missing. BBO: 109,410 valid, 3,608 zero/missing. Floor-action timestamp on 618 rows: 61 >=90s late, 557 under 90s, zero negative. EXEC_ID has 1,685 repeated groups, all with both B/S sides; these are linkage pairs, not duplicates. COMPLEX_EXEC_ID has 2,875 repeated groups; exact duplicate rows zero.
- Decision: retain C1 TBT as the highest-information conditional options candidate (explicit side/open-close/capacity/trade-type, history advertised from 2019-10-07, T+1), but do not use a directional/open-close feature until sample conventions are explained and C1 Open-Close reconciliation passes. C1-only and a 3% sample do not prove whole-OPRA or broad PIT coverage. See research/PHASE113_CBOE_TBT_SAMPLE_FEASIBILITY_2026-11-05.md.
- Next: C1 Open-Close EOD actual historical 2005 boundary/missing dates and 2011 format break, broad PIT underlying crosswalk including delisted names, and historical T+1/correction availability. Same-date/same-series TBT vs Open-Close public-sample reconciliation was completed in Phase 115; TBT remains secondary. No forward returns or alpha test.

F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen. No source from Phases 112–113 is promoted to an investment signal.


## 2026-11-05 — Phase 114/115: Cboe C1 Open-Close EOD promoted to priority conditional options source
- Phase 114 public sample run 42027724358 succeeded; artifact 13415230222. The C1 EOD sample is 2025-03-28 and identifies a 20% sample. It contains 23,179 series rows across 1,553 underlyings and all 86 post-2011 fields. No duplicate keys, numeric errors or blank numeric cells. Participant buy/sell buckets equal total_exchange_vol exactly on all 23,179/23,179 rows (4,506,840 contracts).
- C1 EOD advertised history begins 2005-01-03; C1 10-minute begins 2011-01-03; C1 1-minute begins 2019-10-07. C1 GTH begins 2023-12-11. The legacy format spec describes 1990–2010, but current DataShop availability starts 2005; do not assume 1990–2004 access. The 2011 format/bucket-meaning break, C1 total_exchange_vol convention through 2019-10-04, shifted C1 OI through 2019-10-04, and previous-close break must be handled explicitly. Product-page history is not proof that every historical file is accessible.
- Phase 115 same-date public sample cross-check: TBT 3% and Open-Close EOD 20% samples on 2025-03-28 share 3,971 option series and 654 underlyings with common series. EOD buckets reconcile exactly on the common series. Underlying-level Spearman between TBT sample volume and EOD capacity volume: Market Maker 0.760, Customer 0.741, Pro-Customer 0.611, Firm 0.704, Broker-Dealer 0.624 (sparse). TBT sample volume is 3.765% of EOD volume on overlapping series, but capacity ratios range 1.75%–5.42%; do not use one global expansion weight.
- This is not independent replication: Cboe says TBT is the transaction-level data used to derive Open-Close. TBT still has SIDE=T and blank OPEN_CLOSE exceptions. Prefer EOD summary for daily classified capacity/side/open-close features; retain TBT for secondary validation.
- Decision: Cboe C1 Open-Close EOD is the highest-priority conditional options-flow candidate so far. It is C1-only, not whole-OPRA; participant labels are clearing-origin/capacity categories, not beneficial-owner identities. Public samples do not establish historical completeness, broad PIT coverage, dissemination timestamps or license cost.
- Next gates: actual 2005 archive and 2011 format boundary/missing dates; broad PIT security crosswalk including inactive/delisted underlyings; T+1 final-file publication/correction timing; historical sample coverage and license estimate. No purchase/contact or returns test without explicit authorization.
- Phase 111 OCC Volume by Account Type remains parked (only ~24-month live history, no side/open-close). Phase 112 Option Trades remains conditional daily context only because its sample timestamp format does not conform to v1.3. Phase 113 TBT remains secondary pending convention resolution.
- F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen; no alpha test or production change.


## 2026-11-05 — Phase 116 Cboe U.S. Equities Historical Market Volume public archive completed
- Live run 42033472218 succeeded; artifact 13416659256 (5,940,729 bytes). All 14 offline parser/regression tests passed.
- Downloaded all 18 annual daily and 18 annual monthly files listed by Cboe for 2009–2026: 72,103 daily rows, 3,395 monthly rows, 4,488 trading dates from 2009-01-02 through 2026-11-04. Completed participant-month daily-vs-monthly reconciliation passed for 55,865 comparisons across all 12 numeric fields within explicit scale-aware source-rounding tolerances.
- Legacy 2009 monthly URL uses header `Day` but YYYY-MM values; normalized in parser. Some legacy monthly notional and share totals are rounded differently from daily sums; parser now uses documented conservative tolerances (daily notional max($0.20, 1e-10 relative); monthly notional max($2, 1e-9 relative); monthly shares max(1 share, 1e-7 relative); trade counts exact).
- Correctly mapped historical/current FINRA TRF market-center codes DQ, DN and DB. The Cboe current market summary explicitly labels `TRFs (DQ,DN,DB)`; older historical CSV names include NASDAQ (DQ), NYSE (DN) and NASDAQ (DB), so string-only "TRF" matching would have silently missed historical data. The artifact includes 4,488 daily marketwide TRF share/notional fractions.
- This source is market-center/tape aggregate only, with no ticker, side, MPID, capacity, order or beneficial-owner identity. Retain as marketwide venue-regime context candidate, not a Smart Money signal or per-stock feature.
- Strict PIT remains unproven: Cboe's public archive page/files provide no historical first-publication timestamps, immutable file vintages or correction history. No historical alpha/return test authorized. Prospective snapshotting can build a clean future archive but cannot backfill historical knowledge times.
- Official references: https://www.cboe.com/markets/us/equities/market-statistics/historical-market-volume/ and https://www.cboe.com/us/equities/market_share/market/.
- Cboe C1 Open-Close EOD remains the highest-information conditional options candidate (Phases 114/115); Phase 116 is a separate public market-regime control.
- No data purchase/contact, no alpha test, no F80 changes. F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen.


## 2026-11-05 — Phase 117 FINRA ATS/OTC revision-impact and PIT eligibility

- Replayed the immutable Phase 109 raw artifact (968,139 rows; 108,444 symbol aggregates across five weeks and T1/T2). The raw compressed-row SHA-256 was verified as `45b6b169c1d57a1874438362295a656c5bc6499b2c29d6e3be8bd10a48425231`.
- In all 108,444 aggregate rows, `lastUpdateDate = max(initialPublishedDate, lastReportedDate)`. 1,882 rows (1.735%) have an update marker later than first publication.
- Revisions are concentrated in T1 OTC non-ATS: 1,428/10,668 rows (13.386%). Dropping revised rows would retain only 66.76% of shares and 63.79% of trades in that family. Overall it retains 89.92% of shares and 88.56% of trades; this is not a neutral exclusion.
- Critical PIT ruling: filtering out rows because the current extract shows they were eventually revised is itself future-informed selection. Do not call that an unbiased PIT subset. Do not backdate current final values to `initialPublishedDate`. `lastUpdateDate` is an underlying firm-update marker, not a documented public dissemination timestamp; +1/+5 session buffers remain sensitivities only.
- FINRA ATS/OTC remains conditional, not alpha-ready. Need verified public update timing or actual vintages/prospective immutable captures, plus permanent security identity and delisted coverage. No forward-return test or F80 change.
- Reproducible audit: `research/phase117_finra_ats_pit_revision_impact.py`; six offline tests pass. Full report: `research/PHASE117_FINRA_ATS_PIT_REVISION_IMPACT_2026-11-05.md`.
- Phase 69 state corrected: run 41959603351 completed with zero incremental Form 144 candidates for the ten-CIK extension; do not repeat unchanged scan.

## 2026-11-05 — Phase 118 SEC 13D/13G Phase 84 artifact adjudication

- Original Phase 84 failure was a denominator/classification issue, not a missing structured filing: accession 0001104659-26-057293 is indexed under both SC 13D/A and SC TO-T/A, but its raw SEC-HEADER CONFORMED SUBMISSION TYPE and both document types are SC TO-T/A / EX-99.(A)(5)(B). Quarantined as a non-13D/G index alias; no 13D/G document exists in the submission.
- Re-audited immutable artifacts Phase 84 #13364856424 and Phase 82 #13353118959. Recomputed 600/600 raw SHA-256 hashes and sizes, 600/600 SEC acceptance UTC values from America/New_York header timestamps, and 200/200 XML subject/filer matches. After quarantine, 599/599 actual 13D/G forms match and 192/192 actual mandatory-XML 13D/G rows contain XML.
- Phase 84 role pilot: 367 CIK-candidate rows all resolved by SEC-HEADER (224 subject, 143 filer-only); descriptive post-stratified estimate across 34,400 candidate accessions is 52.06% subject-target / 47.94% filer-only. No inferential CI. Candidate coverage is conditional on current 319 CIKs; not global recall or historical universe membership.
- Phase 118 status: PASS_WITH_INDEX_ALIAS_QUARANTINE. Reproducible artifact-only script `research/phase118_sec_13dg_phase84_adjudication.py`, seven tests in `research/test_phase118_sec_13dg_phase84_adjudication.py`, report `research/PHASE118_SEC_13DG_PHASE84_ARTIFACT_ADJUDICATION_2026-11-05.md`. No live SEC requests or forward returns.
- Next gate: deterministic subject/reporting-person/group and amendment lineage, then historical CIK-to-security and active/delisted PIT crosswalk. SEC acceptance is reproducible but not independently verified dissemination time; use next-session availability conservatively. No alpha test or F80 change.

## 2026-11-05 — Phase 119 SEC 13D/13G XML schema and amendment-lineage audit

- Parsed the 200 XML-bearing filings in the Phase 84 pilot separately by schema: 79 13D and 121 13G. Issuer/filer CIKs match SEC-HEADER on 200/200; event dates are present on 200/200; all 97 amendments carry amendmentNo.
- 13D has 260 reportingPersonInfo nodes; reporting-person CIK appears on 158/260 (60.8%), while names and core ownership fields are present on all nodes. 13G has 210 coverPageHeaderReportingPersonDetails nodes; per-person CIK is absent, but filing-level filer CIK matches header on 121/121; names and ownership fields are present on all nodes. A generic 13D parser would miss all 121 13G reporting-person nodes.
- CUSIP field present on 139/200; class title on 200/200. Security key must include CUSIP/class: six BlackRock filings with the same issuer/filer/name but six distinct CUSIPs would otherwise be falsely merged. Repeated group keys fall from 3/10 rows to 1/2 rows for 13G after security key; 13D from 4/9 to 3/6.
- Of 97 amendments, 46 contain previousAccessionNumber. Scanning all 43 Phase 82 master indexes validates 45/46 pointers by prior accession presence, issuer CIK, filer CIK, same form family and earlier filing date. One pointer on accession 0000886982-25-001416 to 0000769993-25-000432 is absent from the frozen index; quarantine it and do not guess. 51/97 amendments lack explicit predecessor pointers. Prior raw submissions have not yet been fetched, so CUSIP/person/ownership continuity is not yet verified.
- Only 200/600 sample rows have XML; the 400 non-XML rows need a legacy HTML parser. XML-only history cannot backfill 2016–2024. Event date is not knowledge date; use next-session-after-acceptance until dissemination time is validated.
- Phase 119 status: PASS_WITH_LINEAGE_CAVEATS. Report research/PHASE119_SEC_13DG_XML_SCHEMA_AND_LINEAGE_FEASIBILITY_2026-11-05.md; auditor research/phase119_sec_13dg_xml_lineage_audit.py; six tests research/test_phase119_sec_13dg_xml_lineage_audit.py. CI runs 42055578553 and 42055592782 passed.
- Next gate: download only the 45 index-validated predecessor submissions and compare security/reporting-person/ownership continuity; keep the unresolved pointer quarantined. Then build historical CIK-to-security PIT crosswalk and legacy HTML parser. No forward returns or alpha tests; F80 remains frozen.


## 2026-11-05 — Phases 120–122 SEC 13D/13G predecessor and ownership continuity

- Phase 120 run 42058411930 retrieved and hash-validated all 45 predecessor submissions selected from the 45/46 Phase 119 index-validated pointers; zero download/accession failures, 44 identical mirror pairs and one single-valid-path case. All 45 SEC-header identity/chronology checks passed. Its workflow conclusion was failure because the data gate correctly returned INCOMPLETE_OR_CONFLICT: 34 header+security passes, 7 header-only/unresolved cases and 4 CUSIP conflicts. This was not a download failure.
- Phase 121 run 42060958167 completed with PASS_WITH_CAVEATS after re-parsing the immutable current and predecessor artifacts. Across 45 links: 39 exact CUSIP matches, 5 CUSIP mismatches and one class-title-only match without CUSIP. The five mismatches comprise a documented SPAC business combination, a documented reverse split, a documented ADS-ratio change, a different ETF series under the same trust CIK, and a suspected (not confirmed) Toro predecessor filing CUSIP mis-key. The Toro link remains quarantined. The class-title-only Jefferies Credit Partners BDC link remains weaker than a CUSIP match.
- Phase 122 run 42062157962 passed 7 offline tests and completed the immutable artifact comparison. All 45 current and 45 predecessor raw hashes were revalidated. Of 21 XML predecessor links, 20 exact-CUSIP pairs were eligible (14 13D, 6 13G); one CUSIP-mismatch XML pair was excluded. The other 24 legacy HTML predecessors were excluded from XML ownership comparison, not treated as zero ownership.
- Across 20 eligible XML pairs, 59 reporting-person links matched by normalized name (47 13D, 12 13G). Reported share amounts changed on 34/59 links and percent-of-class changed on 43/59. Available person-CIK comparisons matched 36/36. The audit found 24 identical amount/percent pair observations within 13D group flags across current/prior filings; these are overlap diagnostics only. Never sum group members or infer separate beneficial owners from the group flag.
- Interpretation: beneficial-ownership snapshots are not transaction-level trade flow. Changes may reflect transfers, attribution, denominator changes, conversions, corporate actions or corrections. 13G per-person CIK is absent in this schema; name matching is not a permanent ID. SEC acceptance remains a conservative proxy for knowledge time; use next-session availability until public dissemination is independently verified.
- Phase 122 report: `research/PHASE122_SEC_13DG_XML_OWNERSHIP_CONTINUITY_AUDIT_2026-11-05.md`; auditor `research/phase122_sec_13dg_xml_ownership_continuity_audit.py`; seven tests; workflow `.github/workflows/phase122_sec_13dg_xml_ownership_continuity_audit.yml`.
- Decision: 13D/G remains conditional, not alpha-ready. The 45-link stratified pilot is not a global census; still required are historical subject-issuer discovery, effective-dated CUSIP/security mapping, inactive/delisted coverage, legacy HTML parsing and independently verified dissemination timing. No forward returns, feature selection, alpha test, paid data, or production changes.
- F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen.


## 2026-11-05 — Phase 123 SEC 13D/13G regulatory PIT regime audit

- Added research/PHASE123_SEC_13DG_REGULATORY_PIT_REGIME_AUDIT_2026-11-05.md from the SEC final rule Release Nos. 33-11253 / 34-98704.
- Do not use one 2024 break for all filings: Schedule 13D deadline amendments apply from 2024-02-05; revised Schedule 13G deadlines apply only from 2024-09-30; mandatory 13D/G XML compliance begins 2024-12-18 (voluntary XML from 2023-12-18).
- Schedule 13D initial >5% deadline changed from 10 calendar days to five business days; material amendments changed from “promptly” to two business days. Schedule 13G QII/exempt, passive and accelerated >10%/5%-change rules differ and must be classified separately.
- EDGAR transmissions by 10 p.m. Eastern can be assigned the same business-day filing date. Preserve SEC acceptance datetime, filing date, event date and first tradable session as separate fields.
- Event date is not public knowledge time. Use the first regular U.S. equity session whose open occurs after verified acceptance as the conservative tradable-availability convention; do not backdate ownership snapshots.
- SEC economic analysis notes possible pre-filing anticipation by other traders around Schedule 13D. This is a hypothesis about foreknowledge/run-up, not evidence that public filing signals have post-publication alpha. Separate pre-filing return-chasing from post-publication incremental information.
- Decision: regulatory timing/schema breaks are now explicit, but 13D/G remains not alpha-ready until global subject-issuer discovery, effective-dated security identity, delisted coverage and legacy HTML parsing pass. No returns/alpha tests or F80 changes.


## 2026-11-05 — Phase 124 global 13D/13G sample — final disposition

- Corrected run 42073725379 produced a complete immutable artifact, but GitHub Actions concluded failure because the exit gate did not accept the intentional PASS_WITH_INDEX_ALIAS_QUARANTINE status. This was a workflow-status gate defect, not a raw-download or identity-reconciliation failure. The corrected status logic and regression tests are now exercised by downstream Phase 125/126 CI; no duplicate live SEC pull was launched.
- The deterministic sample contains 600 index rows: 599 actual 13D/G submissions plus one confirmed SC TO-T/A index alias quarantined from the 13D/G population. The source index contains 324,964 unique accessions across 43 quarters (2016Q1–2026Q3); after 762 prior-pilot/predecessor exclusions, 324,202 remained eligible across 172 quarter × form-family × amendment strata.
- All 600 raw files passed SHA-256 and accession/date checks; 599 actual 13D/G submissions matched header accession, form family and filing date. There were zero transport/mirror failures. The sample is a filing-index sample, not a historical tradable-security universe.
- The 102 XML rows include all 99/99 mandatory-XML rows after 2024-12-18. Header subject/filer CIK presence in 599/599 rows is only header metadata presence; Phase 126 shows it must not be described as verified issuer coverage for legacy HTML filings.
- No forward-return, alpha, or production test was part of Phase 124. F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen.

## 2026-11-05 — Phase 125 SEC 13D/G cover-page CUSIP audit

- Phase 125 run 42077788015 completed successfully using only immutable Phase 124 artifacts; it made no new SEC requests.
- The legacy HTML parser was tightened to use only the first CUSIP value on the primary cover page, including values split across HTML text nodes. Later CUSIPs in narrative/exhibits are intentionally excluded and cannot substitute for a missing cover-page value. The parser distinguishes 000000000 as an XML placeholder rather than an invalid-format CUSIP.
- Across 599 actual filings: 541 rows have a unique checksum-valid CUSIP, two have checksum-invalid CUSIPs (584680106 in legacy HTML and 50214C200 in XML), 55 have no usable CUSIP (23 legacy, 32 XML), and one XML row contains the all-zero placeholder.
- Weighted valid cover-page CUSIP coverage is 96.84% for legacy HTML (473/497 rows), 66.71% for XML (68/102), and 91.36% overall. These are post-stratified descriptive coverage estimates, not inferential confidence intervals.
- The audit found 524 distinct checksum-valid CUSIP strings and 525 (header_subject_cik, CUSIP) pairs; CUSIP 81752R100 appears under two different header subject CIKs. Phase 126 adjudicates that conflict.
- Decision: the cover-page CUSIP is a useful security identifier candidate, but it is not permanent and does not by itself resolve issuer CIK, share class, corporate actions, delistings or ticker history. No returns/alpha test.

- Superseded for XML CUSIP coverage by Phase 127: legacy HTML coverage remains 96.84%, but corrected XML coverage is 97.38% and corrected overall coverage is 96.94% (see Phase 127 below).

## 2026-11-05 — Phase 126 SEC 13D/G body-first issuer identity audit

- Phase 126 run 42079214500 passed. It reconciled the immutable Phase 124/125 artifacts, verified 600 raw SHA-256/accession/date checks, retained 599 actual 13D/G rows and quarantined one index alias. No SEC network requests were made.
- Structured XML issuer CIK matched the SEC-HEADER subject CIK in 102/102 XML rows in this sample. This is a useful conditional result, not proof of universal correctness.
- Two legacy header/body issuer-role discrepancies were hand-adjudicated:
  1. Accession 0001549575-20-000008: SEC-HEADER subject and filer both say Dalal Street, LLC (CIK 1549575); the 13G cover page says Seritage Growth Properties, CUSIP 81752R100.
  2. Accession 0001903596-22-000671: SEC-HEADER subject says American Community Capital, LP (CIK 1626837), filer is Igwealor Frank I (CIK 1945609); the 13D cover page says Nano Mobile Healthcare, Inc., CUSIP 63010B200.
- The Seritage discrepancy is independently reinforced by accession 0001193125-21-208169: the same body issuer and CUSIP 81752R100 appear with header subject CIK 1628063. The two filings therefore carry different header subject CIKs for the same body issuer/CUSIP.
- A third name difference was deliberately not counted as an error: accession 0001172661-24-001310 has header subject ArrowMark Financial Corp (CIK 1578987), a FORMER COMPANY entry for StoneCastle Financial Corp, and a StoneCastle cover page/CUSIP 861780104. This is a valid historical issuer-name change with the same CIK, not a role mismatch. The filer CIK is 1483859.
- Decision: do not use legacy SEC-HEADER SUBJECT COMPANY CIK as an authoritative issuer CIK or as issuer-universe coverage. For legacy 13D/G, start from body cover-page issuer name plus cover-page CUSIP; preserve former-name fields and require an effective-dated CUSIP/security master before joining returns. XML issuerCik can be used conditionally where present and validated.
- Only the two discrepancies and one rename control were manually adjudicated; they are concrete examples, not an estimated global error rate. No broad body-issuer parser was promoted. No forward returns, alpha tests, vendor purchases or production changes.

## Next 13D/G gate

- Build a deterministic, effective-dated CUSIP-to-security/issuer crosswalk with share-class, ETF-series, ADR, rename, split, merger and delisting handling; retain unresolved mappings rather than fuzzy-assigning them.
- Verify mapping against an independent historical security master and preserve acceptance timestamp separately from event date. Only then define a preregistered 13D activist/passive event hypothesis and test incremental information versus frozen LTM/F80 with chronological OOS, identical exposure/costs, bootstrap and LOO.
- Continue Cboe Open-Close EOD as the leading options-flow feasibility candidate in parallel; no vendor purchase or licensing commitment without explicit authorization.
- F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen.
# Smart Money Research State

Updated: 2026-11-05

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
- Phase 82 completed its 43-quarter (2016Q1–2026Q3) global master-index-only audit on run 41892370262 (artifact 13353118959): 323,132 multi-CIK accessions, 34,261 unique master-index CIKs, zero duplicate accessions across quarters and zero unexplained index metadata conflicts. This was an index-only crawl, not a complete-submission download. Master-index and archive-path CIKs remain candidates only; the current 319-CIK map is not historical F80 membership or a PIT security master.

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

### Phase 84/118 — SEC 13D/13G role-aware identity pilot

- Phase 84 run 41914491120 completed; its original live gate returned FAIL only because the mandatory-XML denominator was 192/193 = 99.482%, just below the 99.5% threshold. All 600 submissions were retrieved and the offline tests passed.
- Phase 118 re-audited immutable Phase 84/82 artifacts. The single apparent missing-XML row, accession 0001104659-26-057293, is an index-only cross-form alias: the quarterly master index contains one SC 13D/A row for the accession, but the actual SEC submission header and all document types identify SC TO-T/A. It is not a 13D/G submission and is quarantined from the 13D/G event population.
- After that quarantine, all 599 actual 13D/G sample rows match the SEC header; mandatory XML is present on 192/192 actual mandatory-XML 13D/G rows. Phase 118 independently recomputed raw hashes, file sizes and acceptance UTC from SEC-HEADER for all 600/600 submissions; all 200 present XML subject/filer fields match the SEC header.
- Of 367 current-CIK candidate rows, SEC-HEADER roles resolve 224 to subject and 143 to filer-only. The post-stratified descriptive subject share is 52.06% of 34,400 candidate accessions, with no inferential confidence interval. The 224/224 subject coverage is conditional on the current 319-CIK candidate set, not global issuer recall.
- Decision: PASS_WITH_INDEX_ALIAS_QUARANTINE for the role-aware retrieval/parser gate; proceed only to deterministic reporting-group/amendment lineage and historical issuer-security identity. No forward returns or alpha test. Use next-session-after-acceptance as the conservative knowledge rule until public dissemination time is independently verified.
- Phase 69's ten-CIK Form 144 extension completed (run 41959603351) with zero incremental candidates; do not repeat the unchanged scan. Phase 83's original 120-filing preregistered gate failure remains unchanged.

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
- Phase 69 run 41959603351 completed successfully; artifact 13385365595. The ten newly mapped fund-registrant CIKs added zero Form 144/144-A candidates in the 14-quarter 2023Q2–2026Q3 census. Phase 98 closed this same-set/same-period extension; do not repeat without a materially changed CIK set, period, or source. XML identity sub-gates are not applicable on the zero-candidate denominator, not validated passes.

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


## 2026-11-05 code-only validation addendum

- Corrected Phase 69 zero-candidate denominator semantics on branch `phase69-incremental-form144-fund-registrants` (script commit `c12e9631344d52f609743eed58599c08e36a7784`; test commit `9ef816fd4346f85edccdf3c2c542a8192afab8b8`). XML identity sub-gates now show `null` when no incremental candidate exists, and the summary reports `NOT_APPLICABLE_NO_CANDIDATES` / `PASS_NO_INCREMENTAL_CANDIDATES`.
- Hosted offline regression run 41959973317 passed **45 tests**; the live incremental-scan job was skipped. No SEC rescan was performed.


### 2026-11-05 — Legacy workflow trigger guard
- Main commit `b4bd844b567d4779b474a212c73ef37f7928c30a` changed the Phase 22C 13F audit to manual-dispatch only (unrelated pushes no longer launch it) and disabled the Phase 35 CIK-specific 13D/G crawler after the Phase 96 subject/filer failure.
- An unrelated main-branch state update had already triggered legacy push-on-any-commit workflows before this guard landed. Phase 22C run 41960053553 was cancelled. Phase 35 run 41960053552 remains reported in progress; guarded replacement run 41960188506 is pending with the audit job disabled. The available GitHub connector does not expose a direct cancel action, so this run may require manual cancellation if it does not clear. No further Phase 35 crawl was intentionally dispatched.
- Future research-state commits do not match the new workflow path filters and should not trigger these SEC jobs.


## 2026-11-05 — Phase 99 broad-universe charter and user clarification
- The user clarified that the 335 F80 tickers were selected manually and arbitrarily; no formal selection methodology existed and there is no rule to reconstruct. Do not spend further effort reverse-engineering the list.
- F80_TOP20_PARTIAL50_BASELINE_C20 retains the exact 335-name set solely for legacy comparability. Its results are conditional on that manually curated list, not a representative or survivorship-free market sample.
- Smart Money Research must use a separate broad US equity universe with frozen eligibility/security-type/liquidity rules, permanent security identifiers, historical active/inactive/delisted coverage, and point-in-time membership. No silent replacement of F80.
- Phase 99 charter: research/PHASE99_BROAD_PIT_UNIVERSE_CHARTER_2026-11-05.md. PR #13 remains open and unmerged.

## 2026-11-05 — Phase 109/110 FINRA ATS/OTC full-sample adjudication
- Phase 109 run 42003973132 completed successfully: 10/10 partitions, 968,139 records, 199 page hashes, exact FINRA Record-Total reconciliation, no week/tier mismatches, and no numeric invalids/negatives. Artifact 13405295714; ZIP SHA-256 f1bb176b2bee66d0d736b21e1e6ed64f28053c98aa47baebdd0d48f7a82cfe2d; raw rows SHA-256 45b6b169c1d57a1874438362295a656c5bc6499b2c29d6e3be8bd10a48425231.
- Phase 110 independently adjudicated the immutable artifact. Across 108,425 symbol/week/tier/family groups, all had both symbol-aggregate and participant-detail levels, and all 108,425 reconciled exactly on total shares and trades. There were zero expanded-key collision groups.
- Phase 109's 16 per-date cohort failures are superseded: productTypeCode distinguishes SIP/OTC feeds and lastReportedDate is a last-underlying-update marker, not a firm-report cohort key. The firm-level rows do not carry the product dimension required for the attempted allocation. All 16 groups nevertheless match exactly at weekly total level.
- Two genuinely blank-symbol OTC rows (2022-01-03/T2) each contain 100 shares/one trade and reconcile to each other; keep for market-level completeness, exclude from ticker features. The literal ticker NA occurs in 61 rows and must not be parsed as null.
- Publication timing: initialPublishedDate is 21 calendar days after weekStartDate for T1 and 35 days for T2. Of 108,444 aggregate rows, 1,882 (1.735%) were updated after first publication: T1 1,428/21,305 (6.703%); T2 454/87,139 (0.521%). Revised rows were updated as late as 331 days after first publication.
- For the current final-value extract, never backdate revised values to initialPublishedDate. Use lastUpdateDate as the latest underlying-update marker and make the value eligible no earlier than the next regular trading session; test additional one- and five-session buffers. Exact historical dissemination timestamps are still not proven.
- FINRA API coverage is a four-year historical rolling dataset plus a 12-month production dataset (roughly five years total). A separate official 2019 website guide says the download page's Year selector exposes all historical weekly reports within the selected year, with 2016 examples. This suggests a possible older website archive, but current 2016 download access has not yet been verified.
- Decision: retain FINRA ATS/OTC as a conditional data candidate, not an alpha signal. Next gate is to verify one 2016/2017 T1 and T2 website download, compare schema and overlapping-week values against the API, and establish actual earliest archive coverage. Then map historical symbols to permanent IDs and validate the broad universe before any returns test.
- Phase 110 used no forward returns; no alpha test was authorized; no vendor was contacted or purchased; F80 remains frozen. Offline adjudicator and four regression tests are in research/phase110_finra_ats_artifact_adjudication.py and research/test_phase110_finra_ats_artifact_adjudication.py.

## Current branch/PR status after Phase 110
- PR #13 remains open, unmerged, and mergeable. The research branch was one commit behind main at the latest comparison; no merge was performed.


## 2026-11-05 — Phase 111 OCC options account-type feasibility
- Added an independent public-source audit for OCC Volume by Account Type / ONN daily data. The fixed-width raw report contains Group, Symbol, Exchange, Customer, Firm and Market-Maker volume; it does not contain buyer/seller direction, opening/closing status or beneficial-owner identity.
- First live run 42020488244 completed successfully; artifact 13411093545. The 2026-11-03 report returned 41,847 rows across 4,631 symbols and passed row-width, exchange-code, duplicate-key, numeric and nonnegative-volume checks. Account-volume sums: Customer 50,334,339; Firm 5,339,753; Market Maker 58,497,402.
- The 2016-05-31, 2019-05-31 and 2023-11-03 batch requests returned identical 41-byte non-data responses. The parser initially compared OCC's MMDDYYYY header with a YYYYMMDD request and incorrectly failed the 2026 date; corrected before the second run. Boundary run 42020739832 is in progress for 2024-11-04/05/06 plus 2026-11-03.
- Decision remains conditional. OCC's current UI says 24 months; official batch docs show a 2019 example, but live results have not yet established a long historical archive. No returns test.
- Cboe Option Sentiment is a higher-information conditional option-flow candidate: official FAQ lists Jan 2012 history and OPRA coverage for U.S. stocks, ETFs and indices; its spec describes midpoint-classified directional premium/volume, net option delta, OI, IV/skew, implied borrow and account-type fields. However the former product URL redirects to the DataShop home page and the current Options catalog omits it. Current orderability, price, sample and method continuity are unverified. No contact or purchase.
- No option source is yet authorized for alpha testing. Treat Customer/Firm/MM as account/capacity categories, not institutional or informed traders.

## 2026-11-05 — FINRA historical archive user-certification gate
- FINRA OTC Transparency Website User Guide v6.0 states the user must affirmatively certify on each visit and click "I AGREE" before accessing OTC Transparency data. The guide's screenshots show 2016 weekly data, but the current historical download route has not been verified.
- Do not automate the affirmative certification or accept terms on the user's behalf. FINRA's developer API remains the already-audited rolling historical/production path; older website archives are blocked until the user personally reviews and accepts the terms. No certification was made.


### Phase 111 completion — OCC Volume by Account Type
- Run 42020739832 completed successfully; artifact 13411995693. Four daily dates (2024-11-04/05/06 and 2026-11-03) passed fixed-width/header/exchange/key/numeric checks. Row counts: 37,750; 37,481; 42,266; 41,847. Unique option symbols: 4,207; 4,206; 4,537; 4,631. Group keys: 4,051; 4,069; 4,342; 4,393. Exchange counts: 18; 18; 18; 20.
- 2016-05-31, 2019-05-31 and 2023-11-03 returned identical 41-byte non-data responses. Valid daily data was found from 2024-11-04 through 2026-11-03. This is consistent with a rolling ~24-month window; exact earliest cutoff not exhaustively searched.
- Decision: park OCC as recent participant-composition context only. It lacks direction, opening/closing status and beneficial-owner identity, and does not supply the long daily history needed for a robust independent OOS test. No alpha test.
- Cboe Option Sentiment remains the most information-rich documented options candidate (FAQ says Jan 2012 and OPRA U.S. stock/ETF/index coverage), but the old URL redirects and the current Options catalog omits it. Do not assume orderability; no vendor contact or purchase.
- FINRA historical website archive remains blocked pending the user's affirmative certification. No acceptance was made.


## 2026-11-05 — Phase 112 Cboe Option Trades public sample completed
- Run 42022615770 completed successfully; artifact 13412861022 (7,095,447-byte ZIP; SHA-256 d5407f64e9e6b5bac6773293e6f760004de377282b9f240f2059d5e2bea69613). All 11 offline parser tests passed.
- Public sample HTTP 200; 3,561,778 bytes; SHA-256 a02504e156db28b3f007d9d25a534e4c88ffd8d24ac43f3bf84885583a3d10b8. It contains two nested variants (Calcs included/excluded), each 74,999 rows with identical sequence-key hashes; do not add them. The sample covers only AAPL (one underlying, 308 option series), not full-market coverage.
- Quote checks: 74,218 valid NBBO, 625 locked, 5 crossed, 151 zero/missing; zero duplicate sequence keys. All 15 observed trade-condition IDs and 18 exchange IDs matched the downloaded official mapping files.
- Critical discrepancy: all sample quote_datetime values use a two-component clock such as 21:30.4, while Cboe Option Trades v1.3 specifies full U.S. Eastern trade date/time to milliseconds. Do not infer a timezone or reconstruct intraday timestamps. The adjacent-row sequence/clock monotonicity counter is not a valid acceptance metric because source row order is not established as chronological or sequence-sorted.
- Decision: schema/quote checks pass, documented timestamp conformance remains unresolved, broad market coverage unproven. Retain only as conditional daily trade/quote/IV context; no signed-flow or intraday study. See research/PHASE112_CBOE_OPTION_TRADES_SAMPLE_SCHEMA_AUDIT_2026-11-05.md.

## 2026-11-05 — Phase 113 Cboe Enhanced Options TBT candidate
- Newly prioritized Cboe Enhanced US Options Trade-by-Trade Execution Detail (TBT), based on current official product page and v1.1 specification dated 2026-10-05. Unlike the broad OPRA Option Trades feed, TBT documents SIDE, OPEN_CLOSE, CAPACITY, TRADE_TYPE, EXEC_ID/COMPLEX_EXEC_ID, NBBO/BBO and transaction/floor timestamps.
- Published history starts 2019-10-07; currently C1 only (BZX/C2/EDGX planned), delivered T+1, typically 00:30–01:30 ET next morning. This is materially richer for participant-capacity/position-side hypotheses but is not whole-OPRA coverage and does not identify beneficial owners.
- Phase 113 public-sample audit workflow run 42023567791 is in progress after 8 offline tests were added. It downloads only the public sample and official spec; no purchase, subscription, contact, or authentication. Do not start a duplicate while it runs.
- Before any return test: sample schema and key semantics, actual historical archive boundary/completeness, broad PIT underlying coverage including inactive/delisted names, C1 TBT vs C1 Open-Close reconciliation, T+1/late-file knowledge time, and preregistered handling of complex/auction/floor/routed/provisional trades must pass.
- Official docs: https://datashop.cboe.com/enhanced-us-options-trade-by-trade-execution-detail and https://datashop.cboe.com/documents/TBT_Spec_v1.1.pdf.

F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen. Phases 112–113 are source-feasibility work only; no alpha test or production change.


## 2026-11-05 — Phase 113 Cboe TBT public sample completed
- Run 42023896730 completed successfully; all 9 offline tests passed; artifact 13413280759. Sample ZIP HTTP 200, 3,807,739 bytes, SHA-256 6c99e69e43d259e81bc31334574579cf9c623f5e77ff596cacf268712cd3262c. Current TBT v1.1 PDF HTTP 200, SHA-256 e70599e0829dc5d030ac2e47b73fbd12afd6b7b31047d3ae354bbd884e65dffa.
- Nested 2025-03-28 sample CSV has 113,018 rows, 1,250 underlyings, C1 only, sample filename says 3%. Required schema, transaction/trading-date parsing, positive sizes/prices, capacities and exact-row uniqueness passed. Gate is PASS_PARSE_WITH_UNRESOLVED_CONVENTIONS, not economic approval.
- The sample archive embeds v1.0 spec dated 2026-01-12; current v1.1 is dated 2026-10-05. Both specify SIDE B/S, OPEN_CLOSE O/C and trading segment examples 1=prior-evening/overnight, 2=daytime. Sample has SIDE=T on 69 rows (all also blank open_close), blank open_close on 20,180 rows (17.86%), and TRADING_SEGMENT=1 on every row including RTH. Do not infer T as buy/sell, impute O/C, or rely on trading_segment. T is observed only in Complex Add/Remove, COA Initiator/Responder and Opening Cross rows; blank O/C spans 19 trade types.
- 306 calendar-date mismatches between transact_time and TRADING_DT are all GTH; no RTH/Curb mismatch. NBBO: 111,756 valid, 45 locked, 12 crossed, 1,205 zero/missing. BBO: 109,410 valid, 3,608 zero/missing. Floor-action timestamp on 618 rows: 61 >=90s late, 557 under 90s, zero negative. EXEC_ID has 1,685 repeated groups, all with both B/S sides; these are linkage pairs, not duplicates. COMPLEX_EXEC_ID has 2,875 repeated groups; exact duplicate rows zero.
- Decision: retain C1 TBT as the highest-information conditional options candidate (explicit side/open-close/capacity/trade-type, history advertised from 2019-10-07, T+1), but do not use a directional/open-close feature until sample conventions are explained and C1 Open-Close reconciliation passes. C1-only and a 3% sample do not prove whole-OPRA or broad PIT coverage. See research/PHASE113_CBOE_TBT_SAMPLE_FEASIBILITY_2026-11-05.md.
- Next: C1 Open-Close EOD actual historical 2005 boundary/missing dates and 2011 format break, broad PIT underlying crosswalk including delisted names, and historical T+1/correction availability. Same-date/same-series TBT vs Open-Close public-sample reconciliation was completed in Phase 115; TBT remains secondary. No forward returns or alpha test.

F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen. No source from Phases 112–113 is promoted to an investment signal.


## 2026-11-05 — Phase 114/115: Cboe C1 Open-Close EOD promoted to priority conditional options source
- Phase 114 public sample run 42027724358 succeeded; artifact 13415230222. The C1 EOD sample is 2025-03-28 and identifies a 20% sample. It contains 23,179 series rows across 1,553 underlyings and all 86 post-2011 fields. No duplicate keys, numeric errors or blank numeric cells. Participant buy/sell buckets equal total_exchange_vol exactly on all 23,179/23,179 rows (4,506,840 contracts).
- C1 EOD advertised history begins 2005-01-03; C1 10-minute begins 2011-01-03; C1 1-minute begins 2019-10-07. C1 GTH begins 2023-12-11. The legacy format spec describes 1990–2010, but current DataShop availability starts 2005; do not assume 1990–2004 access. The 2011 format/bucket-meaning break, C1 total_exchange_vol convention through 2019-10-04, shifted C1 OI through 2019-10-04, and previous-close break must be handled explicitly. Product-page history is not proof that every historical file is accessible.
- Phase 115 same-date public sample cross-check: TBT 3% and Open-Close EOD 20% samples on 2025-03-28 share 3,971 option series and 654 underlyings with common series. EOD buckets reconcile exactly on the common series. Underlying-level Spearman between TBT sample volume and EOD capacity volume: Market Maker 0.760, Customer 0.741, Pro-Customer 0.611, Firm 0.704, Broker-Dealer 0.624 (sparse). TBT sample volume is 3.765% of EOD volume on overlapping series, but capacity ratios range 1.75%–5.42%; do not use one global expansion weight.
- This is not independent replication: Cboe says TBT is the transaction-level data used to derive Open-Close. TBT still has SIDE=T and blank OPEN_CLOSE exceptions. Prefer EOD summary for daily classified capacity/side/open-close features; retain TBT for secondary validation.
- Decision: Cboe C1 Open-Close EOD is the highest-priority conditional options-flow candidate so far. It is C1-only, not whole-OPRA; participant labels are clearing-origin/capacity categories, not beneficial-owner identities. Public samples do not establish historical completeness, broad PIT coverage, dissemination timestamps or license cost.
- Next gates: actual 2005 archive and 2011 format boundary/missing dates; broad PIT security crosswalk including inactive/delisted underlyings; T+1 final-file publication/correction timing; historical sample coverage and license estimate. No purchase/contact or returns test without explicit authorization.
- Phase 111 OCC Volume by Account Type remains parked (only ~24-month live history, no side/open-close). Phase 112 Option Trades remains conditional daily context only because its sample timestamp format does not conform to v1.3. Phase 113 TBT remains secondary pending convention resolution.
- F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen; no alpha test or production change.


## 2026-11-05 — Phase 116 Cboe U.S. Equities Historical Market Volume public archive completed
- Live run 42033472218 succeeded; artifact 13416659256 (5,940,729 bytes). All 14 offline parser/regression tests passed.
- Downloaded all 18 annual daily and 18 annual monthly files listed by Cboe for 2009–2026: 72,103 daily rows, 3,395 monthly rows, 4,488 trading dates from 2009-01-02 through 2026-11-04. Completed participant-month daily-vs-monthly reconciliation passed for 55,865 comparisons across all 12 numeric fields within explicit scale-aware source-rounding tolerances.
- Legacy 2009 monthly URL uses header `Day` but YYYY-MM values; normalized in parser. Some legacy monthly notional and share totals are rounded differently from daily sums; parser now uses documented conservative tolerances (daily notional max($0.20, 1e-10 relative); monthly notional max($2, 1e-9 relative); monthly shares max(1 share, 1e-7 relative); trade counts exact).
- Correctly mapped historical/current FINRA TRF market-center codes DQ, DN and DB. The Cboe current market summary explicitly labels `TRFs (DQ,DN,DB)`; older historical CSV names include NASDAQ (DQ), NYSE (DN) and NASDAQ (DB), so string-only "TRF" matching would have silently missed historical data. The artifact includes 4,488 daily marketwide TRF share/notional fractions.
- This source is market-center/tape aggregate only, with no ticker, side, MPID, capacity, order or beneficial-owner identity. Retain as marketwide venue-regime context candidate, not a Smart Money signal or per-stock feature.
- Strict PIT remains unproven: Cboe's public archive page/files provide no historical first-publication timestamps, immutable file vintages or correction history. No historical alpha/return test authorized. Prospective snapshotting can build a clean future archive but cannot backfill historical knowledge times.
- Official references: https://www.cboe.com/markets/us/equities/market-statistics/historical-market-volume/ and https://www.cboe.com/us/equities/market_share/market/.
- Cboe C1 Open-Close EOD remains the highest-information conditional options candidate (Phases 114/115); Phase 116 is a separate public market-regime control.
- No data purchase/contact, no alpha test, no F80 changes. F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen.


## 2026-11-05 — Phase 117 FINRA ATS/OTC revision-impact and PIT eligibility

- Replayed the immutable Phase 109 raw artifact (968,139 rows; 108,444 symbol aggregates across five weeks and T1/T2). The raw compressed-row SHA-256 was verified as `45b6b169c1d57a1874438362295a656c5bc6499b2c29d6e3be8bd10a48425231`.
- In all 108,444 aggregate rows, `lastUpdateDate = max(initialPublishedDate, lastReportedDate)`. 1,882 rows (1.735%) have an update marker later than first publication.
- Revisions are concentrated in T1 OTC non-ATS: 1,428/10,668 rows (13.386%). Dropping revised rows would retain only 66.76% of shares and 63.79% of trades in that family. Overall it retains 89.92% of shares and 88.56% of trades; this is not a neutral exclusion.
- Critical PIT ruling: filtering out rows because the current extract shows they were eventually revised is itself future-informed selection. Do not call that an unbiased PIT subset. Do not backdate current final values to `initialPublishedDate`. `lastUpdateDate` is an underlying firm-update marker, not a documented public dissemination timestamp; +1/+5 session buffers remain sensitivities only.
- FINRA ATS/OTC remains conditional, not alpha-ready. Need verified public update timing or actual vintages/prospective immutable captures, plus permanent security identity and delisted coverage. No forward-return test or F80 change.
- Reproducible audit: `research/phase117_finra_ats_pit_revision_impact.py`; six offline tests pass. Full report: `research/PHASE117_FINRA_ATS_PIT_REVISION_IMPACT_2026-11-05.md`.
- Phase 69 state corrected: run 41959603351 completed with zero incremental Form 144 candidates for the ten-CIK extension; do not repeat unchanged scan.

## 2026-11-05 — Phase 118 SEC 13D/13G Phase 84 artifact adjudication

- Original Phase 84 failure was a denominator/classification issue, not a missing structured filing: accession 0001104659-26-057293 is indexed under both SC 13D/A and SC TO-T/A, but its raw SEC-HEADER CONFORMED SUBMISSION TYPE and both document types are SC TO-T/A / EX-99.(A)(5)(B). Quarantined as a non-13D/G index alias; no 13D/G document exists in the submission.
- Re-audited immutable artifacts Phase 84 #13364856424 and Phase 82 #13353118959. Recomputed 600/600 raw SHA-256 hashes and sizes, 600/600 SEC acceptance UTC values from America/New_York header timestamps, and 200/200 XML subject/filer matches. After quarantine, 599/599 actual 13D/G forms match and 192/192 actual mandatory-XML 13D/G rows contain XML.
- Phase 84 role pilot: 367 CIK-candidate rows all resolved by SEC-HEADER (224 subject, 143 filer-only); descriptive post-stratified estimate across 34,400 candidate accessions is 52.06% subject-target / 47.94% filer-only. No inferential CI. Candidate coverage is conditional on current 319 CIKs; not global recall or historical universe membership.
- Phase 118 status: PASS_WITH_INDEX_ALIAS_QUARANTINE. Reproducible artifact-only script `research/phase118_sec_13dg_phase84_adjudication.py`, seven tests in `research/test_phase118_sec_13dg_phase84_adjudication.py`, report `research/PHASE118_SEC_13DG_PHASE84_ARTIFACT_ADJUDICATION_2026-11-05.md`. No live SEC requests or forward returns.
- Next gate: deterministic subject/reporting-person/group and amendment lineage, then historical CIK-to-security and active/delisted PIT crosswalk. SEC acceptance is reproducible but not independently verified dissemination time; use next-session availability conservatively. No alpha test or F80 change.

## 2026-11-05 — Phase 119 SEC 13D/13G XML schema and amendment-lineage audit

- Parsed the 200 XML-bearing filings in the Phase 84 pilot separately by schema: 79 13D and 121 13G. Issuer/filer CIKs match SEC-HEADER on 200/200; event dates are present on 200/200; all 97 amendments carry amendmentNo.
- 13D has 260 reportingPersonInfo nodes; reporting-person CIK appears on 158/260 (60.8%), while names and core ownership fields are present on all nodes. 13G has 210 coverPageHeaderReportingPersonDetails nodes; per-person CIK is absent, but filing-level filer CIK matches header on 121/121; names and ownership fields are present on all nodes. A generic 13D parser would miss all 121 13G reporting-person nodes.
- CUSIP field present on 139/200; class title on 200/200. Security key must include CUSIP/class: six BlackRock filings with the same issuer/filer/name but six distinct CUSIPs would otherwise be falsely merged. Repeated group keys fall from 3/10 rows to 1/2 rows for 13G after security key; 13D from 4/9 to 3/6.
- Of 97 amendments, 46 contain previousAccessionNumber. Scanning all 43 Phase 82 master indexes validates 45/46 pointers by prior accession presence, issuer CIK, filer CIK, same form family and earlier filing date. One pointer on accession 0000886982-25-001416 to 0000769993-25-000432 is absent from the frozen index; quarantine it and do not guess. 51/97 amendments lack explicit predecessor pointers. Prior raw submissions have not yet been fetched, so CUSIP/person/ownership continuity is not yet verified.
- Only 200/600 sample rows have XML; the 400 non-XML rows need a legacy HTML parser. XML-only history cannot backfill 2016–2024. Event date is not knowledge date; use next-session-after-acceptance until dissemination time is validated.
- Phase 119 status: PASS_WITH_LINEAGE_CAVEATS. Report research/PHASE119_SEC_13DG_XML_SCHEMA_AND_LINEAGE_FEASIBILITY_2026-11-05.md; auditor research/phase119_sec_13dg_xml_lineage_audit.py; six tests research/test_phase119_sec_13dg_xml_lineage_audit.py. CI runs 42055578553 and 42055592782 passed.
- Next gate: download only the 45 index-validated predecessor submissions and compare security/reporting-person/ownership continuity; keep the unresolved pointer quarantined. Then build historical CIK-to-security PIT crosswalk and legacy HTML parser. No forward returns or alpha tests; F80 remains frozen.


## 2026-11-05 — Phases 120–122 SEC 13D/13G predecessor and ownership continuity

- Phase 120 run 42058411930 retrieved and hash-validated all 45 predecessor submissions selected from the 45/46 Phase 119 index-validated pointers; zero download/accession failures, 44 identical mirror pairs and one single-valid-path case. All 45 SEC-header identity/chronology checks passed. Its workflow conclusion was failure because the data gate correctly returned INCOMPLETE_OR_CONFLICT: 34 header+security passes, 7 header-only/unresolved cases and 4 CUSIP conflicts. This was not a download failure.
- Phase 121 run 42060958167 completed with PASS_WITH_CAVEATS after re-parsing the immutable current and predecessor artifacts. Across 45 links: 39 exact CUSIP matches, 5 CUSIP mismatches and one class-title-only match without CUSIP. The five mismatches comprise a documented SPAC business combination, a documented reverse split, a documented ADS-ratio change, a different ETF series under the same trust CIK, and a suspected (not confirmed) Toro predecessor filing CUSIP mis-key. The Toro link remains quarantined. The class-title-only Jefferies Credit Partners BDC link remains weaker than a CUSIP match.
- Phase 122 run 42062157962 passed 7 offline tests and completed the immutable artifact comparison. All 45 current and 45 predecessor raw hashes were revalidated. Of 21 XML predecessor links, 20 exact-CUSIP pairs were eligible (14 13D, 6 13G); one CUSIP-mismatch XML pair was excluded. The other 24 legacy HTML predecessors were excluded from XML ownership comparison, not treated as zero ownership.
- Across 20 eligible XML pairs, 59 reporting-person links matched by normalized name (47 13D, 12 13G). Reported share amounts changed on 34/59 links and percent-of-class changed on 43/59. Available person-CIK comparisons matched 36/36. The audit found 24 identical amount/percent pair observations within 13D group flags across current/prior filings; these are overlap diagnostics only. Never sum group members or infer separate beneficial owners from the group flag.
- Interpretation: beneficial-ownership snapshots are not transaction-level trade flow. Changes may reflect transfers, attribution, denominator changes, conversions, corporate actions or corrections. 13G per-person CIK is absent in this schema; name matching is not a permanent ID. SEC acceptance remains a conservative proxy for knowledge time; use next-session availability until public dissemination is independently verified.
- Phase 122 report: `research/PHASE122_SEC_13DG_XML_OWNERSHIP_CONTINUITY_AUDIT_2026-11-05.md`; auditor `research/phase122_sec_13dg_xml_ownership_continuity_audit.py`; seven tests; workflow `.github/workflows/phase122_sec_13dg_xml_ownership_continuity_audit.yml`.
- Decision: 13D/G remains conditional, not alpha-ready. The 45-link stratified pilot is not a global census; still required are historical subject-issuer discovery, effective-dated CUSIP/security mapping, inactive/delisted coverage, legacy HTML parsing and independently verified dissemination timing. No forward returns, feature selection, alpha test, paid data, or production changes.
- F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen.


## 2026-11-05 — Phase 123 SEC 13D/13G regulatory PIT regime audit

- Added research/PHASE123_SEC_13DG_REGULATORY_PIT_REGIME_AUDIT_2026-11-05.md from the SEC final rule Release Nos. 33-11253 / 34-98704.
- Do not use one 2024 break for all filings: Schedule 13D deadline amendments apply from 2024-02-05; revised Schedule 13G deadlines apply only from 2024-09-30; mandatory 13D/G XML compliance begins 2024-12-18 (voluntary XML from 2023-12-18).
- Schedule 13D initial >5% deadline changed from 10 calendar days to five business days; material amendments changed from “promptly” to two business days. Schedule 13G QII/exempt, passive and accelerated >10%/5%-change rules differ and must be classified separately.
- EDGAR transmissions by 10 p.m. Eastern can be assigned the same business-day filing date. Preserve SEC acceptance datetime, filing date, event date and first tradable session as separate fields.
- Event date is not public knowledge time. Use the first regular U.S. equity session whose open occurs after verified acceptance as the conservative tradable-availability convention; do not backdate ownership snapshots.
- SEC economic analysis notes possible pre-filing anticipation by other traders around Schedule 13D. This is a hypothesis about foreknowledge/run-up, not evidence that public filing signals have post-publication alpha. Separate pre-filing return-chasing from post-publication incremental information.
- Decision: regulatory timing/schema breaks are now explicit, but 13D/G remains not alpha-ready until global subject-issuer discovery, effective-dated security identity, delisted coverage and legacy HTML parsing pass. No returns/alpha tests or F80 changes.


## 2026-11-05 — Phase 124 global 13D/13G sample — final disposition

- Corrected run 42073725379 produced a complete immutable artifact, but GitHub Actions concluded failure because the exit gate did not accept the intentional PASS_WITH_INDEX_ALIAS_QUARANTINE status. This was a workflow-status gate defect, not a raw-download or identity-reconciliation failure. The corrected status logic and regression tests are now exercised by downstream Phase 125/126 CI; no duplicate live SEC pull was launched.
- The deterministic sample contains 600 index rows: 599 actual 13D/G submissions plus one confirmed SC TO-T/A index alias quarantined from the 13D/G population. The source index contains 324,964 unique accessions across 43 quarters (2016Q1–2026Q3); after 762 prior-pilot/predecessor exclusions, 324,202 remained eligible across 172 quarter × form-family × amendment strata.
- All 600 raw files passed SHA-256 and accession/date checks; 599 actual 13D/G submissions matched header accession, form family and filing date. There were zero transport/mirror failures. The sample is a filing-index sample, not a historical tradable-security universe.
- The 102 XML rows include all 99/99 mandatory-XML rows after 2024-12-18. Header subject/filer CIK presence in 599/599 rows is only header metadata presence; Phase 126 shows it must not be described as verified issuer coverage for legacy HTML filings.
- No forward-return, alpha, or production test was part of Phase 124. F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen.

## 2026-11-05 — Phase 125 SEC 13D/G cover-page CUSIP audit

- Phase 125 run 42077788015 completed successfully using only immutable Phase 124 artifacts; it made no new SEC requests.
- The legacy HTML parser was tightened to use only the first CUSIP value on the primary cover page, including values split across HTML text nodes. Later CUSIPs in narrative/exhibits are intentionally excluded and cannot substitute for a missing cover-page value. The parser distinguishes 000000000 as an XML placeholder rather than an invalid-format CUSIP.
- Across 599 actual filings: 541 rows have a unique checksum-valid CUSIP, two have checksum-invalid CUSIPs (584680106 in legacy HTML and 50214C200 in XML), 55 have no usable CUSIP (23 legacy, 32 XML), and one XML row contains the all-zero placeholder.
- Weighted valid cover-page CUSIP coverage is 96.84% for legacy HTML (473/497 rows), 66.71% for XML (68/102), and 91.36% overall. These are post-stratified descriptive coverage estimates, not inferential confidence intervals.
- The audit found 524 distinct checksum-valid CUSIP strings and 525 (header_subject_cik, CUSIP) pairs; CUSIP 81752R100 appears under two different header subject CIKs. Phase 126 adjudicates that conflict.
- Decision: the cover-page CUSIP is a useful security identifier candidate, but it is not permanent and does not by itself resolve issuer CIK, share class, corporate actions, delistings or ticker history. No returns/alpha test.

- Superseded for XML CUSIP coverage by Phase 127: legacy HTML coverage remains 96.84%, but corrected XML coverage is 97.38% and corrected overall coverage is 96.94% (see Phase 127 below).

## 2026-11-05 — Phase 126 SEC 13D/G body-first issuer identity audit

- Phase 126 run 42079214500 passed. It reconciled the immutable Phase 124/125 artifacts, verified 600 raw SHA-256/accession/date checks, retained 599 actual 13D/G rows and quarantined one index alias. No SEC network requests were made.
- Structured XML issuer CIK matched the SEC-HEADER subject CIK in 102/102 XML rows in this sample. This is a useful conditional result, not proof of universal correctness.
- Two legacy header/body issuer-role discrepancies were hand-adjudicated:
  1. Accession 0001549575-20-000008: SEC-HEADER subject and filer both say Dalal Street, LLC (CIK 1549575); the 13G cover page says Seritage Growth Properties, CUSIP 81752R100.
  2. Accession 0001903596-22-000671: SEC-HEADER subject says American Community Capital, LP (CIK 1626837), filer is Igwealor Frank I (CIK 1945609); the 13D cover page says Nano Mobile Healthcare, Inc., CUSIP 63010B200.
- The Seritage discrepancy is independently reinforced by accession 0001193125-21-208169: the same body issuer and CUSIP 81752R100 appear with header subject CIK 1628063. The two filings therefore carry different header subject CIKs for the same body issuer/CUSIP.
- A third name difference was deliberately not counted as an error: accession 0001172661-24-001310 has header subject ArrowMark Financial Corp (CIK 1578987), a FORMER COMPANY entry for StoneCastle Financial Corp, and a StoneCastle cover page/CUSIP 861780104. This is a valid historical issuer-name change with the same CIK, not a role mismatch. The filer CIK is 1483859.
- Decision: do not use legacy SEC-HEADER SUBJECT COMPANY CIK as an authoritative issuer CIK or as issuer-universe coverage. For legacy 13D/G, start from body cover-page issuer name plus cover-page CUSIP; preserve former-name fields and require an effective-dated CUSIP/security master before joining returns. XML issuerCik can be used conditionally where present and validated.
- Only the two discrepancies and one rename control were manually adjudicated; they are concrete examples, not an estimated global error rate. No broad body-issuer parser was promoted. No forward returns, alpha tests, vendor purchases or production changes.

## Next 13D/G gate

- Build a deterministic, effective-dated CUSIP-to-security/issuer crosswalk with share-class, ETF-series, ADR, rename, split, merger and delisting handling; retain unresolved mappings rather than fuzzy-assigning them.
- Verify mapping against an independent historical security master and preserve acceptance timestamp separately from event date. Only then define a preregistered 13D activist/passive event hypothesis and test incremental information versus frozen LTM/F80 with chronological OOS, identical exposure/costs, bootstrap and LOO.
- Continue Cboe Open-Close EOD as the leading options-flow feasibility candidate in parallel; no vendor purchase or licensing commitment without explicit authorization.
- F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen.
## 2026-11-05 — Phase 127 SEC 13D/G XML CUSIP schema correction

- [Phase 127 run 42079517644](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42079517644) passed using the same immutable Phase 124 sample; no new SEC requests were made. All 600 raw hashes/accession/identity checks passed, and 15 Phase 124 plus 21 Phase 125 regression tests passed.
- Root cause: the Phase 125 XML parser read only issuerCusip. SEC 13D/G XML also stores values under issuerInfo/issuerCusips/issuerCusipNumber. The corrected parser reads both tags under issuerInfo, deduplicates identical values and preserves distinct values for ambiguity handling.
- Corrected coverage across 599 actual filings: 571 unique checksum-valid CUSIPs; 23 missing (all legacy HTML); 2 explicit all-zero placeholders; 2 checksum-invalid values; 1 malformed 10-character value; 0 ambiguous rows.
- Weighted valid coverage is 96.84% for legacy HTML (473/497), 97.38% for XML (98/102), and 96.94% overall (571/599). Phase 127 supersedes Phase 125's 66.71% XML and 91.36% overall figures; legacy HTML results are unchanged.
- The two XML placeholders are 000000000 in accessions 0001213900-26-020010 and 0001104659-26-086334. The malformed 10-character value 0753018100 is in 0002006045-26-000008 and is not truncated or repaired. The XML checksum-invalid value 50214C200 is in 0002076128-25-000002; the legacy checksum-invalid value 584680106 remains in 0001213900-19-010653. All remain quarantined.
- Decision: pass the CUSIP extraction feasibility gate for this sample, not the permanent-identity or tradable-universe gate. An effective-dated security master remains mandatory; no returns/alpha test.
- Artifact 13438903901 (90-day retention), ZIP SHA-256 b80d15d736ba6c45f4f3c5dd569604175e221414b31a28fd58a62010a805c166. [Phase 127 report](research/PHASE127_SEC_13DG_XML_CUSIP_SCHEMA_CORRECTION_2026-11-05.md).



## 2026-11-05 — Phase 128 SEC 13D/G CUSIP cross-schema identity feasibility (PASS)

- Reconciles immutable Phase 124 (600 index rows; 599 actual filings; one alias) and Phase 127 corrected CUSIP artifacts. No new SEC requests.
- Preliminary repeated-CUSIP structure: 553 unique checksum-valid CUSIPs; 18 repeated groups (14 legacy-only, 2 XML-only, 2 cross-schema). Only two cross-schema links exist: 90290N109 (USA Compression Partners, CIK 1522727) and G38644103 (GigaCloud Technology, CIK 1857816); both have matching issuer/subject CIK and normalized issuer name across schemas.
- 81752R100 reproduces the Seritage legacy header-CIK conflict: same body issuer name and CUSIP across two filings, but subject CIKs 1549575 and 1628063.
- The legacy body-name heuristic yielded 442/497 apparent candidates; 82 contain obvious separators/boilerplate, and the remaining 360 are unvalidated. It is not promoted as an identity source.
- Decision: internal cross-schema CUSIP overlap (2/553 = 0.36%) is far too sparse to build a historical security master. Need effective-dated permanent security mapping before return tests. No alpha/production changes; F80 remains frozen.
- Phase 128 Actions run 42080440140 succeeded; all Phase 124–128 regression suites passed (52 tests total across the four suites), 600/600 raw hashes verified, and no audit errors. Artifact 13439559366; ZIP SHA-256 `aed19dba803bd47f9ac6a846807d93a778b05bad3cf637c18936e1d3593fb22b`.

## 2026-11-05 — Phase 129 SEC 13(f) official-list CUSIP PIT overlap audit (in progress)

- The first attempt (run 42081506576) failed before source access because a GitHub expression was escaped incorrectly in the artifact-download step. The first corrected run (42081840017) downloaded both source artifacts and passed tests, then failed on the Phase 127 summary filename. Both implementation defects were corrected; no SEC 13(f) list download was performed in those failed attempts.
- Current run [42081987897](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42081987897) passed compilation, the Phase 124/125/126/128/129 regression suites, and both immutable artifact downloads. The 45-quarter SEC 13(f) list availability/CUSIP overlap audit is running.
- Scope: 2015Q3–2026Q3 official 13(f) lists, including 2015Q3 as a pre-sample anchor for early 2016 filings. The audit uses the Phase 127 corrected 13D/G CUSIPs and SEC acceptance dates, tests 1- and 5-calendar-day buffers after the later of PDF Run Date and HTTP Last-Modified, and separately records same-quarter lookahead matches.
- The official 13(f) list is only a 13F-reportable security reference, not a complete security master. PDF Run Date/Time is a generation timestamp, not verified public-release time; no predictive use is permitted until publication availability is independently verified.
- Raw 13(f) list rows, CUSIPs sourced from the list, issuer names and descriptions are not uploaded. The artifact retains only source hashes/metadata and match booleans against CUSIPs already present in SEC 13D/G filings. No alpha test, vendor purchase or production change.


## 2026-11-05 — Phase 130 SEC 13(f) list and Form 13F PIT/scope adjudication

- Added `research/PHASE130_SEC_13F_LIST_AND_FILING_PIT_SCOPE_AUDIT_2026-11-05.md` after reviewing current SEC official documentation.
- The SEC Official List page exposes quarterly archives from 1996 through 2026Q3 and documents CUSIP, option indicator, issuer name/description and add/delete status. It is a Section 13(f)-eligible list, not a complete security master; the eligible population excludes open-end mutual funds and does not establish ticker continuity.
- SEC Form 13F data sets cover July 2013–August 2026 as flattened as-filed extracts. Use individual EDGAR accessions and acceptance timestamps for PIT, not quarter-end or data-set batch dates. The normal 45-day reporting lag, long-only scope, unreported written options, confidential treatment and later amendments/restatements make 13F holdings delayed and incomplete.
- Phase 129 run 42081987897 remains in progress; compilation, regression suites and both immutable input-artifact downloads passed, but the 45-quarter live list audit has not produced an artifact/result yet.
- Phase 129's +2/+6 calendar-day list-availability fields remain sensitivity proxies only. PDF Run Date is generation time, not verified first publication; HTTP Last-Modified is retrieval metadata, not proof of public dissemination. Same-quarter overlap remains a lookahead diagnostic.
- Decision: the official 13(f) list may be used only as a conditional eligibility cross-check. Do not use it as a security master, ownership signal or PIT feature. Do not revive the previously killed N-PORT dose-response hypothesis under a 13F label. No return/alpha test, paid data, vendor contact or production change.
- `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen.


## 2026-11-05 — Phase 131 SEC Form 13F as-filed event-state and PIT feasibility

- Added `research/PHASE131_SEC_13F_AS_FILED_EVENT_STATE_PIT_AUDIT_2026-11-05.md` after reviewing the current SEC bulk-data schema, Form 13F FAQs and actual EDGAR filing-detail pages.
- The SEC Form 13F bulk archive is documented as July 2013–August 2026 and quarterly. It is flattened, as-filed structured XML; the SEC warns that it can contain redundancies/inconsistencies and omits filing metadata. The bulk SUBMISSION table has accession, filing date, type, filer CIK and report period, but no accepted time-of-day.
- Strict PIT therefore requires accession-level EDGAR acceptance timestamps. Two examples have accepted timestamps on the prior calendar date to the displayed filing date: 0001275218-26-000008 (accepted 2026-08-10 18:34:09 ET; filing date 2026-08-11; 2024Q1 restatement) and 0001635409-25-000005 (accepted 2025-08-13 19:30:14 ET; filing date 2025-08-14). A filing-date-only join can misplace the information event.
- Amendment handling must be event-sourced: restatements supersede the prior public state only from their own acceptance time; add-new-holdings amendments and confidentiality-release filings supplement only from their own acceptance time. Never backdate amendments to report quarter-end or original filing.
- Manager aggregation must resolve shared discretion/other-manager relationships to avoid counting the same economic exposure multiple times. 13F remains long-only and incomplete; short equity and written options are omitted, held options use the underlying CUSIP plus put/call flag, some small positions may be omitted, and confidential treatment can delay holdings.
- Decision: Form 13F remains a conditional delayed-holdings candidate, not transaction flow or proven informed activity. No 13F panel, return/alpha test, vendor purchase or production change. Require acceptance-time crosswalk, amendment-state tests, manager graph, effective-dated security master and broad PIT coverage before any preregistered test.
- Phase 129 (run 42081987897) remains a separate in-progress audit of the 13(f) eligibility list; its current job has passed setup, compile, regression and both input-artifact downloads, but the live 45-quarter overlap step remains in progress and no artifact is available. Do not duplicate it.
- `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen.


## 2026-11-05 — Phase 132 cross-phase execution adjudication

- Rechecked the latest 20 GitHub Actions runs, jobs, step summaries, logs, artifacts, branch refs, PR #13 and the Phase 129/130/131 research files. No workflow is currently queued or running.
- **Phase 129 run 42081987897 is cancelled, not active.** Job 127437139618 passed compilation, regression tests and downloads of the immutable Phase 124/127 inputs. The live 45-quarter SEC 13(f) download/parse/overlap step was cancelled at 18:57:42 UTC after the workflow's 45-minute job limit. No Phase 129 artifact was produced. The serial loop has multiple URL candidates/retries and writes its manifest only after the full loop, so timeout leaves no resumable output. This is an execution-time/resumability issue, not a negative CUSIP-overlap result.
- **Decision: close Phase 129 as INCOMPLETE_TIMEOUT; do not rerun unchanged.** Phase 130 already limits the official 13(f) list to a conditional eligibility cross-check, not a complete security master or PIT feature. Re-entry requires a new necessary research question, per-quarter resumable checkpoints, SEC-compliant pacing and independent first-publication evidence. No alpha test is authorized.
- **Phase 124 data result is usable despite a red Actions conclusion.** Run 42073725379's log shows status PASS_WITH_INDEX_ALIAS_QUARANTINE, 600/600 index rows resolved, 599 actual 13D/G filings, one quarantined SC TO-T/A index alias, zero download/mirror failures, and all 600 raw hash/accession/date checks passed. The run nevertheless exited 2 because the execution used an older success gate that did not accept the alias-quarantine status. Its immutable artifact was uploaded and successfully consumed by Phases 127/128. Treat the data audit as complete with the documented alias caveat; do not repeat the 600 downloads.
- Phase 128 run 42080440140 passed. Its result remains decisive for the current identity gate: only 2 of 553 distinct valid CUSIPs (0.36%) overlap across the legacy HTML and XML cohorts. This does not support an internal cross-schema historical security master.
- The most recent 13F-list workflow dispatch with no jobs/artifacts (run 42081985066) adds no empirical result and is not a reason to repeat the audit.
- Current branch phase99-broad-pit-universe-charter is at dc3e6199c96956496e715f4ed3da2ed9053e0072; PR #13 remains open, mergeable, unmerged, targeting main. No branch merge or production write was performed.
- Cboe C1 Open-Close EOD remains the leading options-flow candidate based on Phases 114/115 sample/accounting audits, but paid historical coverage, broad PIT underlying identity and final-file availability remain unresolved. No data purchase, vendor contact or terms acceptance.
- Existing standalone Form 4, FINRA short-flow × short-interest, CFTC equity-index positioning and N-PORT dose-response hypotheses remain killed; do not retune them without a materially new preregistered mechanism.
- No forward-return/alpha test or production change. F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen.


## 2026-11-05 — Phase 133 OCC Flex Reports contract-level OI audit (complete; long-history gate failed)

- Added the preregistered Phase 133 audit of the OCC Flex Reports endpoint (reportType=OI, optionType=E) across seven fixed dates from 2018-01-03 through 2026-11-04. It uses the full returned file and reports unique option contracts/underlying roots; it does not hard-code the original 335 ticker universe.
- Workflow [42097577204](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42097577204) completed successfully; compilation and all seven offline tests passed, and artifact 13448395010 was uploaded. Four dates (2018, 2020, 2022, 2024) returned 'File requested does not exist'; 2025-01-03, 2026-01-05 and 2026-11-04 returned non-empty fixed-width report files.
- This follows Phase 53B: OCC Volume Query passed recent 335-list diagnostics (645/670 valid ticker-date responses, 96.27%) but the OCC UI confirms a 24-month retention boundary; the endpoint aggregates call/put volume by Customer/Firm/Market Maker and exchange, without buy/sell side, open/close, strike/expiry or OI. It fails long-horizon OOS feasibility and is not a standalone Smart Money signal.
- Phase 133 tests whether the separate Flex Reports OI endpoint exposes a longer contract-level history. Its result will still require independent public-release timing, revision, effective-dated underlying identity and economic-incrementality gates. No alpha test is authorized.
- F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen.


- Phase 133 result report: research/PHASE133_OCC_FLEX_OI_HISTORICAL_FEASIBILITY_RESULT_2026-11-05.md. The OCC Flex Reports page explicitly limits the UI to the past 24 months. The old-date probes agree. The current files are fixed-width/page-formatted; the generic CSV parser did not validate contract rows or OI values. The official record layout confirms eight contract-level fields and a strike-format break on 2017-03-25, but does not provide a PIT release timestamp.
- Decision: close OCC Flex Reports as FAIL_FOR_LONG_OOS / RECENT_CROSSCHECK_ONLY. Do not spend effort on a fixed-width parser absent a new use case. OCC Volume Query is also 24-month-only and lacks buy/sell and open/close. Cboe C1 Open-Close EOD remains the highest-priority options candidate, conditional on paid archive, PIT identity and final-file timing.


## 2026-11-05 — Phase 134 Cboe options surface/sentiment source re-triage

- Reviewed the latest 25/756 Actions runs, branch refs, PR #13, Phase 133 job log and artifact. No Actions jobs are queued/running. Phase 133 run 42097577204 passed and uploaded artifact 13448395010; its OCC Flex long-history gate remains failed. Phase 129 run 42081987897 is cancelled at the 45-minute limit with no artifact; do not rerun unchanged.
- Current Cboe Volatility Surfaces product page advertises daily EOD files and historical availability from August 2011. The April 2025 specification defines four price-/delta-relative and constant-maturity/expiry-specific surfaces, with 9:40 ET and end-of-day snapshots, interpolated from listed-option mid-volatility. Weighted confidence is included; values below 0.5 should be treated with suspicion. Decision: leading new IV/skew context candidate, not flow; broad symbol/inactive coverage, sample integrity, historical delivery/revision timing and price remain unverified.
- Option Sentiment v1.4 (May 2025) specification is unusually rich (directional premium/volume, net delta, IV30/IV90, normalized 25-delta skew, OI, participant/exchange volume, size and DTE buckets), but its former product URL redirects to the DataShop home page and it is absent from the current Options catalog. The FAQ still lists Jan 2012 history. Decision: dormant until current orderability/sample/methodology are verified; do not treat a surviving PDF as current access.
- Option EOD Summary is currently listed, covers OPRA U.S. stock/ETF/index options and advertises Jan 2012 on its product page; the FAQ lists Jan 2010, so Jan 2012 remains the conservative floor. Its existing public sample covers only four underlyings and does not establish broad coverage.
- Option Trades is currently listed with Jan 2012 history and full-OPRA trade/NBBO fields, but Phase 112's compact time-only sample timestamp remains inconsistent with the published specification. No signed-flow/intraday use until resolved.
- Open-Close remains the strongest participant/open-close source (C1 from Jan 2005; other Cboe venues from 2018) but is venue-limited and subject to historical format/volume/OI/GTH convention breaks. DataShop FAQ says current daily option files are normally delivered next day 00:05–03:00 ET but may be delayed until after next market open; this is not historical per-file first-publication evidence.
- OptionMetrics IvyDB US + Signed Volume remains the leading external signed-flow candidate from Phase 59, conditional on a sample, permanent-ID/PIT validation, license and price. No vendor contact, purchase, cart action or terms acceptance occurred.
- No forward-return/alpha test, code/model/production change or universe change. Keep all source hypotheses separate and test only after historical coverage, permanent identity, ex-ante availability and licensing gates. F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen.
- Report: `research/PHASE134_CBOE_OPTIONS_SURFACE_AND_SENTIMENT_SOURCE_RETRIAGE_2026-11-05.md`.


## 2026-11-05 — Phase 135 Cboe Options PITCH microstructure feasibility

- Added [Phase 135 report](research/PHASE135_CBOE_OPTIONS_PITCH_MICROSTRUCTURE_FEASIBILITY_2026-11-05.md) after reviewing the current Cboe product page and Titanium Multicast PITCH specification.
- Cboe Options PITCH advertises daily historical archives from October 2019 for C1/C2/BZX/EDGX, partitioned by exchange and Matching Engine, with RTH/GTH depth-of-book and execution events. The protocol supplies per-unit sequence numbers, Time/Time Reference and nanosecond offsets, order lifecycle events, and options symbol mapping to OSI/underlying.
- PITCH is promoted as a conditional venue-specific microstructure candidate, not participant identity or proof of smart money. The feed is anonymous; Add Order side is resting side, and Trade side is not an aggressor label. Hidden executions, order-book state, trade breaks, sequence gaps and GTH segments require careful handling.
- No public historical sample is exposed on the product page. Archive completeness, file size, historical symbol-map retention, inactive/delisted underlying coverage, exact first-publication timing, and price remain unverified. Current product guidance says daily files typically appear after 8 p.m. ET; this is not historical delivery evidence.
- Cboe Complex Order Flow currently exposes subscription only (no historical purchase type on the page); classify as prospective-only until archive history is confirmed. Databento remains the broader multi-venue L2/L3 concept from Phase 32; Cboe PITCH is a narrower alternative, not a replacement.
- No alpha/return test, purchase, cart action, vendor contact, terms acceptance, code/production change or universe change. F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen.

## 2026-11-05 — Phase 136 Cboe Volatility Surfaces public-sample audit

- Added Phase 136 specification, auditor, six offline tests and final result: research/PHASE136_CBOE_VOLATILITY_SURFACES_SAMPLE_AUDIT_RESULT_2026-11-05.md.
- Final workflow [42115525546](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42115525546) passed compile, all six tests, public sample retrieval and aggregate artifact upload. Artifact [13455975956](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42115525546/artifacts/13455975956); sample ZIP SHA-256 d3cb21be928dc1001a54f697aed5009e96da9c824d233a0978a4c8998e81a5e3.
- Public sample returned four expected CSVs (2025-04-07), 360 rows total, one unique underlying, 5,760/5,760 IV cells valid, 5,760/5,760 confidence cells within documented domains, 100% timestamp parse, zero duplicate surface keys. Schema passes; sample breadth does not establish broad coverage.
- Corrected confidence classification: 689 negative extrapolation/flat-lining codes are separate from 32 positive confidence values below 0.5. These points must be excluded/flagged in future features. The expiration-specific price-relative surface carries most of the negative codes (559/2,312 confidence cells).
- Decision: retain as leading IV/skew context candidate, but no alpha test until actual historical date coverage, multi-symbol/inactive-universe coverage, effective-dated identity, missing/revision policy and first-publication/file-receipt PIT are verified. Calculation timestamps are not publication timestamps.
- No forward-return test, vendor contact/purchase, terms acceptance or production change. F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen.


## 2026-11-05 — Phase 137 IVolatility OPRA signed-flow API revalidation

- Added [Phase 137 report](research/PHASE137_IVOLATILITY_OPRA_SIGNED_FLOW_API_REVALIDATION_2026-11-05.md). IVolatility's 2026-10-14 release now documents `/equities/intraday/options-net-flow`: OPRA trades signed against NBBO, midpoint volume left unclassified, classified-volume share returned, minute/daily call/put buys/sells, net premium/delta, customer gamma/vega and filters for sweeps, trade size, 0DTE, multi-leg and execution type; advertised history starts 2015. New dealer exposure/GEX endpoints advertise history from 2014.
- Promoted IVolatility's new endpoint to the top-tier **conditional broad signed-flow candidate**. This is a source-priority decision only: no sample, historical PIT vintages, exact delivery timestamps, complete methodology, delisted/adjusted contract mapping, correction policy, bulk feasibility or applicable license has been verified.
- Critical PIT distinction: the endpoint was announced in October 2026 and its 2015 history may be a retrospective backfill. Current same-evening delivery does not prove historical first-publication or availability in 2015. Preserve TradeEventTime, QuoteEventTime, VendorKnowledgeTime, retrieval time, methodology version and hashes. Until historical vintages/delivery logs are demonstrated, strict historical PIT fails.
- Midpoint volume must remain unclassified; customer gamma/vega and GEX are vendor-derived measures, not verified account identities or reported dealer inventories. Do not label any bucket smart money.
- OptionMetrics Signed Volume remains a parallel vendor/methodology robustness candidate; both IVolatility and OptionMetrics describe OPRA-sourced data, so agreement is not independent raw-market confirmation. Cboe Open-Close remains complementary capacity/open-close information.
- Current IVolatility public API page lists retail request limits and warns retail plans are not designed for full-market downloads; professional use requires a separate license. No account/trial, vendor contact, purchase or terms acceptance occurred. No alpha test or production change. F80 remains frozen.

- Repository preflight for Phase 137: latest run-specific Actions job inspected was Phase 136 run 42115525546; compile, six offline tests, sample retrieval and artifact upload passed, and job 127554052107 is completed. Current head 1dd8c69 has no combined statuses or PR-triggered workflow runs. The GitHub integration does not expose a repository-wide Actions run listing, so 42115525546 is the latest verifiable run, not an exhaustive run census. No workflow was dispatched/duplicated; Phase 136 is path-filtered away from the documentation-only Phase 137 update.


## 2026-11-05 — Phase 138 Cboe Open-Close intraday/PIT and OPRA cross-check

- Added [Phase 138 report](research/PHASE138_CBOE_OPEN_CLOSE_INTRADAY_PIT_AND_OPRA_CROSSCHECK_2026-11-05.md).
- Revalidated the current Cboe Open-Close product page: C1/C2/BZX/EDGX have EOD, 10-minute and 1-minute versions with different history starts. C1 EOD 2005-01-03, 10m 2011-01-03, 1m 2019-10-07; BZX/C2/EDGX EOD 2018-01-02 and both intraday intervals from 2019-03-01. C1 GTH begins 2023-12-11.
- Material correction: intraday files are cumulative day-to-date snapshots, not interval increments. Derive activity only by first differences on stable exchange/session/series/bucket keys. Do not sum snapshots or clip negative differences; later trade breaks/busts/cancellations can remove prior volume and late trades can appear in later snapshots.
- Intraday 1m/10m files omit price, total-volume and OI fields; capacity, buy/sell, open/close and size buckets remain. Files are described as delivered minutes after interval close, but exact historical first-receipt timestamps and immutable first-publication vintages are unverified. Historical archive may contain corrected final states; strict PIT remains blocked until vintage semantics are proved.
- Capacity labels (Firm, Broker/Dealer, Market Maker, Customer, Professional Customer) are trade-origin/account-capacity categories, not beneficial-owner identities or proof of informed trading. Keep customer/pro-customer size buckets separate. Do not equate buy/sell with NBBO aggressor side.
- EOD preliminary/final OI and total-industry-volume differ; final OI is OCC-sourced per the specification, and documented historical conventions include C1/C2 one-day OI shifts, C2 doubled total-industry volume, C1 total-exchange-volume formula changes and series-type changes. Keep versioned and quarantine affected fields until normalized.
- Databento OPRA cross-check: 20 venues (as of Sep 2026), schemas from 2013-04-01, but pre-2023-03-28 data are subsampled, lack TCBBO/CMBP-1/CBBO-1s, have `F_BAD_TS_RECV` and only minute BBO. Do not sign pre-boundary trades using CBBO-1m. TCBBO historical event coverage starts 2023-03-28, but the schema was introduced in 2025: historical/staging availability May 21 and production migration May 27. Strict TCBBO PIT is no earlier than the 2025-05-27 production cutover (subject to delivery logs); 2023-03-28 through 2025-05-26 is retrospective backfill only.
- Decision: promote Cboe Open-Close to the top-tier conditional participant-capacity/open/close candidate; Databento OPRA is the broad independent trade/NBBO reconstruction candidate with strict TCBBO PIT no earlier than 2025-05-27; earlier TCBBO event history is retrospective. IVolatility's 2015 signed-flow backfill remains non-PIT until historical knowledge-time/vintages are demonstrated. No return test or purchase.
- Superseding repository preflight at 2026-11-05 23:07 UTC: branch head `8cb00f306b67a728161958628eabf82346e8060d`; latest 30 Actions runs inspected, zero in-progress and zero queued; latest run remains Phase 136 [42115525546](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42115525546), job [127554052107](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42115525546); artifact [13455975956](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42115525546/artifacts/13455975956). Phase 129 [42081987897](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42081987897) is cancelled with no artifact; do not rerun unchanged.
- PR [#13](https://github.com/jafelix81/NuevaEstrategia/pull/13) is open, unmerged, mergeable/clean, 252 commits ahead and 1 behind main. No workflow was dispatched. F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen.

- **Phase 138 PIT correction:** Databento TCBBO has historical event coverage from 2023-03-28, but the TCBBO/CMBP-1 schemas were introduced in May 2025 (historical/staging from 2025-05-21; production migration 2025-05-27). Do not treat the 2023-03-28–2025-05-26 TCBBO backfill as contemporaneously available. Strict live TCBBO PIT begins no earlier than 2025-05-27, subject to actual delivery logs. The original 2023 T+1 statement applies to then-existing OPRA schemas, not this later TCBBO schema.

- Final Phase 138 documentation verification: branch head `f6cf1b206064eb22f039f4c91913023a6381e87c`; PR #13 remains open/unmerged, GitHub mergeable=true/clean, 257 commits ahead and 1 behind main; post-commit Actions queries show zero in-progress and zero queued runs. No workflow started.

- **Phase 138 OPRA semantics correction:** current Databento docs list 20 venues (as of Sep 2026), not the older 18-venue count. OPRA does not disseminate aggressor side; trade `side` is always N. TCBBO supplies NBBO at trade time, so aggressor direction must be inferred from price versus bid/ask and midpoint prints remain ambiguous. Strict live TCBBO PIT from 2025-05-27 to 2026-11-05 is only about 18 months—use prospectively/for vendor-methodology cross-check, not as a stand-alone multi-regime OOS sample.


## 2026-11-05 — Phase 139 Cboe Open-Close snapshot-state / schema-cutover audit

- Added `research/PHASE139_CBOE_OPENCLOSE_SNAPSHOT_STATE_AND_NOV08_SCHEMA_CUTOVER_2026-11-05.md`, a pure PIT-safe snapshot comparator, 22 synthetic regression tests and a dedicated offline Actions workflow.
- Rechecked Actions before work: 759 total runs; latest 30 inspected; zero queued/in progress. Latest run Phase 136 [42115525546](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42115525546) succeeded; job 127554052107 passed all steps; artifact [13455975956](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42115525546/artifacts/13455975956). Phase 129 remains cancelled/no artifact; do not rerun unchanged.
- Current branch pre-write head was `3ee949cde31d2437e74e0d3cfd36e843178b3859`; PR #13 was open/unmerged/clean, 261 ahead and 1 behind main.
- Cboe's current product page announces 2026-11-08 intraday schema/behavior changes: 1m v1.8 lowercases columns, adds `trading_dt`/`trading_segment`, and removes later-busted/cancelled and indicative/unsettled trades from subsequent snapshots; 10m v1.7 changes timestamp format, adds those date/segment fields, corrects a column typo, removes indicative/unsettled trades, changes final-file times and customer compression. Do not difference across schema versions/cutover.
- C1 `trading_segment` is 1 or 2 (not an RTH/GTH label); it is null for C2/BZX/EDGX. Preserve market_date separately from trading_dt because C1 GTH can span calendar dates/segments.
- Cboe product page says BZX/C2/EDGX intraday history starts 2019-03-01, while FAQ says March 2020 for interval Open-Close. Use 2020-03-01 as conservative multi-venue start until resolved.
- Critical interpretation: cumulative first differences are changes in the published aggregate since the prior received snapshot, not necessarily clock-interval trade volume. Late processing can add older trades; subsequent breaks/busts/cancellations can subtract prior volume. Preserve signed corrections and use the label reported_increment, never backdate or clip.
- Validator compares only common series/metric keys; new/removed series are not zero-filled; missing metrics are counted; same-cutoff changed hashes are revisions; archive backfills cannot pass the live-capture PIT-pair gate. 23/23 synthetic tests passed locally. This is not a Cboe sample-data audit and does not establish alpha readiness.
- Historical first-publication vintages, actual symbol/day coverage, inactive/delisted underlying identity, contract deliverables/multipliers and licensing remain open. No paid data, vendor contact, account/trial, return test or production change. `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen.
