#!/usr/bin/env python3
"""Idempotently converge the canonical structured reference runtime effect surface.

This is a bounded source migration helper for the current go cycle. It edits the
existing canonical runtime in place; it does not create a second runtime path.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / "tools" / "clay_profile_pipeline_runtime.py"
CONTRACT = ROOT / "the artefact" / "blogpost_entity" / "native" / "NATIVE_PROFILE_V2_PARITY_CONTRACT.json"


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count == 0:
        if new in text:
            return text
        raise SystemExit(f"missing expected source anchor: {label}")
    if count != 1:
        raise SystemExit(f"non-unique source anchor {label}: {count}")
    return text.replace(old, new, 1)


def patch_runtime() -> bool:
    text = RUNTIME.read_text(encoding="utf-8")
    original = text

    text = text.replace(
        'VERSION = "clay-profile-pipeline-runtime/0.1"',
        'VERSION = "clay-profile-pipeline-runtime/0.2"',
    )
    text = text.replace('            "profile_load",\n', '            "pipeline_profile_read",\n')
    text = text.replace('            "provider_chat_json",\n', '            "inference_generate",\n')
    text = text.replace(
        '            if kind == "profile_load":\n                result = self._profile_load(payload)',
        '            if kind == "pipeline_profile_read":\n                result = self._pipeline_profile_read(payload)',
    )
    text = text.replace(
        '            elif kind == "provider_chat_json":\n                result = self._provider_chat_json(payload)',
        '            elif kind == "inference_generate":\n                result = self._inference_generate(payload)',
    )

    profile_anchor = '    def _profile_load(self, p: dict[str, Any]) -> dict[str, Any]:\n'
    if '    def _pipeline_profile_read(self, p: dict[str, Any]) -> dict[str, Any]:\n' not in text:
        if profile_anchor not in text:
            raise SystemExit("missing _profile_load insertion anchor")
        profile_methods = '''    @staticmethod
    def _canonical_profile_json(profile: dict[str, Any]) -> str:
        return json.dumps(
            profile,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )

    @staticmethod
    def _forbid_embedded_profile_secrets(value: Any, path: str = "") -> None:
        secret_value_keys = {
            "api_token",
            "api_key",
            "access_token",
            "secret_value",
            "password",
            "private_key",
            "client_secret",
            "bearer_token",
            "refresh_token",
            "auth_token",
        }
        if isinstance(value, dict):
            for key, item in value.items():
                key_text = str(key)
                child = f"{path}.{key_text}" if path else key_text
                if key_text.lower() in secret_value_keys and item not in (None, "", [], {}):
                    raise PipelineFault("PROFILE_CONTAINS_SECRET_VALUE:" + child)
                ProfilePipelineRuntime._forbid_embedded_profile_secrets(item, child)
        elif isinstance(value, list):
            for index, item in enumerate(value):
                ProfilePipelineRuntime._forbid_embedded_profile_secrets(
                    item, f"{path}[{index}]"
                )

    @classmethod
    def _normalize_profile(cls, profile: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(profile, dict):
            raise PipelineFault("PROFILE_NOT_OBJECT")
        out = json.loads(json.dumps(profile))
        if out.get("schema") not in {"clay-pipeline-profile/v1", "clay-pipeline-profile/v2"}:
            raise PipelineFault("BAD_PROFILE_SCHEMA")
        if "inference" not in out and "provider" in out:
            out["inference"] = out.pop("provider")
        for field in ("profile_id", "inference", "personality", "sources", "state_metrics", "gate"):
            if field not in out:
                raise PipelineFault("PROFILE_MISSING:" + field)
        if not isinstance(out["inference"], dict) or not out["inference"].get("kind"):
            raise PipelineFault("PROFILE_BAD_INFERENCE")
        cls._forbid_embedded_profile_secrets(out)
        return out

    @staticmethod
    def _ensure_profile_schema(db: sqlite3.Connection) -> None:
        db.execute(
            """CREATE TABLE IF NOT EXISTS eos_pipeline_profile(
                 singleton INTEGER PRIMARY KEY CHECK(singleton=1),
                 profile_id TEXT NOT NULL,
                 profile_hash TEXT NOT NULL,
                 profile_json TEXT NOT NULL,
                 updated_at REAL NOT NULL)"""
        )

    def import_profile(
        self,
        entity_db: str,
        profile_or_path: dict[str, Any] | str | Path,
    ) -> dict[str, Any]:
        profile = (
            json.loads(self._resolve(str(profile_or_path)).read_text(encoding="utf-8"))
            if isinstance(profile_or_path, (str, Path))
            else profile_or_path
        )
        normalized = self._normalize_profile(profile)
        raw = self._canonical_profile_json(normalized)
        digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()
        with self._db(entity_db) as db:
            self._ensure_profile_schema(db)
            db.execute(
                """INSERT INTO eos_pipeline_profile(
                       singleton,profile_id,profile_hash,profile_json,updated_at)
                   VALUES(1,?,?,?,?)
                   ON CONFLICT(singleton) DO UPDATE SET
                     profile_id=excluded.profile_id,
                     profile_hash=excluded.profile_hash,
                     profile_json=excluded.profile_json,
                     updated_at=excluded.updated_at""",
                (normalized["profile_id"], digest, raw, time.time()),
            )
        return {
            "ok": True,
            "profile_id": normalized["profile_id"],
            "profile_hash": digest,
        }

    def _pipeline_profile_read(self, p: dict[str, Any]) -> dict[str, Any]:
        try:
            with self._db(str(p["entity_db"])) as db:
                self._ensure_profile_schema(db)
                row = db.execute(
                    "SELECT profile_id,profile_hash,profile_json "
                    "FROM eos_pipeline_profile WHERE singleton=1"
                ).fetchone()
            if row is None:
                raise PipelineFault("NO_ACTIVE_PROFILE")
            profile = self._normalize_profile(json.loads(row["profile_json"]))
            raw = self._canonical_profile_json(profile)
            digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()
            if digest != str(row["profile_hash"]):
                raise PipelineFault("PROFILE_INTEGRITY_MISMATCH")
            if str(profile["profile_id"]) != str(row["profile_id"]):
                raise PipelineFault("PROFILE_ID_MISMATCH")
            return {"ok": True, "profile": profile, "profile_hash": digest}
        except Exception as exc:
            return {"ok": False, "error_kind": type(exc).__name__, "error": str(exc)}

'''
        text = text.replace(profile_anchor, profile_methods + profile_anchor, 1)

    inference_anchor = '    def _provider_chat_json(self, p: dict[str, Any]) -> dict[str, Any]:\n'
    if '    def _inference_generate(self, p: dict[str, Any]) -> dict[str, Any]:\n' not in text:
        if inference_anchor not in text:
            raise SystemExit("missing _provider_chat_json insertion anchor")
        inference_method = '''    def _inference_generate(self, p: dict[str, Any]) -> dict[str, Any]:
        try:
            inference = p.get("inference")
            if not isinstance(inference, dict) or not inference.get("kind"):
                raise PipelineFault("INFERENCE_CONFIG_MISSING")
            request = dict(p)
            request["provider"] = inference
            return self._provider_chat_json(request)
        except Exception as exc:
            return {"ok": False, "error_kind": type(exc).__name__, "error": str(exc)}

'''
        text = text.replace(inference_anchor, inference_method + inference_anchor, 1)

    old_pointer = '''    @staticmethod
    def _pointer(value: Any, pointer: str) -> Any:
        current = value
        for part in str(pointer).split("."):
            current = current[int(part)] if isinstance(current, list) else current[part]
        return current
'''
    new_pointer = '''    @staticmethod
    def _pointer(value: Any, pointer: str) -> Any:
        current = value
        raw = str(pointer or "")
        if raw.startswith("/"):
            parts = [part.replace("~1", "/").replace("~0", "~") for part in raw.split("/")[1:]]
        else:
            parts = [part for part in raw.split(".") if part]
        for part in parts:
            current = current[int(part)] if isinstance(current, list) else current[part]
        return current
'''
    if old_pointer in text:
        text = text.replace(old_pointer, new_pointer, 1)
    elif new_pointer not in text:
        raise SystemExit("pointer implementation drifted")

    forbidden_quoted = ('"profile_load"', '"provider_chat_json"')
    for token in forbidden_quoted:
        if token in text:
            raise SystemExit(f"legacy effect name remains publicly encoded: {token}")
    for token in ('"pipeline_profile_read"', '"inference_generate"'):
        if token not in text:
            raise SystemExit(f"current effect name missing: {token}")

    if text != original:
        RUNTIME.write_text(text, encoding="utf-8")
        return True
    return False


def patch_contract() -> bool:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    original = json.dumps(contract, sort_keys=True)
    gap = contract.get("reference_runtime_effect_surface")
    if not isinstance(gap, dict):
        raise SystemExit("reference_runtime_effect_surface contract missing")
    gap["status"] = "PARITY"
    gap["missing_current_effects"] = []
    gap["stale_current_effects"] = []
    rendered = json.dumps(contract, indent=2, ensure_ascii=False) + "\n"
    if json.dumps(contract, sort_keys=True) != original:
        CONTRACT.write_text(rendered, encoding="utf-8")
        return True
    return False


def main() -> None:
    changed_runtime = patch_runtime()
    changed_contract = patch_contract()
    print(json.dumps({
        "runtime_changed": changed_runtime,
        "contract_changed": changed_contract,
        "runtime": str(RUNTIME.relative_to(ROOT)),
        "contract": str(CONTRACT.relative_to(ROOT)),
    }, sort_keys=True))


if __name__ == "__main__":
    main()
