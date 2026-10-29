# Phase 44 — SEC FTD frozen-universe identity / coverage audit

## Decision

Phase 43 actual-file schema/PIT gate passed on GitHub Actions run `40800732551`. The next authorized step is identity/coverage, not alpha.

## Audit input

A 335-symbol snapshot was recovered from the Phase 21C signal panel artifact (`phase21c-sec-form4-predictability`, run `39369692938`). This is an audit snapshot of the frozen research universe, not a modification of `F80_TOP20_PARTIAL50_BASELINE_C20`.

## Representative SEC files

- 2018 first half: `cnsfails201801a.zip`; conservative knowledge date `2018-01-31`.
- 2026 second half: `cnsfails202609b.zip`; conservative knowledge date `2026-10-15`.

The audit compares direct ticker presence and ticker→CUSIP multiplicity. It deliberately does not classify a symbol absent in an old file as a data defect because the frozen universe contains securities that may not have existed or been listed at that historical date.

## PIT discipline

The FTD observation is not considered known on its settlement date. For the representative files, the audit uses conservative file-availability knowledge dates. Any future return test must use the same rule and must not use later revisions or settlement-date knowledge.

## Required next gate

The representative-file coverage test is insufficient by itself for production research. Before any FTD alpha test, construct a date-appropriate active-universe panel and deterministic CUSIP/ticker crosswalk for the actual signal dates. Measure coverage by signal date and identify ticker changes, mergers, ADR/class changes, and symbols that were not yet listed.

Only if that gate is adequate will we define pre-registered FTD features and test incremental information against frozen LTM/F80 using identical exposure/costs, chronological OOS, bootstrap and LOO. FTD will not be interpreted as short selling by assumption.

## Status

`COVERAGE_AUDIT_RUNNING`

Baseline unchanged.
