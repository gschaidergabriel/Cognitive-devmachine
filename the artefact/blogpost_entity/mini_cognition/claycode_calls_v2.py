#!/usr/bin/env python3
"""Non-executing ClayCode call extractor for validation/evaluation.

Only identifier(...) forms outside string literals and comments are returned.
Nested calls are retained so semantic markers such as cfg("entity.id") remain
observable when they occur inside a real outer call. Every call also records its
brace depth so canonical turn-body calls can be distinguished from nested/dead
control flow without creating a second parser authority.
"""
import re

IDENT = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")


def canonical(text):
    out = []
    quoted = False
    escaped = False
    for ch in text:
        if quoted:
            out.append(ch)
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == '"':
                quoted = False
        else:
            if ch == '"':
                quoted = True
                out.append(ch)
            elif not ch.isspace():
                out.append(ch)
    return "".join(out)


def without_comments(text):
    out = list(text)
    quoted = False
    escaped = False
    i = 0
    n = len(text)
    while i < n:
        ch = text[i]
        if quoted:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == '"':
                quoted = False
            i += 1
            continue
        if ch == '"':
            quoted = True
            i += 1
            continue
        if ch == "/" and i + 1 < n and text[i + 1] == "/":
            out[i] = out[i + 1] = " "
            i += 2
            while i < n and text[i] != "\n":
                out[i] = " "
                i += 1
            continue
        if ch == "/" and i + 1 < n and text[i + 1] == "*":
            out[i] = out[i + 1] = " "
            i += 2
            while i < n:
                if text[i] == "*" and i + 1 < n and text[i + 1] == "/":
                    out[i] = out[i + 1] = " "
                    i += 2
                    break
                if text[i] != "\n":
                    out[i] = " "
                i += 1
            continue
        i += 1
    return "".join(out)


def extract_calls(code):
    code = without_comments(code)
    calls = []
    n = len(code)
    i = 0
    quoted = False
    escaped = False
    brace_depth = 0
    while i < n:
        ch = code[i]
        if quoted:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == '"':
                quoted = False
            i += 1
            continue
        if ch == '"':
            quoted = True
            i += 1
            continue
        if ch == "{":
            brace_depth += 1
            i += 1
            continue
        if ch == "}":
            brace_depth -= 1
            i += 1
            continue
        match = IDENT.match(code, i)
        if not match:
            i += 1
            continue
        name = match.group(0)
        j = match.end()
        while j < n and code[j].isspace():
            j += 1
        if j >= n or code[j] != "(":
            i = match.end()
            continue
        depth = 0
        k = j
        inner_quoted = False
        inner_escaped = False
        while k < n:
            current = code[k]
            if inner_quoted:
                if inner_escaped:
                    inner_escaped = False
                elif current == "\\":
                    inner_escaped = True
                elif current == '"':
                    inner_quoted = False
            else:
                if current == '"':
                    inner_quoted = True
                elif current == "(":
                    depth += 1
                elif current == ")":
                    depth -= 1
                    if depth == 0:
                        calls.append({"fn": name, "call": canonical(code[i : k + 1]), "depth": brace_depth})
                        break
            k += 1
        i = match.end()
    return calls


def call_set(code, depth=None):
    return {item["call"] for item in extract_calls(code) if depth is None or item["depth"] == depth}


def fn_counts(code, depth=None):
    counts = {}
    for item in extract_calls(code):
        if depth is not None and item["depth"] != depth:
            continue
        counts[item["fn"]] = counts.get(item["fn"], 0) + 1
    return counts
