# Phase 615 — SEC 13F full-snapshot and late-index safety audit

**Date:** 2026-11-25 UTC  
**Branch:** `phase615-sec-13f-full-snapshot-late-index-safety`  
**Disposition:** Phase 614 collector pagination and interval semantics hardened. Offline validation is triggered by PR creation; no live SEC feed was polled and no persistent capture state was written.

## 1. Preflight

Before starting this correction, the repository's latest Actions runs, jobs, artifacts, branches, open PRs and research files were inspected.

- Latest Phase 614 PR run before this correction: [45560522598](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45560522598), offline regression succeeded; live-capture job skipped as designed.
- Earlier failed run [45560238101](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45560238101) was an assertion mismatch in the empty-feed boundary expectation, not a live SEC failure. It was followed by successful runs.
- Latest scheduled FINRA Reg SHO run: [45550366574](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45550366574); latest CFTC TFF run: [45550124780](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45550124780).
- No Actions run was active or queued at the preflight cutoff.
- PR #231 remains open, draft and unmerged. This correction is stacked on the Phase 614 branch; it does not modify main or the frozen baseline.

## 2. Finding A — accession watermark is not a safe pagination stop

Phase 614 used the previous accession as its only continuity boundary. That is safer than using Atom `updated`, but it still assumes a prior accession must appear before any newly indexed filing in the feed's current ordering.

That assumption is not guaranteed by the SEC's documentation. SEC states that current-day indexes are updated nightly and that post-acceptance corrections/deletions can be incorporated later; full and quarterly indexes are rebuilt weekly. See the official [Accessing EDGAR Data](https://www.sec.gov/search-filings/edgar-search-assistance/accessing-edgar-data) page, updated November 20, 2026. A filing that appears or is re-indexed later may therefore be positioned outside the newest prefix already scanned.

The prior accession is now **diagnostic only**. Scheduled polls enumerate the complete current Atom snapshot to a proven short/empty page, compare accessions against the append-only local ledger, and continue scanning after the prior accession. A late-indexed accession after the former watermark is retained as a candidate.

The initial scheduled baseline also enumerates the complete available snapshot before setting the first watermark. It has no historical lower bound, so baseline rows remain metadata-only and cannot become research observations.

## 3. Finding B — exact-form count differs from raw Atom entry count

A form-filtered feed can contain recognized neighboring forms, while the parser intentionally retains only the exact target form. Comparing parsed target-form rows with the total raw entry count conflates two different counts.

The collector now records:
- total raw Atom entries;
- entries whose parsed form exactly matches the requested feed family;
- successfully parsed accession occurrences.

It fails closed only when an exact target-form entry cannot be parsed, or when an Atom entry's form cannot be classified. Only the explicitly recognized adjacent form (for example, 13F-HR/A in the 13F-HR feed) is tolerated; an unclassifiable or unexpected recognized form fails closed. Cross-feed duplicates remain visible and canonical events remain deduplicated by accession.

## 4. Finding C — Atom updated is not a publication clock

Atom `updated` remains diagnostic metadata. It no longer:
- terminates pagination;
- proves that the prior poll did or did not contain an accession;
- establishes the lower bound of the collector observation interval;
- blocks an otherwise complete snapshot solely because it is stale, future-dated, missing, or non-monotonic.

For a complete scheduled snapshot, the collector-observation interval is bounded by the previous successful complete-snapshot end and the page receipt time. This is an interval for **when our collector first observed the accession**, not an exact SEC public-release time. The conservative knowledge upper bound remains the later of page receipt and the legal filing-date floor. Public availability, manager identity, security identity, historical F80 membership, research-observation eligibility and signal eligibility remain false.

## 5. Pagination and failure policy

- Page size remains 100 raw entries.
- A scheduled poll scans at most 50 pages (5,000 raw entries) per exact-form feed.
- A short page or an empty page proves the end of the current snapshot.
- If 50 full pages are reached without a proven end, or a page repeats, parsing fails, or pagination errors, the feed poll fails closed and its successful watermark is not advanced.
- Manual mode remains one-page diagnostic-only and never persists state.
- Scheduled capture remains hourly on weekdays, starts only after merge to the default branch, and retains the existing scoped write permission.

The full-snapshot policy increases requests versus stopping at the first watermark. At 0.35 seconds between pages it remains below the SEC's stated 10 requests/second ceiling, but request volume will be monitored. The SEC's fair-access guidance is documented at the official [EDGAR data access page](https://www.sec.gov/search-filings/edgar-search-assistance/accessing-edgar-data).

## 6. Offline regressions added

Tests now cover:
- late-indexed accession appearing after the previous accession on a later page;
- complete baseline enumeration before the first watermark;
- a prior watermark missing from a complete snapshot;
- recognized neighboring form entries versus exact-form parse counts;
- unclassified or unparseable target entries failing closed;
- stale, future, unknown and non-monotonic Atom timestamps not controlling pagination or interval eligibility;
- complete empty/short pages, pagination-cap failure and repeated-page detection;
- manual non-persistence and the invariant that metadata observations never become research or signal rows.

The PR workflow compiled the collector and passed **33/33 offline tests** in [Run 45569631053](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45569631053). The live-capture job was skipped as designed; no live SEC request is part of PR validation.

## 7. Current source status

- FINRA Reg SHO: latest scheduled poll returned HTTP 200 for 7/7 daily files, but all 7 were rejected for overlapping duplicate BCPC/TPC rows (14 duplicate extra rows); zero accepted files and zero eligible first-seen events. Artifact: [14992784656](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45550366574/artifacts/14992784656).
- CFTC TFF: 3,043 rows unchanged; no new reports or revisions; latest report date November 17, 2026; zero signal-eligible rows. Artifact: [14992729209](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45550124780/artifacts/14992729209).
- Form 4 / Form 144: continue as separate SEC insider/owner research ledgers; no new signal is admitted by this phase.
- Cboe public monthly symbol-volume archive remains killed for F80 due inadequate coverage and lack of PIT/contract-level flow semantics. OPRA-wide / Open-Close feasibility remains a separate, budget-gated hypothesis.

## 8. Decision

**Phase 615 disposition: technical correction pending CI confirmation.** Do not use Phase 614 metadata as a research feature or signal. Do not run return tests, OOS tests, bootstrap or LOO until the 13F manager/security/F80 identity and public-availability gates are separately satisfied.

`F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen. No production, capital, exposure, universe or parameter changes. No paid data, vendor contact or quote request.
