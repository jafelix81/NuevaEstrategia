# Smart Money Research state addendum — Phase 606 (2026-11-25 UTC)

- Opened an isolated Phase 606 branch from Phase 605 after checking the latest Actions runs, jobs, artifacts, open PRs, branches and research state. No workflow was active at the cutoff.
- Phase 605's latest run 45529146664 completed successfully; its job log confirms 18/18 synthetic tests. The report's workflow-description paragraph still says 16 tests; this is a documentation count discrepancy, not a failing test.
- Phase 605 remains schema/parser-only. Its own report explicitly requires actual TSV cardinality validation before treating (ACCESSION_NUMBER, SEQUENCENUMBER) as the OTHERMANAGER2 logical key.
- Phase 606 adds a bounded public SEC data audit for 2018 Q1 and 2026 Jun–Aug, with streamed INFOTABLE processing, actual key/cardinality counts, sequence-reference checks and SUMMARYPAGE reconciliation.
- The live audit is deliberately isolated to a push-triggered research workflow on this branch. PR validation is offline-only. No production collector or baseline is touched.
- Pending live result: research/phase606_sec_13f_manager_table_live_audit.json.
- No signal, alpha, OOS, bootstrap or LOO result is claimed. F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen; no data purchase or vendor contact; options budget USD 0.
