import hashlib
import os
import stat
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "stage-entityos.sh"


def _run(tmp_path: Path, source: Path, digest: str):
    return subprocess.run(
        ["sh", str(SCRIPT), str(source), digest],
        cwd=tmp_path,
        text=True,
        capture_output=True,
        check=False,
    )


def test_stage_entityos_binds_exact_bytes_and_seals_mode(tmp_path):
    source = tmp_path / "candidate"
    payload = b"bounded-entityos-staging-regression\x00\xff"
    source.write_bytes(payload)
    digest = hashlib.sha256(payload).hexdigest()

    result = _run(tmp_path, source, digest.upper())

    assert result.returncode == 0, result.stderr
    staged = tmp_path / "EntityOS"
    assert staged.read_bytes() == payload
    assert hashlib.sha256(staged.read_bytes()).hexdigest() == digest
    assert stat.S_IMODE(staged.stat().st_mode) == 0o555


def test_stage_entityos_rejects_digest_mismatch_without_output(tmp_path):
    source = tmp_path / "candidate"
    source.write_bytes(b"wrong-bytes")

    result = _run(tmp_path, source, "0" * 64)

    assert result.returncode == 65
    assert "digest mismatch" in result.stderr.lower()
    assert not (tmp_path / "EntityOS").exists()


def test_stage_entityos_rejects_symlink_source(tmp_path):
    target = tmp_path / "target"
    target.write_bytes(b"target")
    source = tmp_path / "candidate"
    os.symlink(target, source)
    digest = hashlib.sha256(target.read_bytes()).hexdigest()

    result = _run(tmp_path, source, digest)

    assert result.returncode == 66
    assert "symlink rejected" in result.stderr.lower()
    assert not (tmp_path / "EntityOS").exists()
