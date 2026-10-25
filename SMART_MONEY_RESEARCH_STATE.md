# Smart Money Research State

Updated: 2026-10-25

## Frozen control
- F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen.
- MOM120 is a validated control candidate but not promoted: realized portfolio metrics slightly exceeded LTM, but incremental daily excess was small and the block-bootstrap CI included zero.

## Phase 31 — FINRA short-flow × short-interest divergence
- Status: KILLED as independent alpha.
- Valid OOS run: 40164323397.
- PIT: short flow through signal close; short interest only after conservative knowledge date.
- Result: horizon-dependent sign reversal; economic spreads' bootstrap intervals included zero. Do not tune horizons to rescue.

## Phase 22C — SEC 13F feasibility
- Status: NOT PRODUCTION-READY; continue identity-resolution research only if it can materially improve coverage without lookahead.
- Run 40064660452 / artifact phase22c-sec-13f-mapping-audit-v6: name/former-name mapping coverage ranged from 70.4% (2016Q1) to 93.0% (2024Q1) across the frozen candidate universe; conclusion was INSUFFICIENT_COVERAGE_FOR_PRODUCTION.
- Run 40081509388 / artifact phase22c-pit-issuer-cusip-audit-v8: report-date 13F issuer/CUSIP mapping restricted to non-derivative common equity produced minimum coverage 54.8% (2016Q1); conclusion 13F_IDENTITY_MAPPING_NEEDS_FURTHER_RESOLUTION.
- Important: this is a data-identity feasibility result, not evidence against 13F economically. The direct PIT CUSIP route is preferable to name fuzzy matching, but still has material class/ADR/legacy-CUSIP ambiguity.
- Next decision gate: only pursue another 13F mapping iteration if it uses deterministic security identity resolution (e.g. report-date CUSIP plus explicit share-class/ADR rules) and materially improves the worst-quarter coverage while preserving PIT. Otherwise park 13F and move to another Smart Money source.

## Phase 32 — market microstructure
- Feasibility audit indicates event-level historical order/quote data would be valuable, but reproducible execution currently requires a licensed historical dataset. Do not synthesize microstructure from inadequate aggregates.

## Research principle
"Smart money" is a hypothesis, not an assumption. Candidate sources must pass historical coverage, ex-ante availability, timestamp/PIT, universe overlap, OOS, incremental-information, bootstrap and LOO tests before portfolio promotion.
