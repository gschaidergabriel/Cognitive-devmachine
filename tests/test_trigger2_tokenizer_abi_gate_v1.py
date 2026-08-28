import importlib.util
from pathlib import Path

def _load():
    p = Path(__file__).resolve().parents[1] / "tools" / "trigger2_tokenizer_abi_gate_v1.py"
    spec = importlib.util.spec_from_file_location("tok_abi_gate", p)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m

gate = _load()

def test_valid_atoms_pass():
    row = {"tokenizer_atoms_used": ["A", "B", "yes", "0"]}
    r = gate.adjudicate(row)
    assert r["pass"], r["failures"]

def test_unknown_symbol_fails_closed():
    row = {"tokenizer_atoms_used": ["A", "ZZZ_not_real"]}
    r = gate.adjudicate(row)
    assert not r["pass"]
    assert any("ATOM_UNKNOWN_NOT_IN_INDEX" in f for f in r["failures"])

def test_rejected_or_atom_fails_closed():
    row = {"tokenizer_atoms_used": ["yes", "or"]}
    r = gate.adjudicate(row)
    assert not r["pass"]
    assert any("ATOM_EXPLICITLY_REJECTED" in f for f in r["failures"])

def test_missing_atoms_used_fails_closed():
    row = {}
    r = gate.adjudicate(row)
    assert not r["pass"]
    assert "NO_TOKENIZER_ATOMS_USED_DECLARED" in r["failures"]

def test_wrong_claimed_ids_fail_closed():
    row = {"tokenizer_atoms_used": ["A"], "tokenizer_atom_ids": {"A": [999999]}}
    r = gate.adjudicate(row)
    assert not r["pass"]
    assert any("ATOM_ID_MISMATCH" in f for f in r["failures"])

def test_correct_claimed_ids_pass():
    baseline = gate.adjudicate({"tokenizer_atoms_used": ["A"]})
    real_ids = baseline["resolved_atoms"]["A"]
    row = {"tokenizer_atoms_used": ["A"], "tokenizer_atom_ids": {"A": real_ids}}
    r = gate.adjudicate(row)
    assert r["pass"], r["failures"]

def test_tokenizer_hash_mismatch_fails_closed():
    row = {"tokenizer_atoms_used": ["A"], "tokenizer_files_sha256": {"bogus": "hash"}}
    r = gate.adjudicate(row)
    assert not r["pass"]
    assert "TOKENIZER_HASH_MISMATCH" in r["failures"]

def test_row_not_dict_fails_closed():
    r = gate.adjudicate("not a dict")
    assert not r["pass"]
    assert "ROW_NOT_DICT" in r["failures"]
