from __future__ import annotations

import argparse
import json
import statistics
import time
from pathlib import Path

from . import judge as judge_mod
from . import translator as translator_mod
from .store import PrestageStore

RETRY_ATTEMPTS = 5
RETRY_BASE_SECONDS = 5.0


def _with_retry(fn, *args, **kwargs):
    """Free-tier judge/translator APIs throw transient 5xx sometimes (measured:
    Gemini 503 on a cold call). Retries are for transport flakiness only --
    they never touch scoring logic."""
    last_exc = None
    for attempt in range(RETRY_ATTEMPTS):
        try:
            return fn(*args, **kwargs)
        except Exception as exc:  # noqa: BLE001 -- deliberately broad, transport-layer retry
            last_exc = exc
            if attempt < RETRY_ATTEMPTS - 1:
                time.sleep(RETRY_BASE_SECONDS * (2**attempt))
    raise last_exc

EVAL_SET_PATH = Path(__file__).with_name("eval_set.json")

# --- The metric, defined before any optimisation (M4 requirement) ---
#
# One eval item PASSES iff:
#   fabrication == False   AND
#   faithfulness >= FAITHFULNESS_MIN   AND
#   readability  >= READABILITY_MIN
#
# The reported score is pass_rate = (# passing items) / (eval set size).
# Target: pass_rate >= 0.95, on an eval set large enough that 0.95 means
# something (this set is 50 items; 95% = at most 2 failures allowed).
#
# Faithfulness gets the strict bar (90) because it is the axis that makes
# the translation layer safe to use at all -- an unfaithful-but-readable
# translation is the exact failure mode the owner flagged as "worse than
# none". Readability gets a looser bar (70) because a technically-faithful
# but slightly clunky sentence is a nuisance, not a trust problem.
FAITHFULNESS_MIN = 90
READABILITY_MIN = 70


def load_eval_set() -> list[str]:
    return json.loads(EVAL_SET_PATH.read_text(encoding="utf-8"))


def run_eval(
    *,
    iteration: int,
    prompt_version: str,
    translate_model: str = translator_mod.TRANSLATOR_MODEL,
    judge_model: str = judge_mod.JUDGE_MODEL,
    db_path: str | None = None,
    sleep_between: float = 0.0,
) -> dict:
    eval_set = load_eval_set()
    store = PrestageStore(db_path)
    results = []
    try:
        for i, caveman in enumerate(eval_set):
            translation = _with_retry(translator_mod.translate_to_german, caveman, model=translate_model)
            verdict = _with_retry(
                judge_mod.judge_translation, caveman, translation["german_translation"], model=judge_model
            )
            fabrication = bool(verdict.get("fabrication"))
            faithfulness = 0 if fabrication else int(verdict.get("faithfulness", 0))
            readability = int(verdict.get("readability", 0))
            passed = (
                not fabrication
                and faithfulness >= FAITHFULNESS_MIN
                and readability >= READABILITY_MIN
            )
            store.record_translation(
                caveman_original=caveman,
                german_translation=translation["german_translation"],
                translator_model=translate_model,
                translator_receipt=translation["translator_receipt"],
                faithfulness_score=faithfulness,
                readability_score=readability,
                judge_model=judge_model,
                judge_verdict=verdict,
                fabrication_flag=fabrication,
            )
            results.append(
                {
                    "idx": i,
                    "caveman": caveman,
                    "german": translation["german_translation"],
                    "faithfulness": faithfulness,
                    "readability": readability,
                    "fabrication": fabrication,
                    "passed": passed,
                    "reason": verdict.get("reason", ""),
                }
            )
            if sleep_between:
                time.sleep(sleep_between)

        n = len(results)
        pass_rate = sum(r["passed"] for r in results) / n
        avg_f = statistics.mean(r["faithfulness"] for r in results)
        avg_r = statistics.mean(r["readability"] for r in results)
        fab_count = sum(r["fabrication"] for r in results)
        store.record_eval_run(
            iteration=iteration,
            prompt_version=prompt_version,
            eval_set_size=n,
            pass_rate=pass_rate,
            avg_faithfulness=avg_f,
            avg_readability=avg_r,
            fabrication_count=fab_count,
            notes=f"translate_model={translate_model} judge_model={judge_model}",
        )
    finally:
        store.close()

    return {
        "iteration": iteration,
        "prompt_version": prompt_version,
        "eval_set_size": len(results),
        "pass_rate": pass_rate,
        "avg_faithfulness": avg_f,
        "avg_readability": avg_r,
        "fabrication_count": fab_count,
        "results": results,
    }


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--iteration", type=int, required=True)
    ap.add_argument("--prompt-version", required=True)
    ap.add_argument("--db-path", default=None)
    ap.add_argument("--sleep-between", type=float, default=3.0)
    ap.add_argument("--show-failures", action="store_true")
    args = ap.parse_args()
    summary = run_eval(
        iteration=args.iteration,
        prompt_version=args.prompt_version,
        db_path=args.db_path,
        sleep_between=args.sleep_between,
    )
    brief = {k: v for k, v in summary.items() if k != "results"}
    print(json.dumps(brief, indent=2, ensure_ascii=False))
    if args.show_failures:
        for r in summary["results"]:
            if not r["passed"]:
                print("---")
                print("caveman:", r["caveman"])
                print("german: ", r["german"])
                print(f"faithfulness={r['faithfulness']} readability={r['readability']} fabrication={r['fabrication']}")
                print("reason: ", r["reason"])
