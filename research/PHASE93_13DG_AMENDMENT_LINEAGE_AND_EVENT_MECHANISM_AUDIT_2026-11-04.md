# Phase 93 — SEC 13D/G conservative amendment-lineage and event-mechanism audit

**Date:** 2026-11-04  
**Branch:** \`phase93-13dg-amendment-lineage-and-event-mechanism-audit\`  
**Mode:** offline only; immutable Phase 84 raw sample + corrected Phase 91 event/person records  
**No SEC requests, no forward returns, no vendor purchase**

## 1. Why this phase exists

Phase 90/92 found 97 amendments among 200 structured filings; 51/97 did not contain a usable \`previousAccessionNumber\`. A missing explicit reference must not be silently reconstructed from filer CIK, accession-prefix CIK, a first-person 13G Filer-CIK candidate, or the most recent filing for the same issuer.

Phase 92's narrative classifier also left 126/200 records unclassified. Its one explicit open-market-purchase phrase is not a reliable estimate of actual open-market purchases. Phase 93 therefore performs two separate diagnostics:

1. a conservative, sample-limited amendment-parent candidate graph; and
2. a broader, transparent event-mechanism taxonomy that preserves matched phrases.

Neither output is an alpha signal or a confirmed legal interpretation.

## 2. Immutable inputs

- Phase 84 raw complete-submission artifact: run **41914491120**, artifact **13364856424**.
- Corrected Phase 91 identity/timing artifact: run **41934402354**, artifact **13373581231**.
- Phase 91 structured XML sample: 200 filings; reporting-person table: 470 rows.
- Phase 92 reported 97 amendments and 51 missing explicit predecessor references.

The workflow re-hashes every raw complete-submission file against the Phase 91 event manifest, reparses the primary XML, and rechecks XML subject CIK, filer CIK and form against Phase 91. No live SEC request is made.

## 3. Conservative amendment-lineage rules

### Explicit references

A non-empty \`previousAccessionNumber\` is treated as an explicit reference, **not automatically as the immediate predecessor**. If the referenced accession is in the 600-row Phase 84 header sample, validate subject CIK, form family and earlier filing date. Distinguish a structured parent from a header-only legacy parent. If the referenced accession is outside the sample, retain the reference and mark it outside-sample; this is not a failed link.

### Missing references

For an amendment without an explicit predecessor, enumerate candidate parents only within the 200 structured filings. A candidate must satisfy all of the following:

- same SEC-HEADER subject CIK;
- same 13D or 13G family;
- strictly earlier SEC acceptance timestamp;
- if both records contain CUSIPs, at least one CUSIP must overlap; and
- either an explicit reporting-person CIK overlaps, or an exact normalized reporting-person name overlaps together with CUSIP overlap.

The following are deliberately **not** identity keys: filer CIK, accession-prefix CIK, and the Phase 91 inferred first-person 13G Filer-CIK candidate. A same-filer relationship alone is insufficient.

A unique candidate is labelled \`unique_candidate_parent_not_confirmed\`; multiple candidates are ambiguous. No candidate is ever promoted to a confirmed link, and no event is collapsed or deduplicated.

### Interpretation limits

- The 200 structured filings are a stratified pilot, not the issuer's complete history.
- A parent outside the sample is not evidence that no parent exists.
- Reporting persons and CUSIPs can legitimately change between amendments.
- Candidate edges are for manual audit and future sample design only.

## 4. Event-mechanism taxonomy

The parser emits overlapping, phrase-auditable tags for:

- activist/control actions (specific proxy, nomination, board-replacement, strategic-alternative or sale-of-company language);
- generic governance references (kept separate from activism);
- business-combination consideration;
- open-market acquisition and disposition (separate tags);
- private placements and offerings;
- employee equity compensation;
- conversion/exercise;
- gifts, transfers and distributions;
- pledges/collateral;
- derivatives and swaps;
- aggregated client/adviser holdings;
- capital reorganization/denominator changes;
- ordinary-course/no-control-intent language;
- no-recent-transactions declarations;
- litigation/disputes; and
- group/joint-reporting-person flags.

The classifier is deliberately conservative. A generic mention of a board does not imply activism; generic purchase language does not imply an open-market trade; an adviser/client aggregate is not treated as one proprietary position. Unmatched records remain unclassified. Matched phrases are retained for review.

## 5. Outputs

- \`phase93_summary.json\`
- \`phase93_event_mechanism_audit.csv\`
- \`phase93_amendment_lineage_audit.csv\`
- \`phase93_candidate_parent_edges.csv\`

## 6. Acceptance gates

- All 200 Phase 91 event rows are reparsed.
- Raw SHA-256 matches the immutable Phase 91 record for every filing.
- XML subject, filer and form match Phase 91 for every filing.
- No silent accession normalization or inferred parent link.
- Regression tests cover false-positive activism, transaction-mechanism separation, explicit-parent validation, same-filer-only rejection, strict chronology, CUSIP conflict, and the prohibition on inheriting first-person 13G candidate CIKs.

A failure is preserved; thresholds are not relaxed.

## 7. Research decision

Phase 93 can authorize only a subsequent **event-normalization feasibility** decision. It cannot authorize forward-return tests. Before an economic test, the project still needs:

- a historically valid F80 security master and active-universe membership;
- broader issuer filing history and amendment-chain completeness;
- point-in-time acceptance/dissemination treatment and next-session execution;
- stable reporting-person/entity resolution and group handling; and
- a preregistered hypothesis separated by event mechanism (activism, open-market accumulation, corporate consideration, compensation, adviser/client aggregate, etc.).

No return chasing or horizon optimization is permitted. Any future incremental test must compare against frozen LTM/F80 with identical exposure and costs, chronological OOS, bootstrap and LOO discipline.

**F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen.**
