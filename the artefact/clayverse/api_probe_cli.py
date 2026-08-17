from __future__ import annotations

import json
import os

from .api_acceptance_probe import run_api_acceptance_probe
from .graph import ClayGraphProjection
from .identity import IdentityRouter
from .recovery import recover_incomplete_episodes
from .service import _acceptance_effect_policy, _clerk_map, _entityos_config
from .store import UnifiedDB


def main() -> int:
    state_root = os.environ.get("CLAYVERSE_STATE_ROOT", "/var/lib/clayverse")
    os.makedirs(state_root, exist_ok=True)
    db = UnifiedDB(os.path.join(state_root, "unified.db"))
    IdentityRouter(db, {})
    try:
        recovery = recover_incomplete_episodes(db)
        ClayGraphProjection(db).rebuild()
        clerk_map = _clerk_map()
        clerk_subject = os.environ.get("CLAYVERSE_ACCEPTANCE_CLERK_SUBJECT", "")
        prompt = os.environ.get("CLAYVERSE_ACCEPTANCE_PROMPT", "")
        require_effect, required_effect_capability = _acceptance_effect_policy()
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
        payload.update(
            {
                "checkpoint": checkpoint_id,
                "state_hash": state_hash,
                "recovery": recovery,
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
