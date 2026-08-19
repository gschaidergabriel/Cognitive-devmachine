import sys, time, json
from clayverse.store import UnifiedDB
from clayverse.mistral_prestage.pipeline import run_chat_turn
from clayverse.mistral_prestage.store import PrestageStore

db = UnifiedDB("/var/lib/clay/wiki.db")
session_id = "session:gabriel"
user_id = "gabriel"

prompts = ["was ist iar?", "wer bin ich?", "wie alt ist gabriel?"]

results = []
for p in prompts:
    t0 = time.time()
    try:
        r = run_chat_turn(db=db, user_id=user_id, session_id=session_id, message=p,
                           record_via_turnlifecycle=False)
        dt = time.time() - t0
        results.append({"prompt": p, "ok": True, "elapsed_s": round(dt, 2),
                         "reply": r["reply"][:300], "elapsed_ms": r["elapsed_ms"],
                         "rounds_used": r["rounds_used"], "self_adapted": r["self_adapted"]})
    except Exception as e:
        dt = time.time() - t0
        results.append({"prompt": p, "ok": False, "elapsed_s": round(dt, 2),
                         "error": f"{type(e).__name__}: {e}"})

for r in results:
    print(json.dumps(r, ensure_ascii=False, indent=2))
    print("---")
