# Phase 585 — post-Phase-584 Form 4 live-validation and cross-source gate audit

**Audit cutoff:** 2026-11-23 23:51 UTC  
**Main HEAD:** `3289400257edb3b8a16efdc3b47a6537276c63ad`  
**Disposition:** operational and source-feasibility checkpoint. No economic test, signal, alpha or OOS result.

## 1. Repository and Actions preflight

- Actions API: **8,104 total runs**. Latest 100: **90 success / 10 failure**; zero active or queued runs.
- Branch inventory: **378** (100 + 100 + 100 + 78 across four pages).
- Open pull requests: **72**. Workflow files on main: **96**.
- Main's latest commit is Phase 584, `3289400`.
- No workflow was dispatched, rerun, cancelled, merged or duplicated during this audit.

### Relevant runs inspected

| Run | Event / phase | Jobs | Artifacts |
|---|---|---|---|
| [45268079558](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45268079558) | Phase 584 PR CI | offline regression success, **63/63**; live capture skipped | none |
| [45267800386](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45267800386) | Phase 583 PR CI | offline regression success, **63/63**; live capture skipped | none |
| [45261140072](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45261140072) | Form 144 scheduled capture | offline and live jobs succeeded | 14861750489, 14860761702, 14860501976 |
| [45257913619](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45257913619) | Form 4 scheduled capture, pre-Phase-583/584 | offline and live jobs succeeded under the old gate | 14859736409 |
| [45236295142](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45236295142) | Phase 580 PR regression | offline contract success, **25/25** | none |
| [45236294572](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45236294572) | Phase 580 PR regression | offline contract success, **25/25** | none |

All listed artifacts are unexpired at the audit cutoff.

## 2. Form 4: Phase 583/584 is merged but not live-validated

The canonical feed-observation ledger confirms the pre-fix natural run's precise failure mode:

- Form 4 feed `4`: 20 successful HTTP pages at offsets 0–1,900; 2,000 raw Atom entries and 938 parsed accession observations. There were no HTTP page errors, but the prior watermark `0001493152-26-053593` was not found inside the old 20-page cap.
- The 408 unique candidate accessions from that incomplete feed remained suppressed; the canonical Form 4 feed state did not advance.
- Form 4/A feed `4A`: one successful page, 33 raw entries / 33 parsed accessions; its watermark gate passed.
- Current `state.json`: Form 4 remains `GAP_OR_FETCH_ERROR`, with last successful poll at **2026-11-23 07:48:52 UTC**; Form 4/A last succeeded at **20:18:55 UTC**.
- The prior workflow's overall success conclusion obscured the incomplete Form 4 feed. This was corrected by Phase 583's explicit all-feed quality gate and Phase 584's `sec_capture` step binding.

PRs [#211](https://github.com/jafelix81/NuevaEstrategia/pull/211) and [#212](https://github.com/jafelix81/NuevaEstrategia/pull/212) are integrated in main. The collector now permits up to 50 pages / 5,000 raw entries, retains fail-closed watermark semantics, persists state and uploads artifacts before failing a scheduled poll whose feed remains incomplete.

**Live-validation status:** no natural Form 4 schedule run against the merged Phase 584 main commit appears in the Actions inventory through 23:51 UTC. The PR runs are offline-only; their live-capture jobs were skipped. The nominal next weekday cron slot is **2026-11-24 00:17 UTC / 2026-11-23 17:17 Hermosillo**, subject to GitHub schedule-delivery delay. Do not dispatch a duplicate poll. Issue [#210](https://github.com/jafelix81/NuevaEstrategia/issues/210) remains open until the live watermark recovery is demonstrated.

## 3. Form 144: latest natural capture remains complete

Run [45261140072](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45261140072) completed both jobs successfully. Current committed state records:

- Last poll: `complete`, both Form 144 and 144/A successful, no poll errors or possible feed gap.
- Structured detail ledger: **349 accessions / 2,486 rows**.
- Bounded detail backfill remaining: **248 accessions**.
- Signal eligibility remains explicitly disabled.
- Unexpired artifacts: [14860761702](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45261140072/artifacts/14860761702), [14861750489](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45261140072/artifacts/14861750489), and [14860501976](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45261140072/artifacts/14860501976).

The latest Form 144 state is a successful capture, not evidence of an insider-trading signal. Historical F80 membership and exact public availability remain uncertified.

## 4. Broad source-feasibility adjudication

| Source / hypothesis | Current evidence | Disposition |
|---|---|---|
| SEC Schedule 13D | Faster event disclosure than 13F; old 20,266-accession panel has subject/filer identity contamination. Phase 485 parser separates SUBJECT COMPANY from FILED BY, but full rebuild is blocked by authorized SEC User-Agent access. | **Highest-priority public ownership-event candidate, quarantined pending identity rebuild and PIT clock.** |
| SEC Form 4 / 4-A | Prospective metadata capture; structured detail and filing-level owner sidecars remain small relative to the feed. First-seen is an upper bound, not exact public availability. | Continue capture; zero signal-eligible observations. Rule 10b5-1-flagged sales are negative controls, not discretionary insider flow. |
| Cboe OPRA Option Trades + Quotes | Broad U.S. listed options history is advertised from 2012 (Cboe documents conflict on 2010 vs 2012); trade/NBBO, IV/Greeks and OCC SOD OI are potentially useful. No authorized sample, exact 335-name coverage or historical first-receipt/correction vintages. | Strongest conditional options data candidate, **blocked** by written investment-strategy-use authorization and third-party OPRA rights. |
| Cboe Open-Close EOD | Capacity × buy/sell × open/close fields, but Cboe-venue-only and with material historical OI/volume convention breaks. | Complement only; separate license and historical convention validation required. |
| SEC MIDAS | 59 quarterly catalog files, 2012 Q1–2026 Q3, daily security-level exchange metrics. Public hidden-volume measures are not dark-pool/off-exchange trades and do not identify participants; hidden-volume coverage is limited to 8/13 feeds. PIT release clock, actual ZIP integrity and exact F80 coverage remain unverified. | Retain only as a conditional slow exchange-liquidity/market-quality context source; kill the “hidden volume = institutional dark-pool accumulation” interpretation. |
| FINRA ATS weekly summary | 259 consecutive weeks, 2021-11-15 through 2026-10-26. Aggregate HHI time-series fails its predeclared sample-size gate; symbol-week panel still needs PIT identity, historical active-universe membership and survivorship-aware returns. 2014+ archive access previously returned HTTP 530. | Conditional panel only; no alpha test or signal. |
| FINRA Reg SHO daily short-sale volume | Measures daily short-sale transactions, not open short positions; post-Phase-539 live parser validation is still required. | Keep separate from Short Interest; no directional or participant-identity inference. |
| FINRA Consolidated Short Interest | Twice-monthly position snapshot, distinct from daily short-sale volume. Phase 447 is a one-settlement, manual-dispatch workflow requiring authorized credentials and permitted-use confirmation. | One-date validation only after credentials/terms are confirmed; no historical batch yet. |
| CFTC TFF | Only two prospectively received report vintages across four index contracts; historical archive update timestamps are not accepted as PIT clocks. | Prospective regime/crowding hypothesis only; sample is insufficient. |
| SEC 13F / N-PORT | 13F is quarterly with a 45-day disclosure lag and unresolved effective-dated share-class coverage. The standalone N-PORT reported-share-balance-growth ranking was killed after inconsistent signs and negative/non-monotonic IC in five of six completed transitions. | 13F parked; N-PORT share-growth hypothesis killed. Do not revive without a materially different preregistered hypothesis and stronger identity/return data. |

## 5. Stale branches and PRs — no blind merges

- `phase20c-finra-walkforward`: 12 commits ahead / **578 behind** main. Phase 20C's previous adjudication and the seven unresolved terminal/successor return cases remain controlling; no reactivation or merge.
- PR #200 (Cboe): 5 ahead / 80 behind.
- PR #201 (MIDAS): 2 ahead / 80 behind.
- PR #202 (Form 144 10b5-1): 17 ahead / 79 behind.
- PR #204 (SEC FTD credentials): 11 ahead / 60 behind.
- PR #199 (Form 4 negative control): 5 ahead / 80 behind.

These branches are diverged from current main. Their findings were reviewed, but no stale branch was merged. PR #204's monitored `SEC_USER_AGENT` prerequisite remains a human configuration item; do not put the contact email or secret in chat or commit it to the repository.

## 6. Next human/data gates

1. **SEC 13D/G and FTD:** configure the repository Actions secret `SEC_USER_AGENT` with a descriptive project identifier and monitored contact email; then perform only the bounded, authorized SEC retrievals and preserve aggregate-only artifacts.
2. **Options:** obtain written Cboe authorization expressly covering investment-strategy/model/indicator use and confirm OPRA third-party rights before any sample, subscription or test.
3. **FINRA Short Interest:** the next scheduled release is **2026-11-24** for the **2026-11-13** settlement. FINRA's Developer Center says Consolidated Short Interest is available by **4:40 PM ET** on publication day (**2:40 PM Hermosillo**). Phase 447 must use an authorized credential and confirmed permitted use; its workflow is configured for exactly one settlement date. No request was initiated. Official docs: https://developer.finra.org/docs and https://www.finra.org/filing-reporting/regulatory-filing-systems/short-interest
4. **Form 4:** wait for the next natural post-Phase-584 run; verify the prior watermark is found within 50 pages. If not, retain suppression and investigate feed retention/pagination; do not re-baseline.

## 7. Frozen controls

- Baseline: `F80_TOP20_PARTIAL50_BASELINE_C20` — **unchanged and frozen**.
- New Smart Money signals admitted: **0**.
- New return/event/alpha/OOS tests: **0**.
- Bootstrap / LOO: **0**.
- Universe, holding-period policy, parameters, costs, exposure, holdout and production: unchanged.

**Bottom line:** Phase 583/584 fixes are technically merged and pass offline regression, but the critical live Form 4 recovery is not yet demonstrated. The strongest next public ownership hypothesis is Schedule 13D, while the strongest options data candidate is Cboe OPRA; both remain blocked by concrete PIT/identity or license/access gates. No evidence justifies changing F80.
