# Phase 383 — CFTC Russell E-mini post-2017 archive availability panel

**Status:** completed — 480/482 archive pages valid; two documented exclusions.  
**Parent:** Phase 378 contract-era split, Phase 380 full archive census, Phase 382 anomaly repair.

## Why isolate Russell code 239742

Phase 378 established that CFTC code 239742 is reused across two Russell contract eras:
- 119 old Russell Mini observations, 2006-06-13–2008-09-16, multiplier $100.
- 482 E-mini observations, 2017-08-15–2026-11-03, multiplier $50.
The 3,255-day gap and multiplier change prohibit splicing. Official 2017 CFTC report identifies the later contract as E-mini Russell 2000 x $50. ICE code 23977A and old code 239741 remain separate.

Phase 380 found historical archive problems, but only two known exceptions intersect the post-2017 239742 series:
- 2018-09-25: archive filename page says positions as of 2018-09-18.
- 2019-12-24: expected archive page returns 404.
Phase 382 confirms the CFTC API contains one Russell 239742 row for each of those two report dates, but no exact archive page was found in adjacent filenames.

## Method

Query all CFTC TFF rows for code 239742 from 2017-08-15 onward. Reconcile counts and metadata before/after, check natural-key uniqueness, then retrieve the matching static archive page for each report date. Admit a date only if the archive heading exactly matches the report date and Updated is not earlier than the report date. Keep missing or mismatched weeks excluded; never forward-fill.

Cross-check all 23 recent official publication-date samples against the archive Updated date. Retain only date metadata and page status, not positions or HTML.

## Candidate availability rule

Use the first regular market session after the archive Updated date; never same-day close. This is a conservative archive-derived proxy, not a formally certified first-publication timestamp. The two known missing/misaligned weeks remain excluded.

## Research interpretation

If the panel passes, CFTC Russell E-mini TFF can be considered for a broad small-cap positioning/crowding regime hypothesis (Dealer, Asset Manager, Leveraged Money), not a stock-specific informed-trader signal. It must be tested against prior Russell returns, volatility, broad market regime and frozen LTM/F80. TFF categories are functional classifications, not beneficial-owner identities.

## Controls

No position data retained, no forward returns, feature construction, alpha, OOS, bootstrap, LOO or holdout use. No changes to F80, production, universe, capital, parameters or exposure. Strict historical PIT is not formally certified in this phase.

## Hosted result — completed 2026-11-13

Run [43500752903](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43500752903) passed; date-only artifact [14074056247](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43500752903/artifacts/14074056247).

- CFTC API count reconciled: 482 rows before, retrieved and after; zero duplicate report-date/code keys; metadata snapshot stable.
- Series: 2017-08-15 through 2026-11-03, contract code 239742, CME E-mini Russell 2000.
- 480/482 archive pages valid (99.5851%).
- Excluded exactly two weeks: 2018-09-25 (archive heading is 2018-09-18) and 2019-12-24 (404). Phase 382 confirmed one 239742 row exists in the CFTC API on each date; do not forward-fill.
- Valid-page archive lag: median 3 days, p90 6 days, maximum 50 days.
- All 23 official schedule crosschecks within the series were on or after official publication.
- Contract name metadata has two text variants, but the same CFTC code and CME exchange; the official 2017 CFTC report identifies the contract as E-mini Russell 2000 x $50.

**Disposition:** admit the post-2017 Russell E-mini series as a candidate for exploratory macro positioning/crowding feature research, using the first regular market session after archive Updated and excluding the two exceptions. This remains a conservative archive-derived PIT proxy, not a formally certified first-publication timestamp. No alpha or return test was run.
