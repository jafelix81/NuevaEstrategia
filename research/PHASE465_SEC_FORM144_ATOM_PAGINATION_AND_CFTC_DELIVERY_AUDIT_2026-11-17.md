# Phase 465 — SEC Form 144 Atom pagination and CFTC delivery audit

**Audit time:** 2026-11-17 22:47 UTC  
**Main HEAD at preflight:** `70112e777fa789aae8880c7be90c371988a054c5` (Phase 464 merged)  
**Disposition:** add fail-closed Atom pagination; preserve the SEC 144 gap until the prior accession is found; CFTC's Nov 17 scheduled first-receipt capture is not present in Actions. No signal or strategy change.

## 1. Preflight and no-duplicate check

- Latest main commit: `70112e777fa789aae8880c7be90c371988a054c5`.
- Actions total: 7,719; latest 100 runs completed; explicit in-progress and queued queries both returned 0.
- Latest runs: SEC Phase 464 PR CI [44184610040](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44184610040) succeeded; latest scheduled SEC capture [44179257367](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44179257367) succeeded.
- Branches: 297 across three pages; open PRs: 56; workflow files: 76.
- No workflow was dispatched, rerun or duplicated. No active run was found.

## 2. Reconciled Phase 464 production capture

Downloaded and inspected artifact [14371301851](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44179257367/artifacts/14371301851), ZIP SHA-256 `e1e1baa44b99eef37cbb2f31494ca6cd00ed2d30f1b663f0eb8591a407db7142`.

The artifact confirms:

- Phase 454 migrated 52 existing rows from 41 to 43 columns before capture.
- 54 new filing-version rows and 58 feed-observation rows were appended.
- 54/54 XML records and SEC filing-detail acceptance timestamps reconciled.
- 14 current 290-CIK diagnostic matches occurred only in the gap-contaminated Form 144 feed.
- Four bounded Form 144/A amendment versions were observed; all have explicit parent accessions.
- Four raw filing-version observations passed the existing interval gate, but 0 are signal-eligible, 0 have certified public-availability timestamps, 0 have historical F80 membership verified, and 0 are authorized for same-day intraday use.

Feed-level results:

| Feed | Raw entries | New accessions | Prior watermark | Decision |
|---|---:|---:|---|---|
| Form 144 | 50 | 50 | Not found | Gap quarantine |
| Form 144/A | 8 | 4 | Found | Four bounded amendment versions |

The Form 144 response covered 19:44:42–21:21:49 UTC and omitted prior accession `0001950047-26-011102`. Its 50 new accessions therefore remain unbounded. Form 144/A's four new accessions are amendments, not four independent proposed-sale events.

Committed ledger after the run: 106 event rows, 388 feed-observation rows and 106 acceptance reconciliations. The state file records run 44179257367 as the latest successful poll and preserves `last_poll_possible_gap_by_feed["144"]=true`.

## 3. Pagination feasibility and implementation

An independent technical walkthrough dated 2026-10-26 documents EDGAR Latest Filings Atom pagination through `start`, a maximum of 100 entries per page, and duplicate role rows for a single accession. It recommends paging until the prior poll's known accession is encountered and deduplicating by accession. This is useful implementation evidence, not an official SEC pagination specification: [Edgrapi technical walkthrough](https://edgrapi.com/blog/sec-edgar-rss-feed).

The official SEC documentation separately confirms that daily index files list company, form, CIK, filing date and file path; the indexes update nightly beginning around 10 p.m. ET and usually complete within a few hours. The daily index is therefore a completeness cross-check, not the first-seen clock. Any filing recovered only through a later index must receive the actual index-observation time, never a retroactive feed timestamp: [SEC — Accessing EDGAR Data](https://www.sec.gov/search-filings/edgar-search-assistance/accessing-edgar-data).

Phase 465 changes the capture client as follows:

- Request `count=100` and add `start=0`, then advance the offset by the **raw Atom entry count**, not unique accessions. EDGAR can emit multiple role rows for one accession.
- Continue through short, non-empty pages until the prior accession watermark is found or an empty page is reached.
- Cap the poll at 10 pages / 1,000 raw Atom entries per feed.
- Detect repeated page hashes, request failures and page-ceiling exhaustion; retain the gap and fail closed.
- Preserve page offset, URL, raw hash and page-receipt time in the existing feed-observation rows. The event's first-seen upper bound is the receipt time of the page where the accession first appeared.
- Bootstrap remains one page and does not claim historical coverage.

The exact SEC `type=144` pagination behavior has **not yet been live-verified**. The next scheduled capture is the validation. Until the prior watermark is found, all new Form 144 rows remain quarantined.

## 4. CFTC TFF — scheduled capture missing

The official CFTC TFF Futures Only dataset `gpe5-46if` now reports an update on 2026-11-16 and approximately 47.4K rows. The 2026 release schedule marks Nov 16 as the holiday-delayed release date; the report reflects positions as of Tuesday Nov 10. Sources: [CFTC TFF Futures Only](https://publicreporting.cftc.gov/Commitments-of-Traders/TFF-Futures-Only/gpe5-46if) and [CFTC release schedule](https://www.cftc.gov/MarketReports/CommitmentsofTraders/ReleaseSchedule/index.htm).

The Phase 384 workflow on main specifies `25 22 * * 1-5` UTC. At 22:47 UTC on Nov 17, no CFTC schedule-event run appeared in the latest Actions run inventory or schedule-event query. The only CFTC run found remains [43525140200](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43525140200), a Nov 13 branch-push baseline. The committed state still has 3,035 warm-up rows, latest report date Nov 3 for all four tracked contracts, and zero prospective observations.

The script's `manual` mode is explicitly state-neutral, so no manual dispatch was used to simulate a first receipt. Workflow enabled/disabled state and the cause of the missing scheduled event are not exposed by the available read interface. Verify the Phase 384 workflow is enabled in GitHub Actions before the next business-day slot; do not change the cron without evidence.

## 5. FINRA and other sources

FINRA remains blocked at the credential guard: the prior live validation found `FINRA_CLIENT_ID`, `FINRA_CLIENT_SECRET` and `FINRA_ACCESS_TOKEN` empty and made zero API requests. The old Phase 31 panel remains killed because its 102 successful synchronous snapshots were all capped at 5,000 rows. No new FINRA request was made.

Nasdaq NOTO/PHOTO remains a conditional options-flow candidate; no licensed sample, API access or vendor data was obtained. No new source was promoted in this phase.

## 6. Tests and controls

Added five offline regressions for raw-vs-unique Atom counts, offset advancement by raw rows, missing-watermark behavior after an empty page, repeated-page fail-closed behavior, and one-page bootstrap. Updated Phase 403 regressions for the 100-entry page ceiling and post-pagination gap semantics.

The PR CI runs the existing Phase 403, Phase 454 and Phase 464 suites plus the new Phase 465 suite. Live capture remains skipped on pull requests.

No return test, alpha test, OOS, bootstrap, LOO or holdout test was run. No signal was admitted. `F80_TOP20_PARTIAL50_BASELINE_C20`, universe, parameters, capital, exposure, holding rules, holdout and production remain frozen.
