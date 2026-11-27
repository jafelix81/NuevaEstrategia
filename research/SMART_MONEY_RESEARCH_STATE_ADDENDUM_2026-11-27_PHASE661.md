# Smart Money Research state addendum — Phase 661

**2026-11-27 10:02 UTC**

- Phase 661 implements persistence of a volume-bearing FINRA CNMS symbol panel for conservatively eligible first-seen/late-first-seen files only.
- The panel is filtered to the exact static 335-ticker reference snapshot (commit `1aa1b91f383ce9cef375a43e775c736a27356a5`; SHA-256 `f850655a22a8843dad90e9562b3152b9ca064560586109022b5bfd205a003dda`). This is a fixed symbol filter, not historical F80 constituent certification.
- Panel rows retain short volume, exempt volume, total volume, ratios, market tokens, row/file hashes, schema/grain, URL, and the conservative poll interval. The first-seen upper bound is not an exact public-release timestamp.
- Duplicate-symbol quarantine remains fail-closed; unique symbols can be retained in partial files. Bootstrap, manual, unchanged and revision observations are not persisted as eligible panel rows. Append is idempotent by trade-date/symbol/file-hash.
- Merged to `main` in commit `00016c90b3452e1de060f413f4ea446a1b37449f`. Final PR validation [45978861267](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45978861267): 65/65 offline tests passed; live-capture skipped as expected on PR.
- Production panel is not yet populated; the last natural run [45939887443](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45939887443) had seven bootstrap files, one 403, and zero eligible observations.
- Next: wait for the next natural scheduled capture on `main`; no manual dispatch. Do not use the new panel for an economic test until enough prospective observations, historical identity, price coverage and a defensible OOS design exist.
- No alpha evidence; no price/forward-return analysis, OOS, bootstrap or LOO run. `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen. Data budget USD 0; no vendor contact or purchase.
