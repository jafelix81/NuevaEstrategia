# Phase 65 — SEC Form 144 PIT event-panel and proposed-supply hypothesis specification

**Date:** 2026-11-04  
**Status:** Preregistered data-assembly plan; no event returns calculated.

## 1. Objective

Convert the Phase 64 identity-validated master-index route into a reproducible Form 144/144-A event panel, then decide whether Form 144 carries incremental information about future supply/returns beyond frozen LTM/F80. Do not label the filer or seller as "smart money"; the hypothesis is specifically about a disclosed Rule 144 sell-order/proposed-sale event.

## 2. Scope and discovery

- Electronic Form 144 history begins 2023-04-13 for reporting issuers; begin at 2023Q2 and filter out filing dates before 2023-04-13.
- Extend master-index discovery through 2026Q3 (last completed quarter at this audit date).
- Use the two-CIK accession pair only for candidate discovery. Fetch the primary XML and require XML issuerCik confirmation for every event. Never infer issuer from the filer CIK or archive path.
- Keep the single ambiguous candidate pair and all future multi-candidate pairs unresolved.
- Current CIK mapping is a candidate map only. The event panel's durable security key is issuer CIK plus historical security-class/contract identity; ticker assignment must be point-in-time.

## 3. Required event fields

Preserve at minimum:
- accession, form, filing date, accepted timestamp when available, issuer CIK/name, filer CIK, seller name, relationship to issuer;
- security class, units to be sold, aggregate market value, approximate sale date, notice date;
- remarks, 10b5-1 mention, plan adoption date(s), previousAccessionNumber, tranche count;
- XML URL, master-index CIK pair, parser version, source hash, retrieval timestamp and all unresolved/ambiguous flags.

Do not drop rows with missing seller identity or missing plan details; retain field-presence flags and report missingness.

## 4. Event semantics and PIT

- Original Form 144 is transmitted concurrently with placement of a broker sell order or direct execution with a market maker under Rule 144(h)(3). It signals an intended/proposed sale order, not a verified execution.
- A bona fide intention to sell within a reasonable time is required; SEC staff CFI 120.01 says a notice is effective for at most three months. Treat the 90-day window as a possible event-validity window, not proof that a sale occurred throughout it.
- 10b5-1 plan adoption is not the Form 144 filing trigger. Keep plan adoption date separate from order/filing time.
- 144/A is an amendment/update, not a fresh sale event by default. Link previousAccessionNumber exactly as a prior reference; do not assume it is the immediately preceding amendment. Reconstruct seller + issuer + security-class lineage before deduplication.
- Filing date is public-date evidence. Capture Accepted timestamp when feasible. Baseline EOD KnowledgeDate/execution is the first full trading-session close after filing date; no same-date use. Secondary same-day-close sensitivity is allowed only if Accepted time plus a pre-registered 30-minute public-dissemination buffer is before the close. Because SEC permits Form 144 filings until 10 p.m. ET, many filings will only be actionable next session.
- Approximate sale date is descriptive only; it is never execution proof or KnowledgeDate.

## 5. Candidate supply variables (only after data gates)

Pre-register, do not tune after returns:
- Proposed sale value / trailing 20-session dollar ADV.
- Proposed units / trailing 20-session share volume.
- Proposed units / point-in-time shares outstanding or float, only if denominator is available as of KnowledgeDate.
- Count and aggregate size of distinct original notices by issuer over trailing 20/60/90 calendar days.
- Separate 10b5-1-flagged vs unflagged notices; separate affiliate/director/officer/other relationship classes where XML supports them.
- Amendments update the original event's proposed size/terms; they do not create independent supply events unless a distinct new order is evidenced.
- Do not sum multiple sellers as a concerted group without evidence; preserve seller-level events and test issuer aggregation separately.

## 6. Coverage and integrity gates before returns

- Confirm every candidate accession's XML issuerCik; report all mismatches and unresolved pairs.
- Reconstruct historical F80 membership and point-in-time CIK/ticker mapping, including predecessor issuers, ticker changes, delistings, mergers and the 27 currently unmapped tickers.
- Require at least 95% coverage of historically active F80 issuer-days in every validation block; report coverage by year, issuer size, liquidity and event type.
- Preserve filing date and Accepted timestamp where available; never use a future accepted timestamp or revised XML before its publication time.
- Reconcile amendments and duplicate notices; no event count until lineage is resolved.
- Compare proposed quantity/value against point-in-time ADV and shares outstanding; reject invalid/zero denominators rather than fill them with future data.

## 7. Economic test design (not yet authorized)

Provisional chronological split, to be frozen before forward returns:
- Development: 2023Q2–2024Q4.
- Validation/model selection: 2025.
- Locked OOS: 2026Q1–Q3.

Measure 1, 2, 5, 10, 20 and 40-session outcomes plus the notice's 90-day event window; these are diagnostics, not a prescribed holding period. Test:
1. Standalone proposed-supply effect.
2. Incremental effect after controlling for prior 1/5/20/60-session returns, volatility, market/sector, liquidity, earnings, Form 4 actual insider sales and short-flow variables.
3. Incremental value over frozen LTM/F80 under identical signal availability, exposure, entry/exit timing, turnover and costs.

Use chronological walk-forward, purging/embargo for overlapping labels, block bootstrap, issuer-clustered uncertainty, leave-one-issuer-out and multiple-testing correction. Report gross and net performance, drawdown, volatility, tail loss, turnover and capacity. No CAGR target.

## 8. Kill criteria

Kill or archive the hypothesis if:
- PIT F80 mapping/coverage or event timestamps fail;
- amendments cannot be separated from original events;
- proposed-sale quantities are too incomplete or not comparable;
- the signal is stale by the first executable EOD close;
- the effect disappears after prior-return, liquidity, event and sector controls;
- costs, turnover, concentration or capacity erase the effect;
- no robust OOS incremental improvement over frozen LTM/F80 survives bootstrap and issuer LOO.

No forward-return test is authorized until Sections 2–6 pass. F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen.
