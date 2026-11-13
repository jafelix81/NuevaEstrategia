# Smart Money Research — Current State
**Updated:** 2026-11-12 UTC  
**Repository:** `jafelix81/NuevaEstrategia`

## Frozen control
- `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen.
- No Smart Money source has been promoted to production or demonstrated incremental OOS alpha in this research cycle.

## Hypotheses and dispositions
- **FINRA short flow × short interest (Phase 31): KILLED as independent alpha.** OOS signs reversed by horizon; bootstrap intervals included zero. Do not tune horizons to rescue.
- **SEC Form 4 insider aggregate signal (Phase 21C): KILLED as standalone alpha.** Final OOS spreads were mixed/weak and all bootstrap intervals included zero. The newer work is identity/lineage infrastructure, not a rescue of that signal.
- **CFTC equity-index COT (Phase 23C): KILLED for the tested equity-selection hypothesis.**
- **SEC N-PORT dose-response (Phase 27O): KILLED in tested form.**
- **Public OCC event-level options endpoints and Cboe public monthly aggregate volume: KILLED for the tested historical event-flow path due inadequate payload/coverage or release-time evidence.**
- **Cboe TBT / OptionMetrics / IvyDB TradeFlow: PARKED pending authorized historical samples, point-in-time availability and reproducible licensing.**
- **SEC MIDAS: conditional public-data candidate; first-publication timestamps remain unverified.**
- **SEC 13F/N-PORT: identity and historical universe coverage remain insufficient for production; do not treat filing-period holdings as available before filing acceptance.**
- **SEC 13D/G: data-feasibility only; 13D activist/control and 13G passive/aggregate must remain separate hypotheses.**

## Latest SEC 13D/G identity work
- **Phase 347:** 200/200 structured filings had exactly one CUSIP field; 197/200 had a valid nonzero security CUSIP; 179 unique checksum-valid nonzero CUSIPs; zero cross-subject collisions in this purposive sample. Four subject CIKs had multiple CUSIPs, so issuer-to-single-security collapse is invalid.
- **Phase 348:** 2/2 explicit predecessor references previously treated as XML-unavailable were recovered as legacy HTML in the immutable Phase 84 artifact. Both passed exact accession, subject, family, earlier acceptance, raw SHA-256 and CUSIP checks. They are validated explicit references, not necessarily immediate predecessors.
- **Hosted replay:** [Phase 347–348 run 43325466776](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43325466776) succeeded; artifact [13992128205](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43325466776/artifacts/13992128205), SHA-256 `f1f2bae9cc278133629562cde8c086e4a1327479d17d38e508fa524506ad8998`. Eight Phase 347 tests and five Phase 348 tests passed, and both deterministic outputs matched committed summaries.
- **Phase 349:** 44 explicit predecessor targets are manifested offline: 25 13D, 19 13G, 41 subject CIKs, 43 valid nonzero child CUSIPs and one zero sentinel. Only 25/44 have explicit reporting-person CIKs; only one has activist/control-action keyword tagging. No parent document has yet been retrieved.
- **Final hosted replay:** [run 43326498877](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43326498877) passed all 22 tests across Phases 347–349. [Artifact 13992528474](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43326498877/artifacts/13992528474), SHA-256 `5073e9f67f0bf3c83f5eb25f513fb231848d3bee2c806eaf8e84da57c02110ef`, includes the 44-row CSV manifest and was independently inspected.

## Next gates
1. Phase 350: retrieve the 44 exact parent accessions, preserve raw files/hashes, and validate subject CIK, family, earlier acceptance, CUSIP and explicit person identity. The first 10 accession digits are the submitting entity's CIK and can identify a third-party filing agent; use this only to construct the SEC archive path, never as issuer identity. Use the SEC archive URL form documented at https://www.sec.gov/search-filings/edgar-search-assistance/accessing-edgar-data, a declared User-Agent and a conservative 2 requests/second. The SEC documents no first-publication timestamp and notes filings often appear 1–3 minutes after acceptance; use the next trading session for any later event-study execution. Never infer immediate predecessor status.
2. Build an effective-dated CUSIP/security crosswalk only after parent validation; include class changes, ADRs, corporate actions, delistings and inactive securities.
3. Measure overlap with the historical investable universe and price history before any return study.
4. Preregister separate 13D activist/control and 13G passive/aggregate event hypotheses, use SEC acceptance UTC as knowledge time and conservative next-session execution, and test incremental information versus frozen LTM/F80 only after all identity/PIT gates pass.
5. Continue source comparison for options flow/OI/IV/skew, CFTC TFF, off-exchange activity and microstructure only where historical coverage and first-publication timestamps are defensible.

## Research discipline
Smart money is a hypothesis, not a label. No forward returns, alpha, chronological OOS, bootstrap, LOO or holdout test is authorized by Phases 347–349. Do not infer a positive result from data availability. Archive failed hypotheses and keep F80, production, universe, capital and parameters unchanged.


## Phase 350 access block — 2026-11-12
- Phase 350's 10 offline tests passed. The first SEC Archives request returned HTTP 403; the project-URL-only User-Agent did not provide a monitored contact email. The run stopped after one request: 0/44 parent documents retrieved, 0 raw files saved.
- Diagnostic artifact: [13991999046](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43327053770/artifacts/13991999046), SHA-256 `04c6568b01de176e55492d75f3224503c38cc8842a549b10f23a30c8d510d6c1`.
- Human action required: add repository Actions secret `SEC_USER_AGENT` with a project identifier and monitored contact email. The workflow preflights this secret and will not send another SEC request while it is missing.


## FINRA ATS/OTC disposition — Phase 117 (2026-11-05)
- The expanded revision-impact audit found that only 1.735% of symbol-aggregate rows were marked revised, but those rows represented 10.08% of shares and 11.44% of trades. In T1 OTC non-ATS, excluding revised rows would remove 33.24% of shares and 36.22% of trades.
- Do not backdate current final values to `initialPublishedDate`; the later `lastUpdateDate` is not a verified public dissemination timestamp, and the final extract is not a historical first-publication vintage.
- FINRA's 2019 website guide documents a year selector for historical weekly reports (including 2016), but the affirmative user certification was not accepted in the prior audit. No attempt was made to bypass it. Treat the older website archive as a gated feasibility candidate, not an admitted source.
- The FINRA ATS/OTC series is therefore parked for predictive use until actual immutable publication vintages or a verified conservative availability timestamp can be obtained. It remains a possible delayed liquidity/venue-composition feature, not directional evidence of informed buying or selling.

## Phase 350 safe preflight replay — 2026-11-13 UTC
- Documentation-only PR update triggered [run 43339390651](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43339390651) against the current workflow revision.
- All 10 offline parser/validation tests passed.
- The new `Validate SEC contact configuration` step failed before network retrieval because `SEC_USER_AGENT` resolved to an empty value. The SEC retrieval step was skipped; **zero SEC requests** were made in this replay and no artifact was expected.
- This confirms the repository Actions secret is still absent/empty. Phase 350 remains blocked at the already-disclosed human configuration gate; no retry will be launched until the preflight can pass.
- The prior HTTP 403 attempt remains isolated to run 43327053770 (one request, zero documents); it was not repeated.

## Cross-source admission review — 2026-11-13 UTC
- **Cboe Open-Close EOD:** a single 2025-03-28 C1 sample parsed 23,179 contract rows and contained 288/335 current candidate symbols (85.97%) with required participant-capacity fields populated. This is a one-date schema/coverage observation, not historical PIT admission. EOD files arrive overnight; conservative knowledge date is next session. Commercial access and full historical-universe validation remain open.
- **ORATS Near-EOD:** one public 2024-01-03 sample contained 716,822 rows and 5,787 underlyings, including 324/335 current candidate symbols (96.72%). Core fields are complete in that sample, but no multiplier/deliverable field was present, the spot fields are option-derived, historical first-publication time is unverified, and delisted/expired-contract retention is not yet independently validated. Historical archive pricing/access remains an owner decision; no purchase was made.
- **OptionMetrics IvyDB TradeFlow:** remains a potentially stronger directional-flow candidate (documented from 2016) but no authorized sample, exact field semantics, classification stability, or historical first-receipt vintage has been validated. Do not infer beneficial-owner identity from vendor classifications.
- **CFTC BPR/TFF:** Phases 239–243 and 263/266/273 provide a prospective append-only capture design with state/revision/rollback/partial-commit safeguards and immutable action pins. It remains on open PR #14, inactive on `main`; no raw prospective capture has occurred. TFF is a market/futures positioning regime source, not a stock-level signal; report date is not knowledge time.
- **FINRA ATS `blocksSummary`:** killed for stock-level alpha because the live schema has no security/ticker dimension. Aggregate ATS-regime use is a distinct, lower-priority hypothesis.
- **FINRA short flow × short interest:** prior standalone hypothesis remains killed; any flow+position interaction would require fresh publication-vintage and universe-coverage admission before a new preregistered test.
- **13F/N-PORT:** 13F historical issuer mapping in the existing audit ranged from 70.43% (2016Q1) to 93.02% (2024Q1) of the current matched candidates, insufficient for identical-universe testing. N-PORT direct-short observations remain concentrated in a tiny purposive sample with no usable ticker mapping; no alpha inference.
- No source is promoted. No forward-return/alpha/OOS/bootstrap/LOO or holdout test was run in this review. F80 and production remain unchanged.


## Phase 350 final preflight reconciliation — 2026-11-13 UTC
- Latest hosted attempt: [run 43339511052](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43339511052), job `retrieve-parents` / job ID `131604005268`.
- The immutable Phase 349 manifest ZIP passed SHA-256 verification; all **10/10** Phase 350 offline parser/validation tests passed.
- The explicit `Validate SEC contact configuration` step failed because `SEC_USER_AGENT` resolved to an empty string. The SEC retrieval step was skipped; **zero SEC requests** were made and no artifact was produced. This is a configuration gate, not a parser or SEC response failure.
- The immediately preceding safe replay [run 43339390651](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43339390651) had the same result. The only actual HTTP 403 remains isolated to [run 43327053770](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43327053770): one request, zero documents, immediate stop.
- Do not rerun Phase 350 until the repository Actions secret `SEC_USER_AGENT` is populated with a project identifier and monitored contact email. No secret value is stored in the repository or this report.
- Repository preflight: 197 branches across two pages; 33 open PRs. The latest 100 workflow runs were all completed (59 success, 30 failure, 10 cancelled, 1 skipped); no queued or in-progress run was present. PR #37 remains Draft/open/unmerged; PRs #34–#36 remain Draft/open/unmerged. No branch or PR was merged during this review.
- Cross-source disposition remains unchanged: Cboe Open-Close and IvyDB TradeFlow are conditional options-flow priorities; ORATS Near-EOD is a possible volatility/activity context source, not participant flow; ORATS Time & Sales is a higher-cost 2022+ microstructure candidate; Databento Security Master is a promising but unverified foundational identity candidate. CFTC historical TFF remains quarantined for the tested 2016–2024 PIT design; FINRA ATS is context-only and its tested short-flow stock-selection hypothesis remains killed; 13F/N-PORT coverage is not yet sufficient for identical-universe alpha testing.
- No new data were acquired, no vendor was contacted, no purchase was made, and no return/alpha/OOS/bootstrap/LOO/holdout test was run. `F80_TOP20_PARTIAL50_BASELINE_C20`, production, universe, capital and parameters remain unchanged.
