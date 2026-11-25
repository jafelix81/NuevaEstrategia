# Phase 613 — SEC Form 13F after-hours legal dissemination floor

**Audit cutoff:** 2026-11-25 04:12 UTC (2026-11-24 21:12 America/Hermosillo)  
**Base:** `phase612-xnys-session-knowledge-clock-audit` at `36ee35b2647afba2da46848bb451e39688ff94a6`  
**Disposition:** tighten the 13F daily knowledge clock so a collector timestamp cannot backdate a filing before its official filing date or the EDGAR dissemination window. This is a point-in-time control, not an alpha result.

## 1. Why this correction was needed

Phase 612 used `max(EDGAR Accepted, collector first-seen)` when a prospective collector timestamp was available. That was conservative relative to acceptance alone, but it did not explicitly enforce the official Filing Date as a lower bound.

The SEC's filing-status guidance says that most submissions received after 5:30 p.m. ET receive the next business day's 6:00 a.m. filing date and are not disseminated by EDGAR until the next business day. The listed after-hours exceptions include Forms 3, 4, 5 and 144, but not Form 13F:

- SEC, **Determine the Status of My Filing**: https://www.sec.gov/submit-filings/filer-support-resources/how-do-i-guides/determine-status-my-filing
- Regulation S-T, 17 CFR §232.13: https://www.ecfr.gov/current/title-17/section-232.13

Therefore, a 13F Atom-feed observation timestamp that falls before the legal filing-date window must not be accepted as an earlier knowledge time.

## 2. Phase 613 rule

When a collector first-seen upper bound exists:

`effective_knowledge = max(EDGAR accepted, first-seen upper bound, Filing Date 06:00 ET)`

- If the first-seen upper bound is earlier than 06:00 ET on the official Filing Date, the clock is floored at 06:00 ET on that date.
- If a 13F is accepted after 17:30 ET and the collector claims first-seen on that same ET calendar date, the event is rejected for manual adjudication. Ordinary 13F submissions are not in the SEC's listed after-hours dissemination exceptions.
- If no prospective first-seen exists, Phase 612's end-of-legal-Filing-Date fallback remains unchanged.
- The first-seen timestamp remains an upper bound from a successful poll interval, not an exact public-release time. The output now keeps `legal_filing_date_floor_utc` fixed at 06:00 ET and keeps the no-first-seen end-of-day fallback as a separate effective-knowledge rule.

This rule is specific to Form 13F. Do not apply it to Form 4 or Form 144: their after-hours treatment is different.

## 3. Regression coverage

New cases cover:
- After-hours 13F accepted the prior evening, with a first-seen upper bound before 06:00 ET on the legal Filing Date.
- First-seen after the legal floor.
- Same-day first-seen after a 17:30 ET acceptance (must be quarantined).
- Acceptance exactly at 17:30 ET (does not trigger the after-hours quarantine).
- Weekend first-seen of a Friday filing without changing the filing date.

The existing XNYS calendar, DST, early-close, holiday, and next-session tests remain in place.

## 4. Repository / Actions preflight

Before implementation:
- Phase 612 PR #229 remained open as a draft, based on Phase 611.
- Its push-triggered XNYS calendar audit run 45538801811 completed successfully; the artifact was present.
- Its PR check run 45538905972 completed the offline regression successfully and skipped the calendar-audit job.
- No active Phase 612 job was found.
- No Phase 613 branch existed before this work.
- The latest persisted Form 4 poll was run 45533818624 (started 2026-11-25 02:33:51 UTC, ended 02:34:18 UTC); both jobs succeeded and artifact 14986800169 was present.
- The latest persisted Form 144 poll was run 45523407949 (created 2026-11-25 01:07:48 UTC); both jobs succeeded and its three artifacts were present.
- FINRA Reg SHO remains fail-closed; CFTC TFF remains context-only. No source was promoted.

The new Phase 613 workflow is pull-request-only and offline-only: it does not call SEC, download filings, or modify capture state. Initial checks [45545873463](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45545873463) and [45545895847](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45545895847) each completed 20/20 tests; the push trigger was removed afterward to avoid duplicate runs.

## 5. Research disposition

- This closes a legal-dissemination timing gap in the 13F clock.
- It does not establish a historical first-seen series; no prospective 13F collector is present on main.
- It does not resolve effective-dated CUSIP/FIGI-to-ticker identity or the historical F80 coverage gap.
- No return/event study, signal test, OOS, bootstrap, or LOO was run.
- No data purchase, quote request, license acceptance, or paid sample occurred.
- `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen.
