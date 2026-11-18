# Smart Money Research state addendum — Phase 485 (2026-11-18)

- New source-level confirmation: SEC accession index-header 0000895421-24-000178 explicitly separates SUBJECT COMPANY CIK 0001793855 (abrdn Global Infrastructure Income Fund) from FILED BY CIK 0000895421 (Morgan Stanley), and gives acceptance timestamp 20240212095001. Official source: https://www.sec.gov/Archives/edgar/data/1793855/000089542124000178/0000895421-24-000178-index-headers.html.
- Implemented a pure offline SEC-HEADER parser that separately reads SUBJECT COMPANY and FILED BY blocks, validates both CIKs, cross-checks FILED BY CIK against the accession prefix, and refuses to infer ticker. Missing/duplicate/mismatched blocks fail closed.
- Added 8 unit tests and an offline-only workflow. Final push run [44356862612](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44356862612) passed 8/8 tests. Two earlier intermediate push commits failed while the workflow/test files were being added; the final head passed. No live SEC requests, raw filings, prices or artifacts.
- PR #146 merged into main at 2026-11-18 17:17 UTC; merge commit: a178aeeba06fef53ac6c61b0589d33ead540eb41.
- Phase 28D/35 remains quarantined until all 20,266 accessions are reprocessed with the SEC index-header identity blocks and an effective-dated CUSIP/security master. This parser is a building block, not a full panel rebuild or signal.
- F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen; no backtest/OOS/bootstrap/LOO.
