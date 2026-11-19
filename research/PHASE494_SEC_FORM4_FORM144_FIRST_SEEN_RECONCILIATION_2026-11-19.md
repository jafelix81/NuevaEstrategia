# Phase 494 — SEC Form 4/4-A and Form 144 scheduled first-seen reconciliation

**Audit cutoff:** 2026-11-19 02:53:16 UTC  
**Main before documentation:** `08842880f79079e102ed999bba5a7dca9dc01c69`  
**Disposition:** two SEC scheduled collectors have now delivered again after the previously observed cross-source schedule gap. The new records remain metadata-only; no signal or strategy change is authorized.

## 1. Preflight and repository state

- Default branch: `main`; repository is public and writable.
- Branches enumerated: 318 (four pages).
- Open pull requests: 57. Existing research PRs #59 (CFTC prospective bootstrap), #61 (FINRA publication clock), #44 (Cboe product/PIT reconciliation), and #37 (SEC 13D/G parent retrieval) were left untouched.
- Latest main commits before this audit:
  - `4e68c0d516d9cd1839cdead7041f797b3e27ac9a` — SEC Form 4 first-seen metadata, run 44440313382.
  - `08842880f79079e102ed999bba5a7dca9dc01c69` — SEC Form 144 first-seen capture, run 44447184058.
- The two scheduled runs and the preceding Phase 493 regression run were inspected at job, step, log and artifact level. All jobs in the two scheduled runs completed successfully; the Phase 493 PR regression passed and its live-capture job was correctly skipped. The connector does not expose a complete repository-wide Actions run-list endpoint in this session, so this report does not infer a global active-run count from those selected runs.

## 2. SEC Form 4/4-A — first bounded metadata poll after Phase 493

**Run:** [44440313382](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44440313382)  
**Poll:** 2026-11-19 01:54:11–01:54:40 UTC  
**Jobs:** `offline-regression` success; `live-capture` success.  
**Artifact:** [14489573760](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44440313382/artifacts/14489573760), 787 bytes, SHA-256 `f5c852e00f28f86371eca477cc8b5e7e06bb9d589165e1866a043212462a277a`.  
**Capture commit:** `4e68c0d516d9cd1839cdead7041f797b3e27ac9a`.

### Accession-level reconciliation

The new append-only sidecar `research/data/sec_form4_first_seen/accession_observations.csv` received 1,311 accession observations:

| Feed | Accession observations | New unique accessions |
|---|---:|---:|
| Form 4 | 1,310 | 637 |
| Form 4/A | 1 | 0 |
| **Total** | **1,311** | **637** |

For the Form 4 feed, 1,309 occurrences were inside the prior-watermark interval. They comprise 637 unique new accessions plus 672 repeated within-feed accession occurrences. There were no cross-feed duplicate occurrences. The single Form 4/A observation was its prior watermark; no new Form 4/A accession was found.

The canonical event ledger now contains 672 rows in total: the original 35 baseline accessions plus 637 new Form 4 accessions. All 637 new canonical rows are `BOUNDED_METADATA_ONLY`. Their Atom `updated` timestamps ranged from 2026-11-18 19:28:13 UTC to 2026-11-19 01:51:01 UTC, after the prior successful Form 4 poll ended at 19:26:08 UTC.

### Important path-CIK finding

Every one of the 637 new accessions appeared under more than one feed-path CIK. The distinct path-CIK multiplicity distribution was:

| Distinct path CIKs for an accession | New accessions |
|---:|---:|
| 2 | 619 |
| 3 | 10 |
| 4 | 4 |
| 5 | 2 |
| 6 | 1 |
| 9 | 1 |
| **Total** | **637** |

These are repeated accession index rows, not 672 additional filings or economic transactions. The SEC ownership XML specification separates issuer and reporting-owner CIKs and allows multiple reporting owners; SEC guidance also explains that an accession prefix is the login CIK and may be a filing agent. Therefore the path CIKs must remain locators only until each is reconciled to the filing header. The sidecar preserves every occurrence and path CIK; the canonical event row retains one deterministic path locator marked unverified.

Official references:
- [SEC Ownership XML Technical Specification](https://www.sec.gov/info/edgar/ownershipxmltechspec-v3.pdf)
- [SEC — Understand, Select and Set a Default Login CIK](https://www.sec.gov/submit-filings/filer-support-resources/how-do-i-guides/understand-select-set-a-default-login-cik)
- [SEC — Accessing EDGAR Data](https://www.sec.gov/search-filings/edgar-search-assistance/accessing-edgar-data)

**Eligibility remains fail-closed:** 637 bounded metadata events, 0 research-observation-eligible events, 0 signal-eligible events, 0 certified public-availability timestamps, and 0 transaction rows. No filing XML or submission text was downloaded. The first-seen receipt remains an upper bound, not the exact public-release time.

## 3. SEC Form 144/144-A — next successful scheduled poll

**Run:** [44447184058](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44447184058)  
**Poll:** 2026-11-19 02:50:33–02:51:04 UTC  
**Jobs:** `offline-regression` success; `live-capture` success.  
**Artifact:** [14493572408](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44447184058/artifacts/14493572408), 2,359 bytes, SHA-256 `bc2a34e61ae6d30103ab890494216bb494d4a11c500ce6f28a9753a60f28fe29`.  
**Capture commit:** `08842880f79079e102ed999bba5a7dca9dc01c69`.

- 103 new unique Form 144 accessions; 0 new Form 144/A accessions.
- 103/103 XML documents resolved.
- 103/103 acceptance timestamps reconciled from the SEC filing-detail index; 0 unresolved.
- Both feed watermarks found; pagination complete; no possible feed-window gap.
- The ledger now contains 350 unique accessions and records 12 complete polls.
- The 103 new observations cover 82 distinct issuer CIKs and 102 distinct sellers; 24 have non-empty remarks. Sixteen match the 290-CIK candidate manifest, but that manifest is not the historical F80 security master.

For all 103 new rows, Atom `updated` matched the independently stored filing-index acceptance timestamp to the second. The first-seen receipt upper bound followed acceptance by 5,401–20,990 seconds (median 18,983 seconds). This does not certify the exact public-availability time.

All 103 rows are metadata research observations under the collector's bounded-poll rule; 0 are signal-eligible. Historical F80 membership and public availability remain unverified. Same-day intraday use remains prohibited.

## 4. Cross-source schedule status

The earlier Issue #150 delivery-gap observation is now partially resolved:

- SEC Form 4/4-A has delivered a subsequent scheduled capture and advanced both feed watermarks.
- SEC Form 144/144-A has delivered a subsequent scheduled capture and advanced both feed watermarks.
- CFTC TFF's last recorded prospective capture remains run [44232546204](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44232546204), 2026-11-18 03:44:57 UTC. Its next existing weekday schedule slot is 2026-11-19 22:25 UTC; that slot had not occurred by this audit cutoff.
- FINRA Reg SHO still has no prospective ledger. Its next existing weekday slots are 2026-11-19 22:30 and 23:30 UTC; neither had occurred by this audit cutoff.

No workflow was manually dispatched, rerun, or rescheduled. Issue [#150](https://github.com/jafelix81/NuevaEstrategia/issues/150) remains open pending the CFTC and FINRA scheduled windows. Human verification is not currently required for the SEC Form 4/144 delivery paths; it may be revisited if the remaining scheduled sources miss their next windows.

## 5. Research disposition and next gates

1. Preserve the new Form 4 accession sidecar. Do not interpret within-feed repeated accession rows as separate transactions.
2. On a stratified sample, reconcile every observed Form 4 path CIK to the SGML filing header's subject issuer and reporting-owner blocks. Do not infer roles from the path or accession prefix.
3. Continue the existing Form 4 identity/transaction audits (Phases 324–346 and 439–461) rather than creating another generic parser or security-master project.
4. For Form 144, validate historical issuer/security membership and distinguish proposed sale notices from executed transactions before any event study.
5. Wait for the next scheduled CFTC and FINRA windows. No manual dispatch or cron change.
6. Do not run an event study until the identity, PIT availability, historical universe and transaction-semantics gates are satisfied.

No backtest, event study, alpha test, OOS validation, bootstrap, LOO or holdout test was run. No new signal was admitted. `F80_TOP20_PARTIAL50_BASELINE_C20` and production remain frozen.
