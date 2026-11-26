# Smart Money Research State Addendum — Phase 651

**Cutoff:** 2026-11-26 21:55 UTC  
**Main before documentation:** `db332ddb2ee271abca7f3c38fd2d3475b297b767`

- **OCC options account-type data:** public docs show daily/weekly/monthly volume by Customer, Firm and Market Maker, and a series-level query with call/put, exchange, activity date and contract date. Public pages state a 24-month window. OCC Website Terms prohibit automated systems from accessing Services/Data; the proposed GitHub Actions collector is therefore not admitted under current terms. No endpoint was queried, no sample/quote/license requested, no provider contacted and no data purchased. Decision: `RIGHTS_BLOCKED / NO-GO`.
- **OCC signal semantics:** account-origin categories are not named institutions or verified informed traders. The series-level layout has no buyer/seller side, opening/closing flag, trade price, IV/Greeks or OI field. Any future permitted test would be volume-composition only, not directional smart-money flow.
- **Latest Actions:** 8,355 total; latest 100 = 71 success / 18 failure / 11 cancelled; zero active or queued. PR #247 / Phase 650 is merged as `c7379f42ffffd631e8ce1bc3b9b3261871e3480d`; PR run 45895296971 passed 62/62 offline tests and skipped live capture.
- **Latest SEC scheduled captures:** Form 4 run 45848689364 (15:23:55 UTC), 13F run 45839454376 (14:29:01 UTC), Form 144 run 45827105431 (13:13:48 UTC); all relevant jobs succeeded and artifacts were downloaded/inspected. Form 4 added 23 transaction detail rows and 24 footnote references in bounded backfills; crosswalk has 12 rows and 0 eligible matches. 13F added 29 initial-baseline accessions, all without lower bounds; no holdings downloaded. Form 144 added 52 detail rows, has 825 accessions / 5,495 rows, and 178 backfills remain; no new accessions or eligible signals.
- **CFTC:** run 45753716471 artifact confirms 3,043 total records, 484 Russell contract rows through 2026-11-17, no new report/revision, and no outcomes or signal.
- **FINRA Reg SHO:** latest natural run 45754121648 predates Phase 650 merge; all eight files were rejected by the old parser due BCPC/TPC duplicate groups. Phase 650 run 45895296971 validated 62/62 offline tests only. Await the next natural capture for production validation; old invalid files are not retroactively promoted.
- **Schedule delivery:** successful natural SEC runs prove the workflows ran on 26 November, but no later schedule events were visible at the 21:55 UTC cutoff. This is an observed cadence gap, not proof that workflows are administratively disabled. Issue #194 remains the operational tracking point.
- **CFTC Russell:** two prospective observations remain insufficient; Phase 649 price-rights gate remains unresolved.
- **FINRA T1 ATS / SEC MIDAS / 13D-G:** no new identity, coverage, rights or PIT gate cleared in this phase.
- **Options authorization:** USD 0; no purchases, quotes, trials, license acceptance or vendor contact.
- **Strategy:** `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen. No new alpha, OOS, bootstrap, LOO or portfolio evidence. No production change.

**Phase 651 status:** completed source-feasibility audit; OCC parked as rights-blocked. No strategy promotion.
