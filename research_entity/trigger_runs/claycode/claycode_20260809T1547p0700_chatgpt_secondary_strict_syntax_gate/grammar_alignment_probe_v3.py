from lark import Lark, UnexpectedInput
import json, hashlib, time

PATCH1 = r'''
start: statement+
?statement: record_decl | cycle_decl | rule_decl
record_decl: "record" IDENT [type_params] block
type_params: "<" type_expr ("," type_expr)* ">"
block: "{" (field | action_stmt | if_stmt | statement)* "}"
field: IDENT ":" type_expr ["=" expr] [";"]
action_stmt: [IDENT "="] expr [";"]
if_stmt: "if" expr block
cycle_decl: "cycle" "(" [params] ")" block
params: param ("," param)*
param: IDENT [":" type_expr]
rule_decl: "rule" expr
?type_expr: union_type
?union_type: atomic_type ("|" atomic_type)*
?atomic_type: qid [type_params] ["?"] | "Set" "<" type_expr ">" | "Map" "<" type_expr "," type_expr ">" | "Ordered" "<" type_expr ">"
?expr: primary (OP primary)*
?primary: qid | NUMBER | STRING | BOOL | list | set | call | "(" expr ")"
call: qid "(" [expr ("," expr)*] ")"
list: "[" [expr ("," expr)*] "]"
set: "{" [expr ("," expr)*] "}"
OP: "="|"!="|"=="|"->"|"|"|"+"|"-"|"*"|"/"|"&&"|"||"|"iff"|"requires"|"in"|"subset_of"|"=>"
qid: IDENT ("." IDENT)*
IDENT: /[A-Za-z_][A-Za-z0-9_-]*/
STRING: /"([^"\\]|\\.)*"/
NUMBER: /-?\d+(\.\d+)?/
BOOL: "true"|"false"
%import common.WS
%ignore WS
'''

# Candidate v2 keeps strict explicit expressions, adds only comparison operators.
# Prose-like source constructs are normalized instead of admitting arbitrary IDENT infix operators.
PATCH2 = r'''
start: statement+
?statement: record_decl | cycle_decl | rule_decl
record_decl: "record" IDENT [type_params] block
type_params: "<" type_expr ("," type_expr)* ">"
block: "{" (field | action_stmt | if_stmt | statement)* "}"
field: IDENT ":" type_expr ["=" expr] [";"]
action_stmt: [IDENT "="] expr [";"]
if_stmt: "if" expr block
cycle_decl: "cycle" "(" [params] ")" block
params: param ("," param)*
param: IDENT [":" type_expr]
rule_decl: "rule" expr
?type_expr: union_type
?union_type: atomic_type ("|" atomic_type)*
?atomic_type: qid [type_params] ["?"] | "Set" "<" type_expr ">" | "Map" "<" type_expr "," type_expr ">" | "Ordered" "<" type_expr ">"
?expr: primary (op primary)*
?primary: qid | NUMBER | STRING | BOOL | list | set | call | "(" expr ")"
call: qid "(" [expr ("," expr)*] ")"
list: "[" [expr ("," expr)*] "]"
set: "{" [expr ("," expr)*] "}"
op: "="|"!="|"=="|"->"|"|"|"+"|"-"|"*"|"/"|"&&"|"||"|"iff"|"requires"|"in"|"subset_of"|"=>"|">="|"<="|">"|"<"
qid: IDENT ("." IDENT)*
IDENT: /[A-Za-z_][A-Za-z0-9_-]*/
STRING: /"([^"\\]|\\.)*"/
NUMBER: /-?\d+(\.\d+)?/
BOOL: "true"|"false"
%import common.WS
%ignore WS
'''

RAW_CASES = {
    "gt_compare": 'rule diff>0 => ADD_OR_STRENGTHEN',
    "ge_compare": 'rule valid_generation requires count(distinct(classes))>=2 && count(executable)>=1',
    "returns_relation": 'rule delegation returns narrower_or_equal(CapabilityToken)',
    "owns_list": 'rule Needle.owns [tool_schema,api_wire,shell_wire]',
    "digit_identifier": 'rule 4B_emits EffectIntent',
    "lifecycle_relation": 'rule external_effect lifecycle=[REQUESTED,AUTHORIZED,EXECUTED,DONE]',
    "prose_chain": 'rule Claude_only consumes latest stack + writes task receipts',
    "includes_relation": 'rule NativeCognitionTask.forbidden_burden includes [filesystem_search,api_selection]',
    "optional_or": 'cycle(input,node){ outcome=verify(receipt? or residual) }',
    "union_if_baseline": 'record X { x:A|B } cycle(input,node){ if node.organ==CHATGPT { outcome=verify(node) } }',
}

NORMALIZED_CASES = {
    "gt_compare": 'rule diff>0 => ADD_OR_STRENGTHEN',
    "ge_compare": 'rule valid_generation requires count(distinct(classes))>=2 && count(executable)>=1',
    "returns_relation": 'rule delegation -> narrower_or_equal(CapabilityToken)',
    "owns_list": 'rule Needle.owns = [tool_schema,api_wire,shell_wire]',
    "digit_identifier": 'rule model4B_emits -> EffectIntent',
    "lifecycle_relation": 'rule external_effect.lifecycle = [REQUESTED,AUTHORIZED,EXECUTED,DONE]',
    "prose_chain": 'rule Claude_only.consumes = latest_stack rule Claude_only.writes = task_receipts',
    "includes_relation": 'rule includes(NativeCognitionTask.forbidden_burden,[filesystem_search,api_selection])',
    "optional_or": 'cycle(input,node){ outcome=verify(coalesce(receipt,residual)) }',
    "union_if_baseline": RAW_CASES["union_if_baseline"],
}

def attempt(parser, src):
    try:
        parser.parse(src)
        return {"status":"PASS"}
    except UnexpectedInput as e:
        return {
            "status":"FAIL",
            "line": e.line,
            "column": e.column,
            "token": str(getattr(e, 'token', '')),
            "expected": sorted(getattr(e, 'expected', []) or []),
        }

p1 = Lark(PATCH1, parser='lalr', start='start')
p2 = Lark(PATCH2, parser='lalr', start='start')
results = {}
for name, raw in RAW_CASES.items():
    results[name] = {
        "raw_patch1": attempt(p1, raw),
        "normalized_patch2": attempt(p2, NORMALIZED_CASES[name]),
        "raw_sha256": hashlib.sha256(raw.encode()).hexdigest(),
        "normalized_sha256": hashlib.sha256(NORMALIZED_CASES[name].encode()).hexdigest(),
    }

summary = {
    "raw_patch1_pass": sum(v["raw_patch1"]["status"]=="PASS" for v in results.values()),
    "raw_patch1_fail": sum(v["raw_patch1"]["status"]=="FAIL" for v in results.values()),
    "normalized_patch2_pass": sum(v["normalized_patch2"]["status"]=="PASS" for v in results.values()),
    "normalized_patch2_fail": sum(v["normalized_patch2"]["status"]=="FAIL" for v in results.values()),
}
out = {"probe":"ClayCode G9 full-corpus representative grammar gate v2", "summary":summary, "results":results}
print(json.dumps(out, indent=2))
