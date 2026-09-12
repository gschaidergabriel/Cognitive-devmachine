from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import time
import uuid
from pathlib import Path
from typing import Any

from .unified_store import UnifiedStore, canon, digest, now


class MasterBridgeError(RuntimeError):
    pass


def _run(repo: Path, *args: str, check: bool = True, timeout: int = 180) -> str:
    proc = subprocess.run(
        ["git", "-C", str(repo), *args], text=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout, check=False,
    )
    if check and proc.returncode != 0:
        raise MasterBridgeError(f"git {' '.join(args)} rc={proc.returncode}: {proc.stderr[-1200:]}")
    return proc.stdout


class MasterBridge:
    """Git mailbox from the persistent OMEGA runtime to its ChatGPT master organ.

    The bridge is intentionally a request/response mailbox, not a second state store.
    OMEGA continues running through GRID even while ChatGPT is unavailable. ChatGPT is
    recruited for high-information reasoning, coordination and tool work; returned
    material is evidence/candidate state until OMEGA assimilates it.
    """

    def __init__(
        self,
        *,
        omega_repo: Path,
        runtime_root: Path,
        store: UnifiedStore,
        control_branch: str = "omega-master-control",
        results_branch: str = "omega-master-results",
    ) -> None:
        self.omega_repo = omega_repo
        self.runtime_root = runtime_root
        self.store = store
        self.control_branch = control_branch
        self.results_branch = results_branch
        self.work_root = runtime_root / "master_bridge" / "git"
        self.submitted = runtime_root / "master_bridge" / "submitted"
        self.responses = runtime_root / "master_bridge" / "responses"
        for p in (self.work_root, self.submitted, self.responses):
            p.mkdir(parents=True, exist_ok=True)
        self.remote = _run(omega_repo, "remote", "get-url", "origin").strip()
        if not self.remote:
            raise MasterBridgeError("OMEGA repo has no origin")

    def _checkout(self, branch: str) -> Path:
        tag = hashlib.sha256(branch.encode()).hexdigest()[:12]
        repo = self.work_root / f"{tag}-{branch.replace('/', '_')}"
        if not (repo / ".git").exists():
            proc = subprocess.run(
                ["git", "clone", "--single-branch", "--branch", branch, self.remote, str(repo)],
                text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=180, check=False,
            )
            if proc.returncode != 0:
                raise MasterBridgeError(f"clone {branch} failed: {proc.stderr[-1200:]}")
            _run(repo, "config", "user.name", "OMEGA Master Bridge")
            _run(repo, "config", "user.email", "omega-master-bridge@localhost")
        return repo

    def _refresh(self, repo: Path, branch: str) -> None:
        _run(repo, "fetch", "origin", branch)
        _run(repo, "checkout", "-B", "omega-master-mailbox", "FETCH_HEAD")

    def _publish(self, branch: str, rel: Path, payload: dict[str, Any], message: str) -> str:
        repo = self._checkout(branch)
        raw = json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n"
        raw_sha = hashlib.sha256(raw.encode()).hexdigest()
        for attempt in range(1, 5):
            self._refresh(repo, branch)
            path = repo / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            if path.exists():
                existing = path.read_text(encoding="utf-8")
                if hashlib.sha256(existing.encode()).hexdigest() != raw_sha:
                    raise MasterBridgeError(f"mailbox id collision: {rel}")
                return raw_sha
            path.write_text(raw, encoding="utf-8")
            _run(repo, "add", str(rel))
            _run(repo, "commit", "-m", message)
            proc = subprocess.run(
                ["git", "-C", str(repo), "push", "origin", f"HEAD:{branch}"],
                text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=180, check=False,
            )
            if proc.returncode == 0:
                return raw_sha
            if attempt == 4:
                raise MasterBridgeError(f"mailbox push unresolved: {proc.stderr[-1200:]}")
            time.sleep(0.5 * attempt)
        raise AssertionError("unreachable")

    def submit(self, payload: dict[str, Any], *, correlation_id: str | None = None) -> dict[str, Any]:
        request_id = "omega_master_" + uuid.uuid4().hex
        omega_head = _run(self.omega_repo, "rev-parse", "HEAD").strip()
        request = {
            "schema": "OMEGA_MASTER_REQUEST/v1",
            "request_id": request_id,
            "created_at": now(),
            "sender": "omega-grid",
            "recipient": "chatgpt-master-organ",
            "omega_head": omega_head,
            "correlation_id": correlation_id,
            "payload": payload,
        }
        request["request_digest"] = digest(request)
        rel = Path("master_bridge") / "requests" / f"{request_id}.json"
        blob_sha = self._publish(self.control_branch, rel, request, f"omega master request: {request_id}")
        local = self.submitted / f"{request_id}.json"
        local.write_text(json.dumps(request, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        self.store.bridge_message(
            direction="OUT", sender="omega-grid", recipient="chatgpt-master-organ",
            kind="MASTER_REQUEST", payload=request, correlation_id=correlation_id or request_id,
        )
        return {"request_id": request_id, "request_digest": request["request_digest"], "git_blob_digest": blob_sha, "path": str(rel)}

    def poll_response(self, request_id: str) -> dict[str, Any] | None:
        repo = self._checkout(self.results_branch)
        self._refresh(repo, self.results_branch)
        rel = Path("master_bridge") / "responses" / f"{request_id}.json"
        path = repo / rel
        if not path.exists():
            return None
        response = json.loads(path.read_text(encoding="utf-8"))
        if response.get("schema") != "OMEGA_MASTER_RESPONSE/v1" or response.get("request_id") != request_id:
            raise MasterBridgeError("invalid master response binding")
        submitted = json.loads((self.submitted / f"{request_id}.json").read_text(encoding="utf-8"))
        if response.get("request_digest") != submitted.get("request_digest"):
            raise MasterBridgeError("master response request_digest mismatch")
        local = self.responses / f"{request_id}.json"
        if not local.exists():
            local.write_text(json.dumps(response, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
            self.store.bridge_message(
                direction="IN", sender="chatgpt-master-organ", recipient="omega-grid",
                kind="MASTER_RESPONSE", payload=response,
                correlation_id=str(submitted.get("correlation_id") or request_id),
            )
            self.store.record_observation(
                source_id="repo:omega", subject_id="omega:master_bridge_response",
                payload=response, observed_at=str(response.get("created_at") or now()),
                evidence_class="RUNTIME_RECEIPT", source_repo="gschaidergabriel/oMEGA",
                source_path=str(rel), raw_locator=f"git:{self.results_branch}:{rel}",
            )
        return response

    def process_grid_outbox_once(self) -> dict[str, int]:
        counts = {"submitted": 0, "responses": 0}
        outbox = self.runtime_root / "outbox"
        for path in sorted(outbox.glob("*.json")):
            try:
                item = json.loads(path.read_text(encoding="utf-8"))
            except Exception:
                continue
            if item.get("schema") != "OMEGA_OUTBOX/v1" or item.get("kind") != "MASTER_COGNITION_UPDATE":
                continue
            message_id = str(item.get("message_id"))
            marker = self.runtime_root / "master_bridge" / "submitted_messages" / f"{message_id}.json"
            if marker.exists():
                continue
            result = self.submit(item, correlation_id=message_id)
            marker.parent.mkdir(parents=True, exist_ok=True)
            marker.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
            counts["submitted"] += 1

        for path in sorted(self.submitted.glob("omega_master_*.json")):
            request_id = path.stem
            if (self.responses / f"{request_id}.json").exists():
                continue
            try:
                if self.poll_response(request_id) is not None:
                    counts["responses"] += 1
            except MasterBridgeError:
                raise
        return counts


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--omega-repo", default=os.getenv("OMEGA_REPO_ROOT", "/workspace/oMEGA"))
    ap.add_argument("--runtime-root", default=os.getenv("OMEGA_RUNTIME_ROOT", "/workspace/omega_runtime/state"))
    ap.add_argument("--db", default=os.getenv("OMEGA_UNIFIED_DB", "/workspace/omega_runtime/data/omega_unified.db"))
    ap.add_argument("--control-branch", default=os.getenv("OMEGA_MASTER_CONTROL_BRANCH", "omega-master-control"))
    ap.add_argument("--results-branch", default=os.getenv("OMEGA_MASTER_RESULTS_BRANCH", "omega-master-results"))
    ap.add_argument("--interval", type=float, default=float(os.getenv("OMEGA_MASTER_BRIDGE_INTERVAL", "20")))
    ap.add_argument("--once", action="store_true")
    args = ap.parse_args()
    repo = Path(args.omega_repo)
    store = UnifiedStore(Path(args.db), repo / "schema")
    bridge = MasterBridge(
        omega_repo=repo, runtime_root=Path(args.runtime_root), store=store,
        control_branch=args.control_branch, results_branch=args.results_branch,
    )
    if args.once:
        print(json.dumps(bridge.process_grid_outbox_once(), indent=2)); return 0
    while True:
        try:
            bridge.process_grid_outbox_once()
        except Exception as exc:
            err = Path(args.runtime_root) / "master_bridge" / "LAST_ERROR.json"
            err.parent.mkdir(parents=True, exist_ok=True)
            err.write_text(json.dumps({"at":now(),"error":f"{type(exc).__name__}:{exc}"},indent=2)+"\n")
        time.sleep(max(2.0,args.interval))


if __name__ == "__main__":
    raise SystemExit(main())
