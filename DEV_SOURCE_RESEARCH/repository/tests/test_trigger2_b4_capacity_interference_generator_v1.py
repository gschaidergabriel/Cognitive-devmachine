from __future__ import annotations

from collections import Counter

from tools import trigger2_b4_capacity_interference_generator_v1 as b4


def test_fail_closed_audit_passes_on_current_generator():
    rows = b4.build_rows()
    report = b4.audit(rows)
    assert report["overall_pass"] is True
    assert report["failures"] == []


def test_split_counts_match_design():
    rows = b4.build_rows()
    counts = Counter(r["split"] for r in rows)
    assert dict(counts) == {"TRAIN": 420, "VALIDATION": 210, "HOLDOUT_FROZEN": 182}


def test_every_row_training_ineligible_and_method_only():
    rows = b4.build_rows()
    for r in rows:
        assert r["training_eligible"] is False
        assert r["evidence_class"] == "METHOD_ONLY"
        assert r["canonical_truth_allowed"] is False


def test_target_always_reachable_from_true_mapping():
    rows = b4.build_rows()
    for r in rows:
        assert r["target"] == r["true_mapping"][r["queried_entity"]]


def test_holdout_atom_pool_disjoint_from_train_val():
    rows = b4.build_rows()
    train_val_atoms = {
        a for r in rows if r["split"] in ("TRAIN", "VALIDATION") for a in r["true_mapping"].values()
    }
    hold_atoms = {a for r in rows if r["split"] == "HOLDOUT_FROZEN" for a in r["true_mapping"].values()}
    assert hold_atoms and hold_atoms.isdisjoint(train_val_atoms)


def test_lookalike_decoys_never_collide_with_real_atoms():
    rows = b4.build_rows()
    for r in rows:
        if r["interference_kind"] == "LOOKALIKE":
            decoy_atoms = {ln.rsplit("=>", 1)[1] for ln in r["filler_lines"]}
            assert not (decoy_atoms & set(r["true_mapping"].values()))


def test_no_duplicate_rendered_prompts():
    rows = b4.build_rows()
    prompts = [r["prompt"] for r in rows]
    assert len(prompts) == len(set(prompts))


def test_deterministic_across_process_reruns():
    import hashlib
    import json
    import os
    import subprocess
    import sys

    payload_a = "\n".join(
        json.dumps(r, ensure_ascii=False, separators=(",", ":")) for r in b4.build_rows()
    )
    env = dict(os.environ)
    env["PYTHONHASHSEED"] = "999"
    proc = subprocess.run(
        [sys.executable, "-c", (
            "import sys; sys.path.insert(0, 'tools'); "
            "import trigger2_b4_capacity_interference_generator_v1 as b4; import json; "
            "print('\\n'.join(json.dumps(r, ensure_ascii=False, separators=(',', ':')) for r in b4.build_rows()))"
        )],
        cwd=str(b4.Path(__file__).resolve().parents[1]),
        capture_output=True,
        text=True,
        env=env,
    )
    assert proc.returncode == 0, proc.stderr
    assert hashlib.sha256(payload_a.encode()).hexdigest() == hashlib.sha256(proc.stdout.strip().encode()).hexdigest()
