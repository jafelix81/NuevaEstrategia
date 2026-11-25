# Phase 48 — SEC 13F manager-period as-of amendment state machine

**Status:** implementation complete; awaiting GitHub Actions offline regression.  
**Date:** 2026-11-24 UTC  
**Branch:** `phase48-sec-13f-asof-amendment-state-machine`  
**Parent:** `phase47-sec-13f-pit-accession-join-audit`

## Why this phase exists

Phase 47 established accession-level SUBMISSION/COVERPAGE/INFOTABLE joins and found 294 / 406 amendments in the 2018 Q1 and 2026 Jun–Aug samples. It also established that amendment semantics differ:

- `RESTATEMENT` replaces the previously reported portfolio state.
- `NEW HOLDINGS` / `NEW HOLDINGS ENTRIES` adds entries to the previously reported state.
- `13F-NT` / `13F-NT/A` is a notice and must not be interpreted as a zero-holdings portfolio.

The Phase 47 audit did not yet implement a historical as-of portfolio state. A naïve concatenation would double-count restatements; treating every amendment as a replacement would drop new-holdings supplements; treating notices as zero positions would create false exits.

## Implemented contract

The new pure-Python module `research/phase48_sec_13f_asof_amendment_state_machine.py` provides:

1. **Manager-period grouping:** normalized manager CIK plus report period.
2. **Accession integrity:** duplicate accessions fail closed.
3. **Amendment identity:** COVERPAGE `ISAMENDMENT`, amendment number and type are reconciled with `SUBMISSIONTYPE`; a `13F-HR` with `ISAMENDMENT=Y` is supported.
4. **Chain integrity:** exactly one original is required; amendment numbers must be unique and contiguous from 1; unknown types and contradictory flags fail closed.
5. **Conservative daily availability:** a filing becomes eligible on the first supplied regular-session date strictly after `FILING_DATE`. Report period is never used as an availability clock. If the supplied calendar ends before a future session can be established, the result is `PENDING_CALENDAR_COVERAGE`, not silently treated as unavailable.
6. **State semantics:** RESTATEMENT replaces the full state; NEW HOLDINGS ENTRIES appends previously absent line keys. Overlapping line keys are blocked rather than silently overwritten.
7. **Line identity:** CUSIP, class, put/call, investment discretion, other-manager code and amount type are retained as separate dimensions. Duplicate line keys within an accession are blocked.
8. **Notice separation:** 13F-NT records are returned as `NOTICE_ONLY_NOT_ZERO_HOLDINGS`; they never create an empty portfolio.
9. **Auditability:** each successful manager-period state records applied accessions and a deterministic SHA-256 digest.

The function accepts the session calendar explicitly. Production callers must supply a verified NYSE session calendar with sufficient forward coverage; the module does not guess holidays or sessions.

## Offline regression coverage

The test suite uses synthetic fixtures only. It covers:

- filing-date strict-next-session availability;
- original → new-holdings supplement → restatement sequence;
- same-day original/amendment availability only on the next full session;
- 13F-NT notice separation;
- overlapping new-holdings rows;
- missing holdings payload;
- amendment without original;
- amendment-number gaps;
- duplicate line keys;
- multiple original submissions;
- truncated session calendar;
- unknown amendment type.

No live SEC retrieval is part of this workflow. The Phase 47 workflow was also changed so pull-request validation is offline-only; bounded live SEC retrieval now requires an explicit `workflow_dispatch` with `run_live_sec_audit=true`. The existing project-contact fallback remains available for that explicit live path; the repository secret itself is not asserted to be configured.

## Data and research limitations

- This phase does **not** reconstruct the actual 2018 or 2026 SEC holdings panels. The tests are synthetic and establish code semantics only.
- It does not yet parse the SEC OTHERMANAGER table or resolve 13F-NT relationships to managers whose holdings are reported by another filer.
- It does not build an effective-dated CUSIP/FIGI-to-F80 security crosswalk. Phase 22C previously showed 2016Q1 coverage of only 212/335, 2020Q1 246/335 and 2024Q1 280/335; Phase 604 improves current ticker discovery but does not solve historical CUSIP identity.
- It does not establish exact EDGAR acceptance timestamps. The daily clock remains first full regular session strictly after date-only FILING_DATE. Accession-specific acceptance timestamps are still required for more precise event timing.
- It does not calculate institutional accumulation, trades, returns, predictive power, alpha, OOS, bootstrap or LOO.
- 13F is delayed holdings disclosure, not order flow or proof of informed buying. Reported market value changes must not be confused with share accumulation.

## Decision

**PASS only for the synthetic amendment-state logic if CI succeeds. NOT ADMITTED for data, signal, or portfolio use.**

Next data gate: extend the bounded SEC parser to preserve the OTHERMANAGER table and exact accession metadata; then select a small set of complete manager-period chains and compare the reconstructed states against the original EDGAR filings. Only after that should the historical CUSIP-to-F80 coverage gate be revisited.

No SEC request, data purchase, vendor contact, portfolio test, production change or capital change was made. `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen. Options budget remains USD 0.
