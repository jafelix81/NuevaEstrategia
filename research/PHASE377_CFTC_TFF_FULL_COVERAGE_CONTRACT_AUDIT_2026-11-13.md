# Phase 377 — CFTC TFF full coverage and contract-key audit

**Status:** implementation and deterministic unit tests added; hosted full-dataset retrieval pending.  
**Parent:** Phase 376 CFTC TFF source-feasibility audit.  
**Scope:** source/data-feasibility only; no feature or return test.

## Why this phase is necessary

Phase 376 identified four candidate equity-index contract codes in the public TFF Futures Only dataset, but those code anchors were not yet validated across the complete history. The CFTC explicitly states that its dataset has no primary key, and that markets can disappear from a report when the reportable-trader threshold is not met. Therefore a code/name crosswalk, candidate-key audit and explicit missing-week accounting are prerequisites.

The audit also separates the E-mini S&P 500 series (13874A) from the S&P 500 Consolidated series (13874+). These are distinct report rows and must not be added together. CFTC historical files show both labels/codes in the same TFF report.

## Method

1. Read the Socrata dataset metadata before and after retrieval.
2. Query the official row count before and after.
3. Retrieve the complete TFF Futures Only resource in one snapshot (current dataset is approximately 47.3k rows, below the 50,000-row request ceiling used here).
4. Require exact row-count reconciliation and an unchanged metadata update stamp.
5. Audit schema fields, ID duplicates (diagnostic only), candidate natural-key duplicates, weekly coverage/gaps, code/name/exchange variants, category-position missingness and open-interest arithmetic.
6. Discover related equity-index rows by contract name rather than assuming the four candidate codes exhaust the universe.
7. Retain only an anonymized summary; no raw rows or IDs are persisted.

## Candidate series

- 13874A — E-MINI S&P 500
- 209742 — NASDAQ-100 STOCK INDEX (MINI)
- 239742 — RUSSELL 2000 STOCK INDEX (MINI)
- 124603 — DOW JONES INDUSTRIAL AVG - x $5
- 13874+ — S&P 500 Consolidated; separately reported and non-additive with the E-mini line.

These are candidates to validate, not assumed immutable mappings. Any code/name changes, duplicate report-date/code keys, missing weeks or threshold-driven disappearances remain visible in the result.

## PIT and interpretation controls

- Tuesday is the position date, not the knowledge date.
- The usual CFTC release is Friday 3:30 p.m. Eastern, with holiday and exceptional backlog delays.
- CFTC says actual historical release dates are only available for the latest 13 months and that historical data is not updated after publication.
- The 2025 catch-up schedule must use the actual catch-up dates, not original scheduled Fridays.
- Older release dates can only be labelled schedule proxies until independently verified; they cannot be called strict historical PIT.
- TFF categories are self-reported business-purpose classifications, not beneficial-owner identities or verified informed traders.
- Missing contract-weeks are not zero and must never be forward-filled.

## Competing hypotheses reserved for later

1. Leveraged Money positioning adds information beyond prior index returns, volatility and the frozen QQQ Risk ON/OFF state.
2. Apparent positioning information is return-chasing and disappears after controlling for prior returns.
3. Extreme positioning predicts crowding/downside risk rather than directional alpha.
4. TFF adds no incremental information and should be archived as redundant.

No hypothesis is tested in this phase. If data gates pass, freeze one primary E-mini S&P 500 feature and a small horizon grid before exploratory chronological tests. Compare against frozen LTM/F80 at identical exposure and costs. Do not use the legacy consumed holdout.

## Execution

- Local/hosted tests are defined in `test_phase377_cftc_tff_full_coverage_audit.py`.
- Hosted result and anonymized artifact link will be added after the branch workflow completes.
- Phase 375 FINRA T1 ATS 209-week retrieval remains a separate active workflow; this CFTC audit does not duplicate or modify it.

## Controls

No raw data retention, forward returns, alpha, OOS, bootstrap, LOO or holdout use. No vendor purchase/contact. No change to `F80_TOP20_PARTIAL50_BASELINE_C20`, production, universe, capital, parameters or exposure.

## Hosted result and Phase 378 correction — 2026-11-13

Phase 377 completed successfully in run [43497266092](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43497266092), artifact [14071613332](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43497266092/artifacts/14071613332).

- Full TFF Futures Only snapshot: 47,322 rows, 90 columns; reported count matched before/after and metadata update stamp was unchanged.
- Candidate natural key (report date, CFTC contract market code): zero duplicate groups.
- 13874A E-mini S&P 500, 209742 Nasdaq-100 Mini and 124603 Dow Jones $5 each had 1,065 report dates from 2006-06-13 through 2026-11-03.
- Russell code 239742 had 601 rows, but Phase 378 proves it is not one continuous contract: 119 old-era observations (2006-06-13–2008-09-16) and 482 new E-mini observations (2017-08-15–2026-11-03), separated by 3,255 days and different multipliers ($100 versus $50).
- Phase 377's Tuesday-anchor missing count treated 14 holiday-shifted report dates as missing for the continuous S&P/Nasdaq/Dow series. Phase 378 replaces that interpretation with interval continuity: 6–8 day report-date gaps are normal weekly observations; gaps over eight days require review.

See [Phase 378](PHASE378_CFTC_RUSSELL_CONTRACT_ERA_AUDIT_2026-11-13.md) for the contract-era and backcast ruling. No alpha or return test is authorized.
