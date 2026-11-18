# Phase 490 — SEC submissions acceptance-timestamp PIT source audit

**Audit cutoff:** 2026-11-18 22:25:14 UTC  
**Disposition:** **DO NOT USE `submissions.json` `acceptanceDateTime` AS CANONICAL PIT TIME. Use the filing's SGML/index header for acceptance time; use observed first-seen receipt for prospective public-availability bounds.**

## 1. Preflight and current repository evidence

- Main HEAD at audit start: `67b08a6e25e7863dda00f4d8fe98b9aa8ffc3ade` (Phase 489 state addendum, committed 2026-11-18 21:54:35 UTC).
- Branch inventory: **316** (four pages: 100 + 100 + 100 + 16).
- Open pull requests: **56**. Open issues: **2** (#132 Cboe sample rights; #9 SEC 13D/G historical coverage).
- No Phase 490 branch or open PR existed before this audit.
- The connected GitHub action set exposes per-run jobs, logs and artifacts, but not a repository-wide Actions-run listing. This audit therefore does not claim a fresh repository-wide active/queued count. No workflow was dispatched, rerun, cancelled or duplicated.

### Latest relevant scheduled captures

**SEC Form 144/144-A — Phase 403**

- Scheduled run [44396134680](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44396134680), main, poll 20:56:07–20:56:30 UTC.
- Both jobs succeeded; offline regression 40/40.
- 51 unique new accessions; both feed watermarks recovered; 51/51 XML and acceptance reconciliations; no possible feed-window gap.
- Current state: 11 complete polls, 247 canonical event rows, zero signal-eligible events.
- The 51 observations remain metadata-only: zero public-availability-certified events and zero verified historical F80 memberships. Form 144 is a proposed-sale notice, not a completed execution record.
- Artifact [14470455938](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44396134680/artifacts/14470455938), SHA-256 `a6d47ef938306f3efa4fcff412c3a737995611030b00a3afe498e5e9ee525d07`.

**SEC Form 4/4-A — Phase 476**

- First scheduled baseline run [44380395679](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44380395679), main, poll 19:26:00–19:26:08 UTC.
- Both jobs succeeded; offline regression 37/37.
- Ledger remains at 35 unique accessions (10 Form 4, 25 Form 4/A), all `INITIAL_BASELINE_NO_LOWER_BOUND`; zero bounded metadata, research-eligible or signal-eligible rows.
- Persisted `state.json` still reports last successful poll end 19:26:08 UTC. No later successful Form 4 state commit appears in the latest main commit history reviewed at this cutoff. Because the connector lacks a repository-wide Actions-run listing, this does not distinguish an absent schedule event from a failed, delayed or still-running attempt. Do not dispatch manually; the next successful poll must reconcile both prior watermarks.

## 2. New source-quality finding: submissions JSON acceptance timestamps are not stable ground truth

The SEC Submissions API is useful for filing discovery and historical accession enumeration. SEC documentation says entity filing histories are available as JSON, current history contains at least one year or 1,000 recent filings (whichever is greater), older history is linked through additional JSON files, and the bulk `submission.zip` is rebuilt nightly. The API is updated throughout the day as submissions are disseminated.

However, a separate empirical data-quality investigation in EdgarTools issue [#1501](https://github.com/dgunning/edgartools/issues/1501), opened 2026-10-08 and discussed through 2026-10-28, found that the JSON `acceptanceDateTime` value can be shifted relative to the filing's own SGML header and SEC filing-index “Accepted” time:

- The same accession could have different JSON timestamps when read from the issuer's submissions file versus the reporting person's file.
- Sampled files showed three states: true UTC, Eastern wall time labelled with a trailing `Z`, or an offset one Eastern time-zone difference from the header.
- The state could change after a submissions JSON file was rebuilt; a previously correct value could become shifted, and vice versa.
- A newly appended filing could temporarily differ from older rows in the same file.
- The issue's maintainer explicitly rejected a per-file offset correction because the rule can change after rebuilds and mixed states occur. The proposed authoritative route is the accession's `-index-headers.html` acceptance value, with the raw SGML header as the other direct source.

This is third-party empirical evidence, not an SEC admission that the API is defective. It is nevertheless sufficient to prohibit the JSON field from serving as the canonical timestamp in a no-lookahead event study. A historical backtest must produce the same timestamp every time it is rerun; a value that changes after a nightly rebuild is unsuitable as the immutable ground truth.

## 3. Official SEC timing semantics

The SEC's own developer documentation establishes the following:

1. The complete submission text file carries `ACCEPTANCE-DATETIME` in its header.
2. The SEC describes the acceptance date as YYYYMMDD and acceptance time as Eastern time.
3. The SEC explicitly says there is **no timestamp indicating when filing content first becomes available on sec.gov**.
4. Filings are often available within 1–3 minutes of acceptance, but the lag can increase significantly under load and is not guaranteed or predictable.
5. Latest Filings/RSS is the SEC's recommended public resource for getting as close to real-time availability as possible.

Primary references:

- [SEC — EDGAR APIs](https://www.sec.gov/search-filings/edgar-application-programming-interfaces): submissions JSON, history files, real-time update behavior and nightly bulk archive.
- [SEC — Webmaster FAQ, developer timing and EDGAR timestamps](https://www.sec.gov/about/webmaster-frequently-asked-questions): acceptance header, Eastern clock, non-guaranteed publication lag and absence of an exact public-availability timestamp.
- [EdgarTools issue #1501](https://github.com/dgunning/edgartools/issues/1501): empirical cross-file/rebuild timestamp inconsistency and decision not to apply unstable offset correction.

## 4. Required timestamp hierarchy for this repository

| Use | Preferred source | Treatment |
|---|---|---|
| Historical accession discovery | SEC Submissions JSON / quarterly bulk data | Allowed for accession, form, filing-date and discovery metadata |
| Canonical EDGAR acceptance time | `ACCEPTANCE-DATETIME` in the accession's raw SGML submission header or `-index-headers.html` | Parse as `America/New_York`; convert using the IANA time-zone database; retain source bytes/hash and raw value |
| Independent acceptance check | Filing detail `-index.htm` “Accepted” value | Must agree with the header after time-zone conversion; otherwise quarantine |
| Prospective first public observation | Existing scheduled Atom poll, page response receipt and prior successful watermark | Preserve the feed's timezone-aware `updated`, poll start, response receipt and page hash; receipt is a conservative upper bound, not the exact publication instant |
| Historical public-availability proxy | Filing date / conservative next-session rule | No same-day intraday use; use the pre-existing conservative date-only EOD boundary until a defensible historical publication clock exists |
| Submissions JSON `acceptanceDateTime` | Advisory comparison only | Never canonical; never use alone to decide pre-/post-close, event day or executable entry |

### Fail-closed rules

- Never repair a JSON timestamp by applying a fixed +4/+5-hour offset, an issuer-level offset, or a per-file offset learned from another row. The empirical evidence shows rebuild-dependent and mixed states.
- If SGML header and index “Accepted” disagree, quarantine the accession; do not select whichever timestamp is more convenient.
- If the raw header is absent, malformed or timezone interpretation is ambiguous, retain date-only metadata and prohibit intraday timing.
- Acceptance time is not public-release time. Even a verified acceptance timestamp does not authorize a trade at that instant.
- For prospective observations, preserve the local receipt upper bound and enter no earlier than the next supported XNYS session after that receipt. Same-day intraday use remains unauthorized.
- For historical studies without a first-seen ledger, keep the conservative filing-date-only execution boundary. Do not backfill public-availability times from the current Submissions JSON.

## 5. Impact on existing research lines

- **Phase 403 Form 144:** the current implementation already extracts `ACCEPTANCE-DATETIME` from the complete submission text and converts the Eastern clock with `ZoneInfo("America/New_York")`; it separately reconciles the filing-detail index. It does not rely on Submissions JSON `acceptanceDateTime`. The 51 latest reconciliations matched Atom `updated` and had zero timing anomalies. Public availability remains uncertified.
- **Phase 476 Form 4/4-A:** the current collector stores Atom metadata and first-seen receipt bounds only. It does not ingest Submissions JSON acceptance timestamps or transaction rows. The 35-row baseline remains unbounded until a later complete poll finds both prior watermarks.
- **Historical Form 4 bulk work (Phase 279/271 lineage):** quarterly transaction archives can remain a candidate for broad discovery, but any accession-level acceptance timestamp must be recovered from the raw SGML/index header. The bulk SUBMISSION table's filing date is not an intraday clock. Before scaling, validate a stratified sample across issuers, filer agents, filing types, DST states and years.
- **13D/G, 13F and other SEC event studies:** apply the same timestamp-source rule. Do not let a mutable Submissions JSON field determine an event's executable date.
- **No change to source ranking or alpha status:** this is a PIT data-quality gate, not evidence that insider activity predicts returns.

## 6. Next gates

1. Obtain a second successful scheduled Phase 476 poll and verify both prior accession watermarks; until then there are still zero bounded Form 4/4-A observations.
2. Before historical Form 4 backfill, run a hash-preserved validation sample of at least 30 accessions spanning multiple issuers, reporting persons, filing agents, forms, years and both DST states. Compare Submissions JSON values with raw SGML `ACCEPTANCE-DATETIME` and the index page's “Accepted” value; record mismatches rather than correcting them.
3. Use header/index timestamps only for acceptance chronology. Keep the separate public-availability and executable-entry gates closed.
4. Reuse the existing Phase 403 parser for SGML/index acceptance extraction; do not create another SEC crawler or a JSON-offset correction utility.

## 7. Frozen strategy controls

No price data, raw filing documents, transaction rows, forward returns or market data were downloaded in this phase. No backtest, event study, OOS, bootstrap, LOO or holdout test was run.

`F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen. No universe, parameters, holding period, capital, exposure, costs, holdout, production or signal eligibility changed.

**Conclusion:** SEC Submissions JSON is useful for discovering historical filings, but its `acceptanceDateTime` field is not an immutable PIT clock. The accession's own SGML/index header is the defensible acceptance source; prospective local first-seen receipt remains the only repository-controlled upper bound on public availability.
