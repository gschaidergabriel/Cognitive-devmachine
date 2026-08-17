from pathlib import Path

import pytest

from clayverse.clerk_auth import AuthenticationError
from clayverse.identity import IdentityRouter
from clayverse.store import UnifiedDB
from clayverse.terminal_gateway import (
    _assert_reauth_identity_current,
    _auth_expiry_deadline,
    _reauthenticated_expiry,
)


ROOT = Path(__file__).resolve().parents[1]


class _IdentityProbe:
    def __init__(self, result):
        self.result = result
        self.subjects = []

    def resolve(self, subject):
        self.subjects.append(subject)
        return self.result


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


def test_reauth_revalidates_current_clayverse_user_and_session_binding():
    identity = _IdentityProbe(("gabriel", "session:gabriel"))
    _assert_reauth_identity_current(
        identity,
        "clerk_g",
        expected_user_id="gabriel",
        expected_session_id="session:gabriel",
    )
    assert identity.subjects == ["clerk_g"]

    for drifted in (("andreas", "session:andreas"), ("gabriel", "session:drift")):
        identity = _IdentityProbe(drifted)
        with pytest.raises(AuthenticationError, match="identity/session changed"):
            _assert_reauth_identity_current(
                identity,
                "clerk_g",
                expected_user_id="gabriel",
                expected_session_id="session:gabriel",
            )


@pytest.mark.parametrize("drift", ["extra_user", "rights", "generation"])
def test_reauth_rechecks_live_unifieddb_identity_contract(tmp_path, drift):
    db = UnifiedDB(tmp_path / "unified.db")
    identity = IdentityRouter(db, {"clerk_g": "gabriel"})
    try:
        _assert_reauth_identity_current(
            identity,
            "clerk_g",
            expected_user_id="gabriel",
            expected_session_id="session:gabriel",
        )
        if drift == "extra_user":
            db.ensure_user("shadow", "Shadow")
        elif drift == "rights":
            db.db.execute("UPDATE users SET rights='admin' WHERE user_id='gabriel'")
        else:
            db.db.execute("UPDATE sessions SET generation=generation+1 WHERE user_id='gabriel'")
        with pytest.raises(PermissionError):
            _assert_reauth_identity_current(
                identity,
                "clerk_g",
                expected_user_id="gabriel",
                expected_session_id="session:gabriel",
            )
    finally:
        db.close()


def test_received_frames_are_rechecked_against_expiry_before_state_effects():
    source = (ROOT / "clayverse" / "terminal_gateway.py").read_text()
    receive_at = source.index("message = await asyncio.wait_for(ws.receive(), timeout=remaining)")
    post_receive_fence_at = source.index("if auth_expires_at <= time.time():", receive_at)
    binary_effect_at = source.index('if message.get("bytes") is not None:', post_receive_fence_at)
    control_effect_at = source.index('elif message.get("text") is not None:', binary_effect_at)
    assert receive_at < post_receive_fence_at < binary_effect_at < control_effect_at


def test_reauth_revalidates_unifieddb_binding_before_extending_live_socket_lease():
    source = (ROOT / "clayverse" / "terminal_gateway.py").read_text()
    verifier_at = source.index("refreshed = await asyncio.to_thread(verifier.verify, _auth_token(control))")
    expiry_at = source.index("refreshed_expiry = _reauthenticated_expiry(", verifier_at)
    identity_at = source.index("_assert_reauth_identity_current,", expiry_at)
    extend_at = source.index("auth_expires_at = refreshed_expiry", identity_at)
    publish_at = source.index('"type": "reauthenticated"', extend_at)
    assert verifier_at < expiry_at < identity_at < extend_at < publish_at
