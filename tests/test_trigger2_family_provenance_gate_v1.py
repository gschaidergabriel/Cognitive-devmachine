import importlib.util
import json
from hashlib import sha256
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "tools" / "trigger2_family_provenance_gate_v1.py"
spec = importlib.util.spec_from_file_location("t2_family_prov", PATH)
mod = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(mod)


def d(v):
    return sha256(json.dumps(v, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()


def row(rid, split, fid, episode, history, parents=None, checkpoint="0" * 64):
    p = {
        "model_family": "Qwen3.5-0.8B",
        "checkpoint_sha256": checkpoint,
        "generator_family_id": "trusted-generator-v1",
        "source_episode_root_id": episode,
        "repackaged_history_root_id": history,
        "parent_family_ids": list(parents or []),
    }
    p["lineage_digest"] = d(p)
    return {"row_id": rid, "split": split, "causal_family_id": fid,
            "family_provenance_evaluator_only": p}


def clean():
    return {"rows": [
        row("r1", "TRAIN", "f-train", "ep-train", "hist-train"),
        row("r2", "CALIBRATION", "f-cal", "ep-cal", "hist-cal"),
        row("r3", "HOLDOUT", "f-hold", "ep-hold", "hist-hold"),
    ]}


def test_disjoint_families_pass():
    out = mod.adjudicate(clean())
    assert out["pass"] is True
    assert out["accepted_dataset_tokens_minted"] == 0
    assert out["training_credit_minted"] == 0


def test_repackaged_history_echo_cross_split_fails_even_after_rehash():
    b = clean()
    p = b["rows"][2]["family_provenance_evaluator_only"]
    p["source_episode_root_id"] = "ep-train"
    p["repackaged_history_root_id"] = "hist-train"
    p["lineage_digest"] = d({k: v for k, v in p.items() if k != "lineage_digest"})
    out = mod.adjudicate(b)
    assert out["pass"] is False
    assert any(x.startswith("ANTI_ECHO_ROOT_CROSS_SPLIT:") for x in out["failures"])


def test_checkpoint_transplant_with_stale_digest_fails():
    b = clean()
    b["rows"][2]["family_provenance_evaluator_only"]["checkpoint_sha256"] = "1" * 64
    out = mod.adjudicate(b)
    assert out["pass"] is False
    assert "ROW[2]:LINEAGE_DIGEST_MISMATCH" in out["failures"]


def test_cross_split_parent_ancestry_fails():
    b = {"rows": [
        row("r1", "TRAIN", "f-train", "ep-a", "hist-a"),
        row("r2", "CALIBRATION", "f-cal", "ep-b", "hist-b"),
        row("r3", "HOLDOUT", "f-hold", "ep-c", "hist-c", parents=["f-train"]),
    ]}
    out = mod.adjudicate(b)
    assert out["pass"] is False
    assert "ANCESTRY_CROSS_SPLIT:f-hold->f-train" in out["failures"]


def test_missing_holdout_fails_closed():
    b = clean()
    b["rows"] = b["rows"][:2]
    out = mod.adjudicate(b)
    assert out["pass"] is False
    assert "MISSING_SPLIT:HOLDOUT" in out["failures"]


def test_missing_or_ambiguous_provenance_fails_closed():
    b = clean()
    del b["rows"][1]["family_provenance_evaluator_only"]["source_episode_root_id"]
    out = mod.adjudicate(b)
    assert out["pass"] is False
    assert any("SOURCE_EPISODE_ROOT_ID" in x for x in out["failures"])
