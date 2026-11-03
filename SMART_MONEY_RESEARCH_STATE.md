# Smart Money Research State

Updated: 2026-11-03

## Frozen control
- `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen.
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
- Decision: do not tune insider features/horizons to rescue this implementation. Reuse only for a materially different, pre-registered mechanism.

## Phase 22C — SEC 13F feasibility
- Status: NOT PRODUCTION-READY; identity-resolution research only if it materially improves worst-period coverage without lookahead.
- Latest run 41652405078 (2026-11-03) succeeded. Coverage remains 70.43% (2016Q1), 81.73% (2020Q1), and 93.02% (2024Q1); ambiguous candidates remain 51, 37, and 19 respectively. Conclusion: `INSUFFICIENT_COVERAGE_FOR_PRODUCTION`.
- Earlier PIT issuer/CUSIP audit produced minimum 54.8% coverage in 2016Q1. Direct PIT CUSIP is preferable to name fuzzy matching but still has class/ADR/legacy-CUSIP ambiguity.
- This is a data-identity feasibility result, not evidence against 13F economically. Park unless a deterministic security identity method materially improves the worst-quarter coverage.

## Phase 23C — CFTC COT positioning
- Status: KILLED for the tested equity-index positioning hypothesis.
- Run 39375172026 completed with 12 walk-forward test dates for NASDAQ and S&P 500 families.
- NASDAQ mean strategy return was +0.192% at H5 versus +0.890% unconditional and -0.460% at H20 versus -3.370% unconditional. S&P 500 mean strategy return was -0.049% at H5 versus +1.024% unconditional and -3.058% at H20 versus -1.443% unconditional; H20 hit rate was 16.7% for S&P 500.
- Decision: no robust incremental equity-selection edge; archive rather than optimize.

## Phase 24B — public listed-options historical feasibility
- Status: public OCC endpoint path is insufficient for event-level historical option-flow research.
- Run 39398787569 tested 11 historical sample dates. Contract-volume, DLP HTTP, and trade-volume endpoints returned effectively empty payloads; daily volume statistics were substantive, while volume-by-account-type was substantive on only 2/11 samples.
- Decision: do not infer historical options flow/OI/IV/skew from these endpoints.

## Phase 27O — SEC N-PORT institutional holdings dose-response
- Status: KILLED in the tested dose-response form.
- Run 39503800069 covered six annual formation periods (2020Q4–2025Q4) using the PIT 27N2 share-accumulation signal and fixed 63-trading-day forward return.
- Top-minus-bottom decile returns were -11.77%, -5.56%, +12.03%, +6.12%, -4.78%, and -1.74%; sign is not stable and no monotonic institutional-flow effect is established.
- Decision: do not optimize dose threshold or horizon.

## Phase 32 / 42B — market microstructure and SEC MIDAS
- Event-level historical order/quote data remain commercially licensed; do not synthesize them from inadequate aggregates.
- SEC MIDAS Metrics by Individual Security has quarterly history from 2012Q1 through 2026Q2 and useful daily security-level fields. However, no per-quarter first-publication timestamp was verified. Uniform 2/3/4-month lag sensitivity is exploratory only, not proof of PIT. Alpha authorization remains FALSE pending archived index snapshots or timestamped official publication evidence.

## Phases 43–45 — SEC fails-to-deliver (FTD)
- Phase 43 actual-file parser gate passed (runs 40800732551 and 40809120246): representative 2018/2026 files contained 43,567 and 66,693 records; SEC trailer counts/quantities reconciled, with no exact duplicate rows or missing CUSIPs.
- Phase 44 representative universe coverage was 253/335 (75.52%) in 2018 and 316/335 (94.33%) in 2026; 332/335 were observed in at least one sample.
- Phase 45 PIT identity gate (run 40973633206) found only 207/335 names observed in all five samples (61.79%); 21 of those 207 had changed/unresolved 2018–2026 CUSIP continuity. Crucially, absence from an FTD file cannot distinguish an active security with zero fails from an inactive/unlisted security.
- Decision: PARK FOR PUBLIC-DATA ALPHA. Restricting to always-observed names would create survivorship/selection bias. Reopen only with a deterministic historical security master/listing-status panel with PIT-effective dates. FTD is an aggregate balance, not a daily flow and not proof of naked short selling.

## Phase 46 / 52 — Cboe options data
- Public monthly symbol-level equity-option volume actual-file audit (run 40841944879) parsed successfully, but minimum frozen-universe coverage was 64.48%, below the predeclared 70% gate; representative 2019 samples were 69.55% and 71.04%. Historical release timestamps were also not available. Decision: KILL the public aggregate-volume candidate for this frozen-universe line.
- Cboe Trade-by-Trade (TBT) is materially richer: participant origin, side, open/close, contract, price, size and NBBO context; historical availability begins 2019-10-07. But the documented proposed price is $12,000/month, with $8,000/month ad-hoc historical access. Decision: PARK — commercial access required; no alpha test until licensed reproducible data is available.

## Phase 35/49 — SEC 13D/13G
- Status: **ROW-LEVEL ISSUER/PIT EXTRACTION PASSED; REPORTING-GROUP / ORIGINAL-AMENDMENT NORMALIZATION FAILED; ECONOMIC TEST BLOCKED.**
- Latest completed corrected artifact: run 41618946255, artifact 13236177463 (`phase35-13dg-pit-event-crosswalk-audit`). It contains 20,266 resolved rows, 303 subject issuers, 14,542 amendments, 19,680/20,266 event dates (97.11%), and zero submission/resolution errors. Filing-date range is 2020-10-01 through 2026-09-25; 27 of 335 universe tickers remain unresolved. `filing_date` is KnowledgeDate.
- The older run 41575083622 had one isolated 503 and 20,265 resolved rows; it is superseded by 41618946255 for current row-level counts.
- Critical correction: the accession-number prefix is the submitting-entity CIK and may be a third-party filing agent, not the actual reporting person. The OXY filing 0000928464-20-000057 has accession prefix 0000928464 but SEC identifies Carl C. Icahn (CIK 0000921669) as “Filed by”. Therefore accession prefix may be stored as `submission_cik`, but **must not** be used as a beneficial-owner/reporting-group key.
- The previous 3,115 issuer/prefix/form sequences and 58.5% amendment share are submission-prefix diagnostics only, not economic-group or true-first-event counts. The current extraction also starts in 2020, so pre-window originals are left-censored.
- `reporting_person` is populated on 3,502 rows and `purpose_text` on 261; current parsing does not reconstruct all joint reporting persons. Raw `percent_class` is mechanically selected around the 5% reporting threshold and is not an independent signal.
- Next gate: extend historical filing history; parse the actual Filed-by/reporting-person set and joint-filing/group evidence from index metadata, cover pages and structured XML; build deterministic issuer/group lineages; mark incomplete history left-censored; then re-audit historical active-universe coverage. No forward returns until these gates pass.
- Current rerun 41652405132 remains `in_progress` in the historical-CIK PIT audit step; no artifact yet. Do not duplicate it.

## Current priority
- Keep `F80_TOP20_PARTIAL50_BASELINE_C20` frozen.
- Do not spend further cycles rescuing killed FINRA, Form 4 standalone, CFTC COT, N-PORT dose-response, public aggregate options volume, or public FTD without a historical security master.
- Continue 13D/13G only through corrected reporting-group identity and complete historical predecessor chains. MIDAS remains a conditional public-data candidate only if PIT publication dates can be verified. Cboe TBT remains conditional on commercial licensing.
- No source has earned alpha promotion in this cycle.

## Research principle
“Smart money” is a hypothesis, not an assumption. Every candidate must pass historical coverage, ex-ante availability, PIT timestamps, universe overlap, incremental-information, chronological OOS, bootstrap and LOO tests before portfolio promotion.
