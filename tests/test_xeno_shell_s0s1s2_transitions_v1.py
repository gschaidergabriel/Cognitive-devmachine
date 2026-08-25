import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import xeno_shell_s0s1s2_transitions_v1 as tr


def test_all_9_transitions_present():
    expected = {
        "S0->S1", "S2->S1", "S1->S0", "S2->S0", "S1->EFFECT",
        "S2->EFFECT", "CLAUDE->S1", "CLAUDE->S0", "JSPACE->S0",
    }
    assert set(tr.TRANSITION_MATRIX.keys()) == expected


def test_forbidden_set_matches_spec_exactly():
    assert tr.FORBIDDEN_TRANSITIONS == frozenset(
        {"S2->S0", "S2->EFFECT", "CLAUDE->S0", "JSPACE->S0"}
    )


def test_legitimate_transition_allowed():
    tr.assert_transition_allowed("S1->S0")
    tr.assert_transition_allowed("CLAUDE->S1")


def test_unknown_transition_fails_closed():
    try:
        tr.assert_transition_allowed("S2->EFFECT_VIA_SIDE_DOOR")
        assert False
    except tr.TransitionError as e:
        assert "UNKNOWN_TRANSITION" in str(e)


def test_s2_to_s0_forbidden():
    try:
        tr.assert_transition_allowed("S2->S0")
        assert False
    except tr.TransitionError as e:
        assert "FORBIDDEN_DIRECT" in str(e)


def test_claude_to_s0_forbidden():
    try:
        tr.assert_transition_allowed("CLAUDE->S0")
        assert False
    except tr.TransitionError as e:
        assert "FORBIDDEN_DIRECT" in str(e)


def test_jspace_to_s0_forbidden():
    try:
        tr.assert_transition_allowed("JSPACE->S0")
        assert False
    except tr.TransitionError as e:
        assert "FORBIDDEN_DIRECT" in str(e)


def test_attempt_forbidden_direct_write_refuses():
    try:
        tr.attempt_forbidden_direct_write("S2->S0", actor="node-1", payload={"x": 1})
        assert False
    except tr.TransitionError as e:
        assert "REFUSED_FORBIDDEN_DIRECT_TRANSITION" in str(e)


def test_attempt_forbidden_direct_write_rejects_legit_transition_misuse():
    try:
        tr.attempt_forbidden_direct_write("S1->S0", actor="coord-1", payload={})
        assert False
    except tr.TransitionError as e:
        assert "NOT_A_FORBIDDEN_TRANSITION" in str(e)


def test_s1_ordinary_write_actually_rejected_by_real_fabric(tmp_path):
    """Ties the S1-side of the transition contract to the real enforcement mechanism
    (grid10_fabric.Fabric), not just the documented matrix -- an ordinary actor cannot
    write S1 canonical state directly, matching TRANSITION_MATRIX's implicit
    'only coordinator_commit may write S1' rule."""
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
    import grid10_fabric as gf

    fab = gf.Fabric(tmp_path / "s1_test.sqlite3")
    try:
        fab.ordinary_write_attempt("ordinary-node-1")
        assert False, "expected FabricError"
    except gf.FabricError as e:
        assert "ORDINARY_NODE_S1_WRITE_FORBIDDEN" in str(e)
