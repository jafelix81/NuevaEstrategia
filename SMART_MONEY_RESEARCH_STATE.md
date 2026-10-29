# Smart Money Research State

Updated: 2026-10-29

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

## Phase 43/44 — SEC FTD
- Status: FEASIBLE_PUBLIC_CANDIDATE; actual-file and representative universe-coverage audits passed. SEC documents coverage from February 2004 through September 2026, with first-half files available at month-end and second-half files around the 15th of the following month.
- The source contains settlement date, CUSIP, ticker, price and aggregate fails-to-deliver balance. FTD is explicitly not equivalent to short selling and must be treated as settlement-friction information.
- Coverage audit found 70.75% overlap on both sampled half-month files, 99.10% on either sampled file, and 94.33% on the late-2026 sample. Missing symbols must not be silently interpreted as zero before the active-universe logic is fixed.
- Next gate: construct the conservative PIT signal panel and distinguish inactive/non-applicable names from active securities with zero FTD. No alpha test yet.

## Phase 48 — SEC 13D/13G source-regime feasibility
- Status: SOURCE-REGIME PASS, but not alpha-authorized.
- Run 40932788305 / artifact 12923896183 passed the pre/post structured-document regime gate. The audit found 4,651 pre-cutoff filings and 4,238 post-cutoff filings in the 2020-10-01 through 2026-09-30 candidate window; filing date is the PIT knowledge date.
- Submission retrieval errors were 53 (17.6%) and were deliberately separated from the document-field gate; they remain an identity/coverage problem that must be resolved before alpha.

## Phase 49 — SEC 13D/13G historical identity coverage
- Status: KILLED FOR CURRENT IMPLEMENTATION / DO NOT ALPHA TEST.
- Run 40938882261 completed the reproducible identity gate on the frozen 335-name universe. Only 308/335 names (91.94%) had a CIK from either SEC current data or the historical CIK mapper, below the pre-registered 95% threshold.
- Only 296/335 names (88.36%) had agreement between the two identity sources. There were 27 unresolved tickers and two source disagreements (PARA and XOM). Five names were SEC-current-only and seven were historical-mapper-only.
- Decision: no 13D/13G alpha testing and no universe shrinkage. The source remains economically interesting, but the current identity layer is not strong enough for a defensible F80/LTM incremental test. Reopen only with deterministic security identity resolution that materially improves coverage and resolves the two disagreements.

## Current priority
- Keep the frozen F80/LTM control unchanged.
- Do not spend further cycles rescuing FINRA, Form 4, CFTC COT, current N-PORT dose-response, or the current 13D/13G identity implementation.
- Prioritize sources with genuinely different information and reproducible PIT: SEC FTD is currently the strongest public candidate for the next economic test; licensed institutional/options microstructure remains attractive only if reproducible historical access can be established.

## Research principle
"Smart money" is a hypothesis, not an assumption. Candidate sources must pass historical coverage, ex-ante availability, timestamp/PIT, universe overlap, incremental-information, chronological OOS, bootstrap and LOO tests before portfolio promotion.
