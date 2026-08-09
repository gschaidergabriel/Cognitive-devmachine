from pathlib import Path
import json
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from claycode_typed_ast import Document, Frontend, SCHEMA, compare, validate, verify_roundtrip


GRAMMAR = r'''
start: NEWLINE* statement (NEWLINE+ statement)* NEWLINE*
statement: "rule" expr
?expr: term (OP term)*
?term: dotted_relation | call | qid | SIGNED_NUMBER | BOOLEAN | list
dotted_relation: qid DOT_REL term
call: qid "(" [expr ("," expr)*] ")"
list: "[" [expr ("," expr)*] "]"
qid: NAME ("." NAME)*
OP: ">="|"<="|"!="|"=="|">"|"<"|"="|"+"|"-"|"&&"|"||"
DOT_REL: ".lowers"|".owns"
BOOLEAN.2: "true"|"false"
NAME: /[A-Za-z_][A-Za-z0-9_]*/
%import common.SIGNED_NUMBER
%import common.NEWLINE
%import common.WS_INLINE
%ignore WS_INLINE
%ignore /\/\/[^\n]*/
'''


@pytest.fixture(scope="module")
def frontend():
    return Frontend(GRAMMAR)


def test_canonical_roundtrip(frontend):
    document = frontend.parse("rule Needle.lowers f(x,2)\n")
    result = verify_roundtrip(document)
    assert result["pass"]
    assert Document.from_json(document.canonical_json()) == document


@pytest.mark.parametrize("left,right", [
    ("rule x>0\n", "rule x<0\n"),
    ("rule x+1\n", "rule x-1\n"),
    ("rule true\n", "rule false\n"),
    ("rule f(a,b)\n", "rule f(b,a)\n"),
    ("rule Needle.lowers X\n", "rule Needle.owns X\n"),
])
def test_mutations_change_hash(frontend, left, right):
    assert compare(frontend, left, right, False)["pass"]


def test_ignored_layout_is_equivalent(frontend):
    assert compare(frontend, "rule x>0\n", "\nrule  x > 0 // c\n\n", True)["pass"]


def test_receipt_declares_hash_and_parser_contract(frontend):
    receipt = validate(frontend, [("sample", "rule x>0\n")])
    assert receipt["pass"]
    assert receipt["hash_algorithm"] == "SHA-256"
    assert receipt["parser_contract"]["maybe_placeholders"] is False
    assert receipt["canonicalization"]["ignored_layout_terminals"] == ["NEWLINE"]


@pytest.mark.parametrize("bad", [
    "[]",
    '{"schema":"wrong","root":{}}',
    json.dumps({"schema": SCHEMA, "root": {"tag": "token", "terminal": "X", "lexeme": "x"}}),
    json.dumps({"schema": SCHEMA, "root": {"tag": "node", "production": "start", "children": [], "extra": 1}}),
])
def test_decoder_fails_closed(bad):
    with pytest.raises(ValueError):
        Document.from_json(bad)
