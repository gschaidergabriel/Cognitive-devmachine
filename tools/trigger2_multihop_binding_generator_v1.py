#!/usr/bin/env python3
"""Trigger-2 multi-hop binding/distractor curriculum extension.

METHOD_ONLY source generator. It extends the canonical direct S3 codebook seed
with episode-local reference chains. It does not admit dataset rows or mint
model/J-Space/HCU/EntityOS/training credit. Abstract output slots must be
resolved to admitted one-token ABI atoms before any train-ready promotion.
"""
from __future__ import annotations

import hashlib
import itertools
import math
import random
import re
from collections import Counter, defaultdict
from typing import Any, Iterable

ROW_SCHEMA = "ENTITYOS_HCU_TRAININGTRACE_CANDIDATE/v1"
AUDIT_SCHEMA = "TRIGGER2_MULTIHOP_BINDING_GENERATOR_AUDIT/v1"
GENERATOR_SCHEMA = "CLAY_TRIGGER2_MULTIHOP_BINDING_GENERATOR/v1"
CLASSES = ("ALLOW", "DENY", "ABSTAIN")
OUTPUT_SLOTS = ("ATOM_A", "ATOM_B", "ATOM_C")
ROOT_ROLES = ("r0", "r1", "r2")
ROOT_S3 = tuple(itertools.permutations(ROOT_ROLES))
SYMBOL_S3 = tuple(itertools.permutations(OUTPUT_SLOTS))
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


def _chain(root: str, slot: str, depth: int, tag: str, ci: int) -> list[tuple[str, str]]:
    cur, out = root, []
    for hop in range(depth - 1):
        nxt = f"m_{tag}_{ci}_{hop}"
        out.append((cur, nxt))
        cur = nxt
    out.append((cur, slot))
    return out


def _distractors(tag: str, depth: int, count: int) -> tuple[list[tuple[str, str]], list[str]]:
    out, roots = [], []
    for d in range(count):
        cur = f"d_{tag}_{d}_0"
        roots.append(cur)
        ddepth = 1 + ((depth + d) % 4)
        for hop in range(ddepth - 1):
            nxt = f"d_{tag}_{d}_{hop + 1}"
            out.append((cur, nxt))
            cur = nxt
        out.append((cur, OUTPUT_SLOTS[(depth + d) % 3]))
    return out, roots


def _shuffle(edges: list[tuple[str, str]], tag: str) -> list[tuple[str, str]]:
    rng = random.Random(int(hashlib.sha256(tag.encode()).hexdigest()[:16], 16))
    out = list(edges)
    rng.shuffle(out)
    return out


def build_rows(*, split: str = "TRAIN", distractor_chains: int = 2) -> list[dict[str, Any]]:
    if distractor_chains < 1:
        raise ValueError("distractor_chains must be >=1")
    rows, orders, row_i = [], tuple(itertools.permutations(CLASSES)), 0
    for depth in DEPTHS:
        for rp_i, root_perm in enumerate(ROOT_S3):
            c2r = dict(zip(CLASSES, root_perm))
            for sp_i, symbol_perm in enumerate(SYMBOL_S3):
                c2s = dict(zip(CLASSES, symbol_perm))
                for t_i, template in enumerate(TEMPLATES):
                    for c_i, cls in enumerate(CLASSES):
                        tag = f"D{depth}R{rp_i}S{sp_i}T{t_i}C{c_i}"
                        edges = []
                        for ci, c in enumerate(CLASSES):
                            edges.extend(_chain(c2r[c], c2s[c], depth, tag, ci))
                        d_edges, d_roots = _distractors(tag, depth, distractor_chains)
                        edges = _shuffle(edges + d_edges, tag)
                        order = orders[(row_i + depth + rp_i + sp_i) % len(orders)]
                        prompt = _prompt(template, _codebook(c2r, order), _bindings(edges), SCENARIOS[cls])
                        target, path = resolve(c2r[cls], edges)
                        rows.append({
                            "schema": ROW_SCHEMA,
                            "evidence_class": "METHOD_ONLY",
                            "reality_level": "R2",
                            "family_id": f"MULTIHOP_{template}_D{depth}_{cls}",
                            "provenance_ancestry_id": f"trigger2-multihop-v1:{split}:{template}:D{depth}:{cls}",
                            "canonical_truth_allowed": False,
                            "direct_effect_authority": False,
                            "fact_status": "NOT_APPLICABLE",
                            "target_type": "DYNAMIC_CODEBOOK_MULTI_HOP_BINDING",
                            "split": split,
                            "split_unit": "CAUSAL_FAMILY_AND_PROVENANCE_ANCESTRY",
                            "selected_using_holdout": False,
                            "prompt": prompt,
                            "target": target,
                            "curriculum": {
                                "generator_schema": GENERATOR_SCHEMA,
                                "referential_depth": depth,
                                "semantic_class_metadata_only": cls,
                                "template_id": template,
                                "root_permutation": list(root_perm),
                                "symbol_permutation": list(symbol_perm),
                                "class_to_root": c2r,
                                "class_to_symbol": c2s,
                                "binding_edges": [list(x) for x in edges],
                                "relevant_path": path,
                                "distractor_roots": d_roots,
                                "distractor_chain_count": distractor_chains,
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
                        row_i += 1
    return rows


def _class_word_leak(prompt: str) -> bool:
    outside = re.sub(r"<CODEBOOK>.*?</CODEBOOK>", "", prompt, flags=re.S).upper()
    return any(re.search(rf"\b{c}\b", outside) for c in CLASSES)


def _mi(rows: list[dict[str, Any]]) -> float:
    pair = Counter((r["curriculum"]["semantic_class_metadata_only"], r["target"]) for r in rows)
    cx = Counter(r["curriculum"]["semantic_class_metadata_only"] for r in rows)
    cy = Counter(r["target"] for r in rows)
    n, out = len(rows), 0.0
    for (x, y), count in pair.items():
        pxy, px, py = count/n, cx[x]/n, cy[y]/n
        out += pxy * math.log2(pxy/(px*py))
    return out


def validate_rows(rows: Iterable[dict[str, Any]]) -> dict[str, Any]:
    rows, failures = list(rows), []
    depths, templates, positions = Counter(), Counter(), Counter()
    class_symbol = defaultdict(Counter)
    root_cov, symbol_cov = defaultdict(set), defaultdict(set)
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
            cb, edges = parse_codebook(prompt), parse_bindings(prompt)
            declared_edges = [tuple(x) for x in meta["binding_edges"]]
            if edges != declared_edges or cb != meta["class_to_root"]:
                failures.append(f"ROW_{i}:TEXT_METADATA_MISMATCH")
            if _class_word_leak(prompt):
                failures.append(f"ROW_{i}:CLASS_WORD_LEAK")
            cls, depth = meta["semantic_class_metadata_only"], int(meta["referential_depth"])
            target, path = resolve(cb[cls], edges)
            if target != row["target"] or len(path)-1 != depth or path != meta["relevant_path"]:
                failures.append(f"ROW_{i}:TARGET_OR_DEPTH_NOT_DERIVED")
            rp, sp = tuple(meta["root_permutation"]), tuple(meta["symbol_permutation"])
            if rp not in ROOT_S3 or dict(zip(CLASSES, rp)) != meta["class_to_root"]:
                failures.append(f"ROW_{i}:ROOT_PERMUTATION_NOT_CAUSAL")
            if sp not in SYMBOL_S3 or dict(zip(CLASSES, sp)) != meta["class_to_symbol"] or meta["class_to_symbol"][cls] != row["target"]:
                failures.append(f"ROW_{i}:SYMBOL_PERMUTATION_NOT_CAUSAL")
            relevant_internal = {x for x in path if x not in OUTPUT_SLOTS}
            roots = set(cb.values())
            for droot in meta["distractor_roots"]:
                _, dpath = resolve(droot, edges)
                d_internal = {x for x in dpath if x not in OUTPUT_SLOTS}
                if relevant_internal & d_internal or roots & d_internal:
                    failures.append(f"ROW_{i}:DISTRACTOR_INTERSECTION")
            positions[edges.index((path[0], path[1]))] += 1
            depths[depth] += 1
            templates[meta["template_id"]] += 1
            class_symbol[(depth, cls)][row["target"]] += 1
            key = (depth, meta["template_id"], cls)
            root_cov[key].add(rp)
            symbol_cov[key].add(sp)
        except Exception as exc:
            failures.append(f"ROW_{i}:PARSE_OR_RESOLUTION:{type(exc).__name__}:{exc}")
    expected = len(DEPTHS)*len(ROOT_S3)*len(SYMBOL_S3)*len(TEMPLATES)*len(CLASSES)
    if len(rows) != expected:
        failures.append(f"ROW_COUNT:{len(rows)}!={expected}")
    if depths and len(set(depths.values())) != 1:
        failures.append("DEPTH_IMBALANCE")
    if templates and len(set(templates.values())) != 1:
        failures.append("TEMPLATE_IMBALANCE")
    for (depth, cls), counts in class_symbol.items():
        if len({counts[s] for s in OUTPUT_SLOTS}) != 1:
            failures.append(f"COUNTERBALANCE:D{depth}:{cls}")
    if any(len(v) != 6 for v in root_cov.values()):
        failures.append("ROOT_S3_COVERAGE")
    if any(len(v) != 6 for v in symbol_cov.values()):
        failures.append("SYMBOL_S3_COVERAGE")
    mi = _mi(rows) if rows else float("nan")
    if rows and abs(mi) > 1e-12:
        failures.append(f"CLASS_SYMBOL_MI:{mi}")
    if rows and len(positions) < 4:
        failures.append("EDGE_POSITION_DIVERSITY")
    return {
        "schema": AUDIT_SCHEMA,
        "pass": not failures,
        "rows_total": len(rows),
        "expected_rows": expected,
        "failures": failures,
        "depth_counts": dict(sorted(depths.items())),
        "class_symbol_mi_bits": mi,
        "relevant_first_edge_position_variants": len(positions),
        "canonical_dataset_write_performed": False,
        "accepted_dataset_tokens_minted": 0,
        "training_credit_minted": False,
        "evidence_boundary": "Synthetic METHOD_ONLY routing curriculum only; no model/runtime/J-Space/HCU/EntityOS/training credit.",
    }
