from __future__ import annotations

import json
import os
from pathlib import Path

from ucm2 import ROOT_MODULE, SCHEMA_VERSION, UCM2

ANCHOR_SCHEMA_VERSION = 1
ANCHOR_FILENAME = "UCM2.lineage_anchor.json"


class AnchoredUCM2:
    """Fail-closed lineage/rollback witness around the UCM2 research runtime.

    The witness is deliberately outside the mutable SQLite event database.  It
    does not grant Clay, effect, identity, quorum, or truth authority.  Its only
    job is to bind the locally admitted UCM2 root/schema/epoch/event-head and to
    refuse automatic recovery when the database presents a different lineage.

    This is a research candidate.  A snapshot/attacker that rolls back both the
    database and this sidecar together remains outside this witness's proof
    boundary and requires a stronger independently durable anchor.
    """

    def __init__(self, root: str | Path):
        self.root = Path(root).resolve()
        self.machine = UCM2(self.root)
        self.anchor_path = (self.machine.state_dir / ANCHOR_FILENAME).resolve()
        try:
            self._verify_or_initialize_anchor()
        except Exception:
            self.machine.close()
            raise

    def close(self) -> None:
        self.machine.close()

    def __enter__(self) -> "AnchoredUCM2":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def __getattr__(self, name: str):
        return getattr(self.machine, name)

    def _current_witness(self) -> dict:
        stream = self.machine.event_stream()
        terminal_hash = self.machine.verify_event_stream(stream)
        return {
            "anchor_schema_version": ANCHOR_SCHEMA_VERSION,
            "root_module": ROOT_MODULE,
            "ucm2_schema_version": SCHEMA_VERSION,
            "epoch": self.machine.epoch(),
            "terminal_event_hash": terminal_hash,
        }

    def _load_anchor(self) -> dict | None:
        if not self.anchor_path.exists():
            return None
        try:
            value = json.loads(self.anchor_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise RuntimeError("LINEAGE_ANCHOR_UNREADABLE") from exc
        required = {
            "anchor_schema_version",
            "root_module",
            "ucm2_schema_version",
            "epoch",
            "terminal_event_hash",
        }
        if not isinstance(value, dict) or set(value) != required:
            raise RuntimeError("LINEAGE_ANCHOR_SCHEMA_INVALID")
        return value

    def _write_anchor(self, value: dict) -> None:
        self.anchor_path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.anchor_path.with_name(self.anchor_path.name + ".tmp")
        data = json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n"
        with open(tmp, "w", encoding="utf-8") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(tmp, 0o600)
        os.replace(tmp, self.anchor_path)
        try:
            dir_fd = os.open(self.anchor_path.parent, os.O_RDONLY)
        except OSError:
            return
        try:
            os.fsync(dir_fd)
        finally:
            os.close(dir_fd)

    def _verify_or_initialize_anchor(self) -> None:
        current = self._current_witness()
        anchor = self._load_anchor()
        if anchor is None:
            if int(current["epoch"]) != 0:
                raise RuntimeError("LINEAGE_ANCHOR_MISSING_NONZERO")
            self._write_anchor(current)
            return

        if int(anchor["anchor_schema_version"]) != ANCHOR_SCHEMA_VERSION:
            raise RuntimeError("LINEAGE_ANCHOR_VERSION_MISMATCH")
        if anchor["root_module"] != ROOT_MODULE:
            raise RuntimeError("LINEAGE_ROOT_MISMATCH")
        if int(anchor["ucm2_schema_version"]) != SCHEMA_VERSION:
            raise RuntimeError("LINEAGE_SCHEMA_MISMATCH")

        anchor_epoch = int(anchor["epoch"])
        current_epoch = int(current["epoch"])
        if current_epoch < anchor_epoch:
            raise RuntimeError("LINEAGE_ROLLBACK_DETECTED")
        if current_epoch > anchor_epoch:
            # Fail closed rather than silently treating DB-ahead-of-anchor as an
            # admitted generation.  A later recovery protocol may reconcile this
            # crash window only with an explicit durable receipt.
            raise RuntimeError("LINEAGE_ANCHOR_STALE")
        if anchor["terminal_event_hash"] != current["terminal_event_hash"]:
            raise RuntimeError("LINEAGE_HEAD_MISMATCH")

    def refresh_anchor(self) -> dict:
        current = self._current_witness()
        self._write_anchor(current)
        return current

    def upsert(self, object_id: str, kind: str, payload: dict, status: str = "ACTIVE") -> int:
        epoch = self.machine.upsert(object_id, kind, payload, status)
        self.refresh_anchor()
        return epoch

    def link(self, src: str, rel: str, dst: str, payload: dict | None = None) -> int:
        epoch = self.machine.link(src, rel, dst, payload)
        self.refresh_anchor()
        return epoch

    def record_experience(
        self,
        actor: str,
        observation: str,
        prediction: str | None,
        outcome: str | None,
        lesson: str | None,
        claim_class: str = "OBSERVED",
    ) -> tuple[str, int]:
        result = self.machine.record_experience(
            actor, observation, prediction, outcome, lesson, claim_class
        )
        self.refresh_anchor()
        return result

    def rebuild_materialized_from_events(self) -> str:
        self._verify_or_initialize_anchor()
        result = self.machine.rebuild_materialized_from_events()
        self._verify_or_initialize_anchor()
        return result

    def restore_from_event_stream(self, stream: list[dict]) -> str:
        anchor = self._load_anchor()
        if anchor is None:
            raise RuntimeError("LINEAGE_ANCHOR_REQUIRED_FOR_RESTORE")
        terminal_hash = self.machine.verify_event_stream(stream)
        candidate_epoch = int(stream[-1]["epoch"])
        if candidate_epoch != int(anchor["epoch"]):
            raise RuntimeError("LINEAGE_RESTORE_EPOCH_NOT_ADMITTED")
        if terminal_hash != anchor["terminal_event_hash"]:
            raise RuntimeError("LINEAGE_RESTORE_HEAD_NOT_ADMITTED")
        result = self.machine.restore_from_event_stream(stream)
        self._verify_or_initialize_anchor()
        return result
