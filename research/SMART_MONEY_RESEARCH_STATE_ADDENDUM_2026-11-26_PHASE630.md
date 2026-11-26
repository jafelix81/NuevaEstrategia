# Smart Money Research state addendum — Phase 630 (2026-11-26 03:33 UTC)

**Main HEAD:** `d81c2c65de8853c46c3987570720bbe8d274b626`

- PR #242 / Phase 629 merged at 03:31:23 UTC after 36/36 offline tests. Phase 614 now injects and validates the existing `SEC_USER_AGENT` secret before any SEC request; no secret value was read. Weekday hourly schedule remains `41 * * * 1-5`. No natural 13F scheduled run yet at cutoff; administrative enabled-state is not visible to this connection.
- Latest Form 144 run 45747356670: offline + live jobs passed; 82 new accession events from 84 feed observations, 82 XML resolutions, 14 candidate-manifest issuer matches; 82 bounded collector-observation intervals, but 0 public-availability-certified and 0 signal-eligible. No exact public-release time or intraday use is authorized.
- Form 144 ledger: 815 accessions / 5,443 detail rows; 441 issuer CIKs; 0 parse errors; 5,443 source-hash matches / 0 mismatches. Bounded backfill: 10 attempted, 35 rows appended, 188 remaining.
- Phase 549: 295 formal plan-date accessions (36.2%); 23 positive explicit, 4 negative explicit, 3 ambiguous, 785 no Remarks mention; 126 distinct plan dates; median plan-date-to-notice lag 183 days. Four Fermi sell-to-cover/tax-withholding notices total 2,253,270 proposed units, not executions. No event-return test.
- Form 4 latest natural run 45714679017 succeeded; 415 new metadata events / 912 entity observations; 27 transaction details and 33 footnote references appended; zero signal eligibility. PR #240 remains Draft/unmerged.
- SEC 13D/G PR #241 remains Draft; 30/30 offline tests passed, live 44-header sample skipped. SEC 13D subject-issuer discovery remains the higher research priority than a directional 13F holdings signal.
- FINRA Reg SHO latest run 45550366574: 7/7 daily files rejected for BCPC/TPC duplicate-symbol/facility overlap; zero eligible. CFTC TFF run 45550124780: 3,043 rows unchanged through report date 2026-11-17; zero signal-eligible.
- MIDAS remains conditional market-quality/liquidity context; ZIP payloads, per-quarter PIT and historical F80 identity are unverified. HiddenVol is on-exchange hidden-resting-order activity, not dark-pool volume. Options data budget remains USD 0.
- No new alpha/OOS/bootstrap/LOO result. `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen; no model, universe, exposure, cost, holding-period or production changes.

Full audit: [Phase 630](PHASE630_SEC13F_ACCESS_GUARD_AND_FORM144_POSTCAPTURE_REFRESH_2026-11-26.md).
