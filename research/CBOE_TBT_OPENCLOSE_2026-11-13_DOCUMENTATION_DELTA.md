# Cboe TBT and Open-Close documentation delta — 2026-11-13

**Scope:** current official product-page and specification review only.  
**Disposition:** documentation confirmed; no sample, PIT, alpha or purchase admission.



## Findings

A fresh read of the live Cboe DataShop pages and the v1.1 TBT specification confirms the Phase 236 admission decision; it does not relax the PIT or licensing gates.

### TBT current product-page confirmation

- The product page still describes one execution-level record with timestamp, underlying/OSI contract fields, price/size, buy/sell, open/close, capacity, trade type, NBBO and local BBO, plus simple/complex execution IDs.
- Current page states **C1 only**, with BZX, C2 and EDGX planned, **T+1** delivery and advertised archive start **2019-10-07**.
- The v1.1 specification dated 2026-10-05 lists 22 fields. Its T+1 subscription schedule is typically 00:30–01:30 ET after midnight. Use TRADING_DT around GTH midnight; do not substitute the calendar date of TRANSACT_TIME.
- Capacity mapping and the warning against treating SIDE as aggressor direction or CAPACITY as beneficial-owner identity remain unchanged.
- The product page's public sample link was visible, but the sample ZIP could not be retrieved by the current web/runtime download path. No sample bytes, row-grain validation or execution-ID reconciliation are claimed.

### Open-Close intraday documentation change effective 2026-11-08

The current Open-Close product page announces a new intraday schema/quality cutover:
- 1-minute files: lowercase column names; new trading_dt and trading_segment; subsequent snapshots reflect trade breaks/busts/cancellations; cancelled/busted trades are removed from later 1-minute snapshots; indicative/unsettled trades are removed.
- 10-minute files: trade_datetime format changes to yyyy-mm-dd hh:mm:ss; trading_dt and trading_segment are added; one misspelled close-quantity field is corrected; indicative/unsettled trades are removed; customer files switch to gzip; final interval file times change (C1 17:00; BZX/C2/EDGX 16:15).
- These changes are explicitly for **intraday** files. Do not apply them to EOD files or TBT. Intraday history therefore needs an explicit pre/post-2026-11-08 schema and correction-vintage regime. A later corrected snapshot must not be backdated to the first interval receipt.

### Current product scope and convention reminders

Open-Close EOD remains separate per exchange and is not consolidated OPRA:
- C1 EOD start 2005-01-03; C1 10-minute start 2011-01-03; C1 1-minute start 2019-10-07.
- BZX/C2/EDGX EOD start 2018-01-02; their 1-/10-minute history starts 2019-03-01.
- C1 GTH coverage starts 2023-12-11.
- Existing C1/C2 OI, total-volume and previous-close historical convention breaks remain as recorded in Phases 250–251.

### Updated disposition

No change to the prior admission ruling:
- TBT remains a high-priority **conditional C1 execution-measurement** candidate, not a smart-money signal.
- Pre-launch archive dates remain retrospective backfill, not strict PIT. The public launch-documentation floor and actual first-receipt logs still govern any live-product use.
- Open-Close intraday is a separate prospective measurement candidate with a 2026-11-08 schema/correction cutover; it does not establish a historical receipt ledger.
- The last located C1 TBT fee schedule (2026-04-21) listed $12,000/month subscription and $8,000/month per month of ad-hoc history; the current product page does not expose a price. Reconfirm pricing and rights before any acquisition.
- No sample, trial, vendor contact, purchase, card authorization, return test, OOS, holdout, or production change occurred. F80 remains frozen.

Official sources checked 2026-11-13:
- TBT product page: https://datashop.cboe.com/enhanced-us-options-trade-by-trade-execution-detail
- TBT v1.1 specification: https://datashop.cboe.com/documents/TBT_Spec_v1.1.pdf
- Open-Close product page and 2026-11-08 intraday notice: https://datashop.cboe.com/cboe-options-open-close-volume-summary
- TBT factsheet: https://datashop.cboe.com/documents/C1_Trade-by-Trade_Factsheet.pdf

