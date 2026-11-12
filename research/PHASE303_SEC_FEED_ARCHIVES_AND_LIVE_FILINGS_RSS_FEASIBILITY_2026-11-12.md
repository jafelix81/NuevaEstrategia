# Phase 303 — SEC Feed archives and Latest Filings RSS feasibility

**Date:** 2026-11-12 UTC  
**Branch:** `phase303-sec-feed-live-rss-feasibility`  
**Status:** `FEED_ARCHIVES_REJECTED_AS_PRIMARY_HISTORICAL_PAC_SOURCE; LATEST_FILINGS_RSS_PROBE_PASSED_PROSPECTIVE_ONLY`  
**Scope:** public SEC source feasibility. No Feed/Oldloads archive, PDS subscription, vendor service, or paid data was used. One live Atom snapshot and two complete-submission header cross-checks were performed.

## Executive decision

The SEC's daily Feed and Oldloads archives are public, but their per-day concatenated payloads are too large to be an efficient broad historical PAC/first-receipt source. They do not supply a compact accession-level PAC event table or a documented exact first-public timestamp. **Do not bulk-download them or make them a prerequisite for the Form 4 panel.**

The SEC's **Latest Filings search and associated RSS** is the more promising route for prospective receipt-time capture: the SEC itself identifies it as the best public resource for getting as close to real-time availability as possible. It has no historical backfill and polling only yields an interval-censored first-observed time, not an exact public timestamp. Retain it as a conditional prospective pilot, not as historical PIT evidence or a signal.

## 1. Public daily Feed and Oldloads archives

The SEC documents:
- `/Archives/edgar/Feed/` as daily `.nc.tar.gz` archives of filing-day dissemination content;
- `/Archives/edgar/Oldloads/` as daily concatenated archives of public filing submissions with filing headers;
- index files (`index.html`, `index.xml`, `index.json`) within these directory trees.

The directory listings demonstrate the scale:

| Public directory sample | Observed daily archive size range |
|---|---:|
| SEC Feed, 2023 Q2 | 642,473 KB to 8,728,562 KB |
| SEC Feed, 2026 Q4 (October dates listed) | 693,801 KB to 2,299,770 KB |

These are per-day archive files, not per-accession objects. Even one day can require hundreds of megabytes to multiple gigabytes before parsing. This is an unattractive way to inspect a handful of Form 4/4-A accessions, and a multi-year sample would be operationally expensive. Directory size is evidence of retrieval burden, not evidence that the underlying filings are unavailable.

The SEC's public description of later-business-day post-acceptance corrections says prior daily/feed/oldload index snapshots are not rewritten; full and quarterly indexes are rebuilt weekly. This supports preserving historical daily-index vintages, but it does **not** establish that downloading a Feed/Oldloads archive yields a complete, compact, accession-level PAC event history. Phase 302 did not capture actual PAC `.pc` records. Form 4/A amendments must not be conflated with PAC.

**Disposition:** reject Feed/Oldloads as the primary historical clock or broad PAC-reconstruction source. Keep a single-day archive inspection as an exceptional diagnostic only if a specific unresolved accession/date justifies the very large transfer. Continue using the much smaller daily `form.YYYYMMDD.idx` files for the historical date-granular knowledge bound.

## 2. Latest Filings RSS as a prospective source

The SEC Webmaster FAQ states that:
- the Latest Filings search and its associated RSS are the best public resources for getting as close to real-time filing availability as possible;
- filings are often available on sec.gov within 1–3 minutes of the EDGAR acceptance timestamp, but the lag can increase significantly under load and is not guaranteed;
- there is no timestamp identifying the exact moment filing content first became available on sec.gov.

The SEC's RSS documentation says Latest Filings can be filtered by company, CIK and filing type, and can include or exclude Ownership filings (Forms 3, 4 and 5). This is the relevant RSS route for Form 4/4-A; the separate Structured Disclosure RSS feeds are for XBRL submissions and are not a substitute for the ownership-form feed.

A prospective capture could record:
1. UTC poll-start and response-completion timestamps, plus HTTP response headers;
2. the raw Atom/RSS response body and SHA-256;
3. accession, form type, issuer CIK, filing date and entry URL;
4. first-seen poll and previous successful poll, giving an explicit arrival interval rather than a falsely precise timestamp;
5. parser version, duplicate handling, missing-feed windows and recovery status;
6. later reconciliation against the complete-submission SEC-HEADER, historical daily index and any available correction evidence.

A 5–10 minute poll cadence would be far below the SEC's published maximum request rate, but actual endpoint behavior, Form 4/A inclusion, feed retention, pagination and gap recovery still require a small live pilot with the declared SEC User-Agent. A poll timestamp is an observation time, not proof of exact first-public time. A missing poll creates an interval wider than the nominal cadence.

**One-time live probe (2026-11-12 01:02 UTC):** both SEC Atom queries returned HTTP 200 and parsed successfully. The `type=4` query returned 100 entity rows representing **50 unique Form 4 accessions**; the `type=4/A` query returned 36 entity rows representing **18 unique Form 4/A accessions**. Across both queries there were 136 raw rows and 68 unique accessions. In this snapshot every accession had exactly two rows—one `Issuer` and one `Reporting`—and the path CIK matched the CIK in the title on all 136 rows. The parser now preserves entity rows and groups at accession grain; it does not mistake a reporting-owner CIK for the issuer CIK.

Two complete submissions (one Form 4 and one Form 4/A) were downloaded and hashed. Their SEC-HEADER `ACCEPTANCE-DATETIME` values matched the Atom `updated` value exactly in **2/2** cases. Therefore, in this sample, Atom `updated` is an acceptance-time field, not an independent first-public timestamp. The HTTP `Last-Modified` headers were 21 and 25 seconds after acceptance, respectively, but SEC does not document this header as first-public time; it is not admitted as such. The SEC FAQ explicitly says no timestamp identifies the exact moment content first became public.

- Final run: [43131625929](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43131625929), **7/7 offline tests passed**, both live queries and both header cross-checks passed.
- Artifact: [13904274568](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43131625929/artifacts/13904274568), 21,041 bytes, SHA-256 `f55f880c3bb14a2744571e8988d907c27c1db6d3833dcc93e7c565eed4771e62`. It contains both raw Atom bodies, the parsed entity/accession ledger and two complete submissions. Raw Atom SHA-256 values: Form 4 `00271e42681445fa46ccfcb631440a8938ea5e294d5a2700bad685198885af7b`; Form 4/A `9c738b2aeb0a15b41096ebf759c1892e438c637edd4e03ad11e4cef3340bb588`.

**Disposition:** retain Latest Filings RSS as a conditional *prospective* clock-validation source. It can capture first-observed intervals when polled continuously, but its `updated` field mirrored acceptance in the two tested filings. It cannot backfill the historical sample and cannot, by itself, admit strict PIT.

## 3. Source admission matrix

| Requirement | Daily form index | Feed / Oldloads | Latest Filings RSS |
|---|---|---|---|
| Historical coverage | Public daily indexes from 1994Q3 | Public daily archives; large per-day payloads | No historical backfill established |
| Universe scope | All indexed EDGAR forms | Broad EDGAR filing archive | Latest filings; ownership forms can be selected |
| Ex-ante / availability evidence | Date-granular historical snapshot | Daily archive vintage; no compact accession event clock | Near-real-time public search/RSS, prospective only |
| Reproducible raw evidence | Small raw index + hash | Raw daily archive + hash, but very large | Raw feed body + hash + poll interval |
| Exact first-public timestamp | No | Not documented by the archive index | No; first-observed interval only |
| Operational disposition | **Keep for historical daily bound** | **Reject as broad primary source** | **Conditional prospective pilot** |

## 4. Next gate

1. The one-time endpoint probe is complete: both Form 4 and Form 4/A filters returned valid Atom feeds. The requested `count=100` produced 100 Form 4 entity rows (50 accessions); retention, pagination beyond the requested count and feed-gap recovery are still untested.
2. Run a prospective 30-day capture pilot on a research-only branch or approved durable store. Preserve raw responses, poll intervals, hashes and all missed-poll gaps.
3. Reconcile a deterministic sample of first-seen accessions to SEC-HEADER acceptance times and subsequent daily-index entries. Do not infer exact first-public time from the RSS `updated` field without independent validation.
4. Keep same-day Form 4/A pairs intraday-unordered when the feed interval cannot establish their order. Keep actual PAC separate from Form 4/A.
5. Do not start return/alpha testing until effective-dated security identity, transaction-owner attribution, universe/price coverage and a conservative availability contract pass.

## Official sources

1. SEC, [Accessing EDGAR Data](https://www.sec.gov/search-filings/edgar-search-assistance/accessing-edgar-data) — Feed/Oldloads descriptions, daily-index cadence, fair-access policy and PAC treatment.
2. SEC, [Webmaster Frequently Asked Questions](https://www.sec.gov/about/webmaster-frequently-asked-questions) — Latest Filings/RSS as the closest public near-real-time resource, typical but non-guaranteed acceptance-to-availability lag, and absence of an exact first-public timestamp.
3. SEC, [RSS Feeds](https://www.sec.gov/files/about/secrss.shtml) — Latest Filings search can be subscribed to and filtered by filing type and Ownership forms.
4. SEC, [Feed 2023 Q2 directory](https://www.sec.gov/Archives/edgar/Feed/2023/QTR2/) and [Feed 2026 Q4 directory](https://www.sec.gov/Archives/edgar/Feed/2026/QTR4/) — observed per-day archive sizes.

## Controls

- No Feed/Oldloads archive was downloaded.
- No PDS subscription, vendor contact, purchase or terms acceptance.
- One live RSS snapshot was captured; no continuous polling schedule or historical backfill was started.
- No return/alpha, bootstrap/LOO, chronological OOS or holdout test.
- `F80_TOP20_PARTIAL50_BASELINE_C20`, production, universe, capital and parameters remain unchanged.
- No PR was opened or merged.
