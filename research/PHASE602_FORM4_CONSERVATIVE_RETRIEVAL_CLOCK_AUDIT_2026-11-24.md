# Phase 602 — SEC Form 4 conservative detail-retrieval knowledge-clock audit

**Audit cutoff:** 2026-11-24 20:35 UTC  
**Main HEAD at preflight:** `0cc4cbdc558c8b249181bd71dbb3d569816e29ee`  
**Disposition:** **retrieval-clock candidate gate passes for the current parsed Form 4 detail ledger; insider attribution and security/universe gates remain blocked.** This is a provenance audit, not a signal or return test.

## 1. Preflight and live-capture state

Reviewed the current main branch, latest Actions runs, relevant jobs/logs/artifacts, open PRs, branches, workflow files and research inventory before adding this audit.

- Actions runs: **8,112 total**. The latest 30 returned runs were completed; no active run appeared in that window.
- Main HEAD: `0cc4cbdc558c8b249181bd71dbb3d569816e29ee`.
- Open PRs include Phase 601 #217 (draft), Phase 559 #204, Form 4 overlap/owner work #199/#196, and the existing SEC FTD access gate #198. No Phase 602 branch or PR existed at preflight.
- No workflow was dispatched, rerun, cancelled, merged, rescheduled or duplicated before the offline audit was added.

Latest relevant completed runs, jobs and artifacts:

| Source | Run | Result |
|---|---:|---|
| SEC 13D/G Phase 601 | [45474927867](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45474927867) | adjudication job succeeded; 8/8 offline tests; artifact [14959051804](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45474927867/artifacts/14959051804) |
| SEC Form 4 Phase 476 | [45453400450](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45453400450) | offline and live jobs succeeded; artifact [14948444955](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45453400450/artifacts/14948444955) |
| SEC Form 144 Phase 403 | [45437675674](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45437675674) | offline and live jobs succeeded; artifacts [14941267954](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45437675674/artifacts/14941267954), [14941742508](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45437675674/artifacts/14941742508), [14942785496](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45437675674/artifacts/14942785496) |
| FINRA Reg SHO Phase 469 | [45339067236](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45339067236) | completed, but six daily files rejected by the fail-closed BCPC/TPC duplicate-symbol gate |
| CFTC TFF Phase 384 | [45338400329](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45338400329) | completed; 3,043-row archive unchanged, no new report/revision |

Phase 476's latest natural poll recorded 57 new accession events and 117 accession-observation rows, with both feed watermarks found. Its bounded structured-detail step parsed 10 accessions / 30 rows; owner enrichment added 11 rows. It admitted zero signal-eligible observations. Phase 403 captured 27 new Form 144 accessions, resolved all 27 XML documents, and reconciled 32 acceptance timestamps; it also admitted zero signals.

## 2. Form 4 ledger census

The committed main-branch ledgers were read directly by blob SHA, not inferred from the latest run summary.

| Measure | Current ledger |
|---|---:|
| First-seen event rows | 2,435 |
| Unique event accessions | 2,435 |
| Bounded metadata intervals | 2,400 |
| Initial baseline rows without a lower bound | 35 |
| Structured detail rows | 229 |
| Distinct structured-detail accessions | 80 |
| Filing-header detail rows | 80 |
| Transaction detail rows | 149 |
| Parsed detail rows | 229 |
| Existing `research_observation_eligible=true` detail rows | 0 |

The 2,400 bounded event intervals are not narrow: median interval 6.47 hours, 75th percentile 12.52 hours, 95th percentile 21.55 hours, and maximum 54.96 hours. The feed receipt is an upper bound, not an exact SEC public-release timestamp.

## 3. Phase 602 retrieval-clock result

The new offline audit joins each detail row to exactly one canonical scheduled first-seen event and applies fail-closed checks:

1. scheduled capture only;
2. bounded first-seen interval with explicit upper-bound semantics and consistent event/detail timestamps;
3. unique accession-to-event join and matching poll ID;
4. successful parse with no parse error;
5. valid SHA-256 hashes for both the complete submission and extracted XML;
6. SEC archive URL whose path contains the exact accession;
7. detail retrieval timestamp not earlier than the first-seen upper bound.

**Result on the current committed ledger:**

- **229/229 detail rows** pass the conservative retrieval-clock candidate gate.
- **80/80 accessions** pass.
- **149/149 transaction rows** pass.
- Rejection reasons: zero.
- Median delay from first-seen upper bound to detail retrieval: approximately **2 seconds**; 75th percentile approximately **5 seconds**. The 95th percentile is approximately **12.50 hours**, reflecting delayed backfill rows; maximum approximately **12.50 hours**.

The proposed conservative research-knowledge clock is therefore **`detail_retrieved_at_utc`**, not acceptance datetime and not transaction date. It is later than the feed receipt and is a reproducible upper bound on when the retrieved document was available to the collector. Any future event label must use the **first full XNYS session strictly after that retrieval timestamp**. Same-day/intraday use remains prohibited.

This does **not** certify the SEC's exact public-availability timestamp. It also does not create a source-XML hash captured in the original Atom event; the current Form 4 ledger has retrieval hashes but `source_hash_comparable=false` and raw XML is not persisted. Those limits remain explicit.

## 4. Why this matters — and what it does not unlock

The Form 4 capture layer currently hard-codes `research_observation_eligible=false` in both the metadata event and structured-detail builder. That was appropriately conservative while the feed poll contained metadata only. After a successful structured retrieval, however, the later retrieval timestamp supplies a stricter knowledge-time upper bound.

Phase 602 therefore introduces a **separate candidate classification** without rewriting the append-only ledger or changing the existing eligibility flags. It demonstrates that the current parsed details can be assigned a conservative retrieval clock. It does not promote those rows to insider-flow signals.

The remaining gates are still decisive:

- The owner sidecar has 72 rows across 60 accessions; transaction-line owner attribution is still unverified.
- Security identity and historical F80 membership remain unverified in the Form 4 detail ledger.
- Transaction semantics remain unverified. Form 4 code `P` may represent an open-market **or private** purchase; it is not sufficient evidence of exchange execution.
- The 149 transaction rows contain 52 `P`, 40 `S`, 22 `M`, 18 `A`, 6 `C`, 4 `J`, 3 `G`, 2 `F` and 2 `X` rows. These are filing rows, not independent issuer-level events.
- The only previously identified exact ticker overlap with the static 335-name F80 snapshot was SE; it was one filing with seven sale lines and an affirmative Rule 10b5-1 indicator, retained as a planned-trading negative control. The static ticker list is not a historical security master.

### Form 144 comparator

The Form 144 structured ledger contains 3,549 detail rows across 514 accessions. All 3,549 rows are marked research-observation eligible and have source XML hash matches to their first-seen event; signal-eligible rows remain zero.

This is not a claim that the two pipelines have identical provenance. Form 144 captured the filing XML during its first-seen process and can compare that XML hash to the event ledger. Form 4 retrieves structured details in a later bounded backfill and therefore must use the later retrieval time, not pretend it has the same event-time hash provenance.

## 5. Decision and next gates

- **Pass:** conservative retrieval-clock candidate gate for the 229 currently parsed Form 4 detail rows.
- **Not passed:** exact public-availability certification, owner-to-transaction-line attribution, security/share-class identity, historical F80 membership, and transaction semantics.
- **Signals admitted:** 0.
- **Forward-return/event study, alpha, OOS, bootstrap, LOO or holdout:** not performed.
- **Production/collector behavior:** unchanged; the audit is read-only.
- **Data purchases/vendor contact:** none.
- **Frozen baseline:** `F80_TOP20_PARTIAL50_BASELINE_C20` unchanged.

Next, keep the scheduled Form 4 collector and bounded backfill running. A separate derived observation panel may use `detail_retrieved_at_utc` as its conservative knowledge clock only after the identity and attribution gates are independently resolved. Do not alter the source ledger's existing flags or use the 229 candidates as a signal before that work is complete.

## Reproducibility

- Audit script: [phase602_form4_conservative_retrieval_clock_audit.py](phase602_form4_conservative_retrieval_clock_audit.py)
- Regression tests: [test_phase602_form4_conservative_retrieval_clock_audit.py](test_phase602_form4_conservative_retrieval_clock_audit.py)
- Workflow: [phase602_form4_conservative_retrieval_clock_audit.yml](../.github/workflows/phase602_form4_conservative_retrieval_clock_audit.yml)
- No SEC requests are made by the audit.
