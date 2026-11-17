# Phase 448 — FINRA short-interest five-year history, credential entitlement and scheduled-capture re-arm

**Audit time:** 2026-11-17 03:09 UTC  
**Disposition:** FINRA history is feasible for a five-year backfill, but PIT vintages are not recoverable retrospectively; one live settlement validation remains blocked by missing credentials. SEC/CFTC scheduled captures have missed expected slots, so their existing schedules were re-armed by changing only the cron minute. No signal or alpha admitted.

## 1. Repository and Actions preflight

- Repository: `jafelix81/NuevaEstrategia`; default branch `main`.
- Main HEAD before this phase: `aee5157cdd41f050efc90272ab9bbaf23b01be19`.
- Actions API reports 7,690 total runs. The latest 30 were inspected; all were completed. No in-progress or queued run appeared in that latest-run page.
- Latest main run: [44007937167](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44007937167), Phase 447, completed successfully: Python compilation and 14/14 synthetic contract tests; no artifact expected.
- Latest Phase 447 PR run: [44007864107](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44007864107), completed successfully.
- Branches: 283 across three pages (100/100/83). Open PRs: 56. Workflow files: 67.
- The five branch-push runs for the Phase 447 live-validation workflow were inspected:
  - [44007395522](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44007395522) failed while parsing the push-event settlement-date input (`ValueError: unconverted data remains: }`); no FINRA request was made.
  - [44007455201](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44007455201), [44007632615](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44007632615), [44007651513](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44007651513) and [44007662531](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44007662531) stopped at the credential guard; no FINRA/FIP request was made.
  - The main-branch live-validation workflow is now `workflow_dispatch` only. No scheduled or automatic push capture is configured for FINRA.

## 2. FINRA short-interest historical coverage — official source audit

FINRA's current **About Equity Short Interest** page states that:
- the interactive grid contains five rolling years;
- the Equity API contains up to five rolling years;
- historical files are available for download;
- publication occurs on the seventh business day after settlement, and the API data is available by 4:40 p.m. ET on the publication date;
- when corrections are made, a revision flag appears, but only the most recent data is made available.

Official page: https://www.finra.org/finra-data/browse-catalog/equity-short-interest

The separate **Equity Short Interest Files** page says its archive files going back to 2014 contain **OTC equity securities only**:
https://www.finra.org/finra-data/browse-catalog/equity-short-interest/files

Implications:
1. The five-year API window is sufficient in principle for the 106 settlement dates in the old Phase 31 panel (approximately June 2022–September 2026), subject to live row-count reconciliation.
2. The OTC-only archive is not a substitute for the all-market API for the frozen 335-name universe. It may be used only as a separately labelled OTC subset if relevant.
3. Five-year historical API data is current/restated history, not a preserved as-known vintage. A historical backfill can support coverage/warm-up diagnostics but cannot reconstruct the exact values first known to the market at each past date. Prospective capture and revision-event logging are required for strict PIT use.
4. The old Phase 31 synchronous extracts remain killed: all 102 successful calls stopped at 5,000 rows and the symbol sample was truncated. No missing ticker can be inferred as zero from those files.

## 3. Credentials and terms

The FINRA Developer Center lists `consolidatedShortInterest` under API credential types Public, Firm and Organization. Its Individual User guidance says individual accounts can provision Public and Mock credentials for individual investors/researchers accessing public data for their own non-commercial purpose; it is not intended for commercial use.

Official docs: https://developer.finra.org/docs

Operational route:
- For strictly personal/non-commercial research, an Individual/Public credential is the documented path.
- For firm, client, commercial or third-party use, do not rely on an Individual credential; obtain the appropriate Firm/Organization credential and comply with the applicable terms.
- Preferred GitHub Actions secrets for the current client: `FINRA_CLIENT_ID` and `FINRA_CLIENT_SECRET`. A valid short-lived `FINRA_ACCESS_TOKEN` is an alternative. Never put credentials in repository files or workflow YAML.

The async API supports up to 100,000 rows per request, with a 60-second minimum polling interval and a pre-signed S3 result URL that must be downloaded before expiry without an Authorization header. The Phase 447 client reconciles the completed response's record metadata against downloaded rows. It deliberately does not guess offsets or partitions.

## 4. SEC Form 144 and CFTC TFF schedule audit

### SEC Form 144

- Latest scheduled run remains [43970444015](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43970444015), created 2026-11-16 22:28 UTC, before Phase 444's independent-feed persistence fix was merged.
- Offline regression passed; live capture failed on Form 144/A after four 60-second read attempts. The state commit was skipped and no artifact was produced.
- Phase 444's correction passed 18/18 tests in [43990197952](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43990197952), but no post-merge scheduled live capture appears in the latest Actions page. The :37 UTC slots at 01:37 and 02:37 on 2026-11-17 were not observed.
- Existing hourly schedule was moved from :37 to :47 UTC to re-arm the existing workflow. It remains the same workflow and concurrency group; no manual poll or duplicate workflow was started.

### CFTC TFF

- Latest run remains [43525140200](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43525140200), a 2026-11-13 branch-push/bootstrap, not a scheduled prospective capture.
- It recorded 3,035 historical warm-up rows, zero signal-eligible historical rows, and no new prospective event. Artifact [14084802705](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43525140200/artifacts/14084802705) is 1,068 bytes, SHA-256 `c7a652038336f852e3c51792d1bdc96ebc1368176bdafdae0693332fb4224eef`.
- The 2026-11-16 22:15 UTC weekday schedule slot was absent. The existing cron was moved from 22:15 to 22:25 UTC. This is a re-arm of the same workflow, not a manual backfill.
- If the 2026-11-17 22:25 UTC scheduled poll succeeds, the 2026-11-10 report will be recorded with the actual first-receipt timestamp. It will not be backdated to the CFTC publication time. Any research use begins no earlier than the first regular equity session after that receipt.

## 5. Phase 448 changes

- Updated `.github/workflows/phase403_sec_form144_first_seen_capture.yml`: hourly cron :37 → :47 UTC.
- Updated `.github/workflows/phase384_cftc_tff_prospective_capture.yml`: weekday cron 22:15 → 22:25 UTC.
- Added this audit report and a concise entry to `SMART_MONEY_RESEARCH_STATE.md`.
- No workflow was manually dispatched or rerun. The latest-run page showed no active/queued execution before the edits.
- The Phase 403 workflow's pull-request path filter includes its own YAML file, so the PR should run offline regression only; live capture is skipped on pull_request. The CFTC workflow has no pull_request trigger; its only change is the cron minute.

## 6. Research disposition and next gates

1. Phase 31 short-interest panel remains **KILLED AS RETRIEVED**. Do not reuse its coverage, zero-fill, or alpha diagnostics.
2. FINRA consolidated short interest remains a **conditional source candidate**. After credentials are configured, run exactly one settlement-date live validation and inspect the non-raw manifest before any 106-date batch.
3. Keep the raw historical download private. Do not upload original FINRA rows to the public repository or Actions artifacts.
4. Recheck the SEC :47 schedule after merge; confirm whether Phase 444 preserves successful-feed observations when the other feed times out.
5. Recheck the CFTC :22:25 scheduled poll; preserve actual first receipt and never backdate.
6. No source signal, return, OOS, bootstrap, LOO or holdout test was run. `F80_TOP20_PARTIAL50_BASELINE_C20`, universe, parameters, capital, exposure, holdout and production remain frozen.

## References

- FINRA About Equity Short Interest: https://www.finra.org/finra-data/browse-catalog/equity-short-interest
- FINRA Equity Short Interest Files: https://www.finra.org/finra-data/browse-catalog/equity-short-interest/files
- FINRA Developer Center / Query API: https://developer.finra.org/docs
- FINRA short-interest publication schedule: https://www.finra.org/filing-reporting/regulatory-filing-systems/short-interest
