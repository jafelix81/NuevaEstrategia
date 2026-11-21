# Phase 549 review addendum — fail-closed Remarks polarity hardening

**Review cutoff:** 2026-11-21 20:52 UTC  
**Base Phase 549 head:** d38b3cd16e10a45ee290cc4c7983d3e047387008

## Finding

An independent review of the Phase 549 classifier found an uncovered false-positive path. The original negative expressions recognized only a narrow set of constructions such as “not made pursuant to” and “not made under”. The broader positive expression could therefore classify a sentence such as “shares are not being sold in connection with a Rule 10b5-1 plan” as positive reliance.

The original six tests did not cover this negated “in connection with” construction, “not sold pursuant to”, an explicit “not a Rule 10b5-1 plan” statement, or mixed positive/negative statements in one filing.

## Correction

- Replaced single-document keyword precedence with clause-level classification.
- Added explicit negative patterns for negated reliance, “not a plan”, “no plan”, and “without reliance” constructions.
- When a negative clause is found, its span is masked before checking for a separate positive clause.
- If the same clause contains contradictory positive evidence, or separate clauses indicate both positive and negative reliance, classification fails closed to `AMBIGUOUS_MENTION`.
- Raw keyword-presence flags remain insufficient to establish polarity.
- Added four regression tests for the uncovered constructions and contradictory statements.

## Validation and disposition

The existing Phase 403 pull-request offline-regression path is reused; no new scheduled collector or live capture is added. The PR regression will regenerate the audit artifact from the bounded current Form 144 and Form 4 ledgers. The resulting accession-level counts must be inspected before updating the narrative summary.

No return/event study, alpha test, backtest, OOS, bootstrap, LOO, data purchase, feature admission, cost/exposure/universe/holdout change, or production change is authorized by this correction. `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen.


## CI-discovered edge case

The first expanded regression run correctly caught one over-broad acceptance: the shared explicit-plan token also accepted the nonstandard compact string `10b51`, which the original audit intentionally kept ambiguous. The explicit positive/negative token was tightened to require the hyphen in `10b5-1`; the broader mention detector remains unchanged so nonstandard mentions are still surfaced but not promoted. A local replay of the seven targeted cases (Fermi wording, negated in-connection language, negated sold-pursuant language, negated plan identity, mixed clauses, nonstandard `10b51`, and explicit positive reliance) now matches the expected fail-closed labels. The failed run was [44948739438](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44948739438); its only failing assertion was the existing nonstandard-token ambiguity test. No live-capture job ran.
