# Smart Money Research — state addendum (Phase 683)

**Updated:** 2026-11-28 UTC  
**Audit base:** `1192a6c28a3da86ee84109497857a5a0bc8cd8d4`.

## Phase 683 — FINRA Reg SHO source-channel rights gate

- Audited the official FINRA Website Terms and the separate FINRA Query API Terms / Equity Specific Terms.
- The direct Reg SHO collector uses `cdn.finra.org/equity/regsho/daily/CNMSshvol{date}.txt`, not the licensed Query API. FINRA Website Terms restrict database creation, bulk copying/harvesting and use in predictive analytics/trade-prediction software. The current Terms page does not expressly identify the CDN path, so the audit records a material unresolved scope question rather than a legal conclusion or breach finding.
- Put further direct-CDN ingestion, database expansion and predictive use on a **rights hold** pending written clarification/permission.
- Identified a separate potential route: Query API `otcMarket/regShoDaily`. The Equity Specific Terms allow non-commercial internal personal/professional use and derivative data; they prohibit further end-user redistribution. The production dataset has a rolling 12-month window. An individual may create a free Public credential (10 GB/month), but the account holder must accept the terms and provision it. The route is not activated.
- No vendor/FINRA contact, credential change, purchase, workflow dispatch, rerun, schedule edit, code change or strategy change occurred.
- This rights gate does not affect independent SEC EDGAR, CFTC or other source lines, which retain their own rights/PIT admission checks.

Full report: [Phase 683 FINRA Reg SHO source-channel rights audit](PHASE683_FINRA_REGSHO_SOURCE_CHANNEL_RIGHTS_AUDIT_2026-11-28.md).  
Machine-readable summary: [Phase 683 JSON](phase683_finra_regsho_source_channel_rights_audit_2026-11-28.json).

## Current research disposition

- Direct FINRA CDN predictive use: **rights hold pending clarification**.
- FINRA Query API alternative: **conditional, not activated**.
- Signals promoted: **0**.
- Incremental alpha demonstrated: **none**.
- New OOS/bootstrap/LOO result: **0**.
- `F80_TOP20_PARTIAL50_BASELINE_C20`: **frozen**.
- No source, universe, feature, parameter, cost, exposure or holding-period change.
- Data spend: **USD 0**.

## Next work

1. Continue source lines with independently valid rights and PIT gates; prioritize SEC Form 4/144/13D/G and CFTC rather than assuming FINRA is indispensable.
2. Do not resume the CDN Reg SHO capture or predictive analysis until the CDN scope is clarified in writing.
3. If the account holder accepts the API terms and provisions a Public credential, assess the Query API schema, 12-month history, pagination, publication timing and first-seen capture before migrating. Keep the 12-month historical limit explicit.
4. Keep Phase 20C's execution-timing defect separate; no old close-of-signal-day result is admissible.
