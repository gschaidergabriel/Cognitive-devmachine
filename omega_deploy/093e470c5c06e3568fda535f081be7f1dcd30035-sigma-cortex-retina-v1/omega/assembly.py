from __future__ import annotations

import argparse
import dataclasses
import json
import os
import time
from pathlib import Path
from typing import Any, Iterable, Mapping

from .unified_store import UnifiedStore, digest, now


class AssemblyError(RuntimeError):
    """The OMEGA composition manifest violates a hard integration invariant."""


@dataclasses.dataclass(frozen=True)
class ProviderSpec:
    source_id: str
    source_path: str
    entrypoint: str
    source_commit_policy: str


@dataclasses.dataclass(frozen=True)
class OrganSpec:
    organ_id: str
    role: str
    authority: str
    activation_policy: str
    providers: tuple[ProviderSpec, ...]
    inputs: tuple[str, ...]
    outputs: tuple[str, ...]
    constraints: tuple[str, ...]


@dataclasses.dataclass(frozen=True)
class GuardDecision:
    state: str
    eligible: bool
    reasons: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        return dataclasses.asdict(self)


class GoodhartGuard:
    """Fail-closed promotion guard for self-improvement candidates.

    The guard never grants effect authority. It only decides whether a candidate has
    enough anti-Goodhart structure to proceed to an independent review/promotion step.
    """

    @staticmethod
    def evaluate(
        candidate: Mapping[str, Any],
        evidence: Iterable[Mapping[str, Any]] = (),
    ) -> GuardDecision:
        reasons: list[str] = []

        for key in ("baseline", "test", "falsifier", "shadow"):
            value = candidate.get(key)
            if not isinstance(value, Mapping) or not value:
                reasons.append(f"missing_{key}")

        scope = candidate.get("promotion_scope")
        if not isinstance(scope, str) or not scope.strip():
            reasons.append("missing_promotion_scope")

        optimized = {
            str(x)
            for x in (candidate.get("optimized_metrics") or ())
            if isinstance(x, (str, int, float))
        }
        holdout = {
            str(x)
            for x in (candidate.get("holdout_metrics") or ())
            if isinstance(x, (str, int, float))
        }
        if not optimized:
            reasons.append("missing_optimized_metrics")
        if not holdout:
            reasons.append("missing_holdout_metrics")
        if optimized & holdout:
            reasons.append("holdout_metric_overlaps_optimized_metric")

        if candidate.get("negative_evidence_preserved") is not True:
            reasons.append("negative_evidence_not_attested")

        if candidate.get("self_authorized") is True or candidate.get("effect_authority") is True:
            reasons.append("candidate_attempted_self_authority")

        independent = False
        for item in evidence:
            if item.get("independent") is not True:
                continue
            result = str(item.get("result", "")).upper()
            if result not in {"", "UNKNOWN", "INFRA_FAILURE", "EVIDENCE_INVALID"}:
                independent = True
                break
        if not independent:
            reasons.append("missing_independent_valid_evidence")

        if reasons:
            return GuardDecision("CANDIDATE_ONLY", False, tuple(sorted(set(reasons))))
        return GuardDecision(
            "ELIGIBLE_FOR_INDEPENDENT_PROMOTION_REVIEW",
            True,
            (
                "anti_goodhart_structure_complete",
                "effect_authority_still_required_separately",
            ),
        )


class AssemblyManifest:
    CANONICAL_AUTHORITY_LABELS = {
        "truth_projection": "CANONICAL_TRUTH_PROJECTION",
        "cognition_selection": "CANONICAL_COGNITION_SELECTION",
        "effect_authority": "CANONICAL_EFFECT_AUTHORITY",
        "runtime_supervision": "CANONICAL_RUNTIME_SUPERVISION",
    }
    EXTERNAL_DONOR_PREFIXES = ("repo:project-frankenstein", "repo:research")
    PROBE_REQUIRED_POLICIES = {"PROBE_BEFORE_USE", "HOST_BOUND_PROBE_REQUIRED"}

    def __init__(self, raw: Mapping[str, Any]) -> None:
        self.raw = dict(raw)
        self.schema = str(raw.get("schema", ""))
        self.entity = str(raw.get("entity", ""))
        self.center = str(raw.get("center", ""))
        self.canonical_authorities = {
            str(k): str(v)
            for k, v in dict(raw.get("canonical_authorities") or {}).items()
        }

        organs: list[OrganSpec] = []
        for item in raw.get("organs", ()):
            providers = tuple(
                ProviderSpec(
                    source_id=str(p["source_id"]),
                    source_path=str(p["source_path"]),
                    entrypoint=str(p["entrypoint"]),
                    source_commit_policy=str(p["source_commit_policy"]),
                )
                for p in item.get("providers", ())
            )
            organs.append(
                OrganSpec(
                    organ_id=str(item["organ_id"]),
                    role=str(item["role"]),
                    authority=str(item["authority"]),
                    activation_policy=str(item["activation_policy"]),
                    providers=providers,
                    inputs=tuple(str(x) for x in item.get("inputs", ())),
                    outputs=tuple(str(x) for x in item.get("outputs", ())),
                    constraints=tuple(str(x) for x in item.get("constraints", ())),
                )
            )
        self.organs = tuple(organs)
        self.connections = tuple(
            (str(edge[0]), str(edge[1]))
            for edge in raw.get("connections", ())
            if isinstance(edge, (list, tuple)) and len(edge) == 2
        )

    @classmethod
    def from_path(cls, path: str | Path) -> "AssemblyManifest":
        return cls(json.loads(Path(path).read_text(encoding="utf-8")))

    @property
    def by_id(self) -> dict[str, OrganSpec]:
        return {organ.organ_id: organ for organ in self.organs}

    @property
    def manifest_digest(self) -> str:
        return digest(self.raw)

    def validate(self, source_ids: Iterable[str]) -> None:
        errors: list[str] = []
        known_sources = set(source_ids)

        if self.schema != "OMEGA_ASSEMBLY/v1":
            errors.append(f"unsupported_schema:{self.schema}")
        if self.entity != "OMEGA":
            errors.append("entity_must_be_OMEGA")
        if self.center != "repo:omega":
            errors.append("center_must_be_repo:omega")

        ids = [o.organ_id for o in self.organs]
        if len(ids) != len(set(ids)):
            errors.append("duplicate_organ_id")
        organ_map = self.by_id

        for role, expected_label in self.CANONICAL_AUTHORITY_LABELS.items():
            organ_id = self.canonical_authorities.get(role)
            if not organ_id:
                errors.append(f"missing_canonical_authority:{role}")
                continue
            organ = organ_map.get(organ_id)
            if organ is None:
                errors.append(f"canonical_authority_unknown_organ:{role}:{organ_id}")
            elif organ.authority != expected_label:
                errors.append(
                    f"canonical_authority_label_mismatch:{role}:{organ_id}:{organ.authority}"
                )

        canonical_labels = set(self.CANONICAL_AUTHORITY_LABELS.values())
        seen_labels: dict[str, str] = {}
        for organ in self.organs:
            if organ.authority in canonical_labels:
                other = seen_labels.get(organ.authority)
                if other and other != organ.organ_id:
                    errors.append(
                        f"duplicate_canonical_authority:{organ.authority}:{other}:{organ.organ_id}"
                    )
                seen_labels[organ.authority] = organ.organ_id

            if not organ.providers:
                errors.append(f"organ_without_provider:{organ.organ_id}")

            for provider in organ.providers:
                if provider.source_id not in known_sources:
                    errors.append(
                        f"unknown_provider_source:{organ.organ_id}:{provider.source_id}"
                    )
                if (
                    provider.source_id.startswith(self.EXTERNAL_DONOR_PREFIXES)
                    and organ.authority in canonical_labels
                ):
                    errors.append(
                        "external_donor_cannot_be_canonical_authority:"
                        f"{organ.organ_id}:{provider.source_id}"
                    )

        for source, target in self.connections:
            if source not in organ_map:
                errors.append(f"connection_unknown_source:{source}")
            if target not in organ_map:
                errors.append(f"connection_unknown_target:{target}")

        relay_inbound = {
            source for source, target in self.connections if target == "omega.relay"
        }
        if relay_inbound - {"omega.alignment"}:
            errors.append(
                "relay_must_only_receive_from_alignment:"
                + ",".join(sorted(relay_inbound - {"omega.alignment"}))
            )

        if ("omega.grid", "omega.alignment") not in self.connections:
            errors.append("grid_must_feed_alignment")
        if ("omega.alignment", "omega.relay") not in self.connections:
            errors.append("alignment_must_feed_relay")
        if ("omega.relay", "omega.unifieddb") not in self.connections:
            errors.append("relay_must_feed_unifieddb")

        if errors:
            raise AssemblyError(";".join(sorted(set(errors))))

    def build_status(
        self,
        *,
        source_registry: Mapping[str, Mapping[str, Any]],
        probes: Iterable[Mapping[str, Any]] = (),
    ) -> dict[str, Any]:
        _ = source_registry
        probe_map: dict[tuple[str, str], Mapping[str, Any]] = {}
        for probe in probes:
            organ_id = str(probe.get("organ_id", ""))
            source_id = str(probe.get("source_id", ""))
            if organ_id and source_id:
                probe_map[(organ_id, source_id)] = probe

        organs: list[dict[str, Any]] = []
        static_core_bound = True
        all_probe_required_verified = True

        for organ in self.organs:
            provider_rows: list[dict[str, Any]] = []
            states_by_source: dict[str, str] = {}

            for provider in organ.providers:
                probe = probe_map.get((organ.organ_id, provider.source_id))
                if probe and probe.get("verified") is True:
                    state = "VERIFIED"
                elif (
                    organ.activation_policy == "STATIC_SOURCE_BOUND"
                    and provider.source_id == "repo:omega"
                ):
                    state = "SOURCE_BOUND"
                elif organ.activation_policy == "REMOTE_EVIDENCE_ONLY":
                    state = "EVIDENCE_ROUTE_BOUND"
                else:
                    state = "DECLARED_UNVERIFIED"

                states_by_source[provider.source_id] = state
                row: dict[str, Any] = {
                    "source_id": provider.source_id,
                    "source_path": provider.source_path,
                    "entrypoint": provider.entrypoint,
                    "source_commit_policy": provider.source_commit_policy,
                    "state": state,
                }
                if probe:
                    row["probe"] = dict(probe)
                provider_rows.append(row)

            if organ.activation_policy == "STATIC_SOURCE_BOUND":
                if states_by_source.get("repo:omega") not in {"SOURCE_BOUND", "VERIFIED"}:
                    static_core_bound = False

            if organ.activation_policy in self.PROBE_REQUIRED_POLICIES:
                if "VERIFIED" not in states_by_source.values():
                    all_probe_required_verified = False

            organs.append(
                {
                    "organ_id": organ.organ_id,
                    "role": organ.role,
                    "authority": organ.authority,
                    "activation_policy": organ.activation_policy,
                    "providers": provider_rows,
                }
            )

        stable = {
            "schema": "OMEGA_ASSEMBLY_STATUS/v1",
            "entity": self.entity,
            "manifest_digest": self.manifest_digest,
            "static_core_bound": static_core_bound,
            "all_probe_required_organs_verified": all_probe_required_verified,
            "organs": organs,
            "connections": [list(x) for x in self.connections],
        }
        return {
            **stable,
            "state_digest": digest(stable),
            "updated_at": now(),
        }


def load_source_registry(
    path: str | Path,
) -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]]]:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    sources = list(raw.get("sources", ()))
    by_id = {str(item["source_id"]): dict(item) for item in sources}
    return sources, by_id


def load_probes(path: str | Path) -> list[dict[str, Any]]:
    p = Path(path)
    if not p.exists():
        return []
    raw = json.loads(p.read_text(encoding="utf-8"))
    if raw.get("schema") != "OMEGA_ASSEMBLY_PROBES/v1":
        raise AssemblyError("unsupported_probe_schema")
    return [dict(item) for item in raw.get("probes", ())]


class AssemblyMonitor:
    """Read-only composition monitor.

    It proves which logical organs are merely declared, source-bound,
    evidence-route-bound or actually runtime-verified. It performs no host effect
    and activates no donor code.
    """

    def __init__(
        self,
        *,
        repo_root: Path,
        runtime_root: Path,
        db_path: Path,
        interval: float = 15.0,
    ) -> None:
        self.repo_root = repo_root
        self.runtime_root = runtime_root
        self.db_path = db_path
        self.interval = max(1.0, float(interval))
        self.manifest_path = repo_root / "config" / "assembly.json"
        self.sources_path = repo_root / "config" / "sources.json"
        self.probe_path = runtime_root / "assembly" / "PROBES.json"
        self.status_path = runtime_root / "ASSEMBLY_STATUS.json"
        self.runtime_root.mkdir(parents=True, exist_ok=True)
        self.probe_path.parent.mkdir(parents=True, exist_ok=True)
        self.store = UnifiedStore(db_path, repo_root / "schema")
        self._last_state_digest: str | None = None

    def tick(self) -> dict[str, Any]:
        manifest = AssemblyManifest.from_path(self.manifest_path)
        sources, source_map = load_source_registry(self.sources_path)
        manifest.validate(source_map)
        self.store.register_sources(sources)
        probes = load_probes(self.probe_path)
        status = manifest.build_status(
            source_registry=source_map,
            probes=probes,
        )

        tmp = self.status_path.with_suffix(".tmp")
        tmp.write_text(
            json.dumps(status, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        os.replace(tmp, self.status_path)

        if status["state_digest"] != self._last_state_digest:
            self.store.record_observation(
                source_id="runtime:omega-vps",
                subject_id="omega:assembly",
                owner_id="omega",
                machine_id="omega-vps",
                payload=status,
                observed_at=status["updated_at"],
                evidence_class="RUNTIME_RECEIPT",
                raw_locator=str(self.status_path),
                authority_rank=80,
                confidence=1.0,
            )
            self._last_state_digest = str(status["state_digest"])
        return status

    def run(self) -> int:
        while True:
            self.tick()
            time.sleep(self.interval)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--repo-root",
        default=os.getenv("OMEGA_REPO_ROOT", "/workspace/omega_runtime/current"),
    )
    ap.add_argument(
        "--runtime-root",
        default=os.getenv("OMEGA_RUNTIME_ROOT", "/workspace/omega_runtime/state"),
    )
    ap.add_argument(
        "--db",
        default=os.getenv("OMEGA_UNIFIED_DB", "/workspace/omega_runtime/data/omega_unified.db"),
    )
    ap.add_argument(
        "--interval",
        type=float,
        default=float(os.getenv("OMEGA_ASSEMBLY_INTERVAL", "15")),
    )
    ap.add_argument("--once", action="store_true")
    args = ap.parse_args()

    monitor = AssemblyMonitor(
        repo_root=Path(args.repo_root),
        runtime_root=Path(args.runtime_root),
        db_path=Path(args.db),
        interval=args.interval,
    )
    if args.once:
        print(json.dumps(monitor.tick(), indent=2, ensure_ascii=False))
        return 0
    try:
        return monitor.run()
    except KeyboardInterrupt:
        return 0


__all__ = [
    "AssemblyError",
    "AssemblyManifest",
    "AssemblyMonitor",
    "GoodhartGuard",
    "GuardDecision",
    "OrganSpec",
    "ProviderSpec",
    "load_probes",
    "load_source_registry",
]


if __name__ == "__main__":
    raise SystemExit(main())
