# Phase 564 — SEC FTD release cadence, balance semantics and PIT gate

**Audit cutoff:** 2026-11-22 23:11 UTC  
**Main HEAD before this report:** `f96a5e5993c64cbf32dc3a9798cafc43b97f2e5d`  
**Disposition:** source-feasibility clarification. The SEC documents a two-part monthly release cadence, but explicitly does not guarantee posting by a particular date. FTD remains a conditional settlement-friction state candidate, not short-sale flow, participant identity, or a directional Smart Money signal. No PIT or alpha admission.

## 1. New official release-clock evidence

The SEC's Fails-to-Deliver Data page currently covers February 2004 through October 2026 and states:

- First-half data for a given month are available at the end of that month.
- Second-half data are available at about the 15th of the following month.
- From July 2009 onward, each month is split into two files.
- Before July 2009, files contain each settlement date in a calendar month and monthly files are archived by calendar quarter.
- The SEC expressly says it cannot guarantee that files will be posted by a particular date or that the data are accurate.

The current page exposes October 2026 first-half and second-half downloads. Their linked names are `cnsfails202610a.zip` and `cnsfails202610b.zip`. The retrieval interface rejected ZIP/octet-stream payloads; no bytes, redirect chain, file hash, row count or schema validation is claimed.

Official source: https://www.sec.gov/data-research/sec-markets-data/fails-deliver-data

## 2. Measurement semantics that constrain any signal

The SEC defines the quantity as the aggregate net balance of fails outstanding in NSCC's Continuous Net Settlement system, aggregated across all NSCC members. A settlement-date observation is not the number of new fails on that day:

- The balance includes prior outstanding fails, new fails on the settlement date, and fails that settle on that date.
- The age of individual fails cannot be inferred from the aggregate series.
- The underlying sources of fails can differ from one day to the next.
- Fails can occur on both long and short sales; they are not necessarily caused by short selling and are not evidence of abusive or naked short selling.
- Before 2008-09-16, only balances of at least 10,000 shares were included. From that date onward, all positive balances are included; a zero balance has no row.

Therefore FTD must not be described or modeled as daily short-sale volume, short interest, a member-level position, or a direct measure of institutional buying/selling.

## 3. PIT and missingness policy

The newly confirmed schedule improves feasibility relative to a source with no published cadence, but it does **not** create an exact historical knowledge timestamp. "End of month" and "about the 15th" are approximate targets, and the SEC explicitly disclaims a guaranteed posting date.

Required controls:

1. Store settlement date separately from file-release/first-seen date. Never use settlement date as the market-knowledge timestamp.
2. For prospective use, capture each file's first successful observation in an append-only UTC ledger, with retrieval time, requested URL, final URL, HTTP status, ETag/Last-Modified if supplied, byte count and SHA-256.
3. For historical studies, use only explicitly labeled release-lag sensitivities. The published cadence is not strict PIT proof; no finite lag can be certified from the SEC statement alone.
4. Post-2008-09-16, an absent row can represent zero only inside a successfully retrieved, complete, validated file and for a security with a valid effective-dated CUSIP mapping. Missing files, unmapped CUSIPs, incomplete files and out-of-universe securities remain unknown.
5. Pre-2008-09-16, an absent row may simply be a balance below the 10,000-share reporting threshold; it cannot be treated as zero.
6. Keep the July 2009 file-layout break and September 2008 reporting-threshold break as explicit schema/measurement regimes.

## 4. Universe and identity gate

The existing Phase 44 fixed-335 diagnostics reported 253/335 (75.522%) coverage for a 2018 first-half sample and 316/335 (94.328%) for a 2026 second-half sample. These are not date-appropriate active-universe coverage rates. They do not establish survival, listing, CUSIP continuity or historical F80 membership.

Before any return test, require:
- immutable raw-file hashes and successful parsing;
- unique settlement-date/CUSIP keys or documented duplicate adjudication (never sum/deduplicate by assumption);
- effective-dated CUSIP/security-class mapping;
- historical active/inactive/delisted/acquired universe membership;
- complete-file reconciliation and explicit zero-vs-missing treatment.

## 5. Actions / repository preflight

- Main HEAD before this report: `f96a5e5993c64cbf32dc3a9798cafc43b97f2e5d`, the Phase 563 state commit.
- Latest known overall run in the available repository audit: Phase 560 PR check [45056358765](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45056358765). Its only job, `offline-regression`, completed successfully; the 16 Form 4 tests passed; no artifact was produced. This is not a live capture.
- Latest known natural Form 144 capture: [45052961790](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45052961790). Both `offline-regression` and `live-capture` jobs completed successfully. Artifact [14765739720](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45052961790/artifacts/14765739720) is unexpired (3,646 bytes; SHA-256 `617023135a9d720d8e9dd850d2a670b68880d2c4e428eac64c7050f1e39dab33`). Its live log reconciles 285 Form 144 headers / 2,114 detail rows, 278 bounded backfill accessions pending, zero parse errors and zero source-hash mismatches.
- The connector used for this audit exposes jobs/artifacts/logs for known run IDs but not the repository-wide Actions run-list endpoint. Consequently, this run does not claim a fresh full run count or a current zero-active-run census. Phase 563's last full inventory at 22:50 UTC reported 8,069 total runs, 96 successes / 4 failures in the latest 100, and zero active/queued.
- Four branch-search pages reconciled 372 branches; the open-PR search returned 72. PR [#204](https://github.com/jafelix81/NuevaEstrategia/pull/204) remains Draft/open. A fresh compare against current main shows 11 commits ahead / 8 behind (diverged); it is mergeable at GitHub metadata level but is not ready for review or merge. No merge, dispatch, rerun, cancellation, cron change or duplicate workflow was performed.
- Human prerequisite for the bounded Phase 43/44 SEC download remains the repository Actions secret `SEC_USER_AGENT`, containing a project identifier and monitored contact. Secret values cannot be inspected or configured through the connected interface. No live SEC request was made.

## 6. Decision and next gate

- FTD is retained as a **low-frequency settlement-friction / market-stress state candidate**.
- The new SEC cadence is useful for designing a prospective first-seen clock, but historical FTD is not strict-PIT admitted.
- Do not infer directional smart-money intent from FTD levels or changes.
- After `SEC_USER_AGENT` is configured, perform only the bounded two-file validation (one first-half and one second-half file), record bytes/hashes/schema/coverage, and then build a prospective first-seen ledger. Do not begin full backfill before that gate passes.
- No new signals admitted; no event/return/backtest/OOS/bootstrap/LOO/holdout test; no change to universe, costs, exposure, holding-period policy or production.
- `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen.
