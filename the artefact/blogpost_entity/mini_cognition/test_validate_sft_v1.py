#!/usr/bin/env python3
import importlib.util
from pathlib import Path

HERE=Path(__file__).resolve().parent
SPEC=importlib.util.spec_from_file_location("validate_sft_v1",HERE/"validate_sft_v1.py")
mod=importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(mod)


def base(extra):
    return (
        'module clay.cog.turn\n'
        'fn think(i:Map)->Map {\n'
        '  let c = cog_new()\n'
        '  self_bind(c,cfg("entity.id"),cfg("entity.continuity"))\n'
        '  role_bind(c,cfg("application.role"))\n'
        '  goal_bind(c,cfg("application.goal"))\n'
        '  personality_bind(c,cfg("application.personality"))\n'
        + extra +
        '  return c\n'
        '}'
    )


def omega(var="w9",gate_var=None,comment_gate=False,reject=False):
    gv=gate_var or var
    lines=[
        f'  let {var} = omega_new(c,"candidate")',
        f'  omega_bind({var},"operation","db.lookup")',
        f'  omega_arg({var},"table","events","Identifier")',
        f'  omega_schema({var},"tool.db.lookup/v1")',
        f'  omega_authority({var},cfg("architecture.effect_authority"))',
        f'  omega_generation({var},cfg("state.generation"))',
    ]
    for g in mod.OMEGA_GATES:
        prefix='// ' if comment_gate and g=='generation' else ''
        lines.append(f'  {prefix}omega_validate({gv},"{g}")')
    if reject:
        lines.append(f'  omega_reject({var},"forced")')
    lines.append(f'  omega_commit_candidate(c,{var})')
    return "\n".join(lines)+"\n"


def require_ok(name,code):
    err=mod.validate_code(code)
    assert not err,(name,err)


def require_bad(name,code,needle):
    err=mod.validate_code(code)
    assert any(needle in x for x in err),(name,needle,err)


def main():
    require_ok("renamed_omega_same_binding",base(omega("w9")))
    require_bad("gates_bound_to_wrong_omega",base(omega("w9","w0")),"omega_missing_gate:w9:grammar")
    require_bad("comment_smuggling",base(omega("w9",comment_gate=True)),"comment_surface")
    require_bad("reject_then_commit",base(omega("w9",reject=True)),"reject_and_commit:w9")
    require_bad("unknown_statement",base('  this is prose\n'),"unknown_statement")
    require_bad("unknown_call",base('  secret_execute(c)\n'),"unknown_call")
    print("6 validator regressions PASS")

if __name__=="__main__": main()
