# Phase 252 — SEC Form 144 event semantics and proposed-notional feasibility

**Audit date:** 2026-11-10 UTC  
**Disposition:** REAL_ARTIFACT_SEMANTICS_AUDIT_PASS_NO_PIT_NO_ALPHA  
**Scope:** immutable Phase 69 artifact only. No new SEC request, market-data download, vendor contact, purchase, return test, holdout use or production change.

## Reproducible source

Phase 69 run 41959603351 / artifact 13385365595 was downloaded and re-hashed:
- 21,634 accession rows; 21,438 original Form 144 notices; 196 Form 144/A amendments.
- Filing dates: 2023-04-13 through 2026-09-30; 289 issuer CIKs; source ticker map has 335 current-universe tickers.
- ZIP SHA-256: f84644200a8925c6fc190a823ca0dcd6b40c7bee127a8d2740a5ea67cae56519
- Expanded CSV SHA-256: 7a54ee09e8d4520e1ec14cf22f2c0d1c62d077798b14d3db596826e3360a3659

## Findings that change feature construction

1. **Plan date is not the keyword flag.** The official [Form 144](https://www.sec.gov/files/form144.pdf) has a separate “Date of Plan Adoption or Giving of Instruction, if Relying on Rule 10b5-1” field. The Phase 50 parser reads the XML planAdoptionDate/dateOfPlanAdoption elements; mentions_10b5_1 is separately derived by searching the remarks text. Of 21,438 original notices, 12,029 have a parsed plan-date field, while only 1,411 have mentions_10b5_1=True. There are 10,665 with a plan date but a false keyword flag and 47 with a true keyword flag but no plan date. Preserve PLAN_DATE_PRESENT / ABSENT / INVALID-UNKNOWN separately from the remarks keyword flag. Do not infer direction or plan status from the keyword flag.
2. **144/A amendments are later state vintages.** Of 196 amendments, 188 link to an original accession; eight remain unmatched. Five add a plan date, seven remove one and eight change a nonempty date. Never backfill amendment content into the original notice; make the amended state usable no earlier than the first XNYS session strictly after the amendment filing date.
3. **Issuer CIK, not candidate_tickers, controls identity.** There are 291 multi-ticker rows: 290 Z;ZG and one AMT;ASTS. Resolving by xml_issuer_cik gives 288 single-ticker current mappings, one ambiguous Z/ZG mapping and no unmapped issuer CIKs. The AMT;ASTS row includes the filer ticker: issuer CIK 0001780312 maps to ASTS; AMT maps to a different CIK, 0001053507. The current map is not effective-dated; historical class/ticker changes and delisted identity remain unresolved.
4. **Approximate sale and notice dates are not availability clocks.** Among original notices, 156 notice dates differ from SEC filing date. Of 21,653 original sale tranches, 20,708 approximate sale dates equal filing date, 432 are before and 513 after. Four prior-sales rows also have sale dates after filing. Keep the Phase 222 conservative event rule: a filing on D becomes eligible only from the first XNYS session strictly after D. The artifact has no complete acceptance-time/first-receipt history, so no intraday replay is possible.
5. **Coverage is threshold-censored.** Electronic Form 144 filing for reporting-issuer securities became mandatory on 2023-04-13 under [SEC Final Rule 33-11070](https://www.sec.gov/files/rules/final/2022/33-11070.pdf). The later [Final Rule 33-11159](https://www.sec.gov/files/rules/final/2023/33-11159.pdf) extended the deemed-filing deadline to 10 p.m. ET. Earlier paper filings mean pre-mandate EDGAR is not a complete no-event census. The 289 issuers are observed-event issuers, not proof that the other 46 current-universe tickers had zero events. Absence is UNKNOWN, not zero. Form 144 reports a proposed sale, not proof of execution.

## Candidate measurement

Phase 223 rejected Form 144 units_outstanding as a universal denominator. The parsed tranches have no missing numeric proposed units or aggregate market values, but two units values and three market values are zero.

A denominator-free candidate is:

    ADV_days_equivalent = sum(filer-reported proposed aggregate market value)
                           / trailing 20-session average daily dollar volume

This measures proposed notional in ADV-days; it is not float pressure, completed selling or guaranteed execution. It still requires an effective-dated issuer CIK → exact listed class → ticker crosswalk and PIT dollar volume through the session before filing. There are 273 original accession rows and 488 tranche rows beyond the first within issuer/seller/filing-date groups; these are repeated group observations, not automatically duplicates, so none were dropped.

## Decision / next gate

Retain Form 144 as a conditional, threshold-censored proposed-supply candidate. Build the effective-dated class crosswalk, PIT ADV20 panel and as-filed amendment vintages before any return test. Then preregister proposed-notional/ADV-days and a separate plan-date interaction without assuming either direction or predictive value. Only after admission compare incrementally with frozen LTM/F80 using identical exposure/costs, chronological walk-forward, label-maturity embargo, date-block bootstrap, leave-one-ticker-out and a new prospective final holdout.

The actual Phase 69 artifact was re-hashed; a local standard-library audit and 10/10 regression tests passed. No hosted Phase 252 CI is claimed. No returns, alpha, bootstrap/LOO, OOS or holdout test was run. F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen; production, universe, capital and parameters are unchanged. No vendor was contacted and no data were purchased.
