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

## Next gates
1. Phase 350: retrieve the 44 exact parent accessions, preserve raw files/hashes, and validate subject CIK, family, earlier acceptance, CUSIP and explicit person identity. Never infer immediate predecessor status.
2. Build an effective-dated CUSIP/security crosswalk only after parent validation; include class changes, ADRs, corporate actions, delistings and inactive securities.
3. Measure overlap with the historical investable universe and price history before any return study.
4. Preregister separate 13D activist/control and 13G passive/aggregate event hypotheses, use SEC acceptance UTC as knowledge time and conservative next-session execution, and test incremental information versus frozen LTM/F80 only after all identity/PIT gates pass.
5. Continue source comparison for options flow/OI/IV/skew, CFTC TFF, off-exchange activity and microstructure only where historical coverage and first-publication timestamps are defensible.

## Research discipline
Smart money is a hypothesis, not a label. No forward returns, alpha, chronological OOS, bootstrap, LOO or holdout test is authorized by Phases 347–349. Do not infer a positive result from data availability. Archive failed hypotheses and keep F80, production, universe, capital and parameters unchanged.
