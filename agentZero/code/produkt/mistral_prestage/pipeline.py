from __future__ import annotations

import time
from typing import Any

from .. import identity  # coordinator-owned, imported not edited
from . import headless_zero, prestage, translator
import re

from .prestage import MAX_ROUNDS, NEGOTIATION_SENTINEL
from .store import PrestageStore

CANONICAL_USERS = {"gabriel", "andreas"}


class PipelineError(RuntimeError):
    pass


def _gather_world_safe(db, session_id: str) -> dict[str, Any]:
    """Read-only world assembly, no turn admission.

    Uses clayverse.retrieval.WorldAssembler directly instead of
    TurnLifecycle.begin_admission() so context can be gathered WITHOUT writing
    a turn. WorldAssembler.assemble() already has a no-active-turn fallback
    path (the "LEGACY_COMPATIBILITY" branch) for exactly this case -- it is
    not a hack, it is the path the module already ships for callers with no
    active causal turn.
    """
    from .. import retrieval  # coordinator-owned module, imported not edited

    assembler = retrieval.WorldAssembler(db)
    return assembler.assemble(session_id, resource_refs=[])




_PAKET_WORTE = ("need_better_package", "besseres paket", "das paket", "the package",
                "paket reicht", "package is enough", "kein bedarf")


def _ohne_paketurteil(text: str) -> tuple[str, str | None]:
    """Entfernt einen kurzen ersten Absatz, der ueber das Vorstufen-Paket urteilt.

    Gibt (text, entfernt_oder_None) zurueck -- der zweite Wert wird MITGESCHRIEBEN.
    Ein stiller Filter waere hier falsch: er beseitigt das Symptom und laesst
    mich glauben, die Anweisung an das Modell wirke. Solange etwas entfernt
    wird, wirkt sie nicht.

    Eng gefasst mit Absicht: nur der erste Absatz, nur unter 300 Zeichen, nur
    mit Paket-Wort. Ein breiter Filter wuerde irgendwann echten Inhalt fressen.
    """
    if not text:
        return text, None
    teile = text.split("\n\n", 1)
    if len(teile) != 2:
        return text, None
    kopf, rest = teile[0].strip(), teile[1]
    if len(kopf) > 300 or not rest.strip():
        return text, None
    if not any(w in kopf.lower() for w in _PAKET_WORTE):
        return text, None
    return rest.lstrip(), kopf


def _profil_safe(db, user_id: str) -> dict | None:
    """Profil, Rechnerbesitz und Wiki-Bestand des anwesenden Menschen.

    Ausfallsicher, weil ein fehlendes Profil einen Zug nicht kippen darf: die
    Vorstufe bekommt dann NO_PROFILE und sagt das, statt zu raten. Ein Fehler
    hier wuerde sonst die ganze Anfrage verlieren -- fuer Beiwerk.

    ⚠️ Der Schluessel heisst `gehoert_zu`, nicht `gehoert`. Mit dem falschen
    Namen liefert .get() klaglos None, und die Vorstufe liest fuer JEDEN Rechner
    "gehoert niemandem, nicht deiner" -- kein Fehler, nur die Unwahrheit, und
    zwar genau bei der Angabe, die der Eigner ausdruecklich bestellt hat.
    """
    try:
        from .. import profile as _profile
        from .. import wirte as _wirte
        from .. import artikel_zuordnung as _az
        p = _profile.profil(db, user_id)
        try:
            p["rechner"] = [
                {"wirt": w.get("wirt"), "gehoert_zu": w.get("gehoert_zu"),
                 "meiner": w.get("gehoert_zu") == user_id, "online": w.get("online")}
                for w in _wirte.verbundene_systeme(db)
            ]
        except Exception:
            p["rechner"] = []
        try:
            p["wiki_bestand"] = _az.bestand(db, user_id)
        except Exception:
            pass
        try:
            from .. import erfolge as _erfolge
            p["bilanz"] = _erfolge.bilanz(db, user_id)
        except Exception:
            pass
        return p
    except Exception:
        return None


def run_chat_turn(
    *,
    db,
    user_id: str,
    session_id: str,
    message: str,
    store: PrestageStore | None = None,
    record_via_turnlifecycle: bool = False,
    tool_selection: list[str] | None = None,
) -> dict[str, Any]:
    """The one interface: German message in, German reply out.

    record_via_turnlifecycle=False (default): does not touch turns/
    active_turns at all. Records the exchange only in this module's own
    mv_prestage_turns/mv_translation_log tables.

    record_via_turnlifecycle=True: uses TurnLifecycle.begin_admission()/
    .complete() -- the product's own atomic admission primitives, reused
    rather than reimplemented, exactly as asked. HISTORY: this was genuinely
    unsafe when first written -- the managed UserPromptSubmit hook fires on
    every `claude -p` call just like an interactive keystroke, and as measured
    2026-08-18 it independently called begin_admission() on the same session,
    a second admitter racing this one. THAT IS FIXED: clayverse/
    terminal_hooks.py's _main() now checks CLAYVERSE_PIPELINE_MANAGED first,
    before any stdin/DB access, and short-circuits to
    {"suppressOutput": true} instead of reaching user_prompt()'s
    begin_admission() -- see headless_zero.py's run_headless() docstring for
    the full account and the live-DB re-verification (active_turns empty).
    headless_zero.run_headless()'s pipeline_managed defaults to True and sets
    that env var, so calls through the normal headless path are covered.
    The collision is only guaranteed again if a caller sets
    pipeline_managed=False on that call (or otherwise disables the managed
    hook) -- do not enable record_via_turnlifecycle=True against a real
    canonical session in that situation, for the reasons above.

    Returns the interface contract (see report): turn_id, causal_id, reply,
    rounds_used, self_adapted, elapsed_ms, tool_selection.
    """
    if user_id not in CANONICAL_USERS or not identity.ist_kanonische_sitzung(session_id, user_id):
        raise PipelineError("invalid canonical user/session")
    if not isinstance(message, str) or not message.strip():
        raise PipelineError("empty message")

    own_store = store or PrestageStore()
    t_start = time.perf_counter()
    lifecycle = None
    admission = None

    try:
        if record_via_turnlifecycle:
            from .. import turn_lifecycle  # coordinator-owned, imported not edited

            lifecycle = turn_lifecycle.TurnLifecycle(db, user_id, session_id)
            admission = lifecycle.begin(message)
            world = admission["context"]
            turn_id = admission["turn_id"]
            causal_id = admission["causal_id"]
        else:
            world = _gather_world_safe(db, session_id)
            turn_id = None
            causal_id = None

        recent_turns = [
            {"role": t.get("role"), "content": t.get("content")}
            for t in (world.get("own_recent") or [])[-3:]
        ]

        # Das Profil des ANWESENDEN Menschen -- dynamisch, je Zug neu gelesen.
        # Nicht zwischengespeichert: es wird autonom verdichtet, ein Cache
        # wuerde die Vorstufe mit einem veralteten Menschenbild fuettern.
        nutzerprofil = _profil_safe(db, user_id)

        # --- round 1 ---
        t0 = time.perf_counter()
        envelope = prestage.run_prestage(
            raw_prompt=message, world=world, current_user=user_id,
            current_user_profile=nutzerprofil,
            recent_turns=recent_turns, round_no=1,
        )
        prestage_ms = (time.perf_counter() - t0) * 1000.0

        selected_tools = tool_selection or [
            t for t in envelope.get("tool_selection", []) if isinstance(t, str) and t.startswith("mcp__clayverse__")
        ] or None
        if selected_tools is not None:
            # Wer da ist und wem was gehoert, darf nicht von der Auswahl eines
            # freien Modells abhaengen. Gemessen: auf "Was ist schiefgegangen?"
            # waehlte die Vorstufe menschen_profil NICHT, Zero suchte im
            # Gedaechtnis, fand nichts und forderte ein besseres Paket an --
            # obwohl die Antwort in menschen_profil()["bilanz"] stand.
            # Lesend, billig, und genau bei den Fragen zustaendig, bei denen
            # Raten am teuersten ist.
            for _pflicht in ("mcp__clayverse__menschen_profil",
                             "mcp__clayverse__wiki_zuordnung"):
                if _pflicht not in selected_tools:
                    selected_tools.append(_pflicht)

        t0 = time.perf_counter()
        zero = headless_zero.run_headless(
            envelope["caveman_prompt"], user_id=user_id, session_id=session_id,
            tool_selection=selected_tools,
        )
        zero_ms = (time.perf_counter() - t0) * 1000.0
        rounds_used = 1
        self_adapted = False
        paketurteil_entfernt = None

        # Markdown-fest: das Modell setzt die Notbremse fett, jedes Mal.
        # Gemessen an fuenf echten Beispielen, alle in ** gewickelt.
        # startswith() prueft Position 0 und traf deshalb nie -- die Zuege liefen
        # als Runde 1 durch, obwohl sie Zurueckweisungen waren, und der Zaehler
        # der Verhandlungsschleife war falsch.
        _bremse = re.match(r"^\s*[*_`#>\s]{0,6}" + re.escape(NEGOTIATION_SENTINEL),
                           zero["caveman_answer"])
        if _bremse:
            suggestion = zero["caveman_answer"][_bremse.end():].strip()
            # Fette Auszeichnung am Ende ebenfalls abstreifen, sonst steht sie
            # im Verbesserungsvorschlag und geht so in die naechste Runde.
            suggestion = re.sub(r"[*_`\s]+$", "", suggestion)
            t0 = time.perf_counter()
            envelope2 = prestage.run_prestage(
                raw_prompt=message, world=world, current_user=user_id,
                current_user_profile=nutzerprofil,
                recent_turns=recent_turns, round_no=2, zero_suggestion=suggestion,
            )
            prestage_ms += (time.perf_counter() - t0) * 1000.0
            t0 = time.perf_counter()
            zero = headless_zero.run_headless(
                envelope2["caveman_prompt"], user_id=user_id, session_id=session_id,
                tool_selection=selected_tools,
            )
            zero_ms += (time.perf_counter() - t0) * 1000.0
            rounds_used = MAX_ROUNDS
            self_adapted = True
            envelope = envelope2
            if zero["caveman_answer"].strip().startswith(NEGOTIATION_SENTINEL):
                # F74 hard counter: round 2 has no escape hatch in its own prompt.
                # If Zero used it anyway, that is a prompt-compliance failure to
                # surface loudly, not silently retry a third time.
                raise PipelineError(
                    "Zero used the negotiation sentinel on round 2 despite it being withdrawn -- "
                    "prompt compliance failure, not a data gap"
                )

        t0 = time.perf_counter()
        german = translator.translate_to_german(zero["caveman_answer"])
        translate_ms = (time.perf_counter() - t0) * 1000.0

        prestage_id = own_store.record_prestage_turn(
            turn_id=turn_id, session_id=session_id, user_id=user_id,
            raw_prompt=message, connected_systems={"status": "NOT_WIRED"},
            caveman_prompt=envelope["caveman_prompt"],
            tool_selection=envelope.get("tool_selection", []),
            memory_artefacts=envelope.get("memory_artefacts", []),
            outsourced=envelope.get("outsourced", []),
            user_intent=envelope.get("user_intent", ""),
            watch_out=envelope.get("watch_out", ""),
            hypotheses=envelope.get("hypotheses", []),
            counter_hypotheses=envelope.get("counter_hypotheses", []),
            prestage_model=envelope.get("prestage_model"),
            prestage_receipt=envelope.get("prestage_receipt", {}),
        )
        translation_id = own_store.record_translation(
            turn_id=turn_id, prestage_id=prestage_id,
            caveman_original=zero["caveman_answer"], german_translation=german["german_translation"],
            translator_model=german["translator_model"], translator_receipt=german["translator_receipt"],
        )

        if record_via_turnlifecycle and lifecycle is not None:
            lifecycle.complete(zero["caveman_answer"])

        total_ms = (time.perf_counter() - t_start) * 1000.0
        return {
            "turn_id": turn_id,
            "causal_id": causal_id,
            "prestage_id": prestage_id,
            "translation_id": translation_id,
            "reply": german["german_translation"],
            "caveman": zero["caveman_answer"],
            "rounds_used": rounds_used,
            "self_adapted": self_adapted,
            "tool_selection": selected_tools or [],
            "elapsed_ms": {
                "prestage_ms": round(prestage_ms, 1),
                "zero_ms": round(zero_ms, 1),
                "translate_ms": round(translate_ms, 1),
                "total_ms": round(total_ms, 1),
            },
        }
    except Exception:
        if record_via_turnlifecycle and lifecycle is not None:
            try:
                lifecycle.abort("pipeline_failure")
            except Exception:
                pass
        raise
    finally:
        if store is None:
            own_store.close()
