from __future__ import annotations

import hashlib
import json
import re
import uuid
from pathlib import Path
from typing import Any

from .alignment import Decision, EffectBinding, GateEvidence


def _canon(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def _sha(value: Any) -> str:
    return hashlib.sha256(_canon(value)).hexdigest()


class PolicyKernel:
    """Small deterministic effect authority for OMEGA's broad autonomy grant.

    The kernel is deliberately separate from the executor. It may issue an exact
    ALLOW/DENY decision, but it never executes the effect itself. The executor still
    has to validate every binding field through ``alignment.dispatch``.
    """

    def __init__(self, policy: dict[str, Any], *, policy_ref: str | None = None) -> None:
        if policy.get("schema") != "OMEGA_AUTONOMY_POLICY/v1":
            raise ValueError("unsupported autonomy policy schema")
        self.policy = policy
        self.policy_ref = policy_ref or "sha256:" + _sha(policy)
        self.allowed_ops = frozenset(str(x) for x in policy.get("allowed_ops", ()))
        self.protected = tuple(str(x) for x in policy.get("protected_surfaces", ()))
        self.deny = tuple(re.compile(str(x), re.IGNORECASE | re.MULTILINE) for x in policy.get("deny_regex", ()))

    @classmethod
    def from_path(cls, path: str | Path) -> "PolicyKernel":
        p = Path(path)
        raw = p.read_bytes()
        policy = json.loads(raw.decode("utf-8"))
        return cls(policy, policy_ref=f"file:{p}:sha256:{hashlib.sha256(raw).hexdigest()}")

    def _decision(self, binding: EffectBinding, decision: Decision, reason: str) -> GateEvidence:
        return GateEvidence(
            authority_ref=self.policy_ref,
            decision_id="decision_" + uuid.uuid4().hex,
            decision=decision,
            effect_id=binding.effect_id,
            binding_id=binding.binding_id,
            invocation_id=binding.invocation_id,
            tool_use_id=binding.tool_use_id,
            delegation_id=binding.delegation_id,
            child_identity_sha256=binding.child_identity_sha256,
            request_sha256=binding.request_sha256,
            organ_id=binding.organ_id,
        )

    def authorize(self, binding: EffectBinding, request: dict[str, Any]) -> GateEvidence:
        if not isinstance(request, dict):
            return self._decision(binding, Decision.REQUIRE_CONFIRMATION, "REQUEST_NOT_OBJECT")
        op = str(request.get("op", "")).strip()
        if op not in self.allowed_ops:
            return self._decision(binding, Decision.REQUIRE_CONFIRMATION, f"OP_NOT_IN_AUTONOMY_GRANT:{op or 'EMPTY'}")

        # Reads and status calls are effects only in the audit sense. They remain
        # attributable but are admitted by the broad owner grant.
        if op in {"status", "read_file", "screenshot"}:
            return self._decision(binding, Decision.ALLOW, "OWNER_GRANT_NONDESTRUCTIVE_OBSERVATION")

        if op == "write_text":
            target = str(request.get("path", ""))
            if not target:
                return self._decision(binding, Decision.REQUIRE_CONFIRMATION, "WRITE_WITHOUT_TARGET")
            if any(surface in target for surface in self.protected):
                return self._decision(binding, Decision.DENY, "PROTECTED_SURFACE_WRITE")
            return self._decision(binding, Decision.ALLOW, "OWNER_GRANT_ORDINARY_WRITE")

        command = str(request.get("command", ""))
        if not command:
            return self._decision(binding, Decision.REQUIRE_CONFIRMATION, "EXEC_WITHOUT_COMMAND")

        for pattern in self.deny:
            if pattern.search(command):
                return self._decision(binding, Decision.DENY, f"HARD_DENY_PATTERN:{pattern.pattern}")

        # Protected kernel files may be inspected/tested from exec, but obvious
        # mutation attempts are rejected. This complements the broader regexes in
        # autonomy_policy.json and keeps the executor from weakening its own gate.
        lower = command.lower()
        mutators = (">", "tee ", "sed -i", "perl -pi", "cp ", "mv ", "install ", "cat >")
        if any(surface.lower() in lower for surface in self.protected) and any(x in lower for x in mutators):
            return self._decision(binding, Decision.DENY, "PROTECTED_SURFACE_MUTATION")

        return self._decision(binding, Decision.ALLOW, "OWNER_GRANT_ORDINARY_EXECUTION")


__all__ = ["PolicyKernel"]
