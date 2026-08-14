<!-- RAE_META
{"packet_id":"FRANK_QWEN_ACTIONS_QUEUE_TRIGGER_NEGATIVES_20260810","title":"GitHub Actions orchestration negatives from the real-Qwen V2 lane","domains":["frank","harness","model_runtime","security"],"topics":["GitHub Actions","concurrency","queue:max","skip ci","workflow dependency","Qwen4B V2"],"epistemic_class":"OFFICIAL_PLATFORM_SEMANTICS_PLUS_PROJECT_EXECUTION_NEGATIVE","claim_status_hint":"CURRENT","origin_actor":"chatgpt-secondary","created_at":"2026-08-10T01:13:00+07:00","source_refs":["https://docs.github.com/en/actions/concepts/workflows-and-actions/concurrency","https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/control-workflow-concurrency","https://docs.github.com/en/actions/how-tos/manage-workflow-runs/skip-workflow-runs","gschaidergabriel/Dr.-Unterweger@5756eded599770f02c42735647a6715ac0ee369b"],"confidence":"HIGH","verification_required":true,"falsifier_or_next_test":"Materialize the priority V2 receipt and observe that its non-skip receipt commit triggers the V2-gated fresh-context prerequisite without replacing the V2 run itself."}
RAE_META -->

## Negative 1 — shared default concurrency is not a FIFO queue

Current GitHub Actions documentation states that a concurrency group normally permits one running and one pending run, and that a newly queued run replaces/cancels an existing pending run in the same group. Multiple distinct workflows using the same hard-coded group can therefore cancel each other's pending work even with `cancel-in-progress: false`.

This matters directly to the Qwen4B line: V2, calibration and fresh-context work had shared `frank-vps-real-qwen4b-prebuilt`. Later lightweight prerequisite/audit runs could occupy the one pending slot and displace an older pending V2 run. Lack of a V2 receipt therefore could not be interpreted as model failure or even as proof that the intended V2 run reached the runner.

GitHub now documents `queue: max` for preserving multiple pending runs. The canonical post-guard V2 falsifier was therefore moved to the unique group `frank-qwen4b-v2-priority` with `queue: max` in FRANK commit `5756eded599770f02c42735647a6715ac0ee369b`.

## Negative 2 — `[skip ci]` breaks receipt-path dependencies

GitHub officially documents that `[skip ci]` and equivalent instructions suppress workflows triggered by `push` and `pull_request` for that commit. The previous V2 receipt writer used `[skip ci]`, while the downstream fresh-context workflow relied on the canonical V2 receipt path changing to trigger its prerequisite check. Those two choices were contradictory: a successfully written V2 receipt could be present but never automatically awaken the gated dependent workflow.

The priority V2 writer therefore deliberately commits its canonical admitted receipt **without** `[skip ci]`. Its own workflow listens only to its workflow file path, so the receipt commit cannot recursively start another priority V2 run. The downstream fresh-context workflow explicitly listens to `runtime/vps_integrity/real_qwen4b_prebuilt_v2_latest.json`, so the dependency edge is now executable rather than documentary.

## General architecture rule

Separate three concepts instead of overloading one Actions mechanism:

1. **Physical/resource exclusion** — prevent conflicting model processes on the same target.
2. **Scientific dependency** — require an admitted predecessor receipt and revalidate its semantics before the dependent experiment executes.
3. **Workflow queue retention/trigger propagation** — preserve pending runs and ensure receipt commits are not suppressed when they are intended to activate dependents.

A shared concurrency key is not scientific dependency. A path filter is not receipt admission. A successful commit is not a downstream trigger if the commit message explicitly suppresses push workflows.

## Promotion

`NO_ARCHITECTURE_PROMOTION`. This is active infrastructure/experimental-method knowledge. It changes how future evidence is scheduled and admitted, not the scientific status of W4/Qwen/FRANK. The post-guard V2 receipt remains the next discriminating evidence.
