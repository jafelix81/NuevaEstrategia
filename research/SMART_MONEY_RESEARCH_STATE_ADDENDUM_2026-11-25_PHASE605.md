# Smart Money Research state addendum — Phase 605 (2026-11-25 UTC)

- PASS: added a pure SEC 13F role-aware relationship parser; 18 synthetic offline regressions are included. The PR workflow is offline-only.
- Official SEC schema distinguishes OTHERMANAGER (other managers reporting for this manager) from OTHERMANAGER2 (other managers included in this report). INFOTABLE.OTHERMANAGER sequence values join to OTHERMANAGER2.SEQUENCENUMBER within the same accession. The SEC PDF's OTHERMANAGER2 key notation is inconsistent with its sequence/list design; the parser's (accession, sequence) logical key remains provisional until raw TSV validation.
- The parser preserves two directed edge types: filer → reporting manager, and reporting filer → included manager. Combination reports can carry both; the edges are not collapsed.
- Form 13F file-number normalization accepts common formatting variants; CIK/file-number conflict, ambiguous file number, dangling line reference, missing notice roster, and notice-with-holdings anomalies are flagged. Names are not used as identity.
- No live SEC dataset was downloaded in this phase. Synthetic tests do not establish actual row coverage or identity completeness. The bounded Phase 47 data samples were not extended with the two manager tables.
- Next: run a bounded free SEC dataset audit for the 2018 Q1 and 2026 Jun–Aug ZIPs, reconcile both manager tables and INFOTABLE references, then verify a stratified set against original EDGAR filings. Build an as-of notice-amendment roster state only after source reconciliation.
- 13F remains delayed quarterly ownership disclosure, not order flow or proof of informed trading; short positions are not reported, so net exposure is unavailable. No alpha/OOS/bootstrap/LOO result.
- F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen. No production, exposure, cost, parameter, or capital changes. Options budget remains USD 0.
