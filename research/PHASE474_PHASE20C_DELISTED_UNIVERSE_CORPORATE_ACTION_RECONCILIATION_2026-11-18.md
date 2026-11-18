# Phase 474 — Phase 20C inactive-symbol and corporate-action reconciliation

**Audit cutoff:** 2026-11-18 08:03 UTC  
**Branch:** `phase473-finra-price-provider-response-audit`  
**Base main:** `cdb6f13ab4fab8929c211430f90d86af9dad869b`  
**Disposition:** Phase 473's generic “provider-history drift” explanation is superseded as the primary interpretation of the seven missing symbols. All seven are confirmed inactive, acquired, merged, or renamed by the audit cutoff. The current yfinance response is a price-history coverage failure for inactive securities; the provider's exact truncation mechanism remains unproven.

## 1. Verified Phase 473 census

The exact Phase 11 `download_universe()` path ran against the frozen 335-name universe in [Run 44258810704](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44258810704), artifact [14408145092](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44258810704/artifacts/14408145092).

- 335 configured symbols.
- 328 passed the 220-feature-row gate.
- Seven failed: AVB, EA, EQR, LPRO, ROKU, WBD and WBS.
- The exact yfinance 1.7.0 Phase 11 call returned only 1 row for six symbols and 2 for ROKU.
- Four liquid controls passed with 2,512 rows each.
- No raw prices/features were retained by the census.

The 24 October 2026 Phase 20C run recorded 329/335, but its artifact preserved only aggregate counts, not the six failed ticker names. Six of today's seven corporate actions had closed before 24 October; ROKU closed on 6 November. This timing is consistent with the one-name reduction from 329 to 328, but the missing prior failure ledger means that exact ticker-level reconciliation is **not proven**.

## 2. Corporate-action evidence

The seven failures are not seven ordinary active listings with unexplained data outages:

| Legacy symbol | Verified event | Closing/effective date | Contractual consideration or continuity |
|---|---|---:|---|
| AVB | Merged into the Vivmark / VMRK structure | 2026-08-17 | 2.793 VMRK common shares per AVB share; fractional cash-in-lieu |
| EA | Acquired and taken private | 2026-08-04 | $210 cash per EA share |
| EQR | Surviving issuer renamed and ticker changed to VMRK | 2026-08-17; VMRK trading from 2026-08-18 | Same issuer-share continuity; not a new 1:1 merger conversion |
| LPRO | Acquired by ANV Group and became indirect wholly owned subsidiary | 2026-07-30 | $3.15 cash per LPRO share |
| ROKU | Acquired by FOX; trading halt requested before 2026-11-09 open | 2026-11-06 | Closing 8-K: 0.9799 FOX Class A shares + $95.30 cash per ROKU share, after appraisal-related adjustment |
| WBD | Acquired by Skydance | 2026-10-06 | $31.01666668 cash per WBD share, including ticking consideration |
| WBS | Acquired by Banco Santander; common stock withdrawn before 2026-08-20 open | 2026-08-20 | 2.0548 Santander ADS + $48.75 cash per WBS share |

Primary evidence:
- AVB/EQR closing and exchange ratio: [SEC Form 8-K](https://www.sec.gov/Archives/edgar/data/906107/000114036126033377/ef20080318_8k.htm); ticker transition: [issuer release](https://www.sec.gov/Archives/edgar/data/906107/000114036126033377/ef20080318_ex99-1.htm).
- EA closing and $210 cash: [Electronic Arts issuer announcement](https://www.ea.com/news/ea-announces-completion-of-acquisition).
- LPRO closing: [SEC Form 8-K](https://www.sec.gov/Archives/edgar/data/1806201/000119312526326655/d117354d8k.htm); offer price: [SEC Form 8-K](https://www.sec.gov/Archives/edgar/data/1806201/000119312526325062/d154380d8k.htm).
- ROKU closing and adjusted merger terms: [SEC Form 8-K](https://www.sec.gov/Archives/edgar/data/1428439/000119312526451874/d181620d8k.htm).
- WBD closing and ticking consideration: [SEC Form 8-K](https://www.sec.gov/Archives/edgar/data/1437107/000119312526415055/d200872d8k.htm).
- WBS closing and mixed consideration: [SEC Form 8-K](https://www.sec.gov/Archives/edgar/data/801337/000119312526357758/d919931d8k.htm).

## 3. Consequence for Phase 20C

The missing seven cannot be silently dropped, replaced with current successor tickers, or treated as zero-return observations. Doing so would alter the frozen 335-name universe and create survivorship/corporate-action bias.

The required repair is an effective-dated security/corporate-action layer that:
1. preserves each legacy ticker's own daily history through its final valid trading session;
2. maps successor identity only from the effective date;
3. records the contractual cash/share consideration and fractional-share treatment;
4. reconciles dividends, splits, cash-in-lieu, trading halt/last trade date and successor prices;
5. marks portfolio holdings through the merger event using executable/official terms and the correct successor security;
6. retains delisted securities in the historical universe.

For stock/cash deals, terminal value cannot be calculated from cash alone. It requires the successor security's contemporaneous price and fractional-share cash-in-lieu. For EQR, the ticker/name transition is continuity of the surviving issuer, not a new merger conversion.

**No terminal total-return series has been reconstructed in this phase.** The last regular trading session and exact price adjustment basis remain to be reconciled from a licensed/authoritative historical price source. The corporate-action ledger is evidence metadata only.

## 4. Corrected source diagnosis

- The current price gap is real: seven symbols fail the current exact Phase 11 price-history gate.
- The symbols' inactive corporate-action status is verified from issuer/SEC evidence.
- The exact Yahoo/yfinance mechanism that leaves only 1–2 historical rows remains unknown.
- The old 24 October failure ticker list was not preserved, so the six-to-seven transition cannot be proven ticker by ticker.
- Stooq and Nasdaq remain unapproved as fallback providers. No provider mixing is admitted.

## 5. Research disposition and next gates

1. Build an effective-dated 335-symbol security master and corporate-action ledger.
2. Recover licensed/authoritative OHLC and corporate-action history for the seven legacy securities, including delisted history.
3. Reconcile last trade/halt dates and terminal consideration for all seven.
4. Only after complete price/corporate-action reconciliation, rerun the same Phase 20C protocol with unchanged universe, signal, execution, costs, chronology and holdout.
5. Continue FINRA first-receipt collection separately; no new short-flow signal is implied by this price audit.

No return, alpha, OOS, bootstrap, LOO or holdout test was performed. No ticker was dropped, no fallback provider was admitted, and no strategy or production parameter was changed.

`F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen.
