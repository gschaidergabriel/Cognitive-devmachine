#!/usr/bin/env python3
"""Build a deterministic, derived ClayGraph materialization from the RAE repository.

Canonical ledgers/raw sources remain authoritative. This graph is a rebuildable semantic
projection used for retrieval/activation experiments and database-transcendence research.
It deliberately excludes private credentials and its own generated runtime output.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import time
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
ARCH = ROOT / "research_entity" / "claygraph" / "CLAYGRAPH_LATEST.claycode.json"
DEFAULT_OUT = ROOT / "research_entity" / "claygraph" / "runtime" / "current"
TEXT_EXTS = {".md", ".txt", ".json", ".jsonl", ".csv", ".tsv", ".py", ".yaml", ".yml", ".toml", ".sql", ".ebnf"}
EXCLUDE_PREFIXES = (
    "research_entity/private/",
    "research_entity/runtime/tool_results/",
    "research_entity/runtime/tool_requests/",
    "research_entity/claygraph/runtime/",
    ".git/",
)
BRANCHES = ["clay", "frank", "gwt", "emergenz", "claycode", "hyperposition", "claygraph"]
ID_KEYS = ["claim_id", "hypothesis_id", "experiment_id", "event_id", "packet_id", "run_id", "negative_result_id", "id"]
LABEL_KEYS = ["proposition", "title", "name", "summary", "statement", "hypothesis", "description", "reasoning_summary"]
REF_RE = re.compile(r"\b[A-Z][A-Z0-9]{0,8}(?:-[A-Z0-9][A-Z0-9._]{1,36}){1,6}\b")

REL_FIELDS = {
    "parent_event_ids": "PARENT_OF",
    "parents": "PARENT_OF",
    "depends_on": "DEPENDS_ON",
    "dependencies": "DEPENDS_ON",
    "upstream_dependencies": "DEPENDS_ON",
    "source_refs": "DERIVED_FROM",
    "evidence_refs": "EVIDENCE_FOR",
    "experiment_ref": "EVIDENCE_FOR",
    "topic_packets": "IN_TOPIC",
    "topic_packet_ids": "IN_TOPIC",
    "contradicts": "CONTRADICTS",
    "contradictions": "CONTRADICTS",
    "supersedes": "SUPERSEDES",
    "supports": "SUPPORTS",
    "challenges": "CHALLENGES",
    "affected_branches": "AFFECTS_BRANCH",
    "feedback_targets": "AFFECTS_BRANCH",
}


def sha_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()


def node_id(kind: str, identity: str) -> str:
    return f"{kind}:{sha_text(kind + '|' + identity)[:24]}"


def relpath(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def excluded(path: Path) -> bool:
    r = relpath(path)
    return any(r.startswith(x) for x in EXCLUDE_PREFIXES)


def branch_from_path(path: str) -> str | None:
    parts = path.split("/")
    if "trigger_runs" in parts:
        i = parts.index("trigger_runs")
        if i + 1 < len(parts) and parts[i + 1] in BRANCHES:
            return parts[i + 1]
    low = path.lower()
    for b in BRANCHES:
        if f"/{b}/" in low or f"_{b}_" in low or low.endswith(f"/{b}.md"):
            return b
    return None


def kind_for_object(obj: dict[str, Any], path: str) -> str:
    if "claim_id" in obj:
        return "claim"
    if "hypothesis_id" in obj:
        return "hypothesis"
    if "experiment_id" in obj:
        return "experiment"
    if "negative_result_id" in obj:
        return "negative_result"
    if "event_id" in obj:
        return "event"
    if "packet_id" in obj:
        return "topic_packet"
    if "run_id" in obj:
        return "run"
    low = path.lower()
    if "hypoth" in low:
        return "hypothesis"
    if "experiment" in low:
        return "experiment"
    if "negative" in low:
        return "negative_result"
    if "architecture" in low or "claycode" in low:
        return "architecture"
    return "reference"


def external_identity(obj: dict[str, Any]) -> str | None:
    for key in ID_KEYS:
        value = obj.get(key)
        if isinstance(value, (str, int)) and str(value).strip():
            return str(value).strip()
    return None


def label_for(obj: dict[str, Any], fallback: str) -> str:
    for key in LABEL_KEYS:
        value = obj.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()[:700]
    return fallback


def bounded_text(value: Any, limit: int = 3500) -> str:
    try:
        text = json.dumps(value, ensure_ascii=False, sort_keys=True)
    except Exception:
        text = str(value)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:limit]


def iter_values(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, (str, int, float)):
        return [str(value)]
    if isinstance(value, list):
        out: list[str] = []
        for x in value:
            if isinstance(x, dict):
                for k in ID_KEYS + ["ref", "path", "branch", "target", "source"]:
                    if x.get(k):
                        out.append(str(x[k]))
                        break
            elif x is not None:
                out.append(str(x))
        return out
    if isinstance(value, dict):
        return [str(k) for k in value.keys()]
    return []


class Graph:
    def __init__(self) -> None:
        self.nodes: dict[str, dict[str, Any]] = {}
        self.edges: dict[tuple[str, str, str], dict[str, Any]] = {}
        self.external: dict[str, str] = {}
        self.pending: list[tuple[str, str, str, str]] = []
        self.artifact_text: dict[str, str] = {}

    def add_node(self, kind: str, identity: str, **attrs: Any) -> str:
        nid = node_id(kind, identity)
        base = {"id": nid, "type": kind, "identity": identity}
        base.update({k: v for k, v in attrs.items() if v not in (None, "", [], {})})
        if nid in self.nodes:
            existing = self.nodes[nid]
            for k, v in base.items():
                if k not in existing or existing[k] in (None, "", [], {}):
                    existing[k] = v
        else:
            self.nodes[nid] = base
        self.external.setdefault(identity, nid)
        self.external.setdefault(identity.lower(), nid)
        return nid

    def add_edge(self, source: str, target: str, etype: str, weight: float = 1.0, provenance: str | None = None) -> None:
        if source == target:
            return
        key = (source, target, etype)
        record = {"source": source, "target": target, "type": etype, "weight": round(float(weight), 4)}
        if provenance:
            record["provenance"] = provenance
        old = self.edges.get(key)
        if old is None or record["weight"] > old.get("weight", 0):
            self.edges[key] = record

    def resolve_ref(self, value: str) -> str:
        value = value.strip()
        if value in BRANCHES:
            return self.external[value]
        target = self.external.get(value) or self.external.get(value.lower())
        if target:
            return target
        return self.add_node("reference", value, label=value)


def read_text(path: Path, limit: int = 100_000) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")[:limit]
    except OSError:
        return ""


def iter_repo_files() -> list[Path]:
    roots = [ROOT / "research_entity", ROOT / "research_sources", ROOT / "tools"]
    files: list[Path] = []
    for base in roots:
        if not base.exists():
            continue
        for p in base.rglob("*"):
            if p.is_file() and p.suffix.lower() in TEXT_EXTS and not excluded(p):
                files.append(p)
    for p in ROOT.iterdir():
        if p.is_file() and p.suffix.lower() in {".md", ".txt", ".json"}:
            files.append(p)
    return sorted(set(files), key=lambda p: relpath(p))


def add_object(g: Graph, obj: dict[str, Any], path: str, ordinal: int | None = None) -> str | None:
    ext = external_identity(obj)
    if not ext:
        return None
    kind = kind_for_object(obj, path)
    branch = obj.get("trigger") if obj.get("trigger") in BRANCHES else branch_from_path(path)
    nid = g.add_node(
        kind,
        ext,
        label=label_for(obj, ext),
        text=bounded_text(obj),
        path=path,
        branch=branch,
        status=obj.get("status") or obj.get("current_status") or obj.get("first_status"),
        evidence_class=obj.get("evidence_class") or obj.get("scope"),
        ordinal=ordinal,
    )
    if branch:
        g.add_edge(nid, g.external[branch], "BELONGS_TO_BRANCH", 0.95, path)
    for field, etype in REL_FIELDS.items():
        for ref in iter_values(obj.get(field)):
            g.pending.append((nid, etype, ref, path))
    return nid


def ingest_file(g: Graph, path: Path, corpus_hash: "hashlib._Hash") -> None:
    r = relpath(path)
    raw = path.read_bytes()
    fsha = hashlib.sha256(raw).hexdigest()
    corpus_hash.update(r.encode() + b"\0" + fsha.encode() + b"\n")
    text = raw.decode("utf-8", errors="replace")
    branch = branch_from_path(r)
    kind = "source" if r.startswith("research_sources/") else "artifact"
    if "architecture" in r.lower() or r.endswith(".claycode.json"):
        kind = "architecture"
    aid = g.add_node(kind, r, label=path.name, text=re.sub(r"\s+", " ", text).strip()[:5000], path=r, branch=branch, sha256=fsha, bytes=len(raw))
    g.artifact_text[aid] = text[:100_000]
    if branch:
        g.add_edge(aid, g.external[branch], "BELONGS_TO_BRANCH", 0.9, r)

    parts = r.split("/")
    if "trigger_runs" in parts:
        i = parts.index("trigger_runs")
        if i + 2 < len(parts):
            b, rid = parts[i + 1], parts[i + 2]
            if b in BRANCHES:
                run_nid = g.add_node("run", rid, label=rid, branch=b, path="/".join(parts[: i + 3]))
                g.add_edge(run_nid, g.external[b], "BELONGS_TO_BRANCH", 1.0, r)
                g.add_edge(run_nid, aid, "HAS_ARTIFACT", 1.0, r)

    if path.suffix.lower() == ".jsonl":
        for idx, line in enumerate(text.splitlines(), 1):
            if not line.strip():
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(obj, dict):
                oid = add_object(g, obj, r, idx)
                if oid:
                    g.add_edge(aid, oid, "DERIVED_FROM", 0.75, r)
    elif path.suffix.lower() == ".json":
        try:
            obj = json.loads(text)
        except json.JSONDecodeError:
            obj = None
        if isinstance(obj, dict):
            oid = add_object(g, obj, r)
            if oid and oid != aid:
                g.add_edge(aid, oid, "DERIVED_FROM", 0.75, r)


def finalize_relations(g: Graph) -> None:
    for source, etype, ref, provenance in g.pending:
        target = g.resolve_ref(ref)
        if etype == "PARENT_OF":
            g.add_edge(target, source, etype, 1.0, provenance)
        elif etype == "EVIDENCE_FOR":
            g.add_edge(target, source, etype, 1.0, provenance)
        else:
            g.add_edge(source, target, etype, 1.0, provenance)

    # Explicit identifier mentions provide low-weight associative edges. They are cues,
    # not support/evidence assertions.
    for aid, text in g.artifact_text.items():
        seen: set[str] = set()
        for match in REF_RE.findall(text):
            target = g.external.get(match) or g.external.get(match.lower())
            if target and target != aid and target not in seen:
                seen.add(target)
                g.add_edge(aid, target, "MENTIONS", 0.42, g.nodes[aid].get("path"))


def build(output_dir: Path) -> dict[str, Any]:
    start = time.perf_counter()
    arch = json.loads(ARCH.read_text(encoding="utf-8"))
    g = Graph()
    for b in BRANCHES:
        g.add_node("branch", b, label=b)

    corpus = hashlib.sha256()
    files = iter_repo_files()
    for p in files:
        ingest_file(g, p, corpus)
    finalize_relations(g)

    output_dir.mkdir(parents=True, exist_ok=True)
    nodes_path = output_dir / "nodes.jsonl"
    edges_path = output_dir / "edges.jsonl"
    nodes = [g.nodes[k] for k in sorted(g.nodes)]
    edges = [g.edges[k] for k in sorted(g.edges)]
    nodes_path.write_text("".join(json.dumps(x, ensure_ascii=False, sort_keys=True) + "\n" for x in nodes), encoding="utf-8")
    edges_path.write_text("".join(json.dumps(x, ensure_ascii=False, sort_keys=True) + "\n" for x in edges), encoding="utf-8")

    type_counts = Counter(x["type"] for x in nodes)
    edge_counts = Counter(x["type"] for x in edges)
    branch_counts = Counter(x.get("branch") for x in nodes if x.get("branch"))
    manifest = {
        "schema_version": "1.0",
        "status": "DERIVED_REBUILDABLE",
        "architecture_graph_id": arch.get("graph_id"),
        "architecture_generation": arch.get("generation"),
        "architecture_sha256": hashlib.sha256(ARCH.read_bytes()).hexdigest(),
        "source_corpus_sha256": corpus.hexdigest(),
        "files_indexed": len(files),
        "nodes": len(nodes),
        "edges": len(edges),
        "node_types": dict(sorted(type_counts.items())),
        "edge_types": dict(sorted(edge_counts.items())),
        "branch_nodes": dict(sorted(branch_counts.items())),
        "nodes_file": "nodes.jsonl",
        "edges_file": "edges.jsonl",
        "canonicality": "derived projection; canonical ledgers/raw evidence outrank this materialization",
        "activation_is_not_truth": True,
        "build_elapsed_ms": round((time.perf_counter() - start) * 1000, 3),
    }
    (output_dir / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return manifest


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output-dir", default=str(DEFAULT_OUT))
    args = ap.parse_args()
    manifest = build(Path(args.output_dir))
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
