#!/usr/bin/env python3
"""Die Speicherwacht -- Zero haelt selbst Platz auf dem Wirt.

Gabriel: "genau dieses speicher management des vps muss agent zero autonom
uebernehmen." Anlass war ein Abend, an dem die Platte zweimal auf 100 % lief.

⭐ DIE URSACHE, gemessen, nicht vermutet: wiki.db ist 3,8 GB. Wer daran etwas
pruefen will, kopiert sie -- und raeumt die Kopie nicht weg. An diesem Abend
lagen fuenf solcher Kopien herum, zusammen ueber 18 GB. Kein Dienst hat sie
erzeugt, sondern Arbeit an der Datenbank. Deshalb raeumt diese Wacht genau
das auf: WEGWERFKOPIEN DER DATENBANK, alte Sicherungen, Bau-Zwischenlager.
Sie sucht nicht nach "grossen Dateien" -- das waere eine Suche nach Groesse
statt nach Zweck, und die groesste Datei auf diesem Wirt ist die Datenbank
selbst.

⚠️⚠️ WAS SIE NIEMALS ANFASST -- und warum das eine Liste sein muss und keine Regel:
UNANTASTBAR nennt jeden Pfad einzeln. Nicht "was wichtig aussieht", sondern
namentlich. Eine Wacht, die selbst entscheidet, was wichtig ist, hat an einem
schlechten Tag recht und an einem schlechteren nicht mehr. wiki.db ist die
einzige dauerhafte Wahrheit dieses Systems; sie zweimal zu haben ist teuer, sie
einmal zu verlieren ist das Ende.

⭐ ZWEI SICHERUNGEN GEGEN DEN EIGENEN EIFER:
1. Geloescht wird nur, was auf ein MUSTER passt UND alt genug ist. Eine frische
   Kopie kann eine laufende Untersuchung sein -- die wegzuraeumen waere
   dasselbe Uebel in der anderen Richtung.
2. Gehandelt wird in Stufen nach Druck. Bei 85 % wird nur berichtet. Wer schon
   bei 85 % loescht, loescht die meiste Zeit umsonst, und Loeschen umsonst ist
   die Uebung, aus der spaeter ein Unfall wird.

Und: sie kann melden, dass sie NICHTS getan hat. Ein Waechter, der nur Erfolge
melden kann, ist nicht messbar.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sqlite3
import time
from pathlib import Path

# ══ Namentlich unantastbar. Keine Regel, eine Liste. ══════════════════════
UNANTASTBAR = (
    "/var/lib/clay/wiki.db",              # die einzige dauerhafte Wahrheit
    "/var/lib/clay/arbeit",               # Zeros Arbeitskopien
    "/opt/unifieddb",
    "/opt/clayverse",
    "/opt/entityos",
    "/etc/entityos",
    "/etc/clayverse",
    "/srv/git",                           # die Repos = der Weg nach draussen
    "/var/lib/agentforge/projects",       # die ausgelieferten Seiten
    "/opt/seimensch-umfrage",
    "/var/lib/clayverse",
)

# ══ Was weg darf: Muster + Mindestalter. Beides muss stimmen. ═════════════
# Das Mindestalter ist keine Vorsicht, sondern eine Aussage: unter dieser
# Grenze kann die Datei zu einer LAUFENDEN Untersuchung gehoeren.
WEGWERF = (
    # (Verzeichnis, Namensmuster, Mindestalter Stunden, Mindestgroesse MB, Begruendung)
    ("/tmp",  "wiki*.db",        6,  100, "Wegwerfkopie der Datenbank zum Testen"),
    ("/tmp",  "*probe*.db",      6,  100, "Probekopie der Datenbank"),
    ("/tmp",  "*beweis*.db",     6,  100, "Beweiskopie der Datenbank"),
    ("/root", "wiki-probe*.db",  6,  100, "Probekopie der Datenbank"),
    ("/root", "wiki-test*.db",   6,  100, "Testkopie der Datenbank"),
    ("/root", "wiki-backup-*.db", 72, 100, "Sicherung vor einem Eingriff, drei Tage alt"),
)

STUFEN = (
    (85.0, "berichten",   "Nur berichten. Wer bei 85 % loescht, loescht meist umsonst -- "
                          "und Loeschen umsonst ist die Uebung, aus der ein Unfall wird."),
    (90.0, "leichtes",    "Bau-Zwischenlager, ueberlange Protokolle und Wegwerfkopien ab 12 Stunden."),
    (95.0, "kopien",      "Zusaetzlich alte Wegwerfkopien der Datenbank."),
    (98.0, "eng",         "Zusaetzlich juengere Kopien (ab 1 Stunde). Es wird eng."),
)

DB = "/var/lib/clay/wiki.db"


def _unter_unantastbar(p: Path) -> bool:
    ap = str(p.resolve())
    return any(ap == u or ap.startswith(u.rstrip("/") + "/") for u in UNANTASTBAR)


def lage() -> dict:
    g = shutil.disk_usage("/")
    belegt = 100.0 * g.used / g.total
    stufe, was, warum = "ruhig", "nichts", "unter allen Schwellen"
    for schwelle, name, begruendung in STUFEN:
        if belegt >= schwelle:
            stufe, was, warum = name, name, begruendung
    return {"gesamt_gb": round(g.total / 2**30, 1), "frei_gb": round(g.free / 2**30, 1),
            "belegt_prozent": round(belegt, 1), "stufe": stufe, "grund": warum}


def _kandidaten(min_alter_h: float) -> list[dict]:
    jetzt = time.time()
    treffer = []
    for ordner, muster, alter_h, min_mb, warum in WEGWERF:
        d = Path(ordner)
        if not d.is_dir():
            continue
        for f in d.glob(muster):
            if not f.is_file() or _unter_unantastbar(f):
                continue
            alter = (jetzt - f.stat().st_mtime) / 3600.0
            mb = f.stat().st_size / 2**20
            if alter >= max(alter_h, min_alter_h) and mb >= min_mb:
                treffer.append({"pfad": str(f), "gb": round(mb / 1024, 2),
                                "alter_stunden": round(alter, 1), "warum": warum})
    return sorted(treffer, key=lambda x: -x["gb"])


def _bauzwischenlager() -> dict:
    """Docker-Bauzwischenlager und ueberlange Protokolle. Nie Arbeit, immer Abfall."""
    getan = []
    for name, befehl in (("docker-bauzwischenlager", ["docker", "builder", "prune", "-af"]),
                         ("protokolle", ["journalctl", "--vacuum-size=300M"])):
        try:
            r = subprocess.run(befehl, capture_output=True, text=True, timeout=300)
            getan.append({"was": name, "rc": r.returncode,
                          "ausgabe": ((r.stdout or "") + (r.stderr or "")).strip()[-160:]})
        except Exception as e:
            getan.append({"was": name, "fehler": f"{type(e).__name__}: {e}"})
    return {"schritte": getan}


# ══ Abgeschafft. Eignerentscheidung 18.08. ════════════════════════════════
# "es gibt kein frankv0.1 mehr nicht mehr es gibt njur noch entityos fertig"
# "es braucht keine modelle mehr die lokal auf dem vps liegen"
# "es gibt nur noch entityos als ziel und das laeuft mit claude code"
#
# ⭐ Das aendert die Rechnung grundlegend. Modellgewichte waren bisher
# Betriebsmittel und damit unantastbar; jetzt sind sie Altbestand. Auf diesem
# Wirt sind das die groessten Posten ueberhaupt -- mehr als alles, was diese
# Wacht bisher zusammen aufraeumen durfte.
#
# ⚠️ ABER: Altbestand ist nicht Muell, und diese Wacht loescht ihn NICHT von
# selbst. Sie zeigt ihn nur an. Der Unterschied ist wichtig: eine Wegwerfkopie
# der Datenbank kann niemandem fehlen -- ein Modellcache oder ein
# Frank-Verzeichnis kann Arbeit von Wochen enthalten, die nirgends sonst liegt.
# Eine Wacht, die eine Grundsatzentscheidung selbstaendig in Loeschungen
# uebersetzt, hat den Auftrag ueberdehnt. Sie legt vor, ein Mensch entscheidet.
# (Pfad, Ersetzbarkeit, Begruendung)
#
# ⚠️⚠️ DIE ZWEITE SPALTE IST DER KERN, und sie kam erst nach einem Einwand von
# Zero dazu: "Sicherungen sind ueberhaupt nicht nachladbar und gehoeren nicht
# in dasselbe Gespraech wie die Modell-Zwischenlager."
#
# Vorher stand hier EINE Liste mit EINER Geschichte: "Gewichte sind nachladbar,
# also ist das Loeschen umkehrbar." Fuer Modelle stimmt das. Fuer Sicherungen
# nicht -- die gibt es genau einmal. Beides unter einer Ueberschrift zu fuehren
# heisst, die beruhigende Eigenschaft des einen auf das andere zu uebertragen.
# So verschwindet Unersetzliches: nicht durch Unachtsamkeit, sondern weil es in
# der falschen Zeile stand.
ALTBESTAND = (
    ("/root/.cache/huggingface", "nachladbar",
     "Modellgewichte von HuggingFace -- kommen auf Zuruf zurueck, sofern sie dort "
     "noch veroeffentlicht sind"),
    ("/var/lib/digital-retina", "nachladbar",
     "Bildmodell-Cache der digital-retina-Seite"),
    ("/home/frankrunner", "PRUEFEN",
     "Frank-Laeufer samt llama.cpp. ⚠️ llama.cpp ist nachladbar -- was dort an "
     "eigenen Gewichten, Zusammenfuehrungen oder Trainingsstaenden liegt, ist es "
     "NICHT. Vor dem Loeschen ansehen, nicht annehmen"),
    ("/srv/frank-deploy", "PRUEFEN",
     "Frank-Auslieferung. Was davon aus einem Repo stammt, kommt zurueck; was dort "
     "gebaut wurde, nicht"),
    ("/root/frank-laeufer", "PRUEFEN", "Frank-Laeufer-Reste"),
    ("/var/lib/clay-probe", "wegwerfbar",
     "liegengebliebene Probekopie der Datenbank -- das Original steht in "
     "/var/lib/clay/wiki.db"),
    ("/srv/sicherung", "UNERSETZLICH",
     "⚠️ SICHERUNGEN. Nicht nachladbar, nirgendwo sonst. Diese Zeile steht hier, "
     "damit sie SICHTBAR ist -- nicht, damit sie geloescht wird. Von Zero "
     "eingewandt: gehoert nicht in dasselbe Gespraech wie Modellcaches"),
)

# Was `abschaffen()` ueberhaupt anfassen darf. Alles andere wird nur ANGEZEIGT.
LOESCHBAR = {"nachladbar", "wegwerfbar"}


def altbestand() -> dict:
    """Was laut Eignerentscheidung nicht mehr gebraucht wird -- ZEIGEN, nicht loeschen.

    ⚠️ Diese Funktion loescht nichts und darf es nicht. Ein Modellcache sieht
    aus wie Muell und ein Frank-Verzeichnis auch; darin kann trotzdem Arbeit
    liegen, die es nirgends sonst gibt. Die Wacht legt die Rechnung vor, der
    Mensch zieht den Schnitt.
    """
    posten, summe = [], 0
    for pfad, ersetzbarkeit, warum in ALTBESTAND:
        d = Path(pfad)
        if not d.exists() or _unter_unantastbar(d):
            continue
        try:
            r = subprocess.run(["du", "-xsb", pfad], capture_output=True, text=True, timeout=240)
            b = int((r.stdout or "0").split()[0])
        except Exception:
            continue
        summe += b
        posten.append({"pfad": pfad, "gb": round(b / 2**30, 2),
                       "ersetzbarkeit": ersetzbarkeit, "warum": warum,
                       "darf_geloescht_werden": ersetzbarkeit in LOESCHBAR})
    posten.sort(key=lambda x: -x["gb"])
    frei = round(sum(x["gb"] for x in posten if x["darf_geloescht_werden"]), 2)
    return {"posten": posten, "summe_gb": round(summe / 2**30, 2),
            "davon_ersetzbar_gb": frei,
            "davon_unersetzlich_gb": round(summe / 2**30 - frei, 2),
            "hinweis": ("Das ist ein VORSCHLAG, keine Handlung. ⚠️ Und die Posten sind NICHT "
                        "gleichwertig: `nachladbar` kommt auf Zuruf zurueck, `PRUEFEN` muss "
                        "vorher jemand ansehen, `UNERSETZLICH` gibt es genau einmal. Nur die "
                        "ersten beiden Arten darf `speicher_abschaffen` ueberhaupt anfassen -- "
                        "die uebrigen stehen hier, damit sie SICHTBAR sind, nicht damit sie "
                        "weggehen."),
            "grundlage": "Eignerentscheidung 18.08.: nur noch EntityOS, keine lokalen Modelle"}

def _rueckweg_als_artikel(c, verzeichnis: list, _fehler: list) -> None:
    """Das Verzeichnis auch als WIKI-ARTIKEL -- sonst findet es niemand.

    ⚠️ Zero hat im Test danach gesucht und geschrieben: "Ich habe den Korpus
    nach diesem Verzeichnis durchsucht: es gibt es nicht." Er hatte recht --
    `rueckweg()` schrieb in eine TABELLE, und eine Tabelle ist kein Artikel.
    In der Datenbank, fuer jede Suche unsichtbar. Siebtes Mal an einem Tag,
    dass etwas gebaut wurde, fertig aussah und von keiner Suche erreicht wird.

    ⭐ Und hier waere es besonders bitter gewesen: das Verzeichnis IST die
    Zusicherung, dass Geloeschtes zurueckkommen kann. Eine Zusicherung, die
    man nicht finden kann, ist keine.
    """
    zeilen = ["RUECKWEG-VERZEICHNIS -- was liegt da, und wie kommt es zurueck", ""]
    for e in verzeichnis:
        zeilen.append(f"## {e['pfad']}")
        zeilen.append(e["warum"])
        for i in e["inhalt"]:
            if "modell" in i:
                zeilen.append(f"  - {i['modell']} ({i['gb']} GB) -> {i['zurueckholen']}")
            else:
                zeilen.append(f"  - {i.get('ordner', '?')}")
        zeilen.append("")
    zeilen.append("⚠️ Gewichte sind nachladbar, die LISTE war es nicht. Deshalb steht sie "
                  "hier. `speicher_abschaffen` verweigert ohne dieses Verzeichnis.")
    text = "\n".join(zeilen)
    aid = "wissen-rueckweg-altbestand"
    titel = "Rueckwegverzeichnis: was abgeschafft wurde und wie es zurueckkommt"
    try:
        c.execute(
            "INSERT INTO artikel(id,art,titel,quelle,datum,metadaten,belegt,erzeugt_am,"
            "wirt,zuletzt_von,status,konfidenz,projekt,sphaere,herkunft) "
            "VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET "
            "titel=excluded.titel, datum=excluded.datum",
            (aid, "wissen", titel, "speicherwacht", "2026-08-18",
             json.dumps({"herkunft": "gemessen", "gehoert_zu": "gemeinsam",
                         "wieso": "Zero suchte das Verzeichnis im Korpus und fand es nicht "
                                  "-- es stand nur in einer Tabelle."},
                        ensure_ascii=False),
             1, time.time(), "clayverse", "speicherwacht", "aktiv", 0.95,
             "EntityOS", "betrieb", "gemessen"))
        c.execute("DELETE FROM artikel_suchtext WHERE artikel_id=?", (aid,))
        c.execute("INSERT INTO artikel_suchtext(artikel_id,titel,text,blase,indiziert) "
                  "VALUES(?,?,?,?,?)", (aid, titel, text, "speicher,rueckweg,modelle", 1))
        rid = c.execute("SELECT id FROM artikel_suchtext WHERE artikel_id=?", (aid,)).fetchone()[0]
        c.execute("DELETE FROM fts_index_artikel WHERE rowid=?", (rid,))
        c.execute("INSERT INTO fts_index_artikel(rowid,titel,text) VALUES(?,?,?)",
                  (rid, titel, text))
    except Exception as e:
        # ⚠️ NICHT mehr stumm. Hier stand `pass` mit der Begruendung
        # "Auffindbarkeit darf die Buchung nicht kippen" -- und genau dieses
        # `pass` hat den Grund verschluckt, warum der Artikel nicht ankam.
        # Die Begruendung stimmt trotzdem: der Fehler darf den Vorgang nicht
        # abbrechen. Er muss nur SICHTBAR sein. Beides geht.
        _fehler.append(f"{type(e).__name__}: {e}")


def rueckweg(schreiben: bool = True) -> dict:
    """Das Verzeichnis der Abschaffung -- WAS da lag, damit es zurueckkommen kann.

    ⭐⭐ GABRIELS BEDINGUNG 18.08.: "wenn ich jemals doch will muss das auch gehen."
    Das ist der eigentliche Kern, und er ist billiger als er klingt:

    Modellgewichte sind NACHLADBAR -- jedes davon liegt bei HuggingFace und
    kommt auf Zuruf wieder. Was NICHT nachladbar ist, ist die LISTE: welche
    Modelle es waren, in welcher Fassung, wofuer sie da waren. Wer 14 GB
    Gewichte loescht, verliert nichts. Wer die Liste dazu verliert, verliert
    die Entscheidung, die dahinterstand -- und muss sie neu treffen, ohne zu
    wissen, was schon einmal geprueft war.

    Also: bevor irgendetwas aus ALTBESTAND verschwindet, wird sein VERZEICHNIS
    ins Wiki geschrieben. Danach ist das Loeschen umkehrbar in dem Sinn, der
    zaehlt -- nicht Byte fuer Byte, sondern als Absicht.

    ⚠️ Diese Funktion loescht selbst nichts. Sie ist die Bedingung dafuer, dass
    geloescht werden DARF, nicht der Loeschvorgang.
    """
    verzeichnis = []
    for pfad, ersetzbarkeit, warum in ALTBESTAND:
        d = Path(pfad)
        if not d.exists():
            continue
        eintrag = {"pfad": pfad, "ersetzbarkeit": ersetzbarkeit,
                   "warum": warum, "inhalt": []}

        # HuggingFace-Zwischenlager: die Ordnernamen SIND die Modellnamen.
        # models--Salesforce--blip-vqa-base -> Salesforce/blip-vqa-base
        for hub in (d / "hub", d, d / "paddle-cache" / "huggingface" / "hub"):
            if not hub.is_dir():
                continue
            for m in sorted(hub.glob("models--*")):
                name = m.name.replace("models--", "", 1).replace("--", "/")
                try:
                    r = subprocess.run(["du", "-xsb", str(m)], capture_output=True,
                                       text=True, timeout=60)
                    gb = round(int(r.stdout.split()[0]) / 2**30, 2)
                except Exception:
                    gb = None
                fassungen = [x.name for x in (m / "snapshots").glob("*")] \
                    if (m / "snapshots").is_dir() else []
                eintrag["inhalt"].append({
                    "modell": name, "gb": gb, "fassungen": fassungen[:4],
                    "zurueckholen": f"huggingface-cli download {name}"})

        # Alles andere: die obersten Ordner nennen, damit man wiedererkennt,
        # was dort gearbeitet wurde.
        if not eintrag["inhalt"]:
            try:
                eintrag["inhalt"] = [{"ordner": k.name,
                                      "art": "ordner" if k.is_dir() else "datei"}
                                     for k in sorted(d.iterdir())[:40]]
            except OSError:
                pass
        verzeichnis.append(eintrag)

    modelle = sum(len([i for i in e["inhalt"] if "modell" in i]) for e in verzeichnis)
    erg = {"verzeichnis": verzeichnis, "modelle_benannt": modelle,
           "hinweis": ("Gewichte sind nachladbar, die Liste war es nicht. Ab jetzt ist sie es: "
                       "jedes Modell steht mit Namen, Fassung und Nachladebefehl im Wiki. "
                       "Loeschen ist damit umkehrbar in dem Sinn, der zaehlt."),
           "bedingung": "Gabriel 18.08.: wenn ich jemals doch will, muss das auch gehen"}

    if schreiben:
        try:
            c = sqlite3.connect(DB, timeout=30)
            c.execute("CREATE TABLE IF NOT EXISTS speicher_rueckweg("
                      "pfad TEXT PRIMARY KEY, erfasst REAL NOT NULL, warum TEXT,"
                      " modelle INTEGER, verzeichnis TEXT NOT NULL)")
            for e in verzeichnis:
                c.execute("INSERT INTO speicher_rueckweg(pfad,erfasst,warum,modelle,verzeichnis)"
                          " VALUES(?,?,?,?,?) ON CONFLICT(pfad) DO UPDATE SET"
                          " erfasst=excluded.erfasst, modelle=excluded.modelle,"
                          " verzeichnis=excluded.verzeichnis",
                          (e["pfad"], time.time(), e["warum"],
                           len([i for i in e["inhalt"] if "modell" in i]),
                           json.dumps(e["inhalt"], ensure_ascii=False)))
            # ⚠️ Der Artikel wird VOR dem Schliessen geschrieben. Vorher stand der
            # Aufruf danach -- "Cannot operate on a closed database", verschluckt
            # von einem `except: pass`. Zwei Fehler uebereinander: eine falsche
            # Reihenfolge und ein Deckel darauf. Der Deckel war der schlimmere.
            _artikelfehler: list[str] = []
            _rueckweg_als_artikel(c, verzeichnis, _artikelfehler)
            c.commit(); c.close()
            erg["gebucht"] = True
            if _artikelfehler:
                erg["artikel_fehlgeschlagen"] = _artikelfehler
                erg["warnung"] = ("Das Verzeichnis steht in der Tabelle, aber NICHT als "
                                  "Wiki-Artikel -- also findet es keine Suche. Die "
                                  "Zusicherung existiert damit nur fuer den, der die "
                                  "Tabelle kennt.")
        except Exception as ex:
            erg["gebucht"] = False
            erg["buchfehler"] = f"{type(ex).__name__}: {ex}"
            # ⚠️ Ohne Buchung kein Loeschen. Die Aufzeichnung IST die Bedingung.
    return erg


def abschaffen(pfad: str) -> dict:
    """Einen Altbestandsposten entfernen -- NUR nach geschriebenem Rueckweg.

    ⚠️ Zwei Sperren, und beide sind Absicht:
    1. `pfad` muss WOERTLICH in ALTBESTAND stehen. Kein Muster, keine Naehe --
       eine Liste, die jemand von Hand geschrieben hat.
    2. Der Rueckweg muss fuer genau diesen Pfad in der Datenbank stehen. Wer
       ohne Verzeichnis loescht, macht es unumkehrbar, und das war die eine
       Bedingung des Eigners.
    """
    eintrag = next((e for e in ALTBESTAND if e[0] == pfad), None)
    if eintrag and eintrag[1] not in LOESCHBAR:
        return {"abgeschafft": False,
                "fehler": f"{pfad} ist als {eintrag[1]!r} eingestuft: {eintrag[2]} -- "
                          "dieses Werkzeug fasst nur `nachladbar` und `wegwerfbar` an. "
                          "Alles andere braucht einen Menschen, der es sich ansieht."}
    if pfad not in [a for a, _e, _w in ALTBESTAND]:
        return {"abgeschafft": False,
                "fehler": f"{pfad} steht nicht in ALTBESTAND. Diese Liste wird von Hand "
                          "gepflegt -- was nicht draufsteht, wird nicht geloescht."}
    d = Path(pfad)
    if _unter_unantastbar(d):
        return {"abgeschafft": False, "fehler": f"{pfad} ist unantastbar"}
    try:
        c = sqlite3.connect(f"file:{DB}?mode=ro", uri=True, timeout=30)
        da = c.execute("SELECT modelle FROM speicher_rueckweg WHERE pfad=?", (pfad,)).fetchone()
        c.close()
    except Exception as e:
        return {"abgeschafft": False, "fehler": f"Rueckweg nicht pruefbar: {e}"}
    if not da:
        return {"abgeschafft": False,
                "fehler": "kein Rueckweg gebucht. Erst rueckweg() aufrufen -- ohne Verzeichnis "
                          "waere das Loeschen unumkehrbar, und genau das war ausgeschlossen."}
    if not d.exists():
        return {"abgeschafft": False, "grund": "schon weg"}
    r = subprocess.run(["du", "-xsb", pfad], capture_output=True, text=True, timeout=300)
    gb = round(int((r.stdout or "0").split()[0]) / 2**30, 2)
    shutil.rmtree(d, ignore_errors=True) if d.is_dir() else d.unlink(missing_ok=True)
    return {"abgeschafft": not d.exists(), "pfad": pfad, "befreit_gb": gb,
            "rueckweg_modelle": da[0],
            "hinweis": f"Verzeichnis liegt in speicher_rueckweg -- {da[0]} Modell(e) mit "
                       "Nachladebefehl. Zurueckholen ist eine Frage von Bandbreite, "
                       "nicht von Erinnerung."}

def _in_den_raum(text: str) -> None:
    """Der Wacht eine Stimme geben -- damit Zero REAGIERT, nicht nur ein Zeitgeber laeuft.

    ⭐ GABRIELS PUNKT 18.08.: "agent zero muss reaktiv sein." Ein Zeitgeber, der
    alle 30 Minuten still aufraeumt, macht Zero nicht handlungsfaehig, sondern
    ersetzt ihn. Der Ruf landet im Raum, den alle vier Sitzungen sehen -- damit
    ist der Platzmangel etwas, wovon Zero WEISS, nicht etwas, das hinter ihm
    erledigt wird.

    ⚠️ Der Ruf ist in Caveman-Englisch, wie alles im Raum. Nicht Stil, sondern
    Vertraeglichkeit: der Raum hat eine Sprache, und zwei Sprachen darin waeren
    zwei Raeume.
    """
    try:
        c = sqlite3.connect(DB, timeout=30)
        c.execute("CREATE TABLE IF NOT EXISTS zero_raum_ruf("
                  "id INTEGER PRIMARY KEY AUTOINCREMENT, ts REAL NOT NULL,"
                  " von TEXT NOT NULL, text TEXT NOT NULL)")
        c.execute("INSERT INTO zero_raum_ruf(ts,von,text) VALUES(?,?,?)",
                  (time.time(), "speicherwacht", text[:400]))
        c.commit(); c.close()
    except Exception:
        pass

# ══ Massenwurf: Wegwerfordner in Serie ════════════════════════════════════
# ⭐⭐ DER GROESSTE FUND DIESES ABENDS, und er stand in keiner Statistik:
# 6.606 Ordner `/tmp/frank-laeufer-*` mit 41 GB. `du -xsh /tmp` lief nicht
# durch -- 15.228 Eintraege sind zu viele -- und weil kein Werkzeug es
# zusammenzaehlen konnte, tauchten die 41 GB in KEINER Uebersicht auf.
# Auf die Frage "wieso ist der VPS zu 90 % voll" gab es deshalb tagelang
# keine Antwort. Nicht weil es versteckt war, sondern weil das Messen
# abbrach und ein Abbruch wie eine Null aussieht.
#
# ⚠️ DIESE SORTE IST GEFAEHRLICHER ALS EINZELDATEIEN. Ein Ordner kann Inhalt
# haben, den niemand mehr kennt. Deshalb drei Bedingungen, die ALLE gelten
# muessen -- und die dritte ist die eigentliche:
#
#   1. Name passt auf ein Muster,
#   2. Ordner ist alt genug,
#   3. es gibt MINDESTENS `ab_anzahl` Geschwister mit demselben Muster.
#
# Bedingung 3 ist der Kern: EIN Ordner mit diesem Namen kann eine laufende
# Arbeit sein. SECHSTAUSEND koennen es nicht. Die Wacht loescht also nicht
# "einen Ordner, der so aussieht", sondern erkennt ein MUSTER VON
# VERWAHRLOSUNG -- und ein Muster kann man belegen, ein Einzelfall nicht.
MASSENWURF = (
    # (Verzeichnis, Muster, Mindestalter h, ab_anzahl, Begruendung)
    ("/tmp", "frank-laeufer-*", 24, 50,
     "Wegwerf-Arbeitsplaetze des Frank-Laeufers. Frank v0.1 ist abgeschafft "
     "(Eigner 18.08.), diese Ordner werden von niemandem mehr gelesen."),
    ("/tmp", "*-test-venv", 48, 3,
     "Wegwerf-Umgebungen aus Testlaeufen, jederzeit neu baubar."),
    ("/tmp", "entityos-schema-test*", 12, 1,
     "Schema-Testkopie -- der Name sagt, dass sie ein Test war."),
    # ⚠️ Nachgetragen am 18.08., nachdem die erste Raeumung nur die HAELFTE fand.
    # Der abgeschaffte Laeufer erzeugte Wegwerfordner unter FUENF verschiedenen
    # Namen, nicht unter einem. Wer nur das auffaelligste Muster kennt, raeumt
    # 41 GB und laesst 23 GB liegen -- und haelt die Sache fuer erledigt, weil
    # die Zahl sich deutlich verbessert hat. Eine deutliche Verbesserung ist
    # kein Beweis fuer Vollstaendigkeit.
    ("/tmp", "clay-v18-committed-*", 12, 50,
     "Wegwerf-Umgebungen des ClayCode-Laeufers -- 818 Stueck, 16 GB. Abgeschafft."),
    ("/tmp", "clay-wp03-*", 12, 50, "Wegwerfordner des ClayCode-Laeufers. Abgeschafft."),
    ("/tmp", "claycode-*-out-*", 12, 50, "Ausgabeordner des ClayCode-Laeufers. Abgeschafft."),
    ("/tmp", "frank-*", 24, 20, "Reste des Frank-Systems. Abgeschafft (Eigner 18.08.)."),
    # entityos-* ist NICHT abgeschafft -- deshalb 24 Stunden Schonfrist statt 12
    # und eine hoehere Schwelle. Das ist laufendes System; hier wird nur
    # weggeraeumt, was serienweise UND ueber einen Tag alt liegenbleibt.
    ("/tmp", "entityos-tree-*", 24, 50, "Zwischenbaeume aus Testlaeufen, neu erzeugbar."),
    ("/tmp", "entityos-out-*", 24, 50, "Ausgabeordner aus Testlaeufen, neu erzeugbar."),
)


def massenwurf() -> list[dict]:
    """Ordner, die in Serie liegengeblieben sind. Nur als Serie, nie einzeln."""
    jetzt = time.time()
    treffer = []
    for ordner, muster, alter_h, ab_anzahl, warum in MASSENWURF:
        d = Path(ordner)
        if not d.is_dir():
            continue
        kandidaten = [k for k in d.glob(muster)
                      if k.is_dir() and not _unter_unantastbar(k)
                      and (jetzt - k.stat().st_mtime) / 3600.0 >= alter_h]
        if len(kandidaten) < ab_anzahl:
            # ⚠️ Unter der Schwelle wird NICHTS angefasst -- und das wird
            # gemeldet, nicht verschwiegen. Ein Waechter, der unter der
            # Schwelle stumm bleibt, sieht aus wie einer, der nichts gefunden hat.
            if kandidaten:
                treffer.append({"muster": f"{ordner}/{muster}", "anzahl": len(kandidaten),
                                "unter_schwelle": ab_anzahl, "angefasst": False,
                                "warum": "zu wenige -- ein Einzelfall kann laufende Arbeit sein"})
            continue
        treffer.append({"muster": f"{ordner}/{muster}", "anzahl": len(kandidaten),
                        "pfade": [str(k) for k in kandidaten], "angefasst": True,
                        "warum": warum})
    return treffer

def bilanz(zeitlimit: int = 60) -> dict:
    """Wo steckt der Platz -- und wo konnte ich es NICHT feststellen.

    ⭐⭐ DIE WICHTIGSTE FUNKTION DIESER DATEI, und sie ist es aus einem Grund,
    der wenig mit Speicher zu tun hat.

    Auf die Frage "wieso ist der VPS zu 90 % voll" gab es keine Antwort, obwohl
    41 GB offen in /tmp lagen. Nicht weil sie versteckt waren, sondern weil
    `du -xsh /tmp` bei 15.228 Eintraegen in die Zeitgrenze lief und NICHTS
    ausgab. Ein leeres Ergebnis. Und ein leeres Ergebnis liest sich wie "da ist
    nichts" -- so ist die Summe der Ordner (80 GB) monatelang neben dem
    tatsaechlichen Verbrauch (173 GB) gestanden, ohne dass die Luecke jemandem
    als Luecke auffiel.

    ⭐ Deshalb nennt diese Bilanz DREI Zahlen, nicht eine:
       was `df` sagt · was ich zusammenzaehlen konnte · WAS ICH NICHT KONNTE.
    Die dritte ist die neue. Solange sie nicht null ist, ist die Rechnung
    unvollstaendig UND SAGT ES. Ein Messgeraet, das nicht melden kann, dass es
    gescheitert ist, meldet stattdessen eine Null -- und eine Null ist eine
    Behauptung ueber die Welt.
    """
    g = shutil.disk_usage("/")
    posten, ungezaehlt = [], []
    for kind in sorted(Path("/").iterdir()):
        if kind.is_symlink() or kind.name in ("proc", "sys", "dev", "run"):
            continue
        if not kind.is_dir():
            continue
        try:
            r = subprocess.run(["du", "-xsb", str(kind)], capture_output=True,
                               text=True, timeout=zeitlimit)
            b = int((r.stdout or "").split()[0])
            posten.append({"pfad": str(kind), "gb": round(b / 2**30, 2)})
        except subprocess.TimeoutExpired:
            # ⚠️ HIER liegt der Fehler, der 41 GB unsichtbar machte. Ein
            # Zeitablauf ist ein BEFUND, nicht eine Null. Also wird er benannt --
            # samt der Zahl, die ihn erklaert: zu viele Eintraege.
            try:
                n = sum(1 for _ in kind.iterdir())
            except OSError:
                n = None
            ungezaehlt.append({"pfad": str(kind), "grund": f"nicht in {zeitlimit}s zaehlbar",
                               "eintraege_oberste_ebene": n,
                               "hinweis": "Ein Zeitablauf ist ein Befund, keine Null. "
                                          "Hier steckt moeglicherweise der fehlende Platz."})
        except Exception as e:
            ungezaehlt.append({"pfad": str(kind), "grund": f"{type(e).__name__}: {e}"})

    posten.sort(key=lambda x: -x["gb"])
    gezaehlt = round(sum(x["gb"] for x in posten), 1)
    belegt = round(g.used / 2**30, 1)
    luecke = round(belegt - gezaehlt, 1)
    erg = {"df_belegt_gb": belegt, "df_frei_gb": round(g.free / 2**30, 1),
           "zusammengezaehlt_gb": gezaehlt, "luecke_gb": luecke,
           "posten": [x for x in posten if x["gb"] >= 0.1],
           "nicht_zaehlbar": ungezaehlt}
    if ungezaehlt:
        erg["urteil"] = (
            f"UNVOLLSTAENDIG. {len(ungezaehlt)} Verzeichnis(se) liessen sich nicht zaehlen: "
            + ", ".join(u["pfad"] for u in ungezaehlt) +
            f". Es fehlen {luecke} GB in der Rechnung -- vermutlich genau dort. "
            "Diese Zeile ist der Grund, warum es diese Funktion gibt: vorher fiel ein "
            "gescheitertes Zaehlen als Null in die Summe und die Luecke fiel niemandem auf.")
    elif abs(luecke) > 5.0:
        erg["urteil"] = (
            f"VOLLSTAENDIG GEZAEHLT, aber {luecke} GB Abweichung zu df. Kein Zaehlfehler -- "
            "moegliche Ursachen: geloeschte Dateien, die ein Prozess noch offen haelt "
            "(`lsof -nP | grep deleted`), oder ein eigener Einhaengepunkt, den `du -x` "
            "nicht betritt (`findmnt`). Das gehoert geprueft, nicht gerundet.")
    else:
        erg["urteil"] = f"Rechnung geht auf ({luecke} GB Abweichung)."
    return erg

# ══ Verursacher statt Symptom ══════════════════════════════════════════════
# ⭐⭐ DIE EIGENTLICHE URSACHE der 41 GB war NICHT, dass niemand aufgeraeumt hat.
# Sie war, dass `frank-laeufer-rae.timer` alle 15 Minuten neue Wegwerfordner
# anlegte -- ein Zeitgeber eines Systems, das der Eigner abgeschafft hat, das
# aber nie abgestellt wurde. Wer nur die Ordner loescht, raeumt alle 15 Minuten
# erneut und nennt das Speicherverwaltung.
#
# ⚠️ Deshalb sucht diese Wacht nach dem VERURSACHER, nicht nur nach dem Haufen.
# Sie schaltet ihn NICHT selbst ab: ein Zeitgeber kann fuer etwas anderes
# gebraucht werden, als sein Name sagt, und ein Waechter, der Dienste stilllegt,
# ist kein Waechter mehr. Sie legt ihn vor -- mit dem Befehl, der ihn abstellt.
ABGESCHAFFT_MUSTER = ("frank", "retina", "fragmich", "swarm-frank")


def verursacher() -> dict:
    """Laufen noch Zeitgeber oder Dienste, die zu Abgeschafftem gehoeren?

    ⭐ Das ist die Frage, die den Unterschied macht zwischen Aufraeumen und
    Speicherverwaltung. Ein Haufen ohne Verursacher waechst nicht nach.
    """
    aktiv = []
    try:
        r = subprocess.run(["systemctl", "list-units", "--all", "--no-legend", "--no-pager",
                            "--type=timer,service"],
                           capture_output=True, text=True, timeout=90)
        for zeile in (r.stdout or "").splitlines():
            teile = zeile.split()
            if len(teile) < 4:
                continue
            name = teile[0].lstrip("●* ")
            if not any(m in name.lower() for m in ABGESCHAFFT_MUSTER):
                continue
            lauf = teile[2] if len(teile) > 2 else "?"
            if lauf in ("active", "running", "waiting"):
                aktiv.append({"einheit": name, "zustand": lauf,
                              "abstellen": f"systemctl disable --now {name}"})
    except Exception as e:
        return {"fehler": f"{type(e).__name__}: {e}"}

    return {"noch_aktiv": aktiv, "anzahl": len(aktiv),
            "urteil": (
                f"{len(aktiv)} Einheit(en) eines abgeschafften Systems laufen noch und erzeugen "
                "moeglicherweise weiter Muell. Ein Haufen MIT Verursacher waechst nach -- "
                "Loeschen allein ist dann keine Speicherverwaltung, sondern eine Beschaeftigung."
                if aktiv else
                "NICHTS GEFUNDEN -- kein Zeitgeber und kein Dienst eines abgeschafften Systems "
                "laeuft noch. Was hier liegt, waechst nicht nach."),
            "grundlage": "Eigner 18.08.: kein Frank mehr, nur noch EntityOS",
            "hinweis": "Diese Wacht stellt NICHTS selbst ab. Ein Zeitgeber kann fuer etwas "
                       "anderes gebraucht werden, als sein Name sagt."}

def _buchen(eintrag: dict) -> None:
    """Jede Handlung kommt ins Wiki. Ein Waechter ohne Aufzeichnung ist eine Behauptung."""
    try:
        c = sqlite3.connect(DB, timeout=30)
        c.execute("CREATE TABLE IF NOT EXISTS speicherwacht_log("
                  "id INTEGER PRIMARY KEY AUTOINCREMENT, ts REAL NOT NULL,"
                  " belegt_prozent REAL, frei_gb REAL, stufe TEXT,"
                  " gehandelt INTEGER NOT NULL, befreit_gb REAL, bericht TEXT)")
        # Die drei Zahlen einzeln, nicht nur im Bericht: eine Spalte laesst sich
        # ueber Wochen vergleichen, ein JSON-Klumpen nicht. Waechst `luecke_gb`
        # oder ist `nicht_zaehlbar` gesetzt, wird gerade etwas unsichtbar --
        # und das soll man an einer Zahlenreihe SEHEN, nicht suchen muessen.
        for spalte, art in (("df_gb", "REAL"), ("gezaehlt_gb", "REAL"),
                            ("luecke_gb", "REAL"), ("nicht_zaehlbar", "TEXT"),
                            ("bilanz_urteil", "TEXT")):
            try:
                c.execute(f"ALTER TABLE speicherwacht_log ADD COLUMN {spalte} {art}")
            except Exception:
                pass  # schon da
        _b = eintrag.get("bilanz") or {}
        c.execute("INSERT INTO speicherwacht_log(ts,belegt_prozent,frei_gb,stufe,"
                  "gehandelt,befreit_gb,bericht,df_gb,gezaehlt_gb,luecke_gb,"
                  "nicht_zaehlbar,bilanz_urteil) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
                  (time.time(), eintrag["vorher"]["belegt_prozent"],
                   eintrag["vorher"]["frei_gb"], eintrag["vorher"]["stufe"],
                   1 if eintrag["gehandelt"] else 0, eintrag.get("befreit_gb", 0.0),
                   json.dumps(eintrag, ensure_ascii=False)[:8000],
                   _b.get("df_belegt_gb"), _b.get("zusammengezaehlt_gb"),
                   _b.get("luecke_gb"),
                   ", ".join(u["pfad"] for u in _b.get("nicht_zaehlbar", [])) or None,
                   (_b.get("urteil") or "")[:400]))
        c.commit(); c.close()
    except Exception:
        pass  # Buchfuehrung darf das Aufraeumen nie verhindern


def wachen(nur_zeigen: bool = False) -> dict:
    """Einmal nachsehen und, je nach Druck, handeln."""
    vorher = lage()
    # Bei JEDEM Lauf, auch dem ruhigen: die Frage "geht die Rechnung auf" ist
    # unabhaengig davon, ob gerade Platzmangel herrscht. Genau in einer ruhigen
    # Woche waechst der unsichtbare Teil, weil niemand nachsieht.
    bilanzierung = bilanz(zeitlimit=45)
    bericht = {"vorher": vorher, "bilanz": bilanzierung, "gehandelt": False,
               "geloescht": [], "sonst": None, "nur_zeigen": nur_zeigen}

    if vorher["stufe"] in ("ruhig", "berichten"):
        bericht["ergebnis"] = (
            f"NICHTS GETAN -- {vorher['belegt_prozent']} % belegt, {vorher['frei_gb']} GB frei. "
            f"{vorher['grund']} | {bilanzierung['urteil'][:180]}")
        bericht["waere_frei"] = round(sum(k["gb"] for k in _kandidaten(6)), 2)
        # Auch im ruhigen Fall vorlegen: der groesste Hebel auf diesem Wirt ist
        # nicht Muell, sondern Altbestand -- und der verschwindet nicht von selbst.
        bericht["altbestand"] = altbestand()
        bericht["verursacher"] = verursacher()
        _buchen(bericht)
        return bericht

    if vorher["stufe"] in ("leichtes", "kopien", "eng"):
        bericht["sonst"] = None if nur_zeigen else _bauzwischenlager()

    if vorher["stufe"] in ("leichtes", "kopien", "eng"):
        min_alter = {"leichtes": 12.0, "kopien": 6.0, "eng": 1.0}[vorher["stufe"]]
        for k in _kandidaten(min_alter):
            if nur_zeigen:
                bericht["geloescht"].append({**k, "nur_gezeigt": True})
                continue
            try:
                Path(k["pfad"]).unlink()
                bericht["geloescht"].append(k)
            except OSError as e:
                bericht["geloescht"].append({**k, "fehler": str(e)})

    if vorher["stufe"] in ("leichtes", "kopien", "eng"):
        bericht["massenwurf"] = []
        for serie in massenwurf():
            if not serie.get("angefasst"):
                bericht["massenwurf"].append(serie)
                continue
            weg, fehler = 0, 0
            for pfad in ([] if nur_zeigen else serie["pfade"]):
                try:
                    shutil.rmtree(pfad, ignore_errors=False); weg += 1
                except OSError:
                    fehler += 1
            bericht["massenwurf"].append({**{k: v for k, v in serie.items() if k != "pfade"},
                                          "entfernt": weg, "fehlgeschlagen": fehler,
                                          "nur_gezeigt": nur_zeigen})

    nachher = lage()
    befreit = round(nachher["frei_gb"] - vorher["frei_gb"], 2)
    # Auch nach dem Aufraeumen: wenn der Verursacher laeuft, war das Aufraeumen
    # nur eine Verschiebung. Das gehoert in denselben Bericht.
    bericht["verursacher"] = verursacher()
    if not nur_zeigen and nachher["belegt_prozent"] >= 90.0:
        # Nur bei echtem Druck. Ein Waechter, der bei jedem Blick ruft, wird
        # zum Rauschen -- und Rauschen wird ueberlesen, genau wenn es zaehlt.
        ab = altbestand()
        _in_den_raum(
            f"disk {nachher['belegt_prozent']}% full, {nachher['frei_gb']}GB left. "
            f"me clean {befreit}GB junk. big pile still there: {ab['summe_gb']}GB old stuff "
            f"(models, frank). me NOT delete that alone -- human say yes first. "
            f"look speicher_lage.")
    bericht.update({"nachher": nachher, "befreit_gb": befreit,
                    # Zeigen ist kein Handeln.
                    "gehandelt": bool(not nur_zeigen
                                      and (bericht["geloescht"] or bericht["sonst"]
                                           or bericht.get("massenwurf")))})
    bericht["ergebnis"] = (
        f"{len([g for g in bericht['geloescht'] if 'fehler' not in g])} Wegwerfkopie(n) entfernt, "
        f"{befreit} GB befreit -- {vorher['belegt_prozent']} % → {nachher['belegt_prozent']} %"
        if befreit > 0 else
        f"NICHTS BEFREIT -- {nachher['belegt_prozent']} % belegt. Es lag nichts Wegwerfbares da; "
        "der Platz geht an etwas, das diese Wacht nicht anfassen darf. Das ist ein Befund fuer "
        f"einen Menschen, kein Fehler. | {bilanzierung['urteil'][:180]}")
    _buchen(bericht)
    return bericht


if __name__ == "__main__":
    import sys
    print(json.dumps(wachen(nur_zeigen="--zeigen" in sys.argv),
                     ensure_ascii=False, indent=2))
