# Harness Follow-up — Real Drive Needle Sandbox Probe

Run: `harness-20260809T1825p0700-chatgpt-secondary-needle-drive-probe`  
Actor: `chatgpt-secondary` / OpenAI / GPT-5.6 Sol  
Canonical parent: `r2 · 04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`  
Work package: `H-WP-04-NEEDLE-BOUNDARY`

## Why this run happened

The project owner clarified that Needle is small and its source is in Google Drive, so the prior H-WP-04 adapter-only evidence was extended with execution against the actual Drive Needle code and Frank tool registry.

## Real source recovered

The Drive contains the upstream Needle repository plus Frank's Needle zero-shot design and registry. The zero-shot design fixes the intended operating mode as unchanged official Needle with the tool list supplied dynamically at runtime, no project-specific Needle finetuning, and hard gates for encoder budget, German zero-shot behavior and constrained-name binding.

## Executed sandbox probe

Actual Drive `constrained.py` and Frank `registry.json` were loaded into the ChatGPT Linux sandbox and the real ToolConstraints/masking behavior was exercised.

Observed result:

- 51 active Frank tools after the 62-total / 11-blocked registry split;
- allowed tool-name trie matches the supplied runtime list;
- first-character masking matches the supplied tool universe;
- a valid supplied tool can reach its terminal quote;
- an invented tool-name prefix is rejected by the constrained path;
- the project alias `calc.ausdruck -> calc.expression` is representable;
- full-description 51-tool JSON produced by this probe is 10,923 characters.

This provides direct executable support for design gate 0c: constrained decoding can structurally bind generated tool names to the runtime-supplied list once the decoder is in the tool-name span.

## New adapter counterexample

The Drive constrained decoder iterates the dictionary under each tool's `parameters` field as the allowed argument-key map. The upstream Needle examples use direct maps such as:

`parameters: {location: {type: string, ...}}`

A standard OpenAI nested schema such as:

`parameters: {type: object, properties: {location: {...}}, required: [location]}`

therefore yields `properties` as the constrained argument key in this Drive snapshot instead of `location`.

This is an H1 adapter/schema-contract issue, not evidence that the Needle model itself is defective. The FRANK->Needle wrapper must normalize/flatten nested schemas or construct Needle-native direct parameter maps before constrained decoding.

## What is still not executable in this environment

The accessible Drive source snapshot contains code, docs and registry but no visible `checkpoints/`, `weights/`, `needle.pkl` or `needle-cq4` artifact. Full German zero-shot model inference therefore was not executed in this run.

Needle model size is not the blocker. The blocker is availability of the actual weight/tokenizer blobs through the current connected-file transport. Once the official weight bundle and tokenizer model are present as readable files, the next tests are:

1. exact gate 0a: query + active tool registry < 1024 encoder tokens with >=200-token headroom;
2. hard gate 0b: German zero-shot routing on the frozen five-tool set;
3. 0c model-level constrained-name test in addition to the now-passed decoder-structure test;
4. end-to-end Needle output -> H1 NeedleBridgeReceipt/Clay ingress -> external effect-gate invariant.

## Status

`COMPLETE_EXECUTABLE_PROBE / H-WP-04 REMAINS OPEN`

The prior adapter component remains valid. This run adds real source-code execution, discovers one concrete schema normalization requirement, and removes uncertainty about whether constrained decoding has an allow-list mechanism. It does not yet establish German zero-shot quality or encoder-budget fit.
