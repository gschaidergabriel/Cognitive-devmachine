#!/usr/bin/env python3
"""Differential adjudication probe for the two current H-WP-02 StateLedger lineages.

This intentionally imports and executes both repository implementations on the same
small golden corpus. It records divergence; it does not select a winner by ancestry.
"""
from __future__ import annotations
import importlib.util
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
A_PATH = ROOT / "harness" / "reference_state_ledger.py"
B_PATH = ROOT / "harness" / "reference" / "state_ledger.py"


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def a_commit(mod, ledger, *, eid, idem, base, muts):
    return ledger.commit(
        event_id=eid,
        idempotency_key=idem,
        base_epoch=base,
        event_type="SET_STATE",
        mutations=[mod.Mutation(domain=d, key=k, value=v, epistemic_state="KNOWN") for d, k, v in muts],
        provenance={"source": "wp02-lineage-differential"},
        committed_at=f"2026-08-09T00:00:{base+1:02d}Z",
        writer_node="DIFF",
    )


def b_commit(mod, ledger, *, eid, idem, base, muts):
    return ledger.append_event(
        event_id=eid,
        idem=idem,
        base_epoch=base,
        event_type="SET_STATE",
        writer="DIFF",
        ops=[{"op": "SET", "domain": d, "key": k, "value": v, "epistemic": "KNOWN", "status": "CURRENT"} for d, k, v in muts],
        provenance={"source": "wp02-lineage-differential"},
        source={"fixture": "golden"},
        execution={"attempt": base + 1},
        committed_at=f"2026-08-09T00:00:{base+1:02d}Z",
    )


def main():
    A = load("hwp02_lineage_a", A_PATH)
    B = load("hwp02_lineage_b", B_PATH)
    out = {"schema_version": "1.0", "probe": "H-WP-02-LINEAGE-DIFFERENTIAL", "cases": {}}

    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        # Same final semantic values, different event grouping/history.
        a1 = A.StateLedger(td / "a1.sqlite"); a_commit(A, a1, eid="a-one", idem="a-one", base=0, muts=[("world","a",1),("world","b",2)])
        a2 = A.StateLedger(td / "a2.sqlite"); a_commit(A, a2, eid="a-two-1", idem="a-two-1", base=0, muts=[("world","a",1)]); a_commit(A, a2, eid="a-two-2", idem="a-two-2", base=1, muts=[("world","b",2)])
        b1 = B.StateLedger(td / "b1.sqlite"); b_commit(B, b1, eid="b-one", idem="b-one", base=0, muts=[("world","a",1),("world","b",2)])
        b2 = B.StateLedger(td / "b2.sqlite"); b_commit(B, b2, eid="b-two-1", idem="b-two-1", base=0, muts=[("world","a",1)]); b_commit(B, b2, eid="b-two-2", idem="b-two-2", base=1, muts=[("world","b",2)])
        out["cases"]["same_final_state_different_history"] = {
            "A_root_equal": a1.head()["root_hash"] == a2.head()["root_hash"],
            "B_semantic_state_hash_equal": b1.semantic_state_hash == b2.semantic_state_hash,
        }
        a1.close(); a2.close(); b1.close(); b2.close()

        # Typed set permutation/dedup semantics.
        va = {"$kind":"set","items":["a","b","a"]}; vb = {"$kind":"set","items":["b","a"]}
        a1 = A.StateLedger(td / "aset1.sqlite"); a_commit(A, a1, eid="as1", idem="as1", base=0, muts=[("memory","tags",va)])
        a2 = A.StateLedger(td / "aset2.sqlite"); a_commit(A, a2, eid="as2", idem="as2", base=0, muts=[("memory","tags",vb)])
        b1 = B.StateLedger(td / "bset1.sqlite"); b_commit(B, b1, eid="bs1", idem="bs1", base=0, muts=[("memory","tags",va)])
        b2 = B.StateLedger(td / "bset2.sqlite"); b_commit(B, b2, eid="bs2", idem="bs2", base=0, muts=[("memory","tags",vb)])
        out["cases"]["typed_set_permutation"] = {
            "A_root_equal": a1.head()["root_hash"] == a2.head()["root_hash"],
            "B_semantic_state_hash_equal": b1.semantic_state_hash == b2.semantic_state_hash,
        }
        a1.close(); a2.close(); b1.close(); b2.close()

        # Idempotency payload collision: same key/event id, changed semantic payload.
        a = A.StateLedger(td / "aidem.sqlite"); a_commit(A, a, eid="same", idem="idem", base=0, muts=[("world","x",1)])
        a_second = a_commit(A, a, eid="same", idem="idem", base=1, muts=[("world","x",999)])
        b = B.StateLedger(td / "bidem.sqlite"); b_commit(B, b, eid="same", idem="idem", base=0, muts=[("world","x",1)])
        b_conflict = False
        try:
            b_commit(B, b, eid="same", idem="idem", base=1, muts=[("world","x",999)])
        except B.IdempotencyConflict:
            b_conflict = True
        out["cases"]["idempotency_payload_collision"] = {
            "A_second_status": a_second["status"],
            "A_value_after_second": a.read("world","x")["value"],
            "B_conflict_rejected": b_conflict,
            "B_value_after_second": b.get("world","x")["value"],
        }
        a.close(); b.close()

    out["capability_surface"] = {
        "A_full_verify": hasattr(A.StateLedger, "verify"),
        "A_snapshot_restore": hasattr(A.StateLedger, "restore_snapshot"),
        "A_domain_epochs": hasattr(A.StateLedger, "domain_epochs"),
        "B_full_verify": hasattr(B.StateLedger, "verify"),
        "B_snapshot_restore": hasattr(B.StateLedger, "restore_snapshot"),
        "B_domain_epochs": hasattr(B.StateLedger, "domain_epochs"),
    }
    print(json.dumps(out, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
