# Smart Money Research — Current State

**Updated:** 2026-11-09  
**Active PR branch:** `phase231-cboe-option-quotes-full-row-reparse` (stacked on `phase99-broad-pit-universe-charter`)  
**Frozen production baseline:** \`F80_TOP20_PARTIAL50_BASELINE_C20\` — unchanged

## Latest material updates

### Phase 231 — Cboe Option Quotes full-row reparse
- Public sample hash pinned and reverified: \`7645a6cc94f1a984e98264a4b494f748e373c30ecde85de25ceadb83a5c56782\`.
- 115,617 populated row instances across five data members.
- 3,304 ambiguous expiration rows quarantined; no locale guessing.
- 112,313 unambiguous rows passed the full row-level contract/numeric/duplicate/OI checks.
- 0 invalid quote timestamps, 0 numeric errors, 0 duplicate contract/interval keys, 0 inconsistent start-of-day OI contract-days, 0 bid-above-ask rows.
- Independent Phase 175 all-row date diagnostics reconciled on all five members.
- Latest code-validation run 42719093680 (code commit a277581f8cf2d7caed4c83da9cfa9b7d8cc2870b) succeeded; 9/9 regression tests; 115,617 populated rows inspected, 112,313 unambiguous rows accepted and 3,304 ambiguous-expiration rows quarantined; artifact 13718924050 (2,422 bytes).
- Sample remains too narrow (two quote dates and only one or two underlyings per file) for historical coverage. Source is not PIT- or alpha-admitted.

### Phase 232 — Cboe Option Sentiment feasibility
- Public spec v1.4 (05/25) documents 80 daily fields and a historical start of January 2012.
- Rich candidate fields: directional net option delta and premium/volume, OI, customer/firm/market-maker clearing categories, size/DTX buckets, IV/skew/borrow, and exchange volumes.
- Cboe documents preliminary/complete subscription delivery targets, but historical first-receipt timestamps and immutable correction vintages are not established.
- Universe is documented broadly for U.S. stock, ETF, and index options disseminated over OPRA; delisted-symbol continuity and daily historical symbol coverage remain unverified.
- No raw sample or paid history obtained. Candidate only; strict PIT and alpha gates remain closed.
- 10/10 local documentation-audit tests passed. No hosted CI was run for this static feasibility audit.

### Phase 233 — Cboe Option Sentiment field dimensionality and directional semantics
- Audited the official DataShop specification v1.4 (05/25), its footnotes, and Cboe's early-exercise research.
- Found three inconsistent footnote references: net_option_delta, calls_sold, and puts_sold point to note 2, although note 2 is the blank-field list and note 3 contains the midpoint direction rule.
- The 80-field schema does not expose direction by trade size, OCC participant category, DTX, or moneyness. The proposed large-size-directional and customer-net-directional hypotheses are therefore unimplementable with this file and are killed as measurement designs, not empirically falsified.
- Non-ITM put/call volume is retained only as a non-directional activity/composition control. Customer/firm/market-maker totals are context only; they do not identify beneficial owners.
- net_option_delta units, sign, multiplier/deliverable treatment, and complete field-specific rules are unspecified. Its feature definition and normalization by underlying volume are suspended pending written provider clarification.
- Historical orders are delivered at order-processing completion; original historical first-receipt and immutable correction vintages remain unverified. Strict PIT remains blocked.
- 12/12 local regression tests passed. No hosted Phase 233 workflow was run; files use skip-ci commits.
- [Phase 233 report](PHASE233_CBOE_OPTION_SENTIMENT_FIELD_DIMENSION_AND_DIRECTIONAL_SEMANTICS_AUDIT_2026-11-09.md)

### Phase 234 — CFTC Bank Participation Report (BPR) feasibility
- Identified a separate monthly CFTC source with aggregate gross long/short positions of U.S. and Non-U.S. commercial banks; current report includes E-mini S&P 500, Nasdaq Mini, Russell E-mini, and DJIA $5 futures.
- CFTC public archive retains only 25 months. BPR is not a stock-level dataset and is not all institutional investors; bank labels derive from Form 40 and staff approval. The separate options report is gross and not delta-adjusted.
- November 2026 report date is 2026-11-03 and scheduled publication date 2026-11-06. Exact first public receipt time is not established; 2025 shutdown/catch-up history proves the nominal schedule can fail.
- Rejected for standalone historical OOS/stock selection; retained only as a conditional prospective broad-market regime candidate. No returns tested and no alpha admission.
- Added append-only raw-page/hash/receipt capture script and weekday 20:35 UTC workflow. Scheduled receipts are pipeline-availability candidates only after 15:30 ET; manual dispatches are non-PIT. Revisions append by hash; no raw snapshot has yet been captured.
- 26/26 local tests passed across BPR semantics, reconciliation, unknown-vs-zero handling, capture idempotence, revisions, and delayed weekday receipts. No hosted workflow was run; the schedule activates only after the research branch reaches the default branch.
- [Phase 234 report](PHASE234_CFTC_BANK_PARTICIPATION_REPORT_EQUITY_INDEX_FEASIBILITY_AUDIT_2026-11-09.md)

### Phase 235 — CFTC BPR PIT bootstrap and missingness hardening
- Separated the first scheduled capture from a new release event: it is a baseline state usable only after its actual pipeline receipt, not an event signal and never backdated to report date. Subsequent newly indexed URLs and observed revisions can qualify from their own scheduled receipt.
- The capture protocol now stores append-only raw index HTML and link-set snapshots, selects the latest report by month encoded in its URL rather than page order, validates URL month against report date, and captures multiple newly indexed catch-up reports. Manual dispatches do not advance the scheduled baseline.
- Legacy protocol-v1 metadata cannot suppress the v2 baseline. Older non-latest report pages are not continuously polled for revisions; this remains a limitation.
- BPR blanks in bank counts, positions, and percentages remain UNKNOWN; explicit numeric zero remains zero. Combined net requires observed total long/short or complete category rows; positive market OI is mandatory.
- 36/36 local regression tests passed (13 Phase 234 capture + 13 Phase 234 parser/semantics + 10 Phase 235). No hosted CI was run and no BPR capture has occurred.
- [Phase 235 report](PHASE235_CFTC_BPR_PIT_BOOTSTRAP_AND_MISSINGNESS_AUDIT_2026-11-09.md)

### Phase 236 — Cboe Trade-by-Trade (TBT) execution-detail feasibility
- Identified a materially richer C1 options execution dataset than Option Sentiment/Open-Close for side × open/close × capacity × size × trade-type research, with NBBO/local BBO and simple/complex execution IDs.
- The current archive advertises history from 2019-10-07, but the first located public launch evidence is Cboe Traders Weekly 2026-02-20. Pre-launch rows are retrospective backfill, not strict PIT. The post-launch window is under nine months and actual per-file first-receipt logs remain unavailable.
- C1 only. C2/BZX expansion proposals were noticed 2026-11-06; EDGX is still described as planned. Do not infer all-OPRA coverage.
- T+1 delivery is typically 00:30–01:30 ET; use TRADING_DT around GTH midnight. SIDE is Buy/Sell, not automatically aggressor direction; CAPACITY is not beneficial-owner identity; OPEN_CLOSE is not OI. EXEC_ID/COMPLEX_EXEC_ID row grain and paired-side/complex-leg behavior require sample validation.
- Last located C1 fee schedule (2026-04-21): $12,000/month subscription and $8,000/month historical ad hoc; eligible one-month trial. No sample bytes obtained, no trial requested, no vendor contact or purchase.
- 15/15 local guardrail tests passed. No hosted CI, return test, PIT admission or alpha claim.
- Decision: high-priority conditional C1 execution-measurement candidate, ahead of Option Sentiment for crossed directional/opening-flow hypotheses; not strict-PIT or alpha admitted.
- [Phase 236 report](PHASE236_CBOE_TBT_EXECUTION_DETAIL_FEASIBILITY_AND_PIT_AUDIT_2026-11-09.md)

## Source decisions

| Source | Current decision | Main blocker |
|---|---|---|
| FINRA 20C / short flow | Not promoted | Historical coverage and incremental value not established |
| CFTC BPR | Conditional prospective market-regime candidate only | 25-month rolling archive, monthly frequency, no historical first-receipt vintages, no stock-level coverage; first capture is baseline state-only, later new URLs/revisions require scheduled receipt |
| CFTC TFF | Conditional prospective broad-market regime candidate only | Historical release dates available only for the latest 13 months; category labels are not trader identities; no stock-level coverage; no raw capture yet |
| SEC FTD | Context-only; not historical PIT or alpha admitted | ChartExchange history contains later bulk backfills; first/latest receipt semantics, badge algorithm, immutable value vintages and effective-dated identity are unverified |
| Form 4 | Standalone implementation discarded | Must distinguish transaction semantics and filing availability |
| Form 144 | Conditional event candidate; class-share path feasible via raw inline XBRL, not admitted | Exact class mapping, 289-issuer coverage, PIT float/ADV and security identity |
| SEC 13D/G | Separate 13D and 13G research tracks | Reporting-person economic identity and amendment chains |
| N-PORT | Conditional short-side hypothesis | Original XML retrieval blocked by missing authorized \`SEC_CONTACT_EMAIL\` |
| Cboe Option Quotes | Sample parser gate passes on unambiguous rows only | PIT receipt/vintage, broad history/universe, licensing |
| Cboe All Access API Time & Sales | High-priority conditional sample-acquisition candidate; historical option trades advertised from 2003; no PIT/alpha admission | Trial historical OPRA-field access, venue coverage, correction vintages, first receipt, delisted/adjusted-contract identity and licensing unverified; 14-day trial requires card authorization |
| Cboe TBT | High-priority conditional C1 execution-measurement candidate; no PIT/alpha admission | first-receipt/correction vintages, sample row-grain/ID pairing, C1-vs-OPRA coverage, inactive symbols, licensing and cost |
| Cboe Option Sentiment | Conditional lower-priority candidate; no PIT/alpha admission | net_option_delta units/sign/multiplier and field semantics; no directional size/participant cross-tabs; historical receipts/vintages, delisted coverage, sample, price/license |
| SEC MIDAS | Microstructure context only | Historical publication vintages and PIT identity |
| Cboe Open-Close | Not admitted to daily PIT | First-receipt/vintage and venue coverage controls |

## Non-negotiable controls
- No forced CAGR target; optimize return relative to risk and robustness.
- No minimum or maximum holding period.
- \`F80_TOP20_PARTIAL50_BASELINE_C20\` remains frozen.
- \`CONSUMED_NOT_PRISTINE\` is not used as a final holdout.
- No signal promotion without chronological OOS, identical exposure/costs, bootstrap/time-block inference, and LOO diagnostics.
- Explicitly control for prior returns to distinguish predictive flow from return-chasing.
- Missing data remain UNKNOWN, not zero.
- No purchases, production changes, or universe changes without explicit gates.

## Human/technical blockers
1. Set an authorized \`SEC_CONTACT_EMAIL\` in GitHub Actions to enable SEC N-PORT original-document retrieval.
2. Before any Cboe paid historical order, obtain written answers on first-receipt logs, correction/revision policy, historical delisted coverage, licensing, and price. No order has been placed.
3. Cboe All Access trial: 14 days and 500 points/day; card authorization is required although Cboe says the trial is not charged. Trial SIP access is excluded and historical OPRA-price access is unverified. No signup or card authorization without explicit approval.

## Next research steps
1. After the stacked PR14/PR13 chain reaches main, the existing Phase 234 workflow captures both BPR and TFF. Each stream's first scheduled receipt is baseline-only; later new reports are usable only from their own pipeline observation timestamp.
2. Keep Phase 231 parser and artifact metadata as the accepted sample diagnostic; do not generalize it to the full product.
3. Prioritize a lawful Cboe TBT sample or eligible one-month trial only if available without purchase; validate row grain, paired sides, EXEC_ID/COMPLEX_EXEC_ID, trade-type coverage, timestamp/GTH rules, C1 share of OPRA and correction vintages before feature work.\n4. Build a raw inline-XBRL class-share pilot for Form 144 issuers; measure exact class-member mapping and coverage before any supply-pressure feature.
4. Do not purchase TBT at the located $12,000/month subscription or $8,000/month historical rate without explicit approval; confirm internal-use/derived-feature rights and actual first-receipt logs.
5. Keep Option Sentiment lower priority: obtain written clarification of net_option_delta units/sign/multiplier, footnote mappings and cancellation scope; do not normalize it or test alpha until its measurement and PIT gates pass.
6. Compare incremental information to frozen LTM/F80 under identical exposure and costs; do not use the consumed holdout.


### Phase 237 — Form 144 class-specific shares-outstanding denominator feasibility
- SEC Company Facts aggregates non-custom-taxonomy facts applying to the entire filing entity; the July 2025 EDGAR XBRL Guide requires multi-class common shares to be reported in separate class-dimensioned instant contexts. Company Facts alone is therefore insufficient for multi-class class-specific denominators; raw as-filed inline XBRL is required.
- Noodles & Company 2015 10-Q/A demonstrates that an amendment can correct a class share count; preserve each accession as a separate PIT vintage. Flowco 2026 cover page demonstrates separate Class A/B counts. Phase 223's Expedia cross-check remains the denominator-quality control.
- Added fail-closed normalized-fact resolver. It requires exact class-member mapping, instant shares facts, filed-date eligibility, immutable amendment vintages, and blocks stale fallback after a newer invalid fact. Prototype currently admits only the documented US-GAAP class-axis QNames; other standard-taxonomy namespaces remain quarantined. Public float (market value) and ADV remain separate from shares outstanding.
- 23/23 local standard-library fixture tests passed; same-day acceptance ties and cross-class instant-date consistency are fail-closed. This is not a raw inline-XBRL parser test, not a 289-issuer coverage estimate, and not hosted CI.
- **Decision:** class-specific shares-outstanding retrieval is feasible in principle via raw inline XBRL; Company Facts-only multi-class path rejected. Form 144 denominator, PIT float/ADV, security identity and alpha remain NOT ADMITTED. No SEC API request, raw filing download, return test, holdout use, purchase or production change.
- [Phase 237 report](PHASE237_FORM144_XBRL_CLASS_SHARES_OUTSTANDING_PIT_DENOMINATOR_FEASIBILITY_AUDIT_2026-11-09.md) · [result](phase237_form144_xbrl_class_shares_pit_audit_result.json)



### Phase 238 — Form 144 / Form 4 reverse-linkage selection audit
- Reversed the Phase 208–210 linkage perspective using the immutable Phase 69 Form 144 panel and Phase 39 2026 Q3 Form 4 bulk snapshot.
- In the 289-issuer panel, 1,665 eligible single-owner Form 4 code-S disposition blocks were found; 570 (34.23%) linked one-to-one to eligible Form 144 notices under exact-first matching (521 exact date/share, 49 fallback 0–2 day). The 1,095 unmatched blocks are not classified as missing or noncompliant notices.
- The raw Form 4 AFF10B5ONE plan-flag linkage gap (29.17% vs 47.99%) is not robust after issuer and issuer × reporting-owner-role conditional randomization: p=0.557 and p=0.960, respectively, with 20,000 permutations. Do not use the plan flag alone as a Form 144 linkage predictor.
- Form 144 remains a threshold-censored Rule 144 notice source, not a census of insider sales. Form 4 code S includes open-market or private sales. This is one quarter, current-universe selected coverage, and not strict PIT.
- Added immutable-input auditor, five offline regression tests, and JSON result. Local tests: 5/5 passed; 20,000-permutation CLI reproduction completed. No hosted CI run, no returns, no alpha, no holdout, no production/universe change.
- **Decision:** no Form 144 feature admission and no alpha test. Continue only after full-panel EDGAR acceptance vintages, effective-dated issuer/class identity, and independent PIT shares/float/ADV are admitted. F80 remains frozen.
- [Phase 238 report](PHASE238_FORM144_FORM4_REVERSE_LINKAGE_SELECTION_AUDIT_2026-11-09.md) · [auditor](phase238_form144_form4_selection_coverage_audit.py) · [tests](test_phase238_form144_form4_selection_coverage_audit.py) · [result](phase238_form144_form4_selection_coverage_audit_result.json)


### Phase 239 — CFTC TFF prospective capture and publication-regime audit
- The current CFTC COT page links separate 87-field TFF files: futures-only (FinFutWk.txt) and futures-and-options combined (FinComWk.txt). The current report/as-of date is 2026-11-03; the 2026 release schedule lists 2026-11-06 as the scheduled release.
- TFF historical positions begin 2006-06-13, but the CFTC FAQ says only the most recent 13 months of release dates are available. Report date is not publication date; long-history strict PIT is therefore not admitted.
- TFF categories are Dealer/Intermediary, Asset Manager/Institutional, Leveraged Funds and Other Reportables. They are not named beneficial owners or verified informed traders; classification is based on predominant business purpose self-reported on Form 40, and the CFTC says it does not know the specific reason for positions. Contract markets can disappear below the 20-trader reporting threshold; absence is not zero.
- Four official current-file sample rows (S&P 500 futures-only/combined and Canadian Dollar futures-only/combined) were transcribed into fixtures. The 87-field parser passed all four; this is row-level schema validation, not a full-file download.
- The S&P 500 2026-11-03 sample shows a descriptive divergence: futures-only Asset Manager net +930,713 (+46.22% OI), Leveraged Funds net -366,870 (-18.22% OI), Dealer net -693,326 (-34.43% OI). The combined stream has separate OI and different ratios. This is one report date, not predictive evidence.
- CFTC announced a plan on 2026-10-27 to publish COT twice weekly by end-2026. The current official schedule page still shows the weekly Friday schedule as of 2026-11-09, and the announcement does not explicitly confirm TFF financial-contract scope. The capture therefore polls every weekday without assuming TFF has changed cadence.
- Extended the existing Phase 234 BPR workflow; no duplicate CFTC workflow was created. The shared 20:35 UTC weekday schedule, concurrency lock and append-only commit are retained. TFF raw files are gzip-preserved with hashes; the HTTP Date header is recorded but never used as availability.
- First scheduled capture per stream is INITIAL_BASELINE_STATE_ONLY. Later new report dates are usable only from pipeline observation; same-date revisions are state-only; manual dispatch and rollback/backfill are non-PIT. Earliest decision is the next regular XNYS session after observation, with EOD execution at that session's close.
- 29/29 local tests passed, including four official sample rows, 87-field schema, stream/date/duplicate/numeric gates, missing-versus-zero counts, EST/EDT timing, baseline/revision/manual classification, gzip round-trip and index deduplication. No hosted Phase 239 CI run is claimed.
- No live capture was executed and no raw TFF snapshot has been persisted. The workflow remains inactive until the stacked PR chain reaches the default branch. No return test, alpha admission, holdout use, data purchase, production change or universe change.
- [Phase 239 report](PHASE239_CFTC_TFF_PROSPECTIVE_CAPTURE_AND_PUBLICATION_REGIME_AUDIT_2026-11-09.md) · [capture code](phase239_cftc_tff_prospective_capture.py) · [tests](test_phase239_cftc_tff_prospective_capture.py) · [result](phase239_cftc_tff_prospective_capture_result.json)


### Phase 241 — FINRA API versioning is not historical row-vintage recovery
- FINRA's Query API Data Versioning (announced 2025-10-16) versions field structure/data representation for backward compatibility; it is not an as-of query or archive of prior row values. The `weeklySummaryHistoric` endpoint provides older reporting periods, not earlier published payload vintages.
- Phase 117's FINRA ATS/OTC revision problem therefore remains unresolved: current final values cannot be backdated to initial publication, and future-known revision status cannot be used as a filter. Keep FINRA ATS/OTC conditional/context-only; no new return test is authorized.
- Prospective immutable response capture can preserve future states only; it cannot reconstruct missing historical values. See [Phase 241](PHASE241_FINRA_API_SCHEMA_VERSIONING_VS_DATA_VINTAGES_2026-11-09.md).


### Phase 242 — CFTC BPR/TFF capture-vintage completeness and event-promotion hardening
- Re-audit after Phase 240 found two residual PIT risks: BPR scheduled capture polled only the latest report plus newly indexed URLs, so corrections to older retained reports could be missed; and a report first seen in a manual capture could later be promoted to a new event on its first scheduled receipt. TFF had the analogous manual-observation promotion path after an earlier scheduled baseline.
- **BPR protocol v3:** the first scheduled run now bootstraps every currently indexed Futures report as baseline state only; every later scheduled run re-fetches every report URL still present in the CFTC's rolling archive (about 25 months), so older-page revisions are appended as state-only updates. A newly indexed, never-before-observed report can be event-eligible only from its scheduled pipeline receipt. Any previously observed manual/prior-protocol version is state-only and cannot be promoted into a new event.
- **TFF protocol v2:** report dates already observed in the current protocol's metadata, including manual observations, cannot later be promoted to a new scheduled event. The first scheduled v2 observation remains baseline-only; revisions and previously observed dates are state updates, not events.
- Reused the existing Phase 240 regression workflow; no duplicate CFTC workflow was created. Hosted run [42669436293](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42669436293) passed **47/47 tests**: BPR 16/16 and TFF 31/31, including non-latest BPR revision polling, all-retained-report bootstrap, manual-to-scheduled non-promotion, TFF manual-to-scheduled non-promotion, and prior rollback/revision guards.
- This is a capture-integrity improvement, **not** a predictive result. No CFTC raw capture or SEC request was executed; no historical PIT admission, return test, bootstrap/LOO, OOS, holdout use, data purchase, vendor contact, production change, or universe change. The shared capture workflow remains inactive on `main` until the stacked PR chain is merged.
- **Decision:** retain BPR/TFF as conditional prospective broad-market regime candidates only. First-publication timestamps remain unverified; the pipeline receipt is the conservative known-by time. No stock-level Smart Money signal is admitted. F80 remains frozen.
- [Phase 242 report](PHASE242_CFTC_BPR_TFF_CAPTURE_VINTAGE_COMPLETENESS_AND_EVENT_PROMOTION_HARDENING_2026-11-09.md) · [result](phase242_cftc_capture_vintage_hardening_result.json)


### Phase 243 — CFTC raw/metadata partial-commit PIT guard
- Found a failure path created by the existing capture workflow's `continue-on-error: true` source steps and later shared commit step: a source can write its raw file, fail before metadata is written, and still have that raw-only file committed. On the next scheduled run, BPR/TFF previously could treat the already-observed report as a new first event because no receipt metadata existed.
- BPR now verifies any pre-existing raw HTML file against the full SHA-256; a raw-only orphan is treated as previously observed and state-only, never promoted to a new event. If receipt metadata exists but its matching raw file is missing, the fetched bytes repair the raw archive while preserving the original receipt.
- TFF now scans metadata across protocol versions for prior report-date observations, verifies pre-existing gzip bytes against the full SHA-256, quarantines raw-only orphans as state-only, and repairs missing raw files when matching receipt metadata exists. Corrupt or mismatched raw files fail closed.
- Added three BPR and three TFF regression tests: orphan raw state-only, corrupt orphan hash rejection, and missing-raw repair. Hosted Phase 240 regression [42676258774](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42676258774), job 129358311974, confirms **19/19 BPR + 34/34 TFF = 53/53 passed** on commit `d2d86a0e187cd8979979c19450d53fc10fd4a250`.
- Existing Phase 240 workflow was reused; no duplicate workflow was created. The code/test commits are BPR code `9aa8c01f7012e9ad58bd7b9379e898850de2d4e1`, BPR tests `1e2b6ad2e9fe2f43d8dc9b5cbd370c2e17dc0d0e`, TFF code `a019b923d62c46cf54d4d4d849ce9defdc25e01d`, and TFF tests `d2d86a0e187cd8979979c19450d53fc10fd4a250`.
- Hosted regression validation is **PASSED**: run [42676258774](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42676258774) completed successfully; logs confirm 19/19 BPR and 34/34 TFF tests. This validates the code path, not live capture, historical first-publication time or alpha.
- No live CFTC capture, historical PIT admission, returns, alpha, bootstrap/LOO, chronological OOS, or holdout use. No vendor contact/purchase, production/universe change, or baseline change. `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen.

### Latest verified Actions evidence — 2026-11-09
- Phase 240 CFTC regression: [run 42669436293](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42669436293), job 129341718918, completed successfully; logs confirm BPR 16/16 and TFF 31/31 (47/47). No artifact was emitted.
- Phase 231 Cboe reparse: [run 42669444831](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42669444831), job 129341962705, completed successfully with 9/9 tests; artifact [13698615572](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42669444831/artifacts/13698615572), ZIP digest `45e571790d9f6ae428ef44f36fc59f47f9f5fc4465000c463e6f1fc3b2503069`.
- Phase 243 hosted regression is confirmed by run [42676258774](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42676258774): 53/53 tests passed. Phase 231 current-head reparse [42676263668](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42676263668) passed 9/9 tests and emitted metadata-only artifact [13701350271](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42676263668/artifacts/13701350271), 2,422 bytes, SHA-256 `b40b613aa0efb5b0fcf1f17451d19e457e7ad9426eb5a499193605c9913a82b9`.
- Branch inventory: 131. PR #13 and PR #14 remain open and unmerged; PR #14 is stacked on PR #13. No merge was performed. The final documentation-only commit was marked skip-CI, so mergeability was not recalculated for that head.


## Phase 244 — SEC FTD external release/receipt timeline audit
- New source evidence: ChartExchange's public FTD Release History page separates expected date, SEC file modification date and the date its importer retrieved each archive. The page summary reports 28.4% early, 50.8% on time and 20.7% late; examples include October 2025 first-half retrieval 13 days after the expected date and October 2023 first-half retrieval 21 days after the expected date.
- The visible timeline shows monthly first-/second-half entries from October 2021 through September 2026, plus October 2026 first-half. Older observations include bulk/backfill retrieval dates (e.g., August/September 2021 records on 2021-10-08 and July 2009 records on 2022-05-03), not contemporaneous historical receipts.
- This is a potentially useful conservative external known-by-date proxy, but not a strict PIT ledger: date-only resolution, first-versus-latest retrieval semantics unspecified, no immutable ZIP bytes/hash linked to each receipt, and no historical correction-vintage chain. SEC itself says nominal month-end/15th release dates are not guaranteed.
- **Decision:** do not use current FTD values in historical PIT/alpha tests. Retain the external retrieval date only as a conditional proxy pending receipt semantics and immutable value vintages. Prior Phase 102/106 security-identity and 2008 threshold gates remain open.
- [Phase 244 report](PHASE244_SEC_FTD_EXTERNAL_RELEASE_RECEIPT_TIMELINE_AUDIT_2026-11-09.md) · [result](phase244_sec_ftd_external_release_receipt_timeline_result.json)
- No returns, alpha, bootstrap/LOO, OOS or holdout test; no vendor contact/purchase; no production or universe change.


## Phase 245 — SEC FTD external timeline backfill and status-label correction
- Corrected Phase 244's incomplete description of the page span: the current ChartExchange timeline includes records as far back as July 2009, with examples from 2010–2013, 2016, and 2026.
- Older rows are visibly batch-backfilled: 2016-10 first-half shows File Time 2016-10-28 but Retrieved 2021-10-08; 2009-07 second-half shows File Time 2009-08-04 but Retrieved 2022-05-03. These are not contemporaneous historical receipts.
- The row-level “early/on time/late” badge is not reconciled to one documented date field: the 2026-10 row's “3 days early” matches Retrieved, while 2016-10 and 2009-07 labels match File Time. The page's 28.4/50.8/20.7 percentages therefore cannot be treated as a calibrated first-publication delay distribution.
- **Decision:** downgrade ChartExchange FTD timeline to contextual release/metadata evidence only. No historical PIT or alpha admission.
- [Phase 245 report](PHASE245_SEC_FTD_EXTERNAL_TIMELINE_BACKFILL_AND_LABEL_SEMANTICS_CORRECTION_2026-11-09.md) · [result](phase245_sec_ftd_external_timeline_backfill_result.json)


### Phase 246 — Cboe All Access API option time-and-sales feasibility
- Identified an additional trade-level options candidate with vendor-advertised historical data from 2003. The documented API exposes trade price/size, exchange and condition IDs, sequence fields, cancellation flags, NBBO-relative trade-price classification and an optional Greeks endpoint.
- Cboe publishes a 14-day trial with 500 points/day; a historical request costs 15 points, allowing at most 33 full requests/day or 462 over the trial before pagination. Card authorization is required, although the product page says no charge. Trial SIP access is excluded; historical OPRA price-field availability during the trial is not confirmed.
- Paid reference tiers are $2,499/month for 1.25m points and $4,599/month for 4m points. No account was created, no card authorized, no terms accepted, no API request or purchase made.
- option_trade_at is only a price-relative-to-market proxy: ask-side classes may indicate buy-side pressure, bid-side classes sell-side pressure; midpoint/crossed/no-market are unknown. It does not identify participant capacity, beneficial owner, or open/close.
- cancel_flag 0/1/2, sequence linkage, EST/DST timestamp semantics, NBBO freshness, exchange/OPRA breadth, inactive/delisted coverage, adjusted contracts, historical correction vintages and first-receipt timing remain unverified.
- **Decision:** high-priority conditional sample-acquisition candidate because of the advertised long history and low-cost trial route; no PIT or alpha admission. Historical backfill cannot be treated as historically available data.
- Latest hosted Phase 246 validation: 7/7 tests in run 42719093681; artifact 13718859080 (1,909 bytes). No trial/account/card authorization or API query was made.
- [Phase 246 report](PHASE246_CBOE_ALL_ACCESS_OPTION_TRADE_FEASIBILITY_AND_TRIAL_GATE_2026-11-09.md) · [deterministic audit script](phase246_cboe_all_access_option_trade_feasibility.py)



## Phase 247 — SEC N-PORT flattened UNIT field defect and PIT design audit
- Audited the existing separate Phase 27K–27O N-PORT work rather than restarting source feasibility.
- Confirmed a blocking schema mismatch in the legacy Phase 27O workflow: its TSV reader accesses UNITS, while the SEC flattened FUND_REPORTED_HOLDING table defines UNIT (singular) plus BALANCE. The raw XML tag is <units>, which is not the flattened TSV column name.
- Consequence: the legacy NS share-balance test never succeeds on the documented flat-file schema; its share accumulator remains zero, and the ranker requiring positive prior/current shares cannot form valid candidates. Phase 27O output is quarantined; this is a code defect, not evidence for or against N-PORT alpha. Its workflow output was not independently verified here.
- Added a fail-closed parser contract and 11 offline regression tests; hosted GitHub Actions validation passed 11/11 in latest run 42719093659 (artifact 13719602027). The helper accepts only UNIT=NS, ASSET_CAT=EC, explicit PAYOFF_PROFILE=LONG and finite positive BALANCE. It rejects XML-only UNITS, conflicting aliases, non-share units, non-equity, short/unknown payoff and invalid balances.
- Official SEC data-set coverage is October 2019–September 2026 (28 quarterly archives); archives are quarterly compiled, contain publicly disseminated filings and include amendments. They are not a live PIT feed and omit full acceptance metadata.
- Current public regime remains quarterly filing with only each fund's third fiscal-quarter month public upon filing; the 2024 monthly/publication amendments were delayed to 2027/2028.
- Next N-PORT design must use accession-level original/amendment vintages, actual EDGAR public dissemination, asynchronous per-series reporting cadence, effective-dated CUSIP/ISIN mapping, and separate quantity from market-value changes. Amendments are state corrections, not new trades.
- No full archive audit, 335-name effective-dated coverage census, return test, alpha, bootstrap/LOO, OOS or holdout use. F80 remains frozen; production and universe unchanged.
- [Phase 247 report](PHASE247_NPORT_FLATTENED_UNIT_FIELD_AND_PIT_DESIGN_AUDIT_2026-11-09.md) · [schema contract](phase247_sec_nport_unit_field_contract.py) · [tests](test_phase247_sec_nport_unit_field_contract.py) · [result](phase247_nport_unit_field_contract_result.json)


## Phase 231 — latest Cboe full-row reparse confirmation
- Latest GitHub Actions run 42719093680 completed successfully; the full-row reparse and reconciliation finished.
- 115,617 populated rows were inspected; 112,313 rows passed the unambiguous contract and 3,304 rows with ambiguous expiration dates were quarantined. No ambiguous quote timestamps were reported.
- The clean unambiguous subset passed; the full sample gate remains false because the ambiguous rows are not silently accepted. No raw rows were persisted and no alpha test was run.
- Latest artifact 13718924050 (2,422 bytes); ambiguous expiration rows remain quarantined and no raw rows were persisted.


### Phase 248 — Cboe Open-Close EOD directional feature contract
- Reused the Phase 114 public 20% C1 EOD sample audit: 23,179 rows, 1,553 underlyings, 86 fields, and exact participant-volume reconciliation on all 23,179 rows.
- The reported C1 total_exchange_vol / total_industry_vol ratio on that one sample date is 36.8559%; this is a sample field ratio, not a validated market-share estimate or full OPRA coverage.
- Preregistered separate Customer and Pro-Customer opening call/put volume proxies. Calls use buy minus sell; puts use sell minus buy. These are unweighted contract proxies, not delta or beneficial-owner signals.
- Added fail-closed aggregation that rejects missing/negative/non-integer volume, duplicate option-series keys, mixed date/underlying/security types and unsupported index/warrant cohorts. Zero denominators remain undefined; missing values are not zero.
- Use only final EOD files. Preliminary/final revisions, actual first receipt, daily archive completeness and inactive/delisted coverage remain unverified. Historical backfill is not PIT.
- Primary homogeneous panel starts 2019-10-07 to avoid C1 volume/OI convention breaks; control the 2023-12-11 GTH start and exclude FLEX series type F (added 2024-10-16) from the primary cohort. Equity and ETF cohorts remain separate.
- The EOD file lacks Greeks/IV, beneficial-owner identity and complex-order linkage. No delta-weighted or institutional interpretation is admitted.
- 29 synthetic regression tests passed locally and in hosted run 42719093860; metadata-only artifact 13719158402 (1,460 bytes). The helper normalizes MM/DD/YYYY and ISO dates, rejects dates before 2019-10-07, excludes FLEX/unknown series types from the primary cohort, and rejects capacity volume exceeding total_exchange_vol. No raw historical sample was reprocessed in Phase 248, no returns were tested, and alpha/PIT gates remain closed.
- **Decision:** retain as a high-priority conditional options-flow measurement candidate; do not authorize returns until final-file receipt, historical archive coverage, effective-dated security identity and broad PIT universe coverage pass.
- [Phase 248 report](PHASE248_CBOE_OPENCLOSE_EOD_DIRECTIONAL_FEATURE_PREREGISTRATION_2026-11-09.md) · [helper](phase248_cboe_openclose_feature_contract.py) · [tests](test_phase248_cboe_openclose_feature_contract.py) · [result](phase248_cboe_openclose_feature_contract_result.json)


## Phase 249 — Cboe Open-Close EOD real-sample feature reprocessing
- Applied the Phase 248 preregistered capacity/side/open-close contract to the actual Cboe public C1 EOD sample in memory, rather than synthetic fixtures only.
- Independently reruns the Phase 168 archive/schema audit, requires the 86-field EOD contract, validates unique option-series keys and exact participant-volume reconciliation, separates Equity/ETF, excludes Index/Warrant, and removes FLEX rows without discarding standard/nonstandard rows for the same underlying.
- Builds fixed Customer and Pro-Customer opening features overall/by size bucket, closing controls, and Firm/Broker-Dealer opening controls. Output contains aggregate cross-sectional diagnostics only; no raw rows or underlying symbols are persisted.
- **Hosted real-sample result passed:** run [42726166910](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42726166910), job 129532318774, 11/11 tests; metadata-only artifact [13722241996](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42726166910/artifacts/13722241996), 1,918 bytes. The 2025-03-28 sample archive hash `445cd9d658dc06028c286e09d4ac4818bd5884d7da8addd7509f3a0fa4840552` and EOD member hash `1c960e9a7b8b25311d2c8f012c36ea2c43087fe756335e57ffc952699a393ff6` match Phase 114. Reprocessed 23,179 rows; 23,179/23,179 participant-volume reconciliations exact; 20,017 Equity/ETF rows after 69 FLEX exclusions; 1,543 underlying groups (1,255 Equity; 288 ETF); all 18,516 feature groups built with zero aggregation errors. Customer opening was active in 1,257 groups (639 positive/576 negative/328 zero; median imbalance +0.0400); Pro-Customer opening was active in 344 groups (170/172/1,201; median −0.007246). Pro-Customer 100–199 and >199 buckets were sparse (6 and 4 active groups). These are one-day 20% sample cross-sectional diagnostics, not returns or predictive evidence. The sample remains one date and 20%; historical daily coverage, first-receipt timestamps, inactive/delisted identity, PIT and predictive alpha remain unproven.
- No forward returns, bootstrap/LOO, chronological OOS or holdout test. `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen; no production, universe or capital change; no vendor trial/purchase/contact.
- [Phase 249 report](PHASE249_CBOE_OPENCLOSE_REAL_SAMPLE_FEATURE_REPROCESSING_2026-11-09.md) · [script](phase249_cboe_openclose_real_sample_reprocessing.py) · [tests](test_phase249_cboe_openclose_real_sample_reprocessing.py)


### Phase 249 hosted disposition — 2026-11-10 UTC
- [Run 42726166910](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42726166910) passed 11/11 tests and the real-sample measurement gate; artifact [13722241996](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42726166910/artifacts/13722241996).
- Reprocessed sample is exactly the Phase 114 public 20% C1 EOD sample (2025-03-28), confirmed by matching archive/member SHA-256. No raw rows or symbols were persisted.
- The run's one-date cross-section is a data-feasibility diagnostic only. Do not use the positive/negative group counts or median flow imbalance as return labels or alpha evidence.
- On the same commit, Phase 231, 246, 247 and 248 regression workflows also completed successfully: 9/9, 7/7, 11/11 and 29/29 tests, respectively. Phase 231 still quarantines 3,304 ambiguous-expiration rows; its unambiguous subset is 112,313/115,617 rows.
- No workflows remain active after this validation set. Branch inventory remains 131. PR #13 and #14 remain open and unmerged; PR #14 remains stacked on PR #13. No merge was performed.


## Phase 250 — Cboe C1 EOD historical convention-aware feature eligibility (2026-11-10)
- Official DataShop page lists C1 EOD history from 2005-01-03, but distinguishes the pre-2011 legacy schema from the post-migration format. The legacy spec states pre-migration through 2010-12-31 and post-migration from 2011-01-02; pre-2011 buckets are by original order size and the file has Customer/Firm-only categories.
- Corrected the Phase 248 2019-10-07 cutoff at the feature level: same-day participant directional imbalance (call buy−sell; put sell−buy; signed net/gross same-capacity volume) can be studied separately from 2011-01-02 through 2019-10-04 because it does not require C1 total volume, OI, previous OI or previous close.
- C1 total exchange volume used (B+S)/2 through 2019-10-04 and B+S thereafter; C1 OI/previous OI were shifted one day ahead through 2019-10-04. Therefore net-share-of-C1-volume and OI-based features remain blocked before 2019-10-07.
- Cboe maps legacy capacity code W to Pro-Customer prior to October 2019; participant-code regime is explicitly tagged. C1 GTH coverage begins 2023-12-11 and is tagged separately.
- Pre-2011 legacy data is not pooled: it uses order-size buckets and lacks post-migration Pro-Customer/Broker-Dealer granularity. It requires a separate parser and preregistered hypothesis.
- No 2011–2019 files were acquired; historical coverage, inactive/delisted identity, first-receipt vintages, corrections, license and strict PIT remain unproven. No returns/alpha/OOS/holdout test. F80 remains frozen; production/universe/capital unchanged.
- Deterministic Phase 250 tests/workflow are being added; hosted validation status will be recorded after the workflow completes.
- [Phase 250 report](PHASE250_CBOE_OPENCLOSE_HISTORICAL_CONVENTION_AWARE_FEATURE_ELIGIBILITY_2026-11-10.md) · [feature gate](phase250_cboe_openclose_convention_gate.py) · [tests](test_phase250_cboe_openclose_convention_gate.py)

- Hosted Phase 250 validation passed 17/17 deterministic tests in run [42738486543](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42738486543), job 129573491343. Workflow enforced the date-regime and no-PIT/no-alpha boundaries. No artifact was produced; no historical sample was downloaded.
