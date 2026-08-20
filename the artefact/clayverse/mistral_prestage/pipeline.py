from __future__ import annotations

import json
import time
from typing import Any

from .. import identity  # coordinator-owned, imported not edited
from .. import hyperposition  # coordinator-owned, imported not edited (read-only projector)
from . import headless_zero, prestage, translator
from . import reality_layer  # additive anti-confabulation check, default OFF -- see module docstring
import re

from .prestage import MAX_ROUNDS, NEGOTIATION_SENTINEL
from .store import PrestageStore

CANONICAL_USERS = {"gabriel", "andreas"}


class PipelineError(RuntimeError):
    pass


def _gather_world_safe(db, session_id: str, message: str = "") -> dict[str, Any]:
    """Read-only world assembly, no turn admission.

    `message` ist die Frage des Menschen und geht als `query` in assemble() --
    OHNE sie baut assemble den Korpus mit dem leeren Text und liefert immer
    []. Vorgabewert "" nur, damit alte Aufrufer nicht brechen; der Produktions-
    pfad gibt die Nachricht IMMER mit (siehe Modul-Historie 2026-08-20).

    Uses clayverse.retrieval.WorldAssembler directly instead of
    TurnLifecycle.begin_admission() so context can be gathered WITHOUT writing
    a turn. WorldAssembler.assemble() already has a no-active-turn fallback
    path (the "LEGACY_COMPATIBILITY" branch) for exactly this case -- it is
    not a hack, it is the path the module already ships for callers with no
    active causal turn.
    """
    from .. import retrieval  # coordinator-owned module, imported not edited

    assembler = retrieval.WorldAssembler(db)
    return assembler.assemble(session_id, resource_refs=[], query=message or "")


def _hyperposition_safe(world: dict[str, Any]) -> list[dict[str, Any]]:
    """Set-valued world-model readout over world['durable_memory'] (F1 Schritt A).

    Ausfallsicher wie die anderen *_safe-Helfer hier: ein Fehler in der
    Projektion darf den Zug nie kippen -- die Vorstufe bekommt dann einfach
    keinen Readout (leere Liste) statt eines abgebrochenen Zuges. MUSS auf dem
    VOLLEN world laufen, VOR jeder Kuerzung von durable_memory (siehe
    _vorstufen_world) -- sonst verliert das Weltmodell Belege, die die
    Kuerzung bereits entfernt hat.
    """
    try:
        return hyperposition.HyperpositionProjector.from_world(world)
    except Exception:
        return []


# ── Weltmodell-Fusion (2026-08-20) ────────────────────────────────────────
# Deckel: der Vorstufe-Kontext soll unter ~10k Zeichen bleiben (siehe unten).
_WM_MAX_ARTIKEL = 3      # nur die besten Korpustreffer
_WM_MAX_ACHSEN = 3       # je Artikel
_WM_MAX_WERTE = 4        # je Achse
# Achsen, die KEINE Lesart des Inhalts sind -- siehe Modul-Historie:
# `identitaet` traegt Artikelkennungen aus der Dublettenerkennung.
_WM_ACHSEN_AUS = ("identitaet",)


def _weltmodell_safe(world: dict[str, Any]) -> list[dict[str, Any]]:
    """Mehrdeutigkeiten aus wm_lesart zu den Korpustreffern dieses Zuges.

    Liefert Eintraege in der Form, die der `hyperposition`-Schluessel schon
    beschreibt: eine Relation mit einem ARRAY gleichzeitig gueltiger Lesarten,
    nie ein einzelner gesetzter Wert. Nur echte Mehrdeutigkeit (>= 2
    verschiedene Werte nach Entdopplung) wird gemeldet.
    """
    treffer = [t for t in (world.get("corpus") or []) if isinstance(t, dict)]
    if not treffer:
        return []
    import sys as _sys
    for _pfad in ("/opt/unifieddb", "/opt/clay-werkzeug", "/opt/clayverse/werkzeug"):
        if _pfad not in _sys.path:
            _sys.path.append(_pfad)
    try:
        import weltmodell as _wm
    except Exception:
        return []   # Werkzeug nicht eingehaengt -- kein Grund, den Zug zu kippen

    raus: list[dict[str, Any]] = []
    verbindung = None
    try:
        verbindung = _wm.verbinden(schreibend=False)
        for t in treffer[:_WM_MAX_ARTIKEL]:
            artikel_id = t.get("artikel_id")
            if not artikel_id:
                continue
            try:
                gelesen = _wm.lesen(verbindung, artikel_id, {})
            except Exception:
                continue
            achsen = 0
            for achse, lage in (gelesen.get("achsen") or {}).items():
                if achse in _WM_ACHSEN_AUS or achsen >= _WM_MAX_ACHSEN:
                    continue
                # gewaehlt UND kandidaten: eine vom Kontext gewaehlte Lesart
                # bleibt eine Lesart neben den anderen (GESETZ 1 des Moduls).
                roh = list(lage.get("kandidaten") or [])
                if isinstance(lage.get("gewaehlt"), dict):
                    roh.insert(0, lage["gewaehlt"])
                gesehen, facetten = set(), []
                for k in roh:
                    if not isinstance(k, dict):
                        continue
                    wert = k.get("wert")
                    if wert is None or wert in gesehen:
                        continue   # Entdopplung nach WERT -- siehe Modul-Historie
                    gesehen.add(wert)
                    facetten.append({"value": wert, "herkunft": k.get("quelle") or "wm_lesart"})
                    if len(facetten) >= _WM_MAX_WERTE:
                        break
                if len(facetten) < 2:
                    continue   # eine Lesart ist keine Mehrdeutigkeit
                raus.append({
                    "relation": f"{achse} von {artikel_id}",
                    "quelle": "wm_lesart",
                    "status": lage.get("status"),
                    "facets": facetten,
                    "truth_promoted": False,
                    "effect_authority": False,
                })
                achsen += 1
    except Exception:
        return raus
    finally:
        try:
            if verbindung is not None:
                verbindung.close()
        except Exception:
            pass
    return raus


# Zeichen-/Mengendeckel NUR fuer den Vorstufe-Pfad (F1 Schritt B). Gemessen
# 18.08.: world liegt bei ~27k Zeichen (own_recent 12,8k, durable_memory 7,7k,
# canonical_identity 5,5k, anwesender_mensch 1,1k, Rest winzig) und
# bremst/verwaesst die Vorstufe. Ziel: der an die Vorstufe gegebene Kontext
# unter ~10k Zeichen.
_VORSTUFE_MAX_CHARS = 10_000
_VORSTUFE_OWN_RECENT_N = 3
_VORSTUFE_DURABLE_MEMORY_N = 12
_VORSTUFE_OWN_RECENT_FELD_DECKEL = 800
_VORSTUFE_DURABLE_MEMORY_FELD_DECKEL = 300


def _vorstufen_world(world: dict[str, Any]) -> dict[str, Any]:
    """Schlanke Kopie von world NUR fuer den Vorstufe-Aufruf (F1 Schritt B).

    _gather_world_safe/WorldAssembler.assemble bleiben UNVERAENDERT -- andere
    Verbraucher (TurnLifecycle, engine.py) bekommen weiterhin das volle world.
    Diese Funktion baut nur die Kopie, die in prestage.run_prestage(world=...)
    geht: own_recent auf die letzten drei Zuege, durable_memory auf die
    juengsten Eintraege (WorldAssembler liefert sie bereits ts DESC sortiert),
    beide zusaetzlich mit einem Zeichen-Deckel je Feld. canonical_identity und
    anwesender_mensch bleiben unangetastet (klein und Pflicht laut Auftrag).
    corpus/cross_session_collision/retrieval_receipt sind laut Messung ohnehin
    winzig und bleiben unveraendert, ausser das Gesamtbudget greift noch.

    Baut ausschliesslich NEUE dicts/Listen -- veraendert world oder seine
    verschachtelten Objekte nicht, damit nichts anderes (z.B. ein spaeterer
    Aufrufer derselben world-Referenz) beschaedigt wird.
    """

    def _kurz(wert: Any, deckel: int) -> Any:
        if isinstance(wert, str) and len(wert) > deckel:
            return wert[:deckel] + "…[gekuerzt]"
        return wert

    own_recent = [
        {"role": t.get("role"), "content": _kurz(t.get("content"), _VORSTUFE_OWN_RECENT_FELD_DECKEL),
         "ts": t.get("ts")}
        for t in (world.get("own_recent") or [])[-_VORSTUFE_OWN_RECENT_N:]
        if isinstance(t, dict)
    ]
    durable_memory = [
        {"kind": m.get("kind"), "subject": m.get("subject"),
         "value": _kurz(m.get("value"), _VORSTUFE_DURABLE_MEMORY_FELD_DECKEL), "ts": m.get("ts")}
        for m in (world.get("durable_memory") or [])[:_VORSTUFE_DURABLE_MEMORY_N]
        if isinstance(m, dict)
    ]

    packed: dict[str, Any] = {
        "own_recent": own_recent,
        "durable_memory": durable_memory,
        "cross_session_collision": list(world.get("cross_session_collision") or []),
        "corpus": list(world.get("corpus") or []),
    }
    if world.get("retrieval_receipt") is not None:
        packed["retrieval_receipt"] = world["retrieval_receipt"]
    # Nie gekuerzt: ohne canonical_identity weiss die Vorstufe nicht, was Zero
    # ist; ohne anwesender_mensch nicht, mit wem gesprochen wird.
    if world.get("canonical_identity") is not None:
        packed["canonical_identity"] = world["canonical_identity"]
    if world.get("anwesender_mensch") is not None:
        packed["anwesender_mensch"] = world["anwesender_mensch"]

    def _groesse() -> int:
        return len(json.dumps(packed, ensure_ascii=False, default=str))

    # Sicherheitsnetz, falls die Feld-Deckel oben trotzdem nicht reichen (z.B.
    # eine sehr lange canonical_identity): erst das billigste weg -- corpus ist
    # naechste Runde neu abrufbar, cross_session_collision ist im
    # Vorstufe-Pfad wegen resource_refs=[] ohnehin fast immer leer.
    while _groesse() > _VORSTUFE_MAX_CHARS and packed["corpus"]:
        packed["corpus"] = packed["corpus"][:-1]
    while _groesse() > _VORSTUFE_MAX_CHARS and packed["cross_session_collision"]:
        packed["cross_session_collision"] = packed["cross_session_collision"][:-1]
    while _groesse() > _VORSTUFE_MAX_CHARS and packed["durable_memory"]:
        packed["durable_memory"] = packed["durable_memory"][:-1]
    while _groesse() > _VORSTUFE_MAX_CHARS and len(packed["own_recent"]) > 1:
        packed["own_recent"] = packed["own_recent"][1:]

    return packed


_PAKET_WORTE = ("need_better_package", "besseres paket", "das paket", "the package",
                "paket reicht", "package is enough", "kein bedarf")



def log_paketurteil(store, turn_id, session_id, kopf: str) -> None:
    """Zaehlt, wie oft Zero doch ueber das Paket geurteilt hat. Darf nie werfen."""
    try:
        store.db.executescript(
            "CREATE TABLE IF NOT EXISTS mv_paketurteil("
            "  id INTEGER PRIMARY KEY AUTOINCREMENT, ts REAL NOT NULL,"
            "  turn_id TEXT, session_id TEXT, entfernt TEXT);")
        store.db.execute(
            "INSERT INTO mv_paketurteil(ts,turn_id,session_id,entfernt) VALUES(?,?,?,?)",
            (time.time(), turn_id, session_id, kopf[:400]))
        store.db.commit()
    except Exception:
        pass  # Buchfuehrung darf einen Zug nie kippen


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



_ROH_VERMERK = (
    "⚠️ Die Uebersetzung ins Deutsche ist ausgefallen. Darunter steht Zeros "
    "Antwort im Originalton (Caveman-Englisch) -- unuebersetzt, aber "
    "vollstaendig. Lieber roh als verloren.\n\n"
)


def _uebersetzung_mit_rueckfall(own_store, turn_id, session_id, caveman: str) -> tuple[dict, bool]:
    """Uebersetzen; bei endgueltigem Ausfall den Originalton ausliefern.

    Die Uebersetzung ist ein Komfort, die Antwort ist die Leistung. Ein
    Komfort, der bei Ausfall die Leistung mitreisst, ist falsch verdrahtet.
    Gemessen: zwei von vier Zuegen gingen so verloren, NACHDEM Zero fertig war.
    """
    try:
        return translator.translate_to_german(caveman), False
    except Exception as fehler:
        _log_uebersetzungsausfall(own_store, turn_id, session_id, fehler)
        return ({"german_translation": _ROH_VERMERK + caveman,
                 "translation_id": None,
                 "_ausfall": f"{type(fehler).__name__}: {fehler}"}, True)


def _log_uebersetzungsausfall(store, turn_id, session_id, fehler) -> None:
    """Mitschreiben, nicht schweigen.

    Ein stiller Rueckfall waere hier besonders heimtueckisch: die Seite
    funktioniert, der Text sieht nur roh aus, und niemand merkt, dass der
    Uebersetzer seit Tagen tot ist.
    """
    try:
        store.db.executescript(
            "CREATE TABLE IF NOT EXISTS mv_uebersetzung_ausfall("
            "  id INTEGER PRIMARY KEY AUTOINCREMENT, ts REAL NOT NULL,"
            "  turn_id TEXT, session_id TEXT, fehler TEXT);")
        store.db.execute(
            "INSERT INTO mv_uebersetzung_ausfall(ts,turn_id,session_id,fehler) VALUES(?,?,?,?)",
            (time.time(), turn_id, session_id, f"{type(fehler).__name__}: {fehler}"[:300]))
        store.db.commit()
    except Exception:
        pass  # Buchfuehrung darf einen Zug nie kippen



def _moeglichkeitsraum_safe(text: str) -> dict | None:
    """Das Erwartungsfeld zur Frage. Ausfallsicher, aber nie stillschweigend.

    "Ein Raum mit nur einer Lesart ist kein Raum" -- das Feld meldet
    Einseitigkeit selbst (`einseitig: true`). Scheitert der Bau, bekommt die
    Vorstufe den GRUND zu sehen: ein fehlender Raum darf nicht wie ein leerer
    aussehen.
    """
    # /opt/unifieddb ist schreibgeschuetzt eingehaengt, steht aber nicht im
    # Suchpfad -- dort liegt das Paket `udb`. Ohne diese Zeile meldet das Feld
    # dauerhaft NICHT_GEBAUT, und zwar mit korrektem Grund.
    import sys as _sys
    for _pfad in ("/opt/unifieddb",            # das Paket udb
                  "/opt/clay-werkzeug",         # der Erfindungsmelder verdichtung.py (eingehaengt)
                  "/opt/clayverse/werkzeug"):  # derselbe Pfad ausserhalb des Containers
        if _pfad not in _sys.path:
            _sys.path.append(_pfad)
    try:
        from udb.abruf.moeglichkeitsraum import moeglichkeitsraum as _mr
        r = _mr(text, budget=6)
        return {"raum": r.get("raum"), "einseitig": r.get("einseitig"),
                "quelle_hypothesen": r.get("quelle_hypothesen"),
                "quelle_gegenseite": r.get("quelle_gegenseite")}
    except Exception as e:
        return {"status": "NICHT_GEBAUT", "grund": f"{type(e).__name__}: {e}"[:200]}


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
    # Wandzeit (time.time(), nicht perf_counter) zusaetzlich zu t_start:
    # effects/causal_episodes in wiki.db tragen Unix-Zeitstempel -- nur damit
    # laesst sich das Zeitfenster fuer die Lernschleife (Phase 2b, store.py
    # _effects_evidence) ueberhaupt bilden.
    turn_started_at = time.time()
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
            world = _gather_world_safe(db, session_id, message)
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
        erwartungsfeld = _moeglichkeitsraum_safe(message)

        # F1 Schritt A: Hyperposition-Weltmodell -- MUSS auf dem VOLLEN world
        # laufen, bevor Schritt B durable_memory kuerzt (siehe _vorstufen_world),
        # sonst verliert das Weltmodell Belege.
        # Zwei Quellen, EIN Kanal: die Projektion ueber durable_memory (bislang
        # live immer leer) und das gebaute wm_-Weltmodell zu den Korpustreffern.
        hyperposition_readout = _hyperposition_safe(world) + _weltmodell_safe(world)
        # F1 Schritt B: schlanke world-Kopie NUR fuer die Vorstufe -- world
        # selbst bleibt unveraendert (record_via_turnlifecycle=True liest
        # spaeter u.U. noch daraus, und andere Verbraucher der geteilten
        # WorldAssembler-Quelle sind davon so oder so nicht betroffen).
        vorstufe_world = _vorstufen_world(world)

        # Phase 2b Schritt 3 (Rueckspeisung): das gelernte "was-ist-falsch"
        # als schlanker Text in den Vorstufe-Kontext, BEVOR Runde 1 laeuft --
        # nur so kann es die Routing-Entscheidung noch beeinflussen. Darf nie
        # einen Zug kippen: own_store.gelernter_block() ist bereits intern
        # ausfallsicher (leerer String bei jedem Fehler), hier zusaetzlich
        # defensiv, falls store selbst die Methode (aeltere Version) nicht hat.
        try:
            gelernt_block = own_store.gelernter_block()
        except Exception:
            gelernt_block = ""

        # --- round 1 ---
        t0 = time.perf_counter()
        envelope = prestage.run_prestage(
            raw_prompt=message, world=vorstufe_world, current_user=user_id,
            current_user_profile=nutzerprofil, moeglichkeitsraum=erwartungsfeld,
            recent_turns=recent_turns, round_no=1,
            hyperposition=hyperposition_readout, gelernt=gelernt_block,
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
                raw_prompt=message, world=vorstufe_world, current_user=user_id,
                current_user_profile=nutzerprofil, moeglichkeitsraum=erwartungsfeld,
                recent_turns=recent_turns, round_no=2, zero_suggestion=suggestion,
                hyperposition=hyperposition_readout, gelernt=gelernt_block,
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

        # Erst hier, nachdem BEIDE Notbremsen-Pruefungen durch sind: sonst
        # koennte das Netz eine echte Nachforderung verstuemmeln und aus einer
        # berechtigten Zurueckweisung eine halbe Antwort machen.
        _sauber, paketurteil_entfernt = _ohne_paketurteil(zero["caveman_answer"])
        if paketurteil_entfernt:
            # Mitschreiben, nicht stillschweigen: solange hier etwas entfernt
            # wird, wirkt die Anweisung an das Modell nicht.
            log_paketurteil(own_store, turn_id, session_id, paketurteil_entfernt)

        t0 = time.perf_counter()
        german, roh_ausgeliefert = _uebersetzung_mit_rueckfall(
            own_store, turn_id, session_id, _sauber)
        translate_ms = (time.perf_counter() - t0) * 1000.0

        # Reality Layer (additive, default OFF -- CLAYVERSE_REALITY_CHECK=1):
        # scans the DELIVERED German reply for claims that contradict
        # canonical_identity's own non-LIVE status tags (compute nodes,
        # reputation/ERS -- the only closed, authoritative truth set this
        # pipeline has, see reality_layer.py's module docstring for the full
        # argument on why a general corpus-grounding checker was rejected).
        # Never touches the reply on any internal failure -- same fallback
        # ethic as every other _safe helper in this file.
        if reality_layer.reality_check_enabled():
            try:
                _realitaet_verdict = reality_layer.check_reply(
                    german.get('german_translation', ''), world.get('canonical_identity'))
                if not _realitaet_verdict.get('ok', True):
                    german['german_translation'] = reality_layer.annotate_if_violated(
                        german.get('german_translation', ''), _realitaet_verdict)
                    reality_layer.log_realitaetscheck(own_store, turn_id, session_id, _realitaet_verdict)
            except Exception:
                pass  # Realitaetspruefung darf einen Zug nie kippen

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
            # F1 Schritt Metakognik: durchgereicht fuer eine spaetere Persistenz
            # (Phase 2b, store.py). record_prestage_turn nimmt **fields entgegen
            # und ignoriert unbekannte Schluessel klaglos -- kein Crash, solange
            # store.py die Spalte noch nicht kennt.
            epistemik=envelope.get("epistemik", {}),
            # Phase 2b Schritt 1 (Ergebnis-Signal): self_adapted/roh_ausgeliefert
            # sind bereits berechnete Strukturmerkmale dieses Zuges (siehe oben);
            # reply_text ist die tatsaechlich ausgelieferte deutsche Antwort (fuer
            # den mechanischen Luecke-Marker-Scan in store.py); turn_started_at
            # setzt das Zeitfenster fuer den effects/causal_episodes-Best-Effort-Blick.
            self_adapted=self_adapted,
            translation_raw_fallback=roh_ausgeliefert,
            reply_text=german.get("german_translation", ""),
            turn_started_at=turn_started_at,
        )
        translation_id = own_store.record_translation(
            turn_id=turn_id, prestage_id=prestage_id,
            caveman_original=zero["caveman_answer"], german_translation=german["german_translation"],
            # .get() statt []: der Rueckfall-Dict aus _uebersetzung_mit_rueckfall()
            # traegt bei totem Uebersetzer weder Modell noch Quittung. Der harte
            # Zugriff warf dort KeyError und riss GENAU die Antwort mit, die der
            # Rueckfall retten sollte (gemessen 2026-08-20). Der Ausfallgrund
            # steht in _ausfall und wandert damit in die Quittung -- ein leeres
            # Modellfeld ist ehrlich, ein gekippter Zug ist es nicht.
            translator_model=german.get("translator_model") or "",
            translator_receipt=german.get("translator_receipt")
            or {"ausfall": german.get("_ausfall", "unbekannt"), "rueckfall": "roh"},
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
            "epistemik": envelope.get("epistemik", {}),
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
