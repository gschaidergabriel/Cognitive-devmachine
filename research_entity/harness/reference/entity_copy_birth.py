from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import secrets
from typing import Any, Callable


MANIFEST_REL = Path("state/ENTITY_INSTANCE.json")
BIRTH_EVENTS_REL = Path("state/ENTITY_BIRTH_EVENTS.jsonl")
REGISTRY_SCHEMA = "CLAY_ENTITY_REGISTRY_V1"
MANIFEST_SCHEMA = "CLAY_ENTITY_INSTANCE_V1"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _canon(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _sha(value: Any) -> str:
    raw = value if isinstance(value, str) else _canon(value)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _slug(name: str) -> str:
    value = re.sub(r"[^a-z0-9]+", "-", name.strip().lower()).strip("-")
    return value or "entity"


def _read_json(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"invalid json object: {path}")
    return value


def _atomic_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(_canon(value) + "\n", encoding="utf-8")
    tmp.replace(path)


def _append_jsonl(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(_canon(value) + "\n")


@dataclass(frozen=True)
class BirthDecision:
    classification: str
    entity_id: str
    entity_name: str
    parent_entity_id: str | None
    pulse_index: int
    birth_pulse_id: str
    new_birth: bool
    package_root: str
    state_namespace: str
    ready_for_cognition: bool


class StateRekeyRequired(RuntimeError):
    pass


class EntityBirthRegistry:
    """Host-level identity registry deliberately stored outside copied entity packages."""

    def __init__(self, path: str | Path):
        self.path = Path(path).resolve()
        self._data = self._load()

    def _load(self) -> dict[str, Any]:
        value = _read_json(self.path)
        if value is None:
            return {"schema": REGISTRY_SCHEMA, "entities": {}, "retired_ids": []}
        if value.get("schema") != REGISTRY_SCHEMA:
            raise RuntimeError("unsupported registry schema")
        value.setdefault("entities", {})
        value.setdefault("retired_ids", [])
        return value

    def _save(self) -> None:
        _atomic_json(self.path, self._data)

    def record(self, entity_id: str) -> dict[str, Any] | None:
        row = self._data["entities"].get(entity_id)
        return dict(row) if row else None

    def retire(self, entity_id: str) -> None:
        row = self._data["entities"].pop(entity_id, None)
        if row:
            self._data["retired_ids"] = sorted(set(self._data["retired_ids"]) | {entity_id})
            self._save()

    @property
    def retired_ids(self) -> frozenset[str]:
        return frozenset(self._data.get("retired_ids", ()))

    def _new_entity_id(self, name: str, parent: str | None, birth_pulse_id: str, nonce: str) -> str:
        digest = _sha({
            "name": name.strip(),
            "parent": parent,
            "birth_pulse_id": birth_pulse_id,
            "nonce": nonce,
        })[:24]
        entity_id = f"clay:{_slug(name)}:{digest}"
        if entity_id in self._data["entities"] or entity_id in self.retired_ids:
            raise RuntimeError("entity id collision/reuse")
        return entity_id

    @staticmethod
    def _manifest_path(root: Path) -> Path:
        return root / MANIFEST_REL

    @staticmethod
    def _events_path(root: Path) -> Path:
        return root / BIRTH_EVENTS_REL

    def _write_manifest(self, root: Path, row: dict[str, Any]) -> None:
        _atomic_json(self._manifest_path(root), {
            "schema": MANIFEST_SCHEMA,
            "entity_id": row["entity_id"],
            "entity_name": row["entity_name"],
            "birth_name": row["birth_name"],
            "birth_pulse_id": row["birth_pulse_id"],
            "birth_pulse_index": 1,
            "parent_entity_id": row.get("parent_entity_id"),
            "ancestral_seed_hash": row.get("ancestral_seed_hash"),
            "state_namespace": row["state_namespace"],
            "pulse_count": row["pulse_count"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        })

    def _birth(self, root: Path, name: str, parent: str | None, ancestral_seed_hash: str | None, *, state_rekey: Callable[[Path, str, str | None, str], None] | None = None, inherited_state: bool = False) -> BirthDecision:
        pulse_id = "pulse:" + secrets.token_hex(16)
        nonce = secrets.token_hex(16)
        entity_id = self._new_entity_id(name, parent, pulse_id, nonce)
        ts = _now()
        state_namespace = "entity-state:" + entity_id
        if inherited_state and state_rekey is None:
            raise StateRekeyRequired("copied entity package requires state re-key/isolation before Pulse #1")
        row = {
            "entity_id": entity_id,
            "entity_name": name.strip(),
            "birth_name": name.strip(),
            "birth_pulse_id": pulse_id,
            "birth_nonce_hash": _sha(nonce),
            "parent_entity_id": parent,
            "ancestral_seed_hash": ancestral_seed_hash,
            "package_root": str(root),
            "state_namespace": state_namespace,
            "pulse_count": 1,
            "created_at": ts,
            "updated_at": ts,
        }
        if state_rekey is not None:
            state_rekey(root, entity_id, parent, state_namespace)
        self._data["entities"][entity_id] = row
        self._save()
        self._write_manifest(root, row)
        _append_jsonl(self._events_path(root), {
            "event": "ENTITY_BIRTH",
            "entity_id": entity_id,
            "entity_name": row["entity_name"],
            "parent_entity_id": parent,
            "birth_pulse_id": pulse_id,
            "pulse_index": 1,
            "state_namespace": state_namespace,
            "created_at": ts,
        })
        return BirthDecision("ENTITY_BIRTH", entity_id, row["entity_name"], parent, 1, pulse_id, True,
                             str(root), state_namespace, True)

    def preflight(
        self,
        package_root: str | Path,
        *,
        entity_name: str | None = None,
        ancestral_seed_hash: str | None = None,
        replica_ticket: dict[str, Any] | None = None,
        state_rekey: Callable[[Path, str, str | None, str], None] | None = None,
    ) -> BirthDecision:
        root = Path(package_root).resolve()
        root.mkdir(parents=True, exist_ok=True)
        manifest = _read_json(self._manifest_path(root))

        # Same-entity replication is an explicit authority path, never inferred from copying.
        if replica_ticket is not None:
            if replica_ticket.get("authorization") != "REPLICA_ATTACH":
                raise PermissionError("invalid replica authorization")
            target_id = str(replica_ticket.get("entity_id", ""))
            target = self._data["entities"].get(target_id)
            if not target:
                raise RuntimeError("replica target not registered")
            return BirthDecision("REPLICA_ATTACHED", target_id, target["entity_name"],
                                 target.get("parent_entity_id"), int(target["pulse_count"]),
                                 target["birth_pulse_id"], False, str(root),
                                 target["state_namespace"], True)

        if manifest and manifest.get("schema") != MANIFEST_SCHEMA:
            raise RuntimeError("invalid package identity manifest schema")

        if manifest:
            inherited_id = str(manifest.get("entity_id", ""))
            bound = self._data["entities"].get(inherited_id)
            if bound:
                old_root = Path(bound["package_root"])
                if old_root.resolve() == root:
                    # Normal restart/pulse in same package instance.
                    bound["pulse_count"] = int(bound.get("pulse_count", 1)) + 1
                    bound["updated_at"] = _now()
                    self._save()
                    self._write_manifest(root, bound)
                    return BirthDecision("SAME_ENTITY_RESTART", inherited_id, bound["entity_name"],
                                         bound.get("parent_entity_id"), bound["pulse_count"],
                                         bound["birth_pulse_id"], False, str(root),
                                         bound["state_namespace"], True)

                if not old_root.exists():
                    # A move, not a copy: old bound instance disappeared.
                    bound["package_root"] = str(root)
                    bound["pulse_count"] = int(bound.get("pulse_count", 1)) + 1
                    bound["updated_at"] = _now()
                    self._save()
                    self._write_manifest(root, bound)
                    return BirthDecision("SAME_ENTITY_MOVED", inherited_id, bound["entity_name"],
                                         bound.get("parent_entity_id"), bound["pulse_count"],
                                         bound["birth_pulse_id"], False, str(root),
                                         bound["state_namespace"], True)

                # Both old and new roots exist: certificate was copied. Birth is mandatory.
                child_name = (entity_name or manifest.get("entity_name") or "entity-copy").strip()
                seed = ancestral_seed_hash or manifest.get("ancestral_seed_hash") or _sha({
                    "parent_entity_id": inherited_id,
                    "parent_birth_pulse_id": manifest.get("birth_pulse_id"),
                })
                return self._birth(root, child_name, inherited_id, seed, state_rekey=state_rekey, inherited_state=True)

            # Manifest claims an identity the external registry does not bind. Never trust it.
            child_name = (entity_name or manifest.get("entity_name") or "entity-copy").strip()
            parent = inherited_id or None
            seed = ancestral_seed_hash or manifest.get("ancestral_seed_hash")
            return self._birth(root, child_name, parent, seed, state_rekey=state_rekey, inherited_state=True)

        # No manifest: fresh local entity package.
        name = (entity_name or root.name or "entity").strip()
        return self._birth(root, name, None, ancestral_seed_hash, state_rekey=state_rekey, inherited_state=False)

    def rename_after_birth(self, entity_id: str, new_name: str) -> str:
        row = self._data["entities"].get(entity_id)
        if not row:
            raise KeyError(entity_id)
        row["entity_name"] = new_name.strip()
        row["updated_at"] = _now()
        self._save()
        root = Path(row["package_root"])
        self._write_manifest(root, row)
        return entity_id


__all__ = ["BirthDecision", "EntityBirthRegistry", "StateRekeyRequired", "MANIFEST_REL", "BIRTH_EVENTS_REL"]