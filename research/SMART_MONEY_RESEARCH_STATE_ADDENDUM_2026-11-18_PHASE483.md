# Smart Money Research state addendum — Phase 483 (2026-11-18)

- Re-audited the immutable Phase 35/28D SEC 13D/G artifact (run 41346788365, artifact 13107210885; ZIP SHA-256 ed92141e1474036291df07c9676129f46a0d304a7a8c21eca425d051f3184236).
- Exact date comparison across 20,266 unique accessions found 19,539 event dates before filing, 139 on filing date, 586 missing, and **2 after filing date**. Both future-dated rows are SC 13G/MS filings dated 2024-02-09 and 2024-02-12 with parsed event date 2024-12-31. Their filing_lag_business_days values are null, which hid the anomaly from the earlier lag-only audit.
- Added a fail-closed event-date classifier and 9 offline tests. The future-dated rows are quarantined; no original SEC document request was made because SEC_USER_AGENT remains a human prerequisite. filing_date remains the only knowledge date.
- Phase 20C and Phase 24B branches are stale/diverged (12/330 and 10/327 ahead/behind main respectively); do not merge them as-is. Phase 29 MOM120 remains overlapping momentum, not independent alpha.
- Latest schedule census remains 22 total events, 0 active/queued. Phase 476 has no scheduled Form 4/4-A receipt; Phase 403 latest scheduled run 44302697069 failed before live capture; FINRA 22:30/23:30 UTC and CFTC 22:25 UTC windows were still ahead at the audit cutoff.
- No return test, alpha, OOS, bootstrap, LOO, raw SEC rows or prices were added. F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen.
