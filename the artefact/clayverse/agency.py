from __future__ import annotations

import json
from typing import Any

from .autonomy import AutonomyController
from .store import UnifiedDB

PROFILE_KEY = "agency_profile_v1"
PROFILE_SCHEMA = "ClayVerseAgencyProfile/v1"


class AgencyView:
    """Grounded identity/telemetry view over the one canonical AutonomyController.

    No goal or milestone authority lives here. Durable goals remain exclusively in
    UnifiedDB meta['autonomy_state_v1']. The Concept/Prototype/Final view is derived
    deterministically from that canonical state and EffectJournal evidence.
    """

    PROFILE = {
        "schema": PROFILE_SCHEMA,
        "entity_id": "clayverse",
        "display_name": "Clay",
        "identity_mode": "PERSISTENT_GOAL_AGENT",
        "substrate_anchor": "SERVER_UNIFIEDDB",
        "behavior_mode": "PROACTIVE_GROUNDED",
    }

    def __init__(self, db: UnifiedDB):
        self.db = db
        self.autonomy = AutonomyController(db)
        encoded = json.dumps(self.PROFILE, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        with self.db.tx() as tx:
            row = tx.execute("SELECT value FROM meta WHERE key=?", (PROFILE_KEY,)).fetchone()
            if row is None:
                tx.execute("INSERT INTO meta(key,value) VALUES(?,?)", (PROFILE_KEY, encoded))
            elif row[0] != encoded:
                raise RuntimeError("agency profile does not match canonical runtime contract")

    @staticmethod
    def _effect_ok(row) -> bool:
        if row["status"] != "VERIFIED" or not row["outcome"]:
            return False
        try:
            payload = json.loads(row["outcome"])
        except (json.JSONDecodeError, TypeError):
            return False
        return isinstance(payload, dict) and payload.get("ok") is True

    def metrics(self, user_id: str | None = None) -> dict[str, Any]:
        if user_id is None:
            rows = self.db.db.execute(
                "SELECT user_id,capability,status,outcome FROM effects WHERE capability!='state.noop'"
            ).fetchall()
        else:
            rows = self.db.db.execute(
                "SELECT user_id,capability,status,outcome FROM effects WHERE capability!='state.noop' AND user_id=?",
                (user_id,),
            ).fetchall()
        verified = sum(1 for row in rows if self._effect_ok(row))
        failed = len(rows) - verified
        denominator = verified + failed
        goals = self.autonomy.snapshot(user_id=user_id)["goals"]
        return {
            "verified_effect_steps": verified,
            "failed_effect_steps": failed,
            "completed_goals": sum(1 for goal in goals if goal["status"] == "COMPLETED"),
            "ers": round(verified / denominator, 4) if denominator else 0.0,
            "ers_role": "telemetry_only_not_authority",
        }

    @staticmethod
    def milestone_projection(goal: dict[str, Any]) -> dict[str, Any]:
        """Derived three-phase delivery lens; never a second completion authority."""
        effects = int(goal["counters"]["effects"])
        evidence = bool(goal["evidence_effect_ids"])
        completed = goal["status"] == "COMPLETED"
        concept = "PASSED" if effects > 0 or evidence or completed else "ACTIVE"
        if completed or evidence:
            prototype = "PASSED"
        elif effects > 0:
            prototype = "ACTIVE"
        else:
            prototype = "PENDING"
        if completed:
            final = "PASSED"
        elif evidence or goal["status"] == "VERIFYING":
            final = "ACTIVE"
        else:
            final = "PENDING"
        return {
            "authority": "DERIVED_FROM_AUTONOMY_AND_EFFECT_STATE",
            "CONCEPT": concept,
            "PROTOTYPE": prototype,
            "FINAL": final,
        }

    def snapshot(self, *, user_id: str | None = None) -> dict[str, Any]:
        autonomy = self.autonomy.snapshot(user_id=user_id)
        goals = []
        for raw in autonomy["goals"]:
            goal = dict(raw)
            goal["delivery_milestones"] = self.milestone_projection(goal)
            goals.append(goal)
        return {
            "authority": "UnifiedDB",
            "profile": dict(self.PROFILE),
            "autonomy": {
                "schema": autonomy["schema"],
                "revision": autonomy["revision"],
                "goals": goals,
            },
            "metrics": self.metrics(user_id),
            "grounding_laws": [
                "Identity profile and durable goals come from canonical UnifiedDB state, not model assertions.",
                "The full durable goal objective is copied from a canonical owner user turn; cognition cannot rewrite it.",
                "Runtime capabilities come from EffectGate, never from self-description.",
                "Proposal is not admission; admission is not execution; execution is not verified success.",
                "Goal completion requires the AutonomyController completion contract and canonical evidence.",
                "Concept/Prototype/Final delivery milestones are a deterministic projection, not a competing state authority.",
                "ERS is telemetry only and cannot grant capabilities, bypass gates, or complete a goal.",
            ],
        }
