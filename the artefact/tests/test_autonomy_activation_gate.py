from __future__ import annotations

from types import SimpleNamespace

import pytest

from clayverse.autonomy_activation import (
    AutonomyActivationError,
    attest_autonomy_activation,
    install_attested_autonomy_pulse,
)
from clayverse.autonomy_pulse import AutonomyPulse
from clayverse.terminal_activity import TerminalActivityRegistry
from clayverse.terminal_sessions import TerminalSessionManager


class _App:
    # install_autonomy_pulse (clayverse/autonomy_app.py) moved from
    # add_event_handler(...) to app.router.on_startup/on_shutdown.append(...)
    # -- "FastAPI removed add_event_handler in favour of lifespan" (see that
    # file's comment). This fake must carry the same shape a real FastAPI
    # app exposes, or every install_attested_autonomy_pulse() call blows up
    # on AttributeError before the attestation gate is even reached.
    def __init__(self):
        self.router = SimpleNamespace(on_startup=[], on_shutdown=[])
        self.state = SimpleNamespace()


def test_split_terminal_managers_fail_activation_even_on_same_state_root(tmp_path):
    state = tmp_path / "state"
    web = TerminalSessionManager(state, tmp_path / "workspace")
    pulse_manager = TerminalSessionManager(state, tmp_path / "workspace")
    pulse = AutonomyPulse(state, pulse_manager)

    attestation = attest_autonomy_activation(web, pulse)
    assert attestation.shared_state_root is True
    assert attestation.shared_activity_registry is False
    assert attestation.pulse_uses_web_terminal_manager is False
    assert attestation.ready is False

    app = _App()
    with pytest.raises(AutonomyActivationError, match="exact TerminalSessionManager"):
        install_attested_autonomy_pulse(app, web_terminals=web, pulse=pulse)
    assert app.router.on_startup == [] and app.router.on_shutdown == []
    assert not hasattr(app.state, "autonomy_pulse_lifecycle")


def test_exact_same_terminal_manager_is_activation_ready(tmp_path):
    state = tmp_path / "state"
    shared_activity = TerminalActivityRegistry()
    manager = TerminalSessionManager(
        state,
        tmp_path / "workspace",
        activity=shared_activity,
    )
    pulse = AutonomyPulse(state, manager)

    attestation = attest_autonomy_activation(manager, pulse)
    assert attestation.ready is True
    assert attestation.shared_activity_registry is True
    assert attestation.shared_state_root is True
    assert attestation.pulse_uses_web_terminal_manager is True

    app = _App()
    lifecycle = install_attested_autonomy_pulse(
        app,
        web_terminals=manager,
        pulse=pulse,
    )
    assert lifecycle is app.state.autonomy_pulse_lifecycle
    assert app.state.autonomy_activation.ready is True
    assert app.router.on_startup == [lifecycle.startup]
    assert app.router.on_shutdown == [lifecycle.shutdown]
