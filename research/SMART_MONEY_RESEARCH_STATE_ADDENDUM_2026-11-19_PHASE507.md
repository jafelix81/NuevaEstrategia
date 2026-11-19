# Smart Money Research state addendum — Phase 507 (2026-11-19)

- Preflight: main HEAD `2e0848589e05385c2b4cb4f759970493d9f1a5a2`; 7,895 Actions runs; latest 100 inspected, none active/queued at 20:21 UTC; latest scheduled capture 44598981676 completed successfully. No workflow was started or duplicated.
- **SEC Form 4/4-A:** run 44598981676 completed both offline and live jobs and appended 184 accession-observation rows. After two prior-watermark rows, 182 candidate occurrences resolve to 88 unique new accessions: 85 Form 4 and 3 Form 4/A. Same-feed duplicate occurrences=91; cross-feed duplicate occurrences=3. All 88 canonical events are bounded metadata only; 0 are research-observation eligible or signal eligible.
- Receipt interval for the 88 events is bounded by prior successful poll end 2026-11-19 10:27:06 UTC and first-seen upper bounds 19:30:35–19:31:19 UTC (543.48–544.22 minutes). The first conservative regular-session open after receipt is 2026-11-20. No same-day intraday use is authorized. The run began 13m17s after its nominal 19:17 UTC cron slot; no hourly cadence is established.
- **Metric correction:** per-feed `new_accession_count` had counted repeated candidate occurrences before deduplication (176 for Form 4, 6 for Form 4/A), while global `new_event_rows=88` was canonical. Phase 507 changes summaries to expose candidate occurrences, distinct candidate accessions and canonical new accessions separately. The append-only event/accession/feed ledgers and watermarks are unchanged.
- Phase 507 adds regression coverage for same-feed duplicates, cross-feed duplicates, canonical per-feed attribution, global unique/occurrence counts and fail-closed suppression. No filing XML/text or transaction rows were downloaded or persisted.
- FINRA Consolidated Short Interest remains conditional in draft PR #159; the old Phase 31 panel is incomplete, and Phase 447 still needs authorized credentials plus one successful live single-settlement validation. Do not batch historical dates before that gate.
- FINRA Reg SHO still lacks a real capture after Phase 495; the last live run 44453548570 used pre-fix code. CFTC TFF last reviewed at 3,039 rows with no new report/revision. Form 144 last scheduled capture 44521745535 remains partial; 44534689780 was PR CI, not a live recapture.
- Cboe Volatility Surfaces remains a conditional historical IV/skew/term-structure candidate. OPRA Trades/Quotes and other options products remain gated by coverage, historical first-receipt PIT, corrections, licensing and price.
- No forward-return test, event study, backtest, OOS, bootstrap, LOO or holdout test. New signals admitted: 0.
- `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen: universe, parameters, holding period, exposure, costs, holdout and production unchanged.

See:
- `research/PHASE507_SEC_FORM4_CANONICAL_ACCESSION_COUNT_AUDIT_2026-11-19.md`
- `research/PHASE507_SEC_FORM4_CANONICAL_ACCESSION_COUNT_AUDIT_SUMMARY_2026-11-19.json`
