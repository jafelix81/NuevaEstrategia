# Phase 165 — SEC 13(f) resumable quarterly-list overlap audit

**Date:** 2026-11-06  
**Status:** IMPLEMENTED — checkpointed 45-quarter run is triggered by this commit; empirical overlap result pending.  
**Research role:** Historical Section 13(f) eligibility/identity cross-check only, not an institutional-flow signal.

## 1. Preflight: current repository and workflow state

Before writing:

- Branch: `phase99-broad-pit-universe-charter`, head `73435fa8b7d3a3f83345d466e820f004783ad5cf`.
- PR [#13](https://github.com/jafelix81/NuevaEstrategia/pull/13) is open, mergeable and unmerged.
- The branch inventory was paginated: 100 + 29 = **129 branches**.
- The latest Phase 163 run [42275261288](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42275261288) and Phase 164 run [42275261269](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42275261269) completed successfully. Phase 149 OpenFIGI [42275261108](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42275261108) also completed successfully.
- No queued or in-progress workflow existed at preflight; no active work was duplicated.

Phase 149's completed 553-CUSIP audit found 438 primary mappings, 115 primary no-matches, six unique fallback recoveries and 109 remaining no-matches. It found one cross-CUSIP shareClassFIGI pair, subsequently adjudicated only as the source-dated TSX bridge in Phase 164. This does not create a complete security master.

## 2. Why Phase 129 needed a new execution design

The prior Phase 129 job [42081987897](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42081987897) was cancelled at **2026-11-05 18:57:42 UTC**, at its 45-minute job limit. Its SEC 13(f) download/parse step was cancelled; no artifact was produced.

The inspected Phase 129 implementation had four avoidable bottlenecks:

1. It processed 45 quarterly snapshots serially (2015Q3–2026Q3).
2. It tried up to six candidate URLs per quarter.
3. It retried permanent HTTP 404 responses, as well as transient failures.
4. It wrote the final manifest only after the entire 45-quarter loop, so cancellation discarded all completed work and emitted no durable partial checkpoint.

## 3. Official SEC archive inspection and parser correction

The SEC's [Official List of Section 13(f) Securities](https://www.sec.gov/rules-regulations/staff-guidance/official-list-section-13f-securities) page says the list is updated quarterly and, as reviewed on 2026-10-06, exposes archives back to 1996 and through 2026Q3.

I inspected representative official files:

- [2015Q3 PDF](https://www.sec.gov/divisions/investment/13f/13flist2015q3.pdf): 520 pages; the document says the list was current as of 2015-09-15 and shows a PDF Run Date of 2015-10-06.
- [2020Q1 TXT](https://www.sec.gov/files/investment/13flist2020q1.txt): fixed-width rows, 8,880 text lines; no embedded `Run Date` string.
- [2026Q3 TXT](https://www.sec.gov/files/investment/13flist2026q3.txt): fixed-width rows, 25,789 text lines; no embedded `Run Date` string.

**Parser defect identified:** the Phase 129 generic CUSIP-line regex does not reliably parse the fixed-width TXT convention when the option marker `*` is immediately adjacent to the issuer name (for example, `B38564108*EURONAV...`). The old fallback only scanned columns 1–9 if fewer than 1,000 CUSIPs had already parsed, so a partially parsed file could silently omit many starred rows while still exceeding the fallback threshold.

Phase 165 uses the documented fixed-width layout directly: columns 1–9 are the CUSIP; column 10 is the option marker; issuer text follows. A regression fixture covers both starred and unstarred rows.

For 2020 onward, the official archive page links TXT files at `/files/investment/13flistYYYYqQ.txt`; Phase 165 tries TXT first and retains PDF fallbacks. For 2015Q3–2019Q4 it uses the legacy PDF archive path first.

TXT files do not carry the PDF Run Date field. When an HTTP Last-Modified header is available, Phase 165 records it as a **generation/retrieval metadata proxy only**. If neither Run Date nor Last-Modified exists, the snapshot remains usable for coverage counts but receives no availability proxy and cannot enter the prior-list PIT sensitivity calculation.

## 4. Resumable execution architecture

The new workflow uses:

- One preparation job to download the immutable Phase 124/127 artifacts, verify provenance and create a compact 599-filing sample.
- **Nine deterministic round-robin shards × five quarters**, balancing the 18 legacy PDF quarters at two per shard.
- At most three concurrent shards, with a 20-minute per-shard timeout.
- A quarter-level checkpoint after every download/parse.
- Permanent 404s are not retried; only transient timeout/408/429/5xx classes receive a bounded retry.
- A final aggregation job that reconciles all shard outputs, computes the same 1-day and 5-day conservative availability sensitivities, and preserves same-quarter matches only as a lookahead diagnostic.

Each shard processes the raw 13(f) CUSIP set in memory and discards it after producing the sample match booleans. Artifacts contain source URLs/hashes, file metadata, counts and match booleans against CUSIPs already present in the public Phase 127 13D/G sample. They do **not** contain raw 13(f) list rows, raw 13(f) CUSIPs, issuer names or issuer descriptions.

## 5. Point-in-time and economic interpretation

This remains an identity/eligibility cross-check, not an ownership signal:

- The list is only the Section 13(f)-reportable security population; a no-match does not mean a security is invalid or non-tradable.
- PDF Run Date and HTTP Last-Modified are not verified first-publication timestamps.
- The +2 and +6 calendar-day dates remain sensitivity proxies, not strict PIT proof.
- The list is not a complete security master and cannot establish historical ticker, share-class, ADR, delisting or corporate-action continuity.
- A match does not prove that any institution held the security.

No forward-return, signal, bootstrap/LOO, OOS or final-holdout test is authorized by this phase.

## 6. CI and expected outputs

New files:

- `research/phase165_sec13f_resumable_audit.py`
- `research/test_phase165_sec13f_resumable_audit.py`
- `.github/workflows/phase165_sec13f_resumable_audit.yml`

The offline suite covers fixed-width parsing, all-45-quarter shard partitioning, balanced PDF load, transient/permanent HTTP handling, timestamp-proxy availability, no-lookahead selection, missing-vs-negative matches and artifact privacy.

The workflow produces a final aggregate artifact with:

- `phase165_sec13f_snapshot_manifest.csv`
- `phase165_sec13dg_13f_cusip_match_audit.csv`
- `phase165_sec13f_resumable_summary.json`

The live 45-quarter run is triggered by the code/workflow commit. Its empirical counts and artifact link will be appended after completion; this report does not pre-claim a coverage result.

## Decision

**Proceed with the resumable source-feasibility audit.** Keep the 13(f) list as a conditional identity/eligibility reference only. Even a successful 45-quarter download does not verify first-publication time or create alpha.

No vendor purchase/contact, no production change, no final holdout use and no F80 change. `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen.

## Official SEC references

- [Official List of Section 13(f) Securities and archive links](https://www.sec.gov/rules-regulations/staff-guidance/official-list-section-13f-securities)
- [2015Q3 official PDF](https://www.sec.gov/divisions/investment/13f/13flist2015q3.pdf)
- [2020Q1 official TXT](https://www.sec.gov/files/investment/13flist2020q1.txt)
- [2026Q3 official TXT](https://www.sec.gov/files/investment/13flist2026q3.txt)


## Phase 165 post-run adjudication (2026-11-06)
- The initial Phase 165 CI attempt failed because the test fixture encoded literal backslash-n instead of line breaks; corrected before the successful run.
- The first all-PDF run completed 45/45 but exposed a bug in the imported Phase 129 CUSIP wrapper: it compared a boolean to a string and reported zero checksum-valid list identifiers. Phase 165 was corrected to call the tested Phase 125 boolean validator directly.
- SEC TXT responses were compressed when gzip/deflate was advertised; the initial TXT parser therefore fell back to PDF. Phase 165 now requests identity encoding and decodes compressed responses defensively. The corrected run completed 45/45, with 25 TXT and 20 PDF snapshots.
- The direct TXT-first aggregate's Last-Modified PIT proxy is superseded: 22/25 historical TXT files carry a 2026-09-04 Last-Modified date, a later archive migration/republication timestamp. See Phase 166 for the PDF Run Date bridge and cross-format concordance.
- The standard check-digit diagnostic is not a universal exclusion rule: the 2026Q3 official list contains CALL/PUT series identifiers that fail the standard equity CUSIP check-digit test. The field named `invalid_unique_cusips` should be read as nonconforming-to-standard-check-digit candidates, not proof of malformed securities.
- Final PIT adjudication and content concordance are documented in [Phase 166](PHASE166_SEC13F_CROSS_FORMAT_PIT_METADATA_BRIDGE_2026-11-06.md).
