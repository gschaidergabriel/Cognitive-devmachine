from __future__ import annotations
import json, hashlib
from lark import Lark, UnexpectedInput

ORIGINAL = r'''
?start: statement
?statement: module_decl | version_decl | status_decl | parent_decl | import_decl | rule_decl | invariant_decl | record_decl | cycle_decl
module_decl: "module" qid
version_decl: "version" STRING
status_decl: "status" qid
parent_decl: "parent" list
import_decl: "import" IDENT "=" REF
rule_decl: "rule" expr
invariant_decl: "invariant" expr
record_decl: "record" IDENT [type_params] block
cycle_decl: "cycle" "(" [params] ")" block
block: "{" (field | statement | action_stmt)* "}"
field: IDENT ":" type_expr ["=" expr] [";"]
action_stmt: [IDENT "="] expr [";"]
params: param ("," param)*
param: IDENT [":" type_expr]
type_params: "<" type_expr ("," type_expr)* ">"
?type_expr: qid [type_params] ["?"] | "Set" "<" type_expr ">" | "Map" "<" type_expr "," type_expr ">" | "Ordered" "<" type_expr ">"
?expr: primary (operator primary)*
?primary: qid | REF | SIGNED_NUMBER | STRING | BOOLEAN | list | set | call | "(" expr ")"
call: qid "(" [expr ("," expr)*] ")"
list: "[" [expr ("," expr)*] "]"
set: "{" [expr ("," expr)*] "}"
operator: "="|"!="|"=="|"->"|"|"|"+"|"-"|"*"|"/"|"&&"|"||"|"iff"|"requires"|"in"|"subset_of"|"=>"
qid: IDENT ("." IDENT)*
BOOLEAN: "true" | "false"
IDENT: /[A-Za-z_][A-Za-z0-9_-]*/
REF: /@[A-Za-z0-9_\.\/-]+/
%import common.ESCAPED_STRING -> STRING
%import common.SIGNED_NUMBER
%import common.WS
%ignore WS
'''

PATCHED = r'''
?start: statement
?statement: module_decl | version_decl | status_decl | parent_decl | import_decl | rule_decl | invariant_decl | record_decl | cycle_decl
module_decl: "module" qid
version_decl: "version" STRING
status_decl: "status" qid
parent_decl: "parent" list
import_decl: "import" IDENT "=" REF
rule_decl: "rule" expr
invariant_decl: "invariant" expr
record_decl: "record" IDENT [type_params] block
cycle_decl: "cycle" "(" [params] ")" block
block: "{" (field | statement | if_stmt | action_stmt)* "}"
if_stmt: "if" expr block
field: IDENT ":" type_expr ["=" expr] [";"]
action_stmt: [IDENT "="] expr [";"]
params: param ("," param)*
param: IDENT [":" type_expr]
type_params: "<" type_expr ("," type_expr)* ">"
?type_expr: union_type ["?"]
?union_type: type_atom ("|" type_atom)*
?type_atom: qid [type_params] | "Set" "<" type_expr ">" | "Map" "<" type_expr "," type_expr ">" | "Ordered" "<" type_expr ">"
?expr: primary (operator primary)*
?primary: qid | REF | SIGNED_NUMBER | STRING | BOOLEAN | list | set | call | postfix_optional | "(" expr ")"
postfix_optional: qid "?"
call: qid "(" [expr ("," expr)*] ")"
list: "[" [expr ("," expr)*] "]"
set: "{" [expr ("," expr)*] "}"
operator: "="|"!="|"=="|"->"|"|"|"+"|"-"|"*"|"/"|"&&"|"||"|"iff"|"requires"|"returns"|"includes"|"in"|"subset_of"|"=>"|">"|"<"|"or"
qid: IDENT ("." IDENT)*
BOOLEAN: "true" | "false"
IDENT: /[A-Za-z_][A-Za-z0-9_-]*/
REF: /@[A-Za-z0-9_\.\/-]+/
%import common.ESCAPED_STRING -> STRING
%import common.SIGNED_NUMBER
%import common.WS
%ignore WS
'''

CASES = [
    ("control_module", "module claycode.g9.v3"),
    ("control_record", "record Delta<T> {item:T; diff:Int; logical_time:Epoch}"),
    ("cmp_gt", "rule diff>0 => ADD_OR_STRENGTHEN"),
    ("cmp_lt", "rule diff<0 => RETRACT_OR_WEAKEN"),
    ("union_field", "record ProvAtom {source:EvidenceRef;polarity:POS|NEG;role:Symbol}"),
    ("union_generic", "record ProvExpr {op:ATOM|ANY|ALL|DIFF;args:Ordered<ProvExpr|ProvAtom>;semantic_scope:Scope;status:Symbol}"),
    ("returns_operator", "rule delegation returns narrower_or_equal(CapabilityToken)"),
    ("includes_operator", "invariant NativeCognitionTask.forbidden_burden includes [filesystem_search,api_selection]"),
    ("if_stmt", "cycle(input,node){if residual.effect {effect_intent=EffectIntent(residual);receipt=Needle.execute(effect_intent)}}"),
    ("optional_or", "cycle(input,node){outcome=verify(receipt? or residual)}"),
]

def run(grammar: str):
    parser = Lark(grammar, parser="earley", start="start")
    out=[]
    for name, src in CASES:
        try:
            parser.parse(src); out.append({"case":name,"ok":True,"error":None})
        except UnexpectedInput as e:
            out.append({"case":name,"ok":False,"error":f"{type(e).__name__}@{getattr(e,'line',None)}:{getattr(e,'column',None)}"})
    return out

orig = run(ORIGINAL); patched = run(PATCHED)
result = {
    "experiment":"G9 grammar/spec sampled conformance",
    "source_identity":{"spec_path":"research_entity/claycode/g9/CLAYCODE_G9_FUSION_SPEC_V3.clay","spec_git_blob_sha":"1a17bba3c835520baff2ac8fa432749ba2165d8e","grammar_path":"research_entity/claycode/g9/grammar.ebnf","grammar_git_blob_sha":"80028aae6d9d26ac96fa7179dbccc7e467740990"},
    "corpus_sha256":hashlib.sha256(json.dumps(CASES,sort_keys=True).encode()).hexdigest(),
    "original":orig,"patched":patched,
    "original_pass_count":sum(x["ok"] for x in orig),"patched_pass_count":sum(x["ok"] for x in patched),"case_count":len(CASES)
}
print(json.dumps(result, indent=2))
