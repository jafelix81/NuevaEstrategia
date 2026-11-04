# Phase 90 — SEC 13D/13G event-semantics and amendment-lineage pilot

**Date:** 2026-11-04  
**Branch:** phase90-13dg-event-semantics-pilot  
**Input:** immutable Phase 84 raw-submission artifact from run 41914491120 / artifact 13364856424  
**Mode:** offline only; no SEC requests

## Research question

After Phase 84's role-aware subject/filer gate passed, can the structured 13D/13G XML be normalized into separate filing, issuer, reporting-person and amendment-link records without treating event dates as knowledge dates or collapsing multiple reporting persons?

## Preregistered diagnostics

- Reparse every structured XML document present in the Phase 84 artifact and reconcile XML issuer/filer/form against SEC-HEADER.
- Preserve every reporting person as a separate record, including CIK status, group flag, type codes, voting/dispositive powers, aggregate shares and class percentage.
- Preserve the exact previousAccessionNumber for amendments; classify predecessor links as in-sample consistent, outside sample, missing, or inconsistent by subject/family/date.
- Compare reported event_date with SEC filing date only as a descriptive lag diagnostic. Acceptance-DATETIME remains the conservative knowledge timestamp.
- Separate 13D and 13G form families and preserve 13G rule designations and 13D purpose text.

## Interpretation boundary

This is a parser and event-normalization feasibility test, not an informed-trading test. A predecessor outside the 600-row sample is not a broken link. A missing predecessor in an amendment is a data-quality issue, but should not be silently repaired using accession-prefix CIK or nearest-date heuristics. No forward returns, feature construction, alpha inference or production changes are authorized.

The historical 319-CIK candidate set is not a point-in-time F80 security master. Even a clean event panel cannot be tested against the strategy until historical issuer/security continuity and eligible-universe membership are reconstructed.
