# Phase 608 — SEC 13F sequence-group graph parser

**Status at branch creation:** implementation and offline regression pending.  
**Basis:** source-confirmed Phase 607 XML evidence from six accessions.  
**Scope:** group-aware parser for OTHERMANAGER2 member rows and INFOTABLE group references. No full-quarter live dataset rebuild.

## Data model

Phase 607 established that SEQUENCENUMBER identifies a group, not a unique manager member. Multiple OTHERMANAGER2 rows can intentionally share one sequence number. INFOTABLE.OTHERMANAGER references that sequence group.

Phase 608 implements:
- Accession → sequence group → member rows.
- A stable row-level member key that preserves exact duplicate rows rather than silently dropping them.
- Member identity quality based on explicit CIK / Form 13F file number; names alone are not identity keys.
- Position references attached to groups, with member count and attribution status.
- Group-only attribution whenever the sequence group has multiple member rows.
- Unmatched numeric references retained as unresolved.
- Zero sentinel separated from nonnumeric as-filed text.
- Nonnumeric values such as “XXEC, INC.” preserved as one raw label; comma-separated names are not split into pseudo-identifiers.
- Summary-page included-manager counts reconciled to member-row counts, not distinct group counts.

## Regression coverage

The fixtures cover the source-confirmed Allspring pattern (five member rows under sequence groups 1 and 2), a 12-member sequence group, unmatched numeric references, nonnumeric labels, zero sentinel, exact duplicate rows, and summary-page reconciliation.

The parser is a pure transformation layer. It does not infer beneficial ownership, control, individual decision-maker, trading direction, or alpha.

## Limits and next gate

This phase is offline-only and fixture-driven. It has not yet been run over the full 2018 Q1 / 2026 Jun–Aug TSV datasets. Before any 13F signal work:
1. Integrate the group graph with actual SEC TSV ingestion.
2. Reconcile member rows and group references to source XML across a larger stratified sample.
3. Add as-of filing-acceptance timestamps and amendment state.
4. Build effective-dated security identity coverage for F80.
5. Test group-level ownership measures only, against frozen F80/LTM with chronological OOS and identical exposure/costs.

No alpha, OOS, bootstrap, LOO, production or capital result is claimed. F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen. Options budget USD 0.
