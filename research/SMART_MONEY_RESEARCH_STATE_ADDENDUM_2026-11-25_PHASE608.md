# Smart Money Research state addendum — Phase 608 (2026-11-25 UTC)

- Phase 608 implements the corrected SEC 13F sequence-group data model, based on source-confirmed Phase 607 findings.
- OTHERMANAGER2 rows are preserved as group members; SEQUENCENUMBER identifies a group and may repeat.
- INFOTABLE references attach to groups only. Multi-member groups are marked GROUP_ONLY; no individual manager attribution is inferred.
- Zero sentinels, nonnumeric as-filed labels, numeric group references and unmatched numeric references are separate states.
- Summary-page counts reconcile to member rows, not distinct groups.
- Offline fixtures model Allspring's 5-member / 2-group structure, 12-member sequence groups, unmatched refs, XXEC, INC. raw label, zero sentinel and exact duplicate member rows.
- Full-quarter TSV integration, as-of amendment state and historical security master remain pending.
- No alpha/OOS, bootstrap/LOO, production or capital change. F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen; options budget USD 0.
