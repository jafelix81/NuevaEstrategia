# Smart Money Research — Current State

**Updated:** 2026-11-10 UTC  
**Active branch:** phase231-cboe-option-quotes-full-row-reparse (PR #14, stacked on PR #13)  
**Frozen baseline:** F80_TOP20_PARTIAL50_BASELINE_C20  
**Legacy holdout:** CONSUMED_NOT_PRISTINE; never reused

## Latest material result — Phase 253

SEC registered-security Inline XBRL is a conditional positive identity source, not a complete crosswalk census: the April 2026 SEC XBRL Guide says no instance type requires the registered-security title facts. Company Facts is entity-wide and cannot replace dimensioned filing contexts.

The Phase 69 Form 144 panel has 21,653 original sale tranches across 289 issuer CIKs: 166 raw security-class labels (135 after case/whitespace normalization); 205/289 issuers have multiple normalized labels; 71 have explicit class-letter labels. The generic label Common occurs in 12,562 tranches, including 11,036 in multi-label issuers and 3,297 in issuers with explicit class-letter labels. These are text-heterogeneity diagnostics, not counts of legal classes.

Normalized XBRL context, exact-title join and as-filed vintage prototype: 23/23 local tests passed. Raw iXBRL parsing and issuer-panel coverage remain untested.

- Phase 253 report: PHASE253_FORM144_XBRL_REGISTERED_SECURITY_CROSSWALK_AUDIT_2026-11-10.md
- Helper: phase253_form144_xbrl_registered_security_crosswalk_audit.py
- Tests: test_phase253_form144_xbrl_registered_security_crosswalk_audit.py
- Result: phase253_form144_xbrl_registered_security_crosswalk_audit_result.json

## Next gates

1. Run a stratified 20–30 issuer raw-iXBRL and visible-cover-page pilot; preserve each filing accession, filing/acceptance time, context, axes/members, original bytes and SHA-256. Measure exact-match coverage before scaling.
2. Bulk SEC retrieval is blocked because the authorized GitHub secret SEC_CONTACT_EMAIL is absent. No request was sent and no email was guessed.
3. Obtain a survivorship-free, corporate-action-aware daily dollar-volume source before computing Form 144 ADV20. No paid source has been authorized or purchased.
4. For Cboe options, first prove multi-date coverage, immutable final/preliminary receipt vintages, effective-dated security identity and licensing. No trial/card authorization or purchase.
5. Keep CFTC BPR/TFF prospective capture and all Smart Money candidates out of production until PIT and incremental OOS evidence pass.

## Other source dispositions

- FINRA Phase 20C: not promoted; no demonstrated incremental stock-selection edge.
- CFTC BPR/TFF: prospective regime candidates only; no historical beneficial-owner identity.
- SEC FTD: context metadata only; external history contains backfills and no immutable first-receipt proof.
- N-PORT: Phase 247 fixed the UNIT/UNITS schema defect; raw PIT and security identity remain open.
- Cboe Open-Close: feature contract and one C1 20% sample validated; no PIT or alpha.
- Cboe option quotes: 115,617 rows; 112,313 unambiguous; 3,304 expiration-ambiguous rows quarantined; no PIT or alpha.
- Cboe All Access: conditional high-information candidate; no account, trial, token, API request or purchase.

## Controls

No alpha/OOS result from Phase 253. No returns, bootstrap/LOO, chronological OOS or holdout test. No production, universe, capital or parameter changes. No minimum/maximum holding period or CAGR target is imposed. Compare any future feature against frozen LTM/F80 with identical exposure and costs.
