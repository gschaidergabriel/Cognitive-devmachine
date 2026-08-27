from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_runtime_user_does_not_own_or_write_clayverse_control_plane():
    dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8")

    assert "chown -R clayverse:clayverse /opt/clayverse" not in dockerfile
    assert "chown -R root:root /opt/clayverse" in dockerfile
    assert "chmod -R a-w /opt/clayverse" in dockerfile


def test_runtime_writable_paths_remain_explicitly_separate():
    dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8")

    assert (
        "chown -R clayverse:clayverse /var/lib/clayverse /workspace /home/clayverse/.claude"
        in dockerfile
    )
    assert 'VOLUME ["/var/lib/clayverse", "/workspace"]' in dockerfile
