# Phase 536 — Atea Form 4 / Form 144 mechanical-sale reconciliation and Actions delivery audit

**Audit timestamp:** 2026-11-21 00:11 UTC  
**Base:** `main` at `768148566993e620664610f93b2ba0f624a1d48d`  
**Disposition:** completed data-integrity audit; no alpha test; no strategy change

## Executive finding

Two Atea Pharmaceuticals (AVIR) Form 144 notices can be paired with Form 4 sale rows by issuer, named seller/reporting owner, common-stock class, filing/transaction date and exact share quantity:

| Seller | Form 144 | Form 4 | Form 4 sale | Form 144 amount |
|---|---|---|---:|---:|
| Bruce Polsky | `0001950047-26-011348` | `0001193125-26-469037` | 8,750 shares on 2026-11-19 at $4.0341 | 8,750 |
| Bruno Lucidi | `0001950047-26-011363` | `0001193125-26-469038` | 22,619 shares on 2026-11-19 at $3.9445 | 22,619 |

The two Form 4 filings state that **all reported sales were executed to pay option exercise costs and for tax-planning purposes**. The corresponding notices identify the shares as exercised shares / stock-option exercise. These are therefore not clean examples of discretionary bearish insider selling. Treat them as mechanical/administrative exercise-related dispositions, not as a negative directional signal.

This is a useful negative control for any naive “insider sale count” feature: transaction code `S` alone is insufficient. Form 4 remarks, footnotes, same-filing option exercises and Form 144 context materially change the economic interpretation.

## 1. Filing-level reconciliation

### Bruce Polsky

- Form 4 accession: [0001193125-26-469037](https://ir.ateapharma.com/sec-filings/sec-filing/4/0001193125-26-469037)
- Form 144 accession: [0001950047-26-011348](https://ir.ateapharma.com/sec-filings/sec-filing/144/0001950047-26-011348)
- Issuer CIK: `0001593899`; owner CIK: `0001508458`.
- Form 4: one common-stock `S` disposition, 8,750 shares, 2026-11-19, weighted-average price $4.0341.
- Form 144: seller BRUCE POLSKY; common-stock amount 8,750; notice date 2026-11-19; the acquisition section describes 8,750 exercised shares.
- SEC ownership XML contains the remarks that the sales paid option exercise costs and tax planning: [ownership.xml](https://www.sec.gov/Archives/edgar/data/1508458/000119312526469037/ownership.xml).

### Bruno Lucidi

- Form 4 accession: [0001193125-26-469038](https://ir.ateapharma.com/sec-filings/sec-filing/4/0001193125-26-469038)
- Form 144 accession: [0001950047-26-011363](https://ir.ateapharma.com/sec-filings/sec-filing/144/0001950047-26-011363)
- Issuer CIK: `0001593899`; owner CIK: `0001829622`.
- Form 4: common-stock `S` disposition of 22,619 shares on 2026-11-19 at $3.9445. The same filing reports 53,372 shares acquired through option exercise at $1.24 on that date; it also reports an earlier 6,741-share sale on 2026-11-17.
- Form 144: seller BRUNO LUCIDI; common-stock amount 22,619; notice date 2026-11-19; acquisition nature is stock-option exercise.
- SEC ownership XML contains the same option-cost/tax-planning remarks: [ownership.xml](https://www.sec.gov/Archives/edgar/data/1593899/000119312526469038/ownership.xml).

The share/date/owner reconciliation is corroborated by the official issuer filing index and the SEC ownership XML. The Form 144 amount is a notice/proposed-sale field, not independent proof of execution; the Form 4 supplies the reported transaction. Do not treat Form 144 alone as an executed trade.

## 2. Why the automated crosswalk still returned zero

Latest scheduled Form 4 run [44794670480](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44794670480) completed successfully:

- Offline regression and live-capture jobs both succeeded.
- Owner enrichment processed 10 accessions and appended 14 owner rows.
- 20 bounded owner accessions remained after that batch.
- The strict crosswalk returned 0 matches and 0 signal-eligible matches.
- `reporting_owners.csv` contains 14 data rows from 10 accessions; neither Atea Form 4 accession is present yet.
- Both Atea accessions remain in the next bounded owner-enrichment batch at positions 2 and 3, per the Phase 533 queue diagnostic.

The zero-row result is therefore a queue-coverage limitation, not evidence that the two filings fail to match. Manual review does not authorize a production match or signal. Keep the strict owner/issuer/date/class/quantity rules unchanged and let the next natural scheduled Form 4 run process the queue; do not dispatch manually.

Latest Form 144 run [44796839433](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44796839433) also succeeded. Its structured ledger contains both notices. For both feeds, `public_availability_certified=false`, `same_day_intraday_use_authorized=false` and `signal_eligible_count=0`.

## 3. Feature-design consequence

For insider research, do not use raw `transaction_code=S`, gross sale value, or “two insiders sold” as a standalone bearish feature.

Before any forward-return test, classify or quarantine at least:

1. Sales explicitly linked in Form 4 remarks to option exercise costs or tax planning.
2. Same-filing option exercises / cashless exercise / sell-to-cover patterns.
3. 10b5-1 plan activity, gifts, tax withholding, vesting and compensation-related events.
4. Form 144 proposed sales that have not yet been corroborated by Form 4.
5. Multi-owner filings where line-to-owner attribution is not verified.

Preserve separate features for discretionary open-market dispositions, exercise-related sales, and unresolved/ambiguous events. If the remarks/footnote classifier cannot establish the event type, keep the observation in quarantine rather than infer intent.

**Hypothesis disposition:** the naive “cluster of Form 4 sales is bearish” interpretation is rejected for this Atea event. The broader insider hypothesis is not killed; it remains conditional on owner identity, event semantics, first-seen availability, historical universe identity and strict chronological/OOS testing.

## 4. Scheduled Actions delivery audit

The repository-wide Actions run-list snapshot returned 7,998 total runs and the latest 100 run records. At 2026-11-21 00:11 UTC:

- Latest scheduled Form 4 run: [44794670480](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44794670480), 2026-11-20 18:38:24 UTC.
- Latest scheduled Form 144 run: [44796839433](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44796839433), 2026-11-20 18:52:22 UTC.
- No later scheduled run for either workflow appeared in the latest 100 records; no queued or in-progress run appeared there.
- Form 4 YAML still declares `17 * * * 1-5`; Form 144 YAML still declares `47 * * * *`.
- Later expected slots on 2026-11-20 were not present: Form 4 19:17–23:17 UTC and Form 144 19:47–23:47 UTC.

This confirms a continued observed schedule-delivery gap; it does **not** prove the workflows are administratively disabled. The connected read path cannot expose the workflow enabled/disabled state. Issue [#194](https://github.com/jafelix81/NuevaEstrategia/issues/194) remains open for the repository owner to verify both workflows are enabled and scheduled Actions are permitted. No cron, workflow state, manual dispatch or rerun was changed.

### FINRA Reg SHO

The latest live run remains [44669121290](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44669121290): 8 HTTP-200 files, 8 invalid, 0 valid, 0 eligible observations. It predates the Phase 515 parser correction; no post-fix live validation appears in the latest Actions records. Do not count HTTP 200 as parser success.

## 5. Research controls and final disposition

- No raw or licensed vendor data were acquired.
- No manual SEC/FINRA dispatch, rerun or duplicate poll was performed.
- No forward returns, alpha test, backtest, bootstrap or LOO were run.
- No raw Form 4/144 observations were made signal-eligible.
- `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen.
- No changes to universe, model parameters, exposure, costs, capital, holdout or production.

The next useful operational evidence is the next natural Form 4 run: verify that the two Atea owner rows enter `reporting_owners.csv` and that the strict automated crosswalk reproduces these two manually corroborated pairs without relaxing its matching rules.
