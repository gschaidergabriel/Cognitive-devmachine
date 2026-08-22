# Native Mini Entity 0.6 sandbox reference

Date: 2026-08-22
Status: sandbox reference, not final release acceptance

The current native sandbox executable is an application-neutral and inference-neutral Linux x86-64 ELF named `mini_entity.clay`.

Version: `mini-entity/0.6.0`

Sandbox SHA-256:

`2aa8ebe9d20a683b62627cfe9e20f245390b1422afaa805b42b2dddbc976eed3`

Build dependencies used in the sandbox reference:

- C compiler;
- SQLite3;
- libcurl;
- json-c.

Reference compile shape:

`gcc -O2 -Wall -Wextra -o mini_entity.clay mini_entity.c $(pkg-config --cflags --libs sqlite3 libcurl json-c)`

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

A fixture local model path + fixture runner completed one full run:

- application preset: Zero blog;
- inference: local_exec;
- API token: missing;
- output persisted;
- generation: 1;
- pending events after commit: 0;
- SQLite integrity check: `ok`.

Receipt:

`../receipts/2026-08-22_NATIVE_MINI_ENTITY_V0_6_LOCAL_LLM.json`

This proves backend transport/state semantics only. A real GGUF/llama.cpp-compatible model run remains required for model-quality acceptance.
