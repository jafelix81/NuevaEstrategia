# Phase 371 — FINRA T1 ATS monthly coverage and concentration audit

**Date:** 2026-11-13  
**Disposition:** **Full-partition retrieval and symbol/participant bridge pass in the 47-month sample; strict date gate passes only 38/47. Concentration is descriptive, not a smart-money signal.**  
**No return or alpha test.**

## 1. Scope and retrieval

- Source: FINRA `weeklySummaryHistoric`, T1.
- Inventory: 1,045 historical partition pairs; 209 T1 weekly partitions available.
- Sample: one T1 week per month, closest `weekStartDate` to day 15, January 2022–November 2025.
- Selected: 47/47 monthly partitions.
- Retrieved: **2,469,987 rows across 517 pages**.
- Record-Total matched for every partition; zero retrieval errors.
- Sampled union: **3,092 symbols** and **37 participant keys**.
- This is a stratified monthly sample, not a census of all 209 weekly partitions.

## 2. Bridge and concentration feasibility

- Aggregate symbol/product rows reconciled to firm rows in **47/47 sampled partitions**.
- The broker-dealer reporting concentration calculation passed its technical gate in **47/47**.
- The calculation describes FINRA-reporting intermediaries/participants, not beneficial owners, funds, end-investors, or the direction of their positions.
- Mean of monthly mean HHI: 0.1649 (monthly range 0.1516–0.1800).
- Mean of monthly mean top-one participant share: 27.28% (range 25.64%–29.17%).
- Mean of monthly mean top-three participant share: 56.82% (range 54.25%–60.31%).
- Mean of monthly mean participant count per symbol: 19.35 (range 17.73–20.76).

These are descriptive market-structure statistics only. They do not establish predictive behavior, informed activity or return-chasing.

## 3. Date-gate decomposition

The Phase 371 strict date gate required a 21-calendar-day lag from `weekStartDate` to `initialPublishedDate` and no later update. It passed **38/47**.

The nine non-passes decompose into two distinct cases:

### Five schedule-shift weeks — no later revisions

| Week start | ATS rows | Publication lag | Post-publication update gap |
|---|---:|---:|---:|
| 2022-06-13 | 38,190 | 22 days | 0 |
| 2022-08-15 | 39,966 | 22 days | 0 |
| 2022-12-12 | 41,947 | 22 days | 0 |
| 2023-08-14 | 41,894 | 22 days | 0 |
| 2024-08-12 | 42,741 | 22 days | 0 |

These five weeks fail the exact-21-day schedule check, but every sampled ATS row has `lastUpdateDate == initialPublishedDate`. A 22-day lag is consistent with a one-business-day publication shift around U.S. market holidays, but this interpretation is not used to backdate data. Retain the actual `initialPublishedDate` for any future availability rule.

### Four weeks with post-initial revisions

| Week start | ATS rows | Rows with positive update gap | Observed positive gaps |
|---|---:|---:|---|
| 2023-11-13 | 41,124 | 2,103 | 99 and 114 days |
| 2024-02-12 | 41,461 | 3 | 65 days |
| 2025-05-12 | 47,627 | 1,831 | 2 and 7 days |
| 2025-06-16 | 46,468 | 3 | 109 days |

Across the four revision-affected weeks, **3,940 of 2,016,703 ATS symbol-level rows (0.1954%)** had positive `lastUpdateDate - initialPublishedDate`. Revisions are clustered rather than uniformly distributed.

If the five 22-day schedule shifts are accepted using their actual publication dates, 43/47 sampled months have no post-initial revisions at the row level. This does **not** mean every symbol in the four revised weeks is unusable: unaffected symbol-weeks may remain candidates if the aggregate and every firm row for that symbol are revision-stable and reconcile. Phase 374 performs that stricter symbol-level exclusion.

## 4. PIT ruling

- `initialPublishedDate` is a date, not an intraday first-receipt timestamp.
- `lastUpdateDate` identifies the latest update date, not the exact arrival time or the full intermediate-vintage history.
- A final historical response does not reconstruct all earlier versions.
- No exact PIT availability ledger is established.
- A conservative future candidate would use the first exchange session strictly after the actual `initialPublishedDate`, but only for symbol-weeks whose aggregate and all firm rows have no post-initial update and pass exact symbol-level reconciliation.
- Do not infer a same-day close execution from a date-only publication field.

## 5. Next gate

Phase 374 re-fetches the same 47 monthly partitions and calculates a revision-stable symbol-week panel:
- exclude an entire symbol-week if any `ATS_W_SMBL` or `ATS_W_SMBL_FIRM` row has missing/invalid dates or a nonzero update gap;
- accept 21/22 calendar-day publication lags only as schedule-consistent dates, without changing the actual publication date;
- combine CTS/UTP aggregate rows only when product codes are distinct and combined shares/trades exactly reconcile to firm rows;
- compute HHI only on revision-stable, exactly reconciled symbol-weeks with complete unique participant identifiers and no De Minimis bucket.

No return test is authorized until this panel, historical inactive-security identity, exact first-receipt timing, and full weekly coverage are resolved.

## 6. Controls

No forward returns, alpha, OOS, bootstrap, LOO or holdout test. No raw rows or identifiers retained. No signal admitted, no universe/parameter/capital/production change. `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen.

Run: https://github.com/jafelix81/NuevaEstrategia/actions/runs/43474430280  
Artifact: https://github.com/jafelix81/NuevaEstrategia/actions/runs/43474430280/artifacts/14065151518
