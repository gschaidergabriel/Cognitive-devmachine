import re, random, string, hashlib, json

SEED=20260809
N=10000
rng=random.Random(SEED)

CURRENT_REF=re.compile(r'@\S+')
CANDIDATE_REF=re.compile(r'@[A-Za-z0-9_./:-]+')
CURRENT_IDENT=re.compile(r'[A-Za-z_][A-Za-z0-9_-]*')
CANDIDATE_IDENT=re.compile(r'[A-Za-z_][A-Za-z0-9_]*')

def rand_ident():
    return rng.choice(string.ascii_letters+'_') + ''.join(rng.choice(string.ascii_letters+string.digits+'_') for _ in range(rng.randint(1,10)))

def rand_path():
    parts=[rand_ident() for _ in range(rng.randint(2,5))]
    return '@' + '/'.join(parts) + '.clay'

ref_overconsume=0
ref_candidate_fail=0
for _ in range(N):
    a,b=rand_path(),rand_path()
    s=f'[{a},{b}]'
    m=CURRENT_REF.search(s)
    if m and m.group(0) != a:
        ref_overconsume += 1
    m2=CANDIDATE_REF.search(s)
    if (not m2) or m2.group(0) != a:
        ref_candidate_fail += 1

minus_current_collision=0
minus_candidate_fail=0
for _ in range(N):
    a,b=rand_ident(),rand_ident()
    s=f'{a}-{b}'
    m=CURRENT_IDENT.fullmatch(s)
    if m:
        minus_current_collision += 1
    ma=CANDIDATE_IDENT.match(s)
    ok=bool(ma and ma.group(0)==a and s[len(a)]=='-' and CANDIDATE_IDENT.fullmatch(s[len(a)+1:]))
    if not ok:
        minus_candidate_fail += 1

hyphenated_current_accept=0
hyphenated_candidate_accept=0
for _ in range(N):
    a,b=rand_ident(),rand_ident()
    s=f'{a}-{b}'
    if CURRENT_IDENT.fullmatch(s): hyphenated_current_accept += 1
    if CANDIDATE_IDENT.fullmatch(s): hyphenated_candidate_accept += 1

examples={
  'parent_adjacent_refs':'parent [@research_entity/claycode/g9/A.clay,@research_entity/claycode/g9/B.clay]',
  'subtraction_no_spaces':'rule delta=a-b',
  'subtraction_spaced':'rule delta=a - b',
}
example_tokens={}
for k,s in examples.items():
    example_tokens[k]={
      'current_refs':CURRENT_REF.findall(s),
      'candidate_refs':CANDIDATE_REF.findall(s),
      'current_idents':CURRENT_IDENT.findall(s),
      'candidate_idents':CANDIDATE_IDENT.findall(s),
    }

result={
 'seed':SEED,'cases_per_family':N,
 'ref_overconsume_current':ref_overconsume,
 'ref_candidate_fail':ref_candidate_fail,
 'minus_collision_current':minus_current_collision,
 'minus_candidate_fail':minus_candidate_fail,
 'hyphenated_identifier_current_accept':hyphenated_current_accept,
 'hyphenated_identifier_candidate_accept':hyphenated_candidate_accept,
 'examples':example_tokens,
 'conclusion':{
   'ref':'REF lexical rule must be delimiter-aware; literal non-whitespace maximal munch is incompatible with adjacent list delimiters.',
   'minus':'Current bare identifier grammar makes unspaced subtraction lexically ambiguous with hyphenated identifiers under longest-match lexing.',
   'hyphen':'Removing hyphen from bare identifiers fixes subtraction ambiguity but is not promotable until a repository-wide compatibility scan or an explicit escaped/sigil identifier form exists.'
 }
}
print(json.dumps(result,indent=2,sort_keys=True))
print('script_sha256',hashlib.sha256(open(__file__,'rb').read()).hexdigest())
