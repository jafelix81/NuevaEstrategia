# Smart Money Research State Addendum — Phase 659 (2026-11-27)

## New finding: both Form 4/A lineage gaps resolved

- Phase 658 identified two amendment accessions with blank `previous_accession` values.
- SEC primary filing indexes and ownership XMLs resolve the originals:
  - Crescent: amendment `0001104659-26-130067` → original `0001104659-26-105049`.
  - TRON: amendment `0001493152-26-053612` → original `0001493152-26-015786`.
- Crescent is a final-NAV share-count/price update for the same 2026-09-01 investment. Original and amended row-implied values both round to the reported USD 5,484,010.
- TRON adds Bravemorning Ltd as a joint reporting person; the four A/M transaction rows are identical to the original. They describe award/issuance and warrant/preferred conversion activity tied to PIPE financing, not open-market purchases.
- Five amendment rows reviewed; zero new economic events; zero signal-eligible rows.
- Resolved links are preserved in append-only `research/data/sec_form4_first_seen/amendment_lineage_resolutions.json`. The existing transaction ledger and blank `previous_accession` fields were not rewritten.

## Operational state checked first

- Latest Actions run inspected: Phase 658 run `45951568842`, offline-regression successful, artifact `15177630455`.
- Latest natural Form 4 run: `45917890802`; both jobs successful; 10 accessions parsed, 53 detail rows appended, 13 owner rows appended, zero signal-eligible rows.
- Latest natural Form 144 run: `45940802895`; both jobs successful; 10 accessions backfilled with 58 detail rows, zero signal-eligible rows.
- Latest natural 13F run: `45945369771`; both jobs successful; 29 accession observations, zero new accessions, no holdings downloaded, zero eligible observations. The log showed an empty `SEC_USER_AGENT` environment, but the configured fallback allowed all feeds to complete; this does not establish that Phase 616's stricter manual workflow can run.
- Latest natural FINRA run: `45939887443`; seven partial bootstrap files and one 403, zero first-seen eligible observations.
- Latest CFTC run: `45939298160`; 3,043 historical rows, zero signal-eligible historical rows; prospective collection only.
- No workflow was active when this phase began. No duplicate or manual workflow was dispatched.

## Frozen controls

- `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen.
- No signal promoted; no incremental alpha demonstrated.
- No prices/forward returns inspected; no event study, OOS, bootstrap, LOO or holdout test run.
- No production, universe, parameters, exposure, costs, capital or holding-period rules changed.
- No paid data, vendor contact, quote request or purchase; budget remains USD 0.
