#!/usr/bin/env python3
"""One-shot source repair for exact ClayCode Int division semantics.

The integrated compiler currently performs Int division through Python float in its
reference evaluator. That loses precision for large int64 values while the C backend
uses integer division. This patcher replaces only that evaluator expression in the
integrated compiler and effect pipeline with a float-free truncation-toward-zero helper.

It intentionally does not claim structured divide-by-zero / INT64_MIN/-1 error semantics;
those remain a separate fail-closed WP09 error-model obligation.
"""
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
FILES=[ROOT/'tools/claycode_base_compiler.py',ROOT/'tools/claycode_base_effect_pipeline.py']
OLD='if op == "/": return int(left / right) if isinstance(left, int) and isinstance(right, int) else left / right'
NEW='if op == "/": return _trunc_int_div(left, right) if isinstance(left, int) and isinstance(right, int) else left / right'
HELPER='''\n\ndef _trunc_int_div(left: int, right: int) -> int:\n    if right == 0:\n        raise CompileError("DIVISION_BY_ZERO")\n    quotient = abs(left) // abs(right)\n    return -quotient if (left < 0) != (right < 0) else quotient\n'''
ANCHOR='\ndef eval_expr('

def patch(path:Path)->bool:
    text=path.read_text(encoding='utf-8')
    if NEW in text and 'def _trunc_int_div(' in text:
        return False
    if OLD not in text:
        raise SystemExit(f'EXPECTED_DIVISION_SITE_NOT_FOUND:{path}')
    text=text.replace(OLD,NEW,1)
    if 'def _trunc_int_div(' not in text:
        if ANCHOR not in text: raise SystemExit(f'EVAL_ANCHOR_NOT_FOUND:{path}')
        text=text.replace(ANCHOR,HELPER+ANCHOR,1)
    path.write_text(text,encoding='utf-8')
    return True

def main()->int:
    changed=[str(p.relative_to(ROOT)) for p in FILES if patch(p)]
    print({'changed':changed})
    return 0
if __name__=='__main__':raise SystemExit(main())
