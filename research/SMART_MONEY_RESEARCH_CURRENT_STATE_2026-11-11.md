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
