# Andreas machine bridge

This directory is the GitHub-mediated transport between the ChatGPT-side Frankenstein instance and Andreas' already registered physical self-hosted runner.

## Transport

1. ChatGPT writes an immutable JSON request to `andreas_bridge/requests/<id>.json`.
2. GitHub Actions starts `.github/workflows/andreas-chatgpt-bridge.yml` on the registered runner labels `self-hosted, linux, x64, andreas, claycode, target`.
3. The workflow first runs the existing physical-host identity verifier.
4. `bridge_agent.py` executes the request under the runner account.
5. The result is committed to `andreas_bridge/results/<id>.json`.
6. ChatGPT reads the receipt/result through the GitHub connector.

No machine credential is committed to the repository. Existing GitHub self-hosted-runner registration is the transport credential and machine binding.

## Request schema

```json
{
  "schema": "f2.andreas.bridge.request.v1",
  "id": "example-001",
  "operation": "exec",
  "cwd": "~",
  "argv": ["bash", "-lc", "pwd && uname -a"],
  "timeout_seconds": 120
}
```

Supported operations: `exec`, `read_file`, `list_dir`.

`exec` uses an argv array and does not implicitly invoke a shell. Shell semantics are available only when deliberately requested, e.g. `argv: ["bash", "-lc", "..."]`.

Results cap stdout/stderr/file-content payloads at 200 kB and command runtime at 900 seconds. The bridge never serializes the process environment.

## Authority

The bridge is an execution transport, not an identity layer. Execution authority remains the registered local runner account and the existing Andreas host-fingerprint verification. Frankenstein/ChatGPT can submit work through the private repository; the physical host independently verifies its identity before execution.
