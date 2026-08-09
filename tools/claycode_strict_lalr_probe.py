#!/usr/bin/env python3
"""Deterministically expose strict-LALR conflicts in the current ClayCode D candidate.

This is a diagnostic probe, not a parser selection or semantic promotion. It captures
strict construction failure plus non-strict Lark conflict diagnostics so the next repair
can target the exact grammar surface instead of guessing.
"""
from __future__ import annotations
import argparse, hashlib, io, json, logging, re
from datetime import datetime, timezone
from pathlib import Path

from lark import Lark
from lark.exceptions import GrammarError
from lark import logger as lark_logger

ROOT=Path(__file__).resolve().parents[1]
DEFAULT=ROOT/"research_entity/trigger_runs/claycode/claycode-20260809T1717p0700-all-workers-production-parser/D_LALR_GRAMMAR_CANDIDATE_V3.lark"


def sha256(path:Path)->str:return hashlib.sha256(path.read_bytes()).hexdigest()


def normalize(text:str)->str:
    text=re.sub(r"0x[0-9a-fA-F]+","0xADDR",text)
    text=re.sub(r"\s+"," ",text).strip()
    return text


def probe(path:Path)->dict:
    grammar=path.read_text(encoding="utf-8")
    stream=io.StringIO(); handler=logging.StreamHandler(stream); handler.setLevel(logging.DEBUG)
    old_level=lark_logger.level;lark_logger.setLevel(logging.DEBUG);lark_logger.addHandler(handler)
    nonstrict_ok=False;nonstrict_error=None
    try:
        Lark(grammar,parser="lalr",lexer="contextual",strict=False,debug=True)
        nonstrict_ok=True
    except Exception as exc:nonstrict_error=f"{type(exc).__name__}: {exc}"
    finally:
        lark_logger.removeHandler(handler);lark_logger.setLevel(old_level)
    diagnostics=[normalize(x) for x in stream.getvalue().splitlines() if x.strip()]
    strict_ok=False;strict_error=None
    try:
        Lark(grammar,parser="lalr",lexer="contextual",strict=True,debug=True)
        strict_ok=True
    except GrammarError as exc:strict_error=normalize(str(exc))
    except Exception as exc:strict_error=normalize(f"{type(exc).__name__}: {exc}")
    conflict_lines=[x for x in diagnostics if "conflict" in x.lower() or "collision" in x.lower()]
    return {
      "schema_version":"1.0",
      "experiment":"ClayCode D strict-LALR conflict localization",
      "created_at":datetime.now(timezone.utc).isoformat(),
      "grammar_path":str(path.relative_to(ROOT)),"grammar_sha256":sha256(path),
      "runtime":{"parser":"lark","mode":"lalr/contextual","strict_test":True},
      "nonstrict_build_ok":nonstrict_ok,"nonstrict_error":nonstrict_error,
      "strict_build_ok":strict_ok,"strict_error":strict_error,
      "diagnostic_count":len(diagnostics),"conflict_diagnostics":conflict_lines,"all_diagnostics":diagnostics,
      "interpretation":"If strict_build_ok is false, repair only the reported conflict surface and re-run before typed-fn reintegration. This probe does not authorize semantic change or parser selection."
    }


def main():
    ap=argparse.ArgumentParser();ap.add_argument("--grammar",default=str(DEFAULT));ap.add_argument("--output")
    a=ap.parse_args();out=probe(Path(a.grammar));text=json.dumps(out,ensure_ascii=False,indent=2)+"\n"
    if a.output:
        p=Path(a.output);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text,encoding="utf-8")
    print(text,end="")

if __name__=="__main__":main()
