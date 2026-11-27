# Smart Money Research State Addendum — Phase 655 (2026-11-27)

**Mainline documentation:** [Phase 655 report](PHASE655_FORM4_LIVE_LEDGER_OVERLAP_AND_UPST_PURCHASE_CLUSTER_AUDIT_2026-11-27.md) · [JSON summary](PHASE655_FORM4_LIVE_LEDGER_OVERLAP_AND_UPST_PURCHASE_CLUSTER_AUDIT_2026-11-27.json)

## New finding

- Re-auditing the current SEC Form 4 structured ledger against the exact static 335-ticker snapshot expands the earlier overlap from one accession/symbol to **41 transaction rows across 21 accessions and 12 symbols**.
- Owner sidecar coverage is complete for 13/21 overlap accessions; eight remain unresolved. Every overlap row remains signal-ineligible, and the static snapshot does not prove historical F80 membership.
- The most interesting hypothesis is one **UPST issuer-level cluster**: CEO/director Paul Gu reported a 50,000-share `P` purchase on 2026-11-19 (reference value $860,065), and director/10% owner Dave Girouard reported 60,000 shares on 2026-11-20 (reference value $950,988). Both filings have the 10b5-1 box unchecked and report indirect trust ownership. Combined reference value is $1,811,053.
- SEC code `P` includes both open-market and private purchases. The venue is therefore unresolved; no discretionary intent or predictive edge is inferred. Treat the two accessions as one issuer cluster, not independent observations.
- The previous SE overlap is now owner-resolved: seven sale lines belong to one filing by Wang Yanjun and carry affirmative 10b5-1 plan context. TEAM's nine purchase lines are also one accession and explicitly plan-related. Both remain negative controls.

## Availability and next gate

The UPST accessions have a bounded collector interval ending 2026-11-23 07:48:52 UTC (02:48:52 ET). The conservative first regular session is 2026-11-23; under the daily-bar rule, the first complete bar is that day's close and the next executable session is 2026-11-24. This is not an exact first-public timestamp. No price or forward return was inspected.

Next gates remain: finish owner/footnote enrichment, resolve purchase venue, build effective-dated security identity and historical F80 membership, and obtain a rights-cleared price source. Phase 649's price-rights gate remains blocked under the USD 0/no-vendor-contact authorization.

## Controls

- `F80_TOP20_PARTIAL50_BASELINE_C20`: frozen.
- No signal promoted; no incremental alpha demonstrated.
- No new OOS, bootstrap or LOO; holdout untouched.
- No universe, parameter, cost, exposure, capital, production or holding-period change.
- No price data downloaded, vendor contacted or data purchased; budget remains USD 0.
