# Phase 587 — Form 144 candidate-match cluster triage and source-gate refresh

**Audit cutoff:** 2026-11-24 05:03 UTC  
**Base:** `main` at `44ff95f13879a343bffcf483512488000c583c4b` (natural Phase 403 capture commit)  
**Disposition:** descriptive Form 144 cluster triage only. Mechanical/plan-related contexts are useful negative controls; unknown remarks remain unknown. No signal, event study, return test, OOS, bootstrap, LOO or production change.

## 1. Repository and Actions preflight

- Actions inventory: **8,105** total runs; latest 100 = **90 success / 10 failure**; **0 active / 0 queued** at the post-capture recheck.
- Branches: **378** (100 + 100 + 100 + 78); open PRs: **72**; workflow files: **96**; research files: **496**.
- Latest scheduled Form 144 run: [45330252226](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45330252226), Phase 403 run 89, event=schedule. Both offline regression and live capture completed successfully.
- Latest natural Form 4 remains [45257913619](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45257913619), before the Phase 583/584 merge. The next weekday cron slot after this audit cutoff is 2026-11-24 05:17 UTC. No manual dispatch, rerun, duplicate poll, cancellation or cron change was made.

## 2. Natural Form 144 capture — successful recovery

Run 45330252226 used main commit `62a3944a58f442606d7b6d6fc7117014f8ca45ad` at dispatch and persisted the collector data as commit `44ff95f`.

- Form 144 and 144/A both found their prior watermarks; both feeds completed without feed errors or possible-window-gap flags.
- 118 new accession events were written and 118 XML payloads were resolved.
- 153 feed-observation rows were appended across the two feeds; one accession had cross-feed overlap.
- Acceptance reconciliation: 118 attempts, 113 added, 5 unresolved. Acceptance time is not exact public availability.
- The Form 144 feed used 3 Atom pages / 300 raw entries; 144/A used 1 page / 6 raw entries.
- The first-seen interval upper bound is poll receipt, not the SEC's exact public-release time. Median interval from the prior successful poll start to receipt was approximately 8.40 hours in this run.
- Structured ledger after the run: **477 accessions / 3,360 detail rows**; 10 bounded older accessions were parsed; **238** remain in the bounded detail-backfill queue. New structured details appended: 801; no parse or source-hash mismatch.
- Post-capture Phase 516 and Phase 565 reconciliations passed. Artifacts [14891955642](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45330252226/artifacts/14891955642), [14891416912](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45330252226/artifacts/14891416912), and [14890729923](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45330252226/artifacts/14890729923) were present and unexpired at audit time.

This confirms a successful natural Form 144 poll after the previously observed delivery gap. It does **not** validate the separate Form 4 50-page catch-up repair.

## 3. Candidate-manifest match triage

The 118 new Form 144 accession events include **22** records with `candidate_issuer_match=true`, grouped into **13 issuer CIKs**. The candidate manifest has 290 CIKs and is not an effective-dated security master or historical F80 membership file. These matches must not be described as verified historical F80 constituents.

Accession-level groups and remarks:

| Issuer | Notices | Observed context | Triage |
|---|---:|---|---|
| Rocket Lab Corp | 5 | All five remarks explicitly describe sale amounts needed for tax obligations from vested equity awards | Explicit sell-to-cover / compensation negative-control cluster |
| Amazon.com | 3 | Remarks say securities were acquired upon RSU vesting; they do not, by themselves, establish that the proposed sales are automatic tax sell-to-cover | Vesting-origin context; sale motive not inferred |
| Visa Inc. | 2 | No explanatory remarks in the captured event rows | Unknown; not presumed discretionary |
| Home Depot, Inc. | 2 | No explanatory remarks in the captured event rows | Unknown; not presumed discretionary |
| eBay Inc. | 2 | Remarks identify a selling plan intended to comply with Rule 10b5-1(c), dated 2026-08-20 | Planned-sale negative control |
| Arista Networks, Inc. | 1 | Shares to be sold for a family trust | Trust/ownership context; motive and execution unknown |
| Walmart Inc. | 1 | No explanatory remarks in the captured event row | Unknown |
| Lumentum Holdings Inc. | 1 | No explanatory remarks in the captured event row | Unknown |
| Zimmer Biomet Holdings, Inc. | 1 | No explanatory remarks in the captured event row | Unknown |
| Datadog, Inc. | 1 | Remarks describe RSU/PSU vesting and previously vested option exercises | Compensation/acquisition-origin context; sale motive not inferred |
| Qualcomm Incorporated | 1 | Seller is a family trust; no explanatory remarks in the captured event row | Trust/ownership context; motive and execution unknown |
| Trump Media & Technology Group Corp. | 1 | Remarks state disposition solely covers issuer tax obligations from vested RSUs and no cash proceeds were received by filer | Explicit tax-only / sell-to-cover negative control |
| Meta Platforms, Inc. | 1 | Remarks state sale pursuant to a Rule 10b5-1 trading plan | Planned-sale negative control |

Classification totals (accession-level, not independent return observations):
- **6** explicit sell-to-cover / tax-obligation notices (5 Rocket Lab, 1 Trump Media).
- **3** explicit Rule 10b5-1 planned-sale notices (2 eBay, 1 Meta).
- **4** additional vesting/acquisition-origin notices (3 Amazon, 1 Datadog) whose remarks do not establish automatic sell-to-cover.
- **2** trust/ownership-wrapper cases (Arista, Qualcomm) without a verified sale motive.
- **7** notices with no explanatory remarks in the captured event rows (Visa 2, Home Depot 2, Walmart 1, Lumentum 1, Zimmer Biomet 1).

The nine explicit tax/plan notices are not evidence of discretionary bearish intent. The four vesting/acquisition-origin notices are not automatically mechanical sales; preserve the narrower classification. The remaining unknown cases must remain unknown rather than being promoted to discretionary selling by default.

Every Form 144 filing is a **notice of proposed sale**, not proof that the proposed sale executed. A filing-level cluster is one issuer/event cluster for future research, not a set of independent observations. The five Rocket Lab notices are one same-issuer cluster; the two eBay notices share a disclosed plan date.

## 4. Broader ledger-level 10b5-1 and negative-control context

The post-capture Phase 549 audit covers 477 Form 144 accessions and 3,360 detail rows:

- 174 accessions (36.48%) contain a formal plan-adoption date; those 174 entries represent 89 distinct dates.
- Median lag from formal plan date to notice: **183 days** (range 18–546; n=174).
- Remarks polarity: 15 positive explicit mentions, 4 negative explicit mentions, 1 ambiguous mention, and 457 with no mention.
- Four Fermi Inc. notices are explicit non-10b5-1 sell-to-cover/tax-withholding notices, totaling 2,253,270 proposed shares. This is a mechanical negative-control cluster, not a discretionary bearish signal.
- The audit reports 16 accessions with sell-to-cover/tax-withholding context overall. A formal plan date, a remarks mention, and a checkbox are distinct fields; do not collapse them into one binary label.

Controls remain:
- `public_availability_certified=false`;
- `historical_f80_membership_verified=false`;
- `signal_eligible=false` for all captured Form 144 events;
- same-day intraday use is not authorized;
- no forward returns or event study were calculated.

## 5. Source-gate refresh and next priorities

1. **SEC Form 4:** await the first natural post-Phase-584 scheduled capture. It must demonstrate that the 50-page bounded poll finds the prior watermark; if not, keep candidates suppressed and investigate further. Then continue bounded owner-sidecar enrichment for UPST and other filing clusters without manually promoting eligibility.
2. **SEC Schedule 13D/G:** retain as the highest-priority public ownership-disclosure hypothesis. Historical accessions can be discovered from EDGAR submissions/indexes, but subject-company identity must be parsed separately from filer CIK, and filing acceptance/index dates are not exact public availability. The historical panel remains quarantined until the repository's `SEC_USER_AGENT` secret is configured and a bounded sample passes subject-identity, version, coverage and PIT checks. Do not launch the full legacy rebuild first.
3. **Cboe options / volatility surfaces:** retain as a potentially useful independent flow/risk-state source, not a participant-identity feed. Advertised history (Option Trades/Quotes from 2012; Volatility Surfaces from 2011) is not proof of exact 335-name/date coverage or historical first-delivery vintages. The published standard DataShop license reviewed in Phase 527 restricts use for creating investment strategies/indicators absent a separate written and executed agreement. Do not acquire a sample or order data for strategy research until written authorization, supplier permissions, coverage and price are resolved.
4. **FINRA Short Interest / Reg SHO / ATS:** require authorized credentials/terms, exact release/receipt clocks, valid file/schema coverage and symbol-level identity. Do not treat short-sale volume as short interest or ATS aggregate volume as investor identity.
5. **CFTC TFF:** keep accumulating natural prospective vintages only. The two currently captured prospective observations are insufficient for predictive testing; do not backfill feature history from the historical archive.
6. **SEC MIDAS:** conditional market-structure/liquidity context, not a smart-money identity feed. Archive-link bytes, file integrity, exact coverage and historical first-public timestamps remain unverified.

## 6. Research disposition

The new Form 144 sample is useful for source quality, event classification and negative-control design. It does not establish a predictive selling signal. In particular, a cluster of notices is not a cluster of executed sales, and absence of remarks is not proof of discretionary intent.

Before any event-return test:
- resolve exact first-seen upper bounds and use the next full regular session, never the transaction/acquisition date or acceptance time;
- establish effective-dated CIK/security-class/ticker identity and historical F80 membership;
- join Form 144 notices to Form 4 transactions and later execution/plan evidence where available;
- deduplicate by issuer/event/plan and reporting person;
- predefine exclusions for tax withholding, vesting, 10b5-1 plans, gifts, transfers, exercises and trust structures;
- compare any surviving feature against frozen LTM/F80 with identical exposure and costs, chronological OOS, issuer/event-cluster bootstrap, LOO and multiplicity controls.

**Signals admitted: 0. Alpha demonstrated: 0. OOS tests: 0.**  
`F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen. No universe, parameter, exposure, cost, holdout, holding-period or production change.
