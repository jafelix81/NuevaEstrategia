# Smart Money Research — Current State

**Updated:** 2026-11-08  
**Repository:** jafelix81/NuevaEstrategia  
**Research branch:** phase99-broad-pit-universe-charter  
**PR:** #13, open and currently mergeable; do not merge automatically.

## Frozen controls and guardrails

- `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen.
- The original 335-name F80 universe was manually selected and has no reproducible historical membership rule. Treat F80 results as conditional on that curated list; do not silently replace it.
- The legacy holdout is `CONSUMED_NOT_PRISTINE`; do not use it for new confirmation.
- No CAGR target or fixed holding period. Require chronological OOS, identical exposure/costs, bootstrap and LOO before any promotion.

## Killed or parked hypotheses

- FINRA short-flow × short-interest divergence: killed as independent alpha after horizon-dependent sign reversal and bootstrap intervals including zero.
- SEC Form 4 standalone feature set: killed in its tested frozen-universe OOS diagnostic; do not tune the same implementation to rescue it.
- CFTC TFF equity-index positioning: killed in the tested stock-selection form; TFF may remain regime context only if publication vintages are reconstructed.
- SEC N-PORT long-accumulation dose-response: killed in the tested form.
- OCC volume-by-account-type: parked; short recent history and no direction/open-close/beneficial-owner identity.
- SEC MIDAS: market-structure context only; historical daily rows were published in quarterly releases, so no daily PIT signal admission.
- Nasdaq Trade Outline: not economically justified at quoted acquisition cost and unresolved PIT/venue-routing semantics.

## Conditional source candidates

- **SEC 13D/G:** Phase 225 shows 13D and 13G event-date mechanics differ materially. Keep them separate; 13G is heavily quarter-end weighted. Event date is not knowledge time. Continue amendment state, reporting-person/group and effective-dated CUSIP/security identity before any economic test.
- **Form 144:** daily PIT clock is conservatively the first XNYS session after SEC filing date. Signal is not admitted: seller/security-class identity, historical active/delisted universe, independent PIT shares/float and ADV remain unresolved. Form 144 is a proposed sale notice, not execution.
- **N-PORT short exposure:** distinct short-quantity hypothesis is preregistered, but the 23-row example is purposive and from one filing. Raw filing retrieval/hashes, series lineage, class/security identity and broad PIT coverage remain pending.
- **Options:** Cboe C1 Open-Close EOD remains the leading conditional participant-capacity source; C1-only, not whole OPRA, and historical first-receipt/correction vintages are not established. IvyDB Open Interest / TradeFlow remain conditional candidates; no purchase or alpha admission.
- **FINRA ATS/OTC:** data reconcile, but revised final values cannot be backdated to first publication; historical vintages and broad PIT security identity remain unresolved.
- **SEC Companyfacts/XBRL:** Companyfacts is partial for entity-wide facts; class-specific raw accession XBRL is required for multi-class issuers. Phase 224 has synthetic regression tests but no live coverage census.
- **CFTC TFF:** regime candidate only, not stock-level institutional flow; historical publication-vintage reconstruction is required.

## Phase 225 — 13D/G event-time semantics

- Phase 124 source: 600 stratified index rows, 599 actual filings, one index alias quarantined; 600 raw hashes and SEC headers reverified.
- Event dates: 553/599 parsed (92.32% unweighted). Phase 214 independently reproduced all 497 legacy HTML parser outcomes, but this is not a gold-standard semantic validation.
- Weighted 13D: 96.04% date coverage; 2.63% quarter-end event dates; weighted median filing-event lag 4 days.
- Weighted 13G: 90.73% date coverage; 76.44% quarter-end event dates; weighted median filing-event lag 40 days.
- Keep 13D/13G and initial/amendment cohorts separate. Event date is never the knowledge clock; use SEC acceptance and next-session availability.
- No returns/alpha, holdout, bootstrap/LOO or production test in Phase 225.

## Technical blockers and repository state

- N-PORT raw SEC retrieval previously failed closed because the authorized SEC contact configuration was missing. Do not invent an email or bypass SEC fair-access requirements.
- PR #13 is open, 550 commits ahead / 1 behind main by compare; GitHub currently reports mergeable/clean. No merge was attempted.
- Branch inventory: 130 branches.
- Latest 100 Actions runs: 98 success, one failure and one cancellation; zero in-progress or queued. The Phase 214 failure was an earlier attempt; corrected run 42491346221 passed. The cancelled attempt was replaced.
- Latest CI fan-out is on older commit 5ac79c0; current research head e9f661 has no associated workflow run because its commits use `[skip ci]`.

## Promotion rule

No candidate becomes a model feature until historical coverage, ex-ante availability, stable identifiers, survivorship/delisting treatment, incremental information versus frozen LTM/F80, chronological OOS and economic costs all pass. A plausible institutional interpretation is a hypothesis, not evidence.
