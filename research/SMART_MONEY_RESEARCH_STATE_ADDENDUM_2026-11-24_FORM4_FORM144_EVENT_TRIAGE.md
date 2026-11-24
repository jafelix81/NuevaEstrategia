# Smart Money Research State Addendum — 2026-11-24

**Audit cutoff:** 2026-11-24 04:37 UTC  
**Base:** main at 892b4e28fa4108cb24ef0811eed9e2f3138a9ea5 (Phase 586)  
**Purpose:** record a source-level transaction triage and the latest SEC collector delivery gap. This is a research-state addendum, not a new model phase.

## 1. Actions and collector preflight

- Repository inventory: **8,104** Actions runs; latest 100 = **90 success / 10 failure**; **0 active / 0 queued**; **378 branches**, **72 open PRs**, **96 workflow files**, **495 research files**.
- Latest runs overall were Phase 584 PR checks [45268079558](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45268079558) and [45267800386](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45267800386). Each offline-regression job succeeded; each live-capture job was skipped. These are not live SEC validation.
- Latest natural Form 4 run remains [45257913619](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45257913619), started 2026-11-23 20:17:54 UTC. Latest natural Form 144 run remains [45261140072](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45261140072), started 2026-11-23 20:36:36 UTC.
- No later scheduled run is present at this cutoff. The main workflow files still declare Form 4 17 * * * 1-5 and Form 144 47 * * * *.
  - Form 4 expected slots absent: Nov 23 21:17, 22:17, 23:17 UTC; Nov 24 00:17, 01:17, 02:17, 03:17, 04:17 UTC (**8 slots**).
  - Form 144 expected slots absent: Nov 23 21:47, 22:47, 23:47 UTC; Nov 24 00:47, 01:47, 02:47, 03:47 UTC (**7 slots**).
- The read-only Actions inventory cannot establish whether either workflow is administratively disabled/paused or whether repository schedule policy is blocking delivery. This is an observed delivery gap, not proof of the cause. Human verification remains necessary in GitHub Actions/repository settings. No manual dispatch, rerun, cron change, or duplicate poll was made.

### Artifact and log verification

- Form 4 artifact [14859736409](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45257913619/artifacts/14859736409) and job logs confirm the pre-fix natural poll:
  - Form 4 queried 20 pages / 2,000 entries and did not find prior watermark 0001493152-26-053593.
  - 408 unique candidate accessions / 938 candidate observations remained suppressed.
  - Form 4/A passed its watermark gate.
  - The Phase 583/584 50-page repair still has **no natural post-merge live validation**.
- Form 144 artifact [14860761702](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45261140072/artifacts/14860761702) confirms 34 new filings, 34 XML resolutions, 7 candidate issuer matches, 349 structured accessions, 2,486 detail rows, 248 bounded backfill accessions remaining, and **0 signal-eligible rows**. The post-capture Phase 565 artifact [14860501976](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45261140072/artifacts/14860501976) also reconciles the Form 144 ledger and preserves signal admission as false.

## 2. Form 4 purchase-code census and issuer clusters

The current structured Form 4 transaction ledger contains **34** non-derivative P/A transaction rows across **26 accessions** and **21 normalized symbol labels** (one is N/A). Repeated transaction rows within one accession are not independent insider events. SEC Form 4 Instruction 8 defines code P as an **open-market or private purchase**; code P alone does not establish venue ([official Form 4 instructions](https://www.sec.gov/files/form4.pdf), pp. 11–12).

### UPST — within the static 335-ticker snapshot; discovery only

- Two purchase accessions, two reporting persons, aggregate reported notional approximately **$1,811,053**: Paul Gu (CEO/director) and Dave Girouard (director / 10% owner), each reported through a trust structure.
- The Rule 10b5-1 checkbox is not selected in the filings. This is not proof of open-market execution; code P still permits a private purchase.
- Both purchase accessions remain absent from the current reporting_owners.csv sidecar. The rows remain filing-grain only; public-availability, transaction-line attribution, security-identity, and historical F80-membership gates remain false. The static 335-ticker snapshot is not itself a point-in-time security master.
- No forward-return study or signal test was performed. Keep this as a discovery-only issuer event.

### PICS — three-director cluster, outside the frozen universe

Three distinct director Form 4s report purchases in PicS N.V. (PICS), with transaction dates Nov 18–19 and filing date Nov 20, 2026:

| Reporting person | Reported transaction | Ownership |
|---|---:|---|
| Marcio Antonio Teixeira Linares | 60,000 shares at $4.99 | Indirect, through Bravar Developments Ltda. |
| William Rodney Pruett | 50,000 shares at weighted-average $4.65 (footnote range $4.61–$4.69) | Direct; reported post-transaction holding 175,000 |
| Mauricio Costa de Moura | 4,962 shares at $4.99 | Direct |

- Aggregate: **114,962 shares / $556,660.38** across three accessions and three directors.
- The three filings leave the Rule 10b5-1 checkbox unselected. All use transaction code P; execution venue is not established by the code. The filings also state that the issuer's foreign-private-issuer status makes the reported transactions exempt from Sections 16(b) and 16(c).
- The ledger's first-seen interval is **2026-11-20 10:07:15–18:38:50 UTC**. The conservative first-seen upper bound, not the acceptance timestamp, controls availability; same-day intraday use is not authorized.
- **PICS is not in the static 335-ticker snapshot.** The ledger also has public_availability_certified=false, security_identity_verified=false, and historical_f80_membership_verified=false for these rows. Keep this as an out-of-universe discovery example; do not add it to F80 or use it to justify a universe change.

Primary SEC filings: [Teixeira Linares](https://www.sec.gov/Archives/edgar/data/2121101/000121390026122444/0001213900-26-122444-index.htm), [Pruett](https://www.sec.gov/Archives/edgar/data/2111657/000121390026122460/0001213900-26-122460-index.htm), and [Costa de Moura](https://www.sec.gov/Archives/edgar/data/2121107/000121390026122452/0001213900-26-122452-index.htm).

## 3. Form 144 mechanical-sale negative control: Fermi Inc. (FRMI)

The latest Form 144 post-capture audit identifies four same-issuer notices, all dated Nov 19, 2026:

| Seller | Relationship | Proposed shares |
|---|---|---:|
| Charles Lynn Hamilton | Officer | 761,629 |
| Jacobo Ortiz Blanes | Officer | 847,810 |
| Lee A. McIntire | Director and officer | 20,544 |
| George R. Wentz, Jr. | Officer | 623,287 |
| **Total** | **4 accessions** | **2,253,270** |

- Aggregate market value reported across the notices: **$5,299,116.73**; each notice reports 646,953,440 shares outstanding, so the proposed shares equal approximately **0.3483%** of that reported share count.
- The filings state that the shares were issued on Nov 18 upon settlement of RSUs and that the proposed sales are automatic **sell-to-cover** transactions to satisfy tax-withholding obligations. Each states that the sale is **not** being made pursuant to a Rule 10b5-1 plan.
- These are Form 144 **notices of proposed sales**, not confirmation that the sales executed. They must not be treated as four discretionary bearish insider-sale signals.
- The Phase 549 classifier's NEGATIVE_EXPLICIT label refers to explicit **non-reliance on a Rule 10b5-1 plan**. Its has_sell_to_cover_tax_context test is separately true. Therefore the summary field negative_sell_to_cover_cases means “explicitly not 10b5-1 **and** sell-to-cover/tax context”; it does **not** mean that sell-to-cover was absent. This cluster is a useful mechanical/compensation negative control. A clearer alias for that field may be added later, preserving compatibility.

SEC primary documents: [Hamilton](https://www.sec.gov/Archives/edgar/data/2071778/000121390026122355/0001213900-26-122355-index.htm), [Ortiz Blanes](https://www.sec.gov/Archives/edgar/data/2071778/000121390026122358/0001213900-26-122358-index.htm), [McIntire](https://www.sec.gov/Archives/edgar/data/1343745/000121390026122359/0001213900-26-122359-index.htm), and [Wentz accession 0001213900-26-122362](https://www.sec.gov/Archives/edgar/data/2071778/000121390026122362/0001213900-26-122362-index.htm). The Wentz filing details are also summarized at [DisclosureBoard](https://disclosureboard.com/planned-sales/0001213900-26-122362/).

## 4. Research disposition

- No Form 4 or Form 144 event from this audit is promoted to a signal.
- No forward-return study, alpha test, bootstrap, leave-one-out, or OOS test was run; this is a source/semantics audit, not performance evidence.
- No universe, exposure, costs, holding period, parameters, or production settings changed.
- F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen.
- Next gates: verify scheduled-workflow delivery; obtain a natural post-merge Form 4 run that demonstrates the 50-page watermark recovery; continue owner-sidecar backfill for the two UPST purchase accessions; retain the Fermi notices as a mechanical negative control; keep PICS outside F80 absent a separately approved broader-universe research design.
