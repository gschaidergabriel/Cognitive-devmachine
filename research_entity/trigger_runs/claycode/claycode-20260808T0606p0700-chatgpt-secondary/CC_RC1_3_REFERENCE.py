#!/usr/bin/env python3
"""CC-RC1.3 research reference: trusted semantic envelope + observed trace.

This is a bounded research prototype, not production authority code. Its purpose is to
make the CC8 contract executable enough to fuzz core invariants.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import FrozenSet


@dataclass(frozen=True)
class StaticEnvelope:
    object_reads: FrozenSet[str] = frozenset()
    object_writes: FrozenSet[str] = frozenset()
    predicates: FrozenSet[str] = frozenset()
    invariants: FrozenSet[str] = frozenset()
    volatile_inputs: FrozenSet[str] = frozenset()
    effects: FrozenSet[str] = frozenset()
    required_caps: FrozenSet[str] = frozenset()


@dataclass
class ObservedTrace:
    object_reads: set[str] = field(default_factory=set)
    object_writes: set[str] = field(default_factory=set)
    predicates: set[str] = field(default_factory=set)
    invariants: set[str] = field(default_factory=set)
    volatile_inputs: set[str] = field(default_factory=set)
    effects: set[str] = field(default_factory=set)
    required_caps: set[str] = field(default_factory=set)


OP_REGISTRY: dict[str, StaticEnvelope] = {
    "SET_FIELD": StaticEnvelope(
        object_reads=frozenset({"arg:object"}),
        object_writes=frozenset({"arg:object"}),
    ),
    "CREATE_IF_ABSENT": StaticEnvelope(
        predicates=frozenset({"arg:predicate"}),
        invariants=frozenset({"unique:arg:predicate"}),
        object_writes=frozenset({"new:record"}),
    ),
    "ALLOCATE": StaticEnvelope(
        object_reads=frozenset({"pool:arg:pool"}),
        object_writes=frozenset({"pool:arg:pool"}),
        invariants=frozenset({"capacity:arg:pool"}),
    ),
    "WORKSPACE_READ": StaticEnvelope(
        object_reads=frozenset({"channel:arg:channel"}),
        volatile_inputs=frozenset({"workspace_epoch:arg:channel"}),
    ),
    "SEND": StaticEnvelope(
        effects=frozenset({"network:arg:endpoint"}),
        required_caps=frozenset({"cap:network:arg:endpoint"}),
    ),
}


def trace_within_envelope(trace: ObservedTrace, envelope: StaticEnvelope) -> tuple[bool, dict[str, list[str]]]:
    classes = (
        ("object_reads", trace.object_reads, envelope.object_reads),
        ("object_writes", trace.object_writes, envelope.object_writes),
        ("predicates", trace.predicates, envelope.predicates),
        ("invariants", trace.invariants, envelope.invariants),
        ("volatile_inputs", trace.volatile_inputs, envelope.volatile_inputs),
        ("effects", trace.effects, envelope.effects),
        ("required_caps", trace.required_caps, envelope.required_caps),
    )
    escapes = {
        name: sorted(actual - set(bound))
        for name, actual, bound in classes
        if actual - set(bound)
    }
    return not escapes, escapes


def commit_rule(*, envelope_ok: bool, witnesses_fresh: bool,
                caps_valid: bool, effect_intent_durable: bool) -> bool:
    """Research rule only: every hard gate must pass before commit/effect release."""
    return envelope_ok and witnesses_fresh and caps_valid and effect_intent_durable


# Design invariants encoded by this prototype:
# 1. Model output selects op_id/arguments; OP_REGISTRY is trusted runtime metadata.
# 2. Observed dynamic accesses may narrow validation but must be a subset of StaticEnvelope.
# 3. Predicate/invariant/volatile dependencies are first-class; object versions alone are insufficient.
# 4. Unknown/reflection/FFI accesses that cannot be bounded must fail closed or use a broader envelope.
# 5. External effects are not executed during speculative validation; durable intent + capability gate precede release.
