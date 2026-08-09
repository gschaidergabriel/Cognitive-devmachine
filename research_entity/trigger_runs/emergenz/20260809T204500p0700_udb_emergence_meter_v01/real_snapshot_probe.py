#!/usr/bin/env python3
"""Observational probe over copied FRANK SQLite data.

Creates derived baseline/shuffled/lag-broken episodes in the lab database.
The source databases are opened read-only and never changed.
"""

from __future__ import annotations

import argparse
import json
import random
import sqlite3
import statistics
import time
import uuid
from pathlib import Path

from emergence_meter import (
    CONTRACT_VERSION,
    conditional_mutual_information,
    entropy,
    mutual_information,
    open_lab,
    stable_hash,
)


def quantile_bins(values: list[float], bins: int = 4) -> list[int]:
    ordered = sorted(values)
    cuts = [ordered[min(len(ordered) - 1, int(len(ordered) * i / bins))] for i in range(1, bins)]
    return [sum(v > c for c in cuts) for v in values]


def load_aura(path: Path, limit: int) -> dict[str, list]:
    con = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    rows = con.execute(
        "SELECT id,ts,global_density,global_entropy,change_rate,coherence "
        "FROM snapshots ORDER BY id DESC LIMIT ?", (limit,)
    ).fetchall()[::-1]
    con.close()
    return {
        "id": [r[0] for r in rows], "ts": [r[1] for r in rows],
        "density": [float(r[2]) for r in rows], "entropy": [float(r[3]) for r in rows],
        "change": [float(r[4]) for r in rows], "coherence": [float(r[5]) for r in rows],
    }


def lag_readout(data: dict[str, list], source: str, target: str, lag: int) -> dict:
    s = quantile_bins(data[source])
    t = quantile_bins(data[target])
    xs = s[:-lag]
    ys = t[lag:]
    history = t[:-lag]
    return {
        "source": source, "target": target, "lag": lag, "samples": len(xs),
        "mi_bits": mutual_information(xs, ys),
        "conditional_mi_given_target_history_bits": conditional_mutual_information(xs, ys, history),
    }


def store_episode(con, snapshot_id: str, kind: str, parent: str | None, spec: dict, data: dict) -> str:
    eid = str(uuid.uuid4())
    con.execute(
        "INSERT INTO episodes VALUES(?,?,?,?,?,?,?)",
        (eid, snapshot_id, "repo-seed-v1", parent, kind, json.dumps(spec, sort_keys=True), stable_hash(data)),
    )
    for tick in range(len(data["id"])):
        for channel in ("density", "entropy", "change", "coherence"):
            value = data[channel][tick]
            con.execute(
                "INSERT INTO channel_samples VALUES(?,?,?,?,?,?)",
                (eid, tick, channel, "", json.dumps(value), stable_hash([data["id"][tick], channel, value])),
            )
    return eid


def probe(source: Path, lab: Path, output: Path, limit: int, seed: int) -> dict:
    raw = source.read_bytes()
    source_hash = stable_hash({"sha256": __import__("hashlib").sha256(raw).hexdigest(), "bytes": len(raw)})
    data = load_aura(source, limit)
    con = open_lab(lab)
    snapshot_id = str(uuid.uuid4())
    con.execute("INSERT INTO source_snapshots VALUES(?,?,?,?,1)", (snapshot_id, str(source), source_hash, time.time()))
    baseline_id = store_episode(con, snapshot_id, "BASELINE_COPY", None, {"operation": "none"}, data)

    rng = random.Random(seed)
    perm = list(range(len(data["id"])))
    rng.shuffle(perm)
    shuffled = {k: ([v[i] for i in perm] if k not in {"id", "ts"} else list(v)) for k, v in data.items()}
    shuffled_id = store_episode(
        con, snapshot_id, "TIME_SHUFFLE", baseline_id,
        {"operation": "joint_channel_time_permutation", "seed": seed, "held_fixed": ["row_count", "marginals"]},
        shuffled,
    )

    # Break one proposed source->target path while retaining every other channel.
    broken = {k: list(v) for k, v in data.items()}
    rng.shuffle(broken["entropy"])
    broken_id = store_episode(
        con, snapshot_id, "EDGE_SOURCE_SHUFFLE", baseline_id,
        {"operation": "shuffle_entropy_only", "seed": seed + 1, "held_fixed": ["target_order", "other_channels", "marginals"]},
        broken,
    )

    pairs = [("entropy", "coherence"), ("density", "coherence"), ("change", "coherence")]
    result = {
        "contract_version": CONTRACT_VERSION,
        "source": {"path": str(source), "hash": source_hash, "rows": len(data["id"])},
        "episodes": {"baseline": baseline_id, "time_shuffle": shuffled_id, "edge_source_shuffle": broken_id},
        "lag_profiles": {},
        "evidence_class": "OBSERVATIONAL_REAL_REPO_SNAPSHOT_PLUS_SYNTHETIC_MUTATION",
        "claim_boundary": "conditional MI is directed prediction evidence, not intervention causality",
        "source_redundancy": {},
    }
    for a, b in (("density", "entropy"), ("density", "change"), ("entropy", "change")):
        qa, qb = quantile_bins(data[a]), quantile_bins(data[b])
        result["source_redundancy"][f"{a}<->{b}"] = {
            "mutual_information_bits": mutual_information(qa, qb),
            "normalized_by_min_entropy": mutual_information(qa, qb) / max(1e-12, min(entropy(qa), entropy(qb))),
        }
    for src, dst in pairs:
        key = f"{src}->{dst}"
        result["lag_profiles"][key] = {
            "baseline": [lag_readout(data, src, dst, lag) for lag in range(1, 9)],
            "time_shuffle": [lag_readout(shuffled, src, dst, lag) for lag in range(1, 9)],
            "edge_source_shuffle": [lag_readout(broken, src, dst, lag) for lag in range(1, 9)],
        }
    result["result_hash"] = stable_hash(result)
    con.commit(); con.close()
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    return result


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--source", type=Path, required=True)
    p.add_argument("--lab", type=Path, default=Path("emergence_lab.db"))
    p.add_argument("--output", type=Path, default=Path("real_probe.json"))
    p.add_argument("--limit", type=int, default=5000)
    p.add_argument("--seed", type=int, default=73)
    a = p.parse_args()
    print(json.dumps(probe(a.source, a.lab, a.output, a.limit, a.seed), indent=2))


if __name__ == "__main__":
    main()
