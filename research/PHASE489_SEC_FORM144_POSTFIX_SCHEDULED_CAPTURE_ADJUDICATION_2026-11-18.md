# Phase 489 — SEC Form 144 post-fix scheduled capture and semantic adjudication

**Audit cutoff:** 2026-11-18 21:51 UTC  
**Disposition:** **POST-FIX SCHEDULED CAPTURE SUCCEEDED; 51 BOUNDED METADATA OBSERVATIONS; ZERO SIGNAL-ELIGIBLE EVENTS.**

## 1. Preflight and repository review

- Reviewed the most recent main commits, current research state, SEC first-seen ledgers, open PRs/issues, and all 316 branches (four pages: 100 + 100 + 100 + 16).
- Latest main commit before this audit was the scheduled capture commit [435285a1b60f18d032d861bb2396f4b7c9218ef9](https://github.com/jafelix81/NuevaEstrategia/commit/435285a1b60f18d032d861bb2396f4b7c9218ef9).
- No workflow was dispatched, rerun, cancelled, or duplicated.
- The connector exposed per-run jobs/logs/artifacts but not a repository-wide Actions-run listing endpoint; this report therefore makes no new total-run or active-run census claim.

## 2. Scheduled Phase 403 run

Run [44396134680](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44396134680) completed successfully on `main`.

Both jobs succeeded:

- `offline-regression`: **40 tests passed**.
- `live-capture`: migration, real SEC Atom polling, append-only ledger commit, and artifact upload all succeeded.

Poll window: **2026-11-18 20:56:07–20:56:30 UTC**.

### Feed reconciliation

| Feed | Raw Atom entries | Pages | Previous watermark found | New unique accession contribution |
|---|---:|---:|---|---:|
| Form 144 | 200 | 2 | Yes, page 2 | 50 |
| Form 144/A | 12 | 1 | Yes | 1 |
| **Combined** | **212** | **3** | **Both complete** | **51 unique events** |

There were 52 new feed entries and one cross-feed overlap. The overlapping accession `0001104659-26-129535` is retained once with provenance from both feeds. Pagination completed, no feed failed, and no possible feed-window gap was flagged.

The previous successful poll-start lower bound for both feeds was **2026-11-18 03:09:51 UTC**. All 51 new event feed timestamps fell after that lower bound; the earliest was 12:00:07 UTC and the latest 20:39:56 UTC. Their local first-seen receipt upper bounds were 20:56:09–20:56:13 UTC.

## 3. Append-only event and acceptance reconciliation

The canonical event ledger now contains 247 rows (excluding the header); the current poll added **51**:

- 50 Form 144 accessions.
- 1 Form 144/A accession.
- 51/51 submission XML blocks resolved.
- 51/51 acceptance reconciliations added to the separate `acceptance_reconciliation.csv` table.
- 0 unresolved acceptance reconciliations.
- 0 timing anomalies.
- In all 51 rows, SEC filing-detail acceptance time equals the Atom `updated` timestamp.
- Acceptance-to-first-seen-upper-bound lag: **973 seconds minimum, 16,407 seconds median, 32,166 seconds maximum**.

The separate acceptance table is authoritative for acceptance enrichment; the original event ledger's acceptance columns are intentionally not rewritten. Acceptance time is not treated as exact public first receipt. The local poll receipt is only a conservative upper bound.

## 4. Identity and universe gate

- Candidate issuer matches: **6/51** against a 290-CIK candidate manifest.
- The manifest is explicitly **not** an effective-dated historical F80 security master.
- Historical F80 membership verified: **0/51**.
- Security/issuer identity, beneficial-owner attribution and historical universe eligibility remain unpassed for the research use case.

Do not interpret the six candidate-manifest matches as six confirmed historical F80 constituents.

## 5. Form 144 semantics: proposed sale, not an execution record

The SEC labels Form 144 **“Notice of Proposed Sale of Securities.”** Investor.gov states that an affiliate filing is a notice of a proposed Rule 144 sale and requires a bona fide intention to sell within a reasonable time. Rule 144(h)(3) says the notice is transmitted concurrently with placing an order with a broker or executing directly with a market maker; the filing still does not prove the order filled or quantify the completed execution.

Primary references:
- [SEC Form 144](https://www.sec.gov/about/forms/form144.pdf)
- [Investor.gov — Form 144](https://www.investor.gov/introduction-investing/investing-basics/glossary/form-144)
- [17 CFR 230.144(h)](https://www.govinfo.gov/content/pkg/CFR-2025-title17-vol3/pdf/CFR-2025-title17-vol3-sec230-144.pdf)

Descriptive keyword checks on the 51 newly resolved remarks found:
- 18 with non-empty remarks;
- 2 mentioning a Rule 10b5-1 arrangement;
- 11 mentioning tax, withholding, RSUs or vesting;
- 1 mentioning that a notice superseded an erroneous filing;
- 1 describing historical open-market acquisitions.

These keyword buckets overlap and are not a full semantic classification. They do, however, reinforce why a Form 144 event must not be treated as a completed insider sale or an automatically bearish signal.

## 6. Eligibility disposition

The run summary reports:

- 51 bounded metadata/research-observation rows;
- 51 XML-resolved events;
- 0 public-availability-certified events;
- 0 signal-eligible events;
- same-day intraday use not authorized;
- no forward returns, bootstrap, LOO, holdout, or alpha test.

“Research-observation eligible” here means the accession has a bounded poll interval and resolved filing metadata. It does **not** mean verified F80 membership, completed sale, exact public-release time, or investment-signal eligibility.

The current state records 11 complete polls, 0 partial polls, and the latest successful scheduled poll at 20:56:30 UTC.

## 7. Artifact and persistence

- Artifact [14470455938](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44396134680/artifacts/14470455938), `phase403-sec-form144-first-seen`.
- ZIP size: 2,084 bytes.
- Verified ZIP SHA-256: `a6d47ef938306f3efa4fcff412c3a737995611030b00a3afe498e5e9ee525d07`.
- Contains `summary.json` and `schema_migration.json`; no raw filing documents or market data.
- Scheduled capture commit: [435285a1b60f18d032d861bb2396f4b7c9218ef9](https://github.com/jafelix81/NuevaEstrategia/commit/435285a1b60f18d032d861bb2396f4b7c9218ef9).

## 8. Operational disposition and next gates

- Close Issue [#136](https://github.com/jafelix81/NuevaEstrategia/issues/136): a post-fix scheduled Phase 403 run has now completed both offline regression and live capture. Continue observing subsequent scheduled runs; do not alter cron or manually dispatch.
- Phase 476 Form 4/4-A remains at its initial baseline in the persisted state: 35 unique accessions, no bounded metadata rows yet. A subsequent successful poll that reconciles the previous feed watermarks is still required.
- Issue [#132](https://github.com/jafelix81/NuevaEstrategia/issues/132) remains a human licensing question for the public Cboe Open-Close sample artifact. No deletion action is available through the connected GitHub tools; no new sample was downloaded.
- SEC 13D/G remains quarantined under the issuer-versus-filer identity findings. Reuse the existing PR #37 / Phase 350 retrieval chain after the monitored SEC contact secret prerequisite; do not create another crawler.
- FINRA Phase 20B/20C remain rejected for promotion under Phase 487; Phase 20A remains exploratory. CFTC TFF still lacks the preregistered 52-week prospective warm-up. Options sources remain conditional on licensed historical coverage, stable identifiers and PIT delivery.

## 9. Frozen strategy controls

No backtest, forward-return study, OOS, bootstrap, LOO or holdout test was run.

`F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen. No universe, parameters, holding period, capital, exposure, costs, holdout, production or signal-eligibility changes were made.

**Conclusion:** Phase 403's scheduled delivery has recovered and produced its first post-fix complete bounded capture. The data are useful for building a prospectively timed Form 144 metadata panel, but they are not completed-sale records and none of the 51 events is currently eligible as a F80 signal.
