# Phase 609 — full-quarter SEC 13F sequence-group audit

**Status at branch creation:** full-quarter live audit pending.  
**Samples:** SEC 2018 Q1 and 2026 June–August data sets.  
**Scope:** apply the Phase 608 group-aware graph to actual OTHERMANAGER2, INFOTABLE, SUMMARYPAGE, SUBMISSION and COVERPAGE tables. Stream INFOTABLE; do not export raw holdings.

## Why this phase exists

Phase 607 confirmed from six original EDGAR filings that sequence numbers identify manager groups, not unique manager rows. Phase 608 implemented a group-aware parser, but only against fixtures. Phase 609 applies that model to the same two full-quarter data sets used in Phase 606.

## Measures

- Submission / cover-page accession join coverage.
- OTHERMANAGER roster integrity.
- OTHERMANAGER2 member rows, distinct sequence groups, multi-member groups, maximum group size, exact duplicate member rows and member identifier quality.
- INFOTABLE numeric group references, matched/unmatched groups, group-only versus single-member references, zero sentinels and raw nonnumeric labels.
- SUMMARYPAGE declared included-manager count versus actual member-row count.
- 13F-NT notice roster and information-table controls.

## Interpretation

A matched multi-member sequence group is not an individual manager attribution. Nonnumeric values are retained as raw as-filed text. Zero is a no-group sentinel. Unmatched numeric sequence references remain unresolved. Notice filings are not interpreted as zero-holdings portfolios.

## Limits and next gate

The audit is structural and temporal availability is not yet applied. It does not establish beneficial ownership, decision-maker identity, net exposure, short positions, informed behavior, alpha or OOS performance. After this audit, the next gate is filing-acceptance timestamps, amendment state and effective-dated F80 security identity. Only then should group-level ownership features be tested against frozen F80/LTM.

No data purchase, vendor contact, options request, production change, exposure or capital change. F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen; options budget USD 0.
