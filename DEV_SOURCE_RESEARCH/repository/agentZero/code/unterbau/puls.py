#!/usr/bin/env python3
"""puls.py — der Herzschlag von ClayVerse. Gebaut, um nicht auszusetzen.

FRANK_DATABASE_PULSE_CONTRACT, owner-fixed 2026-08-09:

    "Database Pulse is the endogenous state-and-cognition cycle of a
     FRANK-architecture entity. It is not an LLM inference loop."
    "A Pulse can occur with ZERO LLM calls."

Dieser Daemon macht genau das und nichts darüber hinaus. Er ruft die
mechanischen Phasen auf und führt die Zeit. Phase 10 — Modell, Werkzeug,
Peer — bleibt leer, und das ist der Normalfall, nicht die Ausnahme.

⚠️ Ein Prozess, kein Zeitgeber je Takt. Bei 4 Sekunden wären das 21.600
Prozessstarts am Tag; der Interpreterstart allein käme auf rund eine halbe
Stunde CPU.


HÄRTUNG 2026-08-15 — Eigner: „der puls muss so gebaut sein, dass er nicht
fehlen kann, egal was passiert."

Anlass war eine Messung, kein Verdacht: ein Takt brauchte 30.048.930 µs.
Das ist auf die Mikrosekunde der `busy_timeout` von 30 s. Der Puls hat also
eine halbe Minute auf eine Datenbanksperre gewartet — und ein Herzschlag,
der 30 s auf eine Sperre wartet, hat aufgehört, einer zu sein.
(Der Median lag bei 950 µs. Der MITTELWERT lag bei 209.422 µs und sah nach
einem kaputten Puls aus. Erst das Messgerät, dann das Ergebnis.)

Sieben Wege, auf denen er bisher stehenbleiben konnte, und was jetzt gilt:

  1 Sperre       busy_timeout 30 s -> 200 ms. Belegt heisst AUFSCHIEBEN,
                 nicht warten. Der Takt fällt deswegen nicht aus.
  2 Datenbank    Der Takt hing an ihr. Jetzt geht jeder Takt ZUERST ins
                 Journal (Anhängen an eine Datei, keine Sperre) und erst
                 danach in die Datenbank. Ist die Datenbank weg, schlägt der
                 Puls weiter UND bleibt sichtbar.
  3 Start        `import vorprozessor` und `connect` liefen ungeschützt. Ein
                 Fehler dort hiess: kein Puls. Jetzt schlägt er auch ohne
                 Vorprozessor und ohne Datenbank — mit `art=notlauf`, damit
                 niemand einen Notlauf für Gesundheit hält.
  4 Verbindung   Bricht sie im Lauf (Datei ersetzt, Platte voll), wird neu
                 verbunden statt gestorben.
  5 Ausnahmen    Gefangen wurde nur OperationalError. Jetzt jede Ausnahme.
                 Ein Takt darf sterben, der Herzschlag nicht.
  6 Hänger       Bleibt der Vorprozessor stehen, half bisher nichts. Jetzt
                 bricht SIGALRM ihn nach 3 s ab — kürzer als der Takt.
  7 Aufhängen    systemd-Wachhund: jeder Takt meldet sich. Meldet sich 60 s
                 keiner, tötet und startet systemd den Dienst.

⚠️ ABWEICHUNG VON DER HAUSREGEL, bewusst und begründet.
Bisher galt: kein `Restart=always`, weil ein Dienst, der sich endlos selbst
neu startet, gesund aussieht, während er scheitert. Für einen HERZSCHLAG
kehrt sich das um — er muss schlagen. Deshalb hier `Restart=always`, aber
mit zwei Gegengewichten, damit die alte Regel nicht einfach verloren geht:
`StartLimitBurst` deckelt einen Neustartsturm, und JEDER Neustart wird
gezählt (`pu_lage.neustarts`) und mit Zeitstempel geführt. Ein Puls, der
sich 20-mal in der Stunde neu startet, ist damit MESSBAR krank, statt
unauffällig zu wirken.
"""
import json
import os
import signal
import sqlite3
import socket
import sys
import time
from collections import deque
from datetime import datetime, timezone

sys.path.insert(0, "/opt/clayverse/werkzeug")

DB = os.environ.get("CLAY_DB", "/var/lib/clay/wiki.db")
TAKT = float(os.environ.get("CLAY_TAKT", "4.0"))
# Lebenszeichen je N-tem Leertakt — bei 4 s also einmal pro Minute
LEBENSZEICHEN_JE = int(os.environ.get("CLAY_LEBENSZEICHEN", "15"))
KENNUNG = "/var/lib/clay/clay_id"
JOURNAL = os.environ.get("CLAY_PULS_JOURNAL", "/var/lib/clay/puls.jsonl")

# ⚠️ 200 ms, nicht 30 s. Wer länger wartet, hat den Takt schon verloren.
SPERRE_MS = int(os.environ.get("CLAY_SPERRE_MS", "200"))
# Frist für den Vorprozessor. Muss KÜRZER sein als der Takt, sonst staut es.
FRIST_S = float(os.environ.get("CLAY_FRIST_S", "3.0"))
# So viele unerledigte Zeilen hält der Puls höchstens im Arbeitsspeicher.
# Darüber hinaus lebt die Wahrheit im Journal — dort geht nichts verloren.
STAU_MAX = 500

_laeuft = True


class Frist(Exception):
    """Der Vorprozessor hat seine Frist überschritten."""


def _jetzt() -> str:
    return datetime.now(timezone.utc).isoformat()


def _clay_id() -> str:
    try:
        return open(KENNUNG, encoding="utf-8").read().strip()
    except OSError:
        return "UNBEKANNT"


def _boot_id() -> str:
    try:
        return open("/proc/sys/kernel/random/boot_id", encoding="utf-8").read().strip()
    except OSError:
        return "unbekannt"


# ── ZEITORIENTIERUNG ───────────────────────────────────────────────────
# Eigner 2026-08-15: „clayverse soll ueber den puls in der zeit orientiert
# sein ... in jedem prompt soll die uhrzeit sein anhand des pulses ...
# der puls soll die zeitzone automatisch miteinbeziehen."
#
# ⚠️ GESPEICHERT WIRD IMMER UTC. Eine Ortszeit in der Datenbank ist zweimal
#    im Jahr mehrdeutig — in der Nacht der Zeitumstellung gibt es 02:30 Uhr
#    zweimal. Die Ortszeit ist eine ANZEIGE, nie eine Ablage.
# ⚠️ Und die Zeitzone wird NICHT als Zahl hinterlegt. „+2" waere im Winter
#    falsch. zoneinfo schaltet die Sommerzeit selbst um; genau das ist mit
#    „automatisch" gemeint.
MENSCHZONE = os.environ.get("CLAY_ZONE", "Europe/Vienna")
JETZT_DATEI = os.environ.get("CLAY_JETZT", "/var/lib/clay/jetzt.txt")

TAGE = ("Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag",
        "Samstag", "Sonntag")
MONATE = ("Januar", "Februar", "Maerz", "April", "Mai", "Juni", "Juli",
          "August", "September", "Oktober", "November", "Dezember")


def _dauer(s: float) -> str:
    """Sekunden so, wie ein Mensch sie sagt. Fuer das LLM lesbar."""
    s = int(max(0, s))
    if s < 60:
        return "%d s" % s
    if s < 3600:
        return "%d min %d s" % (s // 60, s % 60)
    if s < 86400:
        return "%d h %d min" % (s // 3600, (s % 3600) // 60)
    return "%d Tage %d h" % (s // 86400, (s % 86400) // 3600)


def _zeitbild(luecke_s=None, wach_seit_mono=None) -> dict:
    """Wo ClayVerse gerade in der Zeit steht. Kein Modellaufruf, reine Rechnung."""
    u = datetime.now(timezone.utc)
    bild = {"utc": u.isoformat(timespec="seconds"), "epoche": int(u.timestamp())}
    try:
        from zoneinfo import ZoneInfo
        o = u.astimezone(ZoneInfo(MENSCHZONE))
        bild.update({
            "zone": MENSCHZONE,
            "ortszeit": o.strftime("%Y-%m-%d %H:%M:%S"),
            "kuerzel": o.tzname(),                       # CEST / CET, selbst umgeschaltet
            "abstand_utc": "%+.0f h" % (o.utcoffset().total_seconds() / 3600),
            "sommerzeit": bool(o.dst()),
            "wochentag": TAGE[o.weekday()],
            "monat": MONATE[o.month - 1],
            "kalenderwoche": o.isocalendar().week,
            "tag_im_jahr": int(o.strftime("%j")),
        })
    except Exception as ex:
        # ⚠️ Faellt die Zonendatenbank aus, wird NICHT auf einen festen
        #    Stundenwert zurueckgefallen. Lieber ehrlich UTC anzeigen.
        bild["zone_fehler"] = str(ex)[:120]
    if luecke_s is not None:
        bild["offline_war"] = _dauer(luecke_s)
        bild["offline_s"] = round(luecke_s, 1)
    if wach_seit_mono is not None:
        bild["wach_seit"] = _dauer(time.monotonic() - wach_seit_mono)
    return bild


def _jetzt_zeile(bild: dict, folge: int, luecke_s=None) -> str:
    """EINE Zeile fuer jeden Prompt. Kurz, weil sie in JEDEN Prompt geht."""
    t = bild.get("ortszeit", bild["utc"])
    k = bild.get("kuerzel", "UTC")
    teile = ["%s, %s %s (UTC %s)" % (bild.get("wochentag", ""), t, k, bild["utc"][11:19])]
    teile.append("Puls %d" % folge)
    if bild.get("wach_seit"):
        teile.append("wach %s" % bild["wach_seit"])
    if luecke_s and luecke_s > 60:
        teile.append("⚠ zuvor %s offline" % _dauer(luecke_s))
    return " · ".join(x for x in teile if x)


def _jetzt_schreiben(zeile: str) -> None:
    """Legt die Zeile dorthin, wo jeder Promptbauer sie billig liest.

    Erst in eine Nachbardatei, dann umbenennen — damit ein Leser nie eine
    halb geschriebene Zeile erwischt.
    """
    try:
        tmp = JETZT_DATEI + ".neu"
        with open(tmp, "w", encoding="utf-8") as f:
            f.write(zeile + "\n")
        os.replace(tmp, JETZT_DATEI)
    except OSError:
        pass


def _halt(signum, rahmen):
    global _laeuft
    _laeuft = False


def _frist_abgelaufen(signum, rahmen):
    raise Frist()


# ── systemd-Wachhund ───────────────────────────────────────────────────
# Reines Python, keine Fremdbibliothek: eine Zeile auf den Notify-Socket.
# Fehlt der Socket (Start von Hand), tut das hier schlicht nichts.
_notify_pfad = os.environ.get("NOTIFY_SOCKET")
_notify = None
if _notify_pfad:
    try:
        _notify = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
        if _notify_pfad.startswith("@"):
            _notify_pfad = "\0" + _notify_pfad[1:]
    except OSError:
        _notify = None


def _melde(was: str) -> None:
    """Meldet an systemd. Scheitert das, ist es NIE ein Grund zu sterben."""
    if not _notify:
        return
    try:
        _notify.sendto(was.encode(), _notify_pfad)
    except OSError:
        pass


# ── Journal: die Wahrheit über den Herzschlag ──────────────────────────
# Anhängen an eine Datei braucht keine Datenbanksperre und keinen anderen
# Prozess. Solange das Dateisystem schreibt, ist der Puls belegt — auch
# wenn die Datenbank belegt, ersetzt oder kaputt ist.
_journal = None


def _journal_offen():
    global _journal
    if _journal is None:
        try:
            _journal = open(JOURNAL, "a", encoding="utf-8")
        except OSError:
            _journal = False        # einmal gescheitert, nicht je Takt erneut
    return _journal or None


def _ins_journal(zeile: dict) -> bool:
    f = _journal_offen()
    if not f:
        return False
    try:
        f.write(json.dumps(zeile, ensure_ascii=False) + "\n")
        f.flush()
        return True
    except OSError:
        return False


def _letzte_journalzeit():
    """Letzter Takt laut Journal — falls die Datenbank nichts hergibt.

    Liest nur das Ende der Datei. Bei einem Journal von vielen Megabyte
    waere das Ganze zu lesen teuer und voellig unnoetig.
    """
    try:
        with open(JOURNAL, "rb") as f:
            f.seek(0, os.SEEK_END)
            groesse = f.tell()
            f.seek(max(0, groesse - 8192))
            zeilen = f.read().decode("utf-8", "replace").splitlines()
        for z in reversed(zeilen):
            try:
                return json.loads(z).get("zeit")
            except Exception:
                continue
    except OSError:
        pass
    return None


# ── Datenbank: Archiv, nicht Lebensader ────────────────────────────────
def _verbinden():
    """Verbindet, oder gibt None zurück. Scheitern ist hier kein Fehler."""
    try:
        c = sqlite3.connect(DB, timeout=SPERRE_MS / 1000.0)
        c.row_factory = sqlite3.Row
        c.execute("PRAGMA journal_mode=WAL")
        c.execute("PRAGMA busy_timeout=%d" % SPERRE_MS)
        _tabellen(c)
        return c
    except Exception:
        return None


def _tabellen(c: sqlite3.Connection) -> None:
    """Der Puls führt sein eigenes Buch. Zeit und Zähler getrennt."""
    c.execute("""CREATE TABLE IF NOT EXISTS pu_takt (
        folge INTEGER PRIMARY KEY,
        clay_id TEXT NOT NULL,
        zeit TEXT NOT NULL,
        monoton REAL NOT NULL,
        boot_id TEXT NOT NULL,
        art TEXT NOT NULL,
        delta INTEGER NOT NULL DEFAULT 0,
        kosten_us REAL,
        modellaufrufe INTEGER NOT NULL DEFAULT 0,
        werkzeugaufrufe INTEGER NOT NULL DEFAULT 0,
        detail TEXT
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS pu_lage (
        schluessel TEXT PRIMARY KEY, wert TEXT NOT NULL, zeit TEXT NOT NULL
    )""")
    c.commit()


def _setz(c, schluessel, wert) -> None:
    c.execute("INSERT INTO pu_lage(schluessel,wert,zeit) VALUES (?,?,?) "
              "ON CONFLICT(schluessel) DO UPDATE SET wert=excluded.wert, zeit=excluded.zeit",
              (schluessel, str(wert), _jetzt()))


def _hol(c, schluessel, vorgabe=None):
    try:
        r = c.execute("SELECT wert FROM pu_lage WHERE schluessel=?", (schluessel,)).fetchone()
        return r[0] if r else vorgabe
    except Exception:
        return vorgabe


def _abfluss(c, stau: deque, lage: dict) -> sqlite3.Connection:
    """Schiebt Aufgestautes in die Datenbank. Gelingt es nicht, bleibt es liegen.

    ⚠️ Diese Funktion darf NIE eine Ausnahme nach oben lassen. Sie ist die
    einzige Stelle, an der der Puls die Datenbank berührt, und die Datenbank
    ist ausdrücklich NICHT lebensnotwendig für den Herzschlag.
    """
    if c is None:
        c = _verbinden()
        if c is None:
            return None
    try:
        while stau:
            z = stau[0]
            c.execute(
                "INSERT OR REPLACE INTO pu_takt(folge,clay_id,zeit,monoton,boot_id,art,"
                "delta,kosten_us,modellaufrufe,werkzeugaufrufe,detail) "
                "VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                (z["folge"], z["clay_id"], z["zeit"], z["monoton"], z["boot_id"],
                 z["art"], z["delta"], z["kosten_us"], 0, 0, z["detail"]))
            stau.popleft()
        for k, v in lage.items():
            _setz(c, k, v)
        c.commit()
        return c
    except Exception:
        # Verbindung verwerfen und beim nächsten Takt neu aufbauen. Der Stau
        # bleibt stehen; das Journal hat die Zeilen ohnehin schon.
        try:
            c.close()
        except Exception:
            pass
        return None


def takt(vp, folge: int, kid: str, boot: str) -> dict:
    """Ein Takt. Phasen 1 bis 5 mechanisch, Phase 10 bleibt leer.

    Der Vertrag verlangt, dass modellaufrufe und pulse_count getrennt
    gezählt werden: ein Puls kann ohne Modellaufruf ablaufen, und ein
    Modellaufruf ist kein Puls.

    ⚠️ Der Vorprozessor bekommt eine FRIST. Bleibt er stehen, bricht
    SIGALRM ihn ab und der Takt wird trotzdem fertig. Ohne das kann ein
    einziger hängender Aufruf den ganzen Herzschlag anhalten.
    """
    t0 = time.perf_counter()
    if vp is None or _TAKT_DB[0] is None:
        # ⚠️ Ohne Verbindung wird der Vorprozessor GAR NICHT gerufen. Ihm None
        # zu reichen und die Ausnahme als Fehler zu buchen waere unehrlich —
        # es ist kein Fehler, es ist ein Notlauf, und der heisst so.
        e = {"art": "notlauf", "delta": 0,
             "grund": ("Vorprozessor nicht geladen" if vp is None
                       else "keine Datenbankverbindung") + " — Puls schlaegt, Phasen 1-5 aus"}
    else:
        try:
            signal.setitimer(signal.ITIMER_REAL, FRIST_S)
            try:
                e = vp.puls(_TAKT_DB[0])   # Phase 1-5: Änderungen, Ausbreitung, Lernen
            finally:
                signal.setitimer(signal.ITIMER_REAL, 0)
        except Frist:
            e = {"art": "fehler", "delta": 0,
                 "fehler": "Vorprozessor ueber Frist (%.1fs) — abgebrochen" % FRIST_S}
        except Exception as ex:      # ein Takt darf sterben, der Herzschlag nicht
            e = {"art": "fehler", "delta": 0, "fehler": str(ex)[:200]}
    e["kosten_us"] = round((time.perf_counter() - t0) * 1e6, 1)
    return e


# Der Vorprozessor braucht eine Verbindung. Sie liegt hier, damit `takt`
# sie nicht als Parameter durchreichen muss und der Aufruf auch dann
# funktioniert, wenn zwischendurch neu verbunden wurde.
_TAKT_DB = [None]


def main() -> int:
    signal.signal(signal.SIGTERM, _halt)
    signal.signal(signal.SIGINT, _halt)
    signal.signal(signal.SIGALRM, _frist_abgelaufen)

    kid, boot = _clay_id(), _boot_id()

    # ⚠️ Der Import darf den Puls nicht verhindern. Scheitert er, schlägt der
    # Puls im Notlauf weiter — sichtbar als art=notlauf, nicht als Gesundheit.
    try:
        import vorprozessor as vp
    except Exception as ex:
        vp = None
        _ins_journal({"zeit": _jetzt(), "art": "startfehler", "clay_id": kid,
                      "detail": "vorprozessor nicht ladbar: %s" % str(ex)[:200]})

    c = _verbinden()
    _TAKT_DB[0] = c

    folge = int(_hol(c, "letzte_folge", "0") if c else 0) + 1
    neustarts = int(_hol(c, "neustarts", "0") if c else 0) + 1

    # ── WIEDERAUFNAHME ─────────────────────────────────────────────────
    # Eigner: „auch nach abstuerzen muss der puls immer recovern und am
    # besten die systemzeit abgleichen um zu erfahren wie lange er offline
    # war, was das llm sehen kann."
    #
    # Die Luecke wird aus der WANDUHR berechnet, nicht aus der Monotonen —
    # die faengt nach einem Neustart bei null an und weiss nichts von der
    # Zeit dazwischen. Genau deshalb braucht es beide Uhren.
    letzter = _hol(c, "letzter_takt") if c else None
    if not letzter:
        letzter = _letzte_journalzeit()
    luecke_s = None
    if letzter:
        try:
            weg = datetime.fromisoformat(letzter)
            if weg.tzinfo is None:
                weg = weg.replace(tzinfo=timezone.utc)
            luecke_s = max(0.0, (datetime.now(timezone.utc) - weg).total_seconds())
        except Exception:
            luecke_s = None

    wach_mono = time.monotonic()
    stau = deque()
    lage = {"neustarts": neustarts, "clay_id": kid, "boot_id": boot,
            "wach_seit": _jetzt(),
            "letzter_neustart": _jetzt(),
            "vorprozessor": "geladen" if vp else "FEHLT"}
    if luecke_s is not None:
        lage["letzte_luecke_s"] = round(luecke_s, 1)
        lage["letzte_luecke"] = _dauer(luecke_s)
        # ⚠️ Die Luecke wird als eigene Zeile geschrieben, nicht nur als
        #    Zaehler. Ein Ausfall, den man nur als Zahl sieht, verschwindet
        #    im Rauschen; als Takt im Journal steht er in der Zeitreihe.
        _ins_journal({"folge": folge - 1, "clay_id": kid, "zeit": _jetzt(),
                      "monoton": wach_mono, "boot_id": boot,
                      "art": "wiederaufnahme", "delta": 0, "kosten_us": 0.0,
                      "detail": json.dumps(
                          {"war_offline": _dauer(luecke_s),
                           "offline_s": round(luecke_s, 1),
                           "letzter_takt_war": letzter,
                           "neustart_nr": neustarts,
                           "zeit": _zeitbild()}, ensure_ascii=False)[:600]})
    c = _abfluss(c, stau, lage)
    _TAKT_DB[0] = c

    _melde("READY=1")
    _melde("STATUS=Puls wach, Takt %.1fs" % TAKT)
    print("puls: %s wach, Takt %ss, Folge ab %s, Neustart Nr. %s, Vorprozessor %s"
          % (kid, TAKT, folge, neustarts, "geladen" if vp else "FEHLT"), flush=True)

    uebersprungen = 0
    ohne_db = 0
    while _laeuft:
        anfang = time.monotonic()

        # ⚠️ Der Wachhund wird VOR der Arbeit bedient. Hängt die Arbeit
        # trotz Frist, greift systemd — das ist die letzte Sicherung.
        _melde("WATCHDOG=1")

        e = takt(vp, folge, kid, boot)

        leer = e.get("art") == "leer"
        if (not leer) or folge % LEBENSZEICHEN_JE == 0:
            zeile = {"folge": folge, "clay_id": kid, "zeit": _jetzt(),
                     "monoton": time.monotonic(), "boot_id": boot,
                     "art": e.get("art", "unbekannt"), "delta": int(e.get("delta", 0)),
                     "kosten_us": e.get("kosten_us"),
                     "detail": json.dumps(e, ensure_ascii=False)[:600]}
            # 1. Journal — hier gilt der Takt als geschlagen.
            _ins_journal(zeile)
            # 2. Datenbank — Archiv. Klappt sie nicht, staut es sich hier.
            if len(stau) < STAU_MAX:
                stau.append(zeile)

        # Die Zeitzeile fuer JEDEN Prompt — bei jedem Takt frisch, damit
        # kein Promptbauer rechnen oder die Datenbank fragen muss.
        bild = _zeitbild(luecke_s, wach_mono)
        _jetzt_schreiben(_jetzt_zeile(bild, folge, luecke_s))

        lage = {"letzte_folge": folge, "takte_gesamt": folge,
                "letzter_takt": _jetzt(), "stau": len(stau),
                "ortszeit": bild.get("ortszeit", ""),
                "zone": "%s %s" % (bild.get("zone", ""), bild.get("kuerzel", "")),
                "sommerzeit": bild.get("sommerzeit", "")}
        if not leer:
            lage["letzte_arbeit"] = _jetzt()
        c = _abfluss(c, stau, lage)
        _TAKT_DB[0] = c
        if c is None:
            ohne_db += 1
            if ohne_db in (1, 15, 150, 1500):   # nicht bei jedem Takt jammern
                print("puls: schlaegt ohne Datenbank weiter (%d Takte, %d gestaut)"
                      % (ohne_db, len(stau)), flush=True)
        else:
            if ohne_db:
                print("puls: Datenbank wieder da nach %d Takten" % ohne_db, flush=True)
            ohne_db = 0

        folge += 1

        rest = TAKT - (time.monotonic() - anfang)
        if rest > 0:
            # in kleinen Schritten schlafen, damit SIGTERM sofort greift
            ende = time.monotonic() + rest
            while _laeuft and time.monotonic() < ende:
                time.sleep(min(0.25, max(0.0, ende - time.monotonic())))
        else:
            # Der Takt hat länger gedauert als der Takt. Nicht aufstauen.
            uebersprungen += 1

    _melde("STOPPING=1")
    _abfluss(c, stau, {"schlaf_seit": _jetzt(), "uebersprungen": uebersprungen})
    print("puls: angehalten bei Folge %d, %d Takte uebersprungen, %d gestaut"
          % (folge - 1, uebersprungen, len(stau)), flush=True)
    return 0


def cmd_zeit() -> int:
    """Wo ClayVerse in der Zeit steht. Fuer Menschen und fuer Prompts."""
    c = _verbinden()
    folge = int(_hol(c, "letzte_folge", "0") if c else 0)
    letzter = _hol(c, "letzter_takt") if c else _letzte_journalzeit()
    alter = None
    if letzter:
        try:
            w = datetime.fromisoformat(letzter)
            if w.tzinfo is None:
                w = w.replace(tzinfo=timezone.utc)
            alter = (datetime.now(timezone.utc) - w).total_seconds()
        except Exception:
            pass
    bild = _zeitbild()
    print(_jetzt_zeile(bild, folge))
    print()
    for k in ("utc", "ortszeit", "zone", "kuerzel", "abstand_utc", "sommerzeit",
              "wochentag", "monat", "kalenderwoche", "tag_im_jahr"):
        if k in bild:
            print("  %-14s %s" % (k, bild[k]))
    if alter is not None:
        # ⚠️ Der wichtigste Wert hier: schlaegt der Puls JETZT noch?
        #    Ein Zeitbild aus einer toten Quelle ist schlimmer als keines.
        print("  %-14s %s %s" % ("letzter Takt", _dauer(alter) + " her",
                                 "" if alter < 60 else "⚠ Puls schweigt"))
    print("  %-14s %s" % ("neustarts", _hol(c, "neustarts", "?") if c else "?"))
    print("  %-14s %s" % ("letzte Luecke", _hol(c, "letzte_luecke", "-") if c else "-"))
    return 0


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "zeit":
        sys.exit(cmd_zeit())
    # ⚠️ Letzte Sicherung. Selbst wenn main() an etwas Unerwartetem scheitert,
    # darf der Prozess nicht still verschwinden — er meldet es und überlässt
    # systemd den Neustart.
    try:
        sys.exit(main())
    except SystemExit:
        raise
    except BaseException as ex:
        _ins_journal({"zeit": _jetzt(), "art": "absturz", "detail": str(ex)[:400]})
        print("puls: ABSTURZ %s" % str(ex)[:200], file=sys.stderr, flush=True)
        sys.exit(1)
