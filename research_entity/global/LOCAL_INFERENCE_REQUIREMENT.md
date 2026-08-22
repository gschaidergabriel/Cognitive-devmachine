# Mini Entity — Local Inference Requirement

Status: CURRENT
Date: 2026-08-22
Program: BLOGPOST_ENTITY_ALL_IN_ONE

The application-neutral Mini Entity pipeline must support interchangeable inference backends without resetting its SQLite MiniUnifiedDB identity, history, evidence consumption or narrative continuity.

Required modes:

1. `remote_api` — configurable remote text-generation endpoint.
2. `local_server` — localhost/OpenAI-compatible text-generation service with optional authentication.
3. `local_model` — direct local model attachment with no remote service required. First reference target: GGUF through a llama.cpp-compatible runtime. Runtime configuration belongs in SQLite and includes model path, context size, threads, GPU layers and generation parameters.

The model is replaceable inference substrate, never application identity. Zero/blog/personality semantics remain fully replaceable SQLite configuration. The executable remains the neutral processing pipeline: evidence -> preprocessing -> canonical envelope -> configured inference -> generic gates -> exactly-once/CAS -> atomic SQLite persistence.

`go` must treat direct local-model support as a required acceptance frontier until it is implemented and sandbox-tested.
