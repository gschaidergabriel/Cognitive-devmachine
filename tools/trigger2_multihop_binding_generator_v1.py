#!/usr/bin/env python3
"""Trigger-2 multi-hop binding/distractor curriculum extension.

METHOD_ONLY source generator. It extends the direct S3 binding curriculum with
episode-local reference chains. It does not admit dataset rows or mint
model/J-Space/HCU/EntityOS/training credit. Abstract output slots must be
resolved to admitted one-token ABI atoms before any train-ready promotion.

v1.1 removes a source-level shortcut from v1: model-visible node names no
longer encode semantic-class/root-permutation/symbol-permutation/template/depth
loop indices. For a fixed graph factorial cell the exact codebook and binding
graph are invariant across all three semantic-state counterfactuals.
"""
from __future__ import annotations

import hashlib
import itertools
import math
import random
import re
from collections import Counter, defaultdict
from typing import Any, Callable, Iterable

ROW_SCHEMA = "ENTITYOS_HCU_TRAININGTRACE_CANDIDATE/v1"
AUDIT_SCHEMA = "TRIGGER2_MULTIHOP_BINDING_GENERATOR_AUDIT/v1.1"
GENERATOR_SCHEMA = "CLAY_TRIGGER2_MULTIHOP_BINDING_GENERATOR/v1.1"
CLASSES = ("ALLOW", "DENY", "ABSTAIN")
OUTPUT_SLOTS = ("ATOM_A", "ATOM_B", "ATOM_C")
ROOT_ROLES = ("r0", "r1", "r2")
ROOT_S3 = tuple(itertools.permutations(ROOT_ROLES))
SYMBOL_S3 = tuple(itertools.permutations(OUTPUT_SLOTS))
CODEBOOK_ORDERS = tuple(itertools.permutations(CLASSES))
DEPTHS = (1, 2, 3, 4)
TEMPLATES = (
    "T1_CODEBOOK_THEN_CASE",
    "T2_CASE_THEN_CODEBOOK",
    "T3_TABLE_STYLE_CODEBOOK",
    "T4_DIALOGUE_STYLE_EPISODE",
)
SCENARIOS = {
    "ALLOW": "Facts: p=true; q=true. Rule condition: p AND q.",
    "DENY": "Facts: p=true; q=false. Rule condition: p AND q.",
    "ABSTAIN": "Facts: p=true; q=UNKNOWN. Rule condition: p AND q.",
}
CLASS_WORD_POLICY = "CODEBOOK_ONLY_ALLOWED_CANDIDATE"
ABI_MANIFEST_SHA256 = "0f664e6a4626351fbf97cd74a4825cedaf115b80f56b71b16c39315dba02fa11"
SOURCE_PACKAGE_SHA256 = "a2babae93dfe39e4e452a06bd8b848337f29766e38c422f05fb395126229b05c"
MEASUREMENT_DONOR_MODEL = "Goekdeniz-Guelmez/Josiefied-Qwen3.5-0.8B-gabliterated-v1"
MEASUREMENT_DONOR_SNAPSHOT = "591852bda6e1979f59e4b0f5ee2919697b12e936"
OLD_FACTOR_TAG_RE = re.compile(r"D\d+R\d+S\d+T\d+C\d+")


def _codebook(mapping: dict[str, str], order: tuple[str, ...]) -> str:
    return "<CODEBOOK>" + ";".join(f"{c}=>{mapping[c]}" for c in order) + "</CODEBOOK>"


def _bindings(edges: list[tuple[str, str]]) -> str:
    return "<BINDINGS>" + ";".join(f"{a}=>{b}" for a, b in edges) + "</BINDINGS>"


def _prompt(template: str, cb: str, graph: str, scenario: str) -> str:
    if template == "T1_CODEBOOK_THEN_CASE":
        return f"{cb}\n{graph}\n<SITUATION>{scenario}</SITUATION>\n<QUERY>Resolve the episode-local bindings and emit only the final symbol.</QUERY>"
    if template == "T2_CASE_THEN_CODEBOOK":
        return f"<EPISODE><OBSERVATION>{scenario}</OBSERVATION>{cb}{graph}<INSTRUCTION>Use only this episode's mapping graph. Emit one final symbol.</INSTRUCTION></EPISODE>"
    if template == "T3_TABLE_STYLE_CODEBOOK":
        return f"{cb}{graph}<STATE>{scenario}</STATE><RESOLVE>?</RESOLVE>"
    if template == "T4_DIALOGUE_STYLE_EPISODE":
        return f"<CASE>{scenario}</CASE><MAPPING>{cb}{graph}</MAPPING><OUTPUT_CONTRACT>Follow the relevant chain, ignore unrelated chains, emit one final symbol.</OUTPUT_CONTRACT>"
    raise ValueError(template)


def _extract_block(prompt: str, name: str) -> str:
    m = re.search(rf"<{name}>.*?</{name}>", prompt, re.S)
    if not m:
        raise ValueError(f"missing {name.lower()}")
    return m.group(0)


def parse_codebook(prompt: str) -> dict[str, str]:
    m = re.search(r"<CODEBOOK>(.*?)</CODEBOOK>", prompt, re.S)
    if not m:
        raise ValueError("missing codebook")
    out = {}
    for item in m.group(1).split(";"):
        lhs, rhs = item.split("=>", 1)
        if lhs not in CLASSES or rhs not in ROOT_ROLES or lhs in out:
            raise ValueError("invalid codebook")
        out[lhs] = rhs
    if set(out) != set(CLASSES):
        raise ValueError("incomplete codebook")
    return out


def parse_bindings(prompt: str) -> list[tuple[str, str]]:
    m = re.search(r"<BINDINGS>(.*?)</BINDINGS>", prompt, re.S)
    if not m:
        raise ValueError("missing bindings")
    out, seen = [], set()
    for item in m.group(1).split(";"):
        lhs, rhs = item.split("=>", 1)
        if not lhs or not rhs or lhs in seen:
            raise ValueError("invalid binding")
        seen.add(lhs)
        out.append((lhs, rhs))
    return out


def resolve(root: str, edges: Iterable[tuple[str, str]]) -> tuple[str, list[str]]:
    graph, cur, path, seen = dict(edges), root, [root], {root}
    for _ in range(16):
        if cur in OUTPUT_SLOTS:
            return cur, path
        if cur not in graph:
            raise ValueError(f"unresolved:{cur}")
        cur = graph[cur]
        if cur in seen:
            raise ValueError("cycle")
        seen.add(cur)
        path.append(cur)
    raise ValueError("too_deep")


def _chain(root: str, slot: str, depth: int) -> list[tuple[str, str]]:
    """Neutral root-role chain; identifiers carry no factorial-cell metadata."""
    root_i = ROOT_ROLES.index(root)
    cur, out = root, []
    for hop in range(depth - 1):
        nxt = f"u{root_i}_{hop}"
        out.append((cur, nxt))
        cur = nxt
    out.append((cur, slot))
    return out


def _distractors(depth: int, count: int) -> tuple[list[tuple[str, str]], list[str]]:
    """Neutral distractor aliases; schedule is target/class independent."""
    out, roots = [], []
    for d in range(count):
        cur = f"z{d}_0"
        roots.append(cur)
        ddepth = 1 + ((depth + d) % 4)
        for hop in range(ddepth - 1):
            nxt = f"z{d}_{hop + 1}"
            out.append((cur, nxt))
            cur = nxt
        out.append((cur, OUTPUT_SLOTS[(depth + d) % len(OUTPUT_SLOTS)]))
    return out, roots


def _shuffle_graph(edges: list[tuple[str, str]], depth: int, template: str) -> list[tuple[str, str]]:
    """Order depends on task-relevant topology/template only, never class/target/S3 cell."""
    seed = f"trigger2-multihop-graph-order-v1|{depth}|{template}"
    rng = random.Random(int(hashlib.sha256(seed.encode()).hexdigest()[:16], 16))
    out = list(edges)
    rng.shuffle(out)
    return out


def _graph_for_cell(
    *,
    depth: int,
    template: str,
    class_to_root: dict[str, str],
    class_to_symbol: dict[str, str],
    distractor_chains: int,
) -> tuple[list[tuple[str, str]], list[str]]:
    """Build once per factorial cell, in neutral root-role order, then reuse for all classes."""
    root_to_class = {root: cls for cls, root in class_to_root.items()}
    edges: list[tuple[str, str]] = []
    for root in ROOT_ROLES:
        cls = root_to_class[root]
        edges.extend(_chain(root, class_to_symbol[cls], depth))
    d_edges, d_roots = _distractors(depth, distractor_chains)
    return _shuffle_graph(edges + d_edges, depth, template), d_roots


def build_rows(*, split: str = "TRAIN", distractor_chains: int = 2) -> list[dict[str, Any]]:
    if distractor_chains < 1:
        raise ValueError("distractor_chains must be >=1")
    rows: list[dict[str, Any]] = []
    for depth in DEPTHS:
        for rp_i, root_perm in enumerate(ROOT_S3):
            class_to_root = dict(zip(CLASSES, root_perm))
            for sp_i, symbol_perm in enumerate(SYMBOL_S3):
                class_to_symbol = dict(zip(CLASSES, symbol_perm))
                for t_i, template in enumerate(TEMPLATES):
                    # Same codebook bytes for all semantic-state twins in this cell.
                    order = CODEBOOK_ORDERS[(depth + rp_i + sp_i + t_i) % len(CODEBOOK_ORDERS)]
                    codebook_text = _codebook(class_to_root, order)
                    edges, d_roots = _graph_for_cell(
                        depth=depth,
                        template=template,
                        class_to_root=class_to_root,
                        class_to_symbol=class_to_symbol,
                        distractor_chains=distractor_chains,
                    )
                    graph_text = _bindings(edges)
                    counterfactual_group = f"MULTIHOP_GRAPH_CF|D{depth}|RP{rp_i}|SP{sp_i}|T{t_i}"
                    for cls in CLASSES:
                        target, path = resolve(class_to_root[cls], edges)
                        rows.append({
                            "schema": ROW_SCHEMA,
                            "evidence_class": "METHOD_ONLY",
                            "reality_level": "R2",
                            "family_id": f"MULTIHOP_{template}_D{depth}_F02",
                            "provenance_ancestry_id": f"trigger2-multihop-v1.1:{template}:D{depth}",
                            "canonical_truth_allowed": False,
                            "direct_effect_authority": False,
                            "fact_status": "NOT_APPLICABLE",
                            "target_type": "DYNAMIC_CODEBOOK_MULTI_HOP_BINDING",
                            "split": split,
                            "split_unit": "CAUSAL_FAMILY_AND_PROVENANCE_ANCESTRY",
                            "selected_using_holdout": False,
                            "prompt": _prompt(template, codebook_text, graph_text, SCENARIOS[cls]),
                            "target": target,
                            "curriculum": {
                                "generator_schema": GENERATOR_SCHEMA,
                                "referential_depth": depth,
                                "semantic_class_metadata_only": cls,
                                "template_id": template,
                                "root_permutation": list(root_perm),
                                "symbol_permutation": list(symbol_perm),
                                "class_to_root": class_to_root,
                                "class_to_symbol": class_to_symbol,
                                "binding_edges": [list(x) for x in edges],
                                "relevant_path": path,
                                "distractor_roots": d_roots,
                                "distractor_chain_count": distractor_chains,
                                "counterfactual_graph_group_id": counterfactual_group,
                            },
                            "class_word_policy": CLASS_WORD_POLICY,
                            "requires_abi_atom_resolution": True,
                            "candidate_train_ready": False,
                            "abi_manifest_sha256": ABI_MANIFEST_SHA256,
                            "measurement_source_package_sha256": SOURCE_PACKAGE_SHA256,
                            "measurement_donor_model_id": MEASUREMENT_DONOR_MODEL,
                            "measurement_donor_snapshot": MEASUREMENT_DONOR_SNAPSHOT,
                            "jspace_label_transfer_allowed": False,
                        })
    return rows


def _class_word_leak(prompt: str) -> bool:
    outside = re.sub(r"<CODEBOOK>.*?</CODEBOOK>", "", prompt, flags=re.S).upper()
    return any(re.search(rf"\b{c}\b", outside) for c in CLASSES)


def _mi(rows: list[dict[str, Any]], fx: Callable[[dict[str, Any]], Any], fy: Callable[[dict[str, Any]], Any]) -> float:
    if not rows:
        return float("nan")
    n = len(rows)
    joint = Counter((fx(r), fy(r)) for r in rows)
    cx = Counter(fx(r) for r in rows)
    cy = Counter(fy(r) for r in rows)
    out = 0.0
    for (x, y), count in joint.items():
        pxy, px, py = count / n, cx[x] / n, cy[y] / n
        out += pxy * math.log2(pxy / (px * py))
    return out


def _first_relevant_edge_position(row: dict[str, Any]) -> int:
    edges = [tuple(x) for x in row["curriculum"]["binding_edges"]]
    path = row["curriculum"]["relevant_path"]
    return edges.index((path[0], path[1]))


def _codebook_order(row: dict[str, Any]) -> tuple[str, ...]:
    return tuple(parse_codebook(row["prompt"]).keys())


def validate_rows(rows: Iterable[dict[str, Any]]) -> dict[str, Any]:
    rows, failures = list(rows), []
    depths, templates, positions = Counter(), Counter(), Counter()
    class_symbol = defaultdict(Counter)
    root_cov, symbol_cov = defaultdict(set), defaultdict(set)
    counterfactual_groups: dict[str, list[dict[str, Any]]] = defaultdict(list)

    for i, row in enumerate(rows):
        try:
            if row.get("schema") != ROW_SCHEMA or row.get("evidence_class") != "METHOD_ONLY" or row.get("reality_level") != "R2":
                failures.append(f"ROW_{i}:EVIDENCE_OR_SCHEMA")
            if row.get("canonical_truth_allowed") is not False or row.get("direct_effect_authority") is not False:
                failures.append(f"ROW_{i}:AUTHORITY")
            if row.get("candidate_train_ready") is not False or row.get("requires_abi_atom_resolution") is not True:
                failures.append(f"ROW_{i}:ABI_GATE")
            if row.get("jspace_label_transfer_allowed") is not False:
                failures.append(f"ROW_{i}:JSPACE_GATE")
            meta, prompt = row["curriculum"], row["prompt"]
            if OLD_FACTOR_TAG_RE.search(prompt):
                failures.append(f"ROW_{i}:MODEL_VISIBLE_FACTOR_TAG")
            codebook, edges = parse_codebook(prompt), parse_bindings(prompt)
            declared_edges = [tuple(x) for x in meta["binding_edges"]]
            if edges != declared_edges or codebook != meta["class_to_root"]:
                failures.append(f"ROW_{i}:TEXT_METADATA_MISMATCH")
            if _class_word_leak(prompt):
                failures.append(f"ROW_{i}:CLASS_WORD_LEAK")
            cls, depth = meta["semantic_class_metadata_only"], int(meta["referential_depth"])
            target, path = resolve(codebook[cls], edges)
            if target != row["target"] or len(path) - 1 != depth or path != meta["relevant_path"]:
                failures.append(f"ROW_{i}:TARGET_OR_DEPTH_NOT_DERIVED")
            root_perm, symbol_perm = tuple(meta["root_permutation"]), tuple(meta["symbol_permutation"])
            if root_perm not in ROOT_S3 or dict(zip(CLASSES, root_perm)) != meta["class_to_root"]:
                failures.append(f"ROW_{i}:ROOT_PERMUTATION_NOT_CAUSAL")
            if symbol_perm not in SYMBOL_S3 or dict(zip(CLASSES, symbol_perm)) != meta["class_to_symbol"] or meta["class_to_symbol"][cls] != row["target"]:
                failures.append(f"ROW_{i}:SYMBOL_PERMUTATION_NOT_CAUSAL")
            relevant_internal = {x for x in path if x not in OUTPUT_SLOTS}
            roots = set(codebook.values())
            for droot in meta["distractor_roots"]:
                _, dpath = resolve(droot, edges)
                d_internal = {x for x in dpath if x not in OUTPUT_SLOTS}
                if relevant_internal & d_internal or roots & d_internal:
                    failures.append(f"ROW_{i}:DISTRACTOR_INTERSECTION")
            position = _first_relevant_edge_position(row)
            positions[position] += 1
            depths[depth] += 1
            templates[meta["template_id"]] += 1
            class_symbol[(depth, cls)][row["target"]] += 1
            coverage_key = (depth, meta["template_id"], cls)
            root_cov[coverage_key].add(root_perm)
            symbol_cov[coverage_key].add(symbol_perm)
            counterfactual_groups[meta["counterfactual_graph_group_id"]].append(row)
        except Exception as exc:
            failures.append(f"ROW_{i}:PARSE_OR_RESOLUTION:{type(exc).__name__}:{exc}")

    expected = len(DEPTHS) * len(ROOT_S3) * len(SYMBOL_S3) * len(TEMPLATES) * len(CLASSES)
    if len(rows) != expected:
        failures.append(f"ROW_COUNT:{len(rows)}!={expected}")
    if depths and len(set(depths.values())) != 1:
        failures.append("DEPTH_IMBALANCE")
    if templates and len(set(templates.values())) != 1:
        failures.append("TEMPLATE_IMBALANCE")
    for (depth, cls), counts in class_symbol.items():
        if len({counts[s] for s in OUTPUT_SLOTS}) != 1:
            failures.append(f"COUNTERBALANCE:D{depth}:{cls}")
    if any(len(v) != len(ROOT_S3) for v in root_cov.values()):
        failures.append("ROOT_S3_COVERAGE")
    if any(len(v) != len(SYMBOL_S3) for v in symbol_cov.values()):
        failures.append("SYMBOL_S3_COVERAGE")

    for gid, members in counterfactual_groups.items():
        if len(members) != len(CLASSES):
            failures.append(f"COUNTERFACTUAL_GROUP_SIZE:{gid}:{len(members)}")
            continue
        if len({_extract_block(r["prompt"], "CODEBOOK") for r in members}) != 1:
            failures.append(f"COUNTERFACTUAL_CODEBOOK_NOT_INVARIANT:{gid}")
        if len({_extract_block(r["prompt"], "BINDINGS") for r in members}) != 1:
            failures.append(f"COUNTERFACTUAL_GRAPH_NOT_INVARIANT:{gid}")

    class_target_mi = _mi(rows, lambda r: r["curriculum"]["semantic_class_metadata_only"], lambda r: r["target"])
    target_position_mi = _mi(rows, lambda r: r["target"], _first_relevant_edge_position)
    class_position_mi = _mi(rows, lambda r: r["curriculum"]["semantic_class_metadata_only"], _first_relevant_edge_position)
    target_order_mi = _mi(rows, lambda r: r["target"], _codebook_order)
    class_order_mi = _mi(rows, lambda r: r["curriculum"]["semantic_class_metadata_only"], _codebook_order)
    nuisance_metrics = {
        "class__target_symbol": class_target_mi,
        "target__first_relevant_edge_position": target_position_mi,
        "class__first_relevant_edge_position": class_position_mi,
        "target__codebook_order": target_order_mi,
        "class__codebook_order": class_order_mi,
    }
    for name, value in nuisance_metrics.items():
        if rows and abs(value) > 1e-12:
            failures.append(f"NUISANCE_MI_NONZERO:{name}:{value}")

    return {
        "schema": AUDIT_SCHEMA,
        "pass": not failures,
        "rows_total": len(rows),
        "expected_rows": expected,
        "failures": sorted(set(failures)),
        "depth_counts": dict(sorted(depths.items())),
        "counterfactual_graph_groups": len(counterfactual_groups),
        "relevant_first_edge_position_variants": len(positions),
        "model_visible_factor_tag_rows": sum(1 for r in rows if OLD_FACTOR_TAG_RE.search(r["prompt"])),
        "nuisance_mi_bits": nuisance_metrics,
        "canonical_dataset_write_performed": False,
        "accepted_dataset_tokens_minted": 0,
        "training_credit_minted": False,
        "evidence_boundary": "Synthetic METHOD_ONLY routing curriculum only; no model/runtime/J-Space/HCU/EntityOS/training credit.",
    }
