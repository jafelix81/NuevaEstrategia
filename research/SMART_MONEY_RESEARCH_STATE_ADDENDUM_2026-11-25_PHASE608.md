# Smart Money Research state addendum — Phase 608 (2026-11-25 UTC)

- Phase 608 group-aware SEC 13F parser implemented; 11/11 offline regressions passed in run 45532947764; artifact 14985222973 uploaded.
- OTHERMANAGER2 rows are preserved as group members; SEQUENCENUMBER identifies a group and may repeat across member rows.
- INFOTABLE references attach to groups only. Multi-member groups are marked GROUP_ONLY; no individual manager attribution is inferred.
- Zero sentinels, nonnumeric as-filed labels, numeric group references and unmatched numeric references are separate states.
- Summary-page counts reconcile to member rows, not distinct groups.
- Phase 606 repeated accession/sequence pairs are not automatically duplicate data; source XML shows they can be intentional group members. Nonnumeric labels are not automatically malformed.
- Full-quarter TSV integration, as-of amendment state and historical security master remain pending.
- No alpha/OOS, bootstrap/LOO, production or capital change. F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen; options budget USD 0.
