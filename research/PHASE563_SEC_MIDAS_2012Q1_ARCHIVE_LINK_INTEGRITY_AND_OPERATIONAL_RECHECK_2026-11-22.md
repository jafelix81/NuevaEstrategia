# Phase 563 — SEC MIDAS 2012 Q1 archive-link integrity and operational recheck

**Audit cutoff:** 2026-11-22 22:50 UTC  
**Main HEAD before this report:** `67e30de1e88717f4cd7434e6891009817f396d99`  
**Disposition:** catalog-link correction only. No ZIP bytes were acquired; no file-level integrity, universe coverage, PIT clock, signal, or return test is admitted.

## 1. Actions and repository preflight

- Actions total: 8,069. Latest 100: 96 successes, 4 failures, zero active/queued runs.
- Latest overall run: Phase 560 PR check [45056358765](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45056358765), completed successfully at 18:39:52 UTC. Its `offline-regression` job passed 16 tests; it is not a live capture and has no artifact.
- Latest natural scheduled Form 144 capture remains [45052961790](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45052961790), created 18:04:20 UTC on main. Both `offline-regression` and `live-capture` succeeded. Artifact [14765739720](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45052961790/artifacts/14765739720) is present, 3,646 bytes, unexpired.
- The live log confirms the post-capture Phase 516 reconciliation passed at 285 filing headers / 2,114 detail rows, 278 accessions remaining in the bounded backfill queue, zero parse errors, zero source-hash mismatches, zero public-availability-certified filings, and zero signal-eligible rows. No new accession/event was found in that poll.
- The Phase 403 workflow on main still declares `47 * * * *`. No later `event=schedule` run appears in the latest 100 Actions runs. Slots 18:47, 19:47, 20:47, 21:47 and 22:47 UTC are absent after the 18:04 natural capture. This is an observed delivery/visibility gap, not proof the workflow is disabled. The API does not expose the administrative enabled-state.
- Repository inventory: 372 branches across four pages and 72 open PRs. PR #204 remains open/Draft; its branch is diverged from current main (11 commits ahead / 6 behind). No merge, dispatch, rerun, cancellation, or duplicate workflow was performed.

## 2. Newly identified 2012 Q1 per-security archive URL mismatch

The current SEC **Metrics by Individual Security** landing page lists 2012 Q1 as the oldest quarter in the 59-quarter sequence (2012 Q1–2026 Q3). Its 2012 Q1 download link resolves to:

`https://www.sec.gov/files/opa/data/market-structure/metrics-individual-security/individual_security_2012_q10.zip`

The SEC Data.gov catalog's 2012 Q1 distribution metadata independently repeats the same `individual_security_2012_q10.zip` URL.

However, the SEC's dedicated static-file landing page titled **Market Activity by Individual Security, 2012 Q1** links to the correctly named file:

`https://www.sec.gov/files/individual_security_2012_q1.zip`

The exchange-partitioned 2012 Q1 link is separately named `individual_security_exchange_2012_q1.zip`, with no analogous q10 suffix in the inspected landing-page href.

**Interpretation:** this is a catalog URL/filename mismatch for the oldest per-security archive, not evidence that the quarter is absent. The dedicated SEC static-file page provides a canonical alternate link. It is not yet established whether the q10 path redirects, returns an error, or aliases the same bytes: the web retrieval client rejects ZIP/octet-stream content and the container download attempt did not obtain bytes. Do not describe the q10 URL as a confirmed HTTP 404 or claim the ZIP itself was validated.

Official references:
- SEC per-security quarterly index: https://www.sec.gov/data-research/sec-markets-data/marketstructuredata-security
- SEC static-file landing page: https://www.sec.gov/file/individualsecurity2012q1updated
- SEC Data.gov catalog: https://catalog.data.gov/dataset/metrics-by-individual-security
- SEC exchange-partitioned index: https://www.sec.gov/data-research/sec-markets-data/market-structure-data-security-exchange

## 3. PIT clock remains unresolved

- The SEC Data Library exposes a general SEC and Markets Data RSS endpoint at `https://www.sec.gov/rss/data`. The current retrieval interface rejects its `application/rss+xml` response, so no historical MIDAS item timestamps were extracted.
- The SEC landing page's `Last Reviewed or Updated: Sept. 30, 2026`, Data.gov's generic `modified` field, the quarter label, and the daily observation `Date` do not establish the first-public timestamp of a quarterly ZIP.
- The earlier Phase 42B 2/3/4-month lag sensitivity remains a conservative research sensitivity only, not proof of historical PIT. No lag was selected to improve returns.
- Archive.org CDX lookup was not accessible through the current research interface. No archive snapshot or first-capture date is claimed.

## 4. Data feasibility and next gate

1. In a network-enabled, SEC-compliant environment, request both the catalog q10 URL and the dedicated static-page q1 URL with a descriptive SEC User-Agent; record status, redirect chain, final URL, bytes, SHA-256 and response time. Do not infer equivalence without matching hashes.
2. Inspect the ZIP README, CSV schema, row counts, date continuity, duplicate keys and security-name/ticker semantics. Preserve raw bytes and hash outside the public repo if required by the repository's data policy.
3. Reconcile exact coverage against the effective-dated F80 universe and inactive/acquired/renamed securities. Ticker-only joins remain prohibited.
4. Continue seeking per-quarter first-public release evidence. The RSS endpoint is a lead, not a verified clock. If no timestamp can be recovered, keep 2/3/4-month lag sensitivities clearly labeled as non-strict-PIT and do not use them for promotion.
5. Preserve Phase 534 semantic regimes (2014, 2017-05-01, 2025-11-03) and the correction that HiddenVol is on-exchange hidden-resting-order activity, not dark-pool/off-exchange institutional flow.

## 5. Controls

- MIDAS remains a conditional public market-structure/liquidity candidate, not an investor-identity feed.
- New signals admitted: **0**.
- File payloads validated: **0**.
- New event/return/backtest/OOS/bootstrap/LOO/holdout tests: **0**.
- No changes to universe, exposure, costs, holding-period policy, parameters, holdout or production.
- `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen.
