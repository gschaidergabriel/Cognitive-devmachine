from __future__ import annotations

import hashlib
import json
import os
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .unified_store import canon, digest


class BridgeError(RuntimeError):
    pass


class BridgeOutcomeUnknown(BridgeError):
    """Dispatch may have crossed the bridge; never replay automatically."""


@dataclass(frozen=True)
class BridgeTarget:
    organ_id: str
    owner_id: str
    machine_id: str
    control_branch: str
    results_branch: str


class GitBranchTransport:
    """Persistent Git transport for the already deployed FranKenstein local bridges.

    It deliberately uses dedicated OMEGA worktrees/clones and never the bridge daemon's
    own polling checkout. Commands are idempotent by command_id at the host daemon.
    """

    def __init__(
        self,
        *,
        carrier_repo: str | Path,
        work_root: str | Path,
        poll_seconds: float = 2.0,
    ) -> None:
        self.carrier_repo = Path(carrier_repo)
        self.work_root = Path(work_root)
        self.work_root.mkdir(parents=True, exist_ok=True)
        self.poll_seconds = max(0.25, float(poll_seconds))
        if not (self.carrier_repo / ".git").exists():
            raise BridgeError(f"carrier repo is not a git checkout: {self.carrier_repo}")
        self.remote = self._git(self.carrier_repo, "remote", "get-url", "origin").strip()
        if not self.remote:
            raise BridgeError("carrier repo has no origin remote")

    @staticmethod
    def _git(repo: Path, *args: str, check: bool = True, timeout: int = 120) -> str:
        proc = subprocess.run(
            ["git", "-C", str(repo), *args],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            check=False,
        )
        if check and proc.returncode != 0:
            raise BridgeError(f"git {' '.join(args)} failed rc={proc.returncode}: {proc.stderr[-1200:]}")
        return proc.stdout

    @staticmethod
    def _safe_branch_dir(branch: str) -> str:
        return hashlib.sha256(branch.encode("utf-8")).hexdigest()[:16] + "-" + branch.replace("/", "_")[:80]

    def _checkout(self, branch: str) -> Path:
        repo = self.work_root / self._safe_branch_dir(branch)
        if not (repo / ".git").exists():
            proc = subprocess.run(
                ["git", "clone", "--single-branch", "--branch", branch, self.remote, str(repo)],
                text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=180, check=False,
            )
            if proc.returncode != 0:
                raise BridgeError(f"clone {branch} failed rc={proc.returncode}: {proc.stderr[-1200:]}")
            self._git(repo, "config", "user.name", "OMEGA Bridge Relay")
            self._git(repo, "config", "user.email", "omega-bridge@localhost")
        return repo

    def _refresh(self, repo: Path, branch: str) -> None:
        self._git(repo, "fetch", "origin", branch, timeout=180)
        self._git(repo, "checkout", "-B", "omega-bridge", "FETCH_HEAD")

    def publish_command(self, target: BridgeTarget, command: dict[str, Any]) -> tuple[str, str]:
        command_id = str(command["command_id"])
        if command.get("machine_id") != target.machine_id or command.get("owner") != target.owner_id:
            raise BridgeError("command attribution does not match selected organ")
        raw = json.dumps(command, indent=2, ensure_ascii=False, sort_keys=True) + "\n"
        command_digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()
        rel = Path("local_bridge") / "commands" / f"{command_id}.json"
        repo = self._checkout(target.control_branch)

        for attempt in range(1, 5):
            self._refresh(repo, target.control_branch)
            path = repo / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            if path.exists():
                existing = path.read_text(encoding="utf-8")
                if hashlib.sha256(existing.encode("utf-8")).hexdigest() != command_digest:
                    raise BridgeError(f"command_id collision with different payload: {command_id}")
                return str(rel), command_digest
            path.write_text(raw, encoding="utf-8")
            self._git(repo, "add", str(rel))
            self._git(repo, "commit", "-m", f"omega: dispatch {command_id}")
            proc = subprocess.run(
                ["git", "-C", str(repo), "push", "origin", f"HEAD:{target.control_branch}"],
                text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=180, check=False,
            )
            if proc.returncode == 0:
                return str(rel), command_digest
            # A concurrent writer may have advanced the mailbox. Rebase by rebuilding
            # the same exact file on the new branch head; command identity is stable.
            if attempt == 4:
                raise BridgeOutcomeUnknown(
                    f"push outcome unresolved for {command_id}; no automatic replay: {proc.stderr[-1000:]}"
                )
            time.sleep(0.5 * attempt)
        raise AssertionError("unreachable")

    def wait_receipt(self, target: BridgeTarget, command_id: str, timeout_seconds: float) -> tuple[dict[str, Any], str]:
        deadline = time.monotonic() + max(1.0, timeout_seconds)
        repo = self._checkout(target.results_branch)
        rel = Path("local_bridge") / "results" / "receipts" / f"{command_id}.json"
        while time.monotonic() < deadline:
            try:
                self._refresh(repo, target.results_branch)
            except BridgeError:
                time.sleep(self.poll_seconds)
                continue
            path = repo / rel
            if path.exists():
                raw = path.read_text(encoding="utf-8")
                receipt = json.loads(raw)
                if str(receipt.get("command_id")) != command_id:
                    raise BridgeOutcomeUnknown("receipt command_id mismatch")
                if str(receipt.get("machine_id")) != target.machine_id:
                    raise BridgeOutcomeUnknown(
                        f"receipt machine mismatch expected={target.machine_id} got={receipt.get('machine_id')}"
                    )
                if str(receipt.get("owner")) != target.owner_id:
                    raise BridgeOutcomeUnknown(
                        f"receipt owner mismatch expected={target.owner_id} got={receipt.get('owner')}"
                    )
                return receipt, hashlib.sha256(raw.encode("utf-8")).hexdigest()
            time.sleep(self.poll_seconds)
        raise BridgeOutcomeUnknown(f"receipt timeout for {command_id}; no automatic replay")

    def dispatch(self, target: BridgeTarget, command: dict[str, Any], *, receipt_timeout: float = 180.0) -> tuple[dict[str, Any], str, str]:
        rel, command_digest = self.publish_command(target, command)
        receipt, receipt_digest = self.wait_receipt(target, str(command["command_id"]), receipt_timeout)
        return receipt, command_digest, receipt_digest


def command_from_effect(effect_id: str, target: BridgeTarget, execution: dict[str, Any]) -> dict[str, Any]:
    op = str(execution.get("op", "")).strip()
    command_id = "omega-" + effect_id.replace("effect_", "")[:48]
    out: dict[str, Any] = {
        "schema": "CLAY_LOCAL_COMMAND/v1",
        "command_id": command_id,
        "machine_id": target.machine_id,
        "owner": target.owner_id,
        "op": op,
    }
    for key in ("command", "cwd", "timeout_seconds", "path", "content", "name"):
        if key in execution:
            out[key] = execution[key]
    if op == "exec":
        out["timeout_seconds"] = min(3600, max(1, int(out.get("timeout_seconds", 120))))
    return out


__all__ = [
    "BridgeError", "BridgeOutcomeUnknown", "BridgeTarget", "GitBranchTransport", "command_from_effect"
]
