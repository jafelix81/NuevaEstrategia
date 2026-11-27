# Smart Money Research State Addendum — Phase 656 (2026-11-27)

**Mainline documentation:** [Phase 656 report](PHASE656_FINRA_POSTMERGE_NATURAL_CAPTURE_VALIDATION_2026-11-27.md) · [JSON summary](PHASE656_FINRA_POSTMERGE_NATURAL_CAPTURE_VALIDATION_2026-11-27.json)

## Latest operational result

- Phase 650's FINRA partial-symbol quarantine fix (PR #247, merge `c7379f42`) passed 62/62 offline tests and its first natural post-merge live capture, run `45939887443`, completed both jobs successfully.
- Seven daily files (2026-11-17 through 2026-11-25) parsed as valid partial panels. BCPC and TPC each appeared twice in every file; 14 symbol-date groups / 28 row occurrences were quarantined. No exact row duplicates were found. Other unique-symbol rows were retained by the parser.
- The 2026-11-26 file returned 403. All seven successful files were bootstrapped because no prior eligible first-seen state existed; first-seen=0, late-first-seen=0, research-eligible=0 and signal-eligible=0. No historical first-seen was imputed.
- FINRA raw rows and volume values remain unpersisted. This is parser/clock validation only, not an investable short-flow feature panel.

## Other feed deltas

- Form 144 run `45940802895`: 53 feed observations appended, no new accessions, 10 existing accessions backfilled with 58 detail rows; ledger 845 accessions / 5,595 detail rows; 807 bounded research-observation filing headers; 158 backfill accessions pending; zero signal-eligible rows.
- Form 4 run `45917890802`: 10 accessions parsed, 13 owner rows appended, 14 crosswalk rows / 12 matched accessions, zero eligible matches.
- 13F run `45910142871`: 29 existing accession observations, zero new accessions, no holdings downloaded, zero eligible signals.

## Next gates

1. Observe the next natural FINRA poll for a conservative late-first-seen of 2026-11-26 and first-seen of the next trade-date file. Do not manually backfill or backdate historical observations.
2. Keep BCPC/TPC quarantined until row grain is independently resolved; retain no summed or guessed values.
3. Continue Form 4 owner/footnote enrichment and effective-dated identity/F80 checks before any event test.
4. Keep the SEC 13D/G global-index sample manual-only; do not use the legacy F80-filer-only workflow.

## Frozen controls

- `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen.
- No signal promoted and no incremental alpha demonstrated.
- No new OOS, bootstrap, LOO or forward-return test; holdout untouched.
- No price data inspected, no vendor contacted, no quote requested and no data purchased. Budget remains USD 0.
