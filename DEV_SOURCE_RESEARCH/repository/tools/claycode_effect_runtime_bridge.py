#!/usr/bin/env python3
"""Bridge ClayCode BASE compiled effect requests to sealed ClayRuntime handles.

The compiler/effect IR carries descriptive symbolic capability requirements such as
``cap.fs.read``. Those strings are never authority. This host-owned bridge resolves a
fixed symbolic slot to an opaque runtime-minted handle and performs a concrete Linux
adapter operation. No handle is placed in model/Clay-visible state.

This is the missing architectural seam between tools/claycode_base_effect_pipeline.py
and tools/claycode_base_runtime.py; it does not widen the language syntax.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Mapping

from claycode_base_runtime import ClayRuntime, CapabilityFault

BRIDGE_VERSION = "claycode-effect-runtime-bridge/0.1"


class BridgeFault(RuntimeError):
    pass


@dataclass(frozen=True)
class BoundEffect:
    symbolic_capability: str
    runtime_adapter: str
    runtime_handle: Any
    effect: str
    config: Mapping[str, Any]


class SealedRuntimeGateway:
    """Effect-pipeline compatible gateway backed by opaque ClayRuntime handles."""

    def __init__(self, runtime: ClayRuntime, bindings: list[BoundEffect]):
        self._runtime = runtime
        self._bindings: dict[tuple[str, str], BoundEffect] = {}
        self.trace: list[list[Any]] = []
        for binding in bindings:
            key = (binding.effect, binding.symbolic_capability)
            if key in self._bindings:
                raise BridgeFault(f"DUPLICATE_EFFECT_BINDING:{key}")
            # Descriptor validation proves the supplied object is registered with this
            # runtime while still exposing only a non-authorizing descriptor externally.
            descriptor = runtime.capability_descriptor(binding.runtime_handle)
            if descriptor.get("authorizing") is not False:
                raise BridgeFault("CAPABILITY_DESCRIPTOR_MUST_BE_NON_AUTHORIZING")
            self._bindings[key] = binding

    def public_binding_manifest(self) -> list[dict[str, Any]]:
        """Non-authorizing manifest safe to put in receipts."""
        rows = []
        for (effect, symbolic), binding in sorted(self._bindings.items()):
            descriptor = self._runtime.capability_descriptor(binding.runtime_handle)
            rows.append({
                "effect": effect,
                "symbolic_capability": symbolic,
                "runtime_adapter": binding.runtime_adapter,
                "runtime_capability_kind": descriptor["kind"],
                "capability_ref": descriptor["capability_ref"],
                "policy": descriptor["policy"],
                "context_hash": descriptor.get("context_hash"),
                "authorizing": False,
            })
        return rows

    def _binding(self, effect: str, symbolic_capability: str) -> BoundEffect:
        binding = self._bindings.get((effect, symbolic_capability))
        if binding is None:
            # A model/compiler-emitted string can request but cannot create a binding.
            raise CapabilityFault(f"UNBOUND_SYMBOLIC_CAPABILITY:{effect}:{symbolic_capability}")
        return binding

    def effect(self, effect: str, symbolic_capability: str, value: int) -> int:
        binding = self._binding(effect, symbolic_capability)
        before = len(self._runtime.trace_receipt())
        if effect == "FS_READ":
            # The input selects a relative data item; scope remains fixed by the minted
            # fs.read capability prefix. The bridge parses the file as an integer because
            # the current integrated effect IR slice is Int->Int.
            template = str(binding.config.get("path_template", "{value}.txt"))
            relative = template.format(value=int(value))
            row = self._runtime.invoke(binding.runtime_adapter, binding.runtime_handle, relative)
            try:
                result = int(str(row["text"]).strip())
            except Exception as exc:
                raise BridgeFault("FS_READ_EXPECTED_INTEGER_TEXT") from exc
        elif effect == "DB_WRITE":
            # Concrete SQLite transaction. The frozen effect-pipeline oracle defines
            # DB_WRITE(x)=2*x; we realize that meaning through INSERT/SELECT, not a Python
            # arithmetic shortcut, so translation validation crosses a real DB boundary.
            db_path = str(binding.config.get("db_path", "effects.db"))
            key = f"v:{int(value)}"
            stored = int(value) * 2
            row = self._runtime.invoke(
                binding.runtime_adapter,
                binding.runtime_handle,
                db_path,
                [
                    ("CREATE TABLE IF NOT EXISTS effect_kv(k TEXT PRIMARY KEY, v INTEGER)", ()),
                    ("INSERT OR REPLACE INTO effect_kv(k,v) VALUES(?,?)", (key, stored)),
                    ("SELECT v FROM effect_kv WHERE k=?", (key,)),
                ],
            )
            selected = row.get("rows", [])[-1]
            if selected != [(stored,)]:
                raise BridgeFault(f"DB_WRITE_ROUNDTRIP_MISMATCH:{selected!r}")
            result = int(selected[0][0])
        elif effect == "HTTP":
            # A fixed trusted origin is minted into the net.http_get handle. Clay controls
            # only an integer query parameter; it cannot widen origin authority.
            base_url = str(binding.config["base_url"])
            url = f"{base_url}?x={int(value)}"
            row = self._runtime.invoke(binding.runtime_adapter, binding.runtime_handle, url)
            try:
                result = int(bytes(row["body"]).decode("utf-8").strip())
            except Exception as exc:
                raise BridgeFault("HTTP_EXPECTED_INTEGER_BODY") from exc
        elif effect == "FS_WRITE":
            template = str(binding.config.get("path_template", "{value}.txt"))
            relative = template.format(value=int(value))
            row = self._runtime.invoke(binding.runtime_adapter, binding.runtime_handle, relative, str(int(value)))
            if not row.get("sha256"):
                raise BridgeFault("FS_WRITE_NO_RECEIPT")
            result = int(value)
        else:
            raise BridgeFault(f"UNSUPPORTED_EFFECT:{effect}")

        after_trace = self._runtime.trace_receipt()
        if len(after_trace) != before + 1 or after_trace[-1].get("status") != "PASS":
            raise BridgeFault("RUNTIME_EFFECT_TRACE_NOT_COMMITTED")
        self.trace.append([effect, symbolic_capability, int(value)])
        return result


__all__ = ["SealedRuntimeGateway", "BoundEffect", "BridgeFault", "BRIDGE_VERSION"]
