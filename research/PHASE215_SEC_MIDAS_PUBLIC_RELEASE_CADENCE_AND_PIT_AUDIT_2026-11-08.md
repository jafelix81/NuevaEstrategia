# Phase 215 — SEC MIDAS public-release cadence and point-in-time admission audit

**Date:** 8 November 2026  
**Status:** Quarterly batch-release cadence confirmed; exact per-quarter first-publication vintages unresolved. No PIT or alpha admission.  
**Research role:** On-exchange market-structure context only; not off-exchange flow, participant identity or a directional Smart Money signal.

## Executive finding

The SEC's own dated documentation confirms that daily stock-by-stock market-activity downloads were released in **quarterly batches**, not as a contemporaneous daily feed. The SEC's Data Highlight 2013-03 states that users could download daily stock-by-stock data from the Data Download page and that the series was "currently released on a quarterly basis." The public market-structure website launch and the first three Data Highlights are dated 9 October 2013.

On 9 January 2014, the SEC stated that 15 months of stock-by-stock odd-lot history had already been published and that Q4 2013 stock-by-stock data would be added in the next scheduled quarterly update, expected in mid-February. That is an expected date, not proof of the actual release date.

The current SEC download pages list 58 quarterly archives from 2012 Q1 through 2026 Q2. Their page-level update date is 30 June 2026. None of this establishes the exact first-publication timestamp for each quarterly archive.

**Consequent PIT rule:** the row's market date is not its knowledge date. A historical daily feature cannot be made available on the row date merely because the current archive contains that row. Each feature vintage must be gated by the actual public release time of its quarterly archive. Those per-quarter first-publication timestamps are not currently available in the research record.

## Dated public-dissemination evidence

| Evidence | What it establishes | What it does not establish |
|---|---|---|
| SEC public market-structure website launch, 9 Oct 2013 | Public dissemination initiative and launch date | First-publication time for each later ZIP |
| Data Highlight 2013-03, 9 Oct 2013 | Daily stock-by-stock data downloads were released quarterly; launch-era material covered quarters ending 30 Jun 2013 | Exact release time for every security-level archive |
| Data Highlight 2014-01, 9 Jan 2014 | 15 months of stock-by-stock odd-lot history were already published; Q4 2013 addition was expected mid-February | Actual Q4 2013 upload date |
| Current SEC download pages, updated 30 Jun 2026 | 58 quarterly archives, 2012 Q1–2026 Q2 | Historical release-vintage ledger |

The older archive HTTP Last-Modified values observed in Phase 203/204 (typically 19 December 2020, with one sampled response returning the Unix epoch) are migration/server metadata, not original quarterly first-publication timestamps. The current page's "Last Updated" date is also not a per-file release ledger.

## Measurement semantics

The public per-security files are market-activity metrics constructed from exchange data. They do not identify beneficial owners or institutional participants. The SEC's own odd-lot discussion explicitly distinguishes hidden orders on exchanges from off-exchange dark venues. Therefore:

- Hidden / HiddenVol must not be labeled dark-pool or off-exchange flow.
- Odd-lot activity is not a retail identifier; order fragmentation and resting-order interactions can generate odd-lot executions.
- Public MIDAS per-security metrics are not an institutional-flow tape.
- The data can be studied as slow market-structure context only after a valid archive-release timestamp is established.

## Phase 203/204 reconciliation cross-check

The latest hosted Phase 204 revalidation (run 42491346529, artifact 13622036454) CRC-validated all six aggregate/per-exchange ZIP archives and hashed the embedded README rules. In the deterministic ticker/control sample, all 12 shared fields reconciled with zero mismatches when the README's field-specific exchange rules were applied:

| Quarter | Sampled security-day keys | README-rule mismatches |
|---|---:|---:|
| 2016 Q2 | 16,125 | 0 |
| 2017 Q2 | 15,752 | 0 |
| 2019 Q4 | 16,157 | 0 |

A naïve sum across every exchange fails for six methodology-sensitive fields. The Phase 204 revalidation manifest records those mismatch counts and the current artifact digest. This is a sample-level integrity result, not a complete-universe reconciliation.

## Admission decision

**MIDAS remains NOT ADMITTED for strict daily PIT or alpha testing.** The quarterly batch-release cadence is now explicit, but exact per-quarter publication timestamps, permanent historical security identity and complete-universe reconciliation remain unresolved.

Allowed next step: build a quarterly release-vintage ledger from dated SEC release notices/RSS or preserved page snapshots. If historical release dates cannot be recovered, use MIDAS only prospectively after capturing each release with an immutable receipt timestamp. Do not backdate any daily row.

No return/alpha test, bootstrap/LOO, OOS evaluation or holdout use was performed. No data purchase or vendor contact occurred. Production and universe were unchanged. `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen; the legacy holdout remains `CONSUMED_NOT_PRISTINE`.

## Reproducibility and sources

- SEC launch event, 9 Oct 2013: https://www.sec.gov/newsroom/meetings-events/news-conference-announce-launch-market-structure-data-analysis-website-100913
- SEC Data Highlight 2013-03, 9 Oct 2013: https://www.sec.gov/about/odd-lot-rates
- SEC Data Highlight 2014-01, 9 Jan 2014: https://www.sec.gov/about/odd-lot-rates-post-transparency-world
- Current Market Structure Data Downloads: https://www.sec.gov/data-research/market-structure-data
- Metrics by Individual Security: https://www.sec.gov/data-research/sec-markets-data/marketstructuredata-security
- Metrics by Individual Security and Exchange: https://www.sec.gov/opa/data/market-structure/market-structure-data-security-and-exchange.html
- Phase 203 hosted sample reconciliation: https://github.com/jafelix81/NuevaEstrategia/actions/runs/42491346519/artifacts/13622046750
- Phase 204 latest hosted revalidation: https://github.com/jafelix81/NuevaEstrategia/actions/runs/42491346529/artifacts/13622036454
- Phase 204 current-run provenance manifest: `research/phase204_20261108_revalidation_manifest.json`

**Controls:** no raw-data download in this phase, no vendor contact or purchase, no returns/alpha test, no holdout use, no production or universe change.
