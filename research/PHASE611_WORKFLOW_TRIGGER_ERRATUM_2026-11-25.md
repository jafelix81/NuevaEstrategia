# Phase 611 operational erratum — live SEC workflow trigger

**Date:** 2026-11-25  
**Scope:** workflow safety and reproducibility; no change to timestamp sample results.

## Finding

The original Phase 611 live-job condition was:

`github.event_name == 'push' || (github.event_name == 'workflow_dispatch' && inputs.run_live_audit == true)`

This meant every matching push to the research branch could run the live SEC download, despite the report describing a dispatch-only gate. The successful live audit in [Run 45535351139](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45535351139) was a push-triggered run. Its 48 filing-detail checks and artifact remain valid. The later PR run [45535594622](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45535594622) ran offline regressions and skipped the live job.

## Correction

The live job now requires both:
- `github.event_name == 'workflow_dispatch'`
- `inputs.run_live_audit == true`

Push and pull-request events execute offline regression only. A unit test reads the workflow file and fails if the live condition again admits a push event.

## Decision

- Preserve the completed 48/48 timestamp sample.
- Do not rerun the live SEC audit for this correction.
- Do not change the research data, signal eligibility, production, capital, exposure, or baseline.
- Any future live SEC audit requires an explicit manual dispatch with the boolean input set to true.
