# ChatGPT ↔ VPS bridge protocol

Control branch: `gpt56sol/vps-chatgpt-bridge-20260824`

## Submit

Create one new file:

`vps_bridge/inbox/<TASK_ID>.json`

with:

```json
{
  "schema": "CLAY_VPS_TASK/v1",
  "task_id": "EXAMPLE_001",
  "base_ref": "main",
  "command": "set -euo pipefail\npython3 -m unittest discover -v",
  "timeout_sec": 3600,
  "cpus": 4,
  "memory": "12g",
  "pids_limit": 4096,
  "min_free_gb": 20,
  "network": true,
  "commit_changes": true,
  "commit_on_failure": false
}
```

`base_ref` may be `main`, another remote branch, or `pr/1263` for a GitHub pull-request head.

The command executes only inside the rootless Podman development image. Its working directory is `/workspace`. Persistent writable stores are `/cache`, `/models`, and `/tools`.

Useful download helpers inside the sandbox:

```bash
webfetch URL DEST [EXPECTED_SHA256]
hffetch REPO_ID FILENAME DEST [REVISION] [EXPECTED_SHA256]
```

Examples:

```bash
webfetch https://github.com/ggml-org/llama.cpp/archive/refs/heads/master.tar.gz /cache/llama-master.tar.gz
hffetch Qwen/Qwen3-0.6B-GGUF Qwen3-0.6B-Q8_0.gguf /models/Qwen3-0.6B-Q8_0.gguf 1eaf4d9657fe65ad10a51eab76a8db5b363bddaa 9465e63a22add5354d9bb4b99e90117043c7124007664907259bd16d043bb031
```

## Receive

The VPS pushes:

`vps_bridge/outbox/<TASK_ID>.json`

The result includes exact base SHA, process exit code, timeout state, elapsed time, local full-log paths, SHA-256 of stdout/stderr, bounded log tails, changed-file status and—when requested and successful—the pushed development branch + commit SHA.

Large binaries/models stay on the VPS. Do not base64 them into GitHub. Put them in `/models`, `/cache`, or `/tools` and return exact path/hash/byte metadata.

## Isolation contract

Task containers never receive the bridge GitHub token. They do not mount host root, host SSH keys, Docker/Podman sockets, or arbitrary host paths. No ports are published. Internet egress is available unless the task sets `network:false`.

## Development rule

Use the bridge aggressively for experiments, builds, model downloads and tests. Keep canonical admissions and product/runtime/training promotion separate: exact sandbox evidence is evidence, not automatic authority promotion.
