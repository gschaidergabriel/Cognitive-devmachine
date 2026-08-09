from lark import Lark
from hashlib import sha256
import json

BASE = r'''
start: statement+
?statement: record_decl | rule_decl | cycle_decl
record_decl: "record" NAME block
rule_decl: "rule" expr
cycle_decl: "cycle" "(" [params] ")" block
block: "{" (field | action_stmt)* "}"
field: NAME ":" type_expr ["=" expr] ";"?
action_stmt: [NAME "="] expr ";"?
params: param ("," param)*
param: NAME [":" type_expr]
?type_expr: type_atom ("|" type_atom)*
?type_atom: qid [type_params] ["?"] | "Set" "<" type_expr ">" | "Map" "<" type_expr "," type_expr ">" | "Ordered" "<" type_expr ">"
type_params: "<" type_expr ("," type_expr)* ">"
?expr: primary (operator primary)*
?primary: qid | ref | SIGNED_NUMBER | ESCAPED_STRING | BOOL | list | set | call | "(" expr ")"
call: qid "(" [expr ("," expr)*] ")"
list: "[" [expr ("," expr)*] "]"
set: "{" [expr ("," expr)*] "}"
ref: "@" /[^\s,;\]\}\)]+/
qid: NAME ("." NAME)*
operator: "="|"!="|"=="|"->"|"|"|"+"|"-"|"*"|"/"|"&&"|"||"|"iff"|"requires"|"in"|"subset_of"|"=>"
BOOL: "true"|"false"
NAME: /[A-Za-z_][A-Za-z0-9_-]*/
%import common.SIGNED_NUMBER
%import common.ESCAPED_STRING
%import common.WS
%ignore WS
%ignore /\/\/[^\n]*/
'''

PATCHED = BASE.replace('block: "{" (field | action_stmt)* "}"','block: "{" (field | if_stmt | action_stmt)* "}"\nif_stmt: "if" expr block').replace('operator: "="|"!="|"=="|"->"|"|"|"+"|"-"|"*"|"/"|"&&"|"||"|"iff"|"requires"|"in"|"subset_of"|"=>"','operator: ">="|"<="|">"|"<"|"="|"!="|"=="|"->"|"|"|"+"|"-"|"*"|"/"|"&&"|"||"|"iff"|"requires"|"in"|"subset_of"|"=>"')

CURRENT_SPEC_COUNTEREXAMPLE = r'''
rule diff>0 => ADD_OR_STRENGTHEN
rule diff<0 => RETRACT_OR_WEAKEN
cycle(input,node){
  if residual.effect {receipt=Needle.execute(effect_intent)}
}
'''

LOOP_CONTRACT = r'''
record LoopDynamicsReadout {
  loop_id:Ref;
  timescale:Duration;
  state_delta_norm:Float;
  unresolved_pressure:Float;
  recurrence_count:Int;
  recurrence_budget:Int;
  convergence_rate:Float;
  marginal_utility_next:Float;
  stagnation:Bool;
  overthinking:Bool;
  evidence:Set<EvidenceRef>;
  rollback:RecoveryRef?;
}
record RecurrenceDecision {
  action:CONTINUE|HALT|ROUTE|ESCALATE;
  reason:Symbol;
  readout:LoopDynamicsReadout;
  capability:CapabilityRef?;
}
rule LoopDynamicsReadout != execution_authority
rule RecurrenceDecision != execution_authority
rule action=CONTINUE requires marginal_utility_next>0
'''

def parse(grammar, src):
    return Lark(grammar, parser='lalr', start='start').parse(src)

results = {"tests": []}
for name, src in [("current_g9_counterexample", CURRENT_SPEC_COUNTEREXAMPLE), ("loop_contract", LOOP_CONTRACT)]:
    for grammar_name, grammar in [("baseline", BASE), ("patched", PATCHED)]:
        try:
            tree = parse(grammar, src); ok = True; err = None; tree_hash = sha256(tree.pretty().encode()).hexdigest()
        except Exception as e:
            ok = False; err = f"{type(e).__name__}: {e}"[:1200]; tree_hash = None
        results["tests"].append({"fixture": name, "grammar": grammar_name, "parse_ok": ok, "error": err, "tree_hash": tree_hash})

def semantic_form(obj):
    out = dict(obj)
    if "permits" in out: out["permits"] = sorted(set(out["permits"]))
    return out

def h(obj):
    return sha256(json.dumps(obj, sort_keys=True, separators=(",", ":")).encode()).hexdigest()

cap_a = {"id":"cap-1","permits":["write","read","write"],"ordered_steps":["reserve","commit"]}
cap_b = {"id":"cap-1","permits":["read","write"],"ordered_steps":["reserve","commit"]}
cap_c = {"id":"cap-1","permits":["read","write"],"ordered_steps":["commit","reserve"]}
results["identity"] = {"a_semantic_hash":h(semantic_form(cap_a)),"b_semantic_hash":h(semantic_form(cap_b)),"c_semantic_hash":h(semantic_form(cap_c)),"a_contract_hash":h(cap_a),"b_contract_hash":h(cap_b),"c_contract_hash":h(cap_c),"set_order_dup_semantically_equal":h(semantic_form(cap_a))==h(semantic_form(cap_b)),"contract_instances_distinct":h(cap_a)!=h(cap_b),"ordered_steps_semantically_distinct":h(semantic_form(cap_b))!=h(semantic_form(cap_c))}

VALID_TOKEN={"id":"cap-1","permits":{"commit"},"issuer":"research-entity","valid":True,"revoked":False}
def can_commit(intent, token):
    return bool(token and token.get("valid") and not token.get("revoked") and "commit" in token.get("permits", set()) and token.get("issuer")=="research-entity")
results["authority"]={"textual_name_only_rejected":not can_commit({"capability":"cap-1"},None),"valid_token_accepted":can_commit({"capability":"cap-1"},VALID_TOKEN),"revoked_token_rejected":not can_commit({"capability":"cap-1"},{**VALID_TOKEN,"revoked":True}),"forged_issuer_rejected":not can_commit({"capability":"cap-1"},{**VALID_TOKEN,"issuer":"model-text"})}
results["source_hashes"]={"current_spec_counterexample":sha256(CURRENT_SPEC_COUNTEREXAMPLE.encode()).hexdigest(),"loop_contract":sha256(LOOP_CONTRACT.encode()).hexdigest(),"baseline_grammar":sha256(BASE.encode()).hexdigest(),"patched_grammar":sha256(PATCHED.encode()).hexdigest()}
print(json.dumps(results,indent=2,sort_keys=True))
