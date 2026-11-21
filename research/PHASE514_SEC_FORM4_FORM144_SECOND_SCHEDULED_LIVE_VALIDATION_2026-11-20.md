# Phase 514 — SEC Form 4 and Form 144 second scheduled live validation

**Date:** 2026-11-20  
**Base main before this documentation:** `8850828f4f76576eba789b907504d23e72d49a9b`  
**Disposition:** both structured parsers have now completed scheduled live runs and persisted non-empty append-only ledgers. This closes the recurring scheduled-delivery gap, but does not admit either source as a predictive feature.

## 1. Actions inventory before work

Repository: `jafelix81/NuevaEstrategia`; default branch: `main`.

- Actions inventory: 7,924 total runs; latest 100 contained 77 successes, 22 failures and 1 cancellation; zero queued or in-progress runs.
- Open pull requests: 60.
- Branch listing: 334 branches across the four inspected pages.
- The latest relevant scheduled jobs were completed before this phase began. No workflow was manually dispatched, rerun or duplicated.
- Current main advanced through the two scheduled data commits:
  - Form 4: `abf97fb7eab6a42e5db284382dca79b05017e212`.
  - Form 144: `8850828f4f76576eba789b907504d23e72d49a9b`.

## 2. SEC Form 4 — Phase 510 live validation

**Run:** [44656159115](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44656159115)  
**Artifact:** [14592859142](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44656159115/artifacts/14592859142)

Both `offline-regression` and `live-capture` succeeded.

The scheduled feed capture recorded:
- 457 new canonical Form 4 accessions.
- Zero new Form 4/A accessions.
- 1,001 accession-observation rows in the poll output and 457 canonical event observations.
- The capture did not download filing XML as part of the original first-seen metadata pass.

The Phase 510 structured backfill then processed 10 accessions:
- 10/10 parsed; zero parser errors.
- 22 rows appended: 10 filing headers and 12 transaction rows.
- Transaction-code counts: P=3, M=2, F=1, A=5, S=1.
- One multiple-owner filing was quarantined; nine filings had a single reporting owner, but remain filing-grain only (not an independently verified owner-to-line attribution).
- 1,190 bounded accessions remain in the structured backfill queue.

All 22 rows remain non-signal:
- `research_observation_eligible=false`.
- `public_availability_certified=false`.
- `same_day_intraday_use_authorized=false`.
- `security_identity_verified=false`.
- `historical_f80_membership_verified=false`.
- `owner_attribution_verified=false`.
- `transaction_semantics_verified=false`.
- `economic_event_new_trade_authorized=false`.

The parser downloaded XML during structured retrieval and stored its SHA-256, but the original first-seen event ledger did not contain an XML hash. Therefore all 22 rows correctly show `source_hash_comparable=false` and `NOT_COMPARABLE_NO_ORIGINAL_XML_HASH_IN_EVENT_LEDGER`. This is not a hash mismatch.

The poll's first-seen interval is metadata-only and spans from 2026-11-19 19:31:20 UTC to 2026-11-20 01:47:52 UTC. The first-seen upper bound is not an exact public-availability timestamp. No same-day intraday use is authorized.

## 3. SEC Form 144 — Phase 509 live validation

**Run:** [44662324343](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44662324343)  
**Artifact:** [14595524069](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44662324343/artifacts/14595524069)

Both `offline-regression` and `live-capture` succeeded.

The scheduled capture recorded:
- Both Form 144 and Form 144/A feeds successful.
- Pagination complete on both feeds.
- No feed errors and no possible feed-window gap.
- 103 feed-observation rows appended.
- 70 new XML blocks resolved.
- 10 accessions processed by the structured-detail backfill in this run; zero parse errors.
- 54 detail rows appended in this run.
- 368 accessions remain in the structured-detail backfill queue.

The persisted `sale_details.csv` contains 80 distinct accessions and 596 detail rows across 61 issuer CIKs:
- 80 `filing_header` rows.
- 80 `securities_information` proposed-sale tranches.
- 169 `securities_to_be_sold` acquisition-history rows.
- 267 `securities_sold_in_past_3_months` historical-sale rows.

All 596 rows have `parse_status=parsed`; all 596 have matching source-XML and first-seen event-ledger SHA-256 hashes. Field completeness in this current ledger:
- Proposed-sale tranches: 80/80 have units, aggregate market value, units outstanding and approximate sale date.
- Acquisition lots: 169/169 have acquisition date, amount and nature of acquisition.
- Prior-sale rows: 267/267 have sale date, amount and gross proceeds.

All rows remain `signal_eligible=false`, `public_availability_certified=false` and `same_day_intraday_use_authorized=false`. The first-seen interval is bounded by successful polls, from 2026-11-19 21:00:26 UTC to 2026-11-20 02:39:37 UTC; it is not an exact receipt/publication timestamp.

Important semantic guard: the Form 144 `nothingToReportFlagOnSecuritiesSoldInPast3Months` applies to the prior-three-month-sales section, not to the proposed-sale tranche. It must not be interpreted as a global “no proposed sale” flag. A Form 144 is a notice of a proposed sale, not evidence that the proposed sale was executed.

## 4. Interpretation and research eligibility

This phase validates scheduled delivery, parsing and persistence only.

- Form 144 now has a matching original event-ledger XML hash, but no certified exact public-availability timestamp, no historical F80 membership verification and no completed-execution evidence.
- Form 4 has a structured XML hash, but no comparable original event-ledger hash; security identity, historical F80 membership, owner-to-line attribution and transaction semantics remain unverified.
- Form 4 transaction codes are not a standalone smart-money classification. In particular, P can represent an open-market or private purchase; A, M and F have distinct award/exercise/withholding contexts. Do not classify them as ordinary discretionary buys without transaction-level evidence and footnote review.
- The Form 144 detail ledger's `research_observation_eligible` field is an ingestion/observation gate, not feature admission. It does not override the explicit false public-availability and signal flags.

No returns, event study, backtest, chronological OOS, bootstrap, LOO or holdout test was run. No signal was admitted.

## 5. Operational disposition

Issue #136 (“Recurring SEC scheduled-capture gap”) is resolved as an operational delivery issue: both existing scheduled workflows have now run successfully after Phases 509/510 and persisted non-empty structured ledgers.

The bounded backfill queues remain open work, not a delivery outage:
- Form 4: 1,190 accessions remaining.
- Form 144: 368 accessions remaining.

Continue only through the existing schedules and their bounded limits. Do not manually dispatch or rerun while a scheduled attempt is active or pending.

## 6. Baseline protection

`F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen. No universe, parameters, exposure, costs, holding-period rules, holdout or production settings changed. No incremental alpha is claimed.
