#!/usr/bin/env python3
"""Regression-only fence for dead/nested ClayCode semantic-call credit.

The shared claycode_syntax_v1 scanner is the single syntax authority. This test
must not grow a second parser; it only proves evaluation keeps top-level semantic
credit separate from nested/dead control flow while cfg(...) expressions remain
visible inside canonical outer calls.
"""
from claycode_syntax_v1 import call_set
from eval_outputs_v1 import exact_omega_ok, marker_present

PREFIX = "module clay.cog.turn\nfn think(i:Map)->Map {\n"


def wrap(body):
    return PREFIX + body + "\n}"


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def main():
    marker = 'hyper_alt(hp,"A",0.5)'
    top = wrap(marker + "\nreturn c")
    nested = wrap("if false {\n" + marker + "\n}\nreturn c")
    quoted = wrap('state_note(c,"hyper_alt(hp,\\"A\\",0.5)")\nreturn c')
    cfg_nested = wrap('self_bind(c,cfg("entity.id"),cfg("entity.continuity"))\nreturn c')

    require(marker_present(top, marker), "top-level semantic call lost")
    require(not marker_present(nested, marker), "nested/dead semantic call received credit")
    require(not marker_present(quoted, marker), "quoted semantic lookalike received credit")
    require(marker_present(cfg_nested, 'cfg("entity.id")'), "nested cfg expression should remain visible")
    require(marker in call_set(top, depth=1), "top-level brace depth not recorded")
    require(marker in call_set(nested, depth=2), "nested brace depth not recorded")
    require(marker not in call_set(nested, depth=1), "nested call leaked into top-level call set")

    expected = {
        "operation": "state.noop",
        "args": [{"name": "reason", "value": "depth-regression", "type": "String"}],
        "schema": "clay.effect/state.noop@1",
        "authority_expr": 'cfg("architecture.effect_authority")',
        "generation_expr": 'cfg("state.generation")',
        "validators": ["grammar", "types", "schema", "authority", "generation"],
        "commit_count": 1,
    }
    omega_lines = [
        'omega_bind(w,"operation","state.noop")',
        'omega_arg(w,"reason","depth-regression","String")',
        'omega_schema(w,"clay.effect/state.noop@1")',
        'omega_authority(w,cfg("architecture.effect_authority"))',
        'omega_generation(w,cfg("state.generation"))',
        'omega_validate(w,"grammar")',
        'omega_validate(w,"types")',
        'omega_validate(w,"schema")',
        'omega_validate(w,"authority")',
        'omega_validate(w,"generation")',
        'omega_commit_candidate(c,w)',
        'return c',
    ]
    good = wrap("\n".join(omega_lines))
    nested_omega = wrap("if false {\n" + "\n".join(omega_lines[:-1]) + "\n}\nreturn c")
    require(exact_omega_ok(good, expected), "top-level exact omega vector should pass")
    require(not exact_omega_ok(nested_omega, expected), "nested/dead omega vector received exact-vector credit")

    print({"cases": 9, "ok": True, "syntax_authority": "claycode_syntax_v1", "role": "regression_only"})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
