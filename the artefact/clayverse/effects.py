from __future__ import annotations

import hashlib
import json
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path

from .entityos_bridge import EntityOSBridge
from .store import Lease, StaleGeneration, UnifiedDB


@dataclass(frozen=True)
class EffectRequest:
    user_id: str
    session_id: str
    capability: str
    target: str
    argv: list[str] | None = None
    expected_generation: int | None = None
    request_key: str | None = None


class EffectGate:
    ALLOWED = {"entityos.exec", "process.exec", "state.noop"}
    SHELL_NAMES = {"sh", "bash", "dash", "zsh", "fish", "ksh", "csh", "tcsh"}

    def __init__(
        self,
        db: UnifiedDB,
        allow_process=False,
        entityos_bridge: EntityOSBridge | None = None,
    ):
        self.db = db
        self.allow_process = allow_process
        self.entityos_bridge = entityos_bridge

    @staticmethod
    def _request_hash(req: EffectRequest, generation: int) -> str:
        payload = {
            "user_id": req.user_id,
            "session_id": req.session_id,
            "capability": req.capability,
            "target": req.target,
            "argv": req.argv,
            "generation": generation,
        }
        return hashlib.sha256(
            json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()

    def execute(self, req: EffectRequest, episode_id=None, lease: Lease | None = None):
        if req.capability not in self.ALLOWED:
            raise PermissionError("capability denied")

        row = self.db.db.execute(
            "SELECT generation FROM sessions WHERE session_id=? AND user_id=?",
            (req.session_id, req.user_id),
        ).fetchone()
        if not row:
            raise PermissionError("session owner mismatch")
        generation = int(row[0])
        if req.expected_generation is not None and req.expected_generation != generation:
            raise StaleGeneration(req.session_id)
        if lease:
            self.db.assert_lease(lease)

        executable = None
        if req.capability == "entityos.exec":
            if not self.entityos_bridge:
                raise PermissionError("EntityOS execution disabled or unpinned")
        elif req.capability == "process.exec":
            if not self.allow_process:
                raise PermissionError("direct process execution disabled")
            if (
                not req.argv
                or not isinstance(req.argv, list)
                or any(not isinstance(x, str) or "\x00" in x for x in req.argv)
            ):
                raise ValueError("explicit valid argv required")
            executable = str(Path(req.argv[0]).resolve())
            if Path(executable).name in self.SHELL_NAMES:
                raise PermissionError(
                    "shell requires a separate explicit capability contract"
                )

        if not req.request_key:
            raise ValueError("effect request_key required")

        request_hash = self._request_hash(req, generation)
        reserved, created = self.db.reserve_effect(
            request_key=req.request_key,
            request_hash=request_hash,
            episode_id=episode_id,
            user_id=req.user_id,
            capability=req.capability,
            target=req.target,
            requested_generation=generation,
            argv=req.argv,
        )

        if not created:
            if reserved.get("request_hash") != request_hash:
                raise RuntimeError("EFFECT_REQUEST_CONFLICT")
            status = reserved["status"]
            if status == "PENDING":
                raise RuntimeError("EFFECT_RECOVERY_REQUIRED")
            if status == "FAILED":
                raise RuntimeError("EFFECT_PREVIOUSLY_FAILED")
            if status != "VERIFIED":
                raise RuntimeError("EFFECT_STATUS_INVALID")
            return reserved["effect_id"], json.loads(reserved["outcome"] or "{}")

        eid = reserved["effect_id"]
        try:
            if req.capability == "state.noop":
                outcome = {"ok": True, "target": req.target}
            elif req.capability == "entityos.exec":
                outcome = self.entityos_bridge.run(req.argv)
            else:
                cp = subprocess.run(
                    [executable, *req.argv[1:]],
                    shell=False,
                    capture_output=True,
                    text=False,
                    timeout=10,
                    env={"PATH": os.environ.get("PATH", "/usr/bin:/bin")},
                )
                outcome = {
                    "ok": cp.returncode == 0,
                    "exit": cp.returncode,
                    "stdout_sha256": hashlib.sha256(cp.stdout).hexdigest(),
                    "stderr_sha256": hashlib.sha256(cp.stderr).hexdigest(),
                    "stdout": cp.stdout[:4096].decode(errors="replace"),
                    "stderr": cp.stderr[:4096].decode(errors="replace"),
                }
        except Exception as exc:
            error = {"ok": False, "error_type": type(exc).__name__, "error": str(exc)}
            self.db.finalize_effect(eid, status="FAILED", outcome=error)
            raise RuntimeError("EFFECT_EXECUTION_FAILED") from exc

        # Persist the observed outcome before a post-effect fencing check. If
        # the lease became stale during execution, the external effect is still
        # evidence and must never become an unrecorded replay candidate.
        self.db.finalize_effect(eid, status="VERIFIED", outcome=outcome)
        if lease:
            self.db.assert_lease(lease)
        return eid, outcome
