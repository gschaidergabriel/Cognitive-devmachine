#!/usr/bin/env python3
"""Identity-instrumented successor entrypoint for the retained intermediate lane.

The scientific experiment remains implemented by
trigger1_local_qwen06_intermediate_execute.py. This wrapper adds one execution-session
identity and a measurement-independent model_execution_id to every concrete local
model invocation so replay identity can be separated from measured evidence.
"""
from __future__ import annotations

import uuid
from typing import Any

import trigger1_local_qwen06_intermediate_execute as core
from jspace_execution_identity_v1 import derive_model_execution_id


class IdentityRuntimeState(core.RuntimeState):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self.runtime_session_id = uuid.uuid4().hex

    def infer(self, payload: dict[str, Any]) -> dict[str, Any]:
        row = super().infer(payload)
        row["runtime_session_id"] = self.runtime_session_id
        row["model_execution_id"] = derive_model_execution_id(self.runtime_session_id, row)
        return row


def main() -> int:
    core.RuntimeState = IdentityRuntimeState
    return core.main()


if __name__ == "__main__":
    raise SystemExit(main())
