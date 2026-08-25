from __future__ import annotations
import hashlib, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import trigger2_dynamic_codebook_binding_gate_v4 as g


def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()

def fixture(tmp_path):
    archive=tmp_path/"123.tar.xz"; archive.write_bytes(b"source")
    abi=tmp_path/"MANIFEST.json"; abi.write_text('{"abi":"test"}\n')
    invp=tmp_path/"atoms.json"
    atoms=[{"source_row":i,"atom":f"z{i:02d}"} for i in range(46)]
    inv={"schema":g.ATOM_INVENTORY_SCHEMA,"source_archive_sha256":sha(archive),"abi_manifest_sha256":sha(abi),"accepted_atom_count":46,"atoms":atoms}
    invp.write_text(json.dumps(inv,sort_keys=True)+'\n')
    tok=tmp_path/"tokenizer.json"; tok.write_text('{"tok":"test"}\n')
    auditp=tmp_path/"audit.json"
    audit={"schema":g.TOKEN_AUDIT_SCHEMA,"tokenizer_identity_sha256":sha(tok),"atom_token_counts":{f"z{i:02d}":1 for i in range(46)}}
    auditp.write_text(json.dumps(audit,sort_keys=True)+'\n')
    row={"schema":g.ROW_SCHEMA,"row_id":"r1","episode_atom_triplet":["z00","z01","z02"],"target":"z00","source_archive_sha256":sha(archive),"atom_inventory_sha256":sha(invp),"atom_tokenization_audit_sha256":sha(auditp)}
    return row,dict(source_archive_path=archive,atom_inventory_path=invp,abi_manifest_path=abi,tokenizer_identity_path=tok,atom_tokenization_audit_path=auditp),audit

def base_pass(rows, lexemes, expected_hashes, atom_token_counts):
    return {"candidate_binding_gate_pass":True,"failures":[],"row_failures":[],"metrics":{"stub":"pass"}}

def run(row,paths,audit):
    return g.validate([row],[],{},audit["atom_token_counts"],base_validate=base_pass,**paths)

def test_exact_accepted_inventory_and_audit_pass(tmp_path):
    row,paths,audit=fixture(tmp_path); r=run(row,paths,audit)
    assert r["candidate_binding_gate_pass"],r
    assert r["metrics"]["verified_accepted_atoms"]==46

def test_unlisted_atom_rejected_even_if_token_audit_is_hash_bound(tmp_path):
    row,paths,audit=fixture(tmp_path); row["episode_atom_triplet"][0]="invented"
    r=run(row,paths,audit)
    assert not r["candidate_binding_gate_pass"]
    assert any("ATOM_NOT_IN_VERIFIED_ACCEPTED_INVENTORY:invented" in f for x in r["row_failures"] for f in x["failures"])

def test_unlisted_target_rejected(tmp_path):
    row,paths,audit=fixture(tmp_path); row["target"]="invented"
    r=run(row,paths,audit)
    assert not r["candidate_binding_gate_pass"]
    assert any("TARGET_NOT_IN_VERIFIED_ACCEPTED_INVENTORY:invented" in f for x in r["row_failures"] for f in x["failures"])

def test_token_audit_must_equal_accepted_inventory(tmp_path):
    row,paths,audit=fixture(tmp_path); audit["atom_token_counts"]["invented"]=1
    paths["atom_tokenization_audit_path"].write_text(json.dumps(audit,sort_keys=True)+'\n')
    row["atom_tokenization_audit_sha256"]=sha(paths["atom_tokenization_audit_path"])
    r=run(row,paths,audit)
    assert "TOKEN_AUDIT_CONTAINS_NONACCEPTED_ATOMS" in r["failures"]

def test_inventory_binds_actual_source_archive(tmp_path):
    row,paths,audit=fixture(tmp_path); paths["source_archive_path"].write_bytes(b"changed")
    row["source_archive_sha256"]=sha(paths["source_archive_path"])
    r=run(row,paths,audit)
    assert "ATOM_INVENTORY_SOURCE_ARCHIVE_BINDING" in r["failures"]

def test_rejected_or_cannot_enter_accepted_inventory(tmp_path):
    row,paths,audit=fixture(tmp_path)
    inv=json.loads(paths["atom_inventory_path"].read_text()); inv["atoms"][0]["atom"]="or"
    paths["atom_inventory_path"].write_text(json.dumps(inv,sort_keys=True)+'\n')
    row["atom_inventory_sha256"]=sha(paths["atom_inventory_path"])
    r=run(row,paths,audit)
    assert "ATOM_INVENTORY_REJECTED_ATOM_OR_PRESENT" in r["failures"]
