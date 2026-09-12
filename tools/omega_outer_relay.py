#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Any

TARGETS = {
    "host:ai-core-node": {
        "machine_id": "ai-core-node",
        "owner": "gabriel",
        "control_branch": "chatgpt-local-ai-core-node-control",
        "results_branch": "chatgpt-local-ai-core-node-results",
    },
    "host:andreas-maco": {
        "machine_id": "andreas-maco",
        "owner": "andreas",
        "control_branch": "chatgpt-local-andreas-maco-control",
        "results_branch": "chatgpt-local-andreas-maco-results",
    },
}
ALLOWED_OPS = {"exec", "status", "read_file", "write_text", "screenshot"}
COMMAND_ID_RE = re.compile(r"^omega-[A-Za-z0-9_.:-]{1,96}$")


class RelayError(RuntimeError):
    pass


class OutcomeUnknown(RelayError):
    pass


def json_bytes(payload: Any) -> bytes:
    return (json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n").encode("utf-8")


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def atomic_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_bytes(json_bytes(payload))
    os.replace(tmp, path)


def run(cmd: list[str], *, cwd: Path | None = None, timeout: int = 120, check: bool = True) -> subprocess.CompletedProcess[bytes]:
    proc = subprocess.run(
        cmd,
        cwd=str(cwd) if cwd else None,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout,
        check=False,
    )
    if check and proc.returncode != 0:
        raise RelayError(
            f"command failed rc={proc.returncode}: {' '.join(cmd[:6])}: "
            + proc.stderr[-1200:].decode("utf-8", errors="replace")
        )
    return proc


class ContainerRuntime:
    def __init__(self, prefix: list[str], container: str) -> None:
        self.prefix = prefix
        self.container = container

    @classmethod
    def detect(cls, container: str) -> "ContainerRuntime":
        candidates = [
            ["podman"],
            ["docker"],
            ["sudo", "-n", "podman"],
            ["sudo", "-n", "docker"],
        ]
        for prefix in candidates:
            try:
                proc = run(prefix + ["inspect", container], timeout=20, check=False)
            except (FileNotFoundError, subprocess.TimeoutExpired):
                continue
            if proc.returncode == 0:
                return cls(prefix, container)
        raise RelayError(f"OMEGA container unavailable: {container}")

    def exec(self, argv: list[str], *, timeout: int = 120, check: bool = True) -> subprocess.CompletedProcess[bytes]:
        return run(self.prefix + ["exec", self.container] + argv, timeout=timeout, check=check)

    def list_outbox(self, spool_root: str) -> list[str]:
        script = (
            "import pathlib;"
            f"p=pathlib.Path({spool_root!r})/'outbox';"
            "p.mkdir(parents=True,exist_ok=True);"
            "print('\\n'.join(sorted(x.name for x in p.glob('*.json') if x.is_file())))"
        )
        proc = self.exec(["python3", "-c", script], timeout=30)
        names = proc.stdout.decode("utf-8", errors="replace").splitlines()
        return [n for n in names if n.endswith(".json") and "/" not in n and "\\" not in n]

    def read_bytes(self, path: str) -> bytes:
        proc = self.exec(["cat", path], timeout=30)
        return proc.stdout

    def write_bytes_atomic(self, path: str, raw: bytes) -> None:
        with tempfile.NamedTemporaryFile(prefix="omega-relay-", delete=False) as f:
            host_tmp = Path(f.name)
            f.write(raw)
        remote_tmp = path + f".tmp.{os.getpid()}"
        try:
            self.exec(["mkdir", "-p", str(Path(path).parent)], timeout=30)
            run(self.prefix + ["cp", str(host_tmp), f"{self.container}:{remote_tmp}"], timeout=60)
            self.exec(["mv", remote_tmp, path], timeout=30)
        finally:
            host_tmp.unlink(missing_ok=True)


class GitMailbox:
    def __init__(self, repo: Path) -> None:
        self.repo = repo
        if not (repo / ".git").exists():
            raise RelayError(f"not a git checkout: {repo}")
        run(["git", "-C", str(repo), "config", "user.name", "OMEGA Outer Relay"])
        run(["git", "-C", str(repo), "config", "user.email", "omega-outer-relay@users.noreply.github.com"])

    def _git(self, *args: str, timeout: int = 120, check: bool = True) -> subprocess.CompletedProcess[bytes]:
        return run(["git", "-C", str(self.repo), *args], timeout=timeout, check=check)

    def fetch(self, branch: str) -> None:
        self._git("fetch", "--no-tags", "origin", branch, timeout=180)

    def show_fetch_head(self, rel: str) -> bytes | None:
        proc = self._git("show", f"FETCH_HEAD:{rel}", timeout=60, check=False)
        if proc.returncode == 0:
            return proc.stdout
        return None

    def read_branch_file(self, branch: str, rel: str) -> bytes | None:
        self.fetch(branch)
        return self.show_fetch_head(rel)

    def publish_exact(self, branch: str, rel: str, raw: bytes) -> None:
        self.fetch(branch)
        existing = self.show_fetch_head(rel)
        if existing is not None:
            if sha(existing) != sha(raw):
                raise OutcomeUnknown(f"mailbox collision at {branch}:{rel}; no automatic replay")
            return

        temp_parent = Path(tempfile.mkdtemp(prefix="omega-worktree-"))
        temp_root = temp_parent / "wt"
        try:
            self._git("worktree", "add", "--detach", str(temp_root), "FETCH_HEAD", timeout=120)
            path = temp_root / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw)
            run(["git", "-C", str(temp_root), "add", rel])
            run(["git", "-C", str(temp_root), "commit", "-m", f"omega outer relay: {Path(rel).stem}"])
            pushed = run(
                ["git", "-C", str(temp_root), "push", "origin", f"HEAD:{branch}"],
                timeout=180,
                check=False,
            )
            if pushed.returncode != 0:
                self.fetch(branch)
                observed = self.show_fetch_head(rel)
                if observed is not None and sha(observed) == sha(raw):
                    return
                raise OutcomeUnknown(
                    "push outcome unresolved; command absent after reconciliation; no automatic replay"
                )
        finally:
            self._git("worktree", "remove", "--force", str(temp_root), timeout=60, check=False)
            shutil.rmtree(temp_parent, ignore_errors=True)

    def wait_receipt(self, branch: str, rel: str, timeout_seconds: float) -> bytes:
        deadline = time.monotonic() + max(1.0, float(timeout_seconds))
        while time.monotonic() < deadline:
            try:
                raw = self.read_branch_file(branch, rel)
            except RelayError:
                raw = None
            if raw is not None:
                return raw
            time.sleep(2.0)
        raise OutcomeUnknown(f"receipt timeout at {branch}:{rel}; no automatic replay")


class OuterRelay:
    def __init__(
        self,
        *,
        runtime: ContainerRuntime,
        mailbox: GitMailbox,
        spool_root: str,
        ledger_root: Path,
        receipt_timeout: float,
    ) -> None:
        self.runtime = runtime
        self.mailbox = mailbox
        self.spool_root = spool_root.rstrip("/")
        self.ledger_root = ledger_root
        self.ledger_root.mkdir(parents=True, exist_ok=True)
        self.receipt_timeout = receipt_timeout

    def _paths(self, command_id: str) -> tuple[str, str, Path]:
        return (
            f"{self.spool_root}/outbox/{command_id}.json",
            f"{self.spool_root}/inbox/{command_id}.json",
            self.ledger_root / f"{command_id}.json",
        )

    @staticmethod
    def validate_envelope(env: dict[str, Any]) -> tuple[dict[str, str], dict[str, Any], str]:
        if env.get("schema") != "OMEGA_OUTER_BRIDGE_COMMAND/v1":
            raise RelayError("invalid outer command schema")
        command_id = str(env.get("command_id", ""))
        if not COMMAND_ID_RE.fullmatch(command_id):
            raise RelayError("invalid command_id")
        organ_id = str(env.get("organ_id", ""))
        target = TARGETS.get(organ_id)
        if target is None:
            raise RelayError(f"unregistered organ: {organ_id}")
        for key in ("machine_id", "owner", "control_branch", "results_branch"):
            if str(env.get(key)) != target[key]:
                raise RelayError(f"target binding mismatch for {key}")
        command = env.get("command")
        if not isinstance(command, dict):
            raise RelayError("command missing")
        if str(command.get("command_id")) != command_id:
            raise RelayError("nested command_id mismatch")
        if str(command.get("machine_id")) != target["machine_id"]:
            raise RelayError("nested machine_id mismatch")
        if str(command.get("owner")) != target["owner"]:
            raise RelayError("nested owner mismatch")
        if str(command.get("op")) not in ALLOWED_OPS:
            raise RelayError("unsupported bridge op")
        command_raw = json_bytes(command)
        command_sha = sha(command_raw)
        if str(env.get("command_sha256")) != command_sha:
            raise RelayError("command digest mismatch")
        return target, command, command_sha

    def _outer_receipt_base(self, env: dict[str, Any]) -> dict[str, Any]:
        return {
            "schema": "OMEGA_OUTER_BRIDGE_RECEIPT/v1",
            "command_id": env["command_id"],
            "organ_id": env["organ_id"],
            "machine_id": env["machine_id"],
            "owner": env["owner"],
            "control_branch": env["control_branch"],
            "results_branch": env["results_branch"],
            "command_sha256": env["command_sha256"],
            "transport_boundary": "VPS_OUTER_HOST_GITHUB_ACTIONS",
            "github_run_id": os.getenv("GITHUB_RUN_ID"),
            "runner_name": os.getenv("RUNNER_NAME"),
        }

    def _write_inbox(self, command_id: str, payload: dict[str, Any]) -> None:
        _, inbox_path, _ = self._paths(command_id)
        self.runtime.write_bytes_atomic(inbox_path, json_bytes(payload))

    def _load_ledger(self, command_id: str) -> dict[str, Any] | None:
        _, _, path = self._paths(command_id)
        if not path.exists():
            return None
        return json.loads(path.read_text(encoding="utf-8"))

    def _save_ledger(self, command_id: str, payload: dict[str, Any]) -> None:
        _, _, path = self._paths(command_id)
        atomic_json(path, payload)

    def _terminal_unknown(self, env: dict[str, Any], reason: str) -> dict[str, Any]:
        payload = {
            **self._outer_receipt_base(env),
            "state": "UNKNOWN",
            "reason": reason,
            "automatic_replay": False,
            "finished_at": time.time(),
        }
        self._save_ledger(str(env["command_id"]), payload)
        self._write_inbox(str(env["command_id"]), payload)
        return payload

    def process_name(self, filename: str) -> dict[str, Any]:
        command_id_from_name = filename[:-5]
        if not COMMAND_ID_RE.fullmatch(command_id_from_name):
            return {"state": "IGNORED", "reason": "UNSAFE_FILENAME", "filename": filename}
        outbox_path, _, _ = self._paths(command_id_from_name)
        raw_env = self.runtime.read_bytes(outbox_path)
        try:
            env = json.loads(raw_env.decode("utf-8"))
            target, command, _ = self.validate_envelope(env)
        except Exception as exc:
            return {"state": "REJECTED", "command_id": command_id_from_name, "reason": f"{type(exc).__name__}:{exc}"}

        if str(env["command_id"]) != command_id_from_name:
            return {"state": "REJECTED", "command_id": command_id_from_name, "reason": "FILENAME_COMMAND_ID_MISMATCH"}

        envelope_sha = sha(json_bytes(env))
        ledger = self._load_ledger(command_id_from_name)
        if ledger is not None:
            if ledger.get("envelope_sha256") and ledger.get("envelope_sha256") != envelope_sha:
                return self._terminal_unknown(env, "ledger/envelope collision; no automatic replay")
            state = str(ledger.get("state", "")).upper()
            if state in {"COMPLETED", "UNKNOWN"}:
                self._write_inbox(command_id_from_name, ledger)
                return ledger
        else:
            ledger = {
                **self._outer_receipt_base(env),
                "state": "STAGED",
                "envelope_sha256": envelope_sha,
                "staged_at": time.time(),
                "automatic_replay": False,
            }
            self._save_ledger(command_id_from_name, ledger)

        command_rel = f"local_bridge/commands/{command_id_from_name}.json"
        receipt_rel = f"local_bridge/results/receipts/{command_id_from_name}.json"
        command_raw = json_bytes(command)

        try:
            if str(ledger.get("state", "")).upper() != "PUBLISHED":
                self.mailbox.publish_exact(target["control_branch"], command_rel, command_raw)
                ledger = {**ledger, "state": "PUBLISHED", "published_at": time.time()}
                self._save_ledger(command_id_from_name, ledger)

            host_raw = self.mailbox.wait_receipt(
                target["results_branch"], receipt_rel, self.receipt_timeout
            )
            host_receipt = json.loads(host_raw.decode("utf-8"))
            if str(host_receipt.get("command_id")) != command_id_from_name:
                raise OutcomeUnknown("host receipt command_id mismatch; no automatic replay")
            if str(host_receipt.get("machine_id")) != target["machine_id"]:
                raise OutcomeUnknown("host receipt machine_id mismatch; no automatic replay")
            if str(host_receipt.get("owner")) != target["owner"]:
                raise OutcomeUnknown("host receipt owner mismatch; no automatic replay")

            completed = {
                **self._outer_receipt_base(env),
                "state": "COMPLETED",
                "envelope_sha256": envelope_sha,
                "published_at": ledger.get("published_at"),
                "finished_at": time.time(),
                "automatic_replay": False,
                "host_receipt": host_receipt,
                "host_receipt_file_sha256": sha(host_raw),
                "host_receipt_canonical_sha256": sha(json_bytes(host_receipt)),
            }
            self._save_ledger(command_id_from_name, completed)
            self._write_inbox(command_id_from_name, completed)
            return completed
        except OutcomeUnknown as exc:
            return self._terminal_unknown(env, str(exc))
        except Exception as exc:
            if str((self._load_ledger(command_id_from_name) or {}).get("state", "")).upper() in {"PUBLISHED", "STAGED"}:
                return self._terminal_unknown(
                    env, f"{type(exc).__name__}:{exc}; no automatic replay"
                )
            raise

    def run_once(self) -> list[dict[str, Any]]:
        results = []
        for name in self.runtime.list_outbox(self.spool_root):
            results.append(self.process_name(name))
        return results


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=os.getenv("GITHUB_WORKSPACE", "."))
    ap.add_argument("--container", default=os.getenv("OMEGA_CONTAINER", "clay-direct-dev"))
    ap.add_argument("--spool-root", default=os.getenv("OMEGA_OUTER_SPOOL", "/workspace/omega_runtime/state/outer_bridge"))
    ap.add_argument("--ledger-root", default=os.getenv("OMEGA_OUTER_LEDGER", str(Path.home() / ".local/state/omega-outer-relay/ledger")))
    ap.add_argument("--receipt-timeout", type=float, default=float(os.getenv("OMEGA_OUTER_RECEIPT_TIMEOUT", "220")))
    ap.add_argument("--duration-seconds", type=float, default=0.0)
    ap.add_argument("--poll-seconds", type=float, default=2.0)
    args = ap.parse_args()

    runtime = ContainerRuntime.detect(args.container)
    relay = OuterRelay(
        runtime=runtime,
        mailbox=GitMailbox(Path(args.repo).resolve()),
        spool_root=args.spool_root,
        ledger_root=Path(args.ledger_root).expanduser(),
        receipt_timeout=args.receipt_timeout,
    )
    deadline = time.monotonic() + max(0.0, args.duration_seconds)
    first = True
    while first or time.monotonic() < deadline:
        first = False
        results = relay.run_once()
        for result in results:
            print(json.dumps(result, ensure_ascii=False, sort_keys=True), flush=True)
        if args.duration_seconds <= 0:
            break
        time.sleep(max(0.5, args.poll_seconds))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
