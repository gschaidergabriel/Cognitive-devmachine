import hashlib, json
from lark import Lark

CASES = [
    ("relop_gt", "rule diff>0 => ADD_OR_STRENGTHEN"),
    ("relop_lt", "rule diff<0 => RETRACT_OR_WEAKEN"),
    ("pseudo_infix_never_implies", "rule Delta never_implies epistemic_upgrade"),
    ("pseudo_infix_returns", "rule delegation returns narrower_or_equal(CapabilityToken)"),
    ("pseudo_infix_is_explanation", "rule ProvExpr is_explanation_of_derivation"),
    ("conditional_if", "if residual.effect {effect_intent=EffectIntent(residual);receipt=Needle.execute(effect_intent)}"),
    ("comment", "// G9 V3: XENO control semantics + Clay/UnifiedDB/ClayGraph native cognition + dialect ecology."),
    ("supported_requires", "rule extraction requires verified_equivalence + target_cost_model"),
    ("supported_invariant", "invariant hidden_provider_cot_not_persisted"),
]

BASELINE = r'''start: rule_stmt | invariant_stmt | action_stmt
rule_stmt: "rule" expr
invariant_stmt: "invariant" expr
?action_stmt: [IDENT "="] expr [";"]
?expr: primary (OP primary)*
?primary: qid | NUMBER | call | "(" expr ")"
call: qid "(" [expr ("," expr)*] ")"
qid: IDENT ("." IDENT)*
OP: "="|"!="|"=="|"->"|"|"|"+"|"-"|"*"|"/"|"&&"|"||"|"iff"|"requires"|"in"|"subset_of"|"=>"
IDENT: /[A-Za-z_][A-Za-z0-9_-]*/
NUMBER: /-?[0-9]+(\.[0-9]+)?/
%import common.WS
%ignore WS
'''

CANDIDATE = r'''start: rule_stmt | invariant_stmt | if_stmt | comment
rule_stmt: "rule" rule_expr
invariant_stmt: "invariant" rule_expr
if_stmt: "if" runtime_expr block ["else" block]
block: "{" action_stmt* "}"
action_stmt: [IDENT "="] runtime_expr [";"]
comment: COMMENT
?rule_expr: rule_atom ((rule_op rule_atom)|legacy_postfix)*
?rule_atom: runtime_expr
?runtime_expr: implication
?implication: logic_or ("=>" implication)?
?logic_or: logic_and ("||" logic_and)*
?logic_and: comparison ("&&" comparison)*
?comparison: additive [COMP_OP additive]
?additive: multiplicative (("+"|"-") multiplicative)*
?multiplicative: primary (("*"|"/") primary)*
?primary: qid | NUMBER | call | "(" runtime_expr ")"
call: qid "(" [runtime_expr ("," runtime_expr)*] ")"
qid: IDENT ("." IDENT)*
rule_op: "="|"!="|"=="|"->"|"|"|"iff"|"requires"|"in"|"subset_of"|"=>"|legacy_pred
legacy_pred: "never_implies"|"returns"|"cannot_authorize"|"may_reference"|"includes"|"consumes"|"uses"|"makes"|"loads"|"owns"
legacy_postfix: "is_explanation_of_derivation"
COMP_OP: "=="|"!="|"<="|">="|"<"|">"
COMMENT: /\/\/[^\n]*/
IDENT: /[A-Za-z_][A-Za-z0-9_-]*/
NUMBER: /-?[0-9]+(\.[0-9]+)?/
%import common.WS
%ignore WS
'''

base = Lark(BASELINE, parser='lalr', maybe_placeholders=False)
cand = Lark(CANDIDATE, parser='lalr', maybe_placeholders=False)

def run(parser, src):
    try:
        tree = parser.parse(src)
        return True, tree.pretty().strip()
    except Exception as e:
        return False, f"{type(e).__name__}: {str(e).splitlines()[0]}"

rows=[]
for name,src in CASES:
    b_ok,b_detail=run(base,src); c_ok,c_detail=run(cand,src)
    rows.append({"case":name,"source":src,"baseline_ok":b_ok,"candidate_ok":c_ok,"baseline_detail":b_detail,"candidate_detail":c_detail})

out={"experiment":"CC-G9-PARSER-DELTA-20260809","experiment_version":"0.1","source_spec_blob_sha":"1a17bba3c835520baff2ac8fa432749ba2165d8e","grammar_blob_sha":"ec2f17077333955cfdabe6c64868d597e7e734e3","corpus_sha256":hashlib.sha256("\n".join(s for _,s in CASES).encode()).hexdigest(),"baseline_pass":sum(r['baseline_ok'] for r in rows),"baseline_fail":sum(not r['baseline_ok'] for r in rows),"candidate_pass":sum(r['candidate_ok'] for r in rows),"candidate_fail":sum(not r['candidate_ok'] for r in rows),"rows":rows,"limits":["fragment corpus, not whole-file parse","candidate grammar is experimental and unpromoted","no target Ubuntu compiler/runtime execution yet","no E2B capability exposed in this ChatGPT session; local Python/Lark fallback used"]}
print(json.dumps(out,indent=2,ensure_ascii=False))
