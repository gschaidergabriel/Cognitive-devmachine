# Mini Entity — Local Inference Requirement

Status: CURRENT
Date: 2026-08-22
Program: MINI_ENTITY_PIPELINE_ALL_IN_ONE

The application-neutral Mini Entity pipeline must support interchangeable inference backends without resetting its SQLite MiniUnifiedDB identity, history, evidence consumption or narrative continuity.

Required modes:

1. `remote_api` — configurable remote text-generation endpoint/model/auth/request/response mapping.
2. `local_server` — localhost/OpenAI-compatible text-generation service with optional authentication; tokenless loopback is permitted when explicitly configured.
3. `local_exec` — direct local model attachment with no remote service or API token required. Reference target: GGUF through llama.cpp-compatible or another configured runner.

Local runtime configuration belongs in SQLite and includes model path, runner argv template, optional local prompt template and generation parameters. Runner invocation must not pass through a shell.

The model is replaceable inference substrate, never application identity. Zero/blog/personality semantics remain fully replaceable SQLite configuration. The executable remains the neutral processing pipeline:

`evidence -> preprocessing -> canonical envelope -> configured inference -> generic gates -> exactly-once/CAS -> atomic SQLite persistence`

## Current evidence

Sandbox native `mini-entity/0.6.0` has implemented and contract-tested `local_exec` using:

- `inference_mode=local_exec`;
- readable local model path;
- JSON argv runner configuration;
- direct exec-style runner invocation with no shell;
- no API token;
- normal immutable gate path;
- exactly-once event consumption;
- generation/CAS persistence;
- SQLite `integrity_check = ok`.

Receipt:

`the artefact/blogpost_entity/receipts/2026-08-22_NATIVE_MINI_ENTITY_V0_6_LOCAL_LLM.json`

This proves the local-model transport/persistence contract with fixture weights/runner. It does not yet prove quality or compatibility of a real GGUF model. Final local-model acceptance requires at least one actual supported local LLM run.

`go` must now treat real local-model acceptance and convergence of the structured Clay runtime onto the same backend contract as active frontiers, not re-open the already-proven transport contract without new evidence.
