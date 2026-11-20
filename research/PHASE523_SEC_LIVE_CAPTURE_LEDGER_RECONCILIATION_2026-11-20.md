# Phase 523 — SEC live-capture and structured-ledger reconciliation

**Audit time:** 2026-11-20 10:38 UTC  
**Base main:** `d513c94e92edf955d0ee0c242d3f43f9949f3048`  
**Disposition:** both SEC scheduled collectors are operating and append-only detail backfills are progressing. Form 144 exposes a useful structured Rule 10b5-1 adoption-date field and four proposed-sale-date/notice-date anomalies; three require source-document review. None of this authorizes a return signal.

## 1. Preflight

- Actions inventory: 7,959 total runs; latest 100 returned; 0 in progress and 0 queued/requested.
- Branch inventory: 346 branches across four API pages; 61 open PRs.
- Main was at `d513c94e92edf955d0ee0c242d3f43f9949f3048` after the latest scheduled Form 144 persistence commit. No active workflow was duplicated.
- SEC Form 144 run [44720422923](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44720422923): offline regression and live capture succeeded; artifact [14621821685](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44720422923/artifacts/14621821685).
- SEC Form 4 run [44716430351](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44716430351): offline regression and live capture succeeded; artifact [14619333577](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44716430351/artifacts/14619333577).
- FINRA Reg SHO run [44669121290](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44669121290) predates the Phase 515 parser merge: 8 HTTP-200 files, 8 invalid, 0 valid. The existing schedule is 22:30/23:30 UTC weekdays; post-merge live validation remains pending that schedule.
- CFTC run [44668300202](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44668300202): no new reports or revisions; 3,039 rows retained, 0 signal-eligible historical rows.
- FINRA T1 Phase 518 run [44701029373](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44701029373) succeeded with 259 consecutive weeks and reconciled both overlap samples. Its preregistered sample gate still fails: 19 strict 52/52-valid observations; 5/10/20-session evaluation counts 137/136/132 versus 150 required. The 48/52 sensitivity is exploratory only.

## 2. SEC Form 4 — new metadata and detail backfill

### First-seen metadata

The current event ledger contains 1,268 unique accession rows. Scheduled run 44716430351 found 33 new unique Form 4 accessions. The poll found its prior watermark and produced bounded metadata intervals; the collector still records first-seen poll receipt as an upper bound, not exact public availability.

- New metadata accessions: 33.
- New event rows: 33.
- Research-observation eligible: 0.
- Signal eligible: 0.
- Public availability certified: false.
- No filing XML or transaction rows are stored by the first-seen metadata collector.

### Structured-detail ledger

The cumulative detail ledger contains 20 accessions and 59 rows: 20 filing headers and 39 transaction rows. The latest run backfilled 10 accessions and appended 37 rows (10 headers + 27 transactions), with zero parser errors. Twenty-three of the 33 newly observed accessions remain unparsed; the bounded backfill queue reports 1,213 accessions remaining.

Latest 10-accession batch transaction codes: P=7, M=4, S=12, A=4. Two rows/accessions in the batch are quarantined for multi-owner line attribution; 35 rows retain filing-grain single-owner status.

Cumulative 39 transaction-row codes: P=10, M=6, F=1, A=9, S=13; acquired/disposed codes A=22 and D=17; nine rows have zero price. These are SEC transaction codes, not a ready-made directional signal. In particular, code M, F, A or S must not be reinterpreted as open-market buying/selling without transaction and footnote semantics.

All 59 structured rows remain:
- research-observation ineligible;
- signal ineligible;
- public-availability uncertified;
- security identity and historical F80 membership unverified;
- owner attribution and transaction semantics unverified.

All 59 XML hashes are marked non-comparable because the original first-seen event ledger did not retain XML hashes. This is a provenance limitation, not a hash mismatch.

## 3. SEC Form 144 — 90-accession structured ledger

### Latest scheduled poll and backfill

Run 44720422923 completed both feeds, found both prior accession watermarks, paginated successfully and reported no possible feed-window gap.

- New Form 144 / 144-A accessions: 0.
- Feed-observation rows appended: 52.
- Structured backfill: 10 accessions, 64 detail rows, zero parse errors.
- Remaining structured-detail accessions: 358.
- Cumulative event ledger: 448 accession rows.
- Cumulative structured ledger: 90 accessions / 660 rows.

The 660 rows comprise 90 filing headers, 90 securities-information rows, 192 securities-to-be-sold rows and 288 securities-sold-in-the-past-three-months rows. All 660 parse successfully and all 660 source XML hashes match the corresponding event-ledger hash.

The detail rows inherit `research_observation_eligible=true` from their bounded parent poll interval. This is a data-observation flag only: `public_availability_certified=false`, `signal_eligible=false` and same-day intraday use remains unauthorized. The latest poll itself had zero new accessions, hence zero newly eligible feed events.

### Rule 10b5-1 adoption-date field

Across 90 accessions:
- 34 have a formal plan-adoption date in the dedicated field.
- 6 mention Rule 10b5-1 in Remarks.
- 32 are formal-date-only, 4 are Remarks-only and 2 have both.
- The 34 formal dates precede the notice by a median 181 days (range 72–528 days).
- Seven of the latest 10 backfilled accessions have a formal adoption date.

The dedicated field is materially more informative for plan classification than a Remarks-only text search. It does not establish that a plan remained active, unmodified or un-terminated at the notice date.

### Proposed-sale scale and date anomalies

All 90 securities-information rows have positive proposed units and units outstanding. Proposed units / units outstanding:
- median: 0.007474%;
- 75th percentile: 0.050978%;
- maximum: 0.386427%.

Approximate sale date equals notice date in 86 cases and precedes it in four; none is later.

1. **Verano Holdings Corp. — Form 144/A, accession 0001493152-26-053320:** this is explicitly an amendment. Remarks state that a plan adopted 2026-08-11 was terminated effective 2026-11-18 and that 15,100 shares had already been sold from Nov 11–17. Do not classify it as a new future-sale intention.
2. **Clean Energy Fuels Corp. — 0001974078-26-000422:** approximate sale date Nov 10 versus notice Nov 19; source-document review required.
3. **Eagle Bancorp Montana, Inc. — 0001972649-26-000002:** Nov 18 versus Nov 19; source-document review required.
4. **Griffon Corp. — 0001959173-26-008160:** Nov 16 versus Nov 19; source-document review required.

The latter three remain temporal/semantic anomalies, not proven completed sales. No return labels or features were created from them.

## 4. Source-level interpretation and decisions

- Continue both SEC scheduled collectors and bounded 10-accession backfills. Do not raise the per-run limit without a rate-limit and retry audit.
- Preserve Form 4 as non-signal until issuer/security-class identity, historical F80 membership, owner-line attribution, transaction/footnote semantics and conservative public-availability timing are verified.
- Preserve Form 144 plan adoption, amendment/termination status, proposed quantity and past-sale fields as distinct event attributes. A Form 144 is a notice of proposed sale, not proof of execution.
- Review the three unresolved Form 144 date anomalies against their original filings before any event classification.
- Wait for the existing FINRA Reg SHO 22:30/23:30 UTC scheduled slot to validate Phase 515 with real CNMS files; do not manually dispatch.
- Keep CFTC prospective-only. Its latest capture had no new report/revision.
- FINRA T1 aggregated HHI remains rejected for insufficient preregistered evaluation sample. Do not relax the sample gate or use the unpreregistered 48/52 sensitivity as a signal.

## 5. Strategy controls

No forward returns, event study, backtest, alpha test, OOS, bootstrap, LOO or holdout test was run. No new signal was admitted. `F80_TOP20_PARTIAL50_BASELINE_C20`, its universe, parameters, exposure, costs, holdout and production remain unchanged.

**Conclusion:** the SEC data pipelines are collecting and enriching real filings, but the remaining barriers are economic identity, attribution and point-in-time availability—not parser success. The Rule 10b5-1 field and the four date anomalies improve the research specification; they do not establish predictive edge.
