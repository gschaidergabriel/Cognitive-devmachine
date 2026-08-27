import re, json, hashlib, random, string

STD_IDENT = re.compile(r'^[A-Za-z_][A-Za-z0-9_.-]*$')
DIGIT_SEM = re.compile(r'^(?=[A-Za-z0-9_.-]*[A-Za-z_])[0-9][A-Za-z0-9_.-]*$')
NUMBER = re.compile(r'^-?(?:\d+(?:\.\d*)?|\.\d+)$')

INFIX = {
    "never_implies", "includes", "may_reference", "returns",
    "uses", "requires", "subset_of", "in", "iff"
}
PREFIX = {"4B_emits"}
PROPERTY_KEYS = {"lifecycle"}

def is_symbol(s):
    return bool(STD_IDENT.match(s) or DIGIT_SEM.match(s))

def atom(s):
    s = s.strip()
    if NUMBER.match(s):
        return ("number", s)
    if is_symbol(s):
        return ("symbol", s)
    if s.startswith("[") and s.endswith("]"):
        inner = s[1:-1].strip()
        items = [] if not inner else [x.strip() for x in inner.split(",")]
        if all(is_symbol(x) or NUMBER.match(x) for x in items):
            return ("list", tuple(("number", x) if NUMBER.match(x) else ("symbol", x) for x in items))
    m = re.match(r'^([A-Za-z_][A-Za-z0-9_.-]*)\((.*)\)$', s)
    if m:
        fn, inner = m.group(1), m.group(2).strip()
        args = [] if not inner else [x.strip() for x in inner.split(",")]
        if all(is_symbol(x) or NUMBER.match(x) for x in args):
            return ("call", fn, tuple(("number", x) if NUMBER.match(x) else ("symbol", x) for x in args))
    return None

def parse_strict(src):
    s = src.strip()
    if s.startswith("rule "):
        s = s[5:].strip()
    elif s.startswith("invariant "):
        s = s[10:].strip()

    m = re.match(r'^(\S+)\s+([A-Za-z_][A-Za-z0-9_-]*)\s*=\s*(.+)$', s)
    if m and is_symbol(m.group(1)) and m.group(2) in PROPERTY_KEYS:
        rhs = atom(m.group(3))
        if rhs:
            return ("property", ("symbol", m.group(1)), m.group(2), rhs)

    m = re.match(r'^(\S+)\s+(.+)$', s)
    if m and m.group(1) in PREFIX:
        rhs = atom(m.group(2))
        if rhs:
            return ("prefix_rel", m.group(1), rhs)

    m = re.match(r'^(\S+)\s+([A-Za-z_][A-Za-z0-9_-]*)\s+(.+)$', s)
    if m:
        lhs, rel, rhs = atom(m.group(1)), m.group(2), atom(m.group(3))
        if lhs and rhs and rel in INFIX:
            return ("infix_rel", lhs, rel, rhs)

    m = re.match(r'^(\S+)\s*(>=|<=|!=|==|>|<)\s*(\S+)\s*(=>|->)\s*(\S+)$', s)
    if m and atom(m.group(1)) and atom(m.group(3)) and atom(m.group(5)):
        return ("op_chain", atom(m.group(1)), m.group(2), atom(m.group(3)), m.group(4), atom(m.group(5)))

    m = re.match(r'^(\S+)\s*(!=|==)\s*(\S+)$', s)
    if m and atom(m.group(1)) and atom(m.group(3)):
        return ("binary_op", atom(m.group(1)), m.group(2), atom(m.group(3)))
    return None

def parse_naive_relation(src):
    s = src.strip()
    if s.startswith("rule "):
        s = s[5:].strip()
    elif s.startswith("invariant "):
        s = s[10:].strip()
    m = re.match(r'^(\S+)\s+([A-Za-z_][A-Za-z0-9_-]*)\s+(.+)$', s)
    if m and atom(m.group(1)) and atom(m.group(3)):
        return ("infix_rel", atom(m.group(1)), m.group(2), atom(m.group(3)))
    return None

def h(ast):
    payload = json.dumps(ast, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(payload.encode()).hexdigest()

valid = {
    "never_implies": "rule Delta never_implies epistemic_upgrade",
    "may_reference": "rule effect.Intent may_reference capability_id",
    "includes": "rule NativeCognitionTask.forbidden_burden includes [filesystem_search,api_selection,json_arguments]",
    "returns": "rule delegation returns narrower_or_equal",
    "digit_prefix": "rule 4B_emits EffectIntent",
    "property": "rule external_effect lifecycle=[REQUESTED,AUTHORIZED,CLAIMED,EXECUTED,VERIFIED,DONE]",
    "comparison": "rule diff>0 => ADD_OR_STRENGTHEN",
    "inequality": "invariant model_output!=authority"
}

valid_asts = {k: parse_strict(v) for k, v in valid.items()}

random.seed(20260809)
unknowns = []
while len(unknowns) < 50000:
    n = random.randint(4, 18)
    rel = "".join(random.choice(string.ascii_lowercase + "_") for _ in range(n)).strip("_") or "xrel"
    if rel not in INFIX and rel not in PROPERTY_KEYS and rel not in PREFIX:
        unknowns.append(rel)

naive_unknown_accepts = 0
strict_unknown_accepts = 0
for rel in unknowns:
    src = f"rule Delta {rel} epistemic_upgrade"
    naive_unknown_accepts += parse_naive_relation(src) is not None
    strict_unknown_accepts += parse_strict(src) is not None

digit_semantic = []
pure_numbers = []
for _ in range(20000):
    d = str(random.randint(0, 9999))
    suffix = random.choice(string.ascii_letters) + "_" + "".join(random.choice(string.ascii_letters + string.digits) for _ in range(5))
    digit_semantic.append(d + suffix)
    pure_numbers.append(str(random.randint(0, 10**8)))

digit_semantic_unambiguous = sum(is_symbol(x) and not NUMBER.match(x) for x in digit_semantic)
numeric_symbol_overlap = sum(is_symbol(x) and NUMBER.match(x) for x in pure_numbers)

base_ast = parse_strict("rule Delta never_implies epistemic_upgrade")
base_hash = h(base_ast)
ws_preserved = 0
for _ in range(10000):
    a = " " * random.randint(1, 4)
    b = " " * random.randint(1, 4)
    ast = parse_strict(f"rule{a}Delta{b}never_implies{a}epistemic_upgrade")
    if ast and h(ast) == base_hash:
        ws_preserved += 1

mutated = parse_strict("rule Delta may_reference epistemic_upgrade")

result = {
    "seed": 20260809,
    "valid_case_count": len(valid),
    "valid_pass_count": sum(ast is not None for ast in valid_asts.values()),
    "valid_cases": {k: ast is not None for k, ast in valid_asts.items()},
    "unknown_relation_fuzz_cases": len(unknowns),
    "naive_unknown_accepts": naive_unknown_accepts,
    "strict_unknown_accepts": strict_unknown_accepts,
    "digit_semantic_symbol_cases": len(digit_semantic),
    "digit_semantic_symbol_unambiguous_accepts": digit_semantic_unambiguous,
    "pure_numeric_cases": len(pure_numbers),
    "numeric_symbol_overlap": numeric_symbol_overlap,
    "whitespace_variants": 10000,
    "whitespace_semantic_hash_preserved": ws_preserved,
    "declared_relation_mutation_changes_hash": h(mutated) != base_hash
}
print(json.dumps(result, sort_keys=True))
