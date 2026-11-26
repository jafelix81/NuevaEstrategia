# Smart Money Research state addendum — Phase 635 (2026-11-26)

**Main merge commit:** `11c2f1acb578784456bc30f82f131ed8fb858c32`

- Phase 635 / [PR #243](https://github.com/jafelix81/NuevaEstrategia/pull/243) merged after hosted run [45786202161](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45786202161) passed **37/37** offline tests.
- Phase 614 now prefers a valid repository `SEC_USER_AGENT` secret and falls back to the established `phase401.SEC_UA` project contact if the secret is missing or placeholder-like. It still fails closed if both are invalid; the User-Agent is not printed or persisted.
- The original failure [45751086501](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45751086501) stopped before any SEC request because the secret was empty. No data were lost or written by that run.
- PR CI's live-capture job was skipped. The next natural scheduled Phase 614 poll is required to validate the fallback against all four Atom feeds. No manual poll was dispatched.
- Phase 611's existing fallback was a separate code path; Phase 635 explicitly aligns Phase 614 with that existing contract.
- SEC 13F historical holdings/identity/acceptance chain #221–#230 remains Draft/unmerged. No 13F signal is admitted.
- SEC 13D/G parent retrieval remains a separate historical identity gate.
- FINRA Reg SHO remains quarantined for BCPC/TPC facility-grain conflicts; CFTC TFF remains a possible broad-market regime covariate, not stock-level flow.
- No new alpha, valid incremental OOS, bootstrap or LOO result. `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen.
- Options/data-purchase budget remains USD 0. No vendor contact or purchase.
- No universe, exposure, cost, parameter, holdout or production changes.

Full report: [Phase 635](PHASE635_SEC_13F_USER_AGENT_FALLBACK_RECONCILIATION_2026-11-26.md).
