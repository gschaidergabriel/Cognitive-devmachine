#!/usr/bin/env python3
"""Small non-executing ClayCode call extractor for evaluation gates.

This is deliberately not an interpreter. It only identifies identifier(...) forms that
actually occur outside string literals, balances nested parentheses, and canonicalizes
whitespace outside strings. A required intrinsic mentioned inside a string therefore
cannot satisfy a semantic OOD gate.
"""
import re
IDENT=re.compile(r'[A-Za-z_][A-Za-z0-9_]*')

def canonical(text):
    out=[]; quoted=False; esc=False
    for ch in text:
        if quoted:
            out.append(ch)
            if esc: esc=False
            elif ch=='\\': esc=True
            elif ch=='"': quoted=False
        else:
            if ch=='"': quoted=True; out.append(ch)
            elif not ch.isspace(): out.append(ch)
    return ''.join(out)

def extract_calls(code):
    calls=[]; n=len(code); i=0; quoted=False; esc=False
    while i<n:
        ch=code[i]
        if quoted:
            if esc: esc=False
            elif ch=='\\': esc=True
            elif ch=='"': quoted=False
            i+=1; continue
        if ch=='"': quoted=True; i+=1; continue
        m=IDENT.match(code,i)
        if not m:
            i+=1; continue
        name=m.group(0); j=m.end()
        while j<n and code[j].isspace(): j+=1
        if j>=n or code[j]!='(':
            i=m.end(); continue
        depth=0; k=j; q=False; e=False
        while k<n:
            c=code[k]
            if q:
                if e: e=False
                elif c=='\\': e=True
                elif c=='"': q=False
            else:
                if c=='"': q=True
                elif c=='(': depth+=1
                elif c==')':
                    depth-=1
                    if depth==0:
                        calls.append({'fn':name,'call':canonical(code[i:k+1])})
                        break
            k+=1
        i=m.end()
    return calls

def call_set(code): return {x['call'] for x in extract_calls(code)}
def fn_counts(code):
    out={}
    for x in extract_calls(code): out[x['fn']]=out.get(x['fn'],0)+1
    return out

if __name__=='__main__':
    import json,sys
    text=sys.stdin.read()
    print(json.dumps({'calls':extract_calls(text),'fn_counts':fn_counts(text)},indent=2))
