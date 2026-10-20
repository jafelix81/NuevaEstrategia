# Research state — 2026-10-20

## Frozen production baseline
- F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen.
- No production rules changed.

## Latest completed phase
### Phase 27C — SEC N-PORT PIT mapping audit
- Workflow: Fase 27B/27C - SEC N-PORT Schema and PIT Mapping Audit
- Run: 39416949124
- Result: SUCCESS
- Decision: PROMOTE_TO_PIT_UNIVERSE_MAPPING
- Audited datasets: 2019Q4, 2023Q4, 2026Q3.
- Required SUBMISSION, REGISTRANT, FUND_REPORTED_HOLDING and IDENTIFIERS members present in all samples.
- SUBMISSION contains ACCESSION_NUMBER, FILING_DATE and REPORT_DATE.
- FUND_REPORTED_HOLDING contains ISSUER_CUSIP.
- IDENTIFIERS contains IDENTIFIER_TICKER and IDENTIFIER_ISIN.
- Important caveat: Phase 27C established schema/identifier feasibility, not alpha and not complete universe coverage.

## Current experiment
### Phase 27D — SEC N-PORT PIT universe coverage
- Branch: phase27d-sec-nport-pit-universe-coverage
- Purpose: measure historical coverage of the frozen 335-name universe and ticker→CUSIP ambiguity before any alpha test.
- Quarters: 2019Q4, 2020Q4, 2021Q4, 2022Q4, 2023Q4, 2024Q4, 2025Q4, 2026Q3.
- No lookahead: FILING_DATE is retained as the conservative knowledge-date candidate; REPORT_DATE is never treated as the knowledge date.
- Ticker is only a historical bridge/cross-check; ISSUER_CUSIP remains the primary security key.
- No universe expansion or survivorship-driven replacement.
- No alpha test is permitted until coverage and ambiguity are audited.

## Prior hypothesis decisions
- SEC Form 4 aggregate insider intensity: killed after OOS testing.
- CFTC COT standalone regime signal: killed after walk-forward.
- FINRA Short Interest incremental signal: killed after corrected walk-forward.
- OCC options historical flow: killed for insufficient homogeneous historical coverage.
- FINRA OTC/ATS: blocked pending authenticated/async data access; no alpha claims made.

## Next gate
Promote only if 27D shows adequate historical universe coverage and manageable identifier ambiguity across all audited periods. Otherwise kill/hold N-PORT before alpha testing.
