# Phase 608 — SEC 13F sequence-group graph parser

<badge>CI: 11/11 offline regressions passed</badge>

**Status:** group-aware structural parser implemented and tested.  
**Run:** https://github.com/jafelix81/NuevaEstrategia/actions/runs/45532947764  
**Artifact:** https://github.com/jafelix81/NuevaEstrategia/actions/runs/45532947764/artifacts/14985222973  
**Basis:** source-confirmed Phase 607 XML evidence from six accessions.  
**Scope:** group-aware parser for OTHERMANAGER2 member rows and INFOTABLE group references. No full-quarter live dataset rebuild.

## Data model

Phase 607 established that SEQUENCENUMBER identifies a group, not a unique manager member. Multiple OTHERMANAGER2 rows can intentionally share one sequence number. INFOTABLE.OTHERMANAGER references that sequence group.

Phase 608 implements:
- Accession → sequence group → member rows.
- A row-level member key that preserves exact duplicate rows rather than silently dropping them.
- Member identity quality based on explicit CIK / Form 13F file number; names alone are not identity keys.
- Position references attached to groups, with member count and attribution status.
- Group-only attribution whenever the sequence group has multiple member rows.
- Unmatched numeric references retained as unresolved.
- Zero sentinel separated from nonnumeric as-filed text.
- Nonnumeric values such as “XXEC, INC.” preserved as one raw label; comma-separated names are not split into pseudo-identifiers.
- Summary-page included-manager counts reconciled to member-row counts, not distinct group counts.

## Regression coverage

11 offline tests passed. Fixtures cover:
- Allspring's five member rows under sequence groups 1 and 2.
- A 12-member sequence group pattern.
- Unmatched numeric references.
- Nonnumeric labels and mixed numeric/text values.
- Zero sentinel.
- Exact duplicate member rows preserved and flagged.
- Summary-page count reconciliation.
- No name-only identity resolution.

The CI structural demo produced five member rows, two groups, two multi-member groups, four matched group-reference tokens, two raw nonnumeric labels, one zero sentinel, and zero summary-page mismatches.

## Phase 606 / 607 interpretation correction

The repeated (ACCESSION_NUMBER, SEQUENCENUMBER) rows are not automatically duplicate data. Source XML proves that the same sequence number can be assigned to several member rows within one group. Therefore:
- Sequence number is a group identifier, not an individual-manager key.
- The 20 / 3 repeated sequence pairs in Phase 606 must be reclassified as group membership patterns unless exact member-row duplication is independently demonstrated.
- Nonnumeric values such as “XXEC, INC.” and “Wellesley” are as-filed text values, not automatically malformed identifiers.
- The group is the finest attribution unit supported by the field. A multi-member group cannot support individual-manager attribution.

## Limits and next gate

This phase is offline-only and fixture-driven. It has not yet been run over the full 2018 Q1 / 2026 Jun–Aug TSV datasets. Before any 13F signal work:
1. Integrate the group graph with actual SEC TSV ingestion.
2. Reconcile member rows and group references to source XML across a larger stratified sample.
3. Add as-of filing-acceptance timestamps and amendment state.
4. Build effective-dated security identity coverage for F80.
5. Test group-level ownership measures only, against frozen F80/LTM with chronological OOS and identical exposure/costs.

No alpha, OOS, bootstrap, LOO, production or capital result is claimed. F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen. Options budget USD 0.
