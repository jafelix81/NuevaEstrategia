# Phase 537 — SEC Form 4 owner-enrichment and Form 144/Form 4 crosswalk live validation

**Audit timestamp:** 2026-11-21 01:22 UTC  
**Base:** `main` at `c5a5d0942a4b97e3147d6a377ff437c700dfe645`  
**Disposition:** natural scheduled capture and descriptive crosswalk validated; no alpha test; no strategy change

## Executive finding

The next natural scheduled SEC Form 4 run processed the previously queued Atea reporting-owner records. The existing strict crosswalk then reproduced **two proposed-sale matches** between Form 144 and Form 4, plus one prior-sale-history match. It did so without relaxing issuer, owner, date, quantity or security-class matching rules.

The two proposed Atea sales remain classified as **option-exercise / exercise-cost / tax-planning dispositions**, not clean discretionary bearish insider sales. The result validates the filing-level reconciliation pipeline and supplies a useful negative control against naive use of Form 4 transaction code `S`. It is not evidence of predictive alpha.

Both SEC scheduled workflows produced successful natural runs after the delivery gap recorded in Phase 536:

- Form 4: [run 44846461134](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44846461134), artifact 14683520646.
- Form 144/144-A: [run 44847230610](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44847230610), artifact 14684225291.

## 1. Natural capture results

### Form 4 / 4-A — run 44846461134

Both offline-regression and live-capture jobs succeeded. The feed poll ran from 2026-11-21 00:50:42 UTC to 00:51:03 UTC.

- 474 unique new accessions and 474 canonical event observations.
- 976 bounded metadata candidates across 15 Form 4 feed pages; prior watermark found and no page errors.
- 988 accession-observation rows in the compact poll artifact; five cross-feed duplicate occurrences and 507 same-feed duplicate occurrences were retained/reconciled by the capture logic.
- Structured transaction backfill: 10 accessions parsed, 24 detail rows appended, zero parse errors, 1,758 bounded accessions remaining.
- Reporting-owner enrichment: 10 accessions parsed, 15 owner rows appended; nine single-owner filings and one multi-owner filing. Twenty bounded accessions remain after the batch.
- The Form 4 poll still has `public_availability_certified=false`, `research_observation_eligible_rows=0` and `signal_eligible_rows=0`.

The first-seen timestamps are poll/watermark bounds, not exact first-publication timestamps. The feed capture is useful for prospective metadata accumulation but does not authorize same-day use.

### Form 144 / 144-A — run 44847230610

Both jobs succeeded. The poll ran from 2026-11-21 00:58:15 UTC to 00:58:43 UTC.

- 91 new Form 144 events and 103 feed-observation rows.
- 91/91 filing-acceptance reconciliations added; zero unresolved.
- Cross-feed provenance complete; no possible feed-window gap; zero cross-feed overlap in this poll.
- Twelve candidate issuer matches were identified for the manifest; this is not proof of historical F80 membership.
- Structured-detail backfill parsed 10 accessions and appended 62 rows; zero parser errors; 338 accessions remain.
- Structured ledger now contains 222 accessions and 1,644 rows.
- `public_availability_certified=false`, `same_day_intraday_use_authorized=false` and `signal_eligible_count=0`.

The 91 rows marked research-observation-eligible by the bounded capture are **not signal eligible**. The first-seen clock remains a receipt upper bound.

## 2. Owner-queue completion and crosswalk

The Form 4 run artifact includes the output of the existing `phase525_form144_form4_crosswalk.py` implementation. Its summary reports:

| Crosswalk field | Result |
|---|---:|
| Crosswalk rows | 3 |
| Proposed-sale matches | 2 |
| Prior-sale-history matches | 1 |
| Distinct matched Form 4 accessions | 2 |
| Single-owner accessions with identity in sidecar | 18 |
| Multi-owner accessions quarantined | 2 |
| Form 4 sale-disposition accessions without single-owner identity | 8 |
| Ambiguous Form 144 events / transaction reuse | 0 / 0 |
| Signal-eligible matches | 0 |

The two Atea Form 4 accessions are now present in `reporting_owners.csv` as single-owner filings:

- Bruce Polsky, Form 4 `0001193125-26-469037`, owner CIK `0001508458`.
- Bruno Lucidi, Form 4 `0001193125-26-469038`, owner CIK `0001829622`.

The strict crosswalk artifact contains these three rows:

| Seller / role | Shares | Form 144 reported value | Form 4 calculated gross | Difference |
|---|---:|---:|---:|---:|
| Bruce Polsky — proposed sale | 8,750 | $35,299.25 | $35,298.3750 | +$0.8750 |
| Bruno Lucidi — proposed sale | 22,619 | $89,219.37 | $89,220.6455 | -$1.2755 |
| Bruno Lucidi — prior-sale history | 6,741 | $27,189.82 | $27,189.8235 | -$0.0035 |

The value differences are small relative to the reported amounts (approximately 0.00248%, 0.00143% and 0.000013%, respectively). They are preserved rather than silently rounded away; the crosswalk's matching key is not relaxed to use a value tolerance.

Both proposed-sale Form 144 notices were accepted before the corresponding Form 4 acceptance timestamps on the same transaction date. That does **not** establish that the notice preceded execution: execution intraday time is unknown. Form 144 is a proposed-sale notice, not proof that the sale occurred; the Form 4 reports the transaction.

The Form 4 remarks for both sellers explicitly state that the reported sales were made to pay option exercise costs and for tax-planning purposes. The notices also identify exercised shares / stock-option exercise. The filing-level remarks flags include option exercise, exercise-price payment and tax-planning context; they do not identify open-market intent. Because the owner sidecar is filing-level and transaction-line owner attribution is not independently verified, retain the conservative filing-level classification and keep all rows non-signal.

## 3. Research disposition

**Validated:** the bounded owner-enrichment queue now contains both Atea accessions and the automated strict crosswalk reproduces the two proposed-sale pairs plus one prior-sale-history pair.

**Rejected for this event:** treating a cluster of Form 4 `S` rows as a discretionary bearish insider signal. Transaction code alone is insufficient; remarks, option-exercise context and Form 144 notice semantics materially alter interpretation.

**Not established:** exact first-publication time, trade execution time, transaction-line owner attribution, historical F80 membership, universe-wide historical coverage, or incremental forward-return predictability.

No event study, return test, backtest, OOS, bootstrap, LOO or holdout test was run. No raw filing XML was committed in this phase. No feature is admitted.

## 4. FINRA / Phase 20C status remains gated

- The latest FINRA Reg SHO scheduled live run remains [44669121290](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44669121290). Its 56 offline tests passed, but the live capture returned eight HTTP-200 files that all failed parser validation: 0 valid files, 0 eligible observations.
- That run predates the Phase 515 CNMS parser correction. No post-Phase-515 scheduled live validation appears in the latest 100 Actions runs checked at 2026-11-21 01:22 UTC. The workflow still declares `30 22,23 * * 1-5`. No manual dispatch or rerun was made.
- Phase 20C price-provider fallback remains blocked at 328/329 valid price histories; the documented alternative-provider probe did not recover the missing historical series. Do not drop symbols, impute prices or mix providers.
- FINRA Consolidated Short Interest remains conditional on authorized credentials and a complete asynchronous settlement snapshot.

This is an operational validation gap, not evidence that the Phase 515 parser fix failed. Wait for a natural scheduled run before judging the repair.

## 5. Controls and next gates

- `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen.
- No change to the universe, model, parameters, exposure, costs, capital, holdout or production.
- No signal admitted and no performance claim made.
- Continue bounded SEC capture and owner backfill; preserve multi-owner quarantine.
- Before any insider feature test, require a defensible public-availability clock, historical security/F80 identity, filing/transaction semantic classification and a chronological test against the frozen baseline with identical exposure and costs.
- Keep the FINRA Reg SHO post-Phase-515 live validation pending the next natural scheduled run.

