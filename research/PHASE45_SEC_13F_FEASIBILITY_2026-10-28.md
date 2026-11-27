# Phase 45 — SEC Form 13F historical feasibility gate

**Date:** 2026-10-28
**Status:** audit in progress
**Scope:** data feasibility only; no alpha test.

## Why 13F is worth auditing

The SEC publishes structured Form 13F datasets extracted from EDGAR XML. The official SEC dataset page lists quarterly historical datasets from July 2013 through August 2026, including continuous quarterly coverage from 2013 onward and representative files for 2018 and 2026. The datasets are presented as as-filed structured data and are updated quarterly.

## PIT rule

A 13F holding is economically known only at the filing/acceptance date, not at the report quarter-end date. The research must therefore retain both `period_of_report` and `filing/acceptance date`, and signals may use the position only after the latter. Amendments/restatements must be handled deterministically.

## Hypothesis status

Institutional ownership is treated as a hypothesis about information, not as proof of informed trading. Possible future signals include changes in holdings, concentration, new positions and exits, but only after the source passes schema/coverage/PIT gates and an incremental OOS test versus frozen F80/LTM.

## Current gate

Audit representative SEC 13F datasets from 2018 Q1 and 2026 Q2 for structured security identity, manager identity, report dates and filing/acceptance dates. If this passes, the next gate is a filer-level PIT holdings panel plus date-appropriate CUSIP crosswalk to the frozen research universe. No production change is authorized.
