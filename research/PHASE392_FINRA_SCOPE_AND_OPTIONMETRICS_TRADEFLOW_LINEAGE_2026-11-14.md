# Phase 392 — FINRA ATS scope reconciliation and OptionMetrics TradeFlow lineage

**Audit date:** 2026-11-14 UTC  
**Disposition:** FINRA T1 publication-date clock is complete; FINRA concentration is an ATS/firm venue measure, not investor flow. OptionMetrics TradeFlow is confirmed as the evolution of Signed Volume, but historical PIT/version and universe gates remain open. No alpha admission.

## 1. Repository and Actions state

The default branch was `main` at `43fa932f269bde48427de59dc1dfcbaeacce8397` (Phase 391 documentation merge). The latest relevant workflow runs were inspected before any new work:

- Phase 385 run [43536490386](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43536490386) completed successfully; job [132311996238](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43536490386/job/132311996238) passed all steps.
- Earlier Phase 385 run [43536354917](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43536354917) also completed successfully.
- Phase 388 raw-only CFTC regression [43539923574](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43539923574) passed.
- At 2026-11-14 06:08 UTC, the repository had zero queued and zero in-progress Actions runs. No duplicate workflow was launched.

### Phase 385 final run

Run 43536490386 confirms:

| Check | Result |
|---|---:|
| T1 weekly partitions | 209/209 |
| Full T1 rows retrieved | 10,917,933 |
| Pages | 2,292 |
| Raw `ATS_W_SMBL` aggregate rows | 438,822 |
| Partitions with one valid initial publication date | 209/209 |
| Publication dates matching 21/22-day NYSE calendar | 209/209 |
| 21-calendar-day lags | 186 |
| Holiday-adjusted 22-calendar-day lags | 23 |
| Aggregate rows with `lastUpdateDate == initialPublishedDate` | 432,828 |
| Aggregate rows updated after initial publication | 5,994 |

Every actual publication date maps to the first NYSE regular session strictly after publication. The artifact is [14100393795](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43536490386/artifacts/14100393795), SHA-256 `3630ce815040a2487ebfc86369552f21da3ee1b58e235f169cd0f604cffc3a46`.

The run explicitly leaves:
- `intraday_first_receipt_certified=false`
- `effective_dated_security_master_gate_passed=false`
- `historical_return_test_authorized=false`

This is a date-level conservative availability bound only.

### Reconciliation with Phase 375

Phase 375 reports 438,798 unioned symbol-week groups, 432,804 revision-stable groups and 5,994 revised groups. Phase 385 counts raw `ATS_W_SMBL` product-grain rows, producing 438,822 total, 432,828 unchanged rows and 5,994 later-updated rows.

These are different grains. Phase 374's logic combines distinct CTS/UTP aggregate product rows at symbol-week grain after exact reconciliation to firm rows. The 24-row difference is consistent with multiple product-grain rows collapsing into one symbol-week group. The anonymized artifacts do not retain a row-level crosswalk, so the denominators must remain separate rather than being forced into a false one-to-one reconciliation.

## 2. FINRA ATS is venue concentration, not investor concentration

FINRA's OTC Transparency User Guide explains that Rule 4552 requires each ATS to report weekly equity volume and transaction counts within the ATS, and to use a single unique MPID for ATS reporting. FINRA publishes reported information in each equity security for each ATS for each week. The Weekly Summary API describes the data as weekly aggregate trade data for each ATS/firm.

Consequently:
- `ATS_W_SMBL` is the aggregate symbol grain.
- `ATS_W_SMBL_FIRM` is the reporting ATS/firm grain used for the venue bridge.
- The 38 unique MPID/CRD-derived keys in Phase 375 represent ATS/firm reporting entities.
- They do not identify customer accounts, beneficial owners, traders, funds, or verified institutions.

The Phase 375 HHI, top-one and top-three shares measure concentration of reported ATS venue activity for a symbol-week. They are not evidence of informed institutional positioning. FINRA should be reclassified within this project as an **off-exchange venue-concentration / market-structure source**, potentially relevant to venue fragmentation, liquidity and concentration hypotheses. No “smart money” label should be attached.

The date-level PIT and revision-stability work remains useful. However, no return test is authorized until an effective-dated security master, historical active-universe membership, inactive/delisted prices and terminal-return treatment are established.

Official sources:
- [FINRA OTC Transparency User Guide](https://www.finra.org/sites/default/files/OTC-transparency-website-user-guide.pdf)
- [FINRA Weekly Summary API](https://developer.finra.org/docs/api-explorer/query_api-equity-weekly_summary)

## 3. OptionMetrics TradeFlow: lineage confirmed, PIT still unresolved

The current official [IvyDB TradeFlow page](https://optionmetrics.com/ivydb-tradeflow/) explicitly says TradeFlow is an evolution of IvyDB Signed Volume. It advertises all U.S. options since January 2016 and 5-minute, 30-minute and EOD snapshots.

The September 28, 2026 [methodology paper](https://optionmetrics.com/research/g-desimone-a-gupta-ivydb-tradeflow-a-framework-for-options-volume-classification-and-microstructure-analytics/) documents:
- Four relational tables: `Signed_Volume`, `Trade_Conditions`, `Market_Structure`, and `Signed_Exchange`.
- Keys based on option symbol, security identifier and date, cross-referenced to IvyDB US.
- A sequential classifier using trade conditions, exchange venue, quote location and VWAP, not just a naive bid/ask test.
- Five proprietary participant buckets: Retail 1–3 and Institutional 1–2.
- Institutional 1 is contained within Institutional 2 and must not be added to it.
- Institutional 2 specifically measures aggressive executions at or through the quote. It excludes passive executions, midpoint trades, patient position-building and market-making activity.

The bucket labels are therefore execution-style proxies. They do not identify beneficial owners and do not measure all institutional participation. In particular, Institutional 2 is aggressive liquidity demand, not a census of institutional buying or selling.

The paper's public worked example is one SPY/FOMC session on 2026-06-17. Its reported directional-classification coverage is vendor evidence on that session, not independent accuracy validation or proof of predictive power.

### Remaining data gates

1. Obtain the current data dictionary and a field-level mapping to the repository's prior four-table TradeFlow/Signed Volume schema.
2. Establish methodology/version history and whether the 2016 archive has been recomputed under the 2026 TradeFlow algorithm.
3. Obtain historical first-delivery, correction, cancellation and replacement-vintage policies.
4. Establish explicit business-use rights and price; retail personal-use terms are not sufficient for firm research.
5. Audit coverage against the frozen 335 diagnostic names and inactive/delisted underlyings, with contract adjustments and security identity.
6. Only after a lawful sample is available, reconcile exact same-day/same-series aggregates against independent raw OPRA trades/NBBO (Cboe Option Trades or ThetaData) and Cboe Open-Close where venue scope overlaps.

The advertised 2016 history is historical coverage, not proof that the current classifier was available in 2016. The repository records a 2026-09-30 TradeFlow launch; absent historical delivery/vintage evidence, pre-prospective TradeFlow features remain retrospective and cannot be treated as strict point-in-time signals. No vendor contact, account, trial, sample acquisition or purchase occurred.

Official sources:
- [IvyDB TradeFlow product page](https://optionmetrics.com/ivydb-tradeflow/)
- [TradeFlow methodology paper](https://optionmetrics.com/research/g-desimone-a-gupta-ivydb-tradeflow-a-framework-for-options-volume-classification-and-microstructure-analytics/)
- [TradeFlow brochure](https://optionmetrics.com/wp-content/uploads/2026/08/TradeFlow-Brochure-1-1.pdf)
- [IvyDB Signed Volume page](https://optionmetrics.com/signed-volume/)

## 4. Research disposition

- FINRA T1 ATS: source and date-level publication feasibility passed; security identity and universe gates remain open. Interpret concentration as venue structure only.
- OptionMetrics TradeFlow: best conditional signed-flow candidate; product lineage clarified, but historical PIT, version, license and sample gates remain open.
- ThetaData / Cboe Option Trades: independent raw OPRA reconstruction/validation candidates; no sample or license admission.
- CFTC TFF: prospective capture remains active; the first new release capture is still pending.
- No signal admitted. No forward returns, alpha, OOS, bootstrap, LOO or holdout test run.
- `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen. No production, universe, capital, exposure or parameter changes.
