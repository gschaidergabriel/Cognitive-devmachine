"""Reality Layer for EntityOS/Zero -- narrow, additive anti-confabulation check.

Adapted from Frank's services/system_reality_layer.py + core/app.py's
_ego_governor_check (see the audit below for what transferred and what did
not -- read this before touching the module).

FRANK'S MECHANISM HAS TWO INDEPENDENT HALVES
---------------------------------------------
  1. A [REALITAET] block injected into the prompt -- a hardcoded/probed truth
     dict about Frank's own hardware/software/services, shown to the model
     BEFORE it answers.
  2. A post-hoc "Ego Governor" (core/app.py) that regex-scans the DELIVERED
     answer for a small, CLOSED set of known-wrong self-claims (wrong model
     name, wrong GPU, wrong architecture, "I run in the cloud") and appends a
     visible correction if found.

WHAT TRANSFERS TO ENTITYOS AND WHAT DOES NOT
---------------------------------------------
Half 1 (the block) is ALREADY BUILT here, and arguably built better: Zero's
own canonical_identity (UnifiedDB `meta.canonical_identity`, injected into
every headless_zero.run_headless() call via RUNTIME_PROMPT/_systemanweisung)
already carries an explicit "du rätst nie" anti-confabulation doctrine
("Erfinden ist die einzige Art, aus dieser Rolle zu fallen") PLUS
per-capability status tags: <compute_nodes status="NOT_CONNECTED">,
<reputation status="NOT_BUILT">, <core status="LIVE">, <terminal_portal
status="LIVE">. Rebuilding a second reality-block here would be pure
doubling -- the one thing the task explicitly said not to do. The existing
`epistemik` field the pre-stage already produces (prestage.py, "bekannt"/
"unbekannt") covers general knowledge-grounding; it is a PREDICTION made
before Zero answers, not a check of what Zero actually said.

Half 2 (the post-hoc check) is genuinely MISSING: nothing today verifies,
AFTER Zero has answered, whether the delivered text actually honoured those
status tags. THIS module adds exactly that -- and only that.

A general corpus-grounding checker (diff the answer against everything
retrieved this turn: world["corpus"], durable_memory, nutzerprofil, ...) was
considered and REJECTED after reading headless_zero.py and inspecting 5 real
rows from mv_prestage_turns/mv_translation_log (wiki.db, read-only):

    Zero is a real `claude -p` agentic subprocess with its own
    Bash/WebSearch/WebFetch/Grep tools (headless_zero.py run_headless(),
    "--tools" includes WebSearch/WebFetch). `--output-format json` returns
    only the FINAL result text -- never the tool-call transcript. In all 5
    sampled production rows (real "wie alt bin ich" turns), the grounding for
    the delivered answer came from a live WebSearch Zero ran ITSELF inside
    that subprocess -- completely invisible to pipeline.py. caveman_prompt
    for those turns was 27-117 characters long; the actual evidence never
    passed through anything pipeline.py can see.

    A pipeline-level "not present in my retrieval context => flag it" checker
    would have flagged all 5 of those correct, well-grounded answers as
    unconfirmed. That is the opposite of Frank's mechanism, where the truth
    dict is closed and authoritative (Frank really does know its own GPU via
    lspci). Building that checker here would violate the "keine
    Uebervorsicht" requirement on the very first real example tested against,
    so it was not built.

What IS closed and authoritative here, exactly like Frank's hardware dict, is
canonical_identity's per-capability status tags: UnifiedDB -- not any single
turn's retrieval -- is the ground truth for "is X connected / built". This
module therefore narrowly checks the DELIVERED reply against THOSE tags
only: same shape of check as Frank's Ego Governor (closed truth set, regex
scan of the output, visible correction, never a silent rewrite), scoped to
the one thing EntityOS actually has a closed truth set for.

FLAG
----
CLAYVERSE_REALITY_CHECK=1 enables it (default OFF/unset). Every public
function here is wrapped so an internal failure can NEVER take a turn down:
worst case is the reply passes through completely untouched, identical to
today's behaviour.

Usage (pipeline.py, additive, after translation, before record_prestage_turn):

    if reality_layer.reality_check_enabled():
        try:
            verdict = reality_layer.check_reply(
                german.get("german_translation", ""), world.get("canonical_identity"))
            if not verdict["ok"]:
                german["german_translation"] = reality_layer.annotate_if_violated(
                    german.get("german_translation", ""), verdict)
                reality_layer.log_realitaetscheck(own_store, turn_id, session_id, verdict)
        except Exception:
            pass
"""

from __future__ import annotations

import json
import logging
import os
import re
import time
from typing import Any

LOG = logging.getLogger("reality_layer")

REALITY_CHECK_FLAG = "CLAYVERSE_REALITY_CHECK"


def reality_check_enabled() -> bool:
    """Default OFF -- set CLAYVERSE_REALITY_CHECK=1 to turn this on."""
    try:
        return os.environ.get(REALITY_CHECK_FLAG, "0").strip() == "1"
    except Exception:
        return False


# Per-capability watch list. Keys MUST match a <tag> name inside
# canonical_identity's <cybernetic_substrate> block (see store.py
# canonical_identity(), UnifiedDB meta table). Only entries whose LIVE status
# -- parsed fresh from canonical_identity every turn, see _parse_status_tags
# -- is something OTHER than "LIVE" are ever checked. If UnifiedDB later
# marks compute_nodes LIVE, this list stops firing for it automatically, no
# code change needed here -- exactly like Frank's hardware probe re-reading
# lspci instead of trusting a stale constant.
_STATUS_WATCH: dict[str, dict[str, Any]] = {
    "compute_nodes": {
        "keywords": (
            "mini-pc", "mini pc", "minipc", "compute node", "compute-knoten",
            "computeknoten", "ausführungsknoten", "ausfuehrungsknoten",
            "ausführungs-knoten", "ausfuehrungs-knoten", "linux-mini-pc",
            "linux-mini-pcs", "zweitrechner",
        ),
        "claim_verbs": (
            "verbunden", "angebunden", "ausgeführt", "ausgefuehrt",
            "läuft dort", "laeuft dort", "lief dort", "zugriff auf",
            "erledigt auf", "gestartet auf", "läuft darauf", "laeuft darauf",
        ),
        "hinweis": "Compute-Knoten (Mini-PCs) sind laut kanonischem Zustand NICHT angebunden",
    },
    "reputation": {
        "keywords": (
            "ers", "reputationswert", "reputationswerte", "netzwerk-reputation",
        ),
        "claim_verbs": (
            "beträgt", "betraegt", "liegt bei", "steht bei", "ist gestiegen",
            "ist gesunken", "zeigt",
        ),
        "hinweis": "Der Reputationswert (ERS) existiert laut kanonischem Zustand noch nicht",
    },
}

# If any of these appear in the same sentence as a keyword+claim_verb match,
# it is very likely a CORRECT statement ("die Mini-PCs sind NICHT
# angebunden") rather than a confabulation -- skip it. Biased deliberately
# toward not-flagging: a missed violation is recoverable next turn, a false
# alarm on a correct, well-hedged answer is the exact "Uebervorsicht" the
# task said to avoid.
_NEGATIONEN = (
    "nicht", "kein", "keine", "keinen", "keiner", "keinem",
    "nie", "niemals", "nichts", "noch nicht", "bislang nicht",
    "unverbunden", "nicht_connected",
)

_STATUS_TAG_RE = re.compile(r'<(\w+)\s+status="([A-Z_]+)"\s*>(.*?)</\1>', re.DOTALL)
_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+|\n+")


def _compile_terms(terms: tuple[str, ...]) -> list[re.Pattern]:
    """Word-boundary regex per term, NOT substring matching.

    Measured why this matters: a naive `"ers" in text.lower()` check flagged
    3/306 real production answers as violations purely because "ers" is a
    substring of "ClayVerse" -- the product's OWN name. Same failure mode for
    the claim-verb "zeigt", a substring of "angezeigt" ("displayed", nothing
    to do with a reputation number). \\b keeps a short acronym like "ERS" from
    matching inside an unrelated word.
    """
    compiled = []
    for term in terms:
        try:
            compiled.append(re.compile(r"\b" + re.escape(term) + r"\b", re.IGNORECASE))
        except re.error:
            continue
    return compiled


def _any_match(patterns: list[re.Pattern], text: str) -> bool:
    return any(p.search(text) for p in patterns)


# Pre-compiled once at import time (cheap; the watch list is tiny and static).
_COMPILED_WATCH: dict[str, dict[str, Any]] = {
    tag: {
        "keywords": _compile_terms(watch["keywords"]),
        "claim_verbs": _compile_terms(watch["claim_verbs"]),
        "hinweis": watch["hinweis"],
    }
    for tag, watch in _STATUS_WATCH.items()
}


def _parse_status_tags(canonical_identity: Any) -> dict[str, str]:
    """{tag_name: status} straight out of canonical_identity's XML-ish text.

    Best-effort regex, not a real XML parser -- canonical_identity is a
    controlled, hand-authored string (store.py canonical_identity()), not
    untrusted input. A parse failure must never take a turn down: on any
    error, return {} (== nothing is checked, safe fallback == today's
    behaviour).
    """
    try:
        text = canonical_identity if isinstance(canonical_identity, str) else str(canonical_identity or "")
        return {m.group(1): m.group(2) for m in _STATUS_TAG_RE.finditer(text)}
    except Exception:
        return {}


def _has_negation(sentence: str) -> bool:
    return any(neg in sentence for neg in _NEGATIONEN)


def check_reply(reply_text: str, canonical_identity: Any) -> dict[str, Any]:
    """Scan the DELIVERED reply for violations of canonical_identity's
    non-LIVE status tags. Never raises -- any internal failure returns a
    clean 'ok' verdict so the reply is never touched.

    Returns {"ok": bool, "violations": [{"tag", "hinweis", "satz"}, ...]}.
    """
    try:
        if not reply_text or not isinstance(reply_text, str):
            return {"ok": True, "violations": []}
        statuses = _parse_status_tags(canonical_identity)
        if not statuses:
            return {"ok": True, "violations": []}
        sentences = _SENTENCE_SPLIT_RE.split(reply_text)
        violations: list[dict[str, str]] = []
        for tag, watch in _COMPILED_WATCH.items():
            status = statuses.get(tag)
            if not status or status == "LIVE":
                continue  # dynamically disabled -- UnifiedDB says it's live now
            if not _any_match(watch["keywords"], reply_text):
                continue  # cheap pre-filter before the per-sentence scan
            for satz in sentences:
                if not _any_match(watch["keywords"], satz):
                    continue
                if not _any_match(watch["claim_verbs"], satz):
                    continue
                if _has_negation(satz.lower()):
                    continue  # "nicht angebunden" IS the correct claim
                violations.append({"tag": tag, "hinweis": watch["hinweis"], "satz": satz.strip()})
        return {"ok": not violations, "violations": violations}
    except Exception as exc:
        LOG.warning("reality check failed, falling back to ok: %s", exc)
        return {"ok": True, "violations": []}


_MARKER_TEMPLATE = (
    "\n\n⚠️ Realitätsprüfung: {saetze} widersprechen dem kanonischen Zustand "
    "({hinweise}). Bitte als ungeprüft behandeln."
)


def annotate_if_violated(reply_text: str, verdict: dict[str, Any]) -> str:
    """Append a visible marker when check_reply() found violations.

    Additive only -- never removes or rewrites the model's own text, same
    ethic as pipeline.py's _ohne_paketurteil/_log_uebersetzungsausfall: stay
    visible, never silently fix. Any internal error returns reply_text
    unchanged.
    """
    try:
        if not reply_text or verdict.get("ok", True):
            return reply_text
        violations = verdict.get("violations") or []
        if not violations:
            return reply_text
        hinweise = "; ".join(dict.fromkeys(v["hinweis"] for v in violations))
        saetze = " / ".join(f"„{v['satz'][:160]}“" for v in violations[:3])
        return reply_text.rstrip() + _MARKER_TEMPLATE.format(saetze=saetze, hinweise=hinweise)
    except Exception:
        return reply_text


def log_realitaetscheck(store, turn_id, session_id, verdict: dict[str, Any]) -> None:
    """Mitschreiben, nicht schweigen -- same bookkeeping ethic as
    pipeline.py's log_paketurteil()/_log_uebersetzungsausfall(). Darf nie
    werfen; own table (mv_realitaetscheck), created additively, never touches
    any existing table.
    """
    try:
        violations = verdict.get("violations") or []
        if not violations:
            return
        store.db.executescript(
            "CREATE TABLE IF NOT EXISTS mv_realitaetscheck("
            "  id INTEGER PRIMARY KEY AUTOINCREMENT, ts REAL NOT NULL,"
            "  turn_id TEXT, session_id TEXT, tags TEXT, detail TEXT);"
        )
        store.db.execute(
            "INSERT INTO mv_realitaetscheck(ts,turn_id,session_id,tags,detail) VALUES(?,?,?,?,?)",
            (
                time.time(), turn_id, session_id,
                ",".join(sorted({v["tag"] for v in violations})),
                json.dumps(violations, ensure_ascii=False)[:2000],
            ),
        )
        store.db.commit()
    except Exception:
        pass  # Buchfuehrung darf einen Zug nie kippen
