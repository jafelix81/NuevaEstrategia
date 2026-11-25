# Phase 605 — SEC Form 13F role-aware manager relationship graph audit

**Status: PASS — 17/17 offline synthetic regression tests passed.**  
**Date:** 2026-11-24/25 UTC  
**Branch:** phase605-sec-13f-manager-relationship-graph-audit  
**Parent:** phase48-sec-13f-asof-amendment-state-machine  
**Scope:** SEC 13F relationship schema, role direction, identifier resolution, and line-reference integrity. No live SEC download or alpha test.

## Why this phase exists

Phase 48 correctly keeps 13F-NT / 13F-NT/A notices separate from holdings states, but it explicitly did not parse the two SEC manager relationship tables. Treating a notice filer as a manager with zero positions would create false exits. Treating all "other manager" rows as the same relationship would also invert or double-count manager attribution.

The official SEC Form 13F Data Sets specification defines two distinct tables:

- OTHERMANAGER: "other managers reporting for this manager"; key is ACCESSION_NUMBER + OTHERMANAGER_SK.
- OTHERMANAGER2: "other managers included in this report"; key is ACCESSION_NUMBER + SEQUENCENUMBER.
- INFOTABLE.OTHERMANAGER: sequence number(s) of included managers with whom discretion is shared.

Official schema: https://www.sec.gov/files/form_13f.pdf (Sections 3 and 5.3, 5.6, 5.7).

The SEC Form 13F FAQ explains that a 13F Notice is filed when all reportable holdings appear on another manager's Form 13F; the notice must name the other manager(s). A 13F Combination Report is used when some holdings appear in the filer's own report and the remainder are reported by another manager. The FAQ also explains that the "Other Included Managers" list identifies managers sharing investment discretion and that Column 7 links individual holdings to their assigned manager number.

Official FAQ: https://www.sec.gov/rules-regulations/staff-guidance/frequently-asked-questions-about-form-13f (Questions 33, 34, 37 and 48).

## Implemented parser contract

The new pure-Python module research/phase605_sec_13f_manager_relationship_graph_audit.py:

1. Builds the filing-manager CIK / Form 13F file-number crosswalk from SUBMISSION + COVERPAGE within the bounded sample.
2. Keeps OTHERMANAGER as directed edge FILER_TO_REPORTING_MANAGER.
3. Keeps OTHERMANAGER2 as directed edge REPORTING_FILER_TO_INCLUDED_MANAGER.
4. Joins INFOTABLE.OTHERMANAGER sequence tokens only to OTHERMANAGER2.SEQUENCENUMBER for the same accession.
5. Normalizes common 13F file-number variants such as 028-04545, 28-4545, and 028 - 4545 to 028-04545.
6. Resolves a target by explicit CIK, or by a unique Form 13F file-number match among filers in the same sample. A non-unique file number remains ambiguous.
7. Flags explicit CIK/file-number conflicts. Names are preserved as filed but are never used as identity keys.
8. Flags missing notice rosters, notice accessions with information-table rows, duplicate/orphan table keys, malformed sequence tokens, and dangling sequence references.
9. Retains 13F-NT as a notice-only relationship event; the output always sets signal_eligible=false.

A 13F Combination Report may carry both relationship directions. The parser preserves both edges and does not collapse them into one generic manager link.

## Offline validation

The GitHub Actions workflow is deliberately offline-only for pull requests. It compiles the module and runs 16 synthetic regressions covering:

- file-number normalization;
- filer → reporting-manager direction;
- reporting-filer → included-manager direction;
- INFOTABLE sequence references, including multiple managers;
- explicit CIK/file-number conflict;
- ambiguous file-number resolution;
- no name-based fallback;
- missing notice roster;
- forbidden notice holdings rows;
- dangling and malformed sequence references;
- duplicate OTHERMANAGER and OTHERMANAGER2 keys;
- non-contiguous positive sequence numbers;
- both relationship directions in a combination report;
- REPORTTYPE / SUBMISSIONTYPE discordance;
- no zero-holdings signal from a notice.

Synthetic tests establish parser behavior only. They do not establish real-world row counts, coverage, relationship completeness, or manager identity accuracy.

## Data feasibility and limitations

- The SEC data-set specification states the structured 13F data begins in May 2013, is published quarterly, and includes filings as filed and amendments. It warns that extracted data can contain redundancies, inconsistencies, or discrepancies; original EDGAR filings remain authoritative.
- The bounded Phase 47 samples (2018 Q1 and 2026 Jun–Aug) validated SUBMISSION/COVERPAGE/INFOTABLE joins, but Phase 47 did not yet include OTHERMANAGER or OTHERMANAGER2 in its parser.
- This phase does not download or parse the actual OTHERMANAGER / OTHERMANAGER2 tables. No actual coverage percentage or edge count is claimed.
- File-number-to-CIK resolution is only considered unique within the same bounded sample. A manager may not have a filing in that sample; unresolved file numbers must remain unresolved until a broader historical roster is built.
- Form 13F file numbers are the SEC's 028- tracking identifiers. Names are not stable keys. Optional CIKs and file numbers must remain nullable.
- The current parser does not reconstruct notice-amendment roster state across quarters. It preserves each accession's as-filed edges; a separate as-of amendment treatment is required before longitudinal graph use.
- The parser does not infer actual beneficial ownership, control, trade direction, or informed behavior from manager relationships.

## Decision

**PASS for role-aware schema and relationship parsing logic only. NOT ADMITTED for live manager attribution, signal, or portfolio use.**

Next gate: run a bounded live audit against the 2018 Q1 and 2026 Jun–Aug SEC ZIPs, add OTHERMANAGER and OTHERMANAGER2 schema/row counts, verify each edge against original EDGAR cover pages, and report CIK/file-number resolution coverage separately by table and report type. Then reconstruct notice amendments as-of filing availability and compare a sample of reconstructed manager chains to source filings.

No SEC request, data purchase, vendor contact, holdings backfill, alpha test, OOS test, production change, or capital change was made. F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen. Options budget remains USD 0.
