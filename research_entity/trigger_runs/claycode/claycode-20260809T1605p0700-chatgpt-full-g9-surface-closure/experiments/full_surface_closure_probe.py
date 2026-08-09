from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path
from lark import Lark, UnexpectedInput

BASE = r'''
?start: statement
?statement: module_decl | version_decl | status_decl | parent_decl | import_decl | interface_decl | dialect_decl | law_decl | rule_decl | invariant_decl | class_decl | record_decl | tensor_decl | codec_decl | surface_decl | metric_decl | hash_decl | needle_decl | cycle_decl
module_decl: "module" qid
version_decl: "version" STRING
status_decl: "status" qid
parent_decl: "parent" list
import_decl: "import" IDENT "=" REF
interface_decl: "interface" IDENT block
dialect_decl: "dialect" IDENT block
law_decl: "law" expr
rule_decl: "rule" expr
invariant_decl: "invariant" expr
class_decl: ("class"|"type") IDENT [type_params] "=" expr
record_decl: "record" IDENT [type_params] block
tensor_decl: "tensor" IDENT "=" list
codec_decl: "codec" IDENT "=" IDENT [IDENT]
surface_decl: "surface" IDENT
metric_decl: "metric" IDENT "=" expr
hash_decl: "hash" IDENT "(" IDENT ")" "=" expr
needle_decl: "needle" IDENT "(" [params] ")" "->" type_expr
cycle_decl: "cycle" "(" [params] ")" block
block: "{" (field | statement | action_stmt)* "}"
field: IDENT ":" type_expr ["=" expr] [";"]
action_stmt: [IDENT "="] expr [";"]
params: param ("," param)*
param: IDENT [":" type_expr]
type_params: "<" type_expr ("," type_expr)* ">"
?type_expr: type_atom ("|" type_atom)*
?type_atom: qid [type_params] ["?"] | "Set" "<" type_expr ">" | "Map" "<" type_expr "," type_expr ">" | "Ordered" "<" type_expr ">"
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

CANDIDATE = BASE.replace(
    'block: "{" (field | statement | action_stmt)* "}"',
    'block: "{" (field | statement | if_stmt | action_stmt)* "}"\nif_stmt: "if" expr block'
).replace(
    '?primary: qid | REF | SIGNED_NUMBER | STRING | BOOLEAN | list | set | call | "(" expr ")"',
    '?primary: qid | REF | SIGNED_NUMBER | STRING | BOOLEAN | list | set | call | postfix_optional | "(" expr ")"\npostfix_optional: qid "?"'
).replace(
    'operator: "="|"!="|"=="|"->"|"|"|"+"|"-"|"*"|"/"|"&&"|"||"|"iff"|"requires"|"in"|"subset_of"|"=>"',
    'operator: ">="|"<="|">"|"<"|"="|"!="|"=="|"->"|"|"|"+"|"-"|"*"|"/"|"&&"|"||"|"or"|"iff"|"requires"|"in"|"subset_of"|"=>"'
)

NORMALIZATIONS = {
    'rule Delta never_implies epistemic_upgrade':'rule never_implies(Delta,epistemic_upgrade)',
    'rule prompt_read never_requires global_recompute':'rule never_requires(prompt_read,global_recompute)',
    'rule ProvExpr is_explanation_of_derivation':'rule is_explanation_of_derivation(ProvExpr)',
    'rule effect.Intent may_reference capability_id':'rule may_reference(effect.Intent,capability_id)',
    'rule textual_capability_name never_confers authority':'rule never_confers(textual_capability_name,authority)',
    'rule delegation returns narrower_or_equal(CapabilityToken)':'rule returns(delegation,narrower_or_equal(CapabilityToken))',
    'rule task_context loads minimal_dialect_closure':'rule loads(task_context,minimal_dialect_closure)',
    'rule graph.derived_relation cannot_authorize effect':'rule cannot_authorize(graph.derived_relation,effect)',
    'rule graph.selection_receipt distinct_from graph.provenance_receipt':'rule distinct_from(graph.selection_receipt,graph.provenance_receipt)',
    'rule graph.hyperrelation roles_are_typed':'rule roles_are_typed(graph.hyperrelation)',
    'rule 4B_emits EffectIntent':'rule model4B.emits(EffectIntent)',
    'rule Needle.lowers EffectIntent -> concrete_adapter_plan':'rule Needle.lowers(EffectIntent) -> concrete_adapter_plan',
    'rule Needle.owns [tool_schema,api_wire,shell_wire,device_wire,retry,serialization,auth_transport]':'rule Needle.owns([tool_schema,api_wire,shell_wire,device_wire,retry,serialization,auth_transport])',
    'rule 4B_need_not_learn Needle.owns':'rule model4B.need_not_learn(Needle.owns)',
    'rule external_effect lifecycle=[REQUESTED,AUTHORIZED,CLAIMED,EXECUTED,VERIFIED,DONE]':'rule external_effect.lifecycle=[REQUESTED,AUTHORIZED,CLAIMED,EXECUTED,VERIFIED,DONE]',
    'rule dynamic_ids_time_hash_runtime outside_stable_prefix':'rule outside_stable_prefix(dynamic_ids_time_hash_runtime)',
    'rule Claude_only consumes latest stack + writes task receipts':'rule consumes(Claude_only,latest_stack) + writes(Claude_only,task_receipts)',
    'rule successful_motif must_be_preserved_unless_counterevidence':'rule must_be_preserved_unless_counterevidence(successful_motif)',
    'rule NativeCognitionTask.forbidden_burden includes [filesystem_search,api_selection,json_arguments,capability_enumeration_if_precomputed,goal_list_recall]':'rule includes(NativeCognitionTask.forbidden_burden,[filesystem_search,api_selection,json_arguments,capability_enumeration_if_precomputed,goal_list_recall])',
    'rule training_data personalizes_for_Andreas_when_FRANK_target && preserves_general_transfer_variants':'rule personalizes_for_Andreas_when_FRANK_target(training_data) && preserves_general_transfer_variants(training_data)',
}

def chunks(source: str) -> list[str]:
    out, buf, depth = [], [], 0
    for raw in source.splitlines():
        line = raw.strip()
        if not line or line.startswith('//'):
            continue
        buf.append(line)
        depth += line.count('{') - line.count('}')
        if depth == 0:
            out.append(' '.join(buf)); buf=[]
    if buf or depth:
        raise ValueError('unbalanced source')
    return out

def parse_all(grammar: str, source: str):
    parser=Lark(grammar, parser='earley', start='start')
    result=[]
    for i, s in enumerate(chunks(source), 1):
        try:
            parser.parse(s); result.append({'index':i,'ok':True})
        except UnexpectedInput as e:
            result.append({'index':i,'ok':False,'error':f'{type(e).__name__}@{getattr(e,"line",None)}:{getattr(e,"column",None)}','source':s})
    return result

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--source', default='research_entity/claycode/g9/CLAYCODE_G9_FUSION_SPEC_V3.clay')
    ap.add_argument('--out')
    args=ap.parse_args()
    source=Path(args.source).read_text(encoding='utf-8')
    normalized=source
    for old,new in NORMALIZATIONS.items():
        if old not in normalized: raise RuntimeError(f'missing expected current form: {old}')
        normalized=normalized.replace(old,new)
    baseline=parse_all(BASE,source)
    candidate=parse_all(CANDIDATE,normalized)
    result={
        'experiment':'whole-current-G9 top-level surface closure proxy',
        'source_path':args.source,
        'source_sha256':hashlib.sha256(source.encode()).hexdigest(),
        'chunk_count':len(baseline),
        'baseline_pass':sum(x['ok'] for x in baseline),
        'baseline_fail':sum(not x['ok'] for x in baseline),
        'candidate_pass':sum(x['ok'] for x in candidate),
        'candidate_fail':sum(not x['ok'] for x in candidate),
        'normalization_count':len(NORMALIZATIONS),
        'candidate_core_grammar_additions':['if_stmt','postfix_optional_value','comparisons > < >= <=','or'],
        'baseline_failures':[x for x in baseline if not x['ok']],
        'candidate_failures':[x for x in candidate if not x['ok']],
        'evidence_boundary':'Lark executable proxy over complete current G9 V3 top-level corpus; not production parser, typed AST oracle, roundtrip proof, or N/S/D winner selection.'
    }
    text=json.dumps(result,indent=2,ensure_ascii=False)
    if args.out: Path(args.out).write_text(text+'\n',encoding='utf-8')
    print(text)

if __name__=='__main__': main()
