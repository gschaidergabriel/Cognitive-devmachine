from pathlib import Path

import pytest

from clayverse.clerk_auth import AuthenticationError
from clayverse.terminal_gateway import _auth_expiry_deadline, _reauthenticated_expiry


ROOT = Path(__file__).resolve().parents[1]


def test_auth_expiry_deadline_requires_finite_future_numeric_expiration():
    assert _auth_expiry_deadline({"exp": 1_100}, now=1_000) == 1_100.0
    for invalid in (True, "1100", None, float("inf"), float("nan")):
        with pytest.raises(AuthenticationError):
            _auth_expiry_deadline({"exp": invalid}, now=1_000)
    with pytest.raises(AuthenticationError, match="expired"):
        _auth_expiry_deadline({"exp": 1_000}, now=1_000)


def test_reauth_stays_bound_to_same_clerk_subject_and_session():
    claims = {"sub": "clerk_g", "sid": "sess_1", "exp": 1_100}
    assert _reauthenticated_expiry(
        claims,
        expected_subject="clerk_g",
        expected_clerk_session_id="sess_1",
        now=1_000,
    ) == 1_100.0

    with pytest.raises(AuthenticationError, match="changed subject"):
        _reauthenticated_expiry(
            {**claims, "sub": "clerk_a"},
            expected_subject="clerk_g",
            expected_clerk_session_id="sess_1",
            now=1_000,
        )
    with pytest.raises(AuthenticationError, match="changed session"):
        _reauthenticated_expiry(
            {**claims, "sid": "sess_2"},
            expected_subject="clerk_g",
            expected_clerk_session_id="sess_1",
            now=1_000,
        )


def test_received_frames_are_rechecked_against_expiry_before_state_effects():
    source = (ROOT / "clayverse" / "terminal_gateway.py").read_text()
    receive_at = source.index("message = await asyncio.wait_for(ws.receive(), timeout=remaining)")
    post_receive_fence_at = source.index("if auth_expires_at <= time.time():", receive_at)
    binary_effect_at = source.index('if message.get("bytes") is not None:', post_receive_fence_at)
    control_effect_at = source.index('elif message.get("text") is not None:', binary_effect_at)
    assert receive_at < post_receive_fence_at < binary_effect_at < control_effect_at


def test_reauth_uses_same_verifier_and_returns_new_expiry_to_browser():
    source = (ROOT / "clayverse" / "terminal_gateway.py").read_text()
    assert "refreshed = await asyncio.to_thread(verifier.verify, _auth_token(control))" in source
    assert "auth_expires_at = _reauthenticated_expiry(" in source
    assert '"type": "reauthenticated"' in source
    assert '"auth_expires_at": int(auth_expires_at)' in source
