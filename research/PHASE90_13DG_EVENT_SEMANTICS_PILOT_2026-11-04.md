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


## Phase 90 execution result — run 41927541088

The offline parser/lineage gate passed. All 600 raw submissions replayed with valid SHA-256; all 200 XML documents were reparsed; XML subject, filer and form each matched SEC-HEADER 200/200; mandatory XML coverage was 192/192; acceptance timestamps were valid 600/600.

The first report showed null event-date lags because the XML stores dates as MM/DD/YYYY while the first diagnostic accepted ISO only. This was a diagnostic parsing defect, not missing source data. The rerun accepts both formats and reports the following from the 200 XML rows:

- 79 Schedule 13D and 121 Schedule 13G filings.
- 103 originals and 97 amendments.
- 470 reporting-person rows; mean 2.35 per filing, maximum 31.
- Reporting-person CIK status: 158 present, 210 unreported, 102 explicitly declared no CIK.
- 46/97 amendments have a direct previousAccessionNumber; 51/97 do not. Of the 51 missing, 50 XML documents omit the field entirely and one contains an empty element.
- Among the 46 direct links, 44 predecessors are outside this small sample and 2 are internally consistent. No heuristic predecessor links are created.
- Event dates are present in 200/200, none occur after filing date in this sample. Filing-minus-event lag has median 17 calendar days (range 0–290); 13D median 3 days, 13G median 34 days. This is descriptive only, not the knowledge timestamp.
- 13D purpose text is present in 67/79; 13G rule designations are present in 121/121.

The 51 missing predecessor fields are a genuine source-level limitation in this sample, not a parser failure. AmendmentNo is retained but is not used to infer a predecessor. The 13D and 13G panels therefore need separate event/lineage treatment before any economic hypothesis.


### Reporting-person CIK structure by form family

The rerun also separates the reporting-person identity fields by form family:

- Schedule 13D: 260 reporting-person rows across 79 filings; 158 have a reporting-person CIK and 102 explicitly declare no CIK.
- Schedule 13G: 210 reporting-person rows across 121 filings; none have a reporting-person CIK in this sample. A raw-tag audit found zero occurrences of both reportingCik and reportingCikNotPresentInEdgarFlag in those 121 primary XML documents. This is an observed sample property, not a claim that every 13G filing lacks the optional field.
- Consequently, 13G reporting-person identity in this sample is name/type/address based, not a deterministic CIK join. Do not substitute the submission filer CIK for the reporting person.
- 13G also has the larger direct-predecessor gap: 39/58 amendments lack previousAccessionNumber (67.2%) versus 12/39 (30.8%) for 13D.

This makes 13D and 13G materially different data products: 13D has stronger reporting-person CIK resolution and a shorter observed event-date lag, while 13G has more periodic/lagged event dates and much weaker person-level CIK identity in this sample. These are feasibility observations, not evidence that either form predicts returns.
