# Phase 319 — live SEC daily-index format and original-header pilot

**Date:** 2026-11-12 UTC  
**Status:** PASS — seven raw SEC daily form indexes and fourteen original filing headers reconciled.  
**GitHub Actions:** [run 43170779986](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43170779986) — success, 39/39 regression tests.  
**Artifact:** [13922595355](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43170779986/artifacts/13922595355)  
**Artifact ZIP SHA-256:** `f916eba4f2ad18a45ba45506dd93e12b116f3d7faf4c82a77befebfc221502ff`

## 1. Live daily-index sample

Seven actual SEC daily form indexes were fetched with an identified User-Agent and `Accept-Encoding: identity`:

| Index date | Quarter | SHA-256 |
|---|---|---|
| 2006-01-03 | 2006 Q1 | `4e3454c7c2a91fb398ebdf1c99b0c10d51d314818438d87542ceb42188a24cf2` |
| 2012-01-03 | 2012 Q1 | `dcd6faae6b8a41656cf06f91ca9c192d400e3a2a8aeaf9d1beccbf9d4438275b` |
| 2023-01-03 | 2023 Q1 | `527762f8a4b6ebe62adce5f0dd208eeb8442e3c113d492da88ac508068eeb49b` |
| 2023-04-03 | 2023 Q2 | `bdd64b4be46fefb2a6cf8a4f23921fd573b87c95cbbe345cd070ca5e059f630d` |
| 2025-07-01 | 2025 Q3 | `bdf95bb08871e4801ec678fbd7cc32925199255ac16e4c643c8259748cb5771d` |
| 2026-07-01 | 2026 Q3 | `b44e0b92a6e5ddd7e97712681c69150dde1a8964d9ac5c1d32c90c8d62b1c379` |
| 2026-11-10 | 2026 Q4 | `f4f72829345f2e538432a4e699cc4c8ea5dc4d280a24eeed1ed9588d546a2c06` |

All seven files used the legacy fixed-width layout, including the 2026 sample. Across them:

- 19,198 Form 4 / Form 4/A entity rows encountered; 19,195 retained after collapsing three exact duplicate rows.
- 9,356 accessions were multi-entity in the seven-file sample.
- 22,783 non-ownership form rows were correctly ignored.
- Zero malformed rows after the multi-word form-type parser correction.
- Zero row-CIK/path-CIK mismatches, zero filed-date/index-date ordering violations and zero conflicting accession identities.

This is a format smoke sample, not a probability sample and not a market-wide prevalence estimate.

## 2. Original-document crosscheck

Fourteen accessions were selected deterministically: seven Form 4 and seven Form 4/A. All fourteen original submission headers matched their index identity on accession, form, issuer CIK and FILED AS OF DATE; all fourteen contained ACCEPTANCE-DATETIME.

Every sampled accession had two CIK/entity rows in the daily index. In six of fourteen cases, the first selected path was under a non-issuer CIK. The original header's CENTRAL INDEX KEY identified the issuer row; fetching through that issuer row returned the identical SHA-256 payload. This is why the parser retains entity rows and identifies the issuer by the original header rather than assuming the first index row is the issuer.

All fourteen sample index dates equaled their filed dates (zero-day index lag). Fourteen acceptance times were available; four were at or after 17:30 ET and none at or after 22:00 ET. ACCEPTANCE-DATETIME is not transmission commencement and is not an exact first-public-receipt timestamp.

## 3. Parser corrections discovered by live data

The first live attempt exposed two parser/test weaknesses:

1. Legacy fixed-width rows can contain multi-word form types such as `DEF 14A`, `APP ORDR`, `CT ORDER` and `1-A POS`. The previous one-token regex misclassified these non-ownership rows as malformed. The parser now extracts the right-hand CIK/date/path fields first, then splits the left prefix once into form type and company name.
2. Fixed-width test fixtures contained double-escaped newline literals. These fixtures were corrected to actual line breaks.

A separate temporary identity rule incorrectly treated different CIK/company-name rows for the same accession as conflicts. Live index counts and the original-header sample confirmed that ownership accessions can be indexed under multiple entity CIKs. The parser now preserves those rows, requires each row CIK to match its own path CIK, and quarantines only conflicting form/date or conflicting names for the same entity CIK.

## 4. PIT decision

- The daily index supplies a reproducible **date-level** observation candidate, not an intraday first-public timestamp.
- The original header's ACCEPTANCE-DATETIME is retained as acceptance metadata only; it is not substituted for transmission-start time.
- The Phase 279 bulk-archive accession join is still outstanding. This smoke test samples rows from daily indexes themselves, so it does not yet measure bulk-to-index coverage or missed accessions.
- No raw index or filing bytes were uploaded to CI artifacts. The artifact contains only parsed metadata, SHA-256 hashes and crosscheck results.

## 5. Next gate

Join a deterministic sample from the six Phase 279 quarterly Form 345 bulk archives to the daily index files, search filing date and next EDGAR business day, and reconcile accession, form, issuer CIK, filing date and original header. Keep any unresolved accession or PAC case quarantined; do not backfill a first-public timestamp from ACCEPTANCE-DATETIME.

No return, alpha, bootstrap/LOO, chronological OOS or holdout test was run. F80, production, universe, capital and parameters remain frozen. No vendor was contacted, no data was purchased and no email was sent.
