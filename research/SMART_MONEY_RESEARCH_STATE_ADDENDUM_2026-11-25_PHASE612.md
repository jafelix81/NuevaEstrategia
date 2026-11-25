# Smart Money Research State Addendum — 2026-11-25 (Phase 612)

## Current state

- Phase 611 SEC 13F timestamp sample: 48/48 filing-detail checks passed across the 2018 Q1 and 2026 Jun–Aug datasets; this is a deterministic stratified feasibility sample, not a population error-rate estimate.
- Phase 611 operational erratum: the live SEC job was corrected to require explicit \`workflow_dispatch\` with \`run_live_audit=true\`; push and pull-request events now run offline tests only. The prior push-triggered sample remains valid.
- Phase 612 XNYS session calendar: 3,496 sessions from 2013-01-01 through 2026-11-24; 29 13:00 ET early closes; regular opens 09:30 ET; no weekend sessions.
- Selected 2026 holidays/early closes agree with the official NYSE calendar; selected 2001/2012/2018/2025 special closures are spot-checked.
- The knowledge-clock function uses max(EDGAR Accepted, prospective collector first-seen); without first-seen it withholds the filing until 23:59:59 ET on the legal Filing Date.
- A daily bar is complete only when its scheduled close is strictly later than knowledge time; daily-bar-derived execution is delayed to the next XNYS session. Both next-open and next-EOD clocks are retained.
- Pinned calendar dependency: exchange_calendars 4.13.1.

## Open gates

1. Obtain prospective collector first-seen timestamps for 13F; historical first-seen is not available.
2. Verify actual daily-price provider publication timestamps and daily-bar semantics.
3. Complete effective-dated CUSIP/FIGI/ticker identity for the historical F80 universe.
4. Reconstruct 13F amendments and sequence-group attribution before creating features.
5. Only then test institutional ownership/persistence/accumulation incrementally versus frozen F80/LTM with chronological OOS, identical exposure/costs, bootstrap and leave-one-out.

## Research discipline

- Event-only earliest open is a lower-bound diagnostic, not a modeled fill.
- No signal eligibility or alpha is inferred from calendar validation.
- No incomplete-universe comparison.
- \`F80_TOP20_PARTIAL50_BASELINE_C20\` remains frozen.
- No production, capital, exposure, or parameter changes.
- No paid data or vendor contact; options budget USD 0.
