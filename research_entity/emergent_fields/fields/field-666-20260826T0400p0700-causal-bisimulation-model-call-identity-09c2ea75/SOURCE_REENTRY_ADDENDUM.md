# Source Re-entry Addendum — Existing HCU Invocation Identity Changes the Conclusion

## Re-entry result

The field's strongest counterhypothesis was tested against the retained HCU donor lane (`PR #1263`). It is **partly confirmed** and materially sharpens the result.

At current PR #1263 head `84006a96e1d5591893ac226d841fd5f0d0a839e1`:

- `model_execution_receipt_v1.py` already models an actual executor occurrence with `executor_id` + `invocation_id`;
- an external invocation registry binds that executor-scoped invocation key to exactly one admitted observation digest;
- the observation binds generation, verified engine-load consumption receipt, GRID plan, output-producing cell/role, input bytes and output bytes;
- reusing one invocation identity for a different observation/output therefore fails closed;
- `VerifiedModelExecution.inference_echo()` exports executor/invocation identity plus observation/receipt/output/grid bindings downstream;
- `inference_receipt_v1.py` is already `HCU_INFERENCE_RECEIPT/v4` and consumes a separately verified/admitted `VerifiedModelExecution` rather than accepting output bytes as independent caller assertions.

This means EntityOS/HCU already has the right **occurrence-identity mechanism class** in its retained donor. A new independent `model_call_event_id` authority would duplicate it and violate the single-authority design law.

## Revised finding

The source-observed Trigger-2 `CLAY_TRIGGER2_MODEL_CALL_BINDING/v2` remains a deterministic **content binding**. That is not a defect by itself.

The real integration question is:

> Does every Trigger-2 model-call result that may later influence checkpoint selection, NODE_RESULT, J-Space/evaluation or training admission get wrapped into / cross-bound to the existing HCU `VerifiedModelExecution` executor+invocation occurrence identity before promotion?

Current Trigger-2 source/tests establish content sensitivity (checkpoint/input/runtime/output), but the inspected Trigger-2 call-binding source does not itself expose the HCU executor/invocation admission registry. Therefore the safe conclusion is a **bridge/provenance integration gap candidate**, not a missing global identity primitive.

## Revised design law

Keep two levels, but reuse existing authority:

1. `model_call_binding_sha256` / content digest — deterministic content-equivalence identity;
2. HCU `VerifiedModelExecution` (`executor_id`, `invocation_id`, admitted observation digest) — canonical execution-occurrence identity.

Promotion-bearing downstream evidence should bind both.

Required semantics:

- distinct executor/invocation occurrences may share the same content digest without collapsing causal lineage;
- exact replay of one admitted invocation remains idempotent;
- same executor/invocation + different observation/output remains fail-closed;
- Trigger-2 content digest transplanted onto a foreign `VerifiedModelExecution` must reject;
- `NODE_RESULT` / J-Space / evaluation / dataset admission must not infer occurrence identity from content hash alone.

## What was falsified

The broad hypothesis "EntityOS/HCU lacks occurrence identity for model execution" is **falsified at retained donor source scope**.

The narrower hypothesis "Trigger-2's new content-binding/evaluation path may not yet be explicitly fused to the existing HCU occurrence identity before downstream promotion" remains **OPEN / SOURCE-INTEGRATION AUDIT REQUIRED**.

## Evidence boundary

This is source re-entry and architecture fusion only. No exact current HCU donor runtime, model runtime, GRID10 runtime, provider execution or training execution was performed. All runtime/model/training credits remain zero.

## Next exact discriminator

Trace one concrete future Trigger-2 evaluation row from:

`checkpoint/input/output content binding -> VerifiedModelExecution executor+invocation occurrence -> HCU_INFERENCE_RECEIPT/v4 -> NODE_RESULT/J-Space/evaluation -> dataset admission`

and require exact cross-binding at each step. If such a source path already exists, close this field as `MERGED_INTO_EXISTING_IDENTITY_AUTHORITY_NO_NEW_PRIMITIVE`. If not, add only the minimal adapter/cross-binding into the existing authority path and regress content/occurrence transplant plus replay-conflict cases.
