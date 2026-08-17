from pathlib import Path

import pytest

import clayverse.terminal_gateway as gateway
from clayverse.clerk_auth import AuthenticationError


ROOT = Path(__file__).resolve().parents[1]


def test_clerk_auth_expiry_must_be_finite_and_future():
    assert gateway._auth_expiry_deadline({"exp": 110}, now=100) == 110.0

    for invalid in (None, True, float("inf"), 100, 99):
        with pytest.raises(AuthenticationError):
            gateway._auth_expiry_deadline({"exp": invalid}, now=100)


def test_reauthentication_cannot_change_clerk_subject_or_session():
    assert gateway._reauthenticated_expiry(
        {"sub": "user_g", "sid": "sess_1", "exp": 120},
        expected_subject="user_g",
        expected_clerk_session_id="sess_1",
        now=100,
    ) == 120.0

    with pytest.raises(AuthenticationError, match="changed subject"):
        gateway._reauthenticated_expiry(
            {"sub": "user_a", "sid": "sess_1", "exp": 120},
            expected_subject="user_g",
            expected_clerk_session_id="sess_1",
            now=100,
        )
    with pytest.raises(AuthenticationError, match="changed session"):
        gateway._reauthenticated_expiry(
            {"sub": "user_g", "sid": "sess_2", "exp": 120},
            expected_subject="user_g",
            expected_clerk_session_id="sess_1",
            now=100,
        )


def test_reauth_envelope_does_not_widen_ordinary_control_bound():
    reauth = '{"type":"reauth","token":"' + ("x" * 5_000) + '"}'
    assert gateway._decode_terminal_control(reauth)["type"] == "reauth"

    oversized_resize = '{"type":"resize","pad":"' + ("x" * 5_000) + '"}'
    with pytest.raises(ValueError, match="exceeds bound"):
        gateway._decode_terminal_control(oversized_resize)


def test_live_terminal_auth_is_expiry_fenced_and_refreshable():
    source = (ROOT / "clayverse" / "terminal_gateway.py").read_text()
    assert "auth_expires_at = _auth_expiry_deadline(claims)" in source
    assert "asyncio.wait_for(ws.receive(), timeout=remaining)" in source
    assert "expected_subject=clerk_subject" in source
    assert "expected_clerk_session_id=clerk_session_id" in source
    assert "getToken({{skipCache:true}})" in source
    assert "type:'reauth'" in source
    assert '"type": "reauthenticated"' in source
    assert "await asyncio.gather(*pending" not in source
