#!/usr/bin/env python3
"""Shared non-executing ClayCode syntax scanner for admission and evaluation.

This is intentionally a small lexical/structural helper, not a runtime executor.
Generated promotion candidates fail closed on comment syntax; quoted text never
creates call credit. Calls retain the brace depth at which the identifier occurs
so canonical turn-body statements can be distinguished from nested/dead control
flow.
"""
import re

IDENT = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")


def canonical(text):
    out=[]; quoted=False; esc=False
    for ch in text:
        if quoted:
            out.append(ch)
            if esc:
                esc=False
            elif ch=="\\":
                esc=True
            elif ch=='"':
                quoted=False
        else:
            if ch=='"':
                quoted=True; out.append(ch)
            elif not ch.isspace():
                out.append(ch)
    return "".join(out)


def outside_strings(text):
    out=[]; quoted=False; esc=False
    for ch in text:
        if quoted:
            if esc:
                esc=False
            elif ch=="\\":
                esc=True
            elif ch=='"':
                quoted=False
            out.append(" ")
        else:
            if ch=='"':
                quoted=True; out.append(" ")
            else:
                out.append(ch)
    return "".join(out), quoted


def statement_lines(code):
    """Return ((raw_statement, depth_before_line), ...), lexical_error."""
    rows=[]; depth=0
    for raw in code.splitlines():
        structural, unterminated=outside_strings(raw)
        if unterminated:
            return None, "unterminated_string"
        if "//" in structural or "/*" in structural or "*/" in structural:
            return None, "comment_syntax_forbidden"
        stripped=raw.strip()
        if stripped:
            rows.append((stripped,depth))
        depth += structural.count("{") - structural.count("}")
        if depth < 0:
            return None, "brace_depth_underflow"
    return tuple(rows), None


def top_level_statements(rows):
    return tuple(statement for statement,depth in rows if depth==1)


def _skip_quoted(code, i):
    i += 1; esc=False; n=len(code)
    while i<n:
        ch=code[i]
        if esc:
            esc=False
        elif ch=="\\":
            esc=True
        elif ch=='"':
            return i+1
        i += 1
    return n


def _skip_line_comment(code, i):
    j=code.find("\n", i+2)
    return len(code) if j<0 else j


def _skip_block_comment(code, i):
    j=code.find("*/", i+2)
    return len(code) if j<0 else j+2


def extract_calls(code):
    """Return identifier(...) forms outside strings/comments with brace depth."""
    calls=[]; n=len(code); i=0; brace_depth=0
    while i<n:
        ch=code[i]
        if ch=='"':
            i=_skip_quoted(code,i); continue
        if code.startswith("//",i):
            i=_skip_line_comment(code,i); continue
        if code.startswith("/*",i):
            i=_skip_block_comment(code,i); continue
        if ch=='{':
            brace_depth += 1; i += 1; continue
        if ch=='}':
            brace_depth -= 1; i += 1; continue
        m=IDENT.match(code,i)
        if not m:
            i += 1; continue
        name=m.group(0); start=i; j=m.end()
        while j<n and code[j].isspace():
            j += 1
        if j>=n or code[j] != '(':
            i=m.end(); continue
        depth=0; k=j
        while k<n:
            c=code[k]
            if c=='"':
                k=_skip_quoted(code,k); continue
            if code.startswith("//",k):
                k=_skip_line_comment(code,k); continue
            if code.startswith("/*",k):
                k=_skip_block_comment(code,k); continue
            if c=='(':
                depth += 1
            elif c==')':
                depth -= 1
                if depth==0:
                    calls.append({"fn":name,"call":canonical(code[start:k+1]),"depth":brace_depth})
                    break
            k += 1
        i=m.end()
    return tuple(calls)


def call_set(code, depth=None):
    return {x["call"] for x in extract_calls(code) if depth is None or x["depth"]==depth}


def fn_counts(code, depth=None):
    out={}
    for item in extract_calls(code):
        if depth is not None and item["depth"] != depth:
            continue
        out[item["fn"]]=out.get(item["fn"],0)+1
    return out
