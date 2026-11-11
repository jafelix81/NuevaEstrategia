# Smart Money Research — current state (2026-11-11 UTC)

**Active research branch:** `phase231-cboe-option-quotes-full-row-reparse`  
**PR chain:** #14 stacked on #13; both open and unmerged.  
**Frozen baseline:** `F80_TOP20_PARTIAL50_BASELINE_C20`  
**Legacy holdout:** `CONSUMED_NOT_PRISTINE`; never reuse.  
**Economic result:** no new Smart Money signal has demonstrated incremental, cost-adjusted OOS edge.

## Latest material research result — Phase 281

SEC EDGAR's historical daily `form.YYYYMMDD.idx` archives provide a conditional route to reconstruct a conservative daily public-dissemination date for Form 4 accessions. SEC documentation says daily indexes extend from 1994Q3 to present, list form/CIK/date/path, are built nightly, and prior daily indexes are not rewritten by later-business-day post-acceptance corrections. Full and quarterly indexes are rebuilt weekly and do incorporate later PAC changes.

**Proposed Form 4 knowledge clock:** join each Phase 279 bulk-dataset accession to all historical daily form-index sightings; use the earliest verified index date; execute no earlier than the close of the next full XNYS session. Do not fall back to FILING_DATE or acceptance time when the index join is missing. This is a conservative daily-PIT candidate, not yet strict PIT: no raw index bytes have been downloaded, same-day PAC handling is not fully measured, the SEC does not publish an exact first-public timestamp, and owner/security identity remain open.

- [Phase 281 report](PHASE281_SEC_DAILY_INDEX_FIRST_PUBLICATION_PIT_FEASIBILITY_2026-11-11.md)
- Official sources: [SEC EDGAR access and daily indexes](https://www.sec.gov/search-filings/edgar-search-assistance/accessing-edgar-data), [SEC timestamp FAQ](https://www.sec.gov/about/webmaster-frequently-asked-questions).



## Phase 282 — SEC PDS public-clock adjudication

The SEC's current PDS system page says PDS is a paid subscriber service and that, following the 2025-05-19 system update, filings are available on sec.gov before they are made available to PDS subscribers. The inspected historical 2014 PDS specification documents EDGAR receipt/acceptance/build fields and PAC timestamps, but ordinary `.dissem` files and the daily EOD filename list do not provide a per-filing first-public timestamp. The 2014 specification is not assumed to represent every field in the current 2025 ZIP.

**Decision:** PDS is not a superior public-availability clock and no paid subscription/contact is justified. Retain the Phase 281 historical daily `form` index as the primary conservative Form 4 knowledge-date candidate; PDS may be only an optional acceptance/PAC cross-check if lawful existing archive bytes become available. No PDS or SEC raw bytes were downloaded, no automated SEC request was sent, and no alpha test was run.

- [Phase 282 report](PHASE282_SEC_PDS_VS_DAILY_INDEX_PUBLICATION_CLOCK_AUDIT_2026-11-11.md)
- Official SEC source: [PDS system and 2025 ordering change](https://www.sec.gov/oit/announcement/public-dissemination-service-system-contact.html).

## Phase 279 — SEC Insider Transactions bulk history

- SEC lists 83 quarterly archives from 2006Q1 through 2026Q3; listed ZIP sizes sum to about 887.43 MB.
- Eight documented tables include submissions, owners, transactions, holdings, footnotes and signatures.
- Critical issues: SUBMISSION has date-only FILING_DATE; NONDERIV_TRANS lacks owner CIK; transaction table lacks permanent security/CUSIP; AFF10B5ONE varies by archive era; P is not sufficient proof of open-market execution.
- Phase 279's documentation gate passed 17/17 deterministic tests, but no ZIP bytes were downloaded and no alpha test was run.
- [Phase 279 report](PHASE279_SEC_INSIDER_TRANSACTIONS_BULK_HISTORY_AND_PIT_FEASIBILITY_2026-11-11.md).

## Latest verified GitHub state — 2026-11-11 08:05 UTC

- Latest 100 Actions runs: **97 success, 3 cancelled, 0 failed, 0 queued/in-progress**. No workflow was duplicated.
- PR #14 head: `816662c125d626542763a1d0d034e3aaf6cd8119`; **23/23 check-runs successful**. It remains open, mergeable and stacked on PR #13. [PR #14](https://github.com/jafelix81/NuevaEstrategia/pull/14).
- PR #13 head: `61f737f18b410bc6d85b8c56ed96bc1fd9c130f5`; open/mergeable, with **zero check-runs registered on that SHA**. [PR #13](https://github.com/jafelix81/NuevaEstrategia/pull/13).
- Latest Phase 272 hosted run [42982871024](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42982871024) passed. The job log preserves the Phase 272 status gate; metadata-only artifact [13838231849](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42982871024/artifacts/13838231849), SHA-256 `459cea1eb615d83efb618310ff15d63a5fd655cddfe3df7b29934c31d566877d`.
- Latest Phase 278 targeted follow-up [42982870960](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42982870960) passed **20/20 tests** and re-fetched 147,725 rows over 30 pages. Two BQ/T2 candidate-key groups remain conflicting; no row was selected or summed. Artifact [13838767377](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42982870960/artifacts/13838767377), SHA-256 `22cfdeaed6616d487bf403d459a0778b5f5a86516c30656a1ea1bda5235179e8`.
- Phase 279 bulk-history gate passed 17/17 on the current PR head; Phase 276 security gate passed. The 31-workflow / 103-action inventory still has no mutable/unverified action refs or missing explicit permissions.
- Branch inventory: **134 branches** (100 on page 1, 34 on page 2). No CFTC capture was activated and no workflow was manually dispatched.
- No PR was merged. Do not merge either PR without explicit authorization.

## Source dispositions

| Source / line | Current disposition |
|---|---|
| FINRA short flow Phase 20C | Weak, incomplete and not strict PIT; no promotion; do not retune the consumed sample |
| FINRA short interest Phase 267 | Pagination/date-availability defects; no strict PIT panel |
| FINRA ATS/OTC Phases 264/277/278 | Context-only; later revisions and two unresolved duplicate-grain conflict groups; do not sum or choose arbitrarily |
| SEC Form 4 | Highest-priority historical candidate after Phase 281 daily-index route; owner attribution and effective-dated security identity still open |
| SEC 13D/G | Extensive event, amendment and identity audits; no broad issuer/security panel admitted |
| SEC 13F / N-PORT | Delayed context only; acceptance, amendment, CUSIP/security mapping and PIT issues remain |
| Form 144/Form 4 | Document-linkage and conditional placebo results only; no market-execution or return edge established |
| Cboe Open-Close | One C1 20% EOD sample date reprocessed; feature construction works, but no multi-date PIT/vintage proof |
| Cboe options quotes / sentiment / TradeFlow / OI | Conditional candidates; no full licensed historical sample with first-receipt and effective-dated identity admitted |
| CFTC BPR/TFF | Market-regime context candidate; prior walk-forward quarantined for label-maturity defects; prospective capture workflow remains research-branch only |
| Form SHO / SLATE | Future regulatory sources only; not a current historical public panel |

## Next research gates

1. Configure the authorized GitHub Actions secret `SEC_CONTACT_EMAIL` before automated SEC retrieval. Do not guess an address or send programmatic requests without the declared User-Agent.
2. Run the Phase 281 sample gate across the six Phase 279 quarters: download only the needed daily `form` index files, validate accession/path parsing, preserve hashes, and reconcile sampled index dates with acceptance headers and original Form 4/Form 4/A content.
3. Measure missing-index, duplicate-sighting, same-day PAC, missing-content and after-hours rates. Test Oldloads only as a targeted fallback; do not bulk-download all daily Oldloads archives.
4. Resolve joint/group transaction-owner attribution and effective-dated issuer/security-class identity, including inactive/delisted names.
5. Only after all data gates pass, preregister a new chronological test against frozen LTM/F80 with identical exposure/costs, label-maturity embargo, date/issuer/owner-clustered bootstrap, LOO and multiplicity controls. Use a new prospective holdout.

## Controls

No returns, alpha, economic optimization, bootstrap/LOO or fresh independent OOS evidence has been produced by Phases 279–281. No holdout was used. No vendor was contacted, no data purchased, no terms accepted, no PR merged, no production/universe/capital/parameter changes, and no F80 change occurred. No CAGR target or minimum/maximum holding period is imposed.


## Phase 283 — SEC daily-index parser contract (2026-11-11)

Implemented an offline parser/ledger for the conditional Phase 281 SEC daily-index route. It validates Form 4/Form 4-A accession paths, CIK consistency, filing-date/index-date consistency, duplicate/conflicting rows, multi-date accession sightings and the next full XNYS session close using timezone-aware calendar inputs. Synthetic tests are wired into the existing PR workflow. No SEC requests or raw index downloads were made; live format/PAC validation, six-quarter joins, owner attribution and effective-dated security identity remain open. See research/PHASE283_SEC_DAILY_INDEX_PARSER_CONTRACT_2026-11-11.md.

## GitHub verification correction — 2026-11-11 10:35 UTC

- Latest 100 Actions runs: 97 successful, 3 cancelled, 0 failed and 0 queued/in-progress. The three cancellations were Phase 258, Phase 259 and Phase 260; no active run was duplicated.
- PR #14 remains open/mergeable and stacked on PR #13. Before Phase 283 files are added, its head is 1f33ecb237521e4dda9101f1742862c2f18f2bb5; the 22 registered check-runs on that SHA all completed successfully.
- PR #13 remains open/mergeable with zero check-runs registered on head 61f737f18b410bc6d85b8c56ed96bc1fd9c130f5.
- Latest Phase 231 raw-row reparse run 42987915103 passed. Metadata-only artifact 13839449799, SHA-256 8127533c1d1fc1835cf6ef7718a2558b0fb6787fc1f8d6900af3e982ee86aa65.
- Phase 279 passed 17/17 tests in run 42987914989; artifact 13840302271, SHA-256 13be9e426f464d15a3d2135148c5df87de9b2685e2390b19da5565a655938b4d.
- Phase 278 passed 20/20 tests and reconciled 147,725 rows / 30 pages in run 42982870960; its two unresolved duplicate-grain conflict groups remain quarantined. Artifact 13838767377, SHA-256 22cfdeaed6616d487bf403d459a0778b5f5a86516c30656a1ea1bda5235179e8.
- Phase 272 passed in run 42982871024; artifact 13838231849, SHA-256 459cea1eb615d83efb618310ff15d63a5fd655cddfe3df7b29934c31d566877d.
- Branch inventory is 134 branches (100 on page 1, 34 on page 2). No PR was merged; F80, production, universe, capital and holdout remain unchanged.

Phase 283 is an offline parser contract only. Do not describe parser tests as passing until the final PR workflow run is inspected.


## Phase 283 refinement — delayed Form 4 index-date handling (2026-11-11)

A code review found that the original parser required `Date Filed == form.YYYYMMDD.idx`, making its advertised multi-date accession ledger unreachable for a later daily-index sighting. This was too strict for the SEC's documented next-business-day dissemination of some Forms 3/4/5 filed after 10 p.m. ET.

The parser now quarantines only index dates before `Date Filed`, retains later index sightings with explicit lag days, and never backdates a later-only sighting to FILING_DATE. Synthetic tests cover the delayed sighting, multi-date aggregation and no-backdating rule. Raw SEC bytes, actual late-sighting frequency and PAC behavior remain unverified.

This is a data-contract correction, not a new source or alpha result. SEC_CONTACT_EMAIL remains unconfigured; no SEC request was made. F80 and all production/holdout controls remain unchanged.


## Phase 284 — SEC delayed-sighting correction (2026-11-11)

The daily-index ledger now retains later index sightings of a Form 4 accession with explicit lag days and never backdates a later-only sighting to FILING_DATE. Synthetic regression suite passed 17/17 in run 43019575009; artifact 13855150143. Real SEC bytes/PAC behavior remain unverified. No SEC request was made.

## Phase 285 — FIS SLD and UREF source admission (2026-11-11)

Documented FIS Astec Securities Lending and Nasdaq UREF as candidates/controls, not admitted signals. Run 43030407555: 13/13 metadata-audit tests passed; artifact 13859064142. No data was purchased or downloaded.

## Phase 286 — Nasdaq NOTO/NOP feasibility (2026-11-11)

Documented NOTO EOD/intraday and NOP as options-flow candidates. Run 43031307177: 12/12 metadata-audit tests passed; artifact 13860368810. NOTO is one exchange only; participant classes are not beneficial-owner identities; intraday snapshots are cumulative. No data was purchased or downloaded.

## Phase 287 — Nasdaq ISE/PHLX options and TotalView-ITCH/NOII feasibility (2026-11-11)

Added research/PHASE287_NASDAQ_OPTIONS_TRADE_OUTLINE_AND_ITCH_NOII_FEASIBILITY_2026-11-11.md on branch phase287-nasdaq-options-and-itch-source-feasibility (documentation-only commit c4ace566a871c0b6b042da46ea46e3b1e761e09d). ISE Trade Outline EOD has history from Jan 2006 but the full-history ad-hoc cost is approximately $150,000 at current list rates; a first-time one-month EOD trial is documented. PHLX PHOTO history begins Jan 2009, with a free Jan-Jun 2014 sample formally documented but current retrieval path unverified. Nasdaq TotalView-ITCH/NOII offers high-resolution order/auction microstructure, but full SFTP access requires credentials, files are large, the public archive is sparse samples, and MPID attribution is partial. No raw sample was obtained, no subscription/contact/purchase was made, and no model test was run.

## Current verification — 2026-11-11 14:24 UTC

- PR #14 remains open/mergeable at head 6dedb088d7289ca5155a319b5f88155c2d431be3. Its 23 associated GitHub Actions runs are all completed successfully; no queued/in-progress run was found. The latest Phase 285 run completed 13/13 tests and its artifact 13859064142 is present and unexpired.
- Phase 286 run 43031307177 completed successfully with one metadata-audit job and artifact 13860368810 present and unexpired.
- PR #13 remains open/mergeable at head 61f737f18b410bc6d85b8c56ed96bc1fd9c130f5 with zero associated workflow runs/check-runs on that SHA.
- Phase 287 branch exists; no PR was opened and no merge was performed.
- SEC_CONTACT_EMAIL remains unconfigured; no SEC request was made. No Nasdaq trial, data purchase, or vendor contact was initiated.
- No raw new source data, return test, alpha, bootstrap/LOO or independent OOS result has been produced by Phases 284–287. F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen; production, universe, capital, parameters and holdout are unchanged. No CAGR target or holding-period constraint is imposed.


## Phase 288 — SEC Form 13F PIT feasibility (2026-11-11)

Added research/PHASE288_SEC_13F_HOLDINGS_PIT_COVERAGE_AMENDMENT_AUDIT_2026-11-11.md on branch phase288-sec-13f-pit-coverage-amendment-audit (report commit 84db69351977302c10f2721796e4f552696c1a4b). SEC 13F structured data is public/free, with quarterly packages from 2013 Q2 / July 2013 through August 2026. It includes accession numbers, filing date/type, CIK, report period, amendment/restatement/addition flags, confidential-treatment metadata, CUSIP, optional FIGI, shares/value, put/call and manager-discretion fields. It is a promising slow-frequency ownership source, but only a candidate: 45-day reporting lag, no shorts, incomplete Section 13(f) universe, confidential omissions, amendments, and CUSIP/FIGI mapping require strict PIT reconstruction. SEC Q3 2026 filings are due 2026-11-16; no Q3 holdings are available as of this run. No raw ZIP bytes were obtained because the runtime cannot resolve external SEC hosts; SEC_CONTACT_EMAIL remains unconfigured. No backtest or signal test was run.

## Current verification — 2026-11-11 14:24 UTC

- PR #14: head 6dedb088d7289ca5155a319b5f88155c2d431be3; 23 associated Actions runs, all completed successfully; no active run was found.
- Phase 285 run 43030407555: metadata-audit job succeeded, 13/13 tests; artifact 13859064142 present and unexpired.
- Phase 286 run 43031307177: metadata-audit job succeeded, 12/12 tests; artifact 13860368810 present and unexpired.
- PR #13: head 61f737f18b410bc6d85b8c56ed96bc1fd9c130f5; zero associated workflow runs/check-runs.
- Phase 287 and Phase 288 are documentation/source-audit branches only; no PRs were opened and no merges were made. No workflow was started by these documentation commits.
- No raw data was acquired from FIS, UREF, NOTO, ISE, PHLX, NYSE Open-Close, Nasdaq ITCH/NOII or SEC 13F. No vendor was contacted and no paid data/trial was requested.
- SEC_CONTACT_EMAIL remains the only previously identified human configuration blocker for automated SEC downloads. No SEC request was made.
- No model test, alpha estimate, bootstrap, LOO or independent OOS result has been produced by Phases 284–288. F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen; production, universe, capital, parameters and holdout are unchanged.


## Phase 289 — SEC 13F re-entry decision and source-priority correction (2026-11-11)

**Decision: keep 13F parked for broad-universe stock selection; defer raw ZIP acquisition until historical identity coverage improves.** Phase 22C already found only 301 current candidate mappings for the 335-name frozen universe. Its historical matches were 212/301 (70.43%) in 2016Q1, 246/301 (81.73%) in 2020Q1 and 280/301 (93.02%) in 2024Q1. Against the full 335-name universe these are 63.28%, 73.43% and 83.58%, respectively. The direct report-date CUSIP/common-equity route had a 54.8% minimum in 2016Q1. Phase 166's 83.18% is a 13(f)-eligibility match in a separate 13D/G sample, not 13F holdings coverage.

Phase 205's ten accessions are purposive edge cases, not a prevalence sample: four original reports were accepted 44–48 days after quarter-end; six amendments were 60–1,137 days after quarter-end (median 361.5 days); five of ten filing dates differ from acceptance calendar dates. The findings reinforce accession-level event clocks and append-only restatement/add-only amendment state, but do not establish population rates or alpha.

Source priority remains: (1) Form 4 bulk + daily-index real-data sample; (2) N-PORT direct short-equity sample as a distinct preregistered registered-fund hypothesis; (3) 13F only after effective-dated security identity and broad-universe coverage pass; (4) paid options/lending sources only after authorized sample/license and cost gates. No synthetic 13F workflow should be added until real bytes reveal a concrete issue.

- [Phase 289 report](PHASE289_SEC_13F_REENTRY_DECISION_AND_SOURCE_PRIORITY_2026-11-11.md) on branch `phase289-sec13f-reentry-adjudication`.
- Latest 30 Actions runs checked: 24 completed successfully, 6 cancelled, zero failed, zero queued/in-progress. Latest run 43031307177 (Phase 286) succeeded; its metadata-only artifact 13860368810 is present and unexpired. No workflow was duplicated.
- PR #14 head remains `6dedb088d7289ca5155a319b5f88155c2d431be3`, open/mergeable, 23/23 check-runs successful. PR #13 head `61f737f18b410bc6d85b8c56ed96bc1fd9c130f5`, open/mergeable, zero check-runs on that SHA.
- Phase 278 latest targeted run 43030407560 passed 20/20 tests but still found 147,725 rows, 30 pages and two conflicting duplicate-grain groups; no rows were selected or summed. Artifact 13861545967 is present and unexpired.
- Phase 231 run 43030407294 passed the raw-row reparse gate: 115,617 populated rows; 112,313 unambiguous valid rows; 3,304 ambiguous expiration rows quarantined. No PIT or alpha admission. Artifact 13860267856 is present and unexpired.
- Branch inventory before this Phase 289 branch was 137 (100 on page 1, 37 on page 2); Phase 289 adds one documentation-only branch. No PR or merge was created.
- The repository state records `SEC_CONTACT_EMAIL` as not configured; no secret was inspected or changed and no SEC request was made.

No raw data, return test, bootstrap/LOO, OOS result or holdout use occurred. F80, production, universe, capital and parameters remain unchanged. The legacy holdout remains consumed and unavailable for reuse.


## Phase 290 — N-PORT / FINRA output reconciliation (2026-11-11)

- Inspected the actual Phase 27O run 39493106882 and artifact 12296499022 (SHA-256 `c8207cd99b5bc80be730db89da62ced1298a18af0330b11335e41864fca4478b`). All eight snapshots have blank `balance_units`, zero tickers with positive shares, and all seven transitions have `n_ranked=0` with no forward returns. This confirms the Phase 247 `UNITS` versus official flattened `UNIT` defect in the real historical output. Quarantine Phase 27N/27O; this is not evidence for or against long accumulation alpha.
- The Phase 27O/27K scripts hard-code `research@example.com` in the SEC User-Agent. Phase 27O logs confirm that eight SEC archives were downloaded historically. Do not reuse that placeholder. No new SEC request was sent; automated SEC retrieval remains blocked until an actual authorized contact is configured in `SEC_CONTACT_EMAIL`.
- Reconciled Phase 20C run 40098425254 / artifact 12562171831 (SHA-256 `c15f75340bdedfbb37c82f79bb563a450dd1da11989d09e18bb745d93b7d3a5c`). All 1,382 XNYS sessions required by the run's signal lookback windows had FINRA CNMS files; the 638 HTTP 403 dates were weekends, XNYS closures or pre-source-start dates, not a 31.6% trading-session gap.
- Phase 20C's 12 pseudo-OOS dates compare four blocked and four replacement names per date. Mean replacement-minus-blocked: +0.141% (5D), -1.686% (10D), -0.858% (20D); positive dates 5/12, 3/12 and 5/12. Factor/direction selection is unstable. All exploratory date-level 95% intervals cross zero; no costs or cluster bootstrap/LOO were included.
- Phase 20C uses same-day FINRA data and starts forward returns at the same day's close without a verified first-public timestamp. Treat as not strict PIT; no promotion. Any revisit must enter no earlier than the next full XNYS session unless source receipt timing is proven.
- Phase 278 remains context-only: 147,725 rows, 30 pages and two unresolved conflicting duplicate-grain groups; do not sum or select those groups.
- Current Actions verification: latest 100 runs = 67 success, 33 cancelled, zero failed and zero active/queued. PR #14 remains open/mergeable with 23/23 checks successful; PR #13 remains open/mergeable with zero checks on its current SHA. Branch count was 138 before this Phase 290 branch; this documentation branch makes 139. No PR was opened or merged.
- [Phase 290 report](PHASE290_NPORT_FINRA_OUTPUT_RECONCILIATION_2026-11-11.md).

**Current decision:** Form 4 remains the first real-data priority after a valid SEC contact is configured; N-PORT direct-short remains a separate, unadmitted hypothesis; 13F remains parked; Phase 20C is not promoted pending next-session PIT correction and a stronger test. No holdout was used. F80, production, universe, capital and parameters remain unchanged.


## Phase 291 — N-PORT direct-short real public-filing positive control (2026-11-11)

A public SEC NPORT-P filing (accession 0001145549-24-071567; CIK 0001872253; series S000074017, Cromwell Long Short Fund) was inspected. It reports at least three explicit short U.S. common-equity positions: DAY (-4,447 shares), CLX (-1,920) and CDW (-1,115), each with negative USD value and negative percent of NAV. The filing was accepted 2024-11-22 12:10:57 ET for report date 2024-09-30; the conservative first full XNYS session after acceptance is 2024-11-25.

This exposed a real Phase 221 parser false-negative: the code required the descriptive ISSUER_TITLE to contain the literal words "Common Stock". The SEC filing uses issuer names such as "Dayforce Inc", while the structured fields identify the instrument as Equity-common / Corporate. The classifier now uses UNIT=NS + ASSET_CAT=EC + ISSUER_TYPE=CORP and leaves the title as descriptive metadata; non-finite balances fail closed. The old predicate rejected 3/3 actual rows; the corrected logic accepts 3/3. The 13 existing Phase 221 semantic cases were rechecked and pass; new tests cover the three real public rows and negative controls.

Important limit: the public SEC filing detail and EDGAR-rendered primary document were inspected, but raw XML/ZIP bytes were not downloaded or hashed. This validates a real filing row-classification path, not bulk-history coverage, series/security longitudinal identity, a PIT panel, or alpha. No return test, bootstrap/LOO, or holdout was run. SEC_CONTACT_EMAIL remains unconfigured; no automated SEC request was made.

- [Phase 291 report](PHASE291_NPORT_DIRECT_SHORT_PUBLIC_FILING_POSITIVE_CONTROL_2026-11-11.md) on branch `phase291-nport-public-short-positive-control`.
- Latest Actions inventory before this branch: 100 most recent runs = 67 success, 33 cancelled, zero failed, zero active/queued. PR #14 head 6dedb088d7289ca5155a319b5f88155c2d431be3 has 23/23 successful check-runs; PR #13 head 61f737f18b410bc6d85b8c56ed96bc1fd9c130f5 has zero check-runs. Phase 286, 285 and 278 logs/artifacts were inspected; all metadata/source-gate jobs succeeded but did not admit data or alpha. This new branch is documentation/parser correction only; no workflow was started.
- No PR opened or merge made. F80, production, universe, capital, parameters and holdout remain unchanged.


## Phase 292 — N-PORT direct-short classifier hardening (2026-11-11)

A review found the Phase 291 predicate did not fully preserve the preregistered Phase 219 row filter: it omitted U.S. investment-country validation, negative CURRENCY_VALUE/PERCENTAGE sign concordance, and row-level exact CUSIP/ISIN matching. The Phase 291 test commit used [skip ci] and had zero check-runs. Phase 292 adds these fail-closed gates, updates the 13 Phase 221 semantic fixtures, replays the three manually transcribed public SEC filing rows with all required fields, and adds five negative controls. A dedicated offline Actions workflow compiles/runs the tests and emits a metadata-only artifact. This remains a public rendered-document fixture, not raw XML parsing or a bulk-data/PIT admission.

- [Phase 292 report](PHASE292_NPORT_DIRECT_SHORT_CLASSIFIER_HARDENING_2026-11-11.md) on branch phase292-nport-short-classification-hardening.
- No SEC requests, raw bytes, hashes, return tests, bootstrap/LOO or holdout use. F80, production, universe, capital and parameters remain unchanged.
