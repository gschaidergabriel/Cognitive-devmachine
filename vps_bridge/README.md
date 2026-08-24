# Direct VPS control plane — no Drive, no GitHub worker

This branch is a **mailbox**, not project authority.

Transport:

`ChatGPT GitHub connector -> chatgpt-vps-control branch -> VPS git poller -> rootless Podman sandbox -> chatgpt-vps-results branch -> ChatGPT`

No GitHub Actions/worker is required. The VPS talks directly to GitHub with a dedicated SSH deploy key.

## Branch ownership

- `chatgpt-vps-control`: ChatGPT writes unique command files. VPS is read-only on this branch by policy.
- `chatgpt-vps-results`: VPS publishes LIVE telemetry + receipts. ChatGPT reads it.

## Command path

`vps_bridge/commands/<command_id>.json`

Example:

```json
{
  "schema": "CLAY_VPS_COMMAND/v3",
  "command_id": "go-example-001",
  "op": "exec",
  "cwd": "/workspace",
  "command": "uname -a && free -h && df -h",
  "timeout_seconds": 300
}
```

Supported operations planned by the daemon:

- `exec`: arbitrary shell inside rootless container
- `fetch`: download URL directly in sandbox, optional SHA-256 check
- `git`: clone/fetch repo in sandbox
- `repo_artifact`: copy an artifact/path from a Git checkout into sandbox
- `snapshot`: tar.zst selected sandbox paths and preserve on VPS
- `status`: emit detailed sandbox/host-safe telemetry

The security boundary is host vs rootless container. `exec` is intentionally broad **inside** the container and must never execute arbitrary command text as host root.

Large public tools/models should be downloaded directly by the VPS from their original URL, not transported through GitHub.
