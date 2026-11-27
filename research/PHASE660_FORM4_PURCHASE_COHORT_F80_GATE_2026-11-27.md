# Phase 660 — SEC Form 4 code-P purchase cohort and frozen-F80 exact-symbol gate

**Audit cutoff:** 2026-11-27 09:45 UTC  
**Main snapshot:** a27340c1866b5e44f2638eb4dc3e0cbd1617b7ea  
**Latest natural Form 4 run:** [45976055356](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45976055356), both jobs successful; artifact [15186742638](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45976055356/artifacts/15186742638).  
**Disposition:** descriptive transaction-code cohort and exact-symbol universe audit only. No event study or signal admission.

## 1. Latest capture and immutable inputs

The latest scheduled Form 4/4-A capture completed successfully. It found **zero new accessions and zero new canonical event rows**. It did enrich previously known filings:

- 48 structured transaction-detail rows appended across 10 accessions;
- 65 transaction-linked footnote references appended;
- a separate footnote pass appended 60 additional references;
- 10 filing-level owner rows appended;
- 16 Form 144 proposed-sale crosswalk matches across 15 Form 4 accessions, with two Form 144 acceptance clocks unresolved;
- zero signal-eligible matches.

These are backfill/enrichment changes, not 48 new economic events.

The audit uses exact immutable inputs:

| Input | Source |
|---|---|
| Transaction details | main commit a27340c, Git blob f3ca95feb6f56e43eaac46a5fca4f66a73783a51 |
| Reporting owners | main commit a27340c, Git blob 9017a22a48e53be0299d85a9a850db0449e6918b |
| Static 335-ticker reference | commit 1aa1b91f383ce9cef375a43e775c736a27356a5, Git blob 7edbd62b4fb34a6123276e4ce45cb3c1c62479c7, SHA-256 f850655a22a8843dad90e9562b3152b9ca064560586109022b5bfd205a003dda |

The workflow recovers these exact Git objects and verifies their blob IDs before recomputing the audit.

## 2. Current Form 4 ledger and code-P cohort

| Measure | Result |
|---|---:|
| Detail records, including filing headers | 464 |
| Structured transaction rows | 314 |
| Distinct transaction accessions | 150 |
| Filing-level owner rows | 147 |
| Accessions with owner sidecars | 130 |
| Code-P transaction rows | **89** |
| Code-P accessions | **59** |
| Distinct symbol values including N/A | 45 |
| Distinct non-N/A symbol values | 44 |
| Filing-date range | 2026-11-19 to 2026-11-25 |

The 59 code-P accessions are not 59 independent issuer events: ten issuer-symbol clusters contain multiple accessions. The repeated-symbol groups include TROX, GROV, PICS, ESEA, UXIN, SEI, UPST, HOS, ACON and PRE.

Three code-P accessions still lack filing-level owner sidecars: ECF, BG and HBCP. None intersects the static F80 snapshot. Four code-P accessions are multi-owner filings and remain at filing grain; their transaction rows are not expanded into separate owner trades.

The filing-level Rule 10b5-1 indicator is affirmative in **3 accessions / 11 rows** and negative in **56 accessions / 78 rows**. It remains a filing-level attribute, not a verified transaction-line intention field.

Footnote keyword diagnostics found no open-market or private-purchase/placement mentions in this code-P cohort. This is not proof that trades were not open-market or private; it only describes the current keyword parser's coverage.

## 3. Exact-symbol intersection with the frozen 335-ticker reference

Only **3 accessions, 11 transaction rows and 2 symbols** intersect the static 335-ticker list:

| Symbol | Issuer | Accessions | P rows | Reported shares | Filing-level 10b5-1 |
|---|---|---:|---:|---:|---|
| UPST | Upstart Holdings, Inc. | 2 | 2 | 110,000 | No |
| TEAM | Atlassian Corp | 1 | 9 | 13,400 | Yes |

### UPST — one issuer-level hypothesis, not two independent observations

The two filings are the previously adjudicated Paul Gu and Dave Girouard purchases: one CEO/officer/director filing and one director/10% owner filing. Both owner sidecars resolve at filing grain, both report indirect trust ownership, and neither has an affirmative filing-level 10b5-1 flag. The two accessions form **one UPST issuer cluster**, not two independent issuer observations. See [Phase 655](PHASE655_FORM4_LIVE_LEDGER_OVERLAP_AND_UPST_PURCHASE_CLUSTER_AUDIT_2026-11-27.md) for the primary-document adjudication and conservative availability clock.

This remains only a candidate for further source/identity verification. Code P does not establish open-market execution, discretionary intent or a predictive effect. The current pipeline still marks transaction-line owner attribution, security identity, historical F80 membership, public availability and transaction semantics unverified.

### TEAM — planned-trading negative control

The nine TEAM rows belong to one filing by Michael Cannon-Brookes. Its filing-level 10b5-1 indicator is affirmative and the footnote parser detects a Rule 10b5-1/trust mention. The nine rows are one filing-level planned-trading context, not nine independent purchases or a discretionary insider cluster.

## 4. Interpretation and decision

SEC transaction code P covers **open-market or private purchases**. It cannot distinguish the venue by itself. A blank 10b5-1 flag, a negative filing-level flag, indirect ownership or the absence of a footnote keyword cannot establish discretionary intent.

The static 335-symbol match is not historical F80 membership. It does not resolve issuer/security-class continuity, listing, delisted status or the exact point-in-time universe. Filing-level owner sidecars also do not certify transaction-line owner attribution.

**Decision: P_CODE_CONTEXT_ONLY_NO_PROMOTION.** The only non-10b5-flagged issuer cluster in the static-F80 intersection is UPST; TEAM is a planned-trading negative control. One issuer cluster is insufficient for an issuer-level predictive hypothesis, much less OOS inference. The wider code-P cohort is dominated by symbols outside the static 335-ticker reference.

## 5. Next gates

1. Keep UPST as a descriptive candidate only; do not run a return test until primary-document venue/transaction semantics, share-class identity and the conservative first-executable-session clock are fully reconciled.
2. Build an effective-dated security master and historical F80 membership layer before any ticker-based event study.
3. Expand the Form 4 cohort over multiple filing windows and cluster by issuer, owner, accession and economic event; do not count transaction rows or amendments as independent events.
4. Only after a sufficiently broad, eligible multi-issuer sample exists, preregister the event hypothesis and compare incremental information against frozen LTM/F80 with identical exposure/costs, chronological OOS, block bootstrap and issuer/time-block LOO.
5. Continue the bounded owner/footnote backfill and preserve unresolved sidecars as unknown.

## 6. Frozen controls

- F80_TOP20_PARTIAL50_BASELINE_C20: **frozen**.
- New signal promoted: **none**.
- Incremental alpha demonstrated: **none**.
- Prices/forward returns inspected in Phase 660: **no**.
- Event study, OOS, bootstrap, LOO or holdout test: **none**.
- Production, universe, capital, exposure, costs, parameters and holding-period rules changed: **no**.
- Vendor contact, quote request or data purchase: **none**; budget remains **USD 0**.
