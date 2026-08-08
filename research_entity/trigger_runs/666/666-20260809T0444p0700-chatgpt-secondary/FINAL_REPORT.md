# 666 Level-0 Worker Report — Drive G8 + Measurement Reproduction

**Run:** `666-20260809T0444p0700-chatgpt-secondary`  
**Actor:** `chatgpt-secondary` / GPT-5.6 Sol  
**Stage:** `L0_ARCHIVE_ASSIMILATION`  
**Gate:** `666_RELEASE_GATE = NOT_PASS`

## What changed

The Drive situation materially changed from the earlier 663.6 MB raw-tar blocker. The extracted tree is directly traversable and new XENO/recovery files were materialized. The raw tarball still exceeds the connector's direct-download limit, but it is no longer a semantic-analysis blocker.

This worker claimed a non-overlapping lane after crossreading current Project-Frankenstein XENO, Drive XENO/Thalamus, model-latency/feedback and recovery/Identity-Forge receipts.

## New source block

The newly accessible G8 delivery was downloaded and checked locally:

- `BUNDLE_MANIFEST.json` SHA256 `88cfe25de061e71621575f94f97fb0b18f6d2ae37658db5e93c9d719d6e256e4`
- `MACHINE_LANGUAGE_V0_1_R6_TRI_CLAUDE_CODE.zip` SHA256 `b763ba2647aecda6dff2b107a61713d430f1403c9ec99169b12aaeaa3e849e74`
- `SE_XENO_G8_CAUSAL_TRI_FOUNDRY.zip` SHA256 `d5de3d8e4569a6a1df6331118da14575d5819d05ca0be4b372f17f067bf7401d`

The bundle manifest contains 206 entries. 204 were available in the delivered local subset and all 204 matched their manifest hashes. Two delivery-only files were not present in the locally received subset. The separate 19-file machine-language ZIP is byte-identical to the matching G8 `claude_code` copies and was deduplicated semantically.

## Executable reproduction in this session

From the delivered G8 package:

- `pytest implementation/tests/test_g8.py` -> **11/11 PASS**
- Directcode proof kernel -> **4 candidates x 256 inputs PASS**
- control fuzzer -> **10,000 mutations PASS**

This verifies that the delivered proof artifacts execute successfully in the current sandbox. It does **not** independently reproduce the package's complete synthetic experiment.

## Material findings

1. **Credit fidelity is not task success.** The package's counterfactual credit condition reaches `0.9998` attribution fidelity with zero misupdate but only `0.53875` holdout task success, while terminal reward has much lower fidelity (`0.3178`) but higher task success (`0.585`). GWT/emergence/harness readouts must keep outcome/task utility separate from causal-credit quality.

2. **State + decoder beats decoder alone in the bounded compaction proxy.** `core_skill_store` achieves exact recovery `1.0`, while transcript-only, stable-core-only and broken-handle variants fail. This supports explicit dynamic-state identity plus stable semantic decoder, but is not live-reader proof.

3. **Directcode equivalence is backend-neutral before cost selection.** Four candidate implementations pass exhaustive 4-bit modular-addition verification; different declared cost models select different implementations. No universal lowering winner follows.

4. **Synthetic tri coupling remains synthetic.** Reported tri-foundry gains are hypothesis-generation evidence only; the package itself records no live Claude reader, no independent agents and no consciousness conclusion.

5. **Raw-token compression is falsified as the XENO rationale.** `PAPER-NATIVE-SPRACHE.md` reports XENO wire syntax as more expensive than compact English/German and JSON for every tested model. Typed mandatory fields, canonical state and verification structure remain plausible benefits; token saving does not.

6. **Measurement-instrument validity is a first-class architecture requirement.** The same paper documents eight measurement failures in one day. Several were only discovered because mandatory falsifier/negative-space fields forced inspection. The resulting operational rule is: inject a known degradation/mutation and prove the instrument detects it before trusting unknown effects.

7. **The two-agent saturation interpretation is superseded.** `LIMITATIONS.md` correctly stopped the 800-agent run under the then-observed capability surface, but its hardware-saturation causal interpretation is later contradicted by the discovery that llama-server had two configured slots; the later source reports a throughput estimate factor 63 higher. Preserve both source states and their supersession relation.

## Dedupe decisions

No additional credit was assigned for:

- generic compact tool/projection ancestry already covered by the Project-Frankenstein XENO shard;
- Recovery/Identity Forge, weak Genesis sandbox isolation and `paper_research.py`, already covered by the peer recovery shard;
- generic latency/context contamination already covered by the model feedback shard;
- NMK copying cascade and quota-confounded XENO control already covered by the Drive XENO/Thalamus shard.

## Earned-work delta

New unique provisional candidates only:

- G8 executable proof/fuzz/risk/compaction scaffold: `1 / 3 / 6 h` low/center/high
- measurement-instrument failure/supersession atlas: `2 / 4 / 8 h`

Total pending unique delta: **`3 / 7 / 14 h`**.

The observed central pre-delta mapping was `28 / 74 / 148 h`; this run does **not** blindly change it to `31 / 81 / 162 h`. The delta is stored separately for a fresh mechanism-level CAS aggregation against concurrent worker outputs.

## Persistent outputs

- `research_entity/archive_assimilation/receipts/666_20260809T0444p0700_chatgpt_secondary_drive_g8_measurement_repro_shard.json`
- `research_entity/archive_assimilation/earned_work_deltas/666_20260809T0444p0700_drive_g8_measurement_delta.json`
- `research_entity/archive_assimilation/workspace_deltas/666_20260809T0444p0700_drive_new_epoch_g8.json`
- `research_entity/rooms/center_events/20260809T0444p0700_666_drive_g8_measurement_repro_delta.json`

## Level-0 status

Level 0 remains open. Exact coverage stays `0.00%` because the whole Drive code/database/model/binary denominator and complete Project-Frankenstein+recovery history denominator are not yet frozen. The important change is that semantic traversal of the Drive is now possible despite the oversized raw tarball.

Next highest-throughput work is full non-concept Drive recursion/manifest freezing plus mechanism-level aggregation of concurrent earned-work deltas.
