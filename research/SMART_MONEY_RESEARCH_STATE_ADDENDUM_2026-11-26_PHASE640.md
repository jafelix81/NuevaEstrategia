# Smart Money Research State Addendum — Phase 640 (2026-11-26)

## Completed

- Audited official CFTC TFF release-time documentation and historical special announcements.
- Confirmed that the CFTC's usual Friday 3:30 p.m. ET schedule cannot certify historical publication time across the full archive.
- CFTC says historical release dates are only publicly listed for the latest 13 months, despite TFF position history extending to June 2006.
- Documented 2025 shutdown catch-up: report 2025-09-30 was scheduled for 2025-10-03 but actually published 2025-11-19 (47 calendar days late); subsequent reports were delayed 4–42 days.
- Also documented the 2023 ION incident, 2025-01-09 mourning-day delay, 2018/2019 shutdowns and 2015 premature/incomplete release.
- Phase 640 report: `research/PHASE640_CFTC_TFF_HISTORICAL_RELEASE_TIME_FEASIBILITY_AUDIT_2026-11-26.md`.

## CFTC source decision

- Keep 3,035 historical archive rows marked `UNVERIFIED_ARCHIVE_PROXY`; do not impute Tuesday+3-day PIT timestamps.
- Keep archive-derived 4-report changes and 52-report z-scores out of prospective feature initialization.
- Continue prospective capture using actual first-seen upper bounds and source/row hashes.
- Current prospective sample remains only two report-date clusters / eight contract observations; no predictive test is justified.
- CFTC trader categories are business-purpose classifications, not verified informed-investor identities.

## Other latest state

- Phase 639 PR #245 merged to main as `3d13c44e2267b73df3266f5a3e842e2a2fb11cdc`.
- Phase 403 Form 144 parser now rejects timezone-naive Atom `updated` values rather than silently assigning UTC. PR run 45806279188 passed 83/83 offline tests; live capture was skipped.
- Phase 638 remains merged; Form 144 ledger has 815 headers / 5,443 detail rows, 807 bounded observations, 8 expected initial-baseline rows quarantined, 0 malformed intervals, 0 exact public-availability certifications and 0 signal-eligible headers.
- SEC 13F PR chain #221–230 remains stacked and stale relative to main; final Phase 613 branch is 137 ahead / 587 behind. Rebase/rebuild before integration.
- SEC 13D/G PR #37 remains Draft on a stale Phase 347 branch; Phase 350 branch is 292 ahead / 565 behind main. Rebase/port deliberately before integration.

## Model controls

`F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen. No new alpha, OOS, bootstrap or LOO result. No universe, parameters, exposure, costs, capital, holdout or holding-period policy changes. Options-data budget remains USD 0.
