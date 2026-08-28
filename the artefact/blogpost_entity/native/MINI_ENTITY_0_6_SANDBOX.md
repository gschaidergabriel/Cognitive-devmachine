# Native Mini Entity 0.6 sandbox reference

Date: 2026-08-22
Status: sandbox reference, not final release acceptance

The current credited native sandbox executable is an application-neutral and inference-neutral Linux x86-64 ELF named `mini_entity.clay`.

Version label: `mini-entity/0.6.0`

Current credited sandbox SHA-256 after the unified-preset retest:

`27ad1fc3f134efacabe89102a86ac5876d62bb7c9d9b1e6d0ca95c36c60e7bd1`

## Same-version artifact collision

Git history records at least two additional ELF identities under the same `mini-entity/0.6.0` label:

- `939784dd29514ead0721882e83fc78b6d21373e8281774c683cebc6cd92ae7a7` — local-inference sandbox receipt;
- `2aa8ebe9d20a683b62627cfe9e20f245390b1422afaa805b42b2dddbc976eed3` — initial local-LLM receipt / original native reference;
- `27ad1fc3f134efacabe89102a86ac5876d62bb7c9d9b1e6d0ca95c36c60e7bd1` — later unified-preset retest and current `PROGRAM_STATE` identity.

These hashes are **not interchangeable artifact identities**. The audit does not infer why the bytes differ: without the exact source/build inputs for each artifact, source changes cannot be distinguished from build-environment changes. Therefore the version string is descriptive metadata only; release identity is the exact ELF digest plus source/build provenance.

Build dependencies used in the historical sandbox reference:

- C compiler;
- SQLite3;
- libcurl;
- json-c.

Historical compile shape:

`gcc -O2 -Wall -Wextra -o mini_entity.clay mini_entity.c $(pkg-config --cflags --libs sqlite3 libcurl json-c)`

## Reproducibility boundary

The compile shape names `mini_entity.c`, but the canonical `main` tree observed on 2026-08-22 does not currently contain `the artefact/blogpost_entity/native/mini_entity.c` and does not contain the credited ELF bytes. Therefore the `27ad...` receipt remains valid bounded sandbox evidence, but **the current repository cannot independently rebuild or byte-verify that exact native artifact yet**.

This is an acceptance blocker for reproducible native release identity, not evidence that the recorded sandbox behavior failed.

The next native acceptance run must use `build_native_bound.py` (or an equivalently strict admitted builder) to bind in one receipt:

- exact recoverable source bytes + source SHA-256;
- exact compiler identity;
- pkg-config dependency versions/flags;
- deterministic build inputs/environment;
- at least two same-environment builds with identical ELF SHA-256;
- linked runtime-library identities;
- final published ELF SHA-256/build-id;
- exact runtime acceptance evidence for that same ELF.

Cross-environment reproducibility remains a separate stronger claim and requires an independent rebuild from the same recorded inputs.

## Binary/application separation

The executable has no immutable Zero/blog/Gasthaus application identity. A fresh DB is neutral.

Editable SQLite configuration includes system prompt, arbitrary application blob, `profile.*` fields, gates and inference settings. `preset-apply` imports a JSON preset without resetting generation/history.

## Inference modes

### API

Configurable endpoint, model, token, auth header/prefix, request template, response JSON pointer and generation parameters. Loopback HTTP may be tokenless for local OpenAI-compatible servers.

### local_exec

`set-local-model FILE` selects local weights and local inference mode.

`set-local-runner-json JSON` stores an argv array with placeholders:

- `{{MODEL_PATH}}`
- `{{PROMPT_FILE}}`
- `{{MAX_TOKENS}}`
- `{{TEMPERATURE}}`

The runner is invoked directly with exec-style semantics, not through a shell. Its stdout becomes model output and then enters the same immutable gate/exactly-once/CAS/atomic-persistence path as API output.

No API token is required in local mode.

## Preset schema

`preset-apply` admits the unified `clay-pipeline-profile/v2` shape. Application identity/personality and inference selection can therefore live in one replaceable preset. API secrets are forbidden inside presets.

## Sandbox evidence

A fixture local model path + fixture runner completed one full run for the currently credited receipt:

- application preset: Zero blog;
- inference: local_exec;
- API token: missing;
- output persisted;
- generation: 1;
- pending events after commit: 0;
- SQLite integrity check: `ok`.

Receipts:

- `../receipts/2026-08-22_NATIVE_MINI_ENTITY_V0_6_LOCAL_LLM.json`
- `../receipts/2026-08-22_GO_NATIVE_ARTIFACT_IDENTITY_RECONCILIATION_GPT56SOL.json`

This proves bounded backend transport/state semantics only. A real GGUF/llama.cpp-compatible model run remains required for model-quality acceptance.
