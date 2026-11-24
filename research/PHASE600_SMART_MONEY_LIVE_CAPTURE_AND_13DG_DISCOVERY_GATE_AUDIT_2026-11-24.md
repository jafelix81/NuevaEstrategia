# Phase 600 — Smart Money live-capture and 13D/G discovery gate audit
**Audit date:** 2026-11-24  
**Main head at audit:** `34e349fbb12889c0f987e7b540e4aa78bab58dec`

## 1. Repository and execution integrity

- Actions reports **8,111 total runs**. The latest 100 were all completed; no queued or in-progress run was present.
- Current inventory: **380 branches**, **72 open PRs**, **96 workflow files**, and **515 research files**.
- The latest Form 4 and Form 144 scheduled captures completed successfully. No workflow was duplicated, dispatched manually, or rescheduled.

Relevant runs:
- [Phase 476 — Form 4 first-seen capture, run 45453400450](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45453400450)
- [Phase 403 — Form 144 first-seen capture, run 45437675674](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45437675674)
- [Phase 469 — FINRA Reg SHO capture, run 45339067236](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45339067236)
- [Phase 384 — CFTC TFF capture, run 45338400329](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45338400329)

## 2. SEC Form 4: prospective capture works, but the new sample is not a signal

Run 45453400450 observed **57 new accessions** across the Form 4/4-A feeds. Both feed watermarks were found and the poll completed. The transaction-detail step parsed **10 accessions / 30 detail rows**, leaving **47 of these 57** without structured details at this checkpoint; the broader bounded queue still contained 2,320 accessions. Owner enrichment parsed 10 accessions / 11 owner rows, but the 10 newly detailed accessions had not yet received owner-sidecar enrichment.

Among those 10 newly detailed filings, the parser found **11 non-derivative P/A rows across six issuer symbols**: PRE, CTEV, EOSE, OVBC, NMAD and UXIN. All six symbols are outside the frozen 335-symbol F80 snapshot. Therefore this poll added **no new in-universe purchase cluster**. PRE was the largest of these descriptive groups (40,000 shares, approximately USD 404,200); owner attribution remains pending, and this is not an eligible signal.

Controls remain strict:
- 0 signal-eligible observations; no return test or alpha claim.
- Public availability is not certified; first-seen feed receipt is an upper bound, not an exact public-release timestamp.
- The detail ledger records retrieved XML/submission hashes, but they are not comparable to a hash captured in the original event ledger; raw XML is not persisted.
- Form 4's current builder hard-codes `research_observation_eligible=false`. A separate policy-parity audit is warranted before using `detail_retrieved_at_utc` as the conservative research knowledge clock. Any such clock must lead to the next full executable session; same-day intraday use remains unauthorized.

## 3. SEC Form 144: stronger first-seen enrichment, still no signal

Run 45437675674 captured **27 new Form 144 accessions**, resolved all 27 XML submissions, and added **32 acceptance-time reconciliations** with zero unresolved reconciliations. The ledger now contains **514 accessions and 3,549 detail rows**, with zero parse-error rows.

The post-capture quality audit reports 27 research-observation-eligible accessions but **zero signal-eligible observations** and zero certified exact public-availability timestamps. The Form 549 plan-date/polarity audit remains descriptive: formal plan dates are context, not availability times; four Fermi sell-to-cover/tax-withholding notices are explicit negative controls, not discretionary insider-sale signals.

The Form 144 pipeline is a useful engineering reference for improving Form 4's first-seen payload provenance, but its eligibility flag must not be interpreted as alpha.

## 4. Other source status

- **FINRA Reg SHO:** the latest scheduled capture did not produce an admissible daily panel. Six candidate files were rejected by the fail-closed duplicate-symbol checks involving BCPC/TPC. Do not aggregate or silently drop those rows.
- **CFTC TFF:** no new report/revision was captured at the latest poll; the historical panel remains 3,043 rows and is too coarse to identify individual F80 issuers. Keep it as a possible market-regime context source, not a stock-level signal.
- **Options:** remain parked. Authorized initial budget is USD 0; no quote requests, purchases, or paid sample access.
- **13F:** remain parked pending an effective-dated CUSIP/security crosswalk and adequate historical F80 coverage. Accession/holdings joins alone do not establish point-in-time ticker coverage.

## 5. Schedule 13D/G: current structural blocker

The legacy Phase 49 script still contains a placeholder SEC User-Agent and enumerates submissions by the 335 F80 CIKs as **filers**. That is not a complete subject-issuer discovery method: it can miss filings made by activist or other reporting persons outside F80 that identify an F80 company as the subject issuer. The old Fase 35 workflow is explicitly disabled after the subject/filer positive-control failure.

The 20,266-accession historical panel therefore remains quarantined; do not use its filer CIK as the subject issuer. The Phase 485 subject/filer header parser is a useful offline component, but the next rebuild needs global Schedule 13D/13G accession discovery, explicit subject/filer separation, and an effective-dated F80 security mapping.

The existence/value of the repository `SEC_USER_AGENT` secret cannot be inspected through the connected GitHub interface. PRs [#198](https://github.com/jafelix81/NuevaEstrategia/pull/198) and [#204](https://github.com/jafelix81/NuevaEstrategia/pull/204) remain Draft; PR #204 wires the secret for the separate FTD workflow, not the legacy Phase 49 13D/G script. Thus, even if the secret has already been configured, the current 13D/G code path does not consume it. Do not send the secret value in chat.

## 6. Decision and next gates

1. Design a **global-index 13D/G discovery** sample that identifies the subject issuer from the filing header, not from the reporting filer's CIK. Wire the SEC client to the repository secret and fail closed if it is absent; do not start a historical crawl before the bounded sample passes.
2. Audit Form 4 research-observation eligibility against the successful Form 144 pattern. Keep public-availability certification, identity, owner attribution, transaction semantics and signal admission as separate gates.
3. Continue scheduled Form 4/Form 144 collection and owner enrichment. Treat new P/A rows as candidate transactions only; no transaction is assumed to be an open-market execution merely from code P.
4. Keep FINRA and CFTC in data-quality/coverage mode until their respective completeness and identity gates pass. Keep paid options sources parked.

**No strategy change:** `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen. No signal promotion, event-return test, OOS test, bootstrap, LOO, cost/exposure change, holdout use or production change was made in this phase.
