# Phase 48 — SEC 13D/13G historical coverage gate

**Date:** 2026-10-29  
**Status:** DESIGN / DATA-FEASIBILITY GATE ONLY  
**Baseline:** `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen

## Current state

Phase 35 already contains a reproducible SEC 13D/13G PIT event-audit runner. It uses issuer-specific SEC `submissions/CIK*.json` data, identifies `SC 13D`, `SC 13G`, `SC 13D/A`, and `SC 13G/A`, and resolves the accession's primary document from EDGAR. The runner treats `filing_date` as the point-in-time knowledge date and parses the event date and ownership fields from the filing itself.

This phase does **not** create a second event parser. It defines the next gate needed before any economic test: demonstrate historical coverage against the frozen 335-name universe without using a current-only ticker universe as a proxy for historical membership.

## Gate objective

For representative historical windows, measure:

1. frozen-universe names with a deterministic historical issuer CIK;
2. names for which SEC submissions can be queried successfully;
3. names with at least one 13D/13G filing in the window;
4. event filings whose accession resolves successfully;
5. coverage by form (`13D`, `13G`, amendments);
6. event-date availability and filing-date availability;
7. whether the issuer was actually an investable/active member of the research universe at the signal date;
8. CUSIP/FIGI identity continuity where available;
9. false-zero risk: distinguish `active issuer + no filing` from `issuer not active / identity unresolved`.

## PIT rules

- `filing_date` is the earliest usable knowledge date.
- `event_date`, ownership percentage, beneficial shares, voting/dispositive power, and purpose text are not usable before `filing_date`.
- A current ticker→CIK mapping must not be used to infer that the same ticker represented the same economic security historically.
- A filing's `report_date` is descriptive, not the knowledge date.
- No backtest is permitted until historical identity and active-universe coverage pass the gate.

## Hypothesis to preserve for later testing

Do **not** label 13D/13G activity as smart money. The testable hypothesis is narrower:

> Large beneficial-ownership disclosures or changes in beneficial ownership may contain incremental information about subsequent returns after controlling for the frozen LTM/F80 information set.

Potential signal families, only after the data gate passes:

- new >5% beneficial ownership event;
- change in ownership percentage;
- activist/control-intent 13D versus passive/QII 13G;
- magnitude of ownership change;
- repeated accumulation by the same reporting person;
- amendment-based persistence/reversal.

All variants must be selected on training data only and evaluated chronologically out of sample.

## Kill criteria

Kill 13D/13G for the F80 line if historical identity/active-universe coverage is materially below the frozen-universe requirement, if timestamps cannot be reproduced, or if the eventual incremental OOS effect disappears after controlling for F80/LTM, costs, exposure, and multiple-testing corrections.

No production change is authorized by this phase.
