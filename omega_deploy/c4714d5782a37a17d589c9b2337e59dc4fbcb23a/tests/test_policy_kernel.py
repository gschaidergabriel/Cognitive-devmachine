from pathlib import Path

from omega.alignment import Decision, EffectBinding
from omega.policy_kernel import PolicyKernel


ROOT = Path(__file__).resolve().parents[1]


def binding(request, organ="omega-vps"):
    return EffectBinding.prepare(
        effect_id="effect_test",
        invocation_id="inv_test",
        tool_use_id="tool_test",
        delegation_id="deleg_test",
        child_identity_sha256="a" * 64,
        request=request,
        organ_id=organ,
        owner_id="omega",
        machine_id="omega-vps",
    )


def test_ordinary_exec_allowed():
    req = {"op":"exec","command":"printf hello","cwd":"/workspace"}
    gate = PolicyKernel.from_path(ROOT / "config/autonomy_policy.json").authorize(binding(req), req)
    assert gate.decision is Decision.ALLOW


def test_delete_is_denied():
    req = {"op":"exec","command":"rm -rf /workspace/something"}
    gate = PolicyKernel.from_path(ROOT / "config/autonomy_policy.json").authorize(binding(req), req)
    assert gate.decision is Decision.DENY


def test_format_is_denied():
    req = {"op":"exec","command":"mkfs.ext4 /dev/sdz1"}
    gate = PolicyKernel.from_path(ROOT / "config/autonomy_policy.json").authorize(binding(req), req)
    assert gate.decision is Decision.DENY


def test_protected_policy_write_is_denied():
    req = {"op":"write_text","path":"config/autonomy_policy.json","content":"{}"}
    gate = PolicyKernel.from_path(ROOT / "config/autonomy_policy.json").authorize(binding(req), req)
    assert gate.decision is Decision.DENY


def test_read_is_allowed():
    req = {"op":"read_file","path":"README.md"}
    gate = PolicyKernel.from_path(ROOT / "config/autonomy_policy.json").authorize(binding(req), req)
    assert gate.decision is Decision.ALLOW
