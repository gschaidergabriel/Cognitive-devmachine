from lark import Lark, UnexpectedInput

# Executable probe derived from current grammar.ebnf: deliberately preserves the
# current omissions (no if statement; no union type in type_expr).
OLD = r'''
start: statement+
?statement: record_decl | cycle_decl | rule_decl
record_decl: "record" IDENT [type_params] block
type_params: "<" type_expr ("," type_expr)* ">"
block: "{" (field | action_stmt | statement)* "}"
field: IDENT ":" type_expr ["=" expr] [";"]
action_stmt: [IDENT "="] expr [";"]
cycle_decl: "cycle" "(" [params] ")" block
params: param ("," param)*
param: IDENT [":" type_expr]
rule_decl: "rule" expr
?type_expr: qid [type_params] ["?"] | "Set" "<" type_expr ">" | "Map" "<" type_expr "," type_expr ">" | "Ordered" "<" type_expr ">"
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

# Minimal grammar repair: union types are an explicit type-level construct and
# if is an explicit action statement. No semantic behavior is changed.
NEW = r'''
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

cases = {
    "union_field": 'record NativeCognitionTask { clay_state:AnswerCapsule|CognitiveView|Hyperposition|WorkspaceCandidate }',
    "if_cycle": 'cycle(input,node){ state=state.query(input); if residual.effect { receipt=Needle.execute(residual) } outcome=verify(receipt) }',
    "baseline": 'record Delta<T> { item:T diff:Int logical_time:Epoch cause:Set<Ref> }',
}

for name, grammar in [("old", OLD), ("repaired", NEW)]:
    parser = Lark(grammar, parser="lalr", start="start")
    print(name)
    for case, src in cases.items():
        try:
            parser.parse(src)
            print(f"  {case}: PASS")
        except UnexpectedInput as e:
            print(f"  {case}: FAIL line={e.line} col={e.column} token={getattr(e, 'token', None)}")
