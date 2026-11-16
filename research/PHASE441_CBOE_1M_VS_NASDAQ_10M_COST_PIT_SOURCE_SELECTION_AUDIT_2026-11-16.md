# Phase 441 — Cboe one-minute versus Nasdaq ten-minute Open-Close cost/PIT selection audit

**Audit time:** 2026-11-16 18:39 UTC  
**Status:** COMPLETED_SOURCE_SELECTION_UPDATE — Cboe 1-minute remains conditional, but is not the next acquisition priority. Prefer EOD first and a Nasdaq 10-minute sample before any expensive Cboe 1-minute trial or purchase. No source is admitted to PIT research or alpha.

## 1. Repository and Actions preflight

- Main HEAD at start: `aee7f4aa0ae1f95563a1f71329936efaa30c783b` (Phase 440).
- Latest observed Actions run: [43918910577](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43918910577), Phase 350 SEC 13D/G parent retrieval, created 2026-11-16 17:29:27 UTC. It completed with failure in job `133480557295`.
- The offline parser/validation tests passed. The job failed at **Validate SEC contact configuration** because `SEC_USER_AGENT` was empty; the exact SEC archive retrieval step was skipped. No artifact was produced.
- The preflight status queries returned zero in-progress and zero queued runs. No workflow was dispatched, rerun or duplicated.
- Repository audit: 275 branches across three pages (100/100/75), 56 open PRs and 67 workflow files.
- Prior research was inspected before this phase: Phase 286/287 Nasdaq Trade Outline branches and Phase 352–357 Cboe 1-minute/EOD branches. This report does not repeat their schema or historical-convention audits; it adds the 2026 one-minute fee/latency comparison and a source-priority decision.
- Phase 440 remains merged at main. The Phase 439/440 state entries are already present in `SMART_MONEY_RESEARCH_STATE.md`.

## 2. New official evidence: Cboe one-minute economics and delivery

The SEC's February 10, 2026 filing, Release 34-104796, describes Cboe Exchange's One-Minute Interval Intraday Open-Close Report:

- One-minute snapshots are expected **2–5 minutes after the interval**.
- The first example update arrives around 09:34 ET for 09:30–09:31; the next around 09:35 ET for 09:31–09:32.
- Every update is **cumulative**: it contains the current snapshot plus all prior snapshots for that trading session.
- Later snapshots can incorporate late-processed trades and remove trades subsequently broken or cancelled. A later corrected snapshot must never overwrite the earlier version used by a historical signal.
- The product is proprietary exchange data and excludes trades from other exchanges.
- The filing lists a $12,000 monthly subscription ($144,000/year), $4,000 per requested historical month for data less than four years old, and $2,500 per requested historical month for data five or more years old. The ad-hoc history is stated to begin 2019-10-07.
- The filing extends the existing up-to-six-month historical trial to the one-minute product for eligible TPH/non-TPH recipients who have not previously subscribed to that dataset or received a free trial. Eligibility is unverified. This is a historical-data trial, not proof of a prospective live-capture entitlement.
- External distribution of derived one-minute data is separately priced at $7,500/month. No external distribution is contemplated in this research.

The $12,000/month tariff is from the Cboe Exchange filing. Do **not** extrapolate it to BZX, C2 or EDGX without their own current fee schedules. Phase 352 documents separate venue files and distinct historical starts; the four-venue suite is not consolidated OPRA.

Official filing: https://www.sec.gov/files/rules/sro/cboe/2026/34-104796.pdf

## 3. Nasdaq 10-minute alternatives already identified in Phases 286/287

The SEC filing itself identifies comparable Nasdaq products. The 2026 Nasdaq US Options price-list PDF confirms the 2026 intraday distributor fees and historical per-request-month rates:

| Venue/product | Intraday subscription | Historical intraday per requested month | Documented history context |
|---|---:|---:|---|
| NOM / NOTO | $2,000/month | $500 | November 2011 |
| PHLX / PHOTO | $3,000/month | $1,000 | January 2009 product history; confirm field-by-field availability |
| ISE Open/Close | $2,500/month | $1,000 | Intraday history from October 2009 |
| GEMX Open/Close | $1,500/month | $750 | August 2013 start, with a documented March 2017–December 2017 gap |

Nasdaq's products report venue-specific series-level volume by origin category and opening/closing trade type. Intraday snapshots are cumulative and are not full-OPRA data. They must be differenced carefully and captured with actual first-receipt timestamps. The products are not independent of one another if the same underlying market activity is represented across venues.

The SEC filing's competitor-price comparison is for the intraday products; it must not be confused with EOD historical pricing. The 2026 Nasdaq price list is the source for the listed 2026 fees.

Official sources:
- Nasdaq Options Trade Outline suite: https://www.nasdaq.com/products/data/options/trade-outline
- Nasdaq Data Link NOTO: https://data.nasdaq.com/databases/NOTOI
- Nasdaq US Options Price List 2025–2027: https://www.nasdaqtrader.com/content/ProductsServices/PriceList/Nasdaq_US_Options_Price_List_2025_2026_2027.pdf
- SEC Release 34-104796, competitor comparison: https://www.sec.gov/files/rules/sro/cboe/2026/34-104796.pdf

## 4. Fee ratios — single-venue comparison only

Using the filed Cboe one-minute fees and Nasdaq 2026 intraday fees:

| Nasdaq 10-minute product | Cboe 1m / Nasdaq subscription | Cboe 1m / Nasdaq historical month (<4y) | Cboe 1m / Nasdaq historical month (5+y) |
|---|---:|---:|---:|
| NOTO | 6.00x | 8.00x | 5.00x |
| PHOTO | 4.00x | 4.00x | 2.50x |
| ISE | 4.80x | 4.00x | 2.50x |
| GEMX | 8.00x | 5.33x | 3.33x |

These are **price ratios per single exchange product**, not coverage-adjusted comparisons. Venue market share, universe coverage, field history, delivery vintages, license rights and actual data quality differ. Cboe's filing says the one-minute product supplies ten times as many data points as its ten-minute product for four times the price; this is a data-frequency comparison, not evidence of ten times the predictive information.

## 5. PIT and feature limitations that remain decisive

- A cumulative snapshot is not an interval bar. Any incremental feature must compare consecutive snapshots for the same venue, trade date and option-series key.
- Preserve negative changes and revisions; never clip them to zero or reinterpret them as sell flow.
- Store every original snapshot append-only with actual first-receipt UTC, interval key, venue, filename, schema/version and SHA-256. A final corrected historical file cannot be backdated as the snapshot originally available to the strategy.
- Phase 352's v1.8 schema audit notes that the one-minute file omits open interest, total exchange volume, total industry volume and EOD price fields. IV/Greeks and market-share denominators require separately timestamped companion data.
- Neither the Cboe nor Nasdaq origin categories identify a named beneficial owner or prove informed trading.
- Historical product start dates and nominal delivery schedules do not establish complete historical coverage or original first-receipt vintages.

## 6. Strategy-level source priority

This comparison does **not** impose a minimum or maximum holding period. It only ranks the data granularity needed for the currently defined research/execution process.

1. **EOD first:** lowest operational complexity for the first daily/swing hypothesis; preserve next-session availability and preliminary/final vintages.
2. **Nasdaq 10-minute sample next:** if intraday timing appears useful, test a lower-cost 10-minute venue product before considering Cboe 1-minute. Start with one venue and a stratified sample; do not assume six venue feeds form a complete or gap-free panel.
3. **Cboe 1-minute later, conditional:** consider only if the 10-minute/EOD evidence shows that finer timing could materially change an executable signal and the data rights, first-receipt capture and companion-data gates are solved.

Given the current end-of-day execution design, the extra one-minute granularity has not yet demonstrated economic value. No purchase, trial request, vendor contact, API call or license acceptance was made or authorized. A six-month historical trial may be worth considering only after explicit authorization and written confirmation of eligibility, permitted private storage and derivative-feature rights.

## 7. Legacy public Actions artifact — rights review required

A separate audit of the existing public repository artifact from the earlier Phase 54 sample run found that run [41762583602](https://github.com/jafelix81/NuevaEstrategia/actions/runs/41762583602), artifact **13291147097**, contains:
- `cboe_open_close_sample.zip`;
- `sample_rows.json`; and
- `summary.json`.

The downloaded artifact ZIP SHA-256 is `0213a5923d7a8973bb51e834551477a68c0b628b8cf112fd1bbc642f62d673ed`; the nested sample ZIP SHA-256 is `445cd9d658dc06028c286e09d4ac4818bd5884d7da8addd7509f3a0fa4840552`.

The repository is public. The source was a Cboe public sample, but the product terms also describe raw product data as proprietary/internal-use and restrict external distribution of derived data. I cannot conclude from the available documents whether this particular sample bundle is exempt from redistribution restrictions. **Do not upload additional raw or derived Cboe files to this public repository.** A repository administrator should confirm the sample-specific terms and remove the legacy artifact if public redistribution is not permitted. The available GitHub connector has no artifact-delete action; no deletion was attempted.

## 8. Human action and final disposition

- **SEC contact configuration:** latest Phase 350 run failed because repository secret `SEC_USER_AGENT` is empty. Configure it with a project identifier and a monitored contact email before the exact SEC parent-retrieval job can run. The offline tests passed; archive retrieval was skipped.
- **Legacy Cboe artifact:** confirm sample redistribution rights and remove the public Actions artifact if the terms do not permit it.
- Cboe 1-minute: retain as conditional, not priority.
- Nasdaq 10-minute: retain as a lower-cost conditional comparator, not admitted.
- Cboe/Nasdaq EOD: preferred first feasibility route for daily research, still subject to licensing, historical coverage and first-receipt gates.
- No raw vendor data was added to this PR. No return/alpha/OOS/bootstrap/LOO test was run. No source or signal was admitted.
- `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen. No universe, parameters, holdout, capital, exposure, trading code or production settings changed.

## 9. Prior research reviewed

- [Phase 286 — Nasdaq Trade Outline feasibility](https://github.com/jafelix81/NuevaEstrategia/tree/phase286-nasdaq-options-trade-outline-feasibility)
- [Phase 287 — Nasdaq Trade Outline and ITCH/NOII feasibility](https://github.com/jafelix81/NuevaEstrategia/tree/phase287-nasdaq-options-and-itch-source-feasibility)
- [Phase 352 — Cboe 1-minute v1.8 PIT audit](https://github.com/jafelix81/NuevaEstrategia/tree/phase352-cboe-open-close-1m-v18-pit-audit)
- [Phase 353 — Cboe EOD/OPRA companion audit](https://github.com/jafelix81/NuevaEstrategia/tree/phase353-cboe-eod-flow-companion-audit)
- [Phase 354 — OCC OI cross-check](https://github.com/jafelix81/NuevaEstrategia/tree/phase354-occ-cboe-eod-oi-crosscheck)
- [Phase 355 — participant accounting audit](https://github.com/jafelix81/NuevaEstrategia/tree/phase355-cboe-eod-participant-accounting-audit)
- [Phase 356 — historical convention regimes](https://github.com/jafelix81/NuevaEstrategia/tree/phase356-cboe-historical-convention-regimes)
- [Phase 357 — product metadata/PIT reconciliation](https://github.com/jafelix81/NuevaEstrategia/tree/phase357-cboe-product-metadata-pit-reconciliation)
