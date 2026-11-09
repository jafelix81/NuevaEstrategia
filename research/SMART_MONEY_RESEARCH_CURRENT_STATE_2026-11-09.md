# Smart Money Research — Current State

**Updated:** 2026-11-09  
**Research branch:** \`phase99-broad-pit-universe-charter\`  
**Frozen production baseline:** \`F80_TOP20_PARTIAL50_BASELINE_C20\` — unchanged

## Latest material updates

### Phase 231 — Cboe Option Quotes full-row reparse
- Public sample hash pinned and reverified: \`7645a6cc94f1a984e98264a4b494f748e373c30ecde85de25ceadb83a5c56782\`.
- 115,617 populated row instances across five data members.
- 3,304 ambiguous expiration rows quarantined; no locale guessing.
- 112,313 unambiguous rows passed the full row-level contract/numeric/duplicate/OI checks.
- 0 invalid quote timestamps, 0 numeric errors, 0 duplicate contract/interval keys, 0 inconsistent start-of-day OI contract-days, 0 bid-above-ask rows.
- Independent Phase 175 all-row date diagnostics reconciled on all five members.
- Current-head GitHub Actions run \`42568771468\` succeeded; 9/9 regression tests; artifact \`13651429847\`.
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
| Form 4 | Standalone implementation discarded | Must distinguish transaction semantics and filing availability |
| Form 144 | Conditional event candidate; class-share path feasible via raw inline XBRL, not admitted | Exact class mapping, 289-issuer coverage, PIT float/ADV and security identity |
| SEC 13D/G | Separate 13D and 13G research tracks | Reporting-person economic identity and amendment chains |
| N-PORT | Conditional short-side hypothesis | Original XML retrieval blocked by missing authorized \`SEC_CONTACT_EMAIL\` |
| Cboe Option Quotes | Sample parser gate passes on unambiguous rows only | PIT receipt/vintage, broad history/universe, licensing |
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

## Next research steps
1. After PR14 reaches the default branch, begin CFTC BPR capture. Treat the first scheduled receipt as a baseline state only; treat later newly indexed reports/revisions as events only from their own receipt timestamps. Accumulate an adequate multi-regime panel before any return test, and compare only as a market-regime overlay against QQQ risk state and frozen LTM/F80.
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
