# Phase 338 — Broad SEC Form 4 issuer-identity coverage audit
**Date:** 2026-11-12  
**Branch:** phase338-sec-broad-form4-identity-sample  
**PR:** #27 (Draft)  
**Run:** [43236684291](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43236684291) — SUCCESS  
**Artifact:** [13953101909](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43236684291/artifacts/13953101909)

## Decision

The broad sample confirms that SEC CIK resolution is reliable, but periodic-filing XBRL is not a sufficiently complete historical security-master source by itself. Keep issuer CIK as the primary issuer key; do not admit ticker, class, listing or permanent-security mappings from this audit into a production security master.

## Sampling design

- Rebuilt the immutable Phase 321 census: **317,267 Form 4/4-A accessions** across 2006Q1, 2012Q1, 2023Q1, 2023Q2, 2025Q3 and 2026Q3.
- Excluded all **56 issuer CIKs** in the purposive Phase 325 set of 28 same-day ticker-collision pairs.
- The remaining frame contained **27,501 issuer-quarter units**.
- Selected **72 issuer-quarter units**, 12 per quarter, with 72 distinct issuer CIKs. One accession per issuer-quarter was selected by deterministic SHA-256; index exceptions were preserved as a separate stratum.
- Strata: 33 canonical single-owner, 12 canonical multi-owner, 6 missing/placeholder, 6 multi/freeform, 6 other noncanonical, 6 exchange-prefixed and 3 index exceptions.
- Design weights are the issuer-quarter population count divided by the sampled count within each quarter/stratum. These are descriptive weighted estimates for this frame, not estimates for all Form 4 accessions or the full trading universe.

Both source ZIP hashes and the deterministic sample-manifest hash were checked before SEC requests. All 72 issuer CIKs resolved through SEC Submissions; no current-active-company filter or current ticker list was used.

## Results

| Measure | Sample result | Design-weighted result |
|---|---:|---:|
| SEC Submissions issuer CIK resolved | 72/72 (100.0%) | 100.00% |
| Fresh prior periodic filing, 1–365 days before sample filing date | 63/72 (87.5%) | 86.70% |
| Prior periodic document retrieved and SHA-256 recorded | 63/72 (87.5%) | 86.70% |
| TradingSymbol fact present | 35/72 (48.6%) | 48.06% |
| TradingSymbol fact with its own class-axis context | 10/72 (13.9%) | 13.47% |
| Direct class binding conditional on a TradingSymbol fact | 10/35 (28.6%) | 28.03% |
| TradingSymbol fact with its own listing-axis context | 0/72 | 0.00% |

Anchor disposition: 63 fresh, 8 with no prior supported periodic filing, 1 stale; zero invalid non-pre-event anchors. Document disposition: 42 XBRL instances parsed, 21 primary HTML documents with no target facts, and 9 not tested because no fresh anchor existed.

The 2006Q1 and 2012Q1 subsamples produced **zero TradingSymbol facts in 24 issuer-quarter units**. Their nine fresh documents in each period were primary HTML without the target structured facts. This is a material historical-coverage gap, not a parser mismatch.

Among the 25 observations where both a canonical candidate and a comparable, filed-date-matched index record existed, the prior periodic filing's TradingSymbol set contained the candidate in all 25 cases (17 single-symbol matches, 8 matches among multiple symbols; zero mismatches). This is a small, stratified identity-consistency check—not proof of broad class/security identity or an alpha result. Sixteen candidates were unavailable for exact comparison, three index exceptions were marked non-comparable, and 19 observations had no TradingSymbol fact.

The 33 symbol facts carrying explicit class-axis members in the ten directly bound documents classified by member-name diagnostics as 13 common-equity, 13 debt, 5 preferred/depositary, 1 warrant and 1 custom/other. These are fact rows, not unique listed securities. The axis is useful for distinguishing instrument types when present, but coverage is sparse.

**Important limitation:** zero EntityListingsExchangeAxis dimensions were attached to the sampled TradingSymbol facts. This audit did not separately retain or measure SecurityExchangeName fact values. Therefore, do not interpret the zero listing-axis result as proof that the filings contain no exchange information; that is the next targeted extraction.

## Identity and PIT disposition

- Issuer identity: SEC CIK resolved for all 72 sample units.
- Symbol identity: conditional consistency is encouraging, but only 35 documents had a TradingSymbol fact and 16 sample candidates were unavailable for exact comparison.
- Share-class identity: direct class-axis evidence exists in 10 documents, but is not broad enough for admission.
- Listing identity: direct listing-axis binding was not observed; SecurityExchangeName remains unmeasured.
- Permanent security identity: **0 admitted**. No stable, effective-dated security identifier or complete share-class/listing crosswalk was established.
- Universe coverage: **not admitted**. The frame is a historical SEC Form 4 issuer frame, not the complete historical trading universe.
- Availability: SEC filingDate and daily-index dates are date-granular. They are not first-public timestamps. The selected prior periodic filing was strictly earlier by calendar date and no older than 365 days, but this is not strict intraday PIT and authorizes no return backtest.

The three sampled daily-index exceptions (two filed-date conflicts and one not found on the filed or next EDGAR business day) were not used for ticker-match comparisons.

## Controls

No alpha, return, bootstrap, LOO, chronological OOS or holdout test was run. No data was purchased; no vendor was contacted. Production, universe, capital and parameters were unchanged. F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen.

## Next work

1. Re-extract SecurityExchangeName from the 42 XBRL instance documents and test whether it shares a context with TradingSymbol; keep issuer-level exchange facts separate from direct security-level bindings.
2. Preserve and classify the existing class-axis members (common, preferred/depositary, warrant, debt, custom) without collapsing distinct instruments.
3. Expand the sample to an intermediate XBRL era and a larger issuer sample, then compare identity coverage by period and issuer type.
4. Only after effective-dated listing/security identity and historical-universe coverage pass should transaction-level Form 4 features be constructed and tested against frozen LTM/F80.

No Smart Money signal is admitted by Phase 338.
