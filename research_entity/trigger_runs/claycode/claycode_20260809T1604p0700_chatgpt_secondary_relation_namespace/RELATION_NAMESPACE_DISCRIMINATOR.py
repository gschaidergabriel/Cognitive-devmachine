from lark import Lark
import json

GRAMMARS = {
    "at_sigil": r'''
?start: expr
?expr: primary
     | expr REL_OP primary -> binrel
     | REL_OP primary      -> unaryrel
?primary: REF              -> ref
        | IDENT            -> ident
        | "(" expr ")"
REL_OP: /@[A-Za-z0-9_][A-Za-z0-9_-]*/
REF: /@[^\s,\]\)\}]+/
IDENT: /[A-Za-z_][A-Za-z0-9_-]*/
%import common.WS
%ignore WS
''',
    "caret_sigil": r'''
?start: expr
?expr: primary
     | expr REL_OP primary -> binrel
     | REL_OP primary      -> unaryrel
?primary: REF              -> ref
        | IDENT            -> ident
        | "(" expr ")"
REL_OP: /\^[A-Za-z0-9_][A-Za-z0-9_-]*/
REF: /@[^\s,\]\)\}]+/
IDENT: /[A-Za-z_][A-Za-z0-9_-]*/
%import common.WS
%ignore WS
''',
    "generic_call": r'''
?start: expr
?expr: primary
?primary: REF -> ref
        | IDENT -> ident
        | relation_call
        | "(" expr ")"
relation_call: "relation" "(" STRING "," primary ["," primary] ")" -> relation
REF: /@[^\s,\]\)\}]+/
IDENT: /[A-Za-z_][A-Za-z0-9_-]*/
%import common.ESCAPED_STRING -> STRING
%import common.WS
%ignore WS
'''
}

CORPUS = {
    "at_sigil": [
        ("ref_short", "@foo"),
        ("ref_path", "@research_entity/global/x"),
        ("unary_relation", "@depends x"),
        ("binary_relation", "x @depends y"),
        ("binary_rhs_ref", "x @depends @foo"),
        ("unary_rhs_ref", "@depends @foo"),
        ("digit_relation", "x @4B_emits y"),
    ],
    "caret_sigil": [
        ("ref_short", "@foo"),
        ("ref_path", "@research_entity/global/x"),
        ("unary_relation", "^depends x"),
        ("binary_relation", "x ^depends y"),
        ("binary_rhs_ref", "x ^depends @foo"),
        ("unary_rhs_ref", "^depends @foo"),
        ("digit_relation", "x ^4B_emits y"),
    ],
    "generic_call": [
        ("ref_short", "@foo"),
        ("ref_path", "@research_entity/global/x"),
        ("unary_relation", 'relation("depends",x)'),
        ("binary_relation", 'relation("depends",x,y)'),
        ("binary_rhs_ref", 'relation("depends",x,@foo)'),
        ("unary_rhs_ref", 'relation("depends",@foo)'),
        ("digit_relation", 'relation("4B_emits",x,y)'),
    ],
}

MODES = [
    ("lalr_contextual", dict(parser="lalr", lexer="contextual")),
    ("lalr_basic", dict(parser="lalr", lexer="basic")),
    ("earley_dynamic", dict(parser="earley", lexer="dynamic")),
]

def shape(tree):
    return tree.pretty().strip().replace("\n", " | ") if hasattr(tree, "pretty") else str(tree)

out = {"experiment": "relation-namespace-discriminator", "cases": {}}
for candidate, grammar in GRAMMARS.items():
    candidate_results = {}
    for mode, kwargs in MODES:
        parser = Lark(grammar, start="start", **kwargs)
        rows = []
        for name, source in CORPUS[candidate]:
            try:
                parsed = parser.parse(source)
                rows.append({"case": name, "source": source, "ok": True, "shape": shape(parsed)})
            except Exception as exc:
                rows.append({"case": name, "source": source, "ok": False,
                             "error": type(exc).__name__ + ":" + str(exc).splitlines()[0]})
        candidate_results[mode] = {
            "passed": sum(r["ok"] for r in rows),
            "total": len(rows),
            "rows": rows,
        }
    out["cases"][candidate] = candidate_results

out["surface_bytes"] = {
    "declared_infix": len("x depends y".encode()),
    "at_sigil": len("x @depends y".encode()),
    "caret_sigil": len("x ^depends y".encode()),
    "generic_call": len('relation("depends",x,y)'.encode()),
}
out["properties"] = {
    "at_reuses_existing_ref_prefix": True,
    "caret_reuses_existing_ref_prefix": False,
    "generic_call_reuses_existing_ref_prefix": False,
}
print(json.dumps(out, sort_keys=True, indent=2))
