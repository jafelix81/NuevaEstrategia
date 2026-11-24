# Phase 590 — FINRA Reg SHO API facility-reconciliation feasibility audit

**Audit cutoff:** 2026-11-24 07:51 UTC  
**Main HEAD at preflight:** `00d4ca975624c255133da4a5f2ce980df5783fee`  
**Disposition:** a bounded, potentially authoritative cross-check path was identified for the unresolved CNMS duplicate-symbol rows. It is not yet live-verified. Keep the daily-file parser fail-closed; no signal or return test is authorized.

## 1. Preflight: current runs, jobs, artifacts and repository

The latest relevant scheduled runs inspected before any write were:

| Workflow | Run | Result | Relevant evidence |
|---|---:|---|---|
| FINRA Reg SHO / Phase 469 | [45339067236](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45339067236) | completed / success | Live job completed; 6 HTTP-200 CNMS files, all rejected for `duplicate_symbol_in_consolidated_file`; artifact [14895571787](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45339067236/artifacts/14895571787) |
| SEC Form 4 / Phase 476 | [45332760566](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45332760566) | completed / success | Both offline and live jobs completed; artifact [14892950135](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45332760566/artifacts/14892950135) |
| SEC Form 144 / Phase 403 | [45330252226](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45330252226) | completed / success | Both jobs completed; post-capture Phase 565 reconciliation passed; artifacts [14891955642](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45330252226/artifacts/14891955642) and [14891416912](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45330252226/artifacts/14891416912) |
| CFTC TFF / Phase 384 | [45338400329](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45338400329) | completed / success | No new reports or revisions; 3,043 historical rows unchanged; artifact [14895036288](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45338400329/artifacts/14895036288) |

All jobs inspected for these runs were completed. The connector provides specific run/job/artifact retrieval but not a repository-wide Actions run-list endpoint; therefore this audit makes no unsupported claim about the global active/queued count.

Repository inventory: 96 workflow files, 380 branches and 72 open PRs. Main is at the SHA above. Relevant branches remain stale/diverged and were not merged:
- `phase20c-finra-walkforward`: 12 ahead / 590 behind main.
- `phase515-finra-cnms-market-list-schema-repair`: 5 ahead / 159 behind.
- `phase547-cboe-opra-options-pit-feasibility`: 5 ahead / 92 behind.
- `phase530-massive-options-history-pit-license-audit`: 5 ahead / 136 behind.
- `phase548-sec-midas-methodology-pit-reclassification`: 2 ahead / 92 behind.

No workflow was dispatched, rerun, cancelled or duplicated. No code or parser change was made.

## 2. FINRA CNMS duplicate evidence

Phase 469 run 45339067236 returned HTTP 200 for six daily files (trade dates 2026-11-23, 2026-11-20, 19, 18, 17 and 16), but rejected all six. The append-only diagnostic identifies repeated symbols BCPC and TPC (12 duplicate-symbol occurrences / 12 extra rows). Their comma-separated facility sets overlap; some TPC rows share the same facility set but have different raw-row hashes.

The artifact intentionally retains only compact diagnostics (facility sets, line references, row hashes and counts), not raw rows or volume values. No file was accepted into the FINRA state ledger; no first-seen observation or signal became eligible.

The current parser correctly refuses to sum or deduplicate these rows by ticker. A repeated ticker could represent an overlapping aggregate or an unresolved security-grain collision. The present CNMS text schema does not itself provide a permanent security identifier sufficient to resolve that ambiguity.

## 3. New cross-check path: FINRA Query API `regShoDaily`

FINRA's official Developer Center describes `regShoDaily` as daily short-sale volume aggregated by security for trades executed and reported to a FINRA trade reporting facility. The Developer Center exposes the dataset under `otcMarket/regShoDaily` and documents authenticated Query API access and Public, Firm and Organization credential types.

A third-party FINRA API client that retrieves the official metadata endpoint documents a seven-field schema including:
- `tradeReportDate`
- `securitiesInformationProcessorSymbolIdentifier`
- `shortParQuantity`
- `shortExemptParQuantity`
- `totalParQuantity`
- `marketCode`
- `reportingFacilityCode`

Its sample response shows separate facility-coded rows for a symbol (e.g. NCTRF, NQTRF and NYTRF). This is a strong lead for reconciliation, not yet an independently verified live schema for this repository. The API metadata and one small production response must be checked before implementation.

Sources:
- [FINRA Developer Center — Query API and Reg SHO Daily Short Sale Volume](https://developer.finra.org/docs)
- [FINRA API dataset documentation — Reg SHO Daily](https://developer.finra.org/docs/api-explorer/query_api-equity-reg_sho_daily_short_sale_volume)
- [Independent client example of FINRA regShoDaily metadata and facility-coded rows](https://github.com/RobertHennings/FINRA_CLIENT)

### Bounded reconciliation protocol

1. After an authorized credential is available, call the `regShoDaily` metadata endpoint and record the returned field names, types, partition fields and data version.
2. Query one trade date (start with 2026-11-23) and only BCPC/TPC, requesting the seven fields above if confirmed by live metadata.
3. Determine whether `reportingFacilityCode` is present and whether the API exposes any stable security/issue identifier beyond the SIP symbol. Do not assume ticker uniqueness.
4. Reconcile per-facility quantities to the CNMS market-token sets and volume columns. Compare short, short-exempt and total quantities independently; require exact date, symbol, facility coverage and total reconciliation.
5. If the API cannot uniquely distinguish multiple securities sharing a SIP symbol, or if the API and CNMS grains do not reconcile exactly, keep the affected symbol/date quarantined. Do not sum, deduplicate, interpolate or infer identity.
6. Only after the one-date schema and arithmetic checks pass, extend to the six affected dates and then a bounded historical-frequency sample. Historical queries are reconciliation/bootstrap evidence only, not first-seen signal observations.

The Query API response receipt must be timestamped prospectively. Historical retrieval now cannot be backdated into an eligible first-seen event.

## 4. Credential and use-right gate

The existing Phase 447 manual workflow already supports FINRA OAuth client credentials through `FINRA_CLIENT_ID` + `FINRA_CLIENT_SECRET`, or a bearer `FINRA_ACCESS_TOKEN`. Its last recorded controlled live attempt stopped at the credential guard before any FIP/FINRA request. No secret was inspected or changed in this audit.

Before the bounded query, an authorized maintainer must confirm that the appropriate FINRA credential and dataset entitlement are available and that the intended personal/professional/commercial use is permitted by the applicable FINRA API and Equity Data terms. FINRA describes Individual/Public access as intended for individual research and not commercial use; do not use an Individual credential for organization or commercial research without the appropriate authorization.

Separately, FINRA's consolidated Short Interest publication for settlement 2026-11-13 is scheduled for 2026-11-24 and is not yet due at this audit cutoff. The official Developer Center says the dataset is available by 4:40 PM ET (21:40 UTC / 14:40 Hermosillo). No request or dispatch was made.

## 5. Other source disposition

- **SEC Form 4:** natural post-Phase-584 capture succeeded; the 50-page-cap repair is live, but this run needed only 20 pages. Watermarks were found; no signal-eligible observation was admitted.
- **SEC Form 144:** natural capture and post-capture reconciliation succeeded; 477 accessions / 3,360 detail rows, 238 bounded backfills pending, zero signal-eligible filings.
- **CFTC TFF:** 3,043 rows across four index contracts; latest scheduled capture found no new report or revision. Prospective accumulation only; no return inference.
- **FINRA T1 ATS:** date-level publication clock is validated, but MPID concentration is ATS/firm venue concentration, not investor or beneficial-owner concentration. Effective-dated security identity and historical universe/terminal-return gates remain open.
- **Cboe OPRA / OptionMetrics TradeFlow:** still the strongest conditional options-flow family; first-receipt/correction vintages, exact 335-name coverage and explicit strategy-use rights remain unverified.
- **Massive Options:** attractive historical depth for a filtered pilot, but current individual terms restrict use to personal own research and prohibit employer/organization or professional/commercial use; no sample or purchase.
- **SEC MIDAS:** public quarterly exchange-market-structure context only; not dark-pool or institutional-identity flow. Archive payload integrity and per-quarter first-public timestamps remain unverified.
- **SEC 13D/G:** subject-issuer identity rebuild remains quarantined pending the SEC_USER_AGENT prerequisite and full subject-issuer reconstruction.

## 6. Research decision

- New signals admitted: **0**.
- Incremental alpha demonstrated: **none**.
- New OOS / bootstrap / LOO evidence: **none**.
- No raw market data added to the public repository.
- No changes to universe, exposure, costs, holding period, parameters or production.
- `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen.

**Next technical gate:** confirm authorized FINRA API credentials and use rights, then run the one-date / two-symbol `regShoDaily` reconciliation. Keep Phase 469 fail-closed until the row-grain and security-identity ambiguity is resolved.
