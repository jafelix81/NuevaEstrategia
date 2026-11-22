# Phase 560 — current Form 144 Rule 10b5-1 polarity refresh

**Audit cutoff:** 2026-11-22 18:38:06 UTC  
**Data head:** 7680c3d66f974622b4aef4764abe885a703742d2  
**Classifier:** existing accession-grain Phase 549 rules; no thresholds or patterns changed  
**Disposition:** descriptive ledger refresh only; no signal, return test or OOS result.

## 1. Natural capture and ledger reconciliation

Natural scheduled run [45052961790](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45052961790) completed on main at 18:04 UTC. Both offline-regression and live-capture succeeded. Artifact [14765739720](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45052961790/artifacts/14765739720) was downloaded and inspected.

- Both SEC feeds succeeded: 51 Form 144 entries and 2 Form 144/A entries (53 feed observations).
- Pagination completed; previous watermarks were present; no feed errors or possible feed-window gap.
- No new accession or event was found.
- Bounded backfill parsed 10 already-known accessions and appended 42 detail rows.
- Current structured ledger: **285 accessions / 2,114 detail rows**; **278 accessions** remain in the backfill queue.
- Parsing errors: 0. Source-hash mismatches: 0. Public-availability-certified filings: 0. Signal-eligible filings: 0.
- The persistent main commit [7680c3d](https://github.com/jafelix81/NuevaEstrategia/commit/7680c3d66f974622b4aef4764abe885a703742d2) changed only feed_observations.csv, sale_details.csv and state.json; it added 53 feed-observation rows and 42 detail rows. It did not add event rows.

## 2. Recomputed accession-grain 10b5-1 classification

The existing Phase 549 classifier was run against the current 285-accession / 2,114-row ledger. The classifier and tests were copied unchanged; the CI run generated aggregate artifact [14767855406](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45056179069/artifacts/14767855406).

| Measure | Current result |
|---|---:|
| Form 144 accessions | 283 |
| Form 144/A accessions | 2 |
| Explicit positive Remarks polarity | 9 |
| Explicit negative Remarks polarity | 4 |
| Ambiguous Remarks polarity | 1 |
| No 10b5-1 mention | 271 |
| Formal plan-adoption date present | 103 (36.14%) |
| Distinct formal plan dates | 64 |
| Plan-date-to-notice lag | 72–546 days; median 185 |
| Plan dates after notice | 0 |
| Plan-termination accessions | 1 |

The formal-plan-date cross-tab is 9 positive, 1 ambiguous and 93 no-mention accessions; the four negative explicit cases have no formal plan date. The polarity counts are accession-level, not detail-row counts.

All four negative explicit cases are Fermi sell-to-cover/tax-withholding notices on 2026-11-19. Their 2,253,270 proposed units are notice quantities, **not verified executed volume**. One plan termination remains separately flagged; it must not be interpreted as new forward supply or a fresh discretionary sale.

The updated classification adds one positive explicit mention and two formal-date accessions relative to the prior 275-accession refresh; the nine additional no-mention accessions account for the remainder of the ledger growth. The unchanged negative and ambiguous counts are not evidence of predictive stability; this is a descriptive sample update only.

Form 4 sidecar at the current bounded snapshot: 40 accessions / 110 detail rows; filing-level AFF10B5ONE flags are 3 checked, 37 unchecked, 0 unknown and 0 conflicts. An unchecked flag is not proof of discretionary trading.

## 3. PIT and interpretation controls

- A Form 144 is a proposed-sale notice, not execution confirmation.
- The structured plan-adoption date is not the market-knowledge timestamp.
- First-seen poll receipt is an upper bound, not exact first public availability.
- The SEC public-availability-certified count remains zero; same-day use is not authorized.
- Positive/negative Remarks polarity is not evidence that the seller is an informed trader, and it is not evidence that the proposed sale occurred.
- The four negative Fermi cases are a mechanical sell-to-cover/tax-withholding negative control, not discretionary bearish supply.

## 4. Validation and strategy protection

PR [#205](https://github.com/jafelix81/NuevaEstrategia/pull/205) adds the existing classifier and its 10 regression tests to the existing Phase 403 offline-regression job; it creates no second scheduled collector and does not change the live-capture job. PR CI [45056179069](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45056179069) passed **74/74 tests** and uploaded the aggregate summary artifact. The live-capture job was skipped for the PR event as designed.

- New signals admitted: **0**.
- Event/return/alpha/OOS/bootstrap/LOO tests: **0**.
- No change to universe, parameters, exposure, costs, holding-period policy, holdout or production.
- F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen.

The next valid step is to preserve the classifier as a descriptive ledger-quality diagnostic and continue the independent PIT/identity work. Do not use the current counts as a backtest label.
