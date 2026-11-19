# Phase 495 — FINRA Reg SHO facility-grain parser correction

**Audit cutoff:** 2026-11-19 04:14 UTC  
**Disposition:** **CORRECT THE SOURCE ROW GRAIN; CI PASSED 56/56; NO SIGNAL OR ALPHA ADMISSION.**  
**Main before PR:** `1068f7a28b06d3799c1c8549764ac61b3b7c928f`  
**PR:** [#151](https://github.com/jafelix81/NuevaEstrategia/pull/151) — merged  
**Merge commit:** `8aa9ef6ce2ab23e4dda9317524db79a31bfc44a9`

## 1. Preflight

The repository was checked before any change:

- Latest Actions inventory at preflight: 7,869 runs; latest 100 contained 72 successes, 26 failures and 2 cancellations; 0 active/queued.
- Branches enumerated: 318 before creating the Phase 495 branch.
- Open PRs: 56 before opening PR #151. Existing lines #61 (FINRA publication clock), #59 (CFTC prospective capture), #48 (Cboe source ranking), #37 (SEC 13D/G parent retrieval), and other historical branches were left untouched.
- Main's latest preflight commit was the first FINRA metadata-only poll, `1068f7a28b06d3799c1c8549764ac61b3b7c928f`.

## 2. First scheduled FINRA poll exposed a parser/schema mismatch

**Run:** [44453548570](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44453548570)  
**Window:** 2026-11-19 03:44:38–03:45:00 UTC  
**Jobs:** `offline-regression` success (52 tests); `live-capture` success.  
**Artifact:** [14495893727](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44453548570/artifacts/14495893727), 565 bytes, SHA-256 `c2a1de282eafa2a46de7c1da575d53436cdfc464d721113d23cb241b51fda3e7`.

The scheduled collector requested eight weekday dates (2026-11-18, 11-17, 11-16, 11-13, 11-12, 11-11, 11-10 and 11-09). All eight returned HTTP 200, but all eight were rejected as `invalid_file / duplicate_symbol`.

Artifact counts:

| Count | Result |
|---|---:|
| HTTP 200 | 8 |
| Invalid files | 8 |
| Valid files | 0 |
| First-seen / late-first-seen | 0 |
| Research-observation eligible | 0 |
| Signal eligible | 0 |

The append-only poll ledger records the eight failed attempts. The file-state map remained empty, no event was written, and no watermark advanced. The previous implementation computed raw hashes and response byte counts only after a successful parse, so these eight rows have blank hashes and zero byte counts. The raw response bodies were not retained; their historical hashes cannot now be reconstructed.

## 3. Official FINRA documentation establishes the correct grain

The parser's assumption that a daily file contains at most one row per symbol was incorrect.

FINRA's official *Short Sale Volume Daily Data User Guide* shows separate rows by Trade Facility. For example, the same symbol AAON appears under NQTRF with Market Q and NCTRF with Market B; AAIC appears under NYTRF/Market N and NQTRF/Market Q. The guide defines Market as a one-letter reporting-facility identifier. See [FINRA User Guide, pp. 2 and 7](https://www.finra.org/sites/default/files/2020-12/short-sale-volume-user-guide.pdf).

The official [Regulation SHO Daily Short Sale Volume File Layout](https://www.finra.org/sites/default/files/2021-07/DailyShortSaleVolumeFileLayout.pdf) specifies the fields Date, Symbol, ShortVolume, Short Exempt Volume, TotalVolume and Market; Market is one alphabetic facility code, and the trailer count represents data records.

Therefore the raw uniqueness key is **(trade date, symbol, market)**, not (trade date, symbol). Symbol-level features must be constructed by aggregating valid facility rows after validation. The prior assumption that Market could be a comma-joined set in one row was not supported by FINRA's official file layout.

## 4. Phase 495 correction

PR #151 updates the existing Phase 469 parser and tests; it does not create a parallel collector.

- Market is now a required header and must contain a single alphabetic facility code.
- Duplicate `(symbol, market)` rows are rejected; the same symbol under different markets is accepted.
- Short, short-exempt and total volume are validated per facility row and then summed with `Decimal` arithmetic to one in-memory row per symbol.
- Trailer validation and `row_count` remain at raw facility-row grain; `symbol_count` is the count of unique symbols; `facility_count` is reported separately by the parser.
- The Phase 468 labeler receives one aggregated observation per symbol, not one per facility.
- For every HTTP-200 response, SHA-256 and byte length are now recorded before parsing. Raw market data remains memory-only and is not committed.

### Validation

[PR #151](https://github.com/jafelix81/NuevaEstrategia/pull/151) merged after [Actions run 44456658463](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44456658463):

- `offline-regression`: **56/56 tests passed**.
- `live-capture`: correctly skipped on the pull-request event.
- No live request, raw data persistence or signal generation occurred during CI.

The new tests cover same-symbol multi-facility aggregation, duplicate symbol/facility rejection, invalid multi-character Market values, required Market header, and HTTP-200 invalid-payload hash/byte preservation without advancing file state.

## 5. No retroactive eligibility

The eight failed first-poll rows remain invalid and ineligible. They are not rewritten as HTTP 403/404 `not_available` observations. When the corrected parser first accepts older trade-date files, they remain bootstrap unless the existing prior-scheduled-not-available rule independently qualifies them. No first-seen time is backdated.

The next valid scheduled capture may qualify the current New York trade date for metadata research after actual local receipt, but all records remain `signal_eligible=false`. No manual dispatch, cron change, historical backfill, price join, event study, alpha test, OOS, bootstrap or LOO was performed.

## 6. Cross-source scheduled delivery

The delivery gap recorded in Issue [#150](https://github.com/jafelix81/NuevaEstrategia/issues/150) is resolved because all four scheduled delivery paths subsequently ran:

- Form 4/4-A: [44440313382](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44440313382) — 637 new unique accessions from 1,311 feed observations; metadata-only, no signal eligibility.
- Form 144/144-A: [44447184058](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44447184058) — 103 new accessions; 103/103 XML and acceptance reconciliations; no signal eligibility.
- CFTC TFF: [44453066854](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44453066854) — successful scheduled capture, but no new reports or revisions. The artifact retains 3,039 historical rows (852 each for three contracts and 483 for Russell E-mini), latest report 2026-11-10; PIT signal-eligible historical rows: 0; alpha test unauthorized.
- FINRA Reg SHO: [44453548570](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44453548570) — scheduled workflow ran, but data parsing failed as described above.

Issue #150 was closed as completed; the FINRA parser/data-quality issue is tracked by PR #151, not by the former delivery-gap issue.

## 7. Frozen strategy

`F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen. No universe, parameter, holding-period, capital, exposure, cost, holdout or production changes were made. No new signal was admitted.
