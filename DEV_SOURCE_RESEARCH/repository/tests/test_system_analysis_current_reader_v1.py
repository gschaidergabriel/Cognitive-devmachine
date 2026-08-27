from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MOD_PATH = ROOT / "tools" / "system_analysis_current_reader_v1.py"
spec = importlib.util.spec_from_file_location("system_analysis_current_reader_v1", MOD_PATH)
mod = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(mod)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def make_publication(tmp_path: Path, *, coherent: bool = True) -> tuple[Path, str, Path]:
    repo = tmp_path / "repo"
    fs = repo / "free swarm"
    generation = "a" * 24
    gen = fs / "publication_generations" / generation
    gen.mkdir(parents=True)

    live = {
        "schema": "CLAY_FREE_SWARM_SYSTEM_ANALYSIS/v6",
        "publication_generation": generation,
        "runtime": {"source": "proc"},
    }
    provenance = {
        "publication_generation": generation,
        "authority": {"valid": coherent, "authority_state": "ALIGNED" if coherent else "FAIL_CLOSED"},
        "runtime": {"source": "LIVE_PROC"},
    }
    payloads = {
        "SYSTEM_ANALYSIS_LIVE.json": (json.dumps(live, indent=2) + "\n").encode(),
        "SYSTEM_ANALYSIS_PROVENANCE.json": (json.dumps(provenance, indent=2) + "\n").encode(),
        "README.md": b"# generation-bound readme\n",
    }
    for name, raw in payloads.items():
        (gen / name).write_bytes(raw)

    manifest = {
        "schema": "CLAY_MONITOR_PUBLICATION_SET/v1",
        "publication_generation": generation,
        "files": {name: sha(raw) for name, raw in payloads.items()},
        "authority_state": "ALIGNED" if coherent else "FAIL_CLOSED",
        "control_plane_coherent": coherent,
    }
    manifest_raw = (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode()
    (gen / "MANIFEST.json").write_bytes(manifest_raw)
    pointer = {
        "schema": "CLAY_MONITOR_CURRENT/v1",
        "publication_generation": generation,
        "generation_root": f"publication_generations/{generation}",
        "manifest_sha256": sha(manifest_raw),
    }
    fs.mkdir(parents=True, exist_ok=True)
    (fs / "SYSTEM_ANALYSIS_CURRENT.json").write_text(json.dumps(pointer), encoding="utf-8")
    return repo, generation, gen


def test_verified_current_generation_reads(tmp_path: Path):
    repo, generation, _ = make_publication(tmp_path)
    result = mod.read_current_publication(repo)
    assert result["publication_generation"] == generation
    assert result["control_plane_coherent"] is True
    assert result["live"]["runtime"]["source"] == "proc"
    assert result["authority_rule"] == "CURRENT_POINTER_GENERATION_ROOT_ONLY"


def test_path_escape_rejected(tmp_path: Path):
    repo, generation, _ = make_publication(tmp_path)
    pointer_path = repo / "free swarm" / "SYSTEM_ANALYSIS_CURRENT.json"
    pointer = json.loads(pointer_path.read_text())
    pointer["generation_root"] = f"publication_generations/{generation}/../../outside"
    pointer_path.write_text(json.dumps(pointer))
    try:
        mod.read_current_publication(repo)
    except mod.PublicationReadError as exc:
        assert "path_escape_or_mismatch" in str(exc)
    else:
        raise AssertionError("path escape accepted")


def test_manifest_tamper_rejected(tmp_path: Path):
    repo, _, gen = make_publication(tmp_path)
    manifest_path = gen / "MANIFEST.json"
    obj = json.loads(manifest_path.read_text())
    obj["authority_state"] = "TRANSPLANTED"
    manifest_path.write_text(json.dumps(obj))
    try:
        mod.read_current_publication(repo)
    except mod.PublicationReadError as exc:
        assert "manifest_digest_mismatch" in str(exc)
    else:
        raise AssertionError("tampered manifest accepted")


def test_file_tamper_rejected(tmp_path: Path):
    repo, _, gen = make_publication(tmp_path)
    (gen / "SYSTEM_ANALYSIS_LIVE.json").write_text("{}\n")
    try:
        mod.read_current_publication(repo)
    except mod.PublicationReadError as exc:
        assert "file_digest_mismatch:SYSTEM_ANALYSIS_LIVE.json" == str(exc)
    else:
        raise AssertionError("tampered file accepted")


def test_missing_file_rejected(tmp_path: Path):
    repo, _, gen = make_publication(tmp_path)
    (gen / "README.md").unlink()
    try:
        mod.read_current_publication(repo)
    except mod.PublicationReadError as exc:
        assert str(exc).startswith("missing_file:README.md")
    else:
        raise AssertionError("missing file accepted")


def test_generation_transplant_rejected(tmp_path: Path):
    repo, generation, gen = make_publication(tmp_path)
    manifest_path = gen / "MANIFEST.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["publication_generation"] = "b" * 24
    raw = (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode()
    manifest_path.write_bytes(raw)
    pointer_path = repo / "free swarm" / "SYSTEM_ANALYSIS_CURRENT.json"
    pointer = json.loads(pointer_path.read_text())
    pointer["manifest_sha256"] = sha(raw)
    pointer_path.write_text(json.dumps(pointer))
    try:
        mod.read_current_publication(repo)
    except mod.PublicationReadError as exc:
        assert "manifest_generation_mismatch" == str(exc)
    else:
        raise AssertionError("generation transplant accepted")


def test_compatibility_mirror_cannot_override_authoritative_generation(tmp_path: Path):
    repo, generation, _ = make_publication(tmp_path)
    mirror = repo / "free swarm" / "SYSTEM_ANALYSIS_LIVE.json"
    mirror.write_text(json.dumps({"schema": "FAKE", "publication_generation": "f" * 24}))
    result = mod.read_current_publication(repo)
    assert result["publication_generation"] == generation
    assert result["live"]["schema"] == "CLAY_FREE_SWARM_SYSTEM_ANALYSIS/v6"


def test_incoherent_generation_is_verified_but_not_authorized(tmp_path: Path):
    repo, _, _ = make_publication(tmp_path, coherent=False)
    result = mod.read_current_publication(repo)
    assert result["control_plane_coherent"] is False
    assert result["authority_state"] == "FAIL_CLOSED"
