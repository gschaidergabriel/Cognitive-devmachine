"""Lagebild -- Zeros Blick auf sein eigenes Haus, nicht nur auf die aktuelle Nachricht.

Ohne dieses Modul sieht Zero pro Anfrage nur den Prompt und was es selbst
abruft: keine Ahnung, ob ein Takt ausgefallen ist, ob die eigene andere
Sitzung etwas getan hat, ob der Korpus gewachsen ist oder ob etwas
fehlgeschlagen ist. Das hier ist EIN billiger Lesezugriff, der genau diese
Luecke schliesst -- "was ist passiert, waehrend ich nicht hingesehen habe".

DREI REGELN (Eignerauftrag 18.08.):

1. DIE GRENZE. Die zwei Sitzungen EINES Menschen gehoeren diesem Menschen --
   Zero darf ueber sie hinwegsehen. NIE ueber den anderen Menschen. user_id
   kommt deshalb NUR aus dem verifizierten self.user_id der Bruecke in
   mcp_server.py, nie aus einem Werkzeugargument -- sonst waere die Trennung
   eine Bitte statt einer Eigenschaft. Diese Funktion hier nimmt user_id als
   Parameter, aber der Aufrufer (die Bruecke) darf ihn nur aus dem
   verifizierten Zustand fuellen, nie das Modell. Genau diese Grenze ist
   heute schon einmal gerissen (memory_tabelle ohne user_id/session_id,
   siehe erfolge.py f-leck) -- deshalb hier bewusst nochmal ausgeschrieben.

2. STILLE IST KEINE GESUNDHEIT. Ein gestoppter Takt sieht genauso aus wie ein
   ruhiger -- das hat dieses Projekt heute zweimal gebissen (verfall() ohne
   Zeitplan, die Kartenaufnahme existierte gar nicht). Deshalb steht hier nie
   nur "zuletzt gelaufen um X", sondern IMMER auch: liegt X laenger zurueck
   als das erwartete Intervall (UEBERFAELLIG_FAKTOR). Ein ueberfaelliger Takt
   muss LAUT im Ergebnis stehen (ueberfaellig: true), nicht nur im Zeitstempel
   versteckt sein.

3. KEINE ERFUNDENE RUHE. Fehlt eine Tabelle, ein Mount oder schlaegt eine
   Abfrage fehl, sagt das Feld das ("nicht_ermittelbar": Grund) -- nie eine
   Null oder leere Liste, die wie "alles ruhig" aussieht. Eine falsche
   Entwarnung ist schlimmer als eine Luecke, weil ihr niemand nachgeht. Ein
   gemessenes Null (z.B. "die andere Sitzung hat wirklich 0 Zuege") wird
   dagegen ausdruecklich als gemessen gekennzeichnet -- das ist kein
   Widerspruch zur Regel, sondern ihr Sinn: Erfundenes und Gemessenes duerfen
   nie gleich aussehen.

⚠️ Legt KEINE Tabellen an. Dieses Modul ist reines Lesen -- Schemaanlage
gehoert an den Start (service.py, neben profil_grundstock), niemals in eine
Lesefunktion: executescript() committet implizit und reisst eine laufende
Transaktion auseinander (heute gemessen: f-77, 77 rote Tests).

⚠️ Die sieben Autonomietakte sind aus dem Container heraus NICHT per
systemctl abfragbar (gemessen 18.08.: kein systemctl im Image, kein
Host-Systemd-Mount). AUTONOME_TAKTE unten haelt deshalb die erwarteten
Intervalle als bekannte Haustatsache fest -- genau wie WIRT_GEHOERT in
wirte.py --, und jeder Takt wird stattdessen ueber seine tatsaechliche Spur
in der gemeinsamen DB (oder dem gemeinsam gemounteten /var/lib/clay/karte)
belegt. Wo keine Spur erreichbar ist (agentzero-export schreibt nur nach
/opt/agentzero-export, das nicht gemountet ist; clayverse-puls ist gar kein
periodischer Timer sondern ein Dauerdienst), sagt das Feld das explizit.
"""
from __future__ import annotations

import time
from datetime import datetime, timezone
from pathlib import Path

from .identity import sitzungen_von

# name -> erwartetes Intervall in Sekunden. None = kein periodischer Timer.
AUTONOME_TAKTE: dict[str, int | None] = {
    "entityos-baunotizen": 15 * 60,
    "entityos-profile": 30 * 60,
    "entityos-abrufkarte": 30 * 60,
    "agentzero-export": 30 * 60,
    "clayverse-karte": 6 * 60 * 60,
    "clayverse-kuration": 10 * 60,
    "clayverse-puls": None,
}

# Ab dem Wievielfachen der eigenen Taktzeit ohne Lebenszeichen ein Takt als
# ueberfaellig gilt. 2x statt 1x: ein einzelner spaeter Lauf (Systemlast,
# Neustart) ist noch kein Ausfall, aber das Doppelte der eigenen Taktzeit
# ohne Spur ist keiner mehr.
UEBERFAELLIG_FAKTOR = 2.0

MAX_THEMA_ZEICHEN = 70
MAX_FEHLSCHLAEGE = 3

# Gemeinsam mit dem Host gemountet (siehe wirte.py ZWILLING_DIR). karte.py
# (clayverse-karte.timer) schreibt hierher Schnappschuss-Dateien -- lesbar
# aus dem Container, auch ohne systemctl.
KARTE_DIR = Path("/var/lib/clay/karte")


def _epoch(iso_text) -> float | None:
    """ISO8601-Text (mit oder ohne Mikrosekunden, mit oder ohne Doppelpunkt im
    Offset) -> Unix-Epoche. Gibt None zurueck statt zu raten, wenn es nicht
    parst -- ein nicht-parsbarer Zeitstempel ist ein nicht_ermittelbar-Fall,
    keine Null."""
    if not iso_text:
        return None
    try:
        dt = datetime.fromisoformat(str(iso_text))
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.timestamp()


def _abfrage_max(db, sql: str) -> float | None:
    try:
        row = db.db.execute(sql).fetchone()
    except Exception:
        return None
    if not row or row[0] is None:
        return None
    return _epoch(row[0])


def _juengste_karte_datei_mtime() -> float | None:
    try:
        zeiten = [p.stat().st_mtime for p in KARTE_DIR.rglob("*.json") if p.is_file()]
    except Exception:
        return None
    return max(zeiten) if zeiten else None


def _takt_eintrag(name: str, letzter_epoch: float | None, quelle: str, jetzt: float) -> dict:
    intervall = AUTONOME_TAKTE.get(name)
    if letzter_epoch is None:
        return {
            "quelle": quelle,
            "nicht_ermittelbar": f"kein Nachweis fuer {name} in dieser Spur gefunden "
                                  "(Tabelle/Datei fehlt oder ist leer) -- kein Ausfall behauptet, "
                                  "nur: von hier aus nicht sichtbar.",
        }
    vor_s = jetzt - letzter_epoch
    eintrag = {
        "quelle": quelle,
        "zuletzt_vor_s": round(vor_s),
        "intervall_erwartet_s": intervall,
    }
    if intervall:
        eintrag["ueberfaellig"] = vor_s > intervall * UEBERFAELLIG_FAKTOR
    else:
        eintrag["ueberfaellig"] = None
        eintrag["hinweis"] = "kein bekanntes periodisches Intervall -- Ueberfaelligkeit nicht pruefbar"
    return eintrag


def _takt_status(db, name: str, jetzt: float) -> dict:
    if name == "entityos-baunotizen":
        return _takt_eintrag(
            name,
            _abfrage_max(db, "SELECT MAX(erzeugt_am) FROM artikel WHERE art IN ('baunotiz','vorfall')"),
            "artikel(art IN ('baunotiz','vorfall')).MAX(erzeugt_am)", jetzt)
    if name == "entityos-profile":
        return _takt_eintrag(
            name, _abfrage_max(db, "SELECT MAX(zeit) FROM vd_lauf"), "vd_lauf.MAX(zeit)", jetzt)
    if name == "entityos-abrufkarte":
        return _takt_eintrag(
            name, _abfrage_max(db, "SELECT MAX(gebaut_am) FROM vp_karte_version"),
            "vp_karte_version.MAX(gebaut_am)", jetzt)
    if name == "clayverse-kuration":
        return _takt_eintrag(
            name, _abfrage_max(db, "SELECT MAX(zuletzt_geprueft_am) FROM kuration"),
            "kuration.MAX(zuletzt_geprueft_am)", jetzt)
    if name == "clayverse-karte":
        return _takt_eintrag(
            name, _juengste_karte_datei_mtime(), f"Datei-mtime unter {KARTE_DIR}", jetzt)
    if name == "agentzero-export":
        return {"nicht_ermittelbar": "kein Nachweisweg im Container: schreibt nicht in "
                "wiki.db, /opt/agentzero-export nicht gemountet (Haustatsache)."}
    if name == "clayverse-puls":
        return {"nicht_ermittelbar": "kein periodischer Timer, sondern Dauerdienst "
                "clayverse-puls.service; systemctl im Container nicht erreichbar (Haustatsache)."}
    return {"nicht_ermittelbar": f"unbekannter Takt: {name}"}


def erheben(db, user_id: str, session_id: str) -> dict:
    """Der eigentliche Lagebild-Aufruf. user_id/session_id MUESSEN aus dem
    verifizierten Bruecken-Zustand kommen (self.user_id/self.session_id in
    mcp_server.py), nie aus einem Werkzeugargument -- siehe Regel 1 oben."""
    jetzt = time.time()
    ergebnis: dict = {"anwesender_mensch": user_id, "erhoben_um_epoch": round(jetzt)}

    # ── 1. Die eigene andere Sitzung ────────────────────────────────────
    sitzungen = sitzungen_von(user_id)
    andere_kandidaten = [s for s in sitzungen if s != session_id]
    andere_id = andere_kandidaten[0] if andere_kandidaten else None

    anker_epoch: float | None = None
    anker_quelle = "keine"

    if andere_id is None:
        ergebnis["eigene_andere_sitzung"] = {
            "nicht_ermittelbar": f"kein zweiter Sitzungsplatz fuer {user_id} bekannt "
                                  "(sitzungen_von lieferte nur diese eine)."}
    else:
        try:
            row = db.db.execute(
                "SELECT COUNT(*) n, MAX(ts) letzte FROM turns WHERE session_id=?",
                (andere_id,)).fetchone()
        except Exception as e:
            ergebnis["eigene_andere_sitzung"] = {
                "session_id": andere_id, "nicht_ermittelbar": f"{type(e).__name__}: {e}"}
        else:
            if not row or not row["n"]:
                ergebnis["eigene_andere_sitzung"] = {
                    "session_id": andere_id, "zuege": 0,
                    "hinweis": "gemessenes Null: diese Sitzung hat noch keinen einzigen Zug -- "
                               "keine Abfrage ist fehlgeschlagen."}
            else:
                letzte_ts = row["letzte"]
                anker_epoch = letzte_ts
                anker_quelle = "letzter Zug der eigenen anderen Sitzung"
                thema = None
                try:
                    letzter = db.db.execute(
                        "SELECT role, content FROM turns WHERE session_id=? "
                        "ORDER BY ordinal DESC LIMIT 1", (andere_id,)).fetchone()
                except Exception:
                    letzter = None
                if letzter:
                    text = (letzter["content"] or "").replace("\n", " ").strip()
                    thema = f"{letzter['role']}: {text[:MAX_THEMA_ZEICHEN]}"
                ergebnis["eigene_andere_sitzung"] = {
                    "session_id": andere_id,
                    "zuege": row["n"],
                    "zuletzt_aktiv_vor_s": round(jetzt - letzte_ts) if letzte_ts else None,
                    "letztes_thema": thema,
                }

    # ── 2. Autonome Takte -- Stille ist keine Gesundheit (Regel 2) ─────
    ergebnis["autonome_takte"] = {name: _takt_status(db, name, jetzt) for name in AUTONOME_TAKTE}

    # ── 3. Korpusbewegung seit dem Anker ────────────────────────────────
    # Ohne eigenen Merker fuer "letzter Blick" ist der Anker der letzte Zug
    # der eigenen anderen Sitzung (oben) -- das beantwortet dieselbe Frage:
    # was geschah, seit dieser Mensch/Zero zuletzt ueberhaupt aktiv war.
    # Gibt es die nicht (frisch, oder noch nie benutzt), faellt das Fenster
    # explizit gekennzeichnet auf 24h zurueck -- keine stillschweigende Wahl.
    if anker_epoch is None:
        anker_epoch = jetzt - 24 * 60 * 60
        anker_quelle = "fallback_24h (keine andere Sitzung mit Zuegen gefunden)"
    anker_dt = datetime.fromtimestamp(int(anker_epoch), tz=timezone.utc)
    anker_iso_colon = anker_dt.strftime("%Y-%m-%dT%H:%M:%S+00:00")
    anker_iso_nocolon = anker_dt.strftime("%Y-%m-%dT%H:%M:%S+0000")
    try:
        zeilen = db.db.execute(
            "SELECT art, COUNT(*) n FROM artikel WHERE erzeugt_am > ? OR erzeugt_am > ? "
            "GROUP BY art ORDER BY n DESC LIMIT 10",
            (anker_iso_colon, anker_iso_nocolon)).fetchall()
        ergebnis["korpus_neu_seit_anker"] = {
            "anker_vor_s": round(jetzt - anker_epoch),
            "anker_quelle": anker_quelle,
            "je_art": {r["art"]: r["n"] for r in zeilen},
            "gesamt": sum(r["n"] for r in zeilen),
        }
    except Exception as e:
        ergebnis["korpus_neu_seit_anker"] = {"nicht_ermittelbar": f"{type(e).__name__}: {e}"}

    # ── 4. Abrufgesundheit ───────────────────────────────────────────────
    try:
        row = db.db.execute(
            "SELECT version, gebaut_am, regionen, wegweiser, verhaeltnis "
            "FROM vp_karte_version ORDER BY version DESC LIMIT 1").fetchone()
        if row is None:
            ergebnis["abrufkarte"] = {"nicht_ermittelbar": "vp_karte_version ist leer -- noch nie gebaut"}
        else:
            gebaut_epoch = _epoch(row["gebaut_am"])
            vor_s = (jetzt - gebaut_epoch) if gebaut_epoch is not None else None
            schwelle = (AUTONOME_TAKTE.get("entityos-abrufkarte") or 0) * UEBERFAELLIG_FAKTOR
            ergebnis["abrufkarte"] = {
                "version": row["version"],
                "gebaut_am": row["gebaut_am"],
                "vor_s": round(vor_s) if vor_s is not None else None,
                "regionen": row["regionen"],
                "wegweiser": row["wegweiser"],
                "verhaeltnis": row["verhaeltnis"],
                "veraltet": (vor_s > schwelle) if vor_s is not None else None,
            }
    except Exception as e:
        ergebnis["abrufkarte"] = {"nicht_ermittelbar": f"{type(e).__name__}: {e}"}

    # ── 5. Was fehlgeschlagen ist ────────────────────────────────────────
    try:
        zeilen = db.db.execute(
            "SELECT id, titel, datum FROM entityos_erfolge WHERE art='fehlschlag' "
            "ORDER BY erfasst DESC LIMIT ?", (MAX_FEHLSCHLAEGE,)).fetchall()
        ergebnis["fehlschlaege_kuerzlich"] = [
            {"id": r["id"], "titel": r["titel"], "datum": r["datum"]} for r in zeilen]
    except Exception as e:
        ergebnis["fehlschlaege_kuerzlich"] = {"nicht_ermittelbar": f"{type(e).__name__}: {e}"}

    # ── 6. Gedaechtnis-Ausbeute seit dem Anker (Ablehnungen) ─────────────
    try:
        row = db.db.execute(
            "SELECT COUNT(*) n, COALESCE(SUM(genommen),0) g, COALESCE(SUM(verworfen),0) v "
            "FROM gedaechtnis_ausbeute WHERE ts > ?", (anker_epoch,)).fetchone()
        ergebnis["gedaechtnis_seit_anker"] = {
            "laeufe": row["n"], "genommen": row["g"], "verworfen": row["v"]}
    except Exception as e:
        ergebnis["gedaechtnis_seit_anker"] = {"nicht_ermittelbar": f"{type(e).__name__}: {e}"}

    return ergebnis
