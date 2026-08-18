"""Die Seitenuebersicht -- uebernommen aus agentforge, nicht neu erfunden.

Gabriel: "schau dir in agentforge die unterseite hosting an die wir gebaut haben
... die nimmst du und baust als unterpage in die entityos page ein ... aber ohne
die anderen frank.ink features wie workspace etc, nur die features die sinn
machen, jetzt nichts neu erfinden." Und: "es soll immer dabei stehen ob self
hosted oder extern."

⭐ UEBERNOMMEN, NICHT NACHGEBAUT. Die Kennzahlen sind exakt die der bestehenden
Hosting-Ansicht (agentforge/engine/project_engine.py):
    Besuche/Unikate  heute, 7 Tage, 30 Tage, gesamt
    Funkenlinie      Besuche je Tag, 30 Eintraege
    Verweise         woher die Besucher kamen
    Seiten           welche Pfade aufgerufen wurden
    Seitengewicht    Bytes je Art (html/css/js/img) und die groessten Dateien
Dieselbe Quelle (site_visits + Dateisystem), dieselbe Rechnung. Eine zweite,
leicht abweichende Zaehlung waere schlimmer als keine -- dann streiten zwei
Anzeigen darueber, wie viele Besucher es gab.

WEGGELASSEN, weil es hier keinen Sinn ergibt: Workspace, Slug umbenennen,
Offline nehmen, Werbung, Marketing-Assistenten. Das sind frank.ink-Funktionen.
Hier geht es darum, WAS es gibt, WIE es laeuft und WIE man es aendert.

⭐ SELBST GEHOSTET ODER EXTERN steht an JEDER Zeile. Das ist keine Zierde: bei
einer selbst gehosteten Seite koennen wir eine Aenderung machen, bei einer
externen nicht -- und der Unterschied entscheidet, ob ein Arbeitspaket ueberhaupt
sinnvoll ist. Die Einstufung wird ABGELEITET (liegt ein Verzeichnis auf diesem
Wirt?), nicht behauptet.
"""
from __future__ import annotations

import sqlite3
import time
from pathlib import Path

# Direkt, ohne Umweg: agentforge ist Gabriels eigener Dienst.
# Zuvor lief das ueber ein Abbild, weil ich ihn faelschlich fuer fremd
# hielt -- richtige Vorsicht bei falscher Praemisse. Ein Direktzugriff
# hat keinen Alterszustand, den jemand uebersehen kann.
AGENTFORGE_DB = Path("/var/lib/agentforge/db/agentforge.db")
PROJEKTWURZEL = Path("/var/lib/agentforge/projects")

# Seiten mit EIGENER nginx-Wurzel, nicht ueber die Plattform. Aus der laufenden
# Konfiguration abgelesen, nicht geraten -- siehe Wissensartikel
# wissen-frank-ink-hosting.
EIGENE_WURZEL = {
    "seimensch": [("seimensch.net", "site"), ("herzrad.at", "site/herzrad"),
                  ("leihmich.org", "site/leihmich")],
}
BEARBEITUNG = {
    "seimensch": "Git-Klon aendern, committen, `git push origin main` -- der "
                 "post-receive-Hook auf /srv/git/seimensch.git spiegelt. Die "
                 "Live-Wurzel ist KEIN Arbeitsverzeichnis.",
}
BEARBEITUNG_STANDARD = ("Dateien unter projects/<konto>/<slug>/site/. ⚠️ Ungeprueft, "
                        "ob dieses Projekt aus einem Repo befuellt wird -- dann waere "
                        "eine direkte Aenderung beim naechsten Lauf weg.")


def _verbinde():
    if not AGENTFORGE_DB.is_file():
        return None
    c = sqlite3.connect(f"file:{AGENTFORGE_DB}?mode=ro", uri=True, timeout=20)
    c.row_factory = sqlite3.Row
    return c


def _gewicht(ordner: Path) -> dict:
    """Seitengewicht je Art -- dieselbe Einteilung wie get_site_pagespeed."""
    if not ordner.is_dir():
        return {"nicht_ermittelbar": "Verzeichnis nicht vorhanden"}
    summen = {"html": 0, "css": 0, "js": 0, "img": 0, "rest": 0}
    groesste, dateien = [], 0
    for f in ordner.rglob("*"):
        if not f.is_file():
            continue
        try:
            s = f.stat().st_size
        except OSError:
            continue
        dateien += 1
        e = f.suffix.lower()
        if e in (".html", ".htm"):
            summen["html"] += s
        elif e == ".css":
            summen["css"] += s
        elif e in (".js", ".mjs"):
            summen["js"] += s
        elif e in (".png", ".jpg", ".jpeg", ".webp", ".gif", ".svg", ".avif", ".ico"):
            summen["img"] += s
        else:
            summen["rest"] += s
        groesste.append((s, str(f.relative_to(ordner))))
    groesste.sort(reverse=True)
    return {
        "bytes": summen, "gesamt": sum(summen.values()), "dateien": dateien,
        "groesste": [{"pfad": p, "bytes": b} for b, p in groesste[:5]],
    }


def _zahlen(c, pid: int) -> dict:
    """Besuche und Unikate -- exakt die Fenster der bestehenden Ansicht."""
    jetzt = time.time()
    fenster = {"heute": jetzt - 86400, "d7": jetzt - 7 * 86400,
               "d30": jetzt - 30 * 86400, "gesamt": 0}
    besuche, unikate = {}, {}
    for name, ab in fenster.items():
        besuche[name] = c.execute(
            "SELECT COUNT(*) FROM site_visits WHERE project_id=? AND ts >= ?",
            (pid, ab)).fetchone()[0]
        unikate[name] = c.execute(
            "SELECT COUNT(DISTINCT ip_hash) FROM site_visits "
            "WHERE project_id=? AND ts >= ? AND ip_hash <> ''", (pid, ab)).fetchone()[0]
    tage = {r["day"]: r["n"] for r in c.execute(
        "SELECT day, COUNT(*) AS n FROM site_visits WHERE project_id=? AND ts >= ? "
        "GROUP BY day ORDER BY day", (pid, jetzt - 30 * 86400))}
    funken = []
    for i in range(29, -1, -1):
        tag = time.strftime("%Y-%m-%d", time.gmtime(jetzt - i * 86400))
        funken.append(tage.get(tag, 0))
    verweise = [{"woher": r["referrer"] or "direkt", "n": r["n"]} for r in c.execute(
        "SELECT referrer, COUNT(*) AS n FROM site_visits WHERE project_id=? AND ts >= ? "
        "GROUP BY referrer ORDER BY n DESC LIMIT 5", (pid, jetzt - 30 * 86400))]
    pfade = [{"pfad": r["path"] or "/", "n": r["n"]} for r in c.execute(
        "SELECT path, COUNT(*) AS n FROM site_visits WHERE project_id=? AND ts >= ? "
        "GROUP BY path ORDER BY n DESC LIMIT 5", (pid, jetzt - 30 * 86400))]
    letzter = c.execute("SELECT MAX(ts) FROM site_visits WHERE project_id=?", (pid,)).fetchone()[0]
    return {"besuche": besuche, "unikate": unikate, "funken_30d": funken,
            "verweise": verweise, "pfade": pfade,
            "letzter_besuch_vor_s": round(jetzt - letzter) if letzter else None}


def uebersicht(*, mindest_besuche: int = 1) -> dict:
    """Alle Seiten, die wir verwalten -- mit Herkunft, Zahlen und Bearbeitungsweg."""
    c = _verbinde()
    if c is None:
        return {"nicht_ermittelbar": f"{AGENTFORGE_DB} nicht lesbar -- "
                                     "im Container eingehaengt?"}
    seiten = []
    for p in c.execute(
            "SELECT id, user_id, slug, name, folder_path FROM projects "
            "WHERE COALESCE(archived,0)=0 ORDER BY slug"):
        pid, slug = p["id"], p["slug"]
        ordner = Path(p["folder_path"]) if p["folder_path"] else PROJEKTWURZEL / str(p["user_id"]) / slug
        siteordner = ordner / "site"
        # ⭐ ABGELEITET, nicht behauptet: liegt das Verzeichnis auf diesem Wirt,
        # hosten wir selbst. Sonst extern -- und dann koennen wir es auch nicht
        # aendern, was ueber den Sinn eines Arbeitspakets entscheidet.
        selbst = siteordner.is_dir()
        zahlen = _zahlen(c, pid)
        if zahlen["besuche"]["gesamt"] < mindest_besuche and not selbst:
            continue
        # Erst die eigenen Domains in der eingetragenen Reihenfolge, dann die
        # Plattformadresse. Vorne einzufuegen kehrt die Reihenfolge um -- dann
        # stand bei seimensch leihmich.org als Hauptadresse.
        adressen = [f"https://{d}" for d, _ in EIGENE_WURZEL.get(slug, [])]
        adressen.append(f"https://{slug}.frank.ink")
        seiten.append({
            "slug": slug, "name": p["name"], "konto": p["user_id"],
            "hosting": "selbst gehostet" if selbst else "extern",
            "hosting_begruendung": (f"Verzeichnis {siteordner} liegt auf diesem Wirt"
                                    if selbst else
                                    "kein site-Verzeichnis auf diesem Wirt gefunden"),
            "ausgeliefert_von": ("eigene nginx-Wurzel" if slug in EIGENE_WURZEL
                                 else "agentforge-Plattform (*.frank.ink)"),
            "adressen": adressen,
            "bearbeitung": BEARBEITUNG.get(slug, BEARBEITUNG_STANDARD),
            "gewicht": _gewicht(siteordner) if selbst else {"nicht_ermittelbar": "extern"},
            # ⚠️ Seiten mit EIGENER nginx-Wurzel laufen nicht ueber die
            # Plattform -- agentforge sieht ihren Verkehr gar nicht. Eine Null
            # waere hier kein Messergebnis, sondern ein falscher Wert, der
            # plausibel aussieht: man haelt die Seite fuer tot.
            "zaehlung": ("agentforge zaehlt diese Seite NICHT -- sie laeuft ueber eine "
                         "eigene nginx-Wurzel. Die Zahlen unten sind daher kein Mass "
                         "fuer ihren Verkehr."
                         if slug in EIGENE_WURZEL else "ueber die Plattform gezaehlt"),
            **zahlen,
        })
    c.close()
    seiten.sort(key=lambda s: -s["besuche"]["gesamt"])
    return {
        "seiten": seiten, "anzahl": len(seiten),
        "erhoben": time.strftime("%Y-%m-%dT%H:%M:%S+0000", time.gmtime()),
        # Direktzugriff: die Zahlen sind der Live-Stand, kein Abbild.
        "abbild_alter_s": 0,
        "hinweis": ("Zahlen und Rechnung sind aus der bestehenden Hosting-Ansicht "
                    "uebernommen, nicht nachgebaut -- gleiche Quelle (site_visits), "
                    "gleiche Fenster. Zwei leicht abweichende Zaehlungen waeren "
                    "schlimmer als eine."),
    }
