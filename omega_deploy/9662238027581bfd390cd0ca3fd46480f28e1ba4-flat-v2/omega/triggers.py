from __future__ import annotations

import dataclasses
from typing import Final


@dataclasses.dataclass(frozen=True)
class TriggerSpec:
    token: str
    name: str
    meaning: str
    requires_reentry: bool
    maximal_convergence: bool
    reentry_trigger: str | None = None


@dataclasses.dataclass(frozen=True)
class TriggerInvocation:
    spec: TriggerSpec
    instruction: str = ""


TRIGGERS: Final[dict[str, TriggerSpec]] = {
    "999": TriggerSpec(
        token="999",
        name="REENTRY",
        meaning="RE-ENTER_RESOLVE_DOCK_ASSIMILATE_CONTINUE",
        requires_reentry=False,
        maximal_convergence=False,
    ),
    "777": TriggerSpec(
        token="777",
        name="CONVERGENCE",
        meaning="REENTER_CONVERGE_EXECUTE_VERIFY_PROMOTE",
        requires_reentry=True,
        maximal_convergence=True,
        reentry_trigger="999",
    ),
}


def resolve_trigger(text: str) -> TriggerInvocation | None:
    """Resolve only an explicit leading OMEGA trigger token.

    `777 anything...` and `999 anything...` are valid invocations. Embedded numbers,
    prefixes such as `1777`, and ordinary prose are deliberately ignored so that
    unrelated numeric content cannot start an OMEGA macrocycle accidentally.
    """

    if not isinstance(text, str):
        return None
    parts = text.strip().split(maxsplit=1)
    if not parts:
        return None
    spec = TRIGGERS.get(parts[0])
    if spec is None:
        return None
    instruction = parts[1].strip() if len(parts) == 2 else ""
    return TriggerInvocation(spec=spec, instruction=instruction)


def convergence_requires_reentry(invocation: TriggerInvocation) -> bool:
    return invocation.spec.token == "777" and invocation.spec.requires_reentry
