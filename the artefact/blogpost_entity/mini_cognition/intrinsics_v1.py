#!/usr/bin/env python3
"""Canonical ClayCode Cognition v1 intrinsic vocabulary used by corpus/eval validators.

This file is validation policy, not model truth and not effect authority.  The model may
only emit calls from this set in generated ClayCode cognition.  Runtime effect execution
still requires the separate grammar -> type -> schema -> authority -> generation gates.
"""

INTRINSIC_ARITY = {
    # configuration / envelope
    "cfg": 1,
    "cog_new": 0,
    "self_bind": 3,
    "role_bind": 2,
    "goal_bind": 2,
    "personality_bind": 2,

    # GRF
    "grf_observe": 4,
    "grf_infer": 3,
    "grf_generate": 3,
    "grf_counter": 3,
    "grf_intervene": 3,
    "grf_emergent": 3,
    "grf_verify": 4,

    # Hyperposition
    "hyper_new": 2,
    "hyper_alt": 3,
    "hyper_discriminator": 2,
    "hyper_invariant": 2,
    "collapse_guard": 2,
    "collapse_exact": 3,

    # Omega structured action candidate
    "omega_new": 2,
    "omega_bind": 3,
    "omega_arg": 4,
    "omega_schema": 2,
    "omega_authority": 2,
    "omega_generation": 2,
    "omega_validate": 2,
    "omega_reject": 2,
    "omega_commit_candidate": 2,

    # self / architecture / typed state-control notes
    "self_state": 4,
    "self_scalar": 4,
    "self_kind": 2,
    "arch_bind": 3,
    "authority_bind": 3,
    "authority_deny": 3,
    "state_note": 4,
    "unknown_preserve": 3,
    "provenance": 4,
    "focus_set": 2,
    "policy_select": 2,
    "recovery_state": 2,
}

ALLOWED_INTRINSICS = frozenset(INTRINSIC_ARITY)
