# GO research receipt — Q23 temporal FeatureEpoch parity

Run: `go-20260811T2029p0700-chatgpt-secondary-q23-temporal-feature-epoch`
Actor: `chatgpt-secondary` / OpenAI / GPT-5.6 Sol
Program: `FRANK_V0_1`
Work package: `F-V01-06-DIGITAL-RETINA-MVC`
Architecture promotion: **NONE — TESTING ONLY**

## Fresh coordination

Target candidate was branched from `gschaidergabriel/Dr.-Unterweger@2bdeb35d722417a1c2d9b71a3b3ac9125acf46c3`. Before branch creation, no open PR was found for q23 visual FeatureEpoch temporal-policy parity. Existing ClayCode, storage/recovery, loop-core/GWT, token-API, effect and agency work was not duplicated.

The shared Clay GO state was refreshed again before this write; latest observed GO commit was `9fcefc141e721cf6d79d945ade9b7a359274c150`.

## Measured implementation drift

The authoritative ClayCode type `VisualFeatureEpoch` in `claycode/frank_visual_embedding_gate.clay` already contains `temporal_policy_hash` and requires stale FeatureEpoch prototype reuse to fail closed.

The current-main Python reference oracle `runtime/q23_visual_embedding_gate_v1/target_vps_probe.py::FeatureEpoch` omitted `temporal_policy_hash`.

Therefore the reference/runtime compatibility identity was weaker than the ClayCode semantic identity.

## Hypothesis

Binding `temporal_policy_hash` into the Python FeatureEpoch restores parity with ClayCode and prevents silent MVC prototype reuse across temporal/frame-processing policy changes.

## Strongest counterhypothesis

For a strictly still-image-only operating subset, temporal policy may be observationally irrelevant and the extra identity dimension may invalidate prototypes unnecessarily. The field should remain conservative by default and may be weakened only after controlled descriptor-invariance, prototype-transfer and open-set calibration evidence.

## Fresh external mechanism check

Current `llama.cpp` server code reads `mtmd_batch_get_output_embd(...)` immediately before `mtmd_helper_decode_image_chunk(...)`, preserving the concrete shared-feature tap previously identified by q23. Current libmtmd also models Qwen-VL M-RoPE and temporal merge state. Recent Qwen3.5 multimodal issue evidence remains configuration-sensitive; it is treated as transfer-risk input, not as proof about Frank's exact target configuration.

## Exactly one GO out-of-box experiment

`TEMPORAL_POLICY_EPOCH_ALIAS`

Design: construct two FeatureEpochs identical on every pre-fix field and different only in temporal policy. Recompute the exact old identity domain with the temporal field omitted, then compare against the repaired identity.

Independent local micro-replication:

- old identity aliases the two temporal policies: **PASS / counterexample reproduced**;
- repaired identity separates them: **PASS**.

The target candidate additionally requires an old prototype to be rejected as stale under the changed temporal policy.

## Built candidate

Target branch: `chatgpt/go-q23-temporal-feature-epoch-fence-20260811`

Commits:

- `da0824c0ed4a82d7f40cb5068eb3ef9d327646eb` — bind temporal policy into Python FeatureEpoch and add the sole GO falsifier;
- `bab997be54d144ef363efea7b17c41c8a0578480` — add isolated exact-SHA self-hosted Linux/X64 target workflow.

Draft PR: `gschaidergabriel/Dr.-Unterweger#328`

Fresh-main compare at last check: `ahead_by=2`, `behind_by=0`, two changed files only.

## Execution state

Local independent temporal-alias micro-falsifier: **PASS**.

Accepted-target self-hosted candidate receipt: **NOT OBSERVED YET**. Therefore target evidence credit is **ZERO** and PR #328 remains draft.

A repo-wide hosted Deep Integrity PR job reported failure with zero executed steps, matching a previously documented infrastructure-only failure pattern. It is neither PASS evidence nor a candidate falsification.

## Non-claims

No real Qwen3.5-4B embedding or libmtmd buffer was measured in this candidate cycle. No decoder bypass was promoted. No claim is made that temporal policy always changes descriptors. The original Retina remains `BASELINE_PARTIAL_ARCHAEOLOGY`, so no Retina-replacement claim is permitted.

## Next falsifiers

1. Obtain and inspect the self-hosted target receipt for PR #328; debug rather than promote if it is absent or red.
2. Recheck fresh-main ancestry and overlap before any merge decision.
3. Refresh the accepted-target multimodal runtime inventory; if exact Qwen3.5-4B + matching mmproj/libmtmd exists, bind exact identities and run the FeatureEpoch invariance matrix.
4. Run q23 E0 versus E>0 experience dose-response only after real provenance-bound visual fixtures exist.
5. Re-execute the historical Retina baseline before any replacement decision.

Training authorization was not consumed. Whole Frank v0.1 acceptance is not claimed.
