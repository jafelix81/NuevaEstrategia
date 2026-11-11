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

## Phase 279 — SEC Insider Transactions bulk history

- SEC lists 83 quarterly archives from 2006Q1 through 2026Q3; listed ZIP sizes sum to about 887.43 MB.
- Eight documented tables include submissions, owners, transactions, holdings, footnotes and signatures.
- Critical issues: SUBMISSION has date-only FILING_DATE; NONDERIV_TRANS lacks owner CIK; transaction table lacks permanent security/CUSIP; AFF10B5ONE varies by archive era; P is not sufficient proof of open-market execution.
- Phase 279's documentation gate passed 17/17 deterministic tests, but no ZIP bytes were downloaded and no alpha test was run.
- [Phase 279 report](PHASE279_SEC_INSIDER_TRANSACTIONS_BULK_HISTORY_AND_PIT_FEASIBILITY_2026-11-11.md).

## Latest verified GitHub state

- No queued or in-progress Actions runs were found. The latest 30 workflow runs were all completed successfully.
- PR #14 head: `58f462eab1dc1268e6477118e75816dbcde0960c`; 23/23 check-runs successful. Latest Phase 278 targeted follow-up run [42969581899](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42969581899) passed 20/20 tests; artifact [13833606513](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42969581899/artifacts/13833606513).
- Phase 279 run [42969582002](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42969582002) passed 17/17 tests; artifact [13832876183](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42969582002/artifacts/13832876183).
- Phase 276 workflow security audit run [42969581729](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42969581729) succeeded. Its log reports 31 workflows, 103 action references, zero mutable/unverified refs, zero missing explicit permissions, no pull_request_target workflows, and only the main-guarded CFTC capture workflow with write permission.
- PR #13 head: `61f737f18b410bc6d85b8c56ed96bc1fd9c130f5`; open/mergeable but has zero check-runs registered on that SHA. Do not merge either PR without explicit authorization.
- Branch inventory: 134 branches. No CFTC capture was activated and no workflow was manually dispatched.

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
