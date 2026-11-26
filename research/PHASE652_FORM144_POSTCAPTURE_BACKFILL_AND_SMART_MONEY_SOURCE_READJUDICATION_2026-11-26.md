# Phase 652 — SEC Form 144 post-capture ledger expansion and Smart Money source re-adjudication

**Audit cutoff:** 2026-11-26 23:08 UTC  
**Main HEAD before documentation:** `6964a7863121387174c44467926f1a00ab8c747e`  
**Disposition:** latest natural Form 144 poll succeeded and materially expanded the structured descriptive ledger. No new accession or signal was observed. The phase also re-ranked public Smart Money candidates using current historical coverage, PIT and identity gates. No return test or strategy promotion.

## 1. Required preflight: Actions, jobs, artifacts, branches and research files

- Repository Actions total: **8,356**.
- Latest 100: **72 success / 17 failure / 11 cancelled**.
- Queued, waiting, requested, pending or in-progress: **0**.
- Main head: `6964a7863121387174c44467926f1a00ab8c747e`.
- PR [#247](https://github.com/jafelix81/NuevaEstrategia/pull/247) is merged; merge commit `c7379f42ffffd631e8ce1bc3b9b3261871e3480d`. Its PR run [45895296971](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45895296971) passed 62/62 offline tests; the live-capture job was skipped because this was a pull-request event.
- No workflow was dispatched, rerun, cancelled or duplicated.

### Latest natural Form 144 capture

Run [45906061652](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45906061652), 2026-11-26 22:38:18 UTC, ran on `main`. Both `offline-regression` and `live-capture` succeeded. The live job completed the capture, ledger quality audit, 10b5-1 audit, artifact uploads and append-only commit.

Artifacts downloaded and inspected:
- [15157033731 — first-seen poll](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45906061652/artifacts/15157033731)
- [15157308416 — post-capture 10b5-1 audit](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45906061652/artifacts/15157308416)
- [15157992808 — current 10b5-1 refresh](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45906061652/artifacts/15157992808)

Verified results:
- 53 feed observations; both Form 144 and Form 144/A feeds completed with continuity intact.
- 0 new accessions, 0 new canonical events, 0 new cross-feed overlaps, 0 feed errors and no possible feed-window gap.
- The poll interval is a collector-receipt upper bound, not an exact public-release timestamp.
- Ten already-bounded accessions were backfilled; **42 structured detail rows** appended, zero parser errors, zero source-hash mismatches, 168 accessions remain in the detail backfill queue.
- Ledger now contains **835 accessions / 5,537 detail rows**; all 5,537 source hashes match.
- 807 accessions have bounded collector-observation intervals; 18 initial-baseline accessions still lack a lower bound; zero malformed intervals.
- No acceptance-clock reconciliation was attempted in this poll; public availability is not certified.
- Schema migration was already current; no additional migration was required.

### 10b5-1 and proposed-sale semantics

The refreshed descriptive ledger reports:
- 314 accessions with a formal plan-adoption date (312 Form 144, 2 Form 144/A), across 132 distinct dates.
- 313 plan dates precede the notice; one is the same date; none is after the notice.
- Plan-date-to-notice lag: median **182 days**, p25 97, p75 273, maximum 1,687 days.
- Remarks polarity: 23 explicit positive mentions, 4 explicit negative mentions, 3 ambiguous mentions and 805 with no mention.
- 18 accessions contain sell-to-cover / tax-withholding context. Four Fermi notices form a same-issuer/same-day negative-control cluster totalling **2,253,270 proposed units**. These are proposed-sale notices, not verified executions.

Interpretation: a disclosed plan-adoption date is historical information embedded in a later notice, not the date the market learned of the plan. Form 144 remains a proposed-sale disclosure, not an execution feed. Raw remarks presence is not plan polarity. The current 10b5-1 counts are descriptive and do not identify discretionary insider intent.

Controls remain false: `signal_admitted`, `alpha_test_run`, `oos_test_run`, `bootstrap_run`, `loo_run` and `production_changed`.

### Other latest natural captures rechecked

| Source | Latest natural run | Verified result |
|---|---|---|
| SEC Form 4 | [45848689364](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45848689364) | Both jobs succeeded. 0 new accessions; 2 prior-watermark entity observations; 0 exact duplicate entity groups. Ten-accession backfill added 23 transaction rows, 25 footnote references, then 24 additional footnote references; 10 owner rows. Crosswalk: 12 rows, 0 signal-eligible. |
| SEC 13F | [45839454376](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45839454376) | Both jobs succeeded. 29 accessions across four feeds (18 HR, 9 HR/A, 2 NT); all four feeds are initial baselines with no lower bound. No holdings/XML downloaded; 0 research-eligible and 0 signal-eligible. |
| CFTC TFF | [45753716471](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45753716471) | Capture succeeded; 3,043 rows total, no new reports or revisions, no state change, no forward outcomes. |
| FINRA Reg SHO | [45754121648](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45754121648) | Latest natural capture predates Phase 650 merge: 8 HTTP-200 files, all 8 rejected by the old parser; 16 duplicate symbol/date groups; 0 first-seen/eligible events. Phase 650 PR validation was offline-only. |

The latest Form 4, 13F, CFTC and FINRA artifacts were downloaded and inspected. No post-merge natural FINRA capture exists yet. The next existing scheduled run must validate Phase 650 against real files; the eight older rejected files are not retroactively promoted.

## 2. Branch and pull-request adjudication

The mainline now contains Phase 650's FINRA partial-symbol quarantine. The relevant open research branches remain separate:
- PR #37, SEC 13D/G parent retrieval and identity crosswalk: Draft, stacked on Phase 347; 43/44 explicit parents retrieved, one parent remains 404, five child/parent CUSIP mismatches, six valid child CUSIPs lack a parent CUSIP, and one all-zero CUSIP sentinel. No event signal is admitted.
- PR #8, SEC 13F PIT accession join: Draft; not merged.
- PR #50, FINRA T1 ATS 209-week revision-stability audit: Draft and stacked on earlier ATS branches.
- PR #48, Cboe options source ranking: Draft and stacked on earlier options work.
- PR #13, Phases 99–230 broad PIT/universe research: 580 commits / 506 files and a large historical stack; do not merge wholesale.
- The old Phase 20C FINRA branch remains subject to Phase 593's NO-GO; its same-day-close test is not executable because the daily short-volume file is published after regular trading.

No divergent or stacked research branch was merged in this phase.

## 3. Broad source re-adjudication

### A. SEC Forms 3/4/5 — highest-priority public event candidate, still conditional

The SEC's Insider Transactions Data Sets cover **January 2006 through September 2026** and are published quarterly. The official readme describes eight as-filed tables: SUBMISSION, REPORTINGOWNER, NONDERIV_TRANS, NONDERIV_HOLDING, DERIV_TRANS, DERIV_HOLDING, FOOTNOTES and OWNER_SIGNATURE. The flat-file SUBMISSION table contains accession, filing date, period of report, document type, issuer CIK/name and issuer trading symbol, but not the exact acceptance timestamp. The transaction tables preserve transaction date, code, acquired/disposed indicator, shares, price and ownership context. The SEC added the AFF10B5ONE field to the 2023–2025 data sets in July 2025.

Phase 39 already validated actual 2012 Q1 and 2026 Q3 archive schemas and reproduced accession-header acceptance-time extraction in both regimes. The SEC Webmaster FAQ says filings are often available 1–3 minutes after EDGAR acceptance but explicitly states there is no exact first-public timestamp. For historical tests, acceptance time must not be represented as exact dissemination; a predeclared next-full-XNYS-session entry convention is the conservative fallback. For prospective tests, retain the collector's bounded first-seen interval.

The unresolved blocker is effective-dated issuer/security-class/listing identity and coverage against the full historical F80 universe. Phase 455's six purposively selected quarter sample found only five issuer-filing events with exact matches to the static 335-ticker snapshot. That static snapshot is not a historical security master and the sample is not a coverage estimate. Do not run an event study from it.

Candidate hypotheses remain: independent discretionary P-code purchases; cross-insider purchase clusters; net discretionary buying after grants, exercises, tax withholding, gifts and 10b5-1 controls. P means open-market **or private** purchase, not verified exchange execution. Form 4/A amendments are information arrivals, not new trades. Transaction-line owner attribution remains unverified for multi-owner filings.

Official sources:
- https://www.sec.gov/data-research/sec-markets-data/insider-transactions-data-sets
- https://www.sec.gov/files/insider_transactions_readme.pdf
- https://www.sec.gov/about/webmaster-frequently-asked-questions
- https://www.sec.gov/search-filings/edgar-search-assistance/accessing-edgar-data

**Disposition:** keep Form 4 as the leading public event candidate, but do not test returns until full-universe identity/coverage and transaction semantics pass.

### B. SEC Schedule 13D/G — high-value activist-event hypothesis, quarantined

The Phase 555 rule-clock review prioritizes Schedule 13D over broad 13F/N-PORT holdings-change signals: since 2024-02-05, initial 13D is generally due within five business days and material amendments within two business days. 13G timing is filer-category-specific and must not be pooled under one lag. Acceptance is not exact public availability.

Phase 636 retrieved and identity-validated 43/44 explicit parent submissions. CUSIP continuity is imperfect (31/42 valid child CUSIPs matched a parent CUSIP; five mismatched; six had no parent CUSIP; one was an all-zero sentinel). One explicit parent remains unresolved. Subject issuer, filer, reporting person, CUSIP and security class must remain distinct. PR #37 is Draft and stacked; no event panel or return test is admitted.

**Disposition:** retain as a high-priority event research line after effective-dated security identity and public-availability controls are solved.

### C. SEC MIDAS — long public history, but quarterly release and semantics block daily PIT

The current SEC catalog lists 59 quarterly per-security archives from 2012 Q1 through 2026 Q3 and more than 4,800 securities. The public series has daily observations but quarterly ZIP publication; daily observation date is not a daily knowledge date. The actual ZIP payload was not retrieved in this phase (the web client rejects ZIP/octet-stream and the container download attempt failed). Per-quarter first-publication timestamps and historical F80 identity coverage remain unresolved.

Important semantic rule from Phase 534: `HiddenVol` measures on-exchange executions against hidden/undisplayed resting orders. It is **not** dark-pool/off-exchange volume, signed flow or institutional identity. Odd-lot, cancel-to-trade and feed-methodology regime breaks must be preserved.

**Disposition:** conditional market-quality/liquidity candidate, not Smart Money flow; no backtest until actual payload, quarter release clock and effective-dated security coverage are established.

Official catalog: https://www.sec.gov/data-research/sec-markets-data/marketstructuredata-security

### D. FINRA ATS / Reg SHO

- FINRA T1 ATS remains a potentially useful weekly off-exchange venue-concentration panel. Prior audits cover 209 weeks, but the historical archive endpoint returned HTTP 530 in Phase 535; the API sample has revision and stable-row issues. Phase 579/580 PIT logic is synthetic and still needs real identity, historical universe and total-return coverage.
- FINRA Reg SHO is daily short-sale volume, not short interest or signed investor direction. The file arrives after regular hours; any admissible feature must enter no earlier than the next session. Phase 650's parser is merged, but post-merge natural capture is pending. Phase 593 keeps the current Phase 20C same-day-close implementation NO-GO.

### E. CFTC, 13F/N-PORT and options

- CFTC Russell has only two prospective observations. The frozen-reference percentile feature is reproducible, but no outcome or alpha test is possible; the price-source rights gate remains open.
- 13F's 29 current baseline accessions have no lower-bound poll interval and no holdings rows. Historical broad-universe coverage and amendment lineage remain insufficient. The simple N-PORT quarter-over-quarter aggregate share-growth hypothesis is killed by the six-period negative/unstable dose-response documented in Phases 386/526.
- OCC account-type options volume is parked as RIGHTS_BLOCKED under current automated-access terms. Cboe and Databento options data remain conditional on written research-use rights; no quote, purchase or vendor contact is authorized. Options-data budget remains **USD 0**.

## 4. Next actions

1. Continue the existing Form 144 bounded backfill (168 accessions remain) and preserve the 10b5-1 / sell-to-cover negative controls.
2. Await the next natural Form 4 and 13F polls; do not manually dispatch or duplicate them.
3. Await the next natural FINRA Reg SHO poll after Phase 650 merge; only then adjudicate the partial parser against live files.
4. Keep Form 4 and Schedule 13D/G as the highest-value event research candidates, but prioritize effective-dated identity and full-universe coverage before return labels.
5. Keep SEC MIDAS and FINRA T1 ATS as conditional market-quality/venue-activity sources, not investor identity.
6. Keep CFTC Russell outcome-blind until price rights and enough prospective observations exist.
7. Do not revive the killed N-PORT share-growth feature or blocked Phase 20C same-day-close test.

## 5. Strategy controls

- `F80_TOP20_PARTIAL50_BASELINE_C20`: **frozen**.
- Incremental alpha demonstrated: **none**.
- New OOS / bootstrap / LOO: **none**.
- Holdout: untouched.
- No changes to universe, features, parameters, costs, exposure, capital, production or holding-period policy.
- No options data acquired; budget USD 0.

**Phase 652 result:** successful Form 144 descriptive backfill and a documented source-priority refresh. No new investment signal and no strategy promotion.
