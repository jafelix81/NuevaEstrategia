# Phase 245 — SEC FTD external timeline backfill and status-label correction

**Audit date:** 2026-11-09  
**Status:** `EXTERNAL_TIMELINE_CONTEXT_ONLY_BACKFILL_CONFIRMED_LABEL_METHOD_UNDOCUMENTED`  
**Control:** `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen.  
**Scope:** Re-audit of the public ChartExchange FTD Release History page after Phase 244. No FTD values were downloaded, no return test was run, and no historical PIT admission is made.

## Executive finding

Phase 244 understated the visible historical span of the ChartExchange page. The currently rendered page includes records as far back as **July 2009**, not merely October 2021. That longer display is not a longer point-in-time receipt history: many older rows show common importer-retrieval dates of **2021-10-08** or **2022-05-03**, years after their expected release dates and file modification dates. Those are bulk/backfill observations, not contemporaneous historical receipts.

A second ambiguity is material: the row-level “early/on time/late” label does not consistently reconcile to one documented date field across recent and backfilled rows. The page says it compares expected, file-modification and retrieval dates, but does not document which date drives the badge or summary classification in each case.

**Decision:** downgrade ChartExchange's FTD timeline from a conditional historical known-by proxy to **contextual release/metadata evidence only**. Do not use its retrieval dates, row badges, or page-level early/on-time/late percentages as a historical PIT ledger or as a calibrated publication-delay distribution.

## 1. Corrected visible historical span

The rendered page observed on 2026-11-09 contains, among others:

| Example | Expected | File Time | Retrieved | Displayed label |
|---|---|---|---|---|
| Oct 2026, first half | 2026-11-02 | 2026-10-15 | 2026-10-30 | 3 days early |
| Oct 2016, first half | 2016-10-31 | 2016-10-28 | 2021-10-08 | 3 days early |
| Jul 2009, second half | 2009-08-17 | 2009-08-04 | 2022-05-03 | 13 days early |

The page also shows 2010–2013 entries with the same 2022-05-03 retrieval date and 2016-era entries with 2021-10-08 retrieval dates. The page therefore provides a much longer retrospective metadata catalog than Phase 244 described, but its old retrieval dates are explicit evidence of later batch ingestion.

Sources and rendered-page locations:
- ChartExchange FTD Release History: https://chartexchange.com/docs/ftd-release-history/
- Oct 2026 example: lines 68–75 of the rendered page.
- Oct 2016 example: lines 2313–2329.
- Jul 2009 example: lines 3924–3931.
- 2012–2013 examples with 2022-05-03 retrieval: lines 3118–3226.

This was a manual rendered-page audit, not a complete programmatic census. The live page was not archived or cryptographically hashed.

## 2. Status-label semantic inconsistency

The Oct 2026 first-half row's “3 days early” label matches its **Retrieved** date (2026-10-30 versus expected 2026-11-02), not its File Time (2026-10-15, 18 days before expected).

By contrast, the Oct 2016 first-half row's “3 days early” label matches its **File Time** (2016-10-28 versus expected 2016-10-31), not its Retrieved date (2021-10-08). The Jul 2009 second-half row's “13 days early” label likewise matches File Time (2009-08-04 versus expected 2009-08-17), not Retrieved (2022-05-03).

This suggests an undocumented fallback or mixed-field calculation for historical backfills. It is not safe to interpret the page's 28.4% early / 50.8% on-time / 20.7% late summary as an empirical distribution of actual first-publication delays until the provider documents the exact classification algorithm and denominator.

## 3. PIT and value-vintage consequences

1. A 2021/2022 importer retrieval date for a 2009–2016 file is not the date that file first became public.
2. The page does not establish whether a recent retrieval date is the importer's first receipt, a later re-fetch, or the latest retrieval.
3. The page does not bind each historical retrieval record to immutable ZIP bytes and SHA-256.
4. The current SEC archive may contain values that differ from earlier versions; no historical value-vintage chain is shown.
5. A date-only field cannot justify same-day execution even if its first-receipt semantics were later confirmed.

Consequently, the timeline cannot supply a strict historical knowledge clock for the underlying FTD values. At best, a future verified first-receipt log could establish a conservative date-only known-by boundary for a specific immutable file. That evidence is not currently present.

## 4. Updated source disposition

| Gate | Result |
|---|---|
| Public historical metadata catalog | PASS — visible examples from 2009 through 2026 |
| Complete programmatic census of the page | NOT PERFORMED |
| First-versus-latest importer retrieval semantics | NOT ESTABLISHED |
| Historical batch/backfill contamination | CONFIRMED |
| Row badge / summary classification algorithm | NOT DOCUMENTED; examples show mixed-field behavior |
| Immutable ZIP/hash by historical receipt | NOT ESTABLISHED |
| Historical correction/value vintages | NOT ESTABLISHED |
| Effective-dated CUSIP-to-permanent-security identity | NOT ESTABLISHED |
| Inactive/delisted return linkage | NOT ESTABLISHED |
| Historical PIT / alpha admission | NO |

**Disposition:** FTD remains a settlement-friction / fails-balance context source only. It is not short-sale flow, short interest, an institutional identity measure, or proof of abusive short selling. The 2008-09-16 reporting-threshold break and Phase 102/106 identity blockers remain in force.

## 5. Next admissible work

- Do not spend time expanding the historical FTD backfill unless a genuinely immutable, first-receipt/vintage source becomes available.
- If prospective FTD capture is ever implemented, preserve SEC index and exact ZIP bytes, SHA-256, HTTP headers, URL, pipeline receipt timestamp and every revision append-only. First scheduled capture is baseline-only.
- Keep FTD out of stock-selection and return tests until identity, inactive-security coverage, publication time and value vintages all pass.
- Continue higher-priority work on authorized N-PORT raw filings and conditional Cboe execution data rather than treating a long retrospective FTD archive as PIT history.

## Controls

No FTD returns or alpha were tested; no bootstrap/LOO, chronological OOS or holdout was used. No vendor was contacted, no data was purchased, and no production, universe, capital or baseline setting changed. The legacy holdout remains `CONSUMED_NOT_PRISTINE`.
