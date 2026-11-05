# Phase 130 — SEC 13(f) official-list and Form 13F filing PIT/scope adjudication

**Date:** 5 November 2026  
**Status:** Documentation/source-scope audit complete; Phase 129 live list-overlap audit subsequently hit the 45-minute job timeout and was cancelled without an artifact. No data-coverage conclusion was produced.  
**Purpose:** Define what the SEC 13(f) Official List and public Form 13F filings can and cannot support before any ownership signal or identity join is attempted.

## 1. Official 13(f) list: historical availability and scope

The SEC's current Official List page states that the list is updated quarterly and exposes quarterly archives from 1996 through 2026Q3. The Phase 129 audit deliberately covers 45 quarterly snapshots from 2015Q3 through 2026Q3, using 2015Q3 as a pre-sample anchor for early 2016 filings.

The SEC page documents a fixed-width list with:
- CUSIP (positions 01–09);
- option indicator (position 10);
- issuer name (positions 11–40);
- issuer description (positions 41–67);
- addition/deletion status (positions 68–70).

This is a **Section 13(f)-reportable security eligibility list**, not a complete U.S. equity security master. SEC FAQ guidance says the population primarily covers U.S. exchange-traded stocks, closed-end funds and ETFs, with certain convertibles, equity options and warrants; open-end mutual funds are excluded. An option may appear as its own listed security, but the reporting instructions use the underlying security CUSIP for a held put/call position. Written options and short equity positions are not reported.

Consequences:
- A positive match means the filing CUSIP appeared in the 13(f)-eligible list snapshot. It does not establish a permanent ticker, a complete issuer/security identity, or a position held by an institution.
- A non-match does not prove the filing CUSIP is invalid or non-tradable; the security may simply be outside 13(f) scope, a class/series exception, or a timing/version mismatch.
- List membership must not be treated as an ownership or trading signal.
- Preserve additions/deletions and exact list vintage; never use the current list to classify historical filings.

## 2. Publication-time limitation

The SEC describes the official list as available "shortly after" each calendar quarter and its archive files carry a Run Date/Time. That is a generation timestamp, not a verified first-publication timestamp. HTTP Last-Modified/ETag/Date headers are useful retrieval metadata and integrity diagnostics, but they do not by themselves prove when the file first became publicly accessible.

Phase 129's +2- and +6-calendar-day dates after the later of PDF Run Date and HTTP Last-Modified are therefore **sensitivity proxies only**. They are not verified dissemination times and cannot authorize a strict point-in-time backtest. The same-quarter match is explicitly a lookahead diagnostic, not a usable feature.

Before any PIT claim, obtain a contemporaneous SEC release/archive timestamp, an independently timestamped web/archive capture, or another verifiable publication record. If that cannot be recovered, the 13(f) list remains an identity/eligibility cross-check only.

## 3. Form 13F filings: useful public history, but delayed and incomplete

The SEC's public Form 13F data-set page currently covers July 2013 through August 2026 and describes the data as flattened, "as-filed" extracts of structured EDGAR submissions. It is updated quarterly; filings submitted after 5:30 p.m. Eastern on the last business day of a quarter roll into the subsequent posting. Since March 2024, data-set builds follow the February/May/August/November cycle and are intended to follow the 13F due dates.

For research, the data-set publication date is not the event's knowledge date. The preferred source of truth is each individual EDGAR accession and its acceptance timestamp. A manager's quarter-end position is not publicly knowable at quarter-end: the filing is generally due within 45 days after quarter-end, and the actual acceptance time may be later or earlier than the deadline. Use the first public filing's acceptance timestamp and the next eligible trading session; never backdate the position to quarter-end.

Important incompleteness:
- Form 13F reports long positions; short positions are neither reported nor netted against longs.
- Held put/call options may be reported if eligible, but written options are not reported. Option rows use the underlying CUSIP under the SEC instructions.
- Confidential treatment can omit positions from the public filing and can delay later disclosure.
- Amendments can add previously confidential holdings, supplement an original filing, or restate/supersede the original. A later amendment is new knowledge at its own acceptance time; it must never be backdated to the original quarter-end or original filing.
- EDGAR's flattened data sets omit some filing metadata and the SEC warns that extraction errors can occur. Keep the original accession/document as the authoritative record.

Thus 13F is a delayed, incomplete, long-biased institutional holdings disclosure—not transaction-level flow and not proof of informed trading. Any future hypothesis must separate manager aggregation from duplicated reporting discretion, original filings from amendments/restatements, and genuine changes from price-driven changes in reported market value.

## 4. Phase 129 status and interpretation

At the time of this audit, GitHub Actions run [42081987897](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42081987897) remained in progress. Compilation, the Phase 124/125/126/128/129 regression suites, and both immutable input-artifact downloads had completed successfully. The 45-quarter list download/parse/overlap step was still running; no Phase 129 artifact or empirical overlap result was available yet.

Phase 129's output is intentionally privacy/licensing constrained: it does not upload raw 13(f) list rows, CUSIPs sourced from those lists, issuer names or descriptions. It records hashes/metadata and match booleans against CUSIPs already present in the public 13D/G sample. This is appropriate for the present feasibility question, but it cannot create a reusable ticker/security master.

## 5. Decision and next gates

1. Keep the official 13(f) list as a **conditional quarterly eligibility cross-check**, not a complete identity map or Smart Money feature.
2. Treat Phase 129's 1-/5-day values as sensitivity proxies only. Do not claim PIT approval from them.
3. If Phase 129 overlap is high, it still does not solve ticker, share-class, ADR, corporate-action, delisting or historical-universe identity. If overlap is low, do not infer the underlying filing CUSIPs are wrong.
4. For any future 13F ownership hypothesis, reconstruct from individual EDGAR accessions using acceptance timestamps; classify 13F-HR/13F-HR/A, restatement vs add-new-holdings, other managers/shared discretion, and confidential-treatment amendments. Build effective-dated security identity before joining returns.
5. Do not revive the previously killed N-PORT dose-response hypothesis by relabeling it as 13F. Any new 13F signal requires a materially different, pre-registered mechanism and a fresh feasibility gate.
6. No forward-return/alpha test, vendor purchase, vendor contact or production change was made in Phase 130.

**Frozen control:** `F80_TOP20_PARTIAL50_BASELINE_C20` remains unchanged.

## Official references

- SEC, [Official List of Section 13(f) Securities](https://www.sec.gov/rules-regulations/staff-guidance/official-list-section-13f-securities) — quarterly archive, fixed-width fields and historical snapshots.
- SEC, [Frequently Asked Questions About Form 13F](https://www.sec.gov/rules-regulations/staff-guidance/frequently-asked-questions-about-form-13f) — eligible-security scope, 45-day filing deadlines, long-only reporting, options, confidentiality and amendments.
- SEC, [Form 13F Data Sets](https://www.sec.gov/data-research/sec-markets-data/form-13f-data-sets) — public structured filing history, as-filed extracts and quarterly publication notes.


## 6. Post-run execution adjudication (2026-11-05)

The latest Phase 129 attempt, [Actions run 42081987897](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42081987897), is cancelled, not running. Its job passed compilation, all regression suites and both immutable input-artifact downloads. The live 45-quarter download/parse/overlap step was cancelled at 18:57:42 UTC after the workflow's 45-minute job limit; the log records an explicit cancellation and termination of the Python process. No artifact was produced.

The current implementation processes 45 quarterly snapshots serially, tries multiple candidate URLs with up to four retries, and writes the manifest only after the complete loop. Consequently, timeout leaves no durable partial progress. This is an execution-time/resumability limitation, not evidence that the SEC lists are unavailable or that CUSIP overlap is low.

**Decision:** do not rerun Phase 129 unchanged. Phase 130 already establishes that the list is only an eligibility cross-check and that Run Date/HTTP metadata do not establish public dissemination time. A future re-entry would require (a) a genuinely necessary research question, (b) resumable per-quarter checkpoints, (c) explicit SEC-compliant request pacing, and (d) independent first-publication evidence. The result must not be used for an alpha feature.
