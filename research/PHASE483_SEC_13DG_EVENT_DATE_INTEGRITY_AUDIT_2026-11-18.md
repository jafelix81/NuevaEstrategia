# Phase 483 — SEC 13D/G event-date integrity correction

**Audit cutoff:** 2026-11-18 16:36:52 UTC  
**Disposition:** **EXACTLY TWO FUTURE-DATED EVENT-DATE PARSE CANDIDATES FOUND; QUARANTINE THEM; KEEP FILING DATE AS THE ONLY KNOWLEDGE DATE. NO SIGNAL OR ALPHA ADMISSION.**

## 1. Preflight — current repository and Actions

- Default branch: \`main\`; main HEAD at preflight: \`185c0f1530acf188c5274b335116f7f37b9c2174\` (Phase 482).
- Actions: 7,844 total runs; latest 100 contained 56 pull-request, 41 push and 3 schedule events. Explicit status queries: 0 in progress, 0 queued.
- Schedule-filtered history: 22 runs total. Latest schedule events: Phase 403 run [44302697069](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44302697069) (failure, 12:18 UTC), CFTC Phase 384 [44232546204](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44232546204) (success, 03:44 UTC), and Phase 403 [44228413864](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44228413864) (success, 03:09 UTC).
- Branch census: 311 branches. The old \`phase20c-finra-walkforward\` branch is 12 commits ahead / 330 behind main; \`phase24b-options-historical-audit\` is 10 ahead / 327 behind. Neither is a safe merge candidate; their historical code was not copied or merged.
- Open PRs: 56. PR #143 (Phase 482) is merged. PR #61 (Phase 385 ATS publication clock) remains a draft based on an old Phase 375 branch; it explicitly does not authorize return testing. PR #1 (Phase 29) remains a draft; Phase 480 already adjudicated MOM120 as overlapping the existing momentum family, not new alpha.
- Inspected current main workflows for SEC Form 4/4-A (Phase 476), SEC Form 144 (Phase 403), FINRA Reg SHO (Phase 469) and CFTC TFF (Phase 384), plus Phase 467–482 research reports and relevant artifacts. No running workflow was duplicated.

### Capture windows at cutoff

- Phase 476 Form 4/4-A: cron \`17 * * * 1-5\`; no schedule-triggered run exists in the complete 22-run schedule history after merge. The 16:17 UTC slot had passed; no live first-seen artifact or receipt exists.
- Phase 403 Form 144: cron \`47 * * * *\`; latest schedule run remains 44302697069, which failed before live capture. The next :47 slot after this audit cutoff is 16:47 UTC. Do not infer disabled state from missing runs; the read connector does not expose administrative workflow state.
- Phase 469 FINRA Reg SHO: existing 22:30 and 23:30 UTC slots are still ahead at this cutoff.
- Phase 384 CFTC TFF: existing 22:25 UTC slot is still ahead.
- No manual dispatch, rerun, cron change or replacement workflow was made.

## 2. Source artifact independently rechecked

Downloaded the existing Phase 35/28D artifact from run [41346788365](https://github.com/jafelix81/NuevaEstrategia/actions/runs/41346788365), artifact [13107210885](https://github.com/jafelix81/NuevaEstrategia/actions/runs/41346788365/artifacts/13107210885).

- Artifact size: 603,353 bytes.
- ZIP SHA-256: \`ed92141e1474036291df07c9676129f46a0d304a7a8c21eca425d051f3184236\` (matches the previously recorded artifact digest).
- Members: \`phase28d_events.csv\` and \`phase28d_summary.json\`.
- CSV SHA-256: \`28024919574c15fffd6c9adfa5ea7becf4119f6601bb8ebd13658ef28a9bd8f2\`.
- No SEC request was made. No raw CSV or filing content was committed to GitHub.

## 3. Exact date reconciliation

The CSV contains 20,266 rows and 20,266 unique accessions across 303 tickers/issuer CIKs. There are no duplicate or missing accession rows.

| Event-date relation to filing date | Rows |
|---|---:|
| Event date before filing date | 19,539 |
| Same calendar date | 139 |
| Event date after filing date | **2** |
| Event date missing | 586 |
| Invalid event date | 0 |
| Invalid/missing filing date | 0 |
| **Total** | **20,266** |

Event-date coverage remains 19,680 / 20,266 = **97.11%**. The form counts are 215 SC 13D, 1,209 SC 13D/A, 5,509 SC 13G and 13,333 SC 13G/A. Amendments account for 14,542 / 20,266 = **71.76%**.

### Two future-dated rows

Both cases are Morgan Stanley (\`MS\`), original SC 13G filings:

| Filing date | Parsed event date | Accession |
|---|---|---|
| 2024-02-09 | 2024-12-31 | 0000895421-24-000126 |
| 2024-02-12 | 2024-12-31 | 0000895421-24-000178 |

The existing \`filing_lag_business_days\` field is null on both rows. The earlier audit's business-day lag routine therefore failed to surface the future-event condition as a positive anomaly count. Direct date comparison establishes that there are **exactly two** future-dated candidates in this artifact, not merely “at least two.”

**Interpretation:** these are unresolved extraction/semantic anomalies, not verified future ownership events. The parser may have captured a reporting-period or unrelated date near the event-date label. The underlying SEC documents must be inspected before assigning a meaning. Until then, both rows are quarantined from event-date-based analysis.

## 4. Correction implemented

Added \`research/phase483_13dg_event_date_integrity_audit.py\` and an offline regression suite.

The classifier now explicitly separates:

- \`BEFORE_FILING\`
- \`SAME_DAY\`
- \`AFTER_FILING_UNRESOLVED\`
- \`MISSING_EVENT_DATE\`
- \`INVALID_EVENT_DATE\`
- \`INVALID_OR_MISSING_FILING_DATE\`

It does not rely on \`filing_lag_business_days\` to detect future dates. Duplicate accessions are counted, not silently collapsed. The summary preserves the original row count and form counts.

Local validation: **9/9 tests passed**, including the exact failure mode where a future event date has a blank business-day lag. The GitHub Actions PR workflow runs the same offline tests; no SEC or market-data request is made.

## 5. PIT and research disposition

- \`filing_date\` remains the conservative knowledge-date field. \`event_date\` is never a substitute for public availability.
- Date-only historical filings are usable no earlier than the next eligible session under the existing conservative rule; no same-day intraday availability is inferred.
- The two future-dated candidates are quarantined pending original-document review. Do not impute their event dates or treat the null lag as a zero/ordinary lag.
- The 71.76% amendment share and sparse reporting-person/purpose fields still require deterministic reporting-group and amendment-state reconstruction.
- The 27 unresolved frozen-universe tickers and historical active-universe membership remain unresolved. No reduced-subset return test is authorized.
- No feature, forward return, backtest, OOS, bootstrap, LOO or holdout was run. No alpha or source signal was admitted.

## 6. Human dependency and next gate

The original SEC parent-document retrieval path remains blocked until the repository Actions secret \`SEC_USER_AGENT\` contains a project identifier and monitored contact email. Do not retry SEC requests before that secret is correctly configured. Once available, inspect the two accessions above against the original filing headers/body and footnotes, then classify the parser issue. Do not paste the contact email into chat.

After that, continue only with the pre-registered 13D/13G gates: deterministic original/amendment lineage, reporting-group identity, historical universe membership, separate 13D versus 13G hypotheses, and filing-date-only availability. Any later return test must compare against frozen LTM/F80 with identical exposure and costs, chronological OOS, issuer-clustered bootstrap/LOO and return-chasing controls.

## 7. Frozen controls

\`F80_TOP20_PARTIAL50_BASELINE_C20\` remains frozen. No universe, parameter, holding-period, capital, exposure, cost, holdout or production change.
