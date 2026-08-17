from __future__ import annotations

import hashlib
import json
import re
import time
from typing import Any

from .store import StaleGeneration, UnifiedDB

METHOD_MEMORY_KINDS = frozenset({
    "framework_candidate",
    "framework",
    "heuristic_candidate",
    "heuristic",
    "failure_pattern",
    "counterexample",
    "method_receipt",
})
PROMOTED_METHOD_KINDS = frozenset({"framework", "heuristic"})

_WORD_RE = re.compile(r"[A-Za-z0-9_À-ÖØ-öø-ÿ-]+", re.UNICODE)
_EXPLICIT_METHOD_RE = re.compile(
    r"(?i)\b(strategy|strategic|plan(?:ning)?|approach|method|diagnos\w*|debug\w*|"
    r"investigat\w*|hypothes\w*|strategie|methode|vorgehen|planen|ursache|analys\w*)\b|"
    r"\bhow\s+should\b|\bwie\s+soll"
)

_FACET_TERMS = {
    "intent": {
        "diagnose": {"diagnose", "diagnosis", "debug", "investigate", "rootcause", "ursache", "analysieren", "analyse"},
        "repair": {"fix", "repair", "recover", "restore", "beheben", "reparieren", "wiederherstellen"},
        "verify": {"verify", "validate", "test", "prove", "prüfen", "pruefen", "validieren", "testen"},
        "design": {"design", "architect", "architecture", "entwerfen", "architektur"},
        "select": {"choose", "select", "decide", "auswählen", "auswaehlen", "entscheiden"},
        "plan": {"plan", "planning", "strategy", "approach", "strategie", "methode", "vorgehen", "planen"},
    },
    "system_shape": {
        "concurrent": {"concurrent", "concurrency", "parallel", "race", "contention", "gleichzeitig"},
        "distributed": {"distributed", "cluster", "multinode", "multi-node", "verteilt"},
        "persistent": {"persistent", "durable", "restart", "recovery", "persist", "neustart"},
        "streaming": {"stream", "streaming", "incremental", "backpressure", "chunk", "chunks"},
        "security_bound": {"permission", "permissions", "auth", "authority", "capability", "provenance", "berechtigung"},
    },
    "failure_shape": {
        "stale_state": {"stale", "generation", "epoch", "veraltet"},
        "intermittent": {"intermittent", "flaky", "sporadic", "sporadisch", "manchmal"},
        "corruption": {"corrupt", "corruption", "beschädigt", "beschaedigt"},
        "timeout_latency": {"timeout", "latency", "slow", "langsam"},
        "replay_identity": {"replay", "duplicate", "idempotent", "identity", "wiederholung"},
        "unknown": {"unknown", "unclear", "unresolved", "unbekannt", "unklar", "offen"},
        "conflict": {"conflict", "contradict", "collision", "konflikt", "widerspruch"},
    },
    "resources": {
        "database": {"db", "database", "sqlite", "sql", "unifieddb", "datenbank"},
        "memory": {"memory", "retrieval", "microclay", "gedächtnis", "gedaechtnis"},
        "network": {"network", "http", "https", "dns", "socket", "tls", "netzwerk"},
        "process": {"process", "exec", "argv", "shell", "prozess"},
        "file": {"file", "path", "filesystem", "repo", "datei"},
        "container": {"container", "docker", "oci", "image"},
        "terminal": {"terminal", "pty", "tmux"},
        "artifact": {"artifact", "artefact", "binary", "build"},
    },
    "constraints": {
        "fail_closed": {"failclosed", "fail-closed", "deny", "reject", "abstain", "unknown", "verweigern"},
        "bounded": {"bounded", "budget", "limit", "cap", "begrenzt"},
        "no_side_effect": {"readonly", "read-only", "shadow", "noeffect", "no-effect"},
        "replay_safe": {"replay", "idempotent", "idempotency"},
        "privacy_bound": {"privacy", "session", "user-bound", "private", "datenschutz"},
    },
}

_REQUIRED_METHOD_FIELDS = frozenset({
    "problem_signature",
    "preconditions",
    "goal_shape",
    "method_steps",
    "invariants",
    "expected_observations",
    "falsifiers",
    "failure_modes",
    "scope_limits",
    "source_episode_ids",
    "supporting_memory_ids",
    "counterexample_memory_ids",
    "provenance",
    "abstraction_version",
    "support_count",
    "success_count",
    "failure_count",
    "calibration",
    "last_validated_at",
    "status",
})

_FACET_WEIGHTS = {
    "intent": 1.0,
    "system_shape": 1.5,
    "failure_shape": 1.5,
    "resources": 1.0,
    "constraints": 1.25,
    "goal_shape": 1.0,
}


def _tokens(text: str) -> set[str]:
    return {x.casefold() for x in _WORD_RE.findall(str(text)) if len(x) > 1}


def _as_string_set(value: Any) -> set[str]:
    if isinstance(value, str):
        return {value.casefold()} if value.strip() else set()
    if isinstance(value, (list, tuple, set)):
        return {str(x).casefold() for x in value if isinstance(x, (str, int, float)) and str(x).strip()}
    return set()


def derive_problem_signature(query: str, resource_refs: list[str] | None = None) -> dict[str, list[str]]:
    """Derive bounded routing facets; this is a retrieval hint, never semantic truth."""
    toks = _tokens(query)
    signature: dict[str, list[str]] = {}
    for facet, classes in _FACET_TERMS.items():
        matched = []
        for canonical, terms in classes.items():
            if toks.intersection({x.casefold() for x in terms}):
                matched.append(canonical)
        if matched:
            signature[facet] = sorted(set(matched))

    if signature.get("intent"):
        signature["goal_shape"] = list(signature["intent"])

    ref_resources: set[str] = set(signature.get("resources", []))
    for ref in resource_refs or []:
        prefix = str(ref).split(":", 1)[0].casefold()
        if prefix in {"repo", "file", "path"}:
            ref_resources.add("file")
        elif prefix == "db":
            ref_resources.add("database")
        elif prefix in {"service", "deploy"}:
            ref_resources.add("network")
        elif prefix == "machine":
            ref_resources.add("artifact")
    if ref_resources:
        signature["resources"] = sorted(ref_resources)
    return signature


def _normalize_signature(raw: Any) -> dict[str, set[str]]:
    if not isinstance(raw, dict):
        return {}
    out: dict[str, set[str]] = {}
    for key, value in raw.items():
        if not isinstance(key, str):
            continue
        values = _as_string_set(value)
        if values:
            out[key.casefold()] = values
    return out


def _structural_match(query_sig: dict[str, set[str]], method_sig: dict[str, set[str]]) -> tuple[float, list[str]]:
    weighted = 0.0
    denom = 0.0
    matched_facets: list[str] = []
    for facet, values in method_sig.items():
        if not values:
            continue
        weight = _FACET_WEIGHTS.get(facet, 0.75)
        denom += weight
        qvals = query_sig.get(facet, set())
        if not qvals:
            continue
        inter = qvals.intersection(values)
        union = qvals.union(values)
        if inter:
            matched_facets.append(facet)
            weighted += weight * (len(inter) / max(1, len(union)))
    return (weighted / denom if denom else 0.0), sorted(matched_facets)


class MethodTransfer:
    """Fail-closed Stage-B analogical retrieval over promoted method memory."""

    POLICY_VERSION = 1
    MIN_STRUCTURAL_SCORE = 0.45
    MIN_MATCHED_FACETS = 2
    MAX_SOURCE_ROWS = 2_000
    MAX_METHODS = 4
    MAX_CONTEXT_CHARS = 12_000

    def __init__(self, db: UnifiedDB):
        self.db = db

    @staticmethod
    def should_trigger(*, evidence_status: str, query: str) -> tuple[bool, str]:
        status = str(evidence_status).upper()
        if status in {"UNKNOWN", "UNDERCOVERED"}:
            return True, "EVIDENCE_" + status
        if _EXPLICIT_METHOD_RE.search(str(query)):
            return True, "EXPLICIT_METHOD_REQUEST"
        return False, "NOT_TRIGGERED"

    @staticmethod
    def _safe_json(value: Any) -> Any:
        if isinstance(value, (dict, list, str, int, float, bool)) or value is None:
            return value
        return str(value)

    def _parse_promoted_method(self, row: Any) -> dict[str, Any] | None:
        if str(row["kind"]) not in PROMOTED_METHOD_KINDS:
            return None
        try:
            env = json.loads(row["value"])
        except (TypeError, json.JSONDecodeError):
            return None
        if not isinstance(env, dict) or not _REQUIRED_METHOD_FIELDS.issubset(env):
            return None
        if env.get("status") != "PROMOTED" or not isinstance(env.get("problem_signature"), dict):
            return None
        list_fields = (
            "preconditions", "method_steps", "invariants", "expected_observations",
            "falsifiers", "failure_modes", "scope_limits", "source_episode_ids",
            "supporting_memory_ids", "counterexample_memory_ids",
        )
        if any(not isinstance(env.get(field), list) for field in list_fields):
            return None
        if not isinstance(env.get("provenance"), dict):
            return None
        try:
            support = int(env["support_count"])
            success = int(env["success_count"])
            failure = int(env["failure_count"])
            calibration = float(env["calibration"])
        except (TypeError, ValueError):
            return None
        if support < 2 or success < 0 or failure < 0 or not (0.0 <= calibration <= 1.0):
            return None
        signature = _normalize_signature(env["problem_signature"])
        goal_shape = _as_string_set(env.get("goal_shape"))
        if goal_shape:
            signature.setdefault("goal_shape", set()).update(goal_shape)
        if not signature:
            return None
        return {"row": row, "env": env, "signature": signature, "calibration": calibration}

    @staticmethod
    def _parse_limiter(row: Any) -> dict[str, Any] | None:
        try:
            env = json.loads(row["value"])
        except (TypeError, json.JSONDecodeError):
            return None
        if not isinstance(env, dict) or not isinstance(env.get("problem_signature"), dict):
            return None
        if str(env.get("status", "")).upper() not in {"VERIFIED", "PROMOTED"}:
            return None
        try:
            severity = float(env.get("severity", 0.5))
        except (TypeError, ValueError):
            return None
        if not (0.0 <= severity <= 1.0):
            return None
        method_ids = env.get("method_ids", [])
        if method_ids is not None and not isinstance(method_ids, list):
            return None
        return {
            "memory_id": str(row["memory_id"]),
            "signature": _normalize_signature(env["problem_signature"]),
            "severity": severity,
            "method_ids": {str(x) for x in (method_ids or [])},
        }

    @staticmethod
    def _public_method(candidate: dict[str, Any]) -> dict[str, Any]:
        row, env = candidate["row"], candidate["env"]
        return {
            "method_id": str(row["memory_id"]),
            "kind": str(row["kind"]),
            "subject": str(row["subject"]),
            "structural_score": round(float(candidate["structural_score"]), 6),
            "calibration": float(candidate["calibration"]),
            "matched_facets": list(candidate["matched_facets"]),
            "preconditions": list(env["preconditions"]),
            "goal_shape": MethodTransfer._safe_json(env["goal_shape"]),
            "method_steps": list(env["method_steps"]),
            "invariants": list(env["invariants"]),
            "expected_observations": list(env["expected_observations"]),
            "falsifiers": list(env["falsifiers"]),
            "failure_modes": list(env["failure_modes"]),
            "scope_limits": list(env["scope_limits"]),
            "source_episode_ids": list(env["source_episode_ids"]),
            "supporting_memory_ids": list(env["supporting_memory_ids"]),
            "counterexample_memory_ids": sorted(set(env["counterexample_memory_ids"]).union(candidate["limiter_ids"])),
            "provenance": MethodTransfer._safe_json(env["provenance"]),
            "truth_authority": False,
            "effect_authority": False,
        }

    def _replay(self, receipt_row: Any, *, query_hash: str, user_id: str, session_id: str,
                turn_id: str, episode_id: str, generation: int) -> dict[str, Any]:
        try:
            receipt = json.loads(receipt_row["value"])
        except (TypeError, json.JSONDecodeError) as exc:
            raise StaleGeneration("method_retrieval_receipt") from exc
        identity = (
            receipt.get("query_sha256") == query_hash
            and receipt.get("user_id") == user_id
            and receipt.get("session_id") == session_id
            and receipt.get("turn_id") == turn_id
            and receipt.get("episode_id") == episode_id
            and int(receipt.get("generation", -1)) == int(generation)
        )
        if not identity:
            raise StaleGeneration("method_retrieval_identity")
        items = receipt.get("selected", [])
        if not isinstance(items, list):
            raise StaleGeneration("method_retrieval_receipt")
        compact = {k: v for k, v in receipt.items() if k != "selected"}
        compact["replayed"] = True
        return {"items": items, "receipt": compact}

    def retrieve(
        self,
        *,
        query: str,
        evidence_status: str,
        user_id: str,
        session_id: str,
        turn_id: str,
        episode_id: str,
        causal_id: str,
        generation: int,
        resource_refs: list[str] | None = None,
        limit: int = MAX_METHODS,
        budget_chars: int = MAX_CONTEXT_CHARS,
    ) -> dict[str, Any]:
        if not isinstance(query, str) or not query.strip():
            raise ValueError("method retrieval requires a non-empty query")
        if limit < 1 or limit > self.MAX_METHODS:
            raise ValueError("invalid method retrieval limit")
        if budget_chars < 512 or budget_chars > self.MAX_CONTEXT_CHARS:
            raise ValueError("invalid method retrieval budget")
        self.db.assert_live_generation(session_id, generation)

        triggered, trigger = self.should_trigger(evidence_status=evidence_status, query=query)
        query_hash = hashlib.sha256(query.encode("utf-8")).hexdigest()
        if not triggered:
            return {
                "items": [],
                "receipt": {
                    "policy_version": self.POLICY_VERSION,
                    "status": "NOT_TRIGGERED",
                    "trigger": trigger,
                    "query_sha256": query_hash,
                    "truth_authority": False,
                    "effect_authority": False,
                    "replayed": False,
                },
            }

        receipt_id = f"method-retrieval:{causal_id}"
        existing = self.db.db.execute(
            "SELECT * FROM durable_memory WHERE memory_id=? AND kind='method_receipt'",
            (receipt_id,),
        ).fetchone()
        if existing is not None:
            return self._replay(
                existing, query_hash=query_hash, user_id=user_id, session_id=session_id,
                turn_id=turn_id, episode_id=episode_id, generation=generation,
            )

        query_sig_raw = derive_problem_signature(query, resource_refs)
        query_sig = _normalize_signature(query_sig_raw)
        rows = self.db.db.execute(
            "SELECT * FROM durable_memory WHERE kind IN ('framework','heuristic') "
            "AND (user_id IS NULL OR user_id=?) "
            "AND (source_turn_id IS NULL OR source_turn_id<>?) "
            "ORDER BY ts DESC LIMIT ?",
            (user_id, turn_id, self.MAX_SOURCE_ROWS),
        ).fetchall()

        parsed: list[dict[str, Any]] = []
        malformed = 0
        for row in rows:
            method = self._parse_promoted_method(row)
            if method is None:
                malformed += 1
                continue
            score, facets = _structural_match(query_sig, method["signature"])
            if score < self.MIN_STRUCTURAL_SCORE or len(facets) < self.MIN_MATCHED_FACETS:
                continue
            method["base_structural_score"] = score
            method["matched_facets"] = facets
            method["limiter_ids"] = []
            parsed.append(method)

        limiter_rows = self.db.db.execute(
            "SELECT * FROM durable_memory WHERE kind IN ('failure_pattern','counterexample') "
            "AND (user_id IS NULL OR user_id=?) "
            "AND (source_turn_id IS NULL OR source_turn_id<>?) "
            "ORDER BY ts DESC LIMIT ?",
            (user_id, turn_id, self.MAX_SOURCE_ROWS),
        ).fetchall()
        limiters = [x for x in (self._parse_limiter(row) for row in limiter_rows) if x is not None]

        ranked = []
        for method in parsed:
            method_id = str(method["row"]["memory_id"])
            penalty = 0.0
            hard_block = False
            for limiter in limiters:
                if limiter["method_ids"] and method_id not in limiter["method_ids"]:
                    continue
                lscore, lfacets = _structural_match(query_sig, limiter["signature"])
                if lscore < self.MIN_STRUCTURAL_SCORE or len(lfacets) < self.MIN_MATCHED_FACETS:
                    continue
                method["limiter_ids"].append(limiter["memory_id"])
                penalty += 0.50 * limiter["severity"] * lscore
                if limiter["severity"] >= 0.85 and lscore >= 0.75:
                    hard_block = True
            if hard_block:
                continue
            method["structural_score"] = method["base_structural_score"] * method["calibration"] * max(0.0, 1.0 - penalty)
            if method["structural_score"] >= self.MIN_STRUCTURAL_SCORE:
                ranked.append(method)

        ranked.sort(
            key=lambda x: (x["structural_score"], x["calibration"], float(x["row"]["ts"]), str(x["row"]["memory_id"])),
            reverse=True,
        )
        selected: list[dict[str, Any]] = []
        chars = 0
        for method in ranked:
            public = self._public_method(method)
            item_chars = len(json.dumps(public, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
            if chars + item_chars > budget_chars:
                continue
            selected.append(public)
            chars += item_chars
            if len(selected) >= limit:
                break

        now = time.time()
        status = "METHOD_PRESENT" if selected else "NO_METHOD"
        receipt = {
            "policy_version": self.POLICY_VERSION,
            "status": status,
            "trigger": trigger,
            "query_sha256": query_hash,
            "user_id": user_id,
            "session_id": session_id,
            "turn_id": turn_id,
            "episode_id": episode_id,
            "causal_id": causal_id,
            "generation": int(generation),
            "problem_signature": query_sig_raw,
            "candidate_count": len(parsed),
            "malformed_rejected": malformed,
            "selected_count": len(selected),
            "selected_method_ids": [x["method_id"] for x in selected],
            "chars_selected": chars,
            "truth_authority": False,
            "effect_authority": False,
            "replayed": False,
        }
        persisted = dict(receipt)
        persisted["selected"] = selected
        self.db.db.execute(
            "INSERT INTO durable_memory(memory_id,kind,subject,value,source_turn_id,user_id,ts,provenance) "
            "VALUES(?,?,?,?,?,?,?,?)",
            (
                receipt_id,
                "method_receipt",
                f"method_retrieval:{causal_id}",
                json.dumps(persisted, ensure_ascii=False, sort_keys=True, separators=(",", ":")),
                turn_id,
                user_id,
                now,
                json.dumps({
                    "source": "microclay:method-transfer",
                    "policy_version": self.POLICY_VERSION,
                    "causal_id": causal_id,
                    "truth_authority": False,
                    "effect_authority": False,
                }, sort_keys=True, separators=(",", ":")),
            ),
        )
        return {"items": selected, "receipt": receipt}
