from __future__ import annotations

import json
from pathlib import Path

from .bridge_relay import LocalSandboxExecutor, Relay
from .policy_kernel import PolicyKernel
from .spool_bridge_relay import SpoolTransport
from .unified_store import UnifiedStore


class CredentialFreeSpoolRelay(Relay):
    """Canonical Relay logic with credential-free outer-spool transport injected at construction.

    This deliberately mirrors Relay.__init__ except for transport construction. The
    sandbox must not instantiate GitBranchTransport merely to replace it afterwards:
    doing so makes first boot depend on a credential-bearing carrier checkout and
    violates the outer-spool trust boundary.
    """

    def __init__(
        self,
        *,
        runtime_root: Path,
        repo_root: Path,
        db_path: Path,
        policy_path: Path,
        router_path: Path,
        spool_root: Path,
        poll_seconds: float = 0.5,
    ) -> None:
        self.runtime_root = runtime_root
        self.repo_root = repo_root
        self.store = UnifiedStore(db_path, repo_root / "schema")
        self.policy = PolicyKernel.from_path(policy_path)
        self.router_cfg = json.loads(router_path.read_text(encoding="utf-8"))
        self.organs = {str(o["organ_id"]): o for o in self.router_cfg["organs"]}
        self.transport = SpoolTransport(spool_root, poll_seconds=poll_seconds)
        self.local = LocalSandboxExecutor(runtime_root / "receipts")
        (runtime_root / "outbox").mkdir(parents=True, exist_ok=True)
        (runtime_root / "relay_results").mkdir(parents=True, exist_ok=True)
