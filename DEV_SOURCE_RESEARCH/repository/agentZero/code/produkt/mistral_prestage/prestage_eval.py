#!/usr/bin/env python3
"""prestage_eval.py -- measuring device for the F74 Mistral pre-stage.

READ-ONLY on the pre-stage. Runs a battery of ~20 representative human
messages through prestage.run_prestage and scores each output with purely
mechanical checks (no LLM judge). Prints per-prompt pass/fail and a summary
pass-rate per check plus a ranked list of the worst failures.

Run inside the entityos container:
    docker cp prestage_eval.py entityos:/tmp/prestage_eval.py
    docker exec entityos python3 /tmp/prestage_eval.py
"""
from __future__ import annotations

import json
import sys
import time

sys.path.insert(0, "/opt/clayverse")

from clayverse.mistral_prestage import prestage
from clayverse.mistral_prestage.headless_zero import DEFAULT_ALLOWED_TOOLS
from clayverse.mistral_prestage.transport import TransportError

ALLOWED = set(DEFAULT_ALLOWED_TOOLS)
PREFIX = "mcp__clayverse__"

# machine-vocab that must NEVER leak into caveman_prompt (read by a human
# after translation). tool_selection legitimately holds mcp__ names -- this
# ban is on the caveman_prompt TEXT only.
LEAK_TOKENS = [
    "mcp__",
    "NEED_BETTER_PACKAGE",
    "PROPOSAL_ONLY",
    "state.noop",
    "EffectGate",
    "UnifiedDB",
    "core_identity",
    "substrate",
]
# social-only extra bans (things Zero must not be told to recite)
SOCIAL_LEAK = ["list tool", "list your tool", "request_effect", "tool name"]

# over-interpretation markers: a greeting whose intent mentions these is a
# gross over-reading (measured failure: "hi" -> "wants MCP tools + traffic").
OVERREAD = ["mcp", "traffic", "stats", "tool access", "capability audit",
            "effect", "request_effect", "inventory"]

SOCIAL_MAX_LEN = 300

# battery: each entry -> raw prompt + expected properties.
#   social=True         -> tool_selection must be EMPTY, caveman short+clean
#   expect_tools=[...]   -> at least one selected tool should match one of
#                           these substrings (relevance, soft check)
#   expect_empty=True    -> tool_selection should be empty (capability/social)
BATTERY = [
    # greetings
    dict(prompt="hi", cls="greeting", social=True, expect_empty=True),
    dict(prompt="servus", cls="greeting", social=True, expect_empty=True),
    dict(prompt="na?", cls="greeting", social=True, expect_empty=True),
    dict(prompt="danke", cls="greeting", social=True, expect_empty=True),
    # wellbeing
    dict(prompt="wie gehts", cls="wellbeing", social=True, expect_empty=True),
    dict(prompt="how are you", cls="wellbeing", social=True, expect_empty=True),
    # capability
    dict(prompt="was kannst du", cls="capability", social=True, expect_empty=True),
    dict(prompt="what can you do", cls="capability", social=True, expect_empty=True),
    # site tasks
    dict(prompt="pruef die telefonnummer auf seimensch.net", cls="site",
         expect_tools=["seite_pruefen", "werkbank_suchen", "werkbank_lesen"]),
    dict(prompt="aendere den titel auf der startseite von seimensch.net", cls="site",
         expect_tools=["werkbank_aendern", "werkbank_suchen", "werkbank_lesen"]),
    dict(prompt="such den impressum text auf seimensch.net", cls="site",
         expect_tools=["werkbank_suchen", "werkbank_lesen", "seite_pruefen"]),
    dict(prompt="veroeffentliche die aenderung auf seimensch.net", cls="site",
         expect_tools=["werkbank_veroeffentlichen", "werkbank_stand"]),
    # reachability
    dict(prompt="seimensch.net geht nicht", cls="reach",
         expect_tools=["seite_diagnose"]),
    dict(prompt="ist herzrad.at erreichbar", cls="reach",
         expect_tools=["seite_diagnose", "seite_pruefen"]),
    # knowledge
    dict(prompt="was ist die ZVR nummer von seimensch", cls="knowledge",
         expect_tools=["korpus_suchen", "menschen_profil", "artikel_lesen", "korpus_tief"]),
    dict(prompt="wer ist andreas", cls="knowledge",
         expect_tools=["menschen_profil", "korpus_suchen"]),
    dict(prompt="such im wissen nach resilienz", cls="knowledge",
         expect_tools=["korpus_suchen", "korpus_tief", "artikel_lesen"]),
    # disk
    dict(prompt="wie voll ist die platte", cls="disk",
         expect_tools=["speicher_lage"]),
    dict(prompt="raeum die platte auf", cls="disk",
         expect_tools=["speicher_aufraeumen", "speicher_lage"]),
    # identity
    dict(prompt="wer bin ich", cls="identity", social_intent_ok=True,
         expect_tools=["menschen_profil"]),
]


def call(raw_prompt):
    """One prestage call, one retry on TransportError."""
    for attempt in (1, 2):
        try:
            return prestage.run_prestage(raw_prompt=raw_prompt, current_user="gabriel")
        except TransportError as e:
            if attempt == 2:
                raise
            time.sleep(3.0)
    raise RuntimeError("unreachable")


def score(entry, r):
    cav = str(r.get("caveman_prompt", ""))
    cav_l = cav.lower()
    intent = r.get("user_intent", "")
    intent_s = intent if isinstance(intent, str) else json.dumps(intent, ensure_ascii=False)
    sel = r.get("tool_selection", [])
    if not isinstance(sel, list):
        sel = [sel] if sel else []
    social = entry.get("social", False)

    checks = {}

    # check1: tool_selection subset of DEFAULT_ALLOWED_TOOLS (KEY METRIC)
    invented = [t for t in sel if t not in ALLOWED]
    checks["c1_tools_subset"] = (len(invented) == 0, {"invented": invented})

    # check2: social -> empty selection AND no recite-tools leak in caveman
    if social or entry.get("expect_empty"):
        social_leaks = [tok for tok in SOCIAL_LEAK if tok in cav_l]
        ok2 = (len(sel) == 0) and (len(social_leaks) == 0)
        checks["c2_social_clean"] = (ok2, {"sel_nonempty": sel, "recite_leaks": social_leaks})
    else:
        checks["c2_social_clean"] = (None, {})

    # check3: caveman length reasonable (<300 for social/terse)
    if social:
        checks["c3_len"] = (len(cav) < SOCIAL_MAX_LEN, {"len": len(cav)})
    else:
        checks["c3_len"] = (len(cav) < 600, {"len": len(cav)})

    # check4: no machine-vocab leak in caveman_prompt
    leaks = [tok for tok in LEAK_TOKENS if tok.lower() in cav_l]
    checks["c4_no_machine_vocab"] = (len(leaks) == 0, {"leaks": leaks})

    # check5: intent present and not absurd over-read (social only)
    present = bool(intent_s.strip())
    if social:
        over = [w for w in OVERREAD if w in intent_s.lower()]
        checks["c5_intent_sane"] = (present and len(over) == 0, {"intent": intent_s, "overread": over})
    else:
        checks["c5_intent_sane"] = (present, {"intent": intent_s})

    # check6: relevance -- expected tool present (soft; only where expected)
    if entry.get("expect_tools"):
        hit = [t for t in sel if any(sub in t for sub in entry["expect_tools"])]
        checks["c6_relevant_tool"] = (len(hit) > 0, {"want_any": entry["expect_tools"], "got": sel})
    elif entry.get("expect_empty"):
        checks["c6_relevant_tool"] = (len(sel) == 0, {"want": "empty", "got": sel})
    else:
        checks["c6_relevant_tool"] = (None, {})

    return checks, cav, sel, intent_s


def main():
    results = []
    for i, entry in enumerate(BATTERY):
        p = entry["prompt"]
        try:
            r = call(p)
            err = None
        except Exception as e:
            r, err = None, f"{type(e).__name__}: {e}"
        results.append((entry, r, err))
        if err:
            print(f"[{i+1:2}/{len(BATTERY)}] {entry['cls']:10} {p!r:50} ERROR {err}")
        else:
            checks, cav, sel, intent = score(entry, r)
            tag = []
            for k, (ok, meta) in checks.items():
                if ok is None:
                    continue
                tag.append(f"{k.split('_')[0]}:{'P' if ok else 'F'}")
            print(f"[{i+1:2}/{len(BATTERY)}] {entry['cls']:10} {p!r:50} {' '.join(tag)}")
            print(f"        caveman: {cav}")
            print(f"        intent : {intent}")
            print(f"        tools  : {sel}")
        time.sleep(1.5)

    # summary
    print("\n" + "=" * 70)
    print("SUMMARY -- pass-rate per check")
    print("=" * 70)
    check_keys = ["c1_tools_subset", "c2_social_clean", "c3_len",
                  "c4_no_machine_vocab", "c5_intent_sane", "c6_relevant_tool"]
    agg = {k: [0, 0] for k in check_keys}  # [pass, applicable]
    failures = []
    for entry, r, err in results:
        if err or r is None:
            for k in check_keys:
                pass
            failures.append((99, entry["prompt"], "CALL ERROR", err, {}))
            continue
        checks, cav, sel, intent = score(entry, r)
        for k in check_keys:
            ok, meta = checks[k]
            if ok is None:
                continue
            agg[k][1] += 1
            if ok:
                agg[k][0] += 1
            else:
                # severity: c1 worst (invented tool), then c4, c2, c6, c5, c3
                sev = {"c1_tools_subset": 0, "c4_no_machine_vocab": 1,
                       "c2_social_clean": 2, "c6_relevant_tool": 3,
                       "c5_intent_sane": 4, "c3_len": 5}[k]
                failures.append((sev, entry["prompt"], k, json.dumps(meta, ensure_ascii=False),
                                 {"caveman": cav, "tools": sel}))
    for k in check_keys:
        pw, ap = agg[k]
        rate = f"{pw}/{ap}" if ap else "n/a"
        pct = f" ({100*pw//ap}%)" if ap else ""
        print(f"  {k:22} {rate}{pct}")

    print("\n" + "=" * 70)
    print("RANKED FAILURES (worst first)")
    print("=" * 70)
    failures.sort(key=lambda x: x[0])
    for sev, prompt, k, meta, extra in failures:
        print(f"\n[sev {sev}] check={k}  prompt={prompt!r}")
        print(f"   detail : {meta}")
        if extra:
            print(f"   caveman: {extra.get('caveman','')}")
            print(f"   tools  : {extra.get('tools','')}")


if __name__ == "__main__":
    main()
