from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_container_user_login_shell_is_the_fail_closed_guard():
    dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8")
    useradd_lines = [line for line in dockerfile.splitlines() if "useradd --system" in line]
    assert len(useradd_lines) == 1
    assert "--shell /opt/clayverse/runtime/deny-shell clayverse" in useradd_lines[0]
    assert "--shell /bin/bash clayverse" not in useradd_lines[0]


def test_direct_shell_guard_is_present_before_runtime_user_creation_and_fails_closed():
    dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8")
    guard_copy = "COPY --chown=root:root policy/deny-shell /opt/clayverse/runtime/deny-shell"
    useradd = "RUN useradd --system --uid 10001 --create-home --shell /opt/clayverse/runtime/deny-shell clayverse"
    assert guard_copy in dockerfile
    assert useradd in dockerfile
    assert dockerfile.index(guard_copy) < dockerfile.index(useradd)
    assert "chmod 0555 /opt/clayverse/runtime/deny-shell" in dockerfile

    guard = (ROOT / "policy" / "deny-shell").read_text(encoding="utf-8")
    assert guard.startswith("#!/bin/sh\n")
    assert "exit 126" in guard


def test_normal_product_entrypoint_remains_explicit_python_not_login_shell():
    dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8")
    assert 'ENTRYPOINT ["python","-m","clayverse.service"]' in dockerfile
