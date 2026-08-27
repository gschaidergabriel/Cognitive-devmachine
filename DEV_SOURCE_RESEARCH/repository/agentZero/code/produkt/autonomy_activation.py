from __future__ import annotations

from dataclasses import dataclass

from .autonomy_app import install_autonomy_pulse, AutonomyPulseLifecycle
from .autonomy_pulse import AutonomyPulse
from .terminal_sessions import TerminalSessionManager


class AutonomyActivationError(RuntimeError):
    pass


@dataclass(frozen=True)
class AutonomyActivationAttestation:
    shared_activity_registry: bool
    shared_state_root: bool
    pulse_uses_web_terminal_manager: bool

    @property
    def ready(self) -> bool:
        return bool(
            self.shared_activity_registry
            and self.shared_state_root
            and self.pulse_uses_web_terminal_manager
        )


def attest_autonomy_activation(
    web_terminals: TerminalSessionManager,
    pulse: AutonomyPulse,
) -> AutonomyActivationAttestation:
    """Prove the pulse and browser attach path share one transient terminal arbiter."""
    pulse_terminals = pulse.terminals
    return AutonomyActivationAttestation(
        shared_activity_registry=web_terminals.activity is pulse_terminals.activity,
        shared_state_root=web_terminals.state_root.resolve() == pulse_terminals.state_root.resolve(),
        pulse_uses_web_terminal_manager=web_terminals is pulse_terminals,
    )


def install_attested_autonomy_pulse(
    app,
    *,
    web_terminals: TerminalSessionManager,
    pulse: AutonomyPulse,
) -> AutonomyPulseLifecycle:
    attestation = attest_autonomy_activation(web_terminals, pulse)
    if not attestation.ready:
        raise AutonomyActivationError(
            "autonomy pulse activation denied: browser/PTTY and pulse do not share the exact TerminalSessionManager/activity arbiter"
        )
    lifecycle = install_autonomy_pulse(app, pulse)
    app.state.autonomy_activation = attestation
    return lifecycle
