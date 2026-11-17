# Phase 446 — Phase 31 FINRA short-interest artifact truncation audit

Date: 2026-11-17

## Decision

**The Phase 31 short-interest panel is incomplete and unusable for zero inference or frozen-universe coverage. Phase 37's kill of the existing Phase 31 candidate remains in force. The FINRA source may be reconsidered only after complete asynchronous re-ingestion.**

This phase downloaded and inspected the already-existing GitHub Actions artifact `12588045711` from run `40164323397`. No new FINRA API data was requested. The ZIP was kept in the private working container and was not uploaded to the public repository.

## Artifact integrity and contents

- Artifact: `phase31-finra-flow-si-divergence`, ID `12588045711`.
- Downloaded ZIP size: 26 MB.
- ZIP SHA-256: `91f7683cf984cb2b00a6bd772608c3243ac9a56717930c6fd2092696e092a266`.
- `si_download_audit.csv` SHA-256: `477f94be7bc0f9c46df3547b9f470164e09b58a3aff8b9b9e68a953525305dff`.
- `short_interest_features.csv` SHA-256: `282e260c7fe085123f576d7315f1e38985b7e285572202b3d9cb22c64936066c`.

The ZIP contained 1,111 members. The SI audit contains 106 requested settlement dates; the feature file contains 9,420 filtered rows over 102 dates from 2022-06-15 through 2026-09-30.

## Critical discovery: every successful pull hit the synchronous API cap

The audit CSV shows:

| Result | Count |
|---|---:|
| Successful settlement requests | 102 |
| Successful requests returning exactly 5,000 rows | 102 |
| Failed requests | 4 |
| Feature rows retained after universe filtering | 9,420 |
| Unique observed tickers | 98 |
| Positive-row symbols per successful settlement | 84–96 |

FINRA's API documentation states that synchronous requests have a maximum of 5,000 records, while asynchronous requests support up to 100,000 records; the documentation also exposes `Record-Total`, `Record-Offset`, `Record-Limit` and related response headers for completeness/pagination control. [FINRA Developer Center — Working with Large Datasets](https://developer.finra.org/docs).

All 102 successful pulls returned exactly 5,000 rows, the documented synchronous ceiling. The SI audit file stores only `settlementDate, rows, universeRows, status, error`; it does not store `Record-Total`, `Record-Offset`, `Record-Limit`, async request IDs, or a pagination-complete flag. Therefore none of the 102 snapshots has evidence of completeness.

The four failed settlement requests are:

- 2024-01-15
- 2024-03-29
- 2026-10-15
- 2026-10-30

The first three are historical retrieval failures; 2026-10-30 was beyond the artifact's 2026-10-23 OOS end and must not be treated as an eligible observation.

## Alphabetical-prefix concentration

The 9,420-row feature file contains 98 unique tickers, all beginning with A–D:

| Initial | Unique symbols |
|---|---:|
| A | 34 |
| B | 19 |
| C | 32 |
| D | 13 |
| E–Z | 0 |

All 9,420 `currentShortPositionQuantity` values are positive; no zero rows are present in the feature file. This is strongly consistent with a prefix-truncated, alphabetically ordered response, although the raw API response order was not preserved, so exact server ordering is not proven.

**Correct interpretation:** 98 is the number of distinct symbols observed in the truncated subset after filtering to the frozen universe. It is neither complete positive-position incidence nor 98/335 effective coverage. Symbols E–Z may simply have been omitted beyond the 5,000-row cap. No absent symbol may be assigned zero from this artifact.

## Reconciliation with Phase 445 zero-vs-missing semantics

Phase 445 correctly identified that FINRA does not require zero-position submissions for issue symbols whose current-cycle short position has fallen to zero. That means a missing row can be a structural zero in a *complete* settlement snapshot.

Phase 446 adds the necessary condition that was not met in Phase 31: **the settlement snapshot must first be proven complete**. The 102 capped pulls fail that condition. The four failed pulls are also unknown, not zero.

Therefore:
- Phase 37's kill of the existing Phase 31 joint flow + short-interest panel remains valid and is strengthened.
- Phase 445's structural-zero rule remains valid in principle, but cannot be applied to the Phase 31 artifact.
- The FINRA Consolidated Short Interest source is not permanently rejected; it is conditional on a new complete retrieval.

## Required corrected retrieval design

For each settlement date:

1. Use the FINRA asynchronous Query API for the full `consolidatedShortInterest` historical dataset, with the settlement-date filter.
2. Record the asynchronous request ID, request/response timestamps, `Record-Total`, `Record-Limit`, offsets or partition keys, page counts, and a final reconciliation proving retrieved rows equal the source total.
3. If a single asynchronous request approaches its 100,000-record ceiling, partition deterministically by market/exchange fields and reconcile the disjoint partitions to a single settlement total.
4. Preserve raw response vintages and any later corrections; do not overwrite prior snapshots.
5. Only after full-snapshot completeness is proven, join the effective-dated 335-name security master. For a valid active/in-scope security with no row in a complete snapshot, record a structural zero; otherwise retain unknown/missing.
6. Preserve `revisionFlag`, `stockSplitFlag`, raw current/previous quantities, official publication date and 16:40 ET availability bound, plus prospective `first_seen_utc`.
7. Recompute positive-position incidence separately from effective universe coverage. Do not run a return test until the identity and snapshot-completeness gates pass.

## Reproducible audit

The new standard-library audit script reads the existing artifact ZIP without embedding or redistributing its market data. It flags synchronous-cap hits, failed settlements, missing completeness metadata, observed ticker-prefix concentration, and whether zero inference is allowed.

The script reproduced:
- 102/102 successful requests at the 5,000-row cap.
- 4 failed requests.
- 9,420 feature rows, 102 dates, 98 observed symbols.
- A–D only (34/19/32/13); no E–Z.
- Zero complete snapshots proven; zero inference not allowed.

Five synthetic regression tests passed locally. No CI workflow was dispatched for this research-only audit.

## Current conclusion

- **Phase 31 short-interest data: KILL / unusable as retrieved.**
- **FINRA source: conditional candidate only after complete async re-ingestion.**
- **No alpha, feature, or return result is admitted.** Phase 31's 36-date diagnostics remain exploratory, not an apples-to-apples full-universe OOS result.
- No new FINRA data was downloaded; only the historical GitHub Actions artifact was inspected.
- No production workflow, trading code, F80 parameter, universe, holdout, capital, or exposure was changed.
- `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen.

## Operational preflight — 2026-11-17 01:17 UTC

- Main HEAD before this phase: `e9cb6510492ca5c9b520c897ab366696d1798b53` (Phase 445).
- Branches: 280 after Phase 445; open PRs: 56.
- Latest known completed research CI: Phase 444 run `43990197952`, 18/18 offline tests passed. The log's dummy accession is a synthetic fixture, not a live SEC event.
- SEC live run `43970444015`: Form 144/A timeout after retries, no artifact. Phase 444 partial-feed persistence fix is merged; no post-merge live capture was confirmed in this audit.
- CFTC run `43525140200`: bootstrap only, 3,035 warm-up records, zero prospective eligible records; artifact `14084802705` SHA-256 `c7a652038336f852e3c51792d1bdc96ebc1368176bdafdae0693332fb4224eef`. The next scheduled capture was not due.
- The connected GitHub interface does not expose a current workflow-run listing endpoint. Run/job/log/artifact records cited above were fetched directly; no manual workflow was dispatched or duplicated.
