"""F94 -- Emergente Wegehierarchie: Autobahnen, Tunnel, langsame Strassen.

Gabriel, 16.08.: "umso oefter ein Weg verwendet wird, umso besser wird er
ausgebaut -- so entstehen emergent Highways, Schnellstrassen, Tunnel
(Hyperposition) und langsame Strassen, was die neurale Aktivitaet, Emergenz und
Kopplung sichtbar macht, und das als Nebenprodukt."

⭐ DER NEBENPRODUKT-PUNKT IST DER WERTVOLLSTE. Normalerweise kostet es eigenes
Messwerk, Kopplung sichtbar zu machen -- und Messwerk verzerrt, was es misst.
Hier faellt die Sichtbarkeit ohne Zusatzaufwand an: der Verkehr wird ohnehin
geschrieben (F92b-Erfolgsmarken). Die Hierarchie IST die Aufzeichnung, nicht
ihr Stellvertreter.

⭐⭐ AUTOBAHN UND TUNNEL SIND NICHT DASSELBE, und der Unterschied traegt alles:

    AUTOBAHN  ein VORHANDENER Weg wird billiger. Verstaerkung bestehender
              Struktur. Ein falscher kostet etwas Zeit.
    TUNNEL    eine NEUE Verbindung zwischen Orten, die im Graphen weit
              auseinanderliegen, aber verlaesslich zusammen gebraucht werden.
              Hier entsteht Struktur, die vorher nicht da war -- ein falscher
              BEHAUPTET eine Verbindung, die es semantisch nicht gibt, und
              alles Spaetere erbt sie.

═══ DIE DREI BEDINGUNGEN, OHNE DIE ES ZUR FOSSILIE WIRD ═══

1 ⚠️ WEGE MUESSEN VERFALLEN. Wer nur verstaerkt, macht die zuerst gegangenen
  Wege dauerhaft zu Autobahnen -- unabhaengig davon, ob sie noch taugen. Das
  Netz erstarrt zum Abdruck des fruehen Verkehrs. `verfallen()` laeuft im Takt.

2 ⭐ VERSTAERKUNG UMGEKEHRT ZUR BISHERIGEN GUETE. Autobahnen erzeugen ihren
  eigenen Verkehr: ist eine erst da, bevorzugt die Eintrittswahl sie, WEIL sie
  billig ist -- was sie weiter verstaerkt. Reich wird reicher, und die
  Hierarchie friert nach der ersten Phase ein.
  Deshalb gewinnt ein NEUER Weg je Nutzung MEHR als eine Autobahn:
      zuwachs = GRUNDZUWACHS * (1 - guete)
  Ohne das kann ein neuer Weg nie genug ansammeln, um zu konkurrieren.

3 ⚠️⚠️ TUNNEL BRAUCHEN EINE STRENGERE SCHWELLE. Verlangt wird wiederholte,
  UNABHAENGIGE Mitbenutzung -- keine starke Korrelation. Und nach F84 zaehlt
  Mitbenutzung aus derselben Sitzung oder derselben Abstammung NICHT als
  unabhaengig. Deshalb wird je Weg festgehalten, aus WIE VIELEN VERSCHIEDENEN
  Sitzungen er getragen hat, und nur das zaehlt fuer den Tunnelrang.

═══ DIE BILLIGE FAELSCHUNGSPRUEFUNG (aus der Doku selbst) ═══

    Verteilung des Verkehrs ueber die Wege auftragen.
    Bei Wirkung      schwerschwaenzig -- wenige Autobahnen, viele langsame.
    Gleichverteilt   es bildet sich KEINE Hierarchie; der Mechanismus tut
                     nichts, unabhaengig davon wie gut er klingt.

`pruefung()` rechnet das aus und sagt es geradeheraus. Ein Mechanismus, der
seine eigene Wirkungslosigkeit nicht anzeigen kann, ist nicht pruefbar.
"""
from __future__ import annotations

import re
import time

SCHEMA = """
CREATE TABLE IF NOT EXISTS vp_weg (
  von TEXT NOT NULL,
  nach TEXT NOT NULL,
  art TEXT,                          -- Kantenart, aus der der Weg entstand
  nutzung INTEGER NOT NULL DEFAULT 0,
  getragen INTEGER NOT NULL DEFAULT 0,
  guete REAL NOT NULL DEFAULT 0.0,   -- 0 = langsame Strasse, 1 = Autobahn
  sitzungen TEXT,                    -- verschiedene Sitzungen, die ihn trugen (JSON-Liste)
  tunnel INTEGER NOT NULL DEFAULT 0,
  erste_nutzung REAL NOT NULL,
  letzte_nutzung REAL NOT NULL,
  PRIMARY KEY(von, nach)
);
CREATE INDEX IF NOT EXISTS idx_vp_weg_guete ON vp_weg(guete DESC);
"""

GRUNDZUWACHS = 0.12
VERFALL = 0.94                   # je Takt; ungenutzte Wege sinken zurueck
SCHWELLE_SCHNELL = 0.30
SCHWELLE_AUTOBAHN = 0.65
TUNNEL_MIN_SITZUNGEN = 3         # strenger als Autobahn: UNABHAENGIGE Mitbenutzung
TUNNEL_MIN_GUETE = 0.45
MAX_SITZUNGEN_GEMERKT = 12

# ⭐⭐ GEMESSEN am 21.08. an /var/lib/clay/wiki.db (366 Wege, produktiv): der
# `sitzung`-Fix (Wirt -> echte Sitzung durchreichen) behebt nur, DASS echte
# Sitzungen ankommen -- er filtert nicht, WAS als "Sitzung" zaehlt. Ergebnis:
# 304 Wege trugen weiterhin die alte Wirt-Kennung "unbekannt", 76 eine von
# drei Diagnose-Labels ("breite-befahrung"/"diag"/"latenzmessung" aus
# Messlaeufen) oder ein "pruefung-<Datum>"-Label aus einem manuellen
# pruefung()-Aufruf -- und ACHT Wege erreichten damit `tunnel=1`
# (>=3 "verschiedene Sitzungen"), OBWOHL keine einzige davon eine unabhaengige
# menschliche Wiederverwendung belegt: "unbekannt" + zwei Diagnoselabels sind
# drei verschiedene STRINGS, aber eine einzige, nicht-unabhaengige Quelle.
# Das ist derselbe Fehler wie eine UNBEKANNT-Bedingung, die als ERFUELLT
# durchgeht (siehe clayverse/wake_condition.py) -- hier auf der
# Sitzungsachse statt der Zeitachse.
#
# SESSION_MUSTER ist bewusst eine ALLOWLIST, keine wachsende Verbotsliste von
# Labelnamen: jede kanonische Sitzung im System hat die Form `session:<user>`
# oder `session:<user>:<platz>` (siehe clayverse/identity.py,
# SITZUNGEN_JE_MENSCH -- diese Datei liegt in einem separaten Repo
# (/opt/unifieddb) und importiert clayverse bewusst NICHT, um die Kopplung
# nicht zu erzwingen; das Muster ist stabil genug, um hier unabhaengig
# dupliziert zu werden). Ein neues Diagnose-Skript mit einem neuen Labelnamen
# faellt automatisch durch, ohne dass diese Datei je wieder angefasst werden
# muss -- eine Verbotsliste haette das Leck bei jedem neuen Labelnamen wieder
# geoeffnet.
SESSION_MUSTER = re.compile(r"^session:[a-z][a-z0-9_-]*(?::\d+)?$")


def ist_echte_sitzung(sitzung) -> bool:
    """Zaehlt `sitzung` als unabhaengige menschliche Sitzung fuer Bedingung 3?

    Diagnose-/Testlabels und die alte "unbekannt"-Kennung liefern False --
    sie duerfen weiterhin AUFGEZEICHNET werden (nutzung/guete kennen keine
    Sitzungsunterscheidung), aber nicht als Beleg fuer unabhaengige
    Mitbenutzung zaehlen.
    """
    return isinstance(sitzung, str) and bool(SESSION_MUSTER.match(sitzung))


def sicherstellen(db) -> None:
    """NUR am Start. executescript committet implizit."""
    db.db.executescript(SCHEMA)


def rang(guete: float, tunnel: int) -> str:
    if tunnel:
        return "tunnel"
    if guete >= SCHWELLE_AUTOBAHN:
        return "autobahn"
    if guete >= SCHWELLE_SCHNELL:
        return "schnellstrasse"
    return "langsame strasse"


def befahren(db, wege, *, sitzung: str) -> dict:
    """Wege verstaerken, die getragen haben. Umgekehrt gewichtet.

    `wege`: Liste von (von, nach, art). Nur Wege, die tatsaechlich zu einem
    ausgelieferten Treffer gefuehrt haben -- Verkehr ohne Ertrag ist kein
    Ausbaugrund, sonst verstaerkt sich auch das Irrfahren.
    """
    import json
    if not wege:
        return {"befahren": 0}
    jetzt = time.time()
    neu = tunnel_neu = 0
    with db.tx() as sql:
        for von, nach, art in wege:
            if not von or not nach or von == nach:
                continue
            r = sql.execute(
                "SELECT nutzung,getragen,guete,sitzungen,tunnel FROM vp_weg WHERE von=? AND nach=?",
                (von, nach)).fetchone()
            if r is None:
                # ⭐ Ein neuer Weg startet nicht bei 0, sondern bekommt den
                # vollen Zuwachs -- sonst braucht er zu lange, um ueberhaupt
                # sichtbar zu werden, und die Hierarchie friert ein.
                sitzungen = [sitzung]
                guete = GRUNDZUWACHS
                sql.execute(
                    "INSERT INTO vp_weg(von,nach,art,nutzung,getragen,guete,sitzungen,"
                    "tunnel,erste_nutzung,letzte_nutzung) VALUES(?,?,?,1,1,?,?,0,?,?)",
                    (von, nach, art, guete, json.dumps(sitzungen), jetzt, jetzt))
                neu += 1
                continue
            try:
                sitzungen = json.loads(r["sitzungen"] or "[]")
            except Exception:
                sitzungen = []
            if sitzung not in sitzungen:
                sitzungen.append(sitzung)
            sitzungen = sitzungen[-MAX_SITZUNGEN_GEMERKT:]
            # ⭐ DIE UMGEKEHRTE GEWICHTUNG: je besser der Weg schon ist, desto
            # weniger bringt eine weitere Nutzung. Ohne das gewinnt immer der
            # zuerst gegangene Weg, egal wie gut die spaeteren sind.
            guete = min(1.0, float(r["guete"]) + GRUNDZUWACHS * (1.0 - float(r["guete"])))
            # Tunnel NUR bei unabhaengiger Mitbenutzung aus verschiedenen
            # Sitzungen -- eine starke Korrelation aus EINER Sitzung reicht
            # nicht. Ein falscher Tunnel behauptet eine Verbindung, die es
            # semantisch nicht gibt, und alles Spaetere erbt sie.
            #
            # ⚠️ GEZAEHLT WIRD NUR `ist_echte_sitzung()` (siehe dortiger
            # Kommentar, gemessen 21.08.): "unbekannt" und Diagnose-/Test-
            # labels bleiben in `sitzungen` (fuer die Anzeige/Nachvollzug
            # erhalten), zaehlen aber NICHT mehr zum Tunnel-Schwellwert --
            # sonst reicht ein einziger mehrfach wiederholter Diagnoselauf,
            # um eine "unabhaengige" Mitbenutzung vorzutaeuschen, die es nie
            # gab.
            echte_sitzungen = {s for s in sitzungen if ist_echte_sitzung(s)}
            ist_tunnel = int(len(echte_sitzungen) >= TUNNEL_MIN_SITZUNGEN and guete >= TUNNEL_MIN_GUETE)
            if ist_tunnel and not r["tunnel"]:
                tunnel_neu += 1
            sql.execute(
                "UPDATE vp_weg SET nutzung=nutzung+1, getragen=getragen+1, guete=?, "
                "sitzungen=?, tunnel=?, letzte_nutzung=? WHERE von=? AND nach=?",
                (guete, json.dumps(sitzungen), ist_tunnel, jetzt, von, nach))
    return {"befahren": len(wege), "neu": neu, "tunnel_neu": tunnel_neu}


def verfallen(db) -> dict:
    """Ungenutzte Wege sinken zurueck. Ohne das erstarrt das Netz.

    Multiplikativ auf ALLE: wer in diesem Takt befahren wurde, hat vorher
    zugelegt und faellt netto weniger. Wege unter der Sichtbarkeitsschwelle
    werden entfernt -- ein Netz, das nur waechst, ist eine Karte in
    Korpusgroesse.
    """
    with db.tx() as sql:
        sql.execute("UPDATE vp_weg SET guete = guete * ?", (VERFALL,))
        cur = sql.execute("DELETE FROM vp_weg WHERE guete < 0.02 AND getragen < 2")
        entfernt = cur.rowcount
        sql.execute("UPDATE vp_weg SET tunnel=0 WHERE tunnel=1 AND guete < ?",
                    (TUNNEL_MIN_GUETE,))
    return {"verfallen": True, "entfernt": entfernt}


def pruefung(db) -> dict:
    """Bildet sich ueberhaupt eine Hierarchie? Die Doku nennt diese Pruefung selbst.

    Erwartung bei Wirkung: schwerschwaenzig -- wenige Autobahnen, viele
    langsame Strassen. Gleichverteilt heisst: der Mechanismus tut NICHTS,
    unabhaengig davon, wie gut er klingt.
    """
    try:
        db.db.execute("SELECT 1 FROM vp_weg LIMIT 1")
    except Exception:
        return {"stand": "NOCH_KEINE_WEGE"}
    zeilen = [dict(r) for r in db.db.execute(
        "SELECT von,nach,guete,nutzung,getragen,tunnel,sitzungen FROM vp_weg")]
    n = len(zeilen)
    if n < 10:
        return {"wege": n, "urteil": "zu wenige Wege fuer ein Urteil",
                "hinweis": "Eine Hierarchie aus weniger als zehn Wegen ist Rauschen."}
    werte = sorted((z["guete"] for z in zeilen), reverse=True)
    oberes_zehntel = sum(werte[:max(1, n // 10)])
    gesamt = sum(werte) or 1.0
    anteil = oberes_zehntel / gesamt
    gleich = (n // 10 or 1) / n          # Anteil bei Gleichverteilung
    raenge = {}
    for z in zeilen:
        r = rang(z["guete"], z["tunnel"])
        raenge[r] = raenge.get(r, 0) + 1

    # ⚠️⚠️ BEDINGUNG-3-EHRLICHKEIT (gebaut 21.08., siehe SESSION_MUSTER-
    # Kommentar oben): "kein Tunnel bildet sich" und "es gab noch nicht genug
    # unabhaengige Sitzungen, um ueberhaupt einen zu erreichen" sehen in
    # `raenge["tunnel"]` GLEICH aus (beides: eine kleine oder Null-Zahl).
    # Das ist derselbe Fehler wie eine UNBEKANNT-Bedingung, die als "nicht
    # eingetreten" durchgeht (siehe clayverse/wake_condition.py) -- hier
    # getrennt ausgewiesen, statt in einer Zahl vermischt. `tunnel_roh` liest
    # das gespeicherte `tunnel`-Flag (kann kontaminierte Alt-Daten enthalten,
    # die vor dem 21.08. mit Diagnose-/Testlabels statt echten Sitzungen
    # entstanden sind -- heilt sich erst, wenn die jeweilige Kante das
    # naechste Mal befahren wird); `tunnel_bereinigt` rechnet live neu, nur
    # mit `ist_echte_sitzung()`-gefilterten Sitzungen.
    import json
    alle_echten_sitzungen: set[str] = set()
    wege_mit_echter_sitzung = 0
    tunnel_bereinigt = 0
    for z in zeilen:
        try:
            sitzungen = json.loads(z["sitzungen"] or "[]")
        except Exception:
            sitzungen = []
        echte = {s for s in sitzungen if ist_echte_sitzung(s)}
        alle_echten_sitzungen |= echte
        if echte:
            wege_mit_echter_sitzung += 1
        if len(echte) >= TUNNEL_MIN_SITZUNGEN and float(z["guete"]) >= TUNNEL_MIN_GUETE:
            tunnel_bereinigt += 1
    verschiedene_echte = len(alle_echten_sitzungen)
    if verschiedene_echte < TUNNEL_MIN_SITZUNGEN:
        bedingung3_stand = "NOCH_ZU_WENIG_DATEN"
        bedingung3_hinweis = (
            f"Erst {verschiedene_echte} verschiedene echte Sitzung(en) je im gesamten "
            f"Graphen gesehen -- ein Tunnel braucht mindestens {TUNNEL_MIN_SITZUNGEN} auf "
            "DERSELBEN Kante. Rechnerisch kann noch kein einziger echter Tunnel "
            "entstanden sein; 0 ist hier Datenmangel, kein Negativbefund."
        )
    elif tunnel_bereinigt == 0:
        bedingung3_stand = "BEDINGUNG3_ERFUELLBAR_ABER_KEIN_TUNNEL"
        bedingung3_hinweis = (
            f"{verschiedene_echte} verschiedene echte Sitzungen insgesamt vorhanden -- "
            "genug, um rechnerisch einen Tunnel zu bilden -- aber noch keine Kante mit "
            f">= {TUNNEL_MIN_SITZUNGEN} davon UND Guete >= {TUNNEL_MIN_GUETE}."
        )
    else:
        bedingung3_stand = "TUNNEL_BILDEN_SICH_ECHT"
        bedingung3_hinweis = f"{tunnel_bereinigt} Kante(n) erfuellen Bedingung 3 mit echten Sitzungen."
    return {
        "wege": n,
        "raenge": raenge,
        "oberes_zehntel_haelt": round(anteil, 3),
        "bei_gleichverteilung": round(gleich, 3),
        "urteil": ("Hierarchie bildet sich" if anteil > gleich * 2
                   else "GLEICHVERTEILT -- es bildet sich keine Hierarchie, "
                        "der Mechanismus tut nichts"),
        "hinweis": ("Das obere Zehntel der Wege haelt diesen Anteil der Gesamtguete. "
                    "Bei Gleichverteilung waeren es genau 10 %. Deutlich mehr heisst: "
                    "wenige Autobahnen, viele langsame Strassen -- die erwartete Form."),
        "bedingung3_echt": {
            "verschiedene_echte_sitzungen_insgesamt": verschiedene_echte,
            "wege_mit_mind_einer_echten_sitzung": wege_mit_echter_sitzung,
            "tunnel_roh_gespeichert": raenge.get("tunnel", 0),
            "tunnel_bereinigt": tunnel_bereinigt,
            "stand": bedingung3_stand,
            "hinweis": bedingung3_hinweis,
        },
    }


def lage(db, grenze: int = 12) -> dict:
    """Die staerksten Wege, fuer Zero lesbar."""
    try:
        db.db.execute("SELECT 1 FROM vp_weg LIMIT 1")
    except Exception:
        return {"stand": "NOCH_KEINE_WEGE"}
    wege = []
    for r in db.db.execute(
            "SELECT von,nach,art,guete,nutzung,getragen,tunnel FROM vp_weg "
            "ORDER BY guete DESC LIMIT ?", (grenze,)):
        wege.append({"von": r["von"], "nach": r["nach"], "art": r["art"],
                     "rang": rang(r["guete"], r["tunnel"]),
                     "guete": round(r["guete"], 3),
                     "nutzung": r["nutzung"], "getragen": r["getragen"]})
    return {"wege": wege, **{k: v for k, v in pruefung(db).items()
                             if k in ("raenge", "urteil", "oberes_zehntel_haelt")}}
