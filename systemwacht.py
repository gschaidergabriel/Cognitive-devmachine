#!/usr/bin/env python3
"""Systemwacht -- live Zustand der Tailscale-Maschinen fuer die Systeme-Bubble.

Gabriel 19.08.: eine ausklappbare Bubble links im Chat, die zeigt welche Systeme
per Tailscale verbunden sind (VPS, Andreas-PC, sein PC), ob sie online sind, die
wichtigsten Hardware-Stats und Speicher frei/belegt -- alles live.

Laeuft als systemd-Timer auf dem VPS (Host, NICHT im Container -- nur der Host
hat tailscale + SSH zu den PCs). Schreibt /var/lib/clay/systeme.json; der
entityos-Container liest denselben Pfad ueber den Bind-Mount und liefert ihn
unter /api/systeme aus.

Grenzen ehrlich abgebildet:
  - VPS    (self)            : Stats direkt.
  - Gabriel-PC (100.70.87.28): Stats per SSH vom VPS (Key liegt).
  - Andreas-PC (100.92.234.52): SSH verweigert (kein Key) -> Online-Status per
    tailscale, Stats erst wenn ein Key liegt. Kein Schaetzen, kein Erfinden.

Gabriel 19.08. (2): zusaetzlich "Dienste" -- die EntityOS-Prozesse selbst, je
EIN Wort + an/aus, fuer die Dienste-Unterseite der Bubble. Reine Anzeige: der
Sammler MISST nur (systemctl is-active / docker health / Prozess-Check),
er greift NICHT ein (kein Auto-Restart -- das ist bewusst Andreas' bzw.
Gabriels separates Immunsystem-Vorhaben, nicht dieser Sammler).

Gabriel 19.08. (3): manuelle Steuerung. Die DIENSTE-Liste hier ist jetzt die
EINZIGE Quelle der Wahrheit fuer die Whitelist des Host-Ausfuehrers
(dienststeuerung.py importiert sie direkt) -- ein Dienst, der hier nicht
"steuerbar": True traegt, kann per Knopf in der Bubble nie gestartet/gestoppt
werden, egal was das Frontend schickt. Zusaetzlich liefert der Sammler jetzt
je Dienst eine kurze "beschreibung" (systemctl Description, sonst der
"hinweis"-Fallback hier) und separat den Immunsystem-Status + die letzten
Journal-Zeilen von eos-immune.service (existiert die Unit noch nicht, wird
das sauber als "noch nicht aktiv" gemeldet -- kein Crash).
"""
import json
import os
import subprocess
import tempfile
import time

ZIEL = "/var/lib/clay/systeme.json"

# Ein portabler Stats-Einzeiler: laeuft lokal (VPS) UND per SSH (Linux-PC).
# Gibt EINE Zeile: last1|kerne|memTotalKB|memAvailKB|diskTotalKB|diskUsedKB|diskAvailKB
STATS_SH = (
    "export LC_ALL=C; "   # sonst formatiert awk unter de_DE 1.33 als 1,33 -> float() kaputt
    "read -r l1 _ < /proc/loadavg; n=$(nproc); "
    "mt=$(awk '/^MemTotal/{print $2}' /proc/meminfo); "
    "ma=$(awk '/^MemAvailable/{print $2}' /proc/meminfo); "
    "df -P / | awk 'NR==2{t=$2;u=$3;a=$4} END{printf \"%s|%s|%s|%s|%s|%s|%s\\n\","
    "'\"$l1\"','\"$n\"','\"$mt\"','\"$ma\"',t,u,a}'"
)

# Die drei Maschinen, die Gabriel sehen will -- per Tailscale-IP identifiziert
# (stabiler als der Hostname). "hol" = wie man an die Stats kommt.
MASCHINEN = [
    {"id": "vps",     "name": "VPS",        "rolle": "clayverse · frank-api", "ip": None,            "hol": "lokal", "ssh_ziel": None},
    {"id": "gabriel", "name": "Gabriel-PC", "rolle": "ai-core-node",          "ip": "100.70.87.28",  "hol": "ssh",   "ssh_ziel": "100.70.87.28"},
    {"id": "andreas", "name": "Andreas-PC", "rolle": "andreas-MACO",          "ip": "100.92.234.52", "hol": "ssh",   "ssh_ziel": "andreas@100.92.234.52"},
]

# Die EntityOS-Dienste fuer die "Dienste"-Unterseite -- je EIN Wort + wie man
# den Status misst. "art": systemd (is-active) | docker (Health/Running) |
# prozess (pgrep). Nur echte, gepruefte Units -- nichts erfunden, gegengeprueft
# per `systemctl list-units --all 'clayverse-*' 'entityos-*' 'eos-*'` + `docker
# ps` + `pgrep` am 19.08.
#
# "steuerbar": True -- der Dienst bekommt Start/Stopp/Neu-Knoepfe in der Bubble
# UND landet in der Whitelist des Host-Ausfuehrers (dienststeuerung.py). False
# heisst: nur Anzeige, niemals ausfuehrbar (z.B. Warmpool -- ein Momentan-
# Prozess ohne systemd-Einheit, den man nicht sauber "neu starten" kann).
# "kritisch": True nur bei der Oberflaeche -- ohne den Container ist die ganze
# Seite weg; das Frontend markiert das eigens, der Knopf bleibt aber da (Wunsch
# des Eigners: steuerbar, aber klar gekennzeichnet).
# "hinweis": Ein-Satz-Fallback, falls `systemctl show -p Description` nichts
# liefert (v.a. bei docker/prozess, die keine systemd-Beschreibung haben).
DIENSTE = [
    {"name": "Oberfläche",  "art": "docker",  "unit": "entityos", "steuerbar": True, "kritisch": True,
     "hinweis": "Die Weboberfläche und der Chat-Zugang von Zero (Docker-Container). "
                "Kritisch: ohne sie ist die Seite nicht erreichbar."},
    {"name": "Kern",        "art": "systemd", "unit": "clayverse-kern.service", "steuerbar": True},
    {"name": "Puls",        "art": "systemd", "unit": "clayverse-puls.service", "steuerbar": True},
    {"name": "Verdichtung", "art": "systemd", "unit": "clayverse-verdichtung.service", "steuerbar": True},
    {"name": "Wiki",        "art": "systemd", "unit": "clayverse-wikiarbeit.service", "steuerbar": True},
    {"name": "Systemwacht", "art": "systemd", "unit": "eos-systeme.timer", "steuerbar": True},
    {"name": "Anmeldung",   "art": "systemd", "unit": "eos-anmeldung.timer", "steuerbar": True},
    {"name": "Abruf",       "art": "systemd", "unit": "entityos-abrufpolitik.timer", "steuerbar": True},
    {"name": "Wegeverfall", "art": "systemd", "unit": "entityos-abrufverfall.timer", "steuerbar": True},
    {"name": "Abrufkarte",  "art": "systemd", "unit": "entityos-abrufkarte.timer", "steuerbar": True},
    {"name": "Backup",      "art": "systemd", "unit": "eos-homepage-backup.timer", "steuerbar": True},
    {"name": "Warmpool",    "art": "prozess", "unit": "input-format stream-json", "steuerbar": False,
     "hinweis": "Vorgewärmte Claude-Code-Prozesse, damit der erste Zug nach einem Neustart nicht kalt "
                "ist. Kein systemd-Dienst -- nicht per Knopf steuerbar."},
    # -- 19.08. (2) ergaenzt: die restlichen realen EntityOS-Units, alle oben
    # gegengeprueft (nichts erfunden). Periodische Jobs zeigen bewusst den
    # .timer (Zeitplan an/aus) statt des .service (das waere nur waehrend des
    # kurzen Laufs "an") -- gleiche Logik wie bei den zwoelf schon vorhandenen.
    {"name": "Eichung",        "art": "systemd", "unit": "clayverse-eichung.timer", "steuerbar": True},
    {"name": "GitHub",         "art": "systemd", "unit": "clayverse-github.timer", "steuerbar": True},
    {"name": "Karte",          "art": "systemd", "unit": "clayverse-karte.timer", "steuerbar": True},
    {"name": "Kuration",       "art": "systemd", "unit": "clayverse-kuration.timer", "steuerbar": True},
    {"name": "Schlüsselwacht", "art": "systemd", "unit": "clayverse-schluesselwacht.timer", "steuerbar": True},
    {"name": "Wache",          "art": "systemd", "unit": "clayverse-wache.timer", "steuerbar": True},
    {"name": "Wirte",          "art": "systemd", "unit": "clayverse-wirte.timer", "steuerbar": True},
    {"name": "Baunotizen",     "art": "systemd", "unit": "entityos-baunotizen.timer", "steuerbar": True},
    {"name": "Paketarbeiter",  "art": "systemd", "unit": "entityos-paketarbeiter.timer", "steuerbar": True},
    {"name": "Profile",        "art": "systemd", "unit": "entityos-profile.timer", "steuerbar": True},
    {"name": "Publish",        "art": "systemd", "unit": "eos-publish.service", "steuerbar": True},
    {"name": "Speicher",       "art": "systemd", "unit": "eos-speicher.timer", "steuerbar": True},
    {"name": "Tunnel",         "art": "systemd", "unit": "entityos-edge-tunnel.service", "steuerbar": True,
     "hinweis": "Reverse-SSH-Tunnel zur SeiMensch-VPS fuer den entityos.frank.ink-Edge. "
                "Stand 19.08. deaktiviert/inaktiv."},
]

# Der Immunsystem-Schalter ist bewusst KEIN Eintrag in DIENSTE (eigener Schalter,
# nicht Teil der Dienste-Liste -- Wunsch des Eigners). Trotzdem feste Whitelist-
# Angabe hier, an EINER Stelle, die dienststeuerung.py mit importiert.
IMMUNSYSTEM_UNIT = "eos-immune.service"


def _lauf(cmd, timeout=9):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return r.returncode, r.stdout.strip(), r.stderr.strip()
    except subprocess.TimeoutExpired:
        return 124, "", "timeout"
    except Exception as e:  # nie den Sammler abstuerzen lassen
        return 1, "", str(e)


def online_map():
    """{tailscale_ip: bool} aus `tailscale status --json`. Self ist immer online."""
    rc, out, _ = _lauf(["tailscale", "status", "--json"], timeout=8)
    m = {}
    if rc == 0 and out:
        try:
            d = json.loads(out)
            self_ = d.get("Self", {})
            for ip in self_.get("TailscaleIPs", []):
                m[ip] = bool(self_.get("Online", True))
            for p in (d.get("Peer") or {}).values():
                for ip in p.get("TailscaleIPs", []):
                    m[ip] = bool(p.get("Online", False))
        except Exception:
            pass
    return m


def parse_stats(zeile):
    """Die Stats-Zeile -> aufgeraeumtes Dict in GB/Prozent. None bei Murks."""
    t = zeile.split("|")
    if len(t) != 7:
        return None
    try:
        last1 = float(t[0].replace(",", ".")); kerne = int(t[1])   # komma-tolerant (de-Locale)
        mt = int(t[2]); ma = int(t[3])                       # kB
        dt = int(t[4]); du = int(t[5]); da = int(t[6])       # 1K-Bloecke
    except ValueError:
        return None
    gb = lambda kb: round(kb / (1024 * 1024), 1)
    mem_used = mt - ma
    return {
        "cpu":  {"kerne": kerne, "last1": round(last1, 2),
                 "pct": min(100, round(last1 / max(1, kerne) * 100))},
        "ram":  {"belegt": gb(mem_used), "gesamt": gb(mt), "einheit": "GB",
                 "pct": round(mem_used / max(1, mt) * 100)},
        "disk": {"belegt": gb(du), "frei": gb(da), "gesamt": gb(dt), "einheit": "GB",
                 "pct": round(du / max(1, dt) * 100)},
    }


def hol_stats(mask):
    if mask["hol"] == "lokal":
        rc, out, err = _lauf(["bash", "-lc", STATS_SH])
    else:
        rc, out, err = _lauf(
            ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=5",
             "-o", "StrictHostKeyChecking=accept-new", mask["ssh_ziel"], STATS_SH])
    if rc == 0 and out:
        s = parse_stats(out.splitlines()[-1])
        if s:
            return s, None
    grund = "SSH verweigert (kein Key)" if "Permission denied" in (err or "") \
            else (err or "nicht erreichbar")
    return None, grund


def dienst_an(d):
    """Reine Messung, kein Eingriff -- true/false ob der Dienst laeuft."""
    if d["art"] == "systemd":
        rc, out, _ = _lauf(["systemctl", "is-active", d["unit"]], timeout=6)
        return rc == 0 and out.strip() == "active"
    if d["art"] == "docker":
        rc, out, _ = _lauf(["docker", "inspect", "-f", "{{.State.Health.Status}}", d["unit"]], timeout=6)
        if rc == 0:
            out = out.strip()
            if out == "healthy":
                return True
            if out in ("", "<no value>"):
                # kein Healthcheck im Image definiert -- "laeuft" ist dann das beste Signal
                rc2, out2, _ = _lauf(["docker", "inspect", "-f", "{{.State.Running}}", d["unit"]], timeout=6)
                return rc2 == 0 and out2.strip() == "true"
            return False
        return False
    if d["art"] == "prozess":
        rc, out, _ = _lauf(["pgrep", "-cf", d["unit"]], timeout=6)
        try:
            return rc == 0 and int(out.strip() or "0") > 0
        except ValueError:
            return False
    return False


def hole_beschreibung(d):
    """Kurzbeschreibung: `systemctl show -p Description` wenn vorhanden (systemd),
    sonst der "hinweis"-Fallback im DIENSTE-Eintrag. Nie ein Fehler nach aussen."""
    if d["art"] == "systemd":
        try:
            rc, out, _ = _lauf(["systemctl", "show", "-p", "Description", "--value", d["unit"]], timeout=6)
            if rc == 0 and out.strip():
                return out.strip()
        except Exception:
            pass
    return d.get("hinweis") or "EntityOS-Dienst."


def sammle_dienste():
    """Nur messen und melden -- kein Neustart, kein Eingriff. Ein Fehler bei
    einem einzelnen Dienst darf die anderen nicht mitreissen."""
    ergebnis = []
    for d in DIENSTE:
        try:
            an = dienst_an(d)
        except Exception:
            an = False
        try:
            beschreibung = hole_beschreibung(d)
        except Exception:
            beschreibung = d.get("hinweis") or "EntityOS-Dienst."
        eintrag = {
            "name": d["name"], "unit": d["unit"], "an": bool(an),
            "steuerbar": bool(d.get("steuerbar", False)),
            "beschreibung": beschreibung,
        }
        if d.get("kritisch"):
            eintrag["kritisch"] = True
        ergebnis.append(eintrag)
    return ergebnis


def hole_immunsystem():
    """Status + letzte Journal-Zeilen von eos-immune.service. Die Unit legt ein
    ANDERER Bau gerade an -- existiert sie noch nicht, wird das sauber gemeldet
    (kein Crash, kein Erfinden von Log-Zeilen)."""
    rc0, out0, _ = _lauf(["systemctl", "list-unit-files", IMMUNSYSTEM_UNIT], timeout=5)
    vorhanden = rc0 == 0 and IMMUNSYSTEM_UNIT in out0
    if not vorhanden:
        return {"an": False, "vorhanden": False}, ["Immunsystem noch nicht aktiv"]
    an = dienst_an({"art": "systemd", "unit": IMMUNSYSTEM_UNIT})
    rc, out, _ = _lauf(["journalctl", "-u", "eos-immune", "-n", "15", "--no-pager", "-o", "cat"], timeout=8)
    zeilen = out.splitlines() if (rc == 0 and out) else []
    if not zeilen:
        zeilen = ["(noch keine Eintraege)"]
    return {"an": bool(an), "vorhanden": True}, zeilen


def main():
    om = online_map()
    systeme = []
    for mask in MASCHINEN:
        online = True if mask["hol"] == "lokal" else om.get(mask["ip"], False)
        eintrag = {"id": mask["id"], "name": mask["name"], "rolle": mask["rolle"],
                   "online": online, "erreichbar": False}
        if online:
            stats, grund = hol_stats(mask)
            if stats:
                eintrag.update(stats)
                eintrag["erreichbar"] = True
            else:
                eintrag["hinweis"] = grund
        else:
            eintrag["hinweis"] = "offline"
        systeme.append(eintrag)

    try:
        dienste = sammle_dienste()
    except Exception:
        dienste = []   # nie den Sammler abstuerzen lassen -- Maschinen-Stats stehen trotzdem

    try:
        immun_status, immun_log = hole_immunsystem()
    except Exception:
        immun_status, immun_log = {"an": False, "vorhanden": False}, ["Immunsystem: Status nicht messbar"]

    doc = {
        "stand": int(time.time()), "systeme": systeme, "dienste": dienste,
        "immunsystem": {**immun_status, "unit": IMMUNSYSTEM_UNIT, "steuerbar": True},
        "immune_log": immun_log,
    }
    os.makedirs(os.path.dirname(ZIEL), exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(ZIEL), suffix=".tmp")
    with os.fdopen(fd, "w") as f:
        json.dump(doc, f, ensure_ascii=False)
    os.replace(tmp, ZIEL)          # atomar -- der Leser sieht nie ein halbes File
    os.chmod(ZIEL, 0o644)
    print(json.dumps(doc, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
