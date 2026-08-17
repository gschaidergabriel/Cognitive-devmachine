from __future__ import annotations

import json
import os
from pathlib import Path

from .api_acceptance_probe import run_api_acceptance_probe
from .graph import ClayGraphProjection
from .identity import IdentityRouter
from .logical_snapshot import LogicalSnapshotManager
from .recovery import recover_incomplete_episodes
from .runtime_identity import collect_runtime_identity
from .service import _acceptance_bool, _clerk_map, _entityos_config
from .store import UnifiedDB


def _final_required_effect_policy() -> tuple[bool, str | None]:
    require_effect = _acceptance_bool("CLAYVERSE_ACCEPTANCE_REQUIRE_EFFECT")
    raw = os.environ.get("CLAYVERSE_ACCEPTANCE_REQUIRED_EFFECT_CAPABILITY", "").strip()
    if raw and raw != "entityos.exec":
        raise RuntimeError(
            "CLAYVERSE_ACCEPTANCE_REQUIRED_EFFECT_CAPABILITY may only be entityos.exec"
        )
    required_capability = raw or ("entityos.exec" if require_effect else None)
    if required_capability is not None:
        require_effect = True
    return require_effect, required_capability


def _restore_before_db_open(state_root: str) -> dict[str, object] | None:
    raw = os.environ.get("CLAYVERSE_RESTORE_SNAPSHOT_DIR", "").strip()
    if not raw:
        os.makedirs(state_root, exist_ok=True)
        return None
    if not os.path.isabs(raw) or any(char in raw for char in ("\x00", "\n", "\r")):
        raise RuntimeError("CLAYVERSE_RESTORE_SNAPSHOT_DIR must be an absolute single-line path")
    return LogicalSnapshotManager(state_root).restore_fresh(
        Path(raw), runtime_identity=collect_runtime_identity()
    )


def _create_acceptance_snapshot(db: UnifiedDB) -> dict[str, object] | None:
    if not _acceptance_bool("CLAYVERSE_ACCEPTANCE_CREATE_SNAPSHOT"):
        return None
    manifest = LogicalSnapshotManager(db.path.parent).create(
        db,
        runtime_identity=collect_runtime_identity(),
        reason="generic-api-final-sandbox-probe",
    )
    anchor = manifest["state"]["checkpoint_anchor"]
    return {
        "created": True,
        "snapshot_id": manifest["snapshot_id"],
        "database_sha256": manifest["database"]["sha256"],
        "checkpoint_id": anchor["checkpoint_id"],
        "state_hash": anchor["state_hash"],
        "entity_generation": manifest["state"]["entity_generation"],
    }


def main() -> int:
    state_root = os.environ.get("CLAYVERSE_STATE_ROOT", "/var/lib/clayverse")
    restore_receipt = _restore_before_db_open(state_root)
    db = UnifiedDB(os.path.join(state_root, "unified.db"))
    IdentityRouter(db, {})
    try:
        recovery = recover_incomplete_episodes(db)
        ClayGraphProjection(db).rebuild()
        clerk_map = _clerk_map()
        clerk_subject = os.environ.get("CLAYVERSE_ACCEPTANCE_CLERK_SUBJECT", "")
        prompt = os.environ.get("CLAYVERSE_ACCEPTANCE_PROMPT", "")
        require_effect, required_effect_capability = _final_required_effect_policy()
        entityos_bridge, entityos_status = _entityos_config()
        if required_effect_capability == "entityos.exec" and entityos_bridge is None:
            raise RuntimeError(
                "final EntityOS acceptance effect is required but EntityOS execution is disabled"
            )

        payload = run_api_acceptance_probe(
            db,
            clerk_map,
            clerk_subject,
            prompt,
            entityos_bridge=entityos_bridge,
            require_effect=require_effect,
            required_effect_capability=required_effect_capability,
        )
        checkpoint_id, state_hash = db.checkpoint("generic-api-direct-probe")
        snapshot = _create_acceptance_snapshot(db)
        payload.update(
            {
                "checkpoint": checkpoint_id,
                "state_hash": state_hash,
                "recovery": recovery,
                "snapshot_restore": restore_receipt,
                "acceptance_snapshot": snapshot,
                "entityos": {
                    "verified": bool(entityos_status.get("verified")),
                    "execution_enabled": bool(entityos_status.get("execution_enabled")),
                    "sha256": entityos_status.get("sha256"),
                },
            }
        )
        print(json.dumps(payload, ensure_ascii=False, sort_keys=True), flush=True)
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
