# Phase 71 — Trace of the original 335-name universe rule

**Date:** 2026-11-04  
**Branch:** \`phase71-original-universe-rule-trace\`  
**Scope:** source-code and Git-history trace only. No return calculations or alpha tests.

## Executive result

The repository does not document a reproducible rule that generated the 335-name universe. The original discovery code explicitly says the 335-symbol \`DEFAULT_UNIVERSE\` must be copied from the current project; it does not construct the universe from a historical screen, index membership file or dated security master.

This confirms the Phase 70 hard blocker: historical tests over the fixed list are conditional on a curated present-day symbol set, not a proven point-in-time eligible cross-section.

## 1. Direct code evidence

### Phase 0 — discovery

File: \`Nueva_Estrategia_Fase0_Descubrimiento.py\`

- Header describes factor discovery across future returns at 5/10/20/40 sessions.
- The source comment says: “El universo DEFAULT_UNIVERSE debe copiarse desde el proyecto vigente.”
- The code embeds 335 ticker strings and aborts unless the count is exactly 335.
- It downloads ten years of prices by ticker through yfinance.
- It then selects factor directions using 12 discovery dates and applies the frozen directions to later dates.
- No upstream rule in this file defines why a security enters or leaves the 335-name list, and no historical membership dates are produced.

### Phase 9 — portfolio persistence

File: `Nueva_Estrategia_Fase9_PortfolioPersistence_LTM.py`

- Contains the same hard-coded 335-name list.
- Its comment calls it the exact frozen universe used by the preceding research phase.
- Its empty-universe error says to replace the list with the exact 335-ticker universe from a preceding “Phase 9D research file”.
- The Phase 9 file itself does not explain how the 335 were selected or provide dated membership. The referenced Phase 9D source file was not found in the inspected repository tree, the 104 current branch names, or the Library search results; the accessible Phase 9 artifact is the portfolio-persistence script itself.

### Phase 5 — momentum validation

File: \`Nueva_Estrategia_Fase5_LongTermMomentum.py\`

- \`PERIOD="10y"\`.
- The same 335-name list is hard-coded and count-checked.
- Prices are downloaded by ticker; no effective-dated listing/security identifier is used in the loader.
- The phase tests momentum windows and forward returns within that fixed list.

### Phase 6 — walk-forward LTM

File: \`Nueva_Estrategia_Fase6_WalkForward_LTM.py\`

- The same fixed 335-name list is embedded.
- The loader requests ten years by ticker.
- The ETF/index classification is a hard-coded allowlist; all other symbols fall through to EQUITY. It is not a complete historical security-type master and does not resolve share classes, ADR status or fund series.
- The LTM ranking is cross-sectional only over the names returned by the current hard-coded list at each historical date.

### Phase 8 — portfolio construction

File: \`Nueva_Estrategia_Fase8_Portfolio_LTM.py\`

- Again embeds the same 335 names.
- Again requests ten years of prices by ticker.
- Portfolio selection is downstream of that fixed list; it does not rebuild the eligible security pool as of each formation date.

## 2. Git-history trace

The repository history shows the Phase 0 discovery file was uploaded on 2026-10-14, and Phase 9/Phase 6/Phase 8 files were uploaded on 2026-10-15. The Phase 9 file contains the list and refers to a preceding Phase 9D research file, but that referenced file is not present in the inspected repository tree, current branch names (104 branches checked), or matching Library search results. Available commit messages are generic “Add files via upload”/rename messages; they do not document the universe source, screening date, inclusion thresholds or replacement process. In the 2026-10-14 prior conversation, the user supplied only that the script required the frozen 335-ticker universe from the current project; the earlier assistant asserted a Phase 9/9D origin but did not establish selection provenance or criteria.

The Phase 0 comment is the strongest direct provenance statement found: the list was copied from the current project. No dated input file, screen export, index-membership source or universe-change ledger appears in the inspected repository tree.

This does not prove the list was selected using future returns. It means the repository cannot currently establish when or by what rule each name became eligible.

## 3. Why a security master alone is insufficient

A PIT security master can resolve the identity and lifecycle of securities that are known to the universe, including ticker changes and delistings. It cannot restore names that were never included in the 335-name list because they later failed, delisted, were acquired or otherwise left a curated screen.

Therefore two separate tasks are required:

1. **Identity/lifecycle:** map each ticker to a permanent security/listing identifier with effective dates and record-known timestamps.
2. **Universe membership:** reconstruct the actual eligibility rule and every security that satisfied it at each historical formation date, including securities that later disappeared.

The Phase 68 335/335 SEC ticker-to-registrant-CIK map addresses neither historical listing identity nor historical membership. CIK is an issuer/registrant cross-check, not a tradable security ID.

## 4. Research decision

- Do not describe fixed-335 historical results as a general survivorship-bias-free cross-sectional test.
- Keep those results as conditional diagnostics on the present-day curated set.
- Do not modify or invalidate the frozen control solely from this audit; the audit identifies an evidence limitation, not a measured performance error.
- Recover the original selection rule only from contemporaneous source material. Do not reverse-engineer thresholds by optimizing historical performance.
- If the original rule cannot be recovered, create a **separate** broad-universe research line with a predeclared PIT eligibility rule, permanent security IDs, delisted coverage and terminal-return handling. Do not silently substitute that universe into F80.
- A broad-universe reconstruction should include common stocks and other instrument types only according to an explicit rule; ETFs/ETNs, ADRs, preferreds, warrants, multiple share classes and OTC transitions must be classified consistently and separately.

## 5. Minimum requirements for a future broad-universe benchmark

1. A reproducible historical eligible universe on every formation date.
2. Permanent security/listing IDs, exchange/MIC and security type.
3. Effective dates plus record-known/publication timestamps or archived contemporaneous snapshots.
4. Active and inactive securities, including acquired, bankrupt and delisted names.
5. Corporate-action and terminal delisting return treatment.
6. Historical price/volume data that join on permanent IDs rather than ticker alone.
7. Exact replication of the frozen strategy's ranking, exposure, rebalance and cost rules before comparing any alternative universe.
8. Chronological OOS, block bootstrap and leave-one-issuer-out after the universe/data gates pass.

## 6. Status

- Original 335-universe rule: **NOT FOUND in inspected repository history/code or the matching Library search**.
- Phase 9 contains the 335-name list and references a preceding Phase 9D file, but the referenced Phase 9D artifact and its selection criteria are unavailable.
- Fixed-list membership history: **NOT AVAILABLE in repository**.
- Phase 68 current ticker-to-CIK map: 335/335, but current-only.
- Phase 67 Form 144 issuer-role census: identity gate passed for the old 309-CIK candidate set; Phase 69 incremental fund scan is prepared but not yet run.
- Databento / AlgoSeek / CRSP: vendor feasibility candidates only; no data purchased and no vendor contacted.
- No forward returns or alpha tests were run.

\`F80_TOP20_PARTIAL50_BASELINE_C20\` remains frozen.


## 7. Phase 9D artifact recovered from Library — provenance narrowed, not resolved (2026-11-04)

A second search of the user's Library surfaced the previously referenced `CERE_Phase9D_Reconciliacion_Economica_FIXED.py` (created 2026-10-14 00:19:38 UTC), along with earlier and later copies named `CERE_Phase9D_Reconciliacion_Economica.py` and `CERE_Phase9D_Reconciliacion_Economica_CORREGIDO.py`. This corrects the earlier statement that no Phase 9D file was available anywhere: a Phase 9D reconciliation script does exist in the Library, although it is not in the GitHub repository.

- The recovered script contains a 335-symbol `DEFAULT_UNIVERSE` with 335 unique tickers.
- Its sorted 335-symbol set matches exactly the 335-symbol lists embedded in repository Phase 0, Phase 6 and Phase 9 (independent normalized set comparison; all counts 335, no duplicates).
- The script labels it only as a “frozen backup universe” and enforces `MIN_UNIVERSE = 335`. It can alternatively load `CERE_UNIVERSE`, `CERE_UNIVERSE_FILE`, or a common local ticker file; the runtime audit would record `UniverseSource`.
- The recovered source does **not** state the screening date, source universe, market-cap/liquidity filters, inclusion/exclusion criteria, replacement policy or dated membership history. No corresponding Phase 9D runtime audit/artifact showing the actual `UniverseSource` was found in the Library search.

Therefore the recovered Phase 9D file confirms the historical existence and exact contents of the frozen 335-name snapshot by 2026-10-14, but it does not establish how the names were selected or whether they were selected without hindsight. The Phase 71 hard blocker remains: no reproducible historical eligibility rule or membership ledger has been recovered. Do not infer that the list was selected using future returns; equally, do not claim survivorship-bias-free cross-sectional coverage.

Library files inspected: `CERE_Phase9D_Reconciliacion_Economica_FIXED.py`, `CERE_Phase9D_Reconciliacion_Economica_CORREGIDO.py`, and `CERE_Phase9D_Reconciliacion_Economica.py`. The fixed and corrected copies contain the same 335 unique default symbols.


## 8. Phase 21C snapshot independently recovered and reconciled (2026-11-04)

The prior Phase 21C artifact is still available: run 39362237089, artifact 12238056805, created 2026-10-20. Its `phase21c_signal_panel.csv` contains 10,050 rows across 30 signal dates and exactly 335 unique tickers. I compared the normalized ticker set against the recovered Phase 9D `DEFAULT_UNIVERSE` and the repository Phase 11 list: all three sets are exactly identical (335/335; no additions or omissions).

The Phase 21C script imports `DEFAULT_UNIVERSE` from `Nueva_Estrategia_Fase11_Real1000_LTM_v4.py` and then uses that frozen list. Phase 11 labels it “Exact frozen 335-ticker universe”; Phase 21C's artifact demonstrates that the snapshot was actually used in a point-in-time Form 4 diagnostic through 2026-09-29. The Phase 21C audit also records that the Form 4 hypothesis was killed for now: no robust standalone or incremental edge was demonstrated, and no production change was made.

This is stronger provenance for the **existence, exact contents and continued use** of the 335-name snapshot, but it is not independent evidence about the snapshot's original selection. Phase 21C consumes the Phase 11 list; Phase 11 embeds the list; the Phase 9D script calls the same list a frozen backup. None records the upstream eligible universe, screening date, thresholds, replacement policy or point-in-time membership history. The original universe-generation rule therefore remains unrecovered.

Artifact: `phase21c-sec-form4-predictability` from run 39362237089. The signal panel itself is the source of the 335-ticker snapshot; no separate dated membership ledger is present in the artifact.
