# Smart Money Research State Addendum — Phase 654 (2026-11-27)

**Mainline documentation commits:** report `ca29fb1eedfdd536a8653461a6c7f0553065662f`; reproducible JSON `4a261d3e367ce1083505a23ebbf610bc0e5fbdf5`.  
**Operational tracking:** Issue [#194 comment 7206946251](https://github.com/jafelix81/NuevaEstrategia/issues/194#issuecomment-7206946251).

## Current findings

- Natural Form 4 run [45917890802](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45917890802) succeeded; offline tests 82/82. No new accessions/events. Ten-accession backfill appended 53 transaction details, 206 transaction-linked footnote references, 29 additional dedicated footnote references and 13 filing-level owner rows.
- The strict Form 144/Form 4 artifact crosswalk now contains 13 proposed-sale matches and one prior-sale-history match across 12 Form 4 accessions. Ten of 13 proposed-sale transaction dates precede the Form 144 collector first-seen-upper-bound calendar date; three are same-day and intraday-unresolved. Two Form 144 acceptance clocks remain unresolved. The matches are descriptive, not predictive; signal-eligible = 0.
- 13F natural run [45910142871](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45910142871) succeeded across all four feeds; 29 existing accession observations, zero new accessions, no holdings/XML and zero eligible rows. The 29 initial-baseline observations still lack lower bounds.
- Form 144 latest natural run [45906061652](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45906061652) remains successful: 835 accessions / 5,537 detail rows, 168 bounded backfills remain, no signal.
- FINRA Phase 650 / PR #247 is merged and passed 62/62 offline tests, but no natural post-merge live run is visible. Its 22:30 and 23:30 UTC weekday schedule slots on 2026-11-26 passed without a post-merge scheduled run. Issue #194 requests a human check of workflow enablement and scheduled-workflow permissions; this is an observed gap, not proof of administrative disablement.

## Source disposition

- SEC Form 4 remains the leading public event candidate, conditional on effective-dated security identity, historical F80 membership, owner/transaction attribution, event semantics and conservative availability clocks.
- Form 144 remains proposed-sale disclosure and context, not an execution feed. The expanded crosswalk reinforces that filing acceptance before Form 4 acceptance does not establish pre-execution information.
- SEC 13F remains metadata-only baseline; no holdings or admissible initial-baseline intervals.
- FINRA Reg SHO awaits natural post-Phase-650 validation; old rejected files are not retroactively promoted.
- CFTC Russell remains outcome-blind with only two prospective observations and an unresolved rights-cleared price source.
- Options remain unpurchased; authorized data budget USD 0.

## Controls

- `F80_TOP20_PARTIAL50_BASELINE_C20`: frozen.
- Incremental alpha demonstrated: none.
- New valid OOS / bootstrap / LOO: none.
- Holdout untouched.
- No changes to universe, model parameters, exposure, costs, capital, production or holding-period policy.
- No options-data spend.

Full detail: [Phase 654 report](PHASE654_FORM144_FORM4_CROSSWALK_EXPANSION_TIMING_NEGATIVE_CONTROL_2026-11-27.md) · [JSON summary](PHASE654_FORM144_FORM4_CROSSWALK_EXPANSION_TIMING_NEGATIVE_CONTROL_2026-11-27.json).
