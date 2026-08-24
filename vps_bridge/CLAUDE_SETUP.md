# Claude Code: install the ChatGPT ↔ VPS development bridge

You are on the user's Ubuntu 24.04 VPS. Your job is to install a durable, pull-only development bridge so ChatGPT can submit isolated development jobs through the private GitHub repository and receive exact results back through GitHub.

## Goal

After setup, ChatGPT must be able to create JSON tasks on branch `gpt56sol/vps-chatgpt-bridge-20260824` under `vps_bridge/inbox/`. A local service on the VPS polls that branch, executes each task **inside an isolated Podman sandbox**, and pushes a compact result JSON to `vps_bridge/outbox/`.

The sandbox must have outbound internet access and a `webfetch` helper so jobs can directly download public GitHub tools, source archives, model artifacts, Hugging Face files, documentation, test fixtures, and other required public resources. Large downloaded assets live on the VPS under persistent `/models`, `/cache`, and `/tools` mounts and are never committed accidentally.

## Important design boundary

This bridge is a development execution surface. It is not a second EntityOS/HCU authority and it must not mint canonical whole-product/runtime/training credit by itself. Current Research `main` must still be refreshed before promotion claims.

## Security / isolation requirements

Do **not** expose a listening HTTP/SSH port for the bridge. It must be pull-only through GitHub.

Do **not** mount `/`, `/root`, `/etc`, `/var/run/docker.sock`, `/run/podman/podman.sock`, host SSH keys, or GitHub credentials into task containers.

The GitHub credential stays host-side and is used only by the bridge runner for pull/push. Containers get no `GH_TOKEN`.

Use a dedicated non-sudo Linux user `claybot`. Use rootless Podman. Sandbox containers must use `--cap-drop=all`, `no-new-privileges`, CPU/memory/PID limits, and only these persistent mounts:

- task worktree -> `/workspace`
- `/srv/clay-gpt/cache` -> `/cache`
- `/srv/clay-gpt/models` -> `/models`
- `/srv/clay-gpt/tools` -> `/tools`

Outbound network is allowed. No inbound published ports.

## Execute now

From a checkout of branch `gpt56sol/vps-chatgpt-bridge-20260824`:

```bash
cd vps_bridge
sudo bash install_bridge.sh
```

If the installer reports `GITHUB_AUTH_REQUIRED`, authenticate the already-authorized GitHub account once on the VPS:

```bash
gh auth login
sudo bash install_bridge.sh
```

Do not paste a token into chat or commit it. The installer may reuse the local `gh` login and writes the token only to a root-owned local credential file for the `claybot` service.

## Definition of done

Do not stop at package installation. Verify all of the following:

```bash
sudo systemctl is-active clay-gpt-bridge.service
sudo journalctl -u clay-gpt-bridge.service -n 80 --no-pager
sudo -u claybot env XDG_RUNTIME_DIR=/run/clay-gpt podman image exists localhost/clay-gpt-dev:ubuntu24
```

The control branch already contains `vps_bridge/inbox/SELFTEST_BOOTSTRAP.json`. Wait until the service consumes it and pushes:

`vps_bridge/outbox/SELFTEST_BOOTSTRAP.json`

That outbox result must show exit code `0`, no timeout, successful internet/webfetch access, and the sandbox profile.

Then leave the service enabled and running. Do not delete the control checkout, canonical checkout, model/cache/tool stores, or bridge state.

## What this gives ChatGPT

ChatGPT can then submit jobs without needing a direct SSH connector. The private GitHub branch becomes a narrow command/result mailbox. The VPS runs the work in a rootless sandbox, keeps large assets locally, and pushes back exact logs/receipts/commit SHAs. ChatGPT can inspect those outputs and submit the next job in the same development loop.

## Final response to the user

Report only:

- service state;
- self-test PASS/FAIL;
- VPS bridge root path;
- the outbox path for `SELFTEST_BOOTSTRAP`;
- any blocker that remains.

Do not reveal tokens, credential files, or secret values.