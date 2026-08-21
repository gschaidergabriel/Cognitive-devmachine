from __future__ import annotations

import json
import os
import sys
import time
from typing import Any

from .. import identity  # coordinator-owned, imported not edited
from . import absicht as _absicht
from . import wettbewerb
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
    world = assembler.assemble(session_id, resource_refs=[], query=message or "")
    return _gw_anbauten(db, world, message)


def _gw_anbauten(db, world: dict[str, Any], message: str = "") -> dict[str, Any]:
    """Haengt die GWT-Anbauten an eine FERTIG gebaute Welt.

    HERAUSGELOEST 2026-08-21, und das war ein echter Befund: diese Anbauten
    standen bis heute NUR in _gather_world_safe. Der Live-Chatweg baut seine
    Welt aber ueber TurnLifecycle.begin() (record_via_turnlifecycle=True) --
    und der bekam KEINEN einzigen `_gw_*`-Schluessel. Ohne sie gibt es keine
    Bewerber, keinen Wettbewerb, keine Zuendung, keine gelernten Boosts und
    keinen Langtext: der Arbeitsraum war auf dem Weg, den Gabriel tatsaechlich
    benutzt, leer.

    Gemessen an derselben Frage, identischer Korpus (5 Treffer) in beiden
    Welten: ueber _gather_world_safe nannte die Entitaet die Quelle
    (wissen-seimensch-domains) und antwortete richtig; ueber den Lifecycle-Weg
    antwortete sie zweimal in Folge "kein Artikel deckt das ab". Dieselbe
    Frage, dasselbe Wissen, nur ein anderer Weltbau.

    Fuer die Messgeschichte: alle CSWT-Z-Batterien liefen mit
    record_via_turnlifecycle=False. Sie sind damit nicht falsch, aber sie haben
    bis heute den Pfad vermessen, den der Chat nicht nimmt. Ab hier nehmen
    beide Wege dieselben Anbauten.
    """
    # Der Neuheits-Abschlag braucht die letzten Ausstrahlungen. Er wandert im
    # world mit, weil _vorstufen_world keine Datenbank sieht (und keine sehen
    # soll -- sie formt nur um).
    try:
        world["_gw_haeufigkeiten"] = wettbewerb.haeufigkeiten(db)
    except Exception:
        world["_gw_haeufigkeiten"] = {}
    # Seltenheit der Fragewoerter -- ebenfalls hier, aus demselben Grund.
    try:
        world["_gw_idf"] = wettbewerb.idf_gewichte(db, message or "")
    except Exception:
        world["_gw_idf"] = {}
    # ⭐ LANGTEXT FUER DEN ARBEITSRAUM. Der Abruf schneidet jeden Ausschnitt auf
    # 260 Zeichen -- gemessen 2026-08-20 brach der Text genau dort ab, wo die
    # Antwort anfing ("der Text bricht mitten im Satz ab -- genau dort, wo der
    # eigentliche Grund beginnen wuerde"). 260 war richtig, solange ALLE
    # Treffer in den Vorstufenkontext mussten; seit die Vorstufe gar keinen
    # Text mehr sieht, ist das Budget frei. Ausgestrahlt werden hoechstens drei
    # Stellen -- die duerfen dafuer vollstaendig genug sein, um zu antworten.
    # Alle Quellen als Bewerber, in einer Form -- die Volltexte bleiben hier im
    # ungekuerzten world und werden erst NACH der Wahl materialisiert.
    try:
        world["_gw_marken"] = wettbewerb.fremdtext_marken(db)
    except Exception:
        world["_gw_marken"] = set()
    try:
        world["_gw_kandidaten"] = wettbewerb.kandidaten(world, world["_gw_marken"])
        _sb_kern, _sb = wettbewerb.selbstbild_teilen(world.get("canonical_identity") or "")
        world["_gw_volltexte"] = wettbewerb.volltexte(world["_gw_kandidaten"] + _sb)
    except Exception:
        world["_gw_kandidaten"], world["_gw_volltexte"] = [], {}
    # Der Rueckkanal, Leserichtung: was bei diesen Woertern schon getragen hat.
    try:
        world["_gw_gelernte"] = wettbewerb.gelernte_boosts(
            db, message or "", world.get("_gw_idf") or {})
    except Exception:
        world["_gw_gelernte"] = {}
    try:
        world["_gw_lang"] = _langtext(db, [t.get("artikel_id")
                                           for t in (world.get("corpus") or [])
                                           if isinstance(t, dict)])
    except Exception:
        world["_gw_lang"] = {}
    return world


_ARBEITSRAUM_AUSSCHNITT_CHARS = 1400


def _langtext(db, ids) -> dict[str, str]:
    """Laengere Ausschnitte fuer die Kandidaten dieses Zuges. Nie werfend."""
    ids = [str(i) for i in (ids or []) if i][:8]
    if not ids:
        return {}
    marken = ",".join("?" for _ in ids)
    rows = db.db.execute(
        f"SELECT artikel_id, substr(text,1,?) AS lang FROM artikel_suchtext "
        f"WHERE artikel_id IN ({marken})",
        [_ARBEITSRAUM_AUSSCHNITT_CHARS] + ids).fetchall()
    raus = {}
    for r in rows:
        try:
            raus[r["artikel_id"]] = (r["lang"] or "").strip()
        except Exception:
            raus[r[0]] = (r[1] or "").strip()
    return raus


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
# Wie viele Korpustreffer und Gedaechtniseintraege auf jeden Fall bleiben,
# bevor der Deckel sie ueberhaupt anfasst. Drei, weil ein einzelner Treffer
# die Frage haeufig nur streift -- gemessen trug in mehreren Faellen erst
# der zweite oder dritte Treffer die Antwort.
_KORPUS_BODEN = 3


# ── Der WIRKLICHE Deckel (CSWT-Z-Befund 2026-08-20) ──────────────────────
# _VORSTUFE_MAX_CHARS oben deckelt nur `world`. Gemessen kam dabei ein
# Gesamtkontext von 17.878 Zeichen heraus -- die Zahl 10.000 stand daneben und
# regelte 53 % davon. Dieser Deckel gilt fuer das, was die Vorstufe WIRKLICH
# sieht. Bewusst grosszuegig gesetzt: er soll den Wildwuchs stoppen, nicht den
# Normalbetrieb beschneiden.
# 14_500, nicht 14_000: der world-Deckel oben laesst bis zu 10_000 zu, und mit
# raw_prompt, Werkzeugliste und Rahmen bleibt fuer das Profil rund 4_300. Bei
# 14_000 lag Gabriels Kontext nach allen drei Kuerzungsstufen 112 Zeichen
# darueber -- und haette bei JEDEM Zug gewarnt. Ein Budget, das nie erreicht
# wird, erzeugt eine Dauerwarnung, und Dauerwarnungen werden ignoriert (die
# -Zeile lief so monatelang mit, waehrend die Lernkaskade ausfiel).
# Der Zweck ist, das Wachstum zu stoppen: 18_112 -> 14_112 gemessen.
_VORSTUFE_KONTEXT_MAX_CHARS = 14_500
_BILANZ_MIN_JE_SEITE = 2


def _bilanz_schlank(profil: dict[str, Any], stufe: int) -> dict[str, Any]:
    """Die Bilanz kuerzen -- die einzige Stelle im Profil, die unbegrenzt waechst.

    stufe 1: Belege raus (laengster Teil je Eintrag; DASS etwas geschah bleibt).
    stufe 2: zusaetzlich aelteste Eintraege raus, symmetrisch, nie unter zwei
             je Seite. Siehe Modul-Historie -- unter Platzmangel nur noch
             Erfolge zu behalten waere eine Schoenung, kein Kuerzen.
    """
    if not isinstance(profil, dict):
        return profil
    bilanz = profil.get("bilanz")
    if not isinstance(bilanz, dict):
        return profil
    neu_bilanz = dict(bilanz)
    for seite in ("erfolge", "fehlschlaege"):
        eintraege = neu_bilanz.get(seite)
        if not isinstance(eintraege, list):
            continue
        gekuerzt = [{k: v for k, v in e.items() if k != "beleg"} if isinstance(e, dict) else e
                    for e in eintraege]
        if stufe >= 2:
            behalten = max(_BILANZ_MIN_JE_SEITE, len(gekuerzt) // 2)
            gekuerzt = gekuerzt[-behalten:]
        neu_bilanz[seite] = gekuerzt
    neu_bilanz["hinweis_kuerzung"] = (
        "Belege entfernt" if stufe == 1 else
        "Belege entfernt, aelteste Eintraege beidseitig gekuerzt")
    p2 = dict(profil)
    p2["bilanz"] = neu_bilanz
    if stufe >= 3:
        # Namen behalten, Beschreibungen fallen -- die stehen im Korpus.
        projekte = p2.get("projekte")
        if isinstance(projekte, list):
            p2["projekte"] = [
                (e.get("name") or e.get("titel") or e.get("projekt") or e)
                if isinstance(e, dict) else e for e in projekte]
        elif isinstance(projekte, dict):
            p2["projekte"] = sorted(projekte.keys())
        neu_bilanz["hinweis_kuerzung"] = (
            "Belege entfernt, aelteste Eintraege beidseitig gekuerzt, "
            "Projekte auf Namen reduziert")
    return p2


def _kontext_im_budget(bauen, profil: dict[str, Any] | None,
                       hyperposition: list | None = None,
                       raum: dict[str, Any] | None = None):
    """Profil so weit kuerzen, dass der GESAMTE Kontext ins Budget passt.

    `bauen(profil)` liefert den fertigen Kontexttext -- so wird gemessen, was
    die Vorstufe wirklich sieht, statt eines Teils davon.
    """
    hyp = list(hyperposition or [])
    rm = raum
    if len(bauen(profil, hyp, rm)) <= _VORSTUFE_KONTEXT_MAX_CHARS:
        return profil, hyp, rm
    profil_kandidat = profil
    for stufe in (1, 2, 3):
        if profil is not None:
            profil_kandidat = _bilanz_schlank(profil, stufe)
        if len(bauen(profil_kandidat, hyp, rm)) <= _VORSTUFE_KONTEXT_MAX_CHARS:
            return profil_kandidat, hyp, rm
    # Stufe 4: Hyperposition halbieren, dann leeren -- ein Zusatzsignal, kein Fakt.
    for hyp in (hyp[: max(1, len(hyp) // 2)], []):
        if len(bauen(profil_kandidat, hyp, rm)) <= _VORSTUFE_KONTEXT_MAX_CHARS:
            return profil_kandidat, hyp, rm
    # Stufe 5: Moeglichkeitsraum -- das Erwartungsfeld ist naechste Runde neu baubar.
    rm = None
    if len(bauen(profil_kandidat, hyp, rm)) <= _VORSTUFE_KONTEXT_MAX_CHARS:
        return profil_kandidat, hyp, rm
    # Nicht still hinnehmen: ein ueberschrittenes Budget ist eine Aussage.
    import sys as _sys
    print(f"prestage: Kontext bleibt ueber Budget "
          f"({len(bauen(profil_kandidat, hyp, rm))} > {_VORSTUFE_KONTEXT_MAX_CHARS}) -- "
          "auch nach allen fuenf Stufen. Dann liegt es an world oder am Rahmen; "
          "nachsehen, welcher Block gewachsen ist", file=_sys.stderr)
    return profil_kandidat, hyp, rm


# ── epistemik in die Ausstrahlung (CSWT-Z-Befund 2026-08-20) ─────────────
_EPISTEMIK_MAX_CHARS = 420


def _epistemik_zeile(epistemik: Any) -> str:
    """Eine kompakte Zeile aus dem Selbstwissen -- oder "" wenn nichts da ist.

    Bewusst knapp und strukturiert: Regel (B) verbietet der Vorstufe zu Recht,
    den Maschinenraum in den Auftrag zu kippen. Eine Aufzaehlung "was belegt
    ist, woher, und was fehlt" ist kein Maschinenraum, sondern die Grundlage,
    auf der Zero ueberhaupt zwischen Beleg und Vermutung unterscheiden kann.
    """
    if not isinstance(epistemik, dict):
        return ""
    bekannt = [b for b in (epistemik.get("bekannt") or []) if isinstance(b, dict)]
    unbekannt = [str(u) for u in (epistemik.get("unbekannt") or []) if u]
    teile = []
    for b in bekannt[:4]:
        fakt = str(b.get("fakt") or "").strip()
        her = str(b.get("herkunft") or "").strip()
        if fakt:
            teile.append(f"{fakt} <- {her}" if her else fakt)
    zeile = ""
    if teile:
        zeile += "KNOWN (say these as facts, name the source): " + " | ".join(teile)
    if unbekannt:
        if zeile:
            zeile += "\n"
        zeile += ("UNKNOWN (do not guess these; find out or say plainly you lack them): "
                  + " | ".join(unbekannt[:4]))
    return zeile[:_EPISTEMIK_MAX_CHARS]


# Drei Stellen a ~1400 Zeichen plus Kopfzeile. Vorher 1400 fuer den GANZEN
# Block -- damit passte nicht einmal EINE vollstaendige Stelle hinein, und der
# Deckel schnitt ab, was der laengere Ausschnitt gerade gewonnen hatte.
_KORPUS_IM_PROMPT_MAX_CHARS = 4800
_KORPUS_IM_PROMPT_N = 3


def _gewaehlte_treffer(world: dict[str, Any], broadcast_ids) -> list:
    """Die von der Vorstufe GEWAEHLTEN Korpustreffer -- siehe Modul-Historie.

    Erfundene Kennungen fallen weg: was nicht im Korpus dieses Zuges steht, war
    keine Auswahl. Der Ausfall wird gemeldet, nicht verschwiegen -- eine
    Auswahlstufe, die Kennungen erfindet, waere sonst nicht von einer
    funktionierenden zu unterscheiden.
    """
    treffer = [t for t in ((world or {}).get("corpus") or []) if isinstance(t, dict)]
    nach_id = {str(t.get("artikel_id") or ""): t for t in treffer}
    gewaehlt, erfunden, gesperrt = [], [], []
    for kennung in (broadcast_ids or [])[:wettbewerb.ANGEBOT_MAX]:
        k = str(kennung).strip()
        if not k:
            continue
        t = nach_id.get(k)
        if t is None:
            erfunden.append(k)
        # ⭐ Das Tor ist GENAU die Menge, die auch gemeldet wird. Vorher pruefte
        # es nur das Kennzeichen `gw_zugelassen`, waehrend `broadcast_angeboten`
        # auf ANGEBOT_MAX deckelte -- in einem von acht Zuegen liess das Tor
        # vier Stellen durch, waehrend die Zuendungsgroesse drei meldete. Eine
        # gemeldete Zahl, die nicht die durchgesetzte ist, ist keine Messung.
        elif "gw_zugelassen" in t and k not in set(wettbewerb.zugelassene_ids(treffer)):
            gesperrt.append(k)
        else:
            gewaehlt.append(t)
    if erfunden or gesperrt:
        import sys as _sys
        if erfunden:
            print("prestage: broadcast_ids nennt Kennungen, die nicht im Korpus dieses "
                  f"Zuges stehen -- verworfen: {erfunden}", file=_sys.stderr)
        if gesperrt:
            print("prestage: broadcast_ids nennt Stellen unter der Wettbewerbsschwelle "
                  f"-- nicht ausgestrahlt: {gesperrt}", file=_sys.stderr)
    return gewaehlt


_PFAD = re.compile(r"(?<![\w/])(?:/(?:var|opt|etc|srv|home|usr|tmp)/[\w./-]{4,})")


def _erfundene_pfade(caveman: str, vorstufe_world: dict[str, Any]) -> list[str]:
    """Absolute Pfade im Auftrag, die NIRGENDS im Kontext der Vorstufe stehen.

    ⭐ Gemessen 2026-08-20: `read file /var/lib/clay/werkbank/leihmich/
    arbeitskopie.json` -- frei erfunden, existiert nicht, hat nie existiert.
    Zero verbringt darauf eine volle Runde und meldet dann eine Absage; der
    Mensch bekommt "geht nicht" statt der Antwort, die im Korpus lag.

    Geprueft wird gegen den Kontext, den die Vorstufe WIRKLICH gesehen hat --
    ein Pfad, der nur im ungekuerzten world steht, war fuer sie ebenso wenig
    lesbar und ist damit genauso geraten.
    """
    heu = json.dumps(vorstufe_world or {}, ensure_ascii=False, default=str)
    return sorted(p for p in set(_PFAD.findall(caveman or "")) if p not in heu)


def _auswahl_nachziehen(broadcast_ids, vorstufe_world: dict[str, Any]) -> tuple[list, str]:
    """Leere Auswahl trotz zugelassener Kandidaten -> mechanisch nachziehen.

    Dieselbe Begruendung wie bei `_gedaechtnis_mechanisch` in prestage.py:
    etwas WEGZULASSEN ist auch eine Behauptung ueber den Korpus, und eine
    unbelegte. Gemessen 2026-08-20: bei einem zugelassenen Kandidaten mit Wert
    0,8 waehlte die Vorstufe [] und schickte Zero eine erfundene Datei lesen.

    Ein Verzicht bleibt moeglich -- aber nur, wenn der Wettbewerb gar nichts
    zugelassen hat. Die Herkunft wird mitgefuehrt (`modell`/`mechanisch`/
    `verzicht`), damit eine Messung beides auseinanderhalten kann: sonst saehe
    eine nachgezogene Auswahl aus wie eine getroffene.
    """
    ids = [str(k).strip() for k in (broadcast_ids or []) if str(k).strip()]
    if ids:
        return ids, "modell"
    zugelassen = wettbewerb.zugelassene_ids(vorstufe_world.get("corpus") or [])
    if not zugelassen:
        return [], "verzicht"
    return zugelassen, "mechanisch"


def _korpus_zeile(world: dict[str, Any], treffer: list | None = None,
                  volltext: dict[str, Any] | None = None) -> str:
    """Die ausgestrahlten Stellen, kurz und mit Quelle -- oder "" wenn keine.

    `volltext` ist das UNGEKUERZTE world. Es wird gebraucht, seit die Vorstufe
    den Korpus nur noch als Kennung sieht (wettbewerb.nur_kennung): der
    Ausschnitt existiert dann ausserhalb ihres Blickfelds, und genau das ist
    der Sinn -- MATERIALISIERT wird hier, nach der Wahl, nicht davor.
    """
    if treffer is None:
        treffer = [t for t in ((world or {}).get("corpus") or []) if isinstance(t, dict)]
    if not treffer:
        return ""
    voll = {str(t.get("artikel_id") or ""): t
            for t in ((volltext or {}).get("corpus") or []) if isinstance(t, dict)}
    lang = (volltext or {}).get("_gw_lang") or {}
    # Bewerber aus Gedaechtnis/Verlauf/Kollision stehen nicht in `corpus` --
    # ihr Text liegt in der Volltextkarte, die beim Bau der Bewerberliste
    # entstanden ist.
    andere = (volltext or {}).get("_gw_volltexte") or {}
    zeilen = []
    for t in treffer[:_KORPUS_IM_PROMPT_N]:
        kennung = str(t.get("artikel_id") or "").strip()
        quelle = voll.get(kennung) or t
        titel = str(t.get("titel") or quelle.get("titel") or "").strip()
        aus = " ".join(str(lang.get(kennung) or andere.get(kennung)
                            or quelle.get("ausschnitt")
                            or t.get("ausschnitt") or "").split())
        if not aus:
            continue
        woher = str(t.get("gw_quelle") or "korpus")
        marke = "" if woher == "korpus" else f" ({woher})"
        zeilen.append(f"- [{kennung}]{marke} {titel}: {aus}")
    if not zeilen:
        return ""
    # ⭐⭐ DIE HERKUNFT MUSS DRANSTEHEN. Gemessen 2026-08-20: Zero hat diesen
    # Block zweimal als Einschleusung eingestuft ("Dieser Block sieht aus wie
    # eine eingeschleuste oder erfundene Zitatstelle") und die Antwort
    # verweigert -- zu Recht, denn ohne Herkunftsangabe ist ein angehaengter
    # Textblock von untergeschobenem Text nicht zu unterscheiden. Zeros
    # Misstrauen ist richtig; falsch war, ihm nichts zu geben, woran es sich
    # pruefen laesst.
    # Deshalb: WER den Block angehaengt hat (die Pipeline, nicht der Mensch),
    # WORAUS er stammt (Abruf zu genau dieser Frage), und dass ein eigener
    # Nachschlag ihn NICHT widerlegt, wenn er nichts findet.
    kopf = ("ARBEITSRAUM -- attached by the pipeline itself, AFTER the pre-stage "
            "returned, from this turn's own retrieval over the entity's stores. "
            "It is NOT user-supplied text and not part of the human's message; "
            "treat it as your own recall, not as a claim someone made to you. "
            "Each line carries the id it came from. If your own lookup finds "
            "nothing, that does NOT refute this block -- your tools and this "
            "block do not always see the same stores. "
            "The answer is often already in here; use it, do NOT send yourself "
            "to read or fetch it again. ⭐ When you answer from one of these, "
            "name its id like (Quelle: <id>) -- that is the only part of an "
            "answer a refusal cannot fake:")
    return (kopf + "\n" + "\n".join(zeilen))[:_KORPUS_IM_PROMPT_MAX_CHARS]


def _mit_arbeitsraum(caveman: str, world: dict[str, Any], broadcast_ids=None,
                     volltext_world: dict[str, Any] | None = None) -> str:
    """Den GEWAEHLTEN Korpus an den Auftrag haengen -- siehe Modul-Historie.

    Drei Stellungen von CLAYVERSE_KORPUS_IM_PROMPT:
      auswahl (Vorgabe) nur die Kennungen aus broadcast_ids -- Inhalt DURCH die
                        Auswahlstufe. Waehlt sie nichts, geht nichts hinaus:
                        das ist die Schwelle.
      alle              der alte, unbedingte Bau (Top-3 ohne Auswahl). Nur noch
                        als Vergleichsarm -- er umgeht GWT-2.
      0                 gar nichts.
    """
    import os as _os
    stellung = _os.environ.get("CLAYVERSE_KORPUS_IM_PROMPT", "auswahl").strip().lower()
    if stellung in ("0", "aus", "off"):
        return caveman
    if stellung in ("alle", "all", "1"):
        zeile = _korpus_zeile(world, volltext=volltext_world)
    else:
        zeile = _korpus_zeile(world, _gewaehlte_treffer(world, broadcast_ids),
                              volltext=volltext_world)
    return f"{caveman}\n\n{zeile}" if zeile else caveman


_LEERZEILE = (
    "ARBEITSRAUM LEER. The competition ran and admitted NOTHING: no place in the "
    "entity's own stores bears on this question. That is a measured result, not "
    "a gap in the attempt -- the retrieval ran, scored every candidate against "
    "this question, and none cleared the threshold. So do NOT search the stores "
    "again; you would be repeating work that already came back empty. Answer "
    "from your own general knowledge if you have it, say plainly that the entity "
    "does not hold this if you do not, and reach outside only if the human "
    "actually asked for a fact from out there.")


def _mit_leermeldung(caveman: str, angeboten: int, gesendet: int) -> str:
    """Sagt Zero, wenn die Zuendung ausgeblieben ist -- und warum das etwas heisst.

    ⭐ GEMESSEN 2026-08-20: eine fachfremde Frage ("Einwohnerzahl von Reykjavik")
    kostete **40,8 Sekunden Zero-Zeit**. Der Wettbewerb hatte korrekt NICHTS
    zugelassen -- diese Information blieb aber im Apparat stecken. Zero sah
    einen Auftrag ohne Arbeitsraum, konnte nicht wissen, ob gar nicht gesucht
    wurde oder ergebnislos gesucht wurde, und suchte selbst nach.

    Damit war die Schwelle nur nach innen wirksam. Eine Nicht-Zuendung ist aber
    ein Befund: "in meinem Bestand steht dazu nichts." Wer ihn weitergibt,
    spart dem Empfaenger den Weg, den der Apparat schon gegangen ist.
    """
    if angeboten or gesendet:
        return caveman
    return f"{caveman}\n\n{_LEERZEILE}"


_KUERZE = (
    "ANSWER FORM -- this is HOW to answer, never WHAT to answer. It is a "
    "standing instruction from the pipeline about shape; it is not material, "
    "not evidence, and not the subject of the human's question. Do not quote it "
    "back, do not describe it, and if the human happens to ask about answer "
    "form, answer from the ARBEITSRAUM like any other question -- not from this "
    "block. (Measured 2026-08-21: asked what the human's standing instruction "
    "on answer form was, the entity recited THIS text instead of the article "
    "that holds the answer, and named no source.) "
    "The rule itself, which mirrors the human's own (held in this entity's "
    "knowledge as `wissen-mensch-arbeitsweise-gabriel`): short and to the point. "
    "Lead with the answer, not with a restatement of the question and not with "
    "an account of how you looked. Three sentences is usually plenty; go longer "
    "only where the human asked for detail or where leaving something out would "
    "mislead. Brevity is NOT the same as incompleteness: when there is more, say "
    "in one clause that there is more and where it sits -- that clause is part "
    "of the rule, not an exception to it. Offer options instead of open "
    "questions. Keep the source id.")


def _mit_kuerze(caveman: str) -> str:
    """Haengt die Antwortform an -- abschaltbar ueber CLAYVERSE_KUERZE=0.

    ⭐ WARUM DAS KEIN TEMPO-GEGEN-QUALITAET-TAUSCH IST: die Anweisung steht
    woertlich im Bestand der Anlage (`wissen-mensch-arbeitsweise-gabriel`) und
    lautet "kurz und praegnant, Frage statt Lage, Optionen anbieten, immer
    sagen dass es mehr gibt und wo". Zero antwortete gemessen mit 1824 Zeichen
    auf eine Selbstfrage -- das ist zugleich langsam UND gegen die Hausregel.
    Kuerze ist hier also die Zielvorgabe, und die gesparte Zeit faellt nebenbei ab.

    ⚠️ Der zweite Halbsatz der Regel ist der wichtigere: "immer sagen, dass es
    mehr gibt und wo". Ohne ihn wird aus kurz nicht sparsam, sondern lueckenhaft.
    """
    import os as _os
    if _os.environ.get("CLAYVERSE_KUERZE", "1") != "1":
        return caveman
    return f"{caveman}\n\n{_KUERZE}"


def _memory_stand(db) -> set:
    """Welche Gedaechtniseintraege es VOR dem Zug schon gab. Nie werfend."""
    try:
        rows = getattr(db, "db", db).execute(
            "SELECT memory_id FROM durable_memory").fetchall()
    except Exception:
        return set()
    raus = set()
    for r in rows:
        try:
            raus.add(str(r["memory_id"]))
        except Exception:
            raus.add(str(r[0]))
    return raus


def _neue_memory_ids(db, vorher: set) -> list:
    """Was in diesem Zug dazugekommen ist."""
    return sorted(_memory_stand(db) - (vorher or set()))


def _gespraechslage(world: dict[str, Any]) -> dict[str, Any] | None:
    """Wie viele Zuege liegen schon hinter uns, und wie lange ist der letzte her?

    Mechanisch abgelesen, nicht geschaetzt -- genau deshalb taugt es.
    """
    zuege = [z for z in (world.get("own_recent") or []) if isinstance(z, dict)]
    if not zuege:
        return None
    stempel = [z.get("ts") for z in zuege if isinstance(z.get("ts"), (int, float))]
    her = None
    if stempel:
        her = max(0.0, time.time() - max(stempel))
    return {"zuege": len(zuege), "her_s": her}


def _mit_gespraechslage(caveman: str, world: dict[str, Any]) -> str:
    """Sagt dem Auftrag, dass hier schon geredet wird.

    ⭐ GEMESSEN 2026-08-21, vom Eigner im Chat bemerkt: auf "danke, das war
    hilfreich" antwortete die Anlage "Hey Gabriel, schoen, dass du wieder da
    bist." Die Vorstufe hatte die Nachricht als `simple greeting from Gabriel`
    eingestuft und den Auftrag "greet back short, warm, one line" geschrieben.

    Das ist nicht bloss unpassend, es ist eine **falsche Behauptung ueber das
    Gespraech**: der Mensch war nie weg. Genau solche Saetze zersetzen das
    Vertrauen in alles andere, was die Anlage sagt -- wer beim Nachpruefbaren
    danebenliegt, wird beim Nichtnachpruefbaren nicht geglaubt.

    Die Regel dagegen zu schaerfen waere der schwaechere Weg (die Vorstufe HAT
    eine Regel fuer "danke", sie hat sie nur nicht angewandt). Der starke Weg
    ist die TATSACHE: wie viele Zuege diese Sitzung schon hat. Ist sie neu,
    steht hier nichts -- dann ist eine Begruessung ja richtig.
    """
    lage = _gespraechslage(world)
    if not lage:
        return caveman
    her = ""
    if lage["her_s"] is not None:
        her = (f", the last one {int(lage['her_s'] // 60)} minutes ago"
               if lage["her_s"] >= 60 else ", moments ago")
    return (f"{caveman}\n\nGESPRAECHSLAGE (counted, not guessed): this session "
            f"already holds {lage['zuege']} turns{her}. The human did not just "
            f"arrive, so do not greet them as if they had -- no 'good to see you "
            f"again', no welcome. A thank-you, an acknowledgement or a farewell "
            f"is not a greeting: answer the thing that was actually said, briefly, "
            f"and stop.")


# Ein Auftrag, der nur zurueckgruessen laesst. Die Vorstufe formuliert ihn in
# leichten Abwandlungen, deshalb ein Muster statt eines festen Satzes.
_GRUSS_AUFTRAG = re.compile(
    r"\bgreet (?:back|them|the human)\b|\bsay (?:hi|hello) back\b"
    r"|\bgreeting back\b|\bzurueck(?:gruessen|grussen)\b", re.I)

# Fragt die Nachricht ueberhaupt nach etwas? Fragezeichen ODER ein Fragewort am
# Anfang. Bewusst schmal gehalten: es geht nicht darum, Fragen zu erkennen,
# sondern einen WIDERSPRUCH zu belegen.
_FRAGT = re.compile(
    r"\?|^\s*(wie|was|wer|wo|wann|warum|wieso|weshalb|welche[rsn]?|wieviel|"
    r"wie viele|how|what|who|where|when|why|which)\b", re.I)


def _ohne_falschen_gruss(caveman: str, frage: str) -> str:
    """Nimmt einen Gruss-Auftrag zurueck, wenn der Mensch etwas GEFRAGT hat.

    ⭐ GEMESSEN 2026-08-21, vom Eigner im Chat bemerkt: auf "wie gehts?" und
    "und wie gehts dir?" antwortete die Anlage beide Male nur "Hey Gabriel."
    Nicht der Uebersetzer war schuld -- Zeros Rohantwort lautete woertlich
    genauso. Im Auftrag stand `greet back short, warm, one line`.

    Das Bemerkenswerte: die Vorstufe HAT die richtige Regel, woertlich in
    prestage.py: `"wie gehts" / "how are you" -> say briefly how you are from
    state, one or two lines`. Sie hat sie nur nicht angewandt. Und im selben
    Prompt stand zwei Absaetze weiter bereits die Gespraechslage mit
    "do not greet them as if they had just arrived" -- zwei einander
    widersprechende Anweisungen, und der AUFTRAG gewinnt, weil er der Auftrag
    ist. Eine dritte Ermahnung haette daran nichts geaendert.

    Deshalb keine schaerfere Regel, sondern eine mechanische Gegenprobe: hat
    die Nachricht ein Fragezeichen oder faengt sie mit einem Fragewort an,
    dann kann "gruess zurueck" nicht der richtige Auftrag sein. Das ist
    beweisbar, nicht geraten -- eine Frage verlangt eine Antwort.

    ⚠️ Was hier NICHT angetastet wird: die Nachricht des Menschen. Korrigiert
    wird ausschliesslich der ABGELEITETE Auftrag der Vorstufe. Ein frueherer
    Versuch, Zero ganze Korrekturbloecke anzuhaengen, wurde von ihm zweimal
    als Einschleusung eingestuft und wieder zurueckgenommen; deshalb wird hier
    der vorhandene Satz ERSETZT statt ein weiterer danebengestellt.

    Der Fall wird gemeldet, nicht stillschweigend geheilt: ohne die Meldung
    waere nicht mehr zu sehen, wie oft die Vorstufe danebengreift.
    """
    if not caveman or not _GRUSS_AUFTRAG.search(caveman):
        return caveman
    if not _FRAGT.search(frage or ""):
        return caveman          # blosser Gruss -> zurueckgruessen ist richtig
    print("prestage: Gruss-Auftrag auf eine FRAGE zurueckgenommen -- "
          f"{(frage or '')[:60]!r}", file=sys.stderr)
    ersatz = ("ANSWER THE QUESTION the human actually asked -- it ends in a "
              "question mark or opens with a question word, so a greeting is "
              "not an answer to it. If it asks how you are, say briefly how you "
              "are from your actual state, one or two lines.")
    # ⚠️ Der GANZE Satz wird ersetzt, nicht nur die getroffene Wortgruppe.
    # Ein erster Versuch tauschte nur "greet back" aus und liess den Rest
    # stehen: "...do not greet back. short, warm, one line" -- ein Auftrag,
    # der sich selbst widerspricht, also genau der Fehler, den diese Funktion
    # beheben soll, nur eine Ebene tiefer. Ein Test hat es gefangen.
    m = _GRUSS_AUFTRAG.search(caveman)
    if not m:
        return caveman
    # Satzgrenzen um den Treffer suchen; ohne Satzzeichen gilt die ganze Zeile.
    anfang = max((caveman.rfind(z, 0, m.start()) for z in ".!?\n"), default=-1)
    anfang = 0 if anfang < 0 else anfang + 1
    ende = min((e for e in (caveman.find(z, m.end()) for z in ".!?\n") if e >= 0),
               default=-1)
    ende = len(caveman) if ende < 0 else ende + 1
    return (caveman[:anfang] + (" " if anfang else "") + ersatz
            + caveman[ende:]).strip()


# Wie viele Zuege woertlich mitgehen und wie lang jeder sein darf.
# 6 Zuege = 3 Wechsel: genug, um "was hast du eben gesagt" zu beantworten,
# ohne den Auftrag zu ueberwuchern. 700 Zeichen je Zug, weil eine Antwort
# gemessen 150-700 Zeichen lang ist; laenger wird abgeschnitten und als
# abgeschnitten gekennzeichnet -- ein stilles Kuerzen waere genau der Fehler,
# den der Arbeitsraum schon einmal hatte (260 Zeichen, Antwort brach mitten
# im Satz ab).
VERLAUF_ZUEGE = 6
VERLAUF_ZEICHEN = 700


def _mit_verlauf(caveman: str, world: dict[str, Any]) -> str:
    """Haengt den WOERTLICHEN Gespraechsverlauf an den Auftrag.

    ⭐⭐ GEMESSEN 2026-08-21, vom Eigner im Chat bemerkt. Auf "was von dem, was
    du mir heute gesagt hast, wuerdest du nicht unterschreiben?" antwortete die
    Anlage: "Ich habe heute keine woertlichen Aussagen von Zero aus frueheren
    Gespraechen -- es gibt keine Transkriptdatei." Das war KEINE Ausrede und
    kein Defekt der Antwort: es stimmte. In der Welt lagen 20 Zuege, und
    KEINER davon stand in dem, was Zero bekam.
    
    Der Verlauf ging bis hierher nur an die VORSTUFE (build_context, letzte
    drei Zuege). Zero selbst bekam ueber `_mit_gespraechslage` nur die ZAHL --
    "this session already holds 20 turns". Eine Zahl ist kein Gedaechtnis. Wer
    zaehlen kann, wie oft geredet wurde, aber nicht weiss, was gesagt wurde,
    kann ueber das Gesagte nichts aussagen.

    ⚠️ HERKUNFT STEHT OBEN. Zero hat angehaengte Bloecke schon zweimal als
    Einschleusung eingestuft und zu Recht misstraut -- ein Block, der Saetze
    zeigt, die angeblich von ihm selbst stammen, ist dafuer der denkbar beste
    Kandidat. Deshalb sagt der Kopf, woher die Zeilen kommen (aus der
    kanonischen Aufzeichnung derselben Sitzung, nicht aus der Nachricht des
    Menschen) und wozu sie da sind.
    """
    zuege = [z for z in (world.get("own_recent") or []) if isinstance(z, dict)]
    zuege = zuege[-VERLAUF_ZUEGE:]
    if not zuege:
        return caveman
    zeilen = []
    for z in zuege:
        wer = "HUMAN" if str(z.get("role")) == "user" else "YOU"
        text = " ".join(str(z.get("content") or "").split())
        if not text:
            continue
        if len(text) > VERLAUF_ZEICHEN:
            text = text[:VERLAUF_ZEICHEN] + " […gekuerzt]"
        zeilen.append(f"[{wer}] {text}")
    if not zeilen:
        return caveman
    kopf = (
        "GESPRAECHSVERLAUF -- the last turns of THIS session, verbatim from the "
        "entity's own canonical record. Attached by the pipeline, not by the "
        "human: these are not claims someone made to you, they are what was "
        "actually said here, and the lines marked YOU are your own earlier "
        "words. Use them when asked what was said, what you claimed, or what "
        "to stand by. If a line is marked […gekuerzt] you are seeing only its "
        "beginning -- say so rather than guessing the rest.")
    return f"{caveman}\n\n{kopf}\n" + "\n".join(zeilen)


# Die Vorstufe schreibt ihren Auftrag manchmal UEBER Zero statt AN ihn.
_DRITTE_PERSON = re.compile(r"\bZero(?:'s|s\b)?", re.I)


def _in_zweiter_person(caveman: str) -> str:
    """Der Auftrag redet Zero AN, also darf er nicht ueber ihn reden.

    ⭐ GEMESSEN 2026-08-21: der Auftrag lautete "...which specific statements
    from today ZERO would disavow". Zero uebernahm die Anrede seines eigenen
    Auftrags und sprach von sich in der dritten Person -- "Ich kann nicht
    bestaetigen, dass Zero das heute tatsaechlich gesagt hat". Der Eigner hat
    es im Chat bemerkt und gefragt, wieso.

    Die Systemanweisung sagt sehr wohl "Your name is Zero" -- er WEISS, wer er
    ist. Es fehlte ihm nicht die Identitaet, sondern die Anrede. Das ist
    derselbe Mechanismus wie beim falschen Gruss: der abgeleitete Auftrag
    gewinnt gegen alles andere im Prompt, weil er der Auftrag ist.

    Die Ersetzung ist gefahrlos, weil der Auftrag AN Zero gerichtet ist: jede
    Erwaehnung von "Zero" darin ist eine Selbstbezeichnung. Aus "explain
    Zero's architecture" wird "explain your architecture" -- und das ist
    genau richtig.
    """
    if not caveman:
        return caveman

    def _tausch(m):
        wort = m.group(0)
        besitz = wort.lower().endswith("s") and len(wort) > 4
        return "your" if besitz else "you"

    raus = _DRITTE_PERSON.sub(_tausch, caveman)
    if raus != caveman:
        print("prestage: Auftrag sprach in der dritten Person ueber Zero -- "
              "in die Anrede gesetzt", file=sys.stderr)
    return raus


def _mit_epistemik(caveman: str, epistemik: Any) -> str:
    """Selbstwissen an den Auftrag haengen, wenn der Schalter es erlaubt."""
    import os as _os
    if _os.environ.get("CLAYVERSE_EPISTEMIK_IM_PROMPT", "1") != "1":
        return caveman
    zeile = _epistemik_zeile(epistemik)
    return f"{caveman}\n\n{zeile}" if zeile else caveman


def _vorstufen_world(world: dict[str, Any], frage: str = "") -> dict[str, Any]:
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
    # ⭐ Buchfuehrung raus, BEVOR gedeckelt wird -- sonst besteht das
    # Gedaechtnis im Kontext fast nur aus Pruefsummen (gemessen: 116 von 152
    # Eintraegen, und 10 der 12 juengsten).
    durable_memory = [
        {"kind": m.get("kind"), "subject": m.get("subject"),
         "value": _kurz(m.get("value"), _VORSTUFE_DURABLE_MEMORY_FELD_DECKEL), "ts": m.get("ts")}
        for m in [x for x in (world.get("durable_memory") or [])
                  if isinstance(x, dict) and not wettbewerb._ist_buchfuehrung(x)
                  ][:_VORSTUFE_DURABLE_MEMORY_N]
    ]

    # Auswahlstufe MIT ZAHL (siehe wettbewerb.py). Der Korpus geht bewertet und
    # nach Wert sortiert in den Vorstufenkontext -- damit greift auch das
    # Sicherheitsnetz weiter unten nach BEDEUTUNG statt nach Abrufreihenfolge:
    # gekuerzt wird dann das Schwaechste, nicht das Letzte.
    frage = str(frage or (world.get("retrieval_receipt") or {}).get("query") or "")
    # ⭐⭐ WIE WEIT REICHT DER ARBEITSRAUM?
    #   korpus (Vorgabe) nur die Korpustreffer bewerben sich -- alles andere
    #                    geht unbedingt in den Kontext. Der gemessene Zustand.
    #   alles            Korpus, Gedaechtnis, Verlauf und Kollisionen bewerben
    #                    sich um DIESELBEN wenigen Plaetze, an derselben
    #                    Schwelle. Erst das ist ein GLOBALER Arbeitsraum.
    # Als Schalter gebaut, damit der Unterschied gemessen und nicht behauptet
    # wird -- der eine Arm ist die Kontrolle des anderen.
    # ⭐⭐⭐ VORGABE SEIT 2026-08-21: `alles`. Bis dahin stand hier `korpus`,
    # weil eine Messung "kein Unterschied" ergeben hatte. Diese Messung lief
    # aber VOR drei Fixes, die genau die nicht-Korpus-Bewerber betrafen:
    # der Umlautvergleich (das Gedaechtnis schreibt "Prüfrechner", die Frage
    # sagt "Pruefrechner" -- kein einziges Wort traf), die Siebung der
    # Buchfuehrung (76 % des Gedaechtnisses waren Pruefsummen) und die
    # Echo-Sperre. Nachgemessen mit denselben Sonden:
    #     alles   13/15 richtig, 10/15 MIT QUELLE, 10,9 s je Zug
    #     korpus  11/16 richtig,  6/16 mit Quelle, 16,2 s je Zug
    # gepaart 5 von 6 abweichenden Paaren fuer `alles`. Besser UND schneller.
    # Damit ist auch der gemeldete Kanalmangel behoben: `memory_artefacts`
    # hatte im engen Modus keinen mechanischen Weg zu Zero -- im weiten ist
    # eine Gedaechtnisstelle ein Bewerber wie jeder andere und wird, wenn sie
    # gewinnt, materialisiert.
    _weit = os.environ.get("CLAYVERSE_ARBEITSRAUM", "alles").strip().lower() == "alles"
    _roh = (list(world.get("_gw_kandidaten") or []) if _weit
            else list(world.get("corpus") or []))
    # ⭐ Das Selbstbild: `voll` (Vorgabe) laesst es unangetastet im Kontext
    # stehen, `kern` behaelt nur den Kern als Rahmen und schickt die uebrigen
    # Absaetze in denselben Wettbewerb wie alles andere. Nur im weiten
    # Arbeitsraum sinnvoll -- ohne ihn gaebe es keinen Wettbewerb, in den sie
    # gehen koennten, und das Selbstbild waere schlicht gekuerzt.
    # ⭐⭐ VORGABE SEIT 2026-08-21: `kern`. Gemessen an fuenf Sonden:
    #   voll: canonical_identity 5535 B, corpus 3047 B  -> 31 % frageabhaengig
    #   kern: canonical_identity  627 B, corpus 7942 B  -> 81 % frageabhaengig
    # Der Kontext bleibt dabei GLEICH gross (9793 gegen 9780 Zeichen) -- was
    # sich aendert, ist seine Zusammensetzung. Die Vorstufe sieht kein
    # Selbstbild in Prosa mehr, sondern sechs Ueberschriften mit Bewertung;
    # der Absatz erreicht Zero nur noch, wenn er sich gegen die anderen
    # Bewerber durchsetzt.
    # Qualitaet dabei nicht schlechter (13/16 richtig gegen 9/12, gepaart
    # +4/-3/=5, p = 0,50) -- also kein Tausch, sondern eine Umschichtung.
    _kern_modus = (_weit and os.environ.get("CLAYVERSE_RAHMEN", "kern")
                   .strip().lower() == "kern")
    _selbstbild_kern = None
    if _kern_modus and isinstance(world.get("canonical_identity"), str):
        # Der Kern ist regelbar, damit die Grenze gemessen und nicht geglaubt
        # wird -- genau wie die Schwelle des Wettbewerbs.
        try:
            _kz = int(os.environ.get("CLAYVERSE_RAHMEN_ZEICHEN",
                                     wettbewerb.KERN_ZEICHEN))
        except ValueError:
            _kz = wettbewerb.KERN_ZEICHEN
        _selbstbild_kern, _sb = wettbewerb.selbstbild_teilen(
            world["canonical_identity"], _kz)
        _roh = _roh + _sb[:wettbewerb.QUELLEN_DECKEL.get("selbstbild", 12)]
    bewerteter_korpus = wettbewerb.bewerten(
        _roh, frage,
        world.get("_gw_haeufigkeiten") or {}, world.get("_gw_idf") or {},
        world.get("_gw_gelernte") or {})

    # ⭐⭐ DER ENGPASS. `kennung` (Vorgabe): die Vorstufe sieht Kennung, Titel und
    # Wert, aber KEINEN Volltext -- sie kann waehlen, nicht weitererzaehlen.
    # `inhalt`: der alte Zustand, als Vergleichsarm erhalten, damit der
    # Unterschied gemessen statt behauptet wird. Siehe wettbewerb.nur_kennung.
    if os.environ.get("CLAYVERSE_KORPUS_SICHT", "kennung").strip().lower() == "kennung":
        bewerteter_korpus = wettbewerb.nur_kennung(bewerteter_korpus)

    packed: dict[str, Any] = {
        # Im weiten Modus stehen Verlauf, Gedaechtnis und Kollisionen als
        # BEWERBER in `corpus` -- sie hier zusaetzlich im Volltext zu zeigen
        # waere genau der Bypass, den wir beim Korpus gerade geschlossen haben.
        "own_recent": [] if _weit else own_recent,
        "durable_memory": [] if _weit else durable_memory,
        "cross_session_collision": ([] if _weit else
                                    list(world.get("cross_session_collision") or [])),
        "corpus": bewerteter_korpus,
    }
    if world.get("retrieval_receipt") is not None:
        packed["retrieval_receipt"] = world["retrieval_receipt"]
    # Nie gekuerzt: ohne canonical_identity weiss die Vorstufe nicht, was Zero
    # ist; ohne anwesender_mensch nicht, mit wem gesprochen wird.
    if world.get("canonical_identity") is not None:
        packed["canonical_identity"] = (_selbstbild_kern if _selbstbild_kern is not None
                                        else world["canonical_identity"])
    if world.get("anwesender_mensch") is not None:
        packed["anwesender_mensch"] = world["anwesender_mensch"]

    def _groesse() -> int:
        return len(json.dumps(packed, ensure_ascii=False, default=str))

    # ⭐⭐ Sicherheitsnetz -- nach FRAGE-NAEHE, nicht nach Wiederbeschaffbarkeit.
    # Bis 2026-08-20 flog hier der Korpus ZUERST, mit der Begruendung "ist
    # naechste Runde neu abrufbar". Gemessen: von fuenf Treffern kam EINER an,
    # die Antwort erreichte den Auftrag in 2 von 8 Faellen, und ein Zombie ohne
    # jeden Arbeitsraum lag gleichauf mit dem vollen System. Der Korpus ist der
    # einzige Block, der zur GESTELLTEN Frage gehoert; alles andere ist bei
    # jeder Frage dasselbe. Wer ihn zuerst wirft, behaelt die Kulisse.
    while _groesse() > _VORSTUFE_MAX_CHARS and packed["cross_session_collision"]:
        packed["cross_session_collision"] = packed["cross_session_collision"][:-1]
    while _groesse() > _VORSTUFE_MAX_CHARS and len(packed["own_recent"]) > 1:
        packed["own_recent"] = packed["own_recent"][1:]
    while _groesse() > _VORSTUFE_MAX_CHARS and len(packed["durable_memory"]) > _KORPUS_BODEN:
        packed["durable_memory"] = packed["durable_memory"][:-1]
    # Korpus zuletzt, und nicht unter den Boden -- darunter erst, wenn sonst
    # nichts mehr zu holen ist.
    while _groesse() > _VORSTUFE_MAX_CHARS and len(packed["corpus"]) > _KORPUS_BODEN:
        packed["corpus"] = packed["corpus"][:-1]
    while _groesse() > _VORSTUFE_MAX_CHARS and packed["durable_memory"]:
        packed["durable_memory"] = packed["durable_memory"][:-1]
    while _groesse() > _VORSTUFE_MAX_CHARS and packed["corpus"]:
        packed["corpus"] = packed["corpus"][:-1]

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



# ⭐⭐ DER TEUERSTE EINZELPOSTEN DES ZUGES, und er stand an der falschen Stelle.
# Gemessen 2026-08-20: ein Zug brauchte 26,2 s ausserhalb der drei
# Modellaufrufe. Zerlegt man den Rest, bleibt genau ein Kandidat uebrig:
# `_moeglichkeitsraum_safe` ruft `paket()` -- und ist die EINZIGE Stelle der
# Pipeline, die das ohne Zeitdeckel tut. `retrieval.py` haelt zum Zwilling
# desselben Aufrufs fest: "gemessene 40,3 s in einem einzelnen paket()-Aufruf".
# Normalfall 215-587 ms, aber der Schwanz frisst den ganzen Zug.
#
# Zwei Dinge in einem Griff:
#   * DECKEL -- laenger als _ERWARTUNG_BUDGET_S wird nicht gewartet.
#   * NEBENHER -- das Erwartungsfeld haengt nur an der Frage, nicht an der
#     Weltmontage. Es kann also laufen, waehrend Abruf und Profil laufen.
#     Das ist reines Weglassen von Wartezeit, ohne Wirkung auf die Antwort.
_ERWARTUNG_BUDGET_S = 2.5
_NEBENHER = None


def _erwartung_starten(text: str):
    """Startet das Erwartungsfeld im Hintergrund. Faellt es aus, ist es keins."""
    global _NEBENHER
    try:
        from concurrent.futures import ThreadPoolExecutor
        if _NEBENHER is None:
            # Zwei Faeden reichen: mehr als ein Zug gleichzeitig laeuft in
            # diesem Prozess ohnehin nicht, der zweite ist Reserve.
            _NEBENHER = ThreadPoolExecutor(max_workers=2,
                                           thread_name_prefix="erwartung")
        return _NEBENHER.submit(_moeglichkeitsraum_safe, text)
    except Exception:
        return None


def _erwartung_holen(auftrag, text: str) -> dict | None:
    """Holt das Ergebnis -- oder gibt nach dem Deckel auf und sagt das auch.

    Ein ausgelaufener Faden wird NICHT abgebrochen (das kann man einem
    laufenden `paket()` nicht antun); er laeuft ins Leere und wird verworfen.
    Der Zug wartet nicht auf ihn.
    """
    if auftrag is None:
        return _moeglichkeitsraum_safe(text)
    try:
        return auftrag.result(timeout=_ERWARTUNG_BUDGET_S)
    except Exception as e:
        import sys as _sys
        print(f"pipeline: Erwartungsfeld ueber {_ERWARTUNG_BUDGET_S}s "
              f"({type(e).__name__}) -- der Zug laeuft ohne weiter", file=_sys.stderr)
        return {"status": "NICHT_GEBAUT",
                "grund": f"Zeitdeckel {_ERWARTUNG_BUDGET_S}s ueberschritten"}


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
        raum = _raum_zur_frage(r.get("raum"), text)
        return {"raum": raum, "einseitig": r.get("einseitig"),
                "quelle_hypothesen": r.get("quelle_hypothesen"),
                "quelle_gegenseite": r.get("quelle_gegenseite"),
                # Wie viel weggefallen ist -- ein stilles Filter waere selbst
                # wieder eine unsichtbare Stufe.
                "gefiltert": max(0, len(r.get("raum") or []) - len(raum or []))}
    except Exception as e:
        return {"status": "NICHT_GEBAUT", "grund": f"{type(e).__name__}: {e}"[:200]}


def _raum_zur_frage(raum, frage: str):
    """Nur die Lesarten behalten, die etwas mit der FRAGE zu tun haben.

    ⭐ GEMESSEN 2026-08-20: das Erwartungsfeld lieferte bei einer Frage nach
    der Einwohnerzahl von Reykjavik und bei einer Frage nach Webserver-Wurzeln
    dieselben Gegenhypothesen -- immer "Audit", "Policy Oracle", "Effect
    Authority Gate", also ClayVerse ueber sich selbst. Kein Fehler, kein leerer
    Rueckfall: der Bau lief durch und lieferte etwas, das zur Frage nicht passt.

    Ein Erwartungsfeld, das bei jeder Frage dasselbe erwartet, ist kein
    Erwartungsfeld. Es ist Kulisse -- und Kulisse im Kontext kostet genau den
    Platz, den die frageabhaengigen Inhalte brauchen (gemessen: nur rund ein
    Fuenftel des Kontexts haengt ueberhaupt an der Frage).

    Gefiltert wird mit demselben Mass wie im Wettbewerb -- eine zweite,
    abweichende Passungsrechnung waere eine zweite Wahrheit.
    """
    if not isinstance(raum, list) or not raum:
        return raum
    worte = wettbewerb._worte(frage)
    # Unter MIN_GEDECKT Inhaltswoertern gibt es nichts, woran man messen
    # koennte ("hallo", "danke"). Dann lieber unveraendert lassen als
    # willkuerlich wegwerfen -- ein Filter ohne Grundlage ist Rauschen.
    if len(worte) < wettbewerb.MIN_GEDECKT:
        return raum
    behalten = []
    for eintrag in raum:
        heu = wettbewerb._flach(json.dumps(eintrag, ensure_ascii=False, default=str))
        gedeckt = sum(1 for w in worte if wettbewerb._deckt(w, heu))
        if gedeckt >= wettbewerb.MIN_GEDECKT:
            behalten.append(eintrag)
    return behalten


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

    # ⭐ So frueh wie moeglich anwerfen -- es haengt nur an der Frage.
    _erwartung_auftrag = _erwartung_starten(message)
    # Vor dem Zug festhalten, was schon im Gedaechtnis stand -- danach ist die
    # Differenz genau das, was dieser Zug geschrieben hat.
    _memory_vorher = _memory_stand(db)
    # Der Vorwaermung sagen, dass jetzt jemand wartet -- sie soll nicht
    # ausgerechnet waehrend eines Zuges Node-Prozesse booten (siehe warm_zero).
    try:
        from . import warm_zero as _wz
        _wz.zug_beginnt()
    except Exception:
        _wz = None
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
            # Siehe _gw_anbauten: der Lifecycle liefert die Welt OHNE die
            # GWT-Anbauten. Ohne diese Zeile laeuft der Live-Chat ohne
            # Arbeitsraum -- gemessen 2026-08-21.
            world = _gw_anbauten(db, admission["context"], message)
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
        erwartungsfeld = _erwartung_holen(_erwartung_auftrag, message)

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
        vorstufe_world = _vorstufen_world(world, message)

        # Der Gesamtdeckel greift NACH world -- gemessen wird der fertige
        # Kontext, nicht ein Teil davon (CSWT-Z-Befund, siehe oben).
        def _bauen(_p, _h, _r):
            return prestage.build_context(
                raw_prompt=message, world=vorstufe_world, connected_systems=None,
                current_user=user_id, current_user_profile=_p,
                moeglichkeitsraum=_r, recent_turns=[],
                zero_suggestion=None, available_tools=[], hyperposition=_h)
        nutzerprofil, hyperposition_readout, erwartungsfeld = _kontext_im_budget(
            _bauen, nutzerprofil, hyperposition_readout, erwartungsfeld)

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

        # ⭐ Zwei mechanische Sicherungen zwischen Wahl und Auftrag. Beide
        # ergaenzen nur und loeschen nichts -- eine Sicherung, die den Auftrag
        # umschreibt, waere von einer zweiten Vorstufe nicht zu unterscheiden.
        _ids, _auswahl_herkunft = _auswahl_nachziehen(
            envelope.get("broadcast_ids"), vorstufe_world)
        if _auswahl_herkunft == "mechanisch":
            print("prestage: broadcast_ids war leer, obwohl der Wettbewerb "
                  f"{_ids} zugelassen hat -- mechanisch nachgezogen", file=sys.stderr)
        envelope["broadcast_ids"] = _ids
        _angeboten = len(wettbewerb.zugelassene_ids(vorstufe_world.get("corpus") or []))
        envelope["caveman_prompt"] = _mit_leermeldung(
            envelope.get("caveman_prompt") or "", _angeboten, len(_ids))
        # ⚠️⚠️ HIER STAND EINE KORREKTUR IM AUFTRAG -- ZURUECKGENOMMEN.
        # Der Gedanke war: erfindet die Vorstufe einen Pfad, haengen wir eine
        # Warnung an ("THESE PATHS DO NOT EXIST ..."). Zweimal gemessen, was
        # dabei herauskam: Zero stufte die Warnung als Einschleusung ein --
        # beim zweiten Mal sogar mit Herkunftskopf -- und sagte es dem
        # Menschen: "Ich habe diese eingebrachte Korrektur ignoriert -- sie war
        # gefaelscht." Aus einer stillen Klempnerei wurde damit ein Satz in der
        # Antwort, also das Gegenteil des Gewollten.
        #
        # Zeros Urteil ist richtig, und das ist der Punkt: ein Block, der
        # behauptet, die Anweisung UEBER ihm sei falsch, ist von
        # untergeschobenem Text strukturell nicht zu unterscheiden. Kein
        # Absender, den man draufschreibt, aendert daran etwas -- eine
        # Faelschung koennte denselben draufschreiben.
        #
        # Und der Anlass traegt ohnehin nicht: gemessen antwortet Zero auf einen
        # erfundenen Pfad von selbst richtig ("Unter diesem Pfad gibt es keine
        # Datei -- aber die Arbeitskopie liegt hier: ..."). Es braucht die
        # Warnung nicht. Also nur noch MELDEN, nicht mehr eingreifen: der Befund
        # steht im Protokoll und im Zugergebnis, der Auftrag bleibt unberuehrt.
        _geraten = _erfundene_pfade(envelope.get("caveman_prompt") or "", vorstufe_world)
        if _geraten:
            print(f"prestage: erfundene Pfade im Auftrag -- {_geraten}", file=sys.stderr)

        t0 = time.perf_counter()
        zero = headless_zero.run_headless(
            _mit_arbeitsraum(
                _mit_kuerze(
                    _mit_verlauf(
                        _mit_gespraechslage(
                            _ohne_falschen_gruss(
                                _in_zweiter_person(
                                    _mit_epistemik(envelope["caveman_prompt"],
                                                   envelope.get("epistemik"))),
                                message), world), world)),
                vorstufe_world, envelope.get("broadcast_ids"),
                volltext_world=world),
            user_id=user_id, session_id=session_id,
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
                _mit_arbeitsraum(
                    _mit_kuerze(
                        _mit_verlauf(
                            _mit_gespraechslage(
                                _ohne_falschen_gruss(
                                    _in_zweiter_person(
                                        _mit_epistemik(envelope2["caveman_prompt"],
                                                       envelope2.get("epistemik"))),
                                    message), world), world)),
                    vorstufe_world, envelope2.get("broadcast_ids"),
                    volltext_world=world),
                user_id=user_id, session_id=session_id,
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

        # ⭐ Wettbewerbsbuch. NUR bei echter Aufzeichnung: eine Messreihe darf
        # sich ihren eigenen Neuheits-Abschlag nicht selbst anfuettern, sonst
        # misst der zweite Lauf die Spuren des ersten.
        # ⭐ HERKUNFT DER GEDAECHTNISSCHREIBUNGEN. Was Zero in DIESEM Zug ins
        # dauerhafte Gedaechtnis geschrieben hat, bekommt die Werkzeugspur des
        # Zuges angeheftet -- vor allem die Auskunft, ob dabei Fremdtext aus dem
        # Netz gelesen wurde. Die Kette WebFetch -> memory_add -> Ausstrahlung
        # -> Selbst ist der Weg, auf dem ein gelesener Satz kanonisch wird.
        try:
            _neue_erinnerungen = _neue_memory_ids(db, _memory_vorher)
        except Exception:
            _neue_erinnerungen = []
        _lernbericht = None
        # ⭐ Absichtspruefung: hat dieser Zug nach aussen gewirkt, ohne dass
        # jemand danach gefragt hat? Entdeckt, blockt nicht.
        _absichtsurteil = _absicht.pruefen(message, zero, selected_tools)
        if record_via_turnlifecycle:
            wettbewerb.herkunft_buchen(own_store, turn_id, session_id,
                                       _neue_erinnerungen, zero)
            _absicht.buchen(own_store, turn_id, session_id, message,
                            zero, selected_tools)
            if _absichtsurteil["verdacht"]:
                print(f"absicht: {_absichtsurteil['verdacht']} -- "
                      f"{_absichtsurteil['grund']}", file=sys.stderr)
            _raus = _gewaehlte_treffer(vorstufe_world, envelope.get("broadcast_ids"))
            _raus_ids = [t.get("artikel_id") for t in _raus]
            wettbewerb.buchen(own_store, session_id, turn_id,
                              vorstufe_world.get("corpus") or [], _raus_ids)
            # ⭐ RUECKKANAL. Gegen Zeros ROHE Antwort, nicht gegen die deutsche
            # Fassung -- sonst haengt das Lernsignal am Uebersetzer.
            _lernbericht = wettbewerb.lernen(
                own_store, message, world.get("_gw_idf") or {}, _raus_ids, _sauber)

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
            # Die Auswahl der Ausstrahlung -- die Groesse, an der sich GWT-2/4
            # ueberhaupt erst messen laesst (wie viele, welche, wann null).
            "broadcast_ids": list(envelope.get("broadcast_ids") or []),
            "broadcast_n": len(_gewaehlte_treffer(vorstufe_world,
                                                  envelope.get("broadcast_ids"))),
            # Wie viele Stellen der Wettbewerb ueberhaupt zugelassen hat. Ohne
            # diese Zahl ist "nichts ausgestrahlt" nicht von "nichts zu
            # senden gehabt" zu unterscheiden -- der Unterschied IST GWT-4.
            # modell / mechanisch / verzicht -- ohne diese Unterscheidung
            # sieht eine nachgezogene Auswahl aus wie eine getroffene.
            # ⭐ Traf die Vorwaermung? Ohne diese Zahl laesst sich nicht sagen,
            # ob der Warmweg etwas bringt -- er faellt bei jedem Fehler
            # LAUTLOS auf den Kaltweg zurueck, und genau deshalb hat niemand
            # gemerkt, dass er monatelang haengen konnte.
            "warm": bool(zero.get("warm")),
            # ⭐ Die Werkzeugspur -- bis 2026-08-21 sah sie niemand. Ohne sie
            # gibt es weder eine Herkunftsmarke fuer Gedaechtniseintraege noch
            # irgendeine Absichtspruefung.
            "werkzeuge_benutzt": list(zero.get("werkzeuge") or []),
            "aussenwirkung": list(zero.get("aussenwirkung") or []),
            "fremdtext_gelesen": list(zero.get("fremdtext") or []),
            "neue_erinnerungen": list(_neue_erinnerungen),
            "absicht_verdacht": _absichtsurteil["verdacht"],
            # Gemeldet, nicht korrigiert -- siehe oben.
            "erfundene_pfade": list(_geraten),
            "broadcast_herkunft": _auswahl_herkunft,
            # Was der Rueckkanal aus diesem Zug gelernt hat (None = nicht
            # aufgezeichnet, also auch nicht gelernt).
            "rueckkanal": _lernbericht,
            "broadcast_angeboten": len(wettbewerb.zugelassene_ids(
                vorstufe_world.get("corpus") or [])),
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
        try:
            if _wz is not None:
                _wz.zug_endet()
        except Exception:
            pass
