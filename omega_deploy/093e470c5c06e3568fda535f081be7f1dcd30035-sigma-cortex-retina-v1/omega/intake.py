from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any, Mapping

from .assembly import AssemblyError, AssemblyManifest, load_probes, load_source_registry
from .unified_store import canon, digest


ENTRY_SCHEMA = "OMEGA_TYPED_ENTRY/v1"
CANDIDATE_SCHEMA = "OMEGA_COGNITIVE_CANDIDATE/v1"


class IntakeError(RuntimeError):
    """A task or donor-cognition input cannot safely enter canonical GRID."""


def _read_object(value: str) -> dict[str, Any]:
    if value == "-":
        data = json.load(__import__("sys").stdin)
    else:
        path = Path(value)
        if path.exists():
            data = json.loads(path.read_text(encoding="utf-8"))
        else:
            data = json.loads(value)
    if not isinstance(data, dict) or not data:
        raise IntakeError("NONEMPTY_JSON_OBJECT_REQUIRED")
    return data


def _atomic_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + f".tmp-{os.getpid()}")
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    with open(tmp, "w", encoding="utf-8") as fh:
        fh.write(raw)
        fh.flush()
        os.fsync(fh.fileno())
    os.replace(tmp, path)


class CanonicalIntake:
    """The one file-level ingress into the already-existing GRID inbox.

    It creates no scheduler, store, worker, effect authority or donor daemon. Generic
    typed entries are merely queued for canonical GRID. External cognition can enter
    only as a provenance-bound candidate from a manifest-declared CANDIDATE_ONLY organ
    whose current provider binding has an exact VERIFIED assembly probe.

    A nested donor candidate is intentionally never copied into top-level ``effect`` or
    ``execution`` fields. Therefore donor output first returns to MASTER/GRID cognition;
    any later real mutation must be emitted as a new normal GRID task and still cross
    alignment -> relay -> receipt.
    """

    def __init__(self, *, repo_root: str | Path, runtime_root: str | Path) -> None:
        self.repo_root = Path(repo_root).resolve()
        self.runtime_root = Path(runtime_root).resolve()
        self.inbox = self.runtime_root / "inbox"
        self.manifest = AssemblyManifest.from_path(self.repo_root / "config" / "assembly.json")
        _, self.sources = load_source_registry(self.repo_root / "config" / "sources.json")
        self.manifest.validate(self.sources)
        self.probes = load_probes(self.runtime_root / "assembly" / "PROBES.json")

    def _put(self, payload: dict[str, Any], *, task_id: str | None = None) -> str:
        core = dict(payload)
        core.pop("task_id", None)
        requested = str(task_id or payload.get("task_id") or "").strip()
        tid = requested or ("task_" + digest(core)[:32])
        if not tid or tid in {".", ".."} or "/" in tid or "\\" in tid:
            raise IntakeError("INVALID_TASK_ID")

        final = dict(core)
        final["task_id"] = tid
        target = self.inbox / f"{tid}.json"
        consumed = target.with_suffix(".consumed")
        expected = canon(final)
        for existing in (target, consumed):
            if not existing.exists():
                continue
            current = json.loads(existing.read_text(encoding="utf-8"))
            if canon(current) != expected:
                raise IntakeError(f"TASK_ID_CONTENT_CONFLICT:{tid}")
            return tid

        _atomic_json(target, final)
        return tid

    def submit_entry(self, entry: Mapping[str, Any], *, task_id: str | None = None) -> str:
        if not isinstance(entry, Mapping) or not entry:
            raise IntakeError("NONEMPTY_ENTRY_REQUIRED")
        payload = dict(entry)
        payload["_omega_entry"] = {
            "schema": ENTRY_SCHEMA,
            "canonical_ingress": "GRID_INBOX",
            "authority": "TASK_INPUT_ONLY",
            "effect_authority": "DEFER_TO_OMEGA_ALIGNMENT_AND_RELAY",
        }
        return self._put(payload, task_id=task_id)

    def _verified_provider(self, organ_id: str, source_id: str | None) -> tuple[str, dict[str, Any]]:
        organ = self.manifest.by_id.get(organ_id)
        if organ is None:
            raise IntakeError(f"UNKNOWN_ASSEMBLY_ORGAN:{organ_id}")
        if organ.authority != "CANDIDATE_ONLY":
            raise IntakeError(f"ORGAN_NOT_CANDIDATE_ONLY:{organ_id}:{organ.authority}")

        providers = [p for p in organ.providers if source_id is None or p.source_id == source_id]
        if len(providers) != 1:
            raise IntakeError(f"PROVIDER_SELECTION_NOT_UNIQUE:{organ_id}")
        provider = providers[0]

        matches = [
            dict(p)
            for p in self.probes
            if str(p.get("organ_id")) == organ_id
            and str(p.get("source_id")) == provider.source_id
            and p.get("verified") is True
        ]
        if not matches:
            raise IntakeError(f"CURRENT_VERIFIED_PROVIDER_PROBE_REQUIRED:{organ_id}:{provider.source_id}")

        probe = matches[-1]
        if not probe.get("source_commit") or not probe.get("subject") or not probe.get("observed_at"):
            raise IntakeError(f"INCOMPLETE_PROVIDER_PROBE:{organ_id}:{provider.source_id}")
        return provider.source_id, probe

    def submit_candidate(
        self,
        organ_id: str,
        candidate: Mapping[str, Any],
        *,
        source_id: str | None = None,
        task_id: str | None = None,
    ) -> str:
        if not isinstance(candidate, Mapping) or not candidate:
            raise IntakeError("NONEMPTY_CANDIDATE_REQUIRED")
        bound_source, probe = self._verified_provider(str(organ_id), source_id)
        task = {
            "kind": "cognitive_candidate",
            "needs_master": True,
            "master_reasoning": True,
            "candidate_envelope": {
                "schema": CANDIDATE_SCHEMA,
                "organ_id": str(organ_id),
                "source_id": bound_source,
                "authority": "CANDIDATE_ONLY",
                "promotion": "GRID_REENTRY_AND_EVIDENCE_REQUIRED",
                "may_dispatch_effects": False,
                "provider_probe": {
                    "source_commit": probe["source_commit"],
                    "subject": probe["subject"],
                    "observed_at": probe["observed_at"],
                },
                "payload": dict(candidate),
            },
            "constraints": [
                "NO_SELF_PROMOTION",
                "NO_DIRECT_EFFECT_DISPATCH",
                "PRESERVE_SOURCE_PROVENANCE",
                "REENTER_CANONICAL_GRID",
            ],
            "_omega_entry": {
                "schema": ENTRY_SCHEMA,
                "canonical_ingress": "GRID_INBOX",
                "authority": "CANDIDATE_INPUT_ONLY",
                "effect_authority": "DEFER_TO_OMEGA_ALIGNMENT_AND_RELAY",
            },
        }
        return self._put(task, task_id=task_id)


def main() -> int:
    ap = argparse.ArgumentParser(description="OMEGA canonical GRID intake")
    ap.add_argument("--repo-root", default=os.getenv("OMEGA_REPO_ROOT", "/workspace/omega_runtime/current"))
    ap.add_argument("--runtime-root", default=os.getenv("OMEGA_RUNTIME_ROOT", "/workspace/omega_runtime/state"))
    sub = ap.add_subparsers(dest="command", required=True)

    entry = sub.add_parser("entry")
    entry.add_argument("payload", help="JSON object, path, or - for stdin")
    entry.add_argument("--task-id")

    candidate = sub.add_parser("candidate")
    candidate.add_argument("organ_id")
    candidate.add_argument("payload", help="JSON object, path, or - for stdin")
    candidate.add_argument("--source-id")
    candidate.add_argument("--task-id")

    a = ap.parse_args()
    intake = CanonicalIntake(repo_root=a.repo_root, runtime_root=a.runtime_root)
    try:
        if a.command == "entry":
            tid = intake.submit_entry(_read_object(a.payload), task_id=a.task_id)
        else:
            tid = intake.submit_candidate(
                a.organ_id,
                _read_object(a.payload),
                source_id=a.source_id,
                task_id=a.task_id,
            )
    except (AssemblyError, IntakeError, json.JSONDecodeError) as exc:
        print(json.dumps({"ok": False, "error": f"{type(exc).__name__}:{exc}"}, ensure_ascii=False))
        return 2
    print(json.dumps({"ok": True, "task_id": tid}, ensure_ascii=False))
    return 0


__all__ = ["CanonicalIntake", "IntakeError", "ENTRY_SCHEMA", "CANDIDATE_SCHEMA"]


if __name__ == "__main__":
    raise SystemExit(main())
