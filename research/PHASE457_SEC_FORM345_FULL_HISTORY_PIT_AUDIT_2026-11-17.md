# Phase 457 — SEC Insider Transactions full-history coverage and point-in-time clock audit

**Audit time:** 2026-11-17 14:28 UTC  
**Main HEAD at preflight:** `be05737e7a1e56ac09b84e00754b385baa6048ff` (Phase 456)  
**Disposition:** SEC Form 3/4/5 bulk data are a feasible, free, long-history source for a full descriptive census, but the quarterly bulk files are not a point-in-time event feed. Preserve the source as a conditional candidate; do not admit an insider signal or run returns until accession-level acceptance/first-public-receipt and historical security identity are reconstructed.

## 1. Repository and Actions preflight

- Latest overall run: [44087732566](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44087732566), Phase 455 PR CI. The single `audit` job completed successfully; six tests passed; aggregate-only artifact [14329718579](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44087732566/artifacts/14329718579) was uploaded (1,567 bytes).
- Phase 454 PR CI: [44086525354](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44086525354). Offline regression passed; `live-capture` was correctly skipped on pull_request; no artifact.
- Latest main scheduled SEC Form 144 run: [44083941814](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44083941814). Offline tests passed, but the live job failed in acceptance reconciliation with the legacy CSV header mismatch. The schema migration fix was subsequently merged in [491d79f4f8d11d8cc76f7e53c9961d6e5040380c](https://github.com/jafelix81/NuevaEstrategia/commit/491d79f4f8d11d8cc76f7e53c9961d6e5040380c); PR CI passed, but its live-capture job was skipped.
- The next configured SEC schedule slot after the fix, 2026-11-17 13:47 UTC, was absent from the Actions run list at 14:28 UTC. The latest observed schedule event remains 44083941814 at 12:31 UTC. Workflow enabled/disabled state is not exposed by the connected read interface; do not infer it from the missing event.
- CFTC's configured 22:25 UTC slot was still in the future at preflight. No manual dispatch, rerun, or duplicate workflow was started.
- Actions API: 7,696 total runs; zero in-progress and zero queued in the latest 100-run window. Branch pagination: 289 unique branches (100 + 100 + 89; fourth page empty); 56 open PRs; 71 workflow files.
- No active workflow was duplicated. Main HEAD is `be05737e7a1e56ac09b84e00754b385baa6048ff`.

## 2. New official SEC coverage finding

The SEC's current Insider Transactions Data Sets page reports coverage from January 2006 through September 2026 and lists 83 quarterly ZIP archives, from 2006 Q1 through 2026 Q3. Summing the SEC-displayed archive sizes gives approximately **887.43 MB compressed** (the sum is approximate because the page reports rounded MB values). The latest 2026 Q3 archive is listed at 8.26 MB.

The SEC states that:
- the files are extracted from the XML portions of Forms 3, 4 and 5 and are presented as filed;
- the data are updated quarterly;
- submissions filed after 5:30 p.m. Eastern on the last business day of a quarter are included in the next quarterly posting;
- the data may contain filer errors or extraction/compilation errors and omit metadata available in the full filings.

The 83-archive history makes a complete descriptive census technically plausible without buying a vendor dataset. It does **not** make the bulk archive a historical point-in-time feed: quarterly publication time is later than the individual filing and cannot be assigned as the trade signal's first-availability time.

Official source: [SEC Insider Transactions Data Sets](https://www.sec.gov/data-research/sec-markets-data/insider-transactions-data-sets).

## 3. Schema and event semantics that constrain the signal

The SEC's seven-page data dictionary describes up to eight UTF-8, tab-delimited tables:

- `SUBMISSION`: accession number, filing date, period of report, original-submission date for amendments, document type, issuer CIK/name and issuer trading symbol.
- `REPORTINGOWNER`: reporting-owner CIK, name, relationship (officer, director, ten-percent owner or other) and title.
- `NONDERIV_TRANS` / `DERIV_TRANS`: security title, transaction date, transaction code, shares, price/value, acquired/disposed code, direct/indirect ownership and related fields.
- `NONDERIV_HOLDING` / `DERIV_HOLDING`, `FOOTNOTES`, and `OWNER_SIGNATURE`: holdings, derivative terms, explanatory footnotes and signature details.

The data dictionary is explicit that `ACCESSION_NUMBER` is the submission key and that transaction rows have accession-plus-surrogate keys. The bulk `SUBMISSION` table has a filing **date**, not the EDGAR acceptance time-of-day.

Two semantic traps are material:

1. Transaction code **P** means “open market or private purchase” (and code S means “open market or private sale”). P is not proof of an exchange execution. A P-coded acquisition must remain a mixed purchase until footnotes and the full filing establish the execution mechanism. Do not label every P row “open-market buying.”
2. Forms 3/4/5 and their amendments are included. The data are as-filed and can contain redundancies or discrepancies relative to earlier filings. A Form 4/A is a new disclosure about a prior filing, not automatically a new economic transaction. Preserve the original and amendment as separate information-arrival events, link them by accession/original-submission lineage, and do not double-count amended rows as fresh trades.

The SEC notes that the `AFF10B5ONE` element was added to the 2023–2025 datasets in July 2025 and that future datasets would be processed similarly. This is a field-regime break: absent/NULL before verified coverage is **unknown**, not “not under a 10b5-1 plan.” Do not use a missing historical flag as a negative label.

Official source: [Insider Transactions Data Sets — documentation PDF](https://www.sec.gov/files/insider_transactions_readme.pdf).

## 4. Correct point-in-time clock

The SEC Webmaster FAQ explains that the EDGAR header contains `<ACCEPTANCE-DATETIME>` in YYYYMMDDHHMMSS form. It also states that filings often appear on sec.gov within 1–3 minutes of the EDGAR timestamp, but the lag can increase and is not guaranteed; there is no timestamp that identifies the exact instant the document first became publicly available on sec.gov. The SEC recommends Latest Filings and associated RSS as the closest public resources to real time.

For Forms 3, 4 and 5 specifically, the SEC's filing-status guide says submissions transmitted after 5:30 p.m. ET but before 10:00 p.m. ET can still receive that day's filing date and be disseminated that day. Do not apply a generic next-business-day filing-date rule to Section 16 forms.

Research clock policy:
- `TRANS_DATE` is the economic transaction date, not the information-availability date.
- `FILING_DATE` is date-only and cannot substitute for acceptance time.
- EDGAR `ACCEPTANCE-DATETIME` is the official acceptance timestamp, but not a guaranteed exact public-web availability timestamp.
- For prospective tradability, retain the Phase 403-style first-seen poll receipt as an upper bound on public availability, with feed/poll health and gaps preserved. Never backfill a first-seen time from the filing date, transaction date, archive quarter, or current archive download time.
- Historical acceptance times may support a conservative event-time reconstruction; any unobserved public-web lag must be treated explicitly, not silently assumed to be zero.

Official sources:
- [SEC Webmaster FAQ — EDGAR timestamps and dissemination lag](https://www.sec.gov/about/webmaster-frequently-asked-questions)
- [SEC: Determine the Status of My Filing](https://www.sec.gov/submit-filings/filer-support-resources/how-do-i-guides/determine-status-my-filing)
- [SEC: Accessing EDGAR Data](https://www.sec.gov/search-filings/edgar-search-assistance/accessing-edgar-data)

## 5. Implications for Phase 455 and the 335-name universe

Phase 455's six-quarter sample contained 413 candidate transaction rows, 262 accessions, 109 issuer CIKs and 224 issuer-filing events. Strict exact as-filed ticker matching found five issuer-filing events across VRTX, CRSP, NTLA and OPEN, all in 2025 Q3 or 2026 Q3. This remains a sampled descriptive overlap, not a representative coverage estimate or a historical membership join.

A full 83-quarter census should therefore be the next *coverage* step, not a return test. It must:
- retain issuer CIK and accession as primary identity anchors;
- use as-filed issuer symbol only as an issuer-level hint, not as transaction-level share-class identity;
- join `SECURITY_TITLE`, CIK and an effective-dated security/listing crosswalk;
- reconstruct historical F80 membership by date rather than retroactively applying the current 335-symbol snapshot;
- preserve unresolved, multiple-class, ticker-change, merger, delisting and OTC states instead of forcing a match.

## 6. Preregistered candidate construction — not yet authorized

If coverage and PIT gates pass, candidate families should be separated rather than blended:
- P-coded acquired transactions, split into derivative/non-derivative, direct/indirect, owner role and confirmed versus unresolved private/exchange mechanism;
- independent insider breadth (distinct owner CIKs) and clustered purchases by issuer/date;
- transaction value scaled by contemporaneous market capitalization and trailing dollar volume, with all denominators available as of the information timestamp;
- `AFF10B5ONE=true` separated from false; missing/unsupported periods remain unknown;
- amendments handled as disclosure corrections/updates, not duplicate economic trades;
- S-coded sales analyzed separately because sales can reflect liquidity, taxes, vesting or diversification and are not symmetric with purchases.

Do not infer that a director/officer is “informed” from the filing alone. Test both continuation and reversal, control for prior returns, volatility, earnings/news windows, liquidity, firm size and insider role, and compare against the frozen LTM/F80 baseline with identical exposure, costs, chronological splits, block bootstrap, leave-one-out and untouched OOS.

## 7. Next gates

1. Verify the repository's `SEC_USER_AGENT` secret is configured with a monitored contact. Prior research state records this as a blocker; the connected interface cannot inspect secret values, so its current state cannot be confirmed here.
2. Run a single-quarter 2026 Q3 archive pilot: download only from the official SEC URL, record HTTP metadata and SHA-256, verify all table names/headers/keys, and emit aggregate-only results. Do not commit raw SEC archives.
3. If the pilot passes, process all 83 quarters sequentially with explicit rate limits, retries, per-archive hashes, row counts, schema versions and quarantine for corrupt/inconsistent files. Keep raw downloads in a private/ephemeral workflow workspace; publish aggregate manifests only.
4. Build accession-level acceptance-time joins and a prospective first-seen ledger. Never infer historical first-seen time from the quarterly archive.
5. Complete effective-dated issuer/security-class/listing and historical-universe joins. Only then authorize an event-study and incremental OOS test.

## 8. Final disposition

- SEC Form 3/4/5 bulk data remain a **high-value, free historical census source**, with 2006–2026 coverage and manageable but nontrivial archive volume.
- The quarterly archives are **not** strict-PIT by themselves. Exact event-time and first-public-receipt controls remain mandatory.
- Code P is mixed open-market/private purchase; the AFF10B5ONE field has a documented coverage regime; amendments must not be double-counted.
- No full 83-quarter download was performed in this phase; no vendor data were purchased; no new raw data were committed.
- No signal, forward-return, alpha, OOS, bootstrap, LOO or holdout test was run. No production change.
- `F80_TOP20_PARTIAL50_BASELINE_C20`, universe, parameters, capital, exposure, holding rules and holdout remain frozen.
