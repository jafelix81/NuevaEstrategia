# Phase 425 — Form 144 order-timing and non-execution semantics recheck

**Audit date:** 2026-11-16 UTC  
**Disposition:** retain Form 144 only as a selective affiliate proposed-supply / order-placement hypothesis. The current SEC interpretation makes it unsafe to describe the filing as a reliably pre-execution warning. No signal or return test is admitted.

## 1. New regulatory evidence

The SEC Division of Corporation Finance's Securities Act Compliance and Disclosure Interpretation (CFI) page is currently marked **last updated October 15, 2026**. Question 136.05 was specifically revised September 25, 2026. It now states that, when Form 144 is required, no waiting period is required between the seller placing an order with a broker and broker execution, provided the seller transmits the form concurrently with the order **to both the Commission and the principal exchange on which the securities are listed**.

Official source: [SEC Securities Act Rules — CFI Questions 136.01–136.09](https://www.sec.gov/rules-regulations/staff-guidance/corporation-finance-interpretations/securities-act-rules) (Question 136.05; page last updated October 15, 2026).

This sharpens the timing interpretation:
- A Form 144 may coincide with order placement and execution may follow without a regulatory waiting period.
- A Form 144 may also be transmitted with a direct sale to a market maker under Rule 144(h).
- Therefore the SEC filing is not a dependable lead-time signal for the execution of the disclosed quantity. At best it is a contemporaneous disclosure of an affiliate's proposed sale/order placement; in some cases execution may already be occurring.
- The updated CFI also refers to transmission to the principal exchange. The repository captures SEC EDGAR, not exchange-side receipt or dissemination. No exchange timestamp or public exchange-feed availability has been established. Do not infer that EDGAR first-seen is the earliest public or market-participant timestamp.

The SEC's Form 144 electronic-filing guide states that reporting-company filings are disseminated publicly on SEC.gov on the same business day when submitted during EDGAR's filing window. It does not provide an exact first-public timestamp. The existing conservative daily rule therefore remains: use the filing date only as a calendar-day boundary and make a record eligible no earlier than the first regular NYSE session strictly after that date. No same-day or intraday use.

Official source: [SEC — File Form 144 Electronically](https://www.sec.gov/submit-filings/filer-support-resources/how-do-i-guides/file-form-144-electronically) (last reviewed December 22, 2025).

## 2. Non-execution cannot be inferred from the absence of an amendment

SEC CFI Question 136.01 states that if a person files Form 144 but does not sell the securities, no amendment reflecting that fact is required.

The implication is important: **absence of a 144/A does not establish that the proposed sale was executed, cancelled, or still outstanding.** It is an unknown execution outcome. The SEC filing alone cannot supply an execution-confirmation label.

CFI Questions 136.06 and 136.07 also confirm that amendments may be filed for broker changes or to correct inaccuracies. An amendment is not itself proof of a new independent sell order.

Official source: [SEC Securities Act Rules — CFI Questions 136.01, 136.06 and 136.07](https://www.sec.gov/rules-regulations/staff-guidance/corporation-finance-interpretations/securities-act-rules).

## 3. Selective coverage and event meaning

Form 144 is not a census of insider sales:
- It is filed by an affiliate for a Rule 144 proposed sale when the applicable three-month threshold is exceeded (more than 5,000 shares/units or aggregate sale price above $50,000).
- Non-affiliates generally no longer have a Form 144 filing requirement under the amended rule.
- The form records proposed units, aggregate market value, seller relationship, broker/market maker and approximate sale date. These are proposed-sale attributes, not proof of executed quantity or realized proceeds.

Sources:
- [Investor.gov — Form 144](https://www.investor.gov/introduction-investing/investing-basics/glossary/form-144).
- [SEC — Revisions to Rules 144 and 145, Small Entity Compliance Guide](https://www.sec.gov/files/rules144-145-secg.htm).
- [SEC Form 144 PDF and instructions](https://www.sec.gov/servlet/sec/about/forms/form144.pdf).

The correct economic label is **selective affiliate supply / order-placement disclosure**, not “smart-money buying”, institutional ownership, or a confirmed insider sale. Seller affiliation does not establish that the seller has superior information.

## 4. Amendment state model remains mandatory

The prior Phase 398 census found 196 candidate 144/A amendments. Among 193 candidate-panel parent matches, 87 changed at least one audited tranche field; 44 changed proposed units, 59 proposed value, 19 the outstanding-share field, 18 the approximate sale date, and 20 broker/market maker (counts overlap). Five matched parents were themselves amendments. These changes make accession-level versioning essential.

Required treatment:
1. Keep the original 144 accession as the proposed-sale event root.
2. Preserve each 144/A as a separate version with its own accession, filing date and availability boundary.
3. A changed quantity, value, security class, broker, exchange or approximate sale date becomes known only from that amendment's own availability date.
4. Never backdate amended fields into the original event.
5. Never count an amendment as a second independent sell order.
6. An unresolved or missing parent leaves the amendment chain unresolved; do not infer the original payload from the child.

Existing supporting work:
- `research/PHASE398_FORM144_AMENDMENT_LINEAGE_AND_TRANCHE_RESOLUTION_2026-11-14.md`
- `research/PHASE401_FORM144A_FULL_PARENT_IDENTITY_CENSUS_2026-11-14.md`
- `research/PHASE402_FORM144_PARENT_ACCEPTANCE_AND_UNRESOLVED_LINK_AUDIT_2026-11-14.md`

## 5. Feature design and kill conditions

If the remaining historical identity and PIT gates ever pass, the only defensible initial hypothesis is whether the **publicly disclosed proposed supply** has incremental information about subsequent returns or risk after the next eligible session, beyond frozen LTM/F80 and ordinary price/volume controls.

Pre-specified candidate descriptors may include:
- Proposed aggregate USD value relative to strictly lagged dollar ADV;
- Proposed units retained as a raw attribute, with no assumption they execute;
- Seller relationship / affiliate category, only when reliably parsed;
- Number of distinct sellers and issuer-level concentration, with seller/issuer clustering;
- Original notice versus amendment-state updates, without duplicate event counting.

Do not use `noOfUnitsOutstanding` as a denominator or feature; Phase 399 killed it because scale metadata and point-in-time reconciliation failed. Do not normalize by future ADV, future shares outstanding, current ticker maps, or post-event security identity. Resolve every tranche to an effective-dated security class and historical F80 membership first.

A future economic test must:
- Begin strictly after the first eligible regular session;
- Treat execution as unobserved unless independently confirmed by a separate source;
- Control for prior return, momentum, volatility, liquidity, earnings/news and market regime to distinguish predictive supply pressure from return-chasing;
- Compare against frozen LTM/F80 under identical exposure and costs;
- Use chronological development/validation/OOS, purging/embargo, block bootstrap/HAC and issuer/seller leave-one-out diagnostics;
- Kill the hypothesis if coverage/identity fails or net incremental value does not survive those controls.

No such test was run in this phase.

## 6. Current operational cross-check

- Main HEAD at audit start: `30f199330ebf664a79e8a971da7d84427145f850`.
- Latest 100 Actions runs: 7,660 total reported; 62 success, 37 failure, 1 cancelled; all 100 returned runs completed, with no queued/in-progress/waiting/requested run visible.
- Inspected 261 branches across three API pages, all 56 open PRs and all 63 workflow files. No workflow was dispatched or rerun; no PR was changed.
- SEC Form 144 latest scheduled run [43773157505](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43773157505): both jobs passed; offline regression 15/15; receipt 2026-11-15 23:08:38Z; 55 feed observations (50 Form 144 + 5 Form 144/A); zero new accessions, events, candidate matches or XML resolutions; no possible feed-window gap; artifact [14185511467](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43773157505/artifacts/14185511467), SHA-256 `bd11931ee68dd3381663719a0690f516f7413a3af48767cfac55a23e1dd97521`. The 5h10m35s interval since the prior successful poll remains inconsistent with a demonstrated hourly capture clock. No manual poll or cron change.
- CFTC TFF latest run [43525140200](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43525140200) is still a branch-push bootstrap: 11/11 tests, 3,035 historical rows, zero signal-eligible rows, no state overwrite; artifact [14084802705](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43525140200/artifacts/14084802705). The first expected post-release scheduled capture remains Monday 2026-11-16 22:15 UTC after the 20:30 UTC release.
- SEC 13D/G parent retrieval remains blocked pending the repository owner's monitored-contact `SEC_USER_AGENT` Actions secret for PR #37. No retry was attempted.
- FINRA Phase 20C remains blocked at 328/329 valid price histories. Options and commercial flow sources remain conditional; no source admitted.

## 7. Decision

Form 144 remains a potentially useful but selective **seller-supply/order-placement** research source. Its filing is too close to order placement/execution to be assumed to provide a pre-execution warning, and a missing amendment cannot identify non-execution. Keep the source in research-only status with next-session-only timing and immutable amendment versions.

No source or signal is admitted. No forward-return, alpha, OOS, bootstrap, LOO or holdout test. `F80_TOP20_PARTIAL50_BASELINE_C20`, universe, parameters, holdout, capital, exposure and production remain unchanged. No vendor purchase, credential change or workflow modification.
