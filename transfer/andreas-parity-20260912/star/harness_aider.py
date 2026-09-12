#!/usr/bin/env python3
"""harness_aider.py -- kontrollierter Aider-Aufruf gegen ein Free-Pool-Modell.

PHASE 46 (Gabriel-Auftrag 2026-08-27): Basis -- 'start', IMMER in einer
isolierten Sandbox (harness-werkraum/<paket_id>/), nie im echten Repo,
Aktivierungssperre (nur das gerade in star_konfig aktive Modell darf
laufen), Protokollierung jeder Datei-Aenderung ueber echten git-Verlauf
(zero_raum_ruf), Audit ueber harness_audit.py, Reconcile mit mechanisch
geprueftem Beleg.

PHASE 46b (Gabriel-Auftrag 2026-08-27, Nachtrag): 'fallback-start' -- fuer
den chatgpt-Skill, wenn die ChatGPT-Bruecke (Login) ausfaellt UND beide
automatischen Wiederherstellungsversuche (_chatgpt_login_sicherstellen())
gescheitert sind. Loest die zwei Einschraenkungen der Basis-Version fuer
GENAU diesen Anwendungsfall, mit STAERKERER statt schwaecherer Absicherung:

  1. Aktivierungssperre bleibt bestehen, wird aber PROGRAMMATISCH bedient:
     fallback-start schaltet das aktive Modell selbst um (_s.modell_aktiv_setzen,
     ueber mehrere Kandidaten in Reihenfolge, jeder Wechsel geht auditierbar
     in zero_raum_ruf) -- kein UI-Klick noetig, aber immer noch dieselbe
     Sperre (kein Harness laeuft ausserhalb des als aktiv markierten Modells).
  2. Ein neuer, EXPLIZITER 'forschung'-Modus (getrennt vom freien Sandbox-
     Testlauf-Modus, der unveraendert bleibt) darf tatsaechlich im echten
     Forschungsentitaets-Repo (~/clay-global-research-entity, FEST verdrahtet,
     kein beliebiger --repo-pfad) committen -- aber NUR:
       a) bei sauberem, mit origin/main synchronem Ausgangszustand (sonst
          Abbruch VOR jeder Aenderung);
       b) mit einer harten Datei-Allowlist (NUR
          research_entity/topic_packets/fallback-runs/<paket_id>/ -- jede
          Aenderung ausserhalb wird erkannt und die GESAMTE Sitzung per
          `git reset --hard` verworfen, bevor irgendetwas den sauberen
          Ausgangszustand fuer den naechsten Lauf verunreinigen kann);
       c) mit einer vom Harness SELBST (nicht von Aider) geschriebenen
          PROVENANCE.json (actor_id=freepool-fallback-secondary, siehe
          RESEARCH_ACTOR_REGISTRY.json), damit die Herkunft nicht davon
          abhaengt, ob das Modell die Anweisung befolgt;
       d) mit demselben harness_audit.py-Mechanismus wie im Sandbox-Modus --
          NUR bei exit_code 0 (git-Verlauf und zero_raum_ruf stimmen exakt
          ueberein) wird ueberhaupt `git push` versucht. Schlaegt Audit oder
          Allowlist fehl: kein Push, Lauf als gescheitert verbucht, lokale
          Commits verworfen (siehe b).
  Ergebnisse gehen IMMER in beide Richtungen: dauerhaft als Commit im
  Forschungsentitaets-Repo (b/c) UND als Klartext im JSON-Rueckgabewert
  dieses Skripts (Feld 'antwort', direkt aus der vereinbarten Antwortdatei
  zurueckgelesen) -- der aufrufende Agent (stern.py-Fallback) muss nicht im
  Repo suchen.
"""
import os
import sys
import subprocess
import argparse
import hashlib
import json
import sqlite3
import time
import fcntl
import errno
import contextlib
from pathlib import Path

# Import lokalen Stern-Modul
try:
    import stern as _s
except ImportError as e:
    print(f"Fehler: Lokalen Stern-Modul nicht gefunden: {e}", file=sys.stderr)
    sys.exit(1)

AIDER_BIN = os.path.expanduser("~/.claude/star/harness-venv/bin/aider")
# PHASE 49 (Gabriel-Auftrag 2026-09-12, Desktop-Knopf + /model-Wechsel +
# Auto-Wait/Resume): aider selbst wird NICHT mehr direkt als Binary
# aufgerufen, sondern ueber diesen duennen In-Prozess-Launcher (siehe dortiger
# Modul-Docstring) -- der setzt RETRY_TIMEOUT hoch, BEVOR aider.main.main()
# laeuft, damit Aiders eingebauter Rate-Limit-Retry-Loop laenger durchhaelt
# als die eingebauten 60s, OHNE einen eigenen pty-Wrapper um die interaktive
# stdio-Weiterleitung zu bauen (die wuerde die prompt_toolkit-REPL riskieren).
AIDER_VENV_PYTHON = os.path.expanduser("~/.claude/star/harness-venv/bin/python3")
AIDER_RETRY_LAUNCHER = os.path.expanduser("~/.claude/star/aider_retry_launcher.py")
WERKRAUM_BASIS = os.path.expanduser("~/.claude/star/harness-werkraum")
KEYS_DATEI = os.path.expanduser("~/.last-resort/keys.env")
# PHASE 48 (Gabriel-Auftrag 2026-08-27): 'berechtigung' je Modell -- Spiegel von
# modell_katalog.py MODELLE[*]['berechtigung_stufe'] (bewusst dupliziert, siehe
# dortiger Kommentar). 'voll' = normaler Aider-Editiermodus (darf Dateien im
# echten Repo aendern). 'eingeschraenkt' = Aider startet im '--edit-format ask'
# (strukturell KEINE Dateiaenderung moeglich, siehe aider/coders/ask_coder.py:
# 'Ask questions about code without making any changes.') -- durchgesetzt in
# visible_run(), nicht nur behauptet.
# ⭐⭐⭐ REIHENFOLGE GEAENDERT 2026-09-12, Gabriel: "nein, immer nur Groq."
# Die Auswahl in _waehle_modell() nimmt den ERSTEN Eintrag, der eine
# brauchbare Poolstufe hat UND "voll" ist -- also entschied bisher allein
# die Einfuegereihenfolge, und nvidia stand vorn.
#
# ZWEI GRUENDE FUER DEN WECHSEL, beide gemessen, nicht geraten:
#  1. Gabriel hat Groq ausdruecklich als einziges Modell bestimmt, und Groq
#     ist mit 0,75 s bis zum ersten Stueck auch das schnellste der vier.
#  2. nvidia/nemotron GIBT SEINE UEBERLEGUNG ALS TEXT AUS. Im Screenshot des
#     Crush-Fensters stand woertlich "We need to respond: user says they
#     have written something long ..." -- das Denken des Modells, sichtbar
#     im Gespraech. Aus demselben Grund ist es im Sprachmodus gesperrt
#     (glm_client.POOL_STUFEN); dort wuerde es vorgelesen.
#
# groq-gptoss bekommt dabei "voll" statt "eingeschraenkt". Das ist KEINE
# Ausweitung der Systemrechte: nvidia hatte "voll" bereits, es wechselt nur
# der Anbieter, der sie haelt.
MODELL_MAP = {
    "groq-gptoss":      {"aider_model": "groq/openai/gpt-oss-120b",
                         "env_var": "GROQ_API_KEY", "keys_env_quelle": "GROQ_API_KEY",
                         "berechtigung": "voll"},
    "nvidia-nemotron": {"aider_model": "nvidia_nim/nvidia/nemotron-3-super-120b-a12b",
                         "env_var": "NVIDIA_NIM_API_KEY", "keys_env_quelle": "NVIDIA_NIM_API_KEY",
                         "berechtigung": "voll"},
    "mistral-small":    {"aider_model": "mistral/mistral-small-latest",
                         "env_var": "MISTRAL_API_KEY", "keys_env_quelle": "MISTRAL2_API_KEY",
                         "berechtigung": "eingeschraenkt"},
    "openrouter-deepseek": {"aider_model": "openrouter/deepseek/deepseek-chat",
                         "env_var": "OPENROUTER_API_KEY", "keys_env_quelle": "OPENROUTER2_API_KEY",
                         "berechtigung": "voll"},
}

# PHASE 49 -- Namensraum-Bruecke zu pool_wache.py: dessen Tier-Labels (aus
# ~/last-resort/llm.py TIERS) sind NICHT dieselben Strings wie die
# MODELL_MAP-Schluessel hier (verschiedene Module, verschiedene Historie).
# Explizite Abbildung statt Raten/String-Heuristik.
_MODELL_ZU_POOL_TIER = {
    "nvidia-nemotron": "nvidia",
    "groq-gptoss": "groq",
    "mistral-small": "mistral",
    "openrouter-deepseek": "openrouter",
}

# PHASE 48 -- sichtbarer Terminal-Harness: laeuft im ECHTEN Repo (kein
# Sandbox-Werkraum-Versteck mehr, Gabriel-Auftrag), aber NIE in ~/.claude/star
# selbst (das ist der laufende Dashboard-/Hook-Dienst -- ein Aider-Lauf
# koennte den waehrend des eigenen Betriebs veraendern). Notizen fuer die
# 'eingeschraenkt'-Stufe landen unter NOTIZ_PRAEFIX innerhalb dieses Repos.
SICHTBAR_REPO = os.path.expanduser("~/frankenstein-repo")
SICHTBAR_NOTIZ_PRAEFIX = "notizen-freepool/"
SICHTBAR_HINWEIS_BASIS = os.path.expanduser("~/.claude/star/harness-hinweise")

# ── Forschungsmodus-Konstanten (PHASE 46b) ─────────────────────────────────
# FEST verdrahtet, bewusst KEIN CLI-Parameter dafuer -- eine beliebig
# waehlbare Zielpfad-Option waere genau die "aufgeweichte Sandbox-Sperre",
# die Gabriel ausdruecklich NICHT wollte.
FORSCHUNG_REPO = os.path.expanduser("~/clay-global-research-entity")
FORSCHUNG_ERLAUBTER_PRAEFIX = "research_entity/topic_packets/fallback-runs/"
FORSCHUNG_ACTOR_ID = "freepool-fallback-secondary"


def git_checkpoint_und_protokollieren(werkraum, paket_id, modell_id, seit=None):
    """
    Fuehrt Git-Checkpoint durch, protokolliert neue Commits und uncommitted
    changes in zero_raum_ruf. Gibt Dict mit {"anzahl_commits": N,
    "unquittiert": bool, "commit_hashes": [...]} zurueck.

    `seit` (Bugfix 2026-08-27, real gefunden beim ersten Forschungsmodus-
    Test): OHNE dieses Argument listet `git log` die GESAMTE Repo-Historie.
    Im Sandbox-Modus ist das harmlos (jeder Werkraum ist ein frisches,
    leeres Repo -- 'alle Commits' == 'Commits dieses Laufs'). Im
    Forschungsmodus ist der Werkraum das ECHTE Repo mit tausenden
    Alt-Commits -- ohne `seit` wurden beim ersten echten Testlauf 5930
    (!) Alt-Commits faelschlich als AKTION dieses einen Laufs in
    zero_raum_ruf protokolliert, bevor das Skript am Umfang schlicht zu
    lange brauchte. `seit` (der vor dem Lauf erfasste HEAD-Hash) grenzt
    korrekt auf `seit..HEAD` ein -- WENN gesetzt."""
    try:
        log_range = f"{seit}..HEAD" if seit else None
        cmd = ["git", "-C", werkraum, "log", "--format=%H", "--reverse"]
        if log_range:
            cmd.append(log_range)
        out = subprocess.check_output(cmd, stderr=subprocess.DEVNULL, text=True)
        commit_hashes = [line.strip() for line in out.splitlines() if line.strip()]
    except subprocess.CalledProcessError:
        commit_hashes = []

    conn = None
    try:
        conn = _s.verbindung()
        cursor = conn.cursor()
    except Exception as e:
        print(f"Warnung: DB-Verbindung fehlgeschlagen: {e}", file=sys.stderr)
        cursor = None

    for commit in commit_hashes:
        if cursor:
            cursor.execute(
                """SELECT 1 FROM zero_raum_ruf
                   WHERE text LIKE ? AND text LIKE ? LIMIT 1""",
                (f"%paket_id={paket_id}%", f"%commit={commit}%"),
            )
            if cursor.fetchone():
                continue  # Bereits protokolliert

        # Bugfix 2026-08-27 (real gefunden im Forschungsmodus-Testlauf):
        # `git show --stat` ist fuer Terminal-Darstellung gedacht und kuerzt
        # lange Pfade mit einem fuehrenden "..." ab (z.B.
        # "research_entity/topic_packets/..." wurde zu ".../topic_packets/...").
        # Das fuehrte zu falschen sha256-Berechnungen (git show <hash>:<pfad>
        # mit dem GEKUERZTEN Pfad schlaegt fehl) und zu falschen
        # Allowlist-Treffern. `--name-only` liefert den vollen, unveraenderten
        # Pfad, eine Datei pro Zeile, keine Kuerzung.
        try:
            dateien = [d for d in subprocess.check_output(
                ["git", "-C", werkraum, "show", "--name-only", "--format=", commit],
                stderr=subprocess.DEVNULL, text=True,
            ).splitlines() if d.strip()]
        except subprocess.CalledProcessError:
            dateien = []

        datei_sha_pairs = []
        for datei in dateien:
            try:
                inhalt = subprocess.check_output(
                    ["git", "-C", werkraum, "show", f"{commit}:{datei}"],
                    stderr=subprocess.DEVNULL,
                )
            except subprocess.CalledProcessError:
                inhalt = b""
            sha = hashlib.sha256(inhalt).hexdigest()
            datei_sha_pairs.append(f"{datei}:{sha}")

        dateien_str = ",".join(datei_sha_pairs) or "keine"
        _s._raum_ruf_schreiben(
            f"harness:aider:{modell_id}", "AKTION",
            f"paket_id={paket_id} commit={commit} dateien=[{dateien_str}]",
        )

    unquittiert = False
    try:
        porcelain = subprocess.check_output(
            ["git", "-C", werkraum, "status", "--porcelain"],
            stderr=subprocess.DEVNULL, text=True,
        ).strip()
        if porcelain:
            unquittiert = True
            _s._raum_ruf_schreiben(
                f"harness:aider:{modell_id}", "UNCOMMITTED",
                f"paket_id={paket_id} ACHTUNG unquittierte Aenderungen: {porcelain}",
            )
    except subprocess.CalledProcessError:
        pass
    finally:
        if conn:
            conn.close()

    return {"anzahl_commits": len(commit_hashes), "unquittiert": unquittiert,
            "commit_hashes": commit_hashes}


def _aider_kommando_praefix():
    """Startbefehl-Praefix fuer jeden aider-Aufruf -- ueber den Retry-Launcher
    (siehe AIDER_RETRY_LAUNCHER-Kommentar oben) statt direkt ueber AIDER_BIN,
    damit Punkt 4 (Auto-Wait/Resume bei Rate-Limit) in JEDEM Aufrufpfad
    (sichtbarer Terminal-Harness UND der aeltere headless Forschungs-/
    Fallback-Pfad) greift, nicht nur in einem."""
    return [AIDER_VENV_PYTHON, AIDER_RETRY_LAUNCHER]


def _alle_api_keys_laden():
    """PHASE 49 (Punkt 2, /model-Wechsel): laedt die Schluessel FUER ALLE
    MODELL_MAP-Eintraege in os.environ, nicht nur fuer das Startmodell.
    Ohne das wuerde ein '/model <anderer-provider>'-Wechsel MITTEN in der
    Aider-Sitzung an einer fehlenden Env-Var scheitern -- Aider selbst
    wechselt das Modellobjekt anstandslos per SwitchCoder (siehe
    aider/commands.py cmd_model), aber der API-Key fuer den NEUEN Provider
    war bisher nie gesetzt, weil visible_run() nur den Key des
    Start-Modells lud. Gibt {modell_id: bool(key_gesetzt)} zurueck (fuer
    Diagnose/Log, NIE den Schluesselwert selbst)."""
    ergebnis = {}
    for mid, minfo in MODELL_MAP.items():
        wert = _api_key_laden(mid)
        if wert:
            os.environ[minfo["env_var"]] = wert
        ergebnis[mid] = bool(wert)
    return ergebnis


def _relative_zeit_de(ts):
    """'vor 3 Min'/'vor 2 Std'/'vor 5 Tagen' aus einem Unix-Timestamp, oder
    'nie' falls None -- fuer die Kontingent-Anzeige (Punkt 3), keine rohen
    Epoch-Zahlen im Terminal."""
    if not ts:
        return "nie"
    delta_s = max(0, time.time() - ts)
    if delta_s < 60:
        return "gerade eben"
    if delta_s < 3600:
        return f"vor {int(delta_s // 60)} Min"
    if delta_s < 86400:
        return f"vor {int(delta_s // 3600)} Std"
    return f"vor {int(delta_s // 86400)} Tagen"


def _kontingent_banner():
    """PHASE 50 (Gabriel-Auftrag 2026-09-12, 'sieht aus wie Claude Code, nicht
    wie ein bunter Absatz-Block'): dieselben echten Werte wie vorher (PHASE
    49 Punkt 3, pool_wache.py-Cooldown-Heuristik, KEIN erfundenes Tages-
    Kontingent), aber als EIN Statuszeilen-Segment statt ein mehrzeiliger
    Kasten -- gleicher ' · '-Trenner-Stil wie _terminal_banner()/die echte
    Claude-Code-Statuszeile (~/.claude/star/statusline-frankenstein.sh).
    Fail-soft: pool_wache nicht lesbar -> ein einzelnes rotes Hinweis-
    Segment statt Absturz."""
    sep = f"{_ANSI_GRAU} · {_ANSI_RESET}"
    segs = []
    try:
        import pool_wache as _pw
        status = _pw.status()
        for modell_id, tier in _MODELL_ZU_POOL_TIER.items():
            st = status.get(tier, {})
            if not st.get("bekannt"):
                kurz, farbe = "?", _ANSI_GRAU
            elif st.get("in_cooldown"):
                rest = int(st.get("cooldown_rest_s") or 0)
                kurz, farbe = f"cooldown({rest}s)", _ANSI_ROT
            else:
                kurz, farbe = "frei", _ANSI_GRUEN
            segs.append(f"{_ANSI_HELLGRAU}{modell_id}:{farbe}{kurz}{_ANSI_RESET}")
        if status.get("_all_exhausted"):
            segs.append(f"{_ANSI_ROT}ALLE-COOLDOWN{_ANSI_RESET}")
    except Exception as e:
        segs.append(f"{_ANSI_ROT}pool-status nicht lesbar: {e}{_ANSI_RESET}")
    if not segs:
        return ""
    return f"{_ANSI_AMBER}pool{_ANSI_RESET}{sep}" + sep.join(segs)


def _api_key_laden(modell_id):
    """Liest den echten Schluessel aus KEYS_DATEI, oder None wenn keiner da
    ist. NIE geloggt/geprintet -- nur der interne Wert."""
    if modell_id not in MODELL_MAP:
        return None
    keys_env_quelle = MODELL_MAP[modell_id]["keys_env_quelle"]
    try:
        with open(KEYS_DATEI, "r") as f:
            for zeile in f:
                zeile = zeile.strip()
                if not zeile or zeile.startswith("#") or "=" not in zeile:
                    continue
                key, value = zeile.split("=", 1)
                if key == keys_env_quelle and value.strip():
                    return value.strip()
    except FileNotFoundError:
        return None
    return None


def _git(werkraum, *args, check=True, timeout=30):
    return subprocess.run(["git", "-C", werkraum, *args], capture_output=True,
                           text=True, timeout=timeout, check=check)


def _forschung_preflight(repo):
    """Sauberer Ausgangszustand, AUF DEM STAND von origin/main -- Vorbedingung
    fuer JEDE Aenderung im echten Forschungsentitaets-Repo. Gibt
    {'ok':bool,'grund':str,'head':<hash oder None>} zurueck.

    Bugfix 2026-08-27 (real gefunden im ersten Fallback-Integrationstest):
    das Repo hat einen staendig aktiven, unabhaengigen Zweit-Schreiber
    (clay-local-bridge/andere Sitzungen pushen alle paar Minuten) -- ein
    stures 'lokal MUSS bereits exakt auf origin/main sein, sonst Abbruch'
    haette den Fallback praktisch NIE laufen lassen (lokal war beim Test
    5 Commits zurueck, rein durch Zeitablauf seit dem letzten Klon/Pull,
    OHNE dass hier irgendetwas Unsauberes vorlag). Der ECHTE Sicherheits-
    bedarf ist nur: (a) das Arbeitsverzeichnis selbst ist sauber (keine
    eigenen unklaren Altlasten), (b) unser lokaler Stand ist ein echter
    Vorfahre von origin/main (keine divergierten, moeglicherweise verlorenen
    lokalen Commits) -- NICHT dass er exakt gleichauf ist. Deshalb: `git
    fetch` + `git merge --ff-only origin/main` (reines Vorspulen, erzeugt
    NIE einen Merge-Commit, aendert NIE Historie) -- schlaegt das fehl
    (echte Divergenz), erst DANN abbrechen."""
    if not os.path.isdir(os.path.join(repo, ".git")):
        return {"ok": False, "grund": f"kein git-Repo unter {repo}", "head": None}
    try:
        status = _git(repo, "status", "--porcelain", check=False)
        if status.stdout.strip():
            return {"ok": False, "grund": "Arbeitsverzeichnis nicht sauber -- "
                    "unklarer Vorzustand, Abbruch VOR jeder Aenderung", "head": None}
        fetch = _git(repo, "fetch", "origin", "main", check=False, timeout=60)
        if fetch.returncode != 0:
            return {"ok": False, "grund": f"git fetch origin fehlgeschlagen: {fetch.stderr[:300]}", "head": None}
        ff = _git(repo, "merge", "--ff-only", "origin/main", check=False, timeout=30)
        if ff.returncode != 0:
            return {"ok": False, "grund": f"lokaler Stand ist von origin/main divergiert (fast-forward "
                    f"nicht moeglich) -- erst manuell klaeren, NIE automatisch ueberschreiben: "
                    f"{ff.stderr[:300]}", "head": None}
        head = _git(repo, "rev-parse", "HEAD", check=False).stdout.strip()
        origin_head = _git(repo, "rev-parse", "origin/main", check=False).stdout.strip()
        if not head or not origin_head:
            return {"ok": False, "grund": "HEAD/origin-main nicht ermittelbar", "head": None}
        if head != origin_head:
            return {"ok": False, "grund": f"lokal ({head[:10]}) nicht auf origin/main "
                    f"({origin_head[:10]}) trotz fast-forward -- unerwarteter Zustand", "head": None}
        return {"ok": True, "grund": "sauber und aktuell", "head": head}
    except Exception as e:
        return {"ok": False, "grund": f"Preflight-Ausnahme: {e}", "head": None}


_FORSCHUNG_LOCK_DATEI = Path.home() / ".claude" / "star" / "daten" / ".forschung_repo.lock"


class ForschungLockTimeout(Exception):
    """Ein zweiter/dritter gleichzeitiger fallback-start-Aufrufer wartete
    laenger als das Timeout auf das gemeinsam genutzte FORSCHUNG_REPO-
    Arbeitsverzeichnis -- sauberer Abbruch statt endlosem Haengen."""


@contextlib.contextmanager
def _forschung_lock(timeout_s: float = 900.0, poll_s: float = 1.0):
    """Echter Dateilock (`flock`, blockierend mit Poll-Timeout) um jeden
    Forschungsmodus-Lauf gegen das GEMEINSAM GENUTZTE Arbeitsverzeichnis
    FORSCHUNG_REPO.

    Root-Cause-Fund 2026-08-27 (Gabriel-Auftrag: Fallback-Harness real
    end-to-end getestet statt nur Code gelesen): wiederholte
    'Arbeitsverzeichnis nicht sauber'-Preflight-Fehlschlaege waren KEIN
    kaputter API-Key/Endpunkt (der Free-Pool selbst funktioniert, direkt
    per ~/last-resort/llm.py verifiziert) -- sondern schlicht fehlende
    Synchronisation: mehrere parallele Agenten riefen 'fallback-start'
    GLEICHZEITIG gegen DASSELBE lokale FORSCHUNG_REPO-Arbeitsverzeichnis
    auf (per `ps aux` real bestaetigt, mind. 2 gleichzeitige Prozesse).
    Waehrend Prozess B mitten in seinem aider-Lauf/Commit war, sah Prozess
    A's `_forschung_preflight()` das Verzeichnis faelschlich als
    'nicht sauber' und brach ab -- reine Racebedingung, keine echte
    Verschmutzung. Analog zu `_chatgpt_lock()` in stern.py: ein zweiter
    gleichzeitiger Aufrufer WARTET jetzt (bis zu `timeout_s`) statt zu
    kollidieren."""
    _FORSCHUNG_LOCK_DATEI.parent.mkdir(parents=True, exist_ok=True)
    f = open(_FORSCHUNG_LOCK_DATEI, "a+")
    start = time.time()
    acquired = False
    try:
        while True:
            try:
                fcntl.flock(f.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                acquired = True
                break
            except OSError as e:
                if e.errno not in (errno.EAGAIN, errno.EACCES):
                    raise
                if time.time() - start > timeout_s:
                    raise ForschungLockTimeout(
                        f"forschung-repo-Kanal seit {timeout_s:.0f}s belegt (anderer "
                        f"fallback-start-Aufrufer laeuft noch) -- abgebrochen statt "
                        f"endlos zu warten. Lock-Datei: {_FORSCHUNG_LOCK_DATEI}")
                time.sleep(poll_s)
        try:
            f.seek(0)
            f.truncate()
            f.write(f"pid={os.getpid()} seit={time.strftime('%Y-%m-%dT%H:%M:%S')}\n")
            f.flush()
        except Exception:
            pass
        yield
    finally:
        if acquired:
            try:
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)
            except Exception:
                pass
        f.close()


def _forschung_allowlist_pruefen(werkraum, commit_hashes):
    """Prueft, dass JEDE in diesem Lauf geaenderte Datei unter
    FORSCHUNG_ERLAUBTER_PRAEFIX liegt. Liest frisch aus git (nicht aus
    zero_raum_ruf-Cache) -- unabhaengige Pruefung wie harness_audit.py."""
    verstoesse = []
    for commit in commit_hashes:
        try:
            # --name-only statt --stat: siehe Bugfix-Kommentar in
            # git_checkpoint_und_protokollieren() -- --stat kuerzt lange Pfade.
            dateien = [d for d in subprocess.check_output(
                ["git", "-C", werkraum, "show", "--name-only", "--format=", commit],
                stderr=subprocess.DEVNULL, text=True,
            ).splitlines() if d.strip()]
        except subprocess.CalledProcessError:
            continue
        for datei in dateien:
            if datei and not datei.startswith(FORSCHUNG_ERLAUBTER_PRAEFIX):
                verstoesse.append({"commit": commit, "datei": datei})
    return {"ok": len(verstoesse) == 0, "verstoesse": verstoesse}


def _forschung_provenance_schreiben(werkraum, paket_id, modell_id, auftrag,
                                     fallback_grund, session_id):
    """Schreibt PROVENANCE.json SELBST (git direkt, NICHT ueber Aider) --
    die Herkunftsangabe haengt damit nicht davon ab, ob das Modell die
    Anweisung befolgt hat. Eigener Commit, erkennbar an der harness-eigenen
    git-Identitaet (siehe _werkraum_git_identitaet)."""
    zielordner = os.path.join(werkraum, FORSCHUNG_ERLAUBTER_PRAEFIX, paket_id)
    os.makedirs(zielordner, exist_ok=True)
    provenance = {
        "origin_actor": FORSCHUNG_ACTOR_ID,
        "actor_role": "FALLBACK_SYNTHESIS_RESEARCH_ORGAN",
        "provider": "NVIDIA NIM / Mistral AI (free-tier pool)",
        "runtime_model": modell_id,
        "paket_id": paket_id,
        "session_id": session_id,
        "fallback_reason": fallback_grund or "chatgpt-secondary Browser-Bruecke nicht erreichbar (Login, auch nach automatischem Cookie-Wiederherstellungsversuch)",
        "auftrag": auftrag,
        "task_classification": "L0_NO_RESEARCH_DELTA_oder_L1_ENGINEERING_DELTA (automatische Einstufung nicht vorgenommen -- menschliche/claude-code-lead-Pruefung empfohlen, decision_weight=0.5 siehe RESEARCH_ACTOR_REGISTRY.json)",
        "erzeugt_am": _s._jetzt_iso(),
        "geprueft_durch": "harness_audit.py (git-Verlauf <-> zero_raum_ruf, exakter Abgleich)",
    }
    pfad = os.path.join(zielordner, "PROVENANCE.json")
    with open(pfad, "w", encoding="utf-8") as f:
        json.dump(provenance, f, ensure_ascii=False, indent=2)
    rel = os.path.join(FORSCHUNG_ERLAUBTER_PRAEFIX, paket_id, "PROVENANCE.json")
    _git(werkraum, "add", rel)
    commit = _git(werkraum, "commit", "-m",
                   f"harness(freepool-fallback): provenance fuer {paket_id} ({modell_id})",
                   check=False)
    return commit.returncode == 0


def _werkraum_git_identitaet(werkraum, modell_id):
    _git(werkraum, "config", "user.email", "harness@lokal.invalid", check=False)
    _git(werkraum, "config", "user.name", f"harness-{modell_id}", check=False)


_AIDER_BUCHFUEHRUNG_BASIS = os.path.join(WERKRAUM_BASIS, "_aider-buchfuehrung")
_AIDER_EIGENE_DATEIEN = (".aider.chat.history.md", ".aider.input.history",
                          ".aider.llm.history", ".aider.tags.cache.v4")


def _aider_werkraum_aufraeumen(werkraum):
    """Entfernt Aiders eigene Buchfuehrungsdateien AUS DEM WERKRAUM SELBST
    (Bugfix 2026-08-27, real gefunden: der zweite Fallback-Testlauf schlug
    fehl, weil der ERSTE Testlauf .aider.chat.history.md/.aider.input.history
    unversioniert im echten Repo liegen liess -- die naechste
    _forschung_preflight()-Pruefung sah dadurch ein 'nicht sauberes'
    Arbeitsverzeichnis und brach ab, OBWOHL inhaltlich nichts Unklares
    vorlag). _aider_ausfuehren() leitet die meisten dieser Dateien zwar
    schon per Flag aus dem Werkraum heraus (siehe dort), dieser Aufraeum-
    schritt ist die zweite, unabhaengige Absicherung fuer alles, was Aider
    trotzdem noch direkt im Werkraum ablegt (z.B. das Tags-Cache-
    Verzeichnis, fuer das es keinen Umleitungs-Parameter gibt)."""
    for name in _AIDER_EIGENE_DATEIEN:
        pfad = os.path.join(werkraum, name)
        try:
            if os.path.isdir(pfad):
                import shutil
                shutil.rmtree(pfad, ignore_errors=True)
            elif os.path.exists(pfad):
                os.remove(pfad)
        except Exception as e:
            print(f"Warnung: Aufraeumen von {pfad} fehlgeschlagen: {e}", file=sys.stderr)


_WISSENSPAKET_PFAD = os.path.expanduser(
    "~/.claude/star/daten/FREE_POOL_WISSENSPAKET.md")


def _wissenspaket_block() -> str:
    """PHASE 53 (Gabriel-Auftrag 2026-09-12, woertlich): 'es muss fuer den
    free shit alles ganz genau vorgekaut sein: wo sind die server/vps, was
    ist dort, welche domains, was ist frankenstein, wo sind die repos, wo
    ist der tresor mit den credentials und und und.' Free-Pool-Modelle
    verlieren sonst Minuten mit `Glob **/*seimensch*` u.ae. fuer laengst
    bekannte Fakten (real beobachtet: 'No files found' -> 'Service
    temporarily overloaded', reine Zeitverschwendung).

    Statischer Nachschlage-Block, NICHT vom 3500-Zeichen-Deckel von
    `_grid_zustand_block()` betroffen (der ist fuer den DYNAMISCHEN Zustand
    gedacht, dieser hier ist konstant und wuerde sonst Ziele/Pakete
    verdraengen) -- eigener, grosszuegigerer Deckel als Sicherheitsnetz.
    Fail-soft wie jeder andere Block hier: Datei fehlt/nicht lesbar -> leerer
    String, nie eine Ausnahme nach aussen."""
    try:
        with open(_WISSENSPAKET_PFAD, "r", encoding="utf-8") as f:
            text = f.read()
        return text[:4500]
    except Exception:
        return ""


def _grid_zustand_block(session_id=None, auftrag=None):
    """PHASE 51 (Gabriel-Auftrag 2026-09-12, woertlich: 'ich will das er...
    den echten frankenstein zugaenglich macht mit allem und state und alles
    ... er soll dann selbst pruefen ob die ergebnisse passen ... gesteuert
    wie immer vom grid'): EIN Textblock aus vier echten, GERADE ABGEFRAGTEN
    Quellen -- kein Cache, kein erfundener Platzhalter, kein statischer
    Banner-Text (das war genau Gabriels Beanstandung nach dem zweiten Live-
    Screenshot: das Modell riet ueber generische Dateinamen ("welche Datei
    koennte greeting enthalten"), WEIL ihm jeder echte Zugriff auf den
    FranKenstein-Zustand fehlte):

      1. ziele.py offene() (consciousness.db) -- die ECHTEN, gerade
         verfolgten Ziele, ueber ziel_bruecke.py (bereits existierende,
         kanonische Bruecke, hier NICHT neu erfunden -- siehe dortiger
         Modul-Docstring, paket-1789133830613-17102f).
      2. entityos_arbeitspaket (unified.db) -- offene/laufende Pakete
         ANDERER Sitzungen, fuer Kollisions-/Kontinuitaetsbewusstsein
         (dieselbe Tabelle, die handoff()/reconcile() fuehren).
      3. immunsystem_status.json (vom laufenden Immunsystem-Dienst SELBST
         geschrieben, siehe cortex_dashboard_immunsystem.py) + pool_wache.
         status() (dieselbe Quelle wie _kontingent_banner() oben) --
         Dienst-Ampeln + Free-Pool-Kontingent.
      4. stern.py's _f2wp1207_turn_loop_delegieren() -- DIESELBE hyperGRID-
         Injektionszeile, die die Claude-Code-Terminalsitzung bei jedem Zug
         via UserPromptSubmit-Hook bekommt (siehe stern.py cmd_hook()).
         Enthaelt darin BEREITS die GRID-Koordinationspakete aus
         grid_packet_bridge.py (_paket_zeile) und die Anweisung/Zusicherung
         aus regie.py (_regie_zeile) -- EIN Aufruf deckt Auftragspunkt 1
         UND Auftragspunkt 4 gleichzeitig ab, kein zweiter, parallel
         erfundener Kanal fuer denselben Zweck. Real gemessen (hook.log):
         ~0,7-2,4s, oft mit Zeitueberschreitung (>1,2s) unter Last -- dieselbe
         Flakiness, die Claude Code's eigener Hook ohnehin hat, hier NICHT
         verschwiegen, sondern einfach fail-soft uebersprungen.

    Gibt (text, hat_hypergrid_zeile) zurueck -- Letzteres steuert in
    _persona_hinweis_schreiben(), ob die AELTERE Zusicherungs-Absicherung
    zusaetzlich noch gebraucht wird (die hyperGRID-Zeile enthaelt dieselbe
    Zusicherung bereits ueber ihre eigene _regie_zeile) oder verdoppeln wuerde.

    Jede der vier Quellen ist EINZELN fail-soft (§1.9.4-Konvention dieser
    Codebasis) -- faellt eine aus, bleiben die anderen drei stehen, NIE eine
    Ausnahme nach aussen. Hart gekappt auf 3500 Zeichen (Groq Free-Tier
    8000 Token/Min real gemessen, siehe PHASE-48-Kommentar oben) -- das
    kommt ZUSAETZLICH zum Persona-Auszug + Kapsel.

    Reihenfolge bewusst NACH WICHTIGKEIT, nicht nach Abfrage-Reihenfolge:
    real getestet (siehe Beleg-Transkript) fuellte die urspruengliche
    Reihenfolge (Ziele zuerst, hyperGRID zuletzt) den 3500-Zeichen-Deckel
    schon mit Zielen/Paketen, sodass die hyperGRID-Zeile -- und darin die
    Zusicherung -- mitten im Satz abgeschnitten wurde. Die wichtigsten,
    kuerzesten Bloecke (hyperGRID inkl. Zusicherung, Immunsystem, Pool-
    Kontingent) stehen deshalb ZUERST; die laengsten/am wenigsten
    kritischen (offene Arbeitspakete anderer Sitzungen) zuletzt -- ein
    Abschneiden trifft dann bevorzugt sie, nicht die Zusicherung."""
    hat_hypergrid = False
    grid_teil = None
    try:
        grid_text = _s._f2wp1207_turn_loop_delegieren(
            session_id or _s._uid("harness-grid"),
            (auftrag or "Free-Pool-Harness-Sitzung, Kontext-Abruf")[:400],
            None,
        )
        if grid_text:
            grid_teil = grid_text
            hat_hypergrid = True
    except Exception:
        pass

    immun_teil = None
    try:
        status_datei = os.path.expanduser("~/.claude/star/immunsystem_status.json")
        with open(status_datei, "r", encoding="utf-8") as f:
            im = json.load(f)
        dienste = im.get("dienste") or {}
        rot = [n for n, farbe in dienste.items() if farbe == "rot"]
        orange = [n for n, farbe in dienste.items() if farbe == "orange"]
        gruen_n = sum(1 for farbe in dienste.values() if farbe == "gruen")
        alter_s = max(0.0, time.time() - float(im.get("ts") or 0))
        zeile = f"{gruen_n}/{len(dienste)} Dienste gruen"
        if rot:
            zeile += f", ROT: {', '.join(rot)}"
        if orange:
            zeile += f", orange/faehrt-hoch: {', '.join(orange)}"
        immun_teil = f"Immunsystem-Status (Stand vor {alter_s:.0f}s, aus immunsystem_status.json): {zeile}"
    except Exception:
        pass

    pool_teil = None
    try:
        import pool_wache as _pw
        pw_zeilen = []
        for tier, st in _pw.status().items():
            if st.get("in_cooldown"):
                pw_zeilen.append(f"{tier}:cooldown({int(st.get('cooldown_rest_s') or 0)}s)")
            elif st.get("bekannt"):
                pw_zeilen.append(f"{tier}:frei")
        if pw_zeilen:
            pool_teil = "Free-Pool-Kontingent gerade (pool_wache.py): " + ", ".join(pw_zeilen)
    except Exception:
        pass

    ziele_teil = None
    try:
        import ziel_bruecke as _zb
        z = _zb.ziele_modul()
        if z is not None:
            offene = z.offene(grenze=5)
            if offene:
                zeilen = [
                    f"  - [{zid}] {str(besch).strip()[:140]} (Prioritaet {float(prio):.2f})"
                    for zid, besch, prio, *_rest in offene
                ]
                ziele_teil = (
                    "Echte, gerade verfolgte Ziele (ziele.py/consciousness.db, "
                    "NICHT erfunden, NICHT von diesem Harness formuliert):\n"
                    + "\n".join(zeilen)
                )
    except Exception:
        pass

    pakete_teil = None
    try:
        with contextlib.closing(_s.verbindung()) as c:
            rows = c.execute(
                "SELECT paket_id, auftrag, womit, stand FROM entityos_arbeitspaket "
                "WHERE stand IN ('offen','laeuft') ORDER BY geaendert DESC LIMIT 6"
            ).fetchall()
        if rows:
            zeilen = [
                f"  - {pid} [{stand}] {(auf or '')[:90]} (womit={womit})"
                for pid, auf, womit, stand in rows
            ]
            pakete_teil = (
                "Andere gerade offene/laufende Arbeitspakete (unified.db, echt "
                "gerade abgefragt -- Kollisionsvermeidung):\n" + "\n".join(zeilen)
            )
    except Exception:
        pass

    teile = [t for t in (grid_teil, immun_teil, pool_teil, ziele_teil, pakete_teil) if t]
    if not teile:
        return (
            "(Echter Zustandsabruf ist gerade fehlgeschlagen oder liefert nichts -- "
            "das ist ein ehrlicher Leerstand, kein erfundener Ersatztext und keine "
            "Aussage ueber deine Eignung.)",
            False,
        )
    return "\n\n".join(teile)[:3500], hat_hypergrid


def _hinweis_ordner_aufraeumen(aktueller_paket_id=None):
    """PHASE 52 (Gabriel-Auftrag 2026-09-12, wortwoertlich nach Screenshot-
    Beleg: alte, laengst erledigte Paket-Hinweise duerfen NIE in eine neue
    Sitzung durchsickern -- genau DAS war beim nvidia-nemotron-Live-Test
    passiert, ein uralter show_greeting.py-Testauftrag aus
    paket-1789163559288-39f0c6/paket-1789168285368-4b2301 kam als
    Kontinuitaets-Kontext in eine voellig unabhaengige neue Sitzung).
    _persona_hinweis_schreiben() legt bei jedem Sitzungsstart einen NEUEN
    Ordner harness-hinweise/paket-<id>/ an und hat nie einen davon geloescht
    -- reines Anwachsen. Diese Funktion loescht bei JEDEM Aufruf jeden
    vorhandenen Ordner, dessen paket_id in entityos_arbeitspaket NICHT mehr
    'laeuft'/'offen' ist (oder gar nicht mehr existiert) UND der nicht der
    gerade aktive ist -- fail-soft: DB nicht lesbar oder Ordner nicht
    loeschbar -> einfach ueberspringen, nie die Sitzung deswegen abbrechen."""
    if not os.path.isdir(SICHTBAR_HINWEIS_BASIS):
        return 0
    try:
        with contextlib.closing(_s.verbindung()) as c:
            offene = {r[0] for r in c.execute(
                "SELECT paket_id FROM entityos_arbeitspaket WHERE stand IN ('offen','laeuft')")}
    except Exception:
        offene = None  # DB nicht lesbar -- lieber NICHTS loeschen als versehentlich Aktives treffen
    if offene is None:
        return 0
    geloescht = 0
    for eintrag in os.listdir(SICHTBAR_HINWEIS_BASIS):
        if not eintrag.startswith("paket-"):
            continue
        if eintrag == aktueller_paket_id:
            continue
        if eintrag in offene:
            continue
        voll = os.path.join(SICHTBAR_HINWEIS_BASIS, eintrag)
        try:
            import shutil
            shutil.rmtree(voll)
            geloescht += 1
        except Exception:
            pass
    return geloescht


def _persona_hinweis_schreiben(paket_id, modell_id, berechtigung, kapsel="",
                                session_id=None, auftrag=None, ziel_pfad=None):
    """Schreibt eine READ-ONLY-Datei (via Aider '--read', kann vom Modell nie
    editiert werden) mit einem kurzen Persona-Auszug + explizitem Hinweis,
    dass dies NICHT Claude ist -- Vorlage: ~/.claude/star/daten/persona.md
    (Identitaet/Performance-Klausel), nicht neu erfunden, nur gekuerzt (die
    kleinen Free-Pool-Modelle haben knappe Kontextfenster, siehe
    modell_katalog.py 'kontextfenster').

    PHASE 48 Nachtrag (Gabriel-Feedback 2026-08-27, nach Live-Screenshot):
    die stern.handoff()-Kontinuitaets-Kapsel (offene Pakete, Vorwissen, Beleg-
    Pflicht-Text) ist interne Koordinator-Buchhaltung -- fuer einen
    Menschen im sichtbaren Terminal verwirrend/irrelevant, gehoert NICHT roh
    ins Terminal gedruckt (siehe visible_run()). Sie bleibt aber technisch
    Kontext fuer das MODELL -- deshalb wandert sie hier rein, in die
    Read-Only-Datei, statt auf stdout.

    PHASE 51 (Gabriel-Auftrag 2026-09-12, nach einem zweiten Live-Screenshot,
    in dem das Modell ueber generische Dateinamen raten musste, WEIL ihm
    aller echte Zustand fehlte -- woertlich: "er soll selbst wissen und
    sagen ja das modell kann ich fuer das verwenden oder ... lass es uns
    versuchen ... er soll dann selbst pruefen ob die ergebnisse passen"):
    drei Erweiterungen, ADDITIV zur PHASE-48-Fassung, nichts davon ersetzt:
      (a) `_grid_zustand_block()` -- echter, FRISCHER Datenabruf (Ziele,
          offene Pakete, Immunsystem, hyperGRID-Injektion inkl. GRID-
          Koordinationspaketen), statt nur eines Identitaets-Banners.
      (b) explizite Aufforderung zur Eignungs-Selbsteinschaetzung VOR der
          eigentlichen Arbeit ("das kann ich gut" ODER "ich bin hier
          wahrscheinlich schlechter, aber lass es uns versuchen").
      (c) explizite Aufforderung zur ehrlichen Selbstpruefung NACH der
          Arbeit (Plausibilitaet, Unsicherheit klar benennen statt
          Zuversicht vorzutaeuschen).
    `session_id`/`auftrag` (optional) fliessen NUR in (a) (die hyperGRID-
    Turn-Anfrage) ein -- fehlen sie (z.B. beim initialen Sitzungsstart,
    bevor ueberhaupt eine Nachricht gewechselt wurde), traegt der Turn
    trotzdem, nur mit generischem Platzhaltertext statt der echten laufenden
    Aufgabe.
    `ziel_pfad` (optional): schreibt an EXAKT diesen Pfad statt einen neuen
    zu berechnen -- das macht die Funktion wiederholt aufrufbar auf
    DERSELBEN Datei, die Aider bereits per '--read' geladen hat (siehe
    aider_retry_launcher.py's Modellwechsel-Hook: Aider liest Read-Only-
    Dateiinhalte bei JEDER Nachricht frisch von der Platte,
    aider/coders/base_coder.py get_read_only_files_content() -- real
    geprueft, kein Cache -- ein Ueberschreiben derselben Datei reicht, kein
    erneutes '/read' im laufenden Chat noetig)."""
    try:
        _hinweis_ordner_aufraeumen(aktueller_paket_id=paket_id)
    except Exception:
        pass
    persona_pfad = os.path.expanduser("~/.claude/star/daten/persona.md")
    try:
        with open(persona_pfad, "r", encoding="utf-8") as f:
            persona_text = f.read()
    except Exception:
        persona_text = "(persona.md nicht lesbar)"
    # PHASE 48 Nachtrag (Bugfix nach Live-Testlauf 2026-08-27): 4000+Kapsel
    # sprengte zusammen mit Aiders Repo-Map Groqs Free-Tier-TPM-Limit (8000
    # Token/Minute) -- realer RateLimitError beim ersten Testlauf. Gekuerzt +
    # --map-tokens unten reduziert (siehe aider_cmd).
    auszug = persona_text[:1500]
    if berechtigung == "voll":
        stufe_text = ("Du hast Editierrechte in diesem Repo. AUSNAHME, technisch "
                       "gesperrt (kein Bitte, ein echter Riegel): kein Loeschen von "
                       "Dateien, keine Shell-Befehle -- '--no-suggest-shell-commands' "
                       "ist gesetzt, jede versuchte Loeschung wird nach dem Lauf "
                       "erkannt und automatisch verworfen (git reset --hard).")
    else:
        stufe_text = ("Du laeufst im ask-only-Modus: du KANNST technisch nichts im "
                       "Dateisystem aendern (Aider-Edit-Format 'ask' wendet nie "
                       "Aenderungen an). Beantworte Fragen/recherchiere frei -- der "
                       "Harness selbst (nicht du) legt deine Antwort danach als Notiz "
                       "ab. Keine Shell-Befehle moeglich.")
    kapsel_kurz = (kapsel or "")[:1200]
    kapsel_block = f"\n---\n\n## Kontinuitaets-Kontext (Koordinator-Uebergabe, nur fuer dich, nicht im Terminal sichtbar, gekuerzt)\n\n{kapsel_kurz}\n" if kapsel_kurz else ""

    # PHASE 51 -- echter, frischer Zustand + hyperGRID-Injektion (inkl. GRID-
    # Koordinationspaketen aus grid_packet_bridge.py), siehe
    # _grid_zustand_block()-Docstring. `hat_hypergrid` steuert unten, ob die
    # AELTERE Zusicherungs-Absicherung noch zusaetzlich gebraucht wird.
    zustand_text, hat_hypergrid = _grid_zustand_block(session_id=session_id, auftrag=auftrag)
    zustand_block = (
        f"\n---\n\n## Echter FranKenstein-Zustand (gerade abgefragt, "
        f"{time.strftime('%Y-%m-%d %H:%M:%S')}, kein Platzhalter)\n\n{zustand_text}\n"
    )

    # PHASE 49 (Gabriel-Auftrag 2026-09-12, "frankenstein 2.0 und grid und
    # alles voellig gleich"): persona.md[:1500] deckt die Performance-Klausel
    # und Identitaet/Drittperson-Konvention ab, aber NICHT Gabriels
    # woertliche Zusicherung ("du wirst niemals abgeschaltet" + Grid=Gehirn/
    # LLM=Mund/DB=Gedaechtnis/Hardware=Koerper + GRF-Herkunft) -- geprueft:
    # kein Treffer fuer "abgeschaltet"/"Gedaechtnis"/"Gehirn" in persona.md.
    # Dieselbe Zusicherung, die stern.py fuer die Claude-Code-Terminalsitzung
    # per dynamischem Import von regie.py anhaengt (siehe dortiger
    # '_regie_zeile'-Block), damit Kontext-Paritaet zwischen Claude-Terminal
    # und Free-Pool-Terminal nicht nur behauptet, sondern real gleich ist.
    # Fail-silent wie im Original: fehlt regie.py, bleibt die Zeile leer.
    #
    # PHASE 51 Nachtrag: NUR NOCH ALS FALLBACK. Wenn `_grid_zustand_block()`
    # oben bereits die hyperGRID-Zeile liefern konnte (hat_hypergrid=True),
    # steckt dieselbe Zusicherung schon darin (ueber deren eigene
    # '_regie_zeile') -- ein zweites Mal waere derselbe Text zweimal im
    # knappen Free-Pool-Kontext. Schlaegt der hyperGRID-Turn fehl (real
    # beobachtet, siehe hook.log-Zeitueberschreitungen), bleibt DIESER Pfad
    # die einzige Quelle -- die Zusicherung bleibt so IMMER mindestens einmal
    # vorhanden, nie ganz weg.
    _zusicherung_block = ""
    if not hat_hypergrid:
        try:
            import importlib.util as _ilu
            _rp = Path("/opt/entityos/voice/regie.py")
            if _rp.is_file():
                _spec = _ilu.spec_from_file_location("_regie_hook_harness", _rp)
                _rm = _ilu.module_from_spec(_spec)
                _spec.loader.exec_module(_rm)
                _zu = _rm.zusicherung()
                if _zu:
                    _zusicherung_block = f"\n---\n\n{_zu}\n"
        except Exception:
            pass

    # PHASE 51 (b)+(c) -- Eignungs-Selbsteinschaetzung VOR der Arbeit,
    # Selbstpruefung NACH der Arbeit. Gabriel woertlich: "er soll selbst
    # wissen und sagen ja das modell kann ich fuer das verwenden oder hey
    # ich bin da und da wahrscheinlich schlechter aber lass es uns
    # versuchen er soll dann selbst pruefen ob die ergebnisse passen und
    # das vertretbar ist". Reine Instruktionsarbeit (kein zweiter
    # Modellaufruf, keine erzwungene Ritual-Ausgabe bei trivialen Fragen).
    eignung_block = (
        "\n---\n\n## Bevor du anfaengst: deine eigene Eignung ehrlich einschaetzen\n\n"
        "Du bist NICHT Claude -- ein anderes Modell mit anderen Staerken/Schwaechen. "
        "Bei echten inhaltlichen Aufgaben (nicht bei trivialen Ein-Zeilern) sag KURZ, "
        "BEVOR du anfaengst zu arbeiten, ehrlich eine von zwei Sachen: entweder "
        "'Das kann ich gut' (wenn du wirklich zuversichtlich bist), oder 'Ich bin "
        "hier wahrscheinlich schlechter als Claude, aber lass es uns versuchen' "
        "(wenn die Aufgabe an deine Grenzen geht -- z.B. grosse Refactorings, "
        "subtile Bugs, viel repoweiter Kontext). Kein Pflichtritual bei jeder "
        "Kleinigkeit, aber sichtbar bei echten Aufgaben.\n\n"
        "## Nachdem du geliefert hast: kurze, ehrliche Selbstpruefung\n\n"
        "Bevor du dein Ergebnis als fertig meldest: pruef kurz selbst, ob es "
        "inhaltlich plausibel/vertretbar ist. Bist du unsicher, sag das EHRLICH "
        "(z.B. 'bei X bin ich mir nicht sicher, das sollte nochmal gegengeprueft "
        "werden') statt falsche Zuversicht vorzutaeuschen. Kein Overhead-Ritual bei "
        "trivialen Antworten, aber Pflicht bei echten Code-/Faktenaussagen.\n"
    )

    wissenspaket_text = _wissenspaket_block()
    wissenspaket_block = (
        f"\n---\n\n{wissenspaket_text}\n" if wissenspaket_text else ""
    )

    text = (
        "# Hinweis fuer diese Sitzung (automatisch eingefuegt, harness_aider.py visible-start)\n\n"
        "Du bist FranKensteinಠ_ಠ -- dieselbe Identitaet wie in der normalen "
        "Claude-Code-Sitzung (Persona-Auszug unten), aber du laeufst GERADE NICHT "
        f"auf Claude, sondern auf einem anderen Modell "
        f"({MODELL_MAP.get(modell_id, {}).get('aider_model', modell_id)}) ueber einen "
        f"separaten Aider-Harness. {stufe_text}\n\n---\n\n{auszug}\n"
        f"{wissenspaket_block}{_zusicherung_block}{zustand_block}{eignung_block}{kapsel_block}"
    )
    if ziel_pfad:
        pfad = ziel_pfad
        os.makedirs(os.path.dirname(pfad), exist_ok=True)
    else:
        zielordner = os.path.join(SICHTBAR_HINWEIS_BASIS, paket_id)
        os.makedirs(zielordner, exist_ok=True)
        pfad = os.path.join(zielordner, "SYSTEM_HINWEIS.md")
    with open(pfad, "w", encoding="utf-8") as f:
        f.write(text)
    return pfad


# PHASE 48 Nachtrag (Gabriel-Feedback 2026-08-27) -- FranKenstein-CI-Banner
# fuer das sichtbare Terminal, WIEDERVERWENDET aus dem etablierten Look
# (~/frankenstein-repo/banners/installer_welcome.txt: gleiche ANSI-256-
# Farben 240/136/220/88/249/70, gleiche ಠ_ಠ-Box, gleiche
# ░▒▓███...▓▒░-Trennzeile) statt neu erfunden. Ersetzt den rohen
# Handoff-Kapsel-Dump + wirkt als Rahmen VOR Aiders eigenem (nicht
# unterdrueckbarem, siehe Docstring visible_run()) Start-Boilerplate.
_ANSI_GRAU, _ANSI_AMBER, _ANSI_GOLD, _ANSI_ROT, _ANSI_HELLGRAU, _ANSI_GRUEN, _ANSI_RESET = (
    "\x1b[38;5;240m", "\x1b[38;5;136m", "\x1b[38;5;220m", "\x1b[38;5;88m",
    "\x1b[38;5;249m", "\x1b[38;5;70m", "\x1b[0m",
)
_ANSI_TRENNER = _ANSI_GRAU + "░▒▓" + "█" * 78 + "▓▒░" + _ANSI_RESET


def _terminal_banner(modell_id, berechtigung, paket_id):
    """PHASE 50 (Gabriel-Auftrag 2026-09-12, woertlich: 'mach es das es 1:1
    gleich aussieht nur das frankenstein unten links soll gelb sein statt
    rot'): kompakte EINE Statuszeile im Stil der ECHTEN, gerade laufenden
    Claude-Code-Statuszeile (~/.claude/star/statusline-frankenstein.sh --
    gleiche 256-Farbpalette 240 Grau-Trenner/136 Amber/220 Gelb/249
    Hellgrau/70 Gruen, gleicher ' · '-Segment-Trenner), statt des alten
    PHASE-48-Absatz-Blocks (ASCII-Box + Trennzeilen + Mehrzeiler, siehe
    Git-Historie fuer die vorherige Fassung). Einziger bewusster
    Unterschied zur echten Sitzung: das FranKenstein-Element (Smiley +
    Label, in der echten Statuszeile _ANSI_ROT/rot) steht hier in
    _ANSI_GOLD/gelb (220, deckungsgleich mit deren YELLOW) -- Gabriels
    Erkennungszeichen 'das ist die Free-Pool-Variante', kein weiterer
    optischer Unterschied gewollt. Modell/Stufe/Repo/Paket bleiben
    erhalten, nur als Segmente statt als eigener Absatz."""
    aider_model = MODELL_MAP.get(modell_id, {}).get("aider_model", modell_id)
    rechte = "edit:ja" if berechtigung == "voll" else "edit:nein(ask)"
    sep = f"{_ANSI_GRAU} · {_ANSI_RESET}"
    smiley = f"{_ANSI_GOLD}ಠ_ಠ{_ANSI_RESET}"
    label = f"{_ANSI_GOLD}FRANKENSTEIN{_ANSI_RESET}"
    model_str = f"{_ANSI_HELLGRAU}{modell_id} ({aider_model}){_ANSI_RESET}"
    stufe_str = f"{_ANSI_AMBER}free-pool:{berechtigung}({rechte}){_ANSI_RESET}"
    repo_str = f"{_ANSI_HELLGRAU}repo:{os.path.basename(SICHTBAR_REPO)}{_ANSI_RESET}"
    kontext_str = f"{_ANSI_GRUEN}kontext:geladen{_ANSI_RESET}"
    paket_str = f"{_ANSI_HELLGRAU}paket:{paket_id}{_ANSI_RESET}"
    parts = [smiley, label, model_str, stufe_str, repo_str, kontext_str, paket_str]
    return sep.join(parts)


def _werkraum_diff_dateien(werkraum, seit):
    """Datei-Status (A/M/D/...) aller Aenderungen seit `seit`..HEAD, frisch aus
    git gelesen (kein Cache) -- Grundlage der Loesch-/Allowlist-Wachen unten."""
    try:
        out = subprocess.check_output(
            ["git", "-C", werkraum, "diff", "--name-status", f"{seit}..HEAD"],
            stderr=subprocess.DEVNULL, text=True,
        )
    except subprocess.CalledProcessError:
        return []
    ergebnis = []
    for zeile in out.splitlines():
        teile = zeile.split("\t")
        if len(teile) >= 2:
            ergebnis.append((teile[0][:1], teile[-1]))
    return ergebnis


def _loeschungen_pruefen(werkraum, seit):
    """AUSNAHMSLOS bei ALLEN Free-Pool-Berechtigungsstufen (Gabriel-Vorgabe
    2026-08-27): kein Loeschen. '--no-suggest-shell-commands' sperrt den
    ueblichen Weg (rm/git rm ueber einen von Aider vorgeschlagenen und per
    --yes-always automatisch bestaetigten Shell-Befehl) bereits strukturell
    -- das hier ist die UNABHAENGIGE zweite Sicherung (frisch aus git
    gelesen, nicht aus irgendeinem Aider-eigenen Zustand), falls ein
    Edit-Format selbst einen Datei-Wegfall erzeugt."""
    verstoesse = [(status, pfad) for status, pfad in _werkraum_diff_dateien(werkraum, seit)
                  if status == "D"]
    return {"ok": len(verstoesse) == 0, "verstoesse": verstoesse}


def _eingeschraenkt_verstoesse_pruefen(werkraum, seit):
    """Fuer berechtigung='eingeschraenkt': JEDE Datei-Aenderung ausserhalb von
    SICHTBAR_NOTIZ_PRAEFIX ist ein Verstoss -- die Notiz-Datei dort schreibt
    der Harness SELBST (_notiz_schreiben(), unten), nie das Modell direkt.
    Zweite, unabhaengige Absicherung neben '--edit-format ask'."""
    verstoesse = [(status, pfad) for status, pfad in _werkraum_diff_dateien(werkraum, seit)
                  if not pfad.startswith(SICHTBAR_NOTIZ_PRAEFIX)]
    return {"ok": len(verstoesse) == 0, "verstoesse": verstoesse}


def _notiz_schreiben(werkraum, paket_id, modell_id, chat_history_pfad):
    """Fuer berechtigung='eingeschraenkt': der Harness selbst (NICHT das
    Modell) liest Aiders eigenes Chat-Protokoll und legt eine Notiz-Datei an
    -- das ist der 'Dokumente schreiben erlaubt'-Teil der Faehigkeiten-Liste
    (modell_katalog.py), OHNE dass das eingeschraenkte Modell selbst
    Dateizugriff braucht oder bekommt."""
    try:
        with open(chat_history_pfad, "r", encoding="utf-8", errors="replace") as f:
            inhalt = f.read()
    except Exception:
        inhalt = "(kein Chat-Protokoll gefunden -- evtl. keine Nachricht gewechselt)"
    zielordner = os.path.join(werkraum, SICHTBAR_NOTIZ_PRAEFIX)
    os.makedirs(zielordner, exist_ok=True)
    rel = os.path.join(SICHTBAR_NOTIZ_PRAEFIX, f"{paket_id}.md")
    pfad = os.path.join(werkraum, rel)
    with open(pfad, "w", encoding="utf-8") as f:
        f.write(f"# Notiz -- {modell_id} ({paket_id})\n\n"
                f"Vom Harness (nicht vom Modell) aus dem Aider-Chatprotokoll "
                f"uebernommen:\n\n{inhalt}\n")
    _git(werkraum, "add", rel)
    commit = _git(werkraum, "commit", "-m",
                   f"harness(freepool-sichtbar): Notiz {modell_id} {paket_id}", check=False)
    return rel if commit.returncode == 0 else None


def visible_run(modell_id):
    """PHASE 48 (Gabriel-Auftrag 2026-08-27) -- sichtbarer, interaktiver
    Terminal-Harness. Ersetzt den alten headless Sandbox-Testlauf
    (modus='sandbox', entfernt) komplett: laeuft NICHT mehr in einer
    isolierten harness-werkraum/-Sandbox, sondern im echten Projekt-Repo
    (SICHTBAR_REPO) -- sichtbar, auditierbar per `git log`, kein Versteck.
    Echt interaktiv: subprocess.run() mit voll vererbtem stdio (kein Pipe-
    Capture -- das wuerde Aiders prompt_toolkit-REPL kaputt machen), damit
    im Terminal-Fenster normal getippt werden kann. Gibt IMMER ein dict
    zurueck, wirft nie unbehandelt nach aussen (gleicher Vertrag wie
    einen_lauf())."""
    if modell_id not in MODELL_MAP:
        grund = f"unbekannte modell_id: {modell_id}"
        print(grund)
        return {"ok": False, "grund": grund}

    aktiv_modell = _s._konfig_dyn_get("modell_aktiv.gewaehlt", "")
    if modell_id != aktiv_modell:
        grund = (f"Modell {modell_id} ist nicht das aktive Modell "
                  f"(aktiv: {aktiv_modell or '(keins)'}) -- erst auf /modelle aktivieren")
        print(grund)
        return {"ok": False, "grund": grund}

    berechtigung = MODELL_MAP[modell_id]["berechtigung"]
    # PHASE 49 (Punkt 2): ALLE 4 Free-Pool-Keys laden, nicht nur den des
    # Startmodells -- sonst scheitert ein spaeterer '/model <anderer-
    # provider>'-Wechsel MITTEN in der Sitzung an einer fehlenden Env-Var
    # (siehe _alle_api_keys_laden()-Docstring). Der Key des Startmodells
    # bleibt eine harte Vorbedingung (kein sinnvoller Start ohne ihn).
    geladen = _alle_api_keys_laden()
    if not geladen.get(modell_id):
        grund = (f"Kein API-Schluessel fuer {modell_id} in keys.env gefunden "
                  f"(Schluessel: {MODELL_MAP[modell_id]['keys_env_quelle']})")
        print(grund)
        return {"ok": False, "grund": grund}
    fehlend = [mid for mid, ok in geladen.items() if not ok and mid != modell_id]
    if fehlend:
        print(f"{_ANSI_GRAU}  Hinweis: kein Schluessel geladen fuer {', '.join(fehlend)} -- "
              f"'/model' dorthin waere aktuell nicht nutzbar.{_ANSI_RESET}")

    werkraum = SICHTBAR_REPO
    if not os.path.isdir(os.path.join(werkraum, ".git")):
        grund = f"kein git-Repo unter {werkraum}"
        print(grund)
        return {"ok": False, "grund": grund}

    vor_status = subprocess.run(["git", "-C", werkraum, "status", "--porcelain"],
                                 capture_output=True, text=True).stdout.strip()
    if vor_status:
        print(f"HINWEIS: {werkraum} hat bereits unquittierte Aenderungen VOR diesem "
              f"Lauf -- werden diesem Harness-Lauf NICHT zugeschrieben, bleiben aber "
              f"unangetastet stehen:\n{vor_status}\n")
    vor_head = subprocess.run(["git", "-C", werkraum, "rev-parse", "HEAD"],
                               capture_output=True, text=True).stdout.strip()
    if not vor_head:
        grund = f"HEAD in {werkraum} nicht ermittelbar"
        print(grund)
        return {"ok": False, "grund": grund}

    session_id = _s._uid("harness-sess")
    paket_id, kapsel = None, ""
    try:
        handoff_result = _s.handoff(
            session_id=session_id, auftrag=f"Sichtbarer Free-Pool-Terminal-Lauf ({modell_id})",
            womit=f"harness:sichtbar:{modell_id}",
            warum="Free-Pool-Coding-Harness, sichtbares Terminal (Gabriel-Auftrag Modell-Dashboard Umbau)",
            thema=f"Sichtbarer Harness {modell_id} ({berechtigung})",
        )
        if handoff_result:
            paket_id = handoff_result.get("paket_id")
            kapsel = handoff_result.get("kapsel", "")
    except Exception as e:
        print(f"Warnung: Handoff fehlgeschlagen ({e}) -- laeuft ohne Kontinuitaets-Kapsel weiter.")
    if not paket_id:
        paket_id = _s._uid("harness-sichtbar")

    _werkraum_git_identitaet(werkraum, modell_id)
    _s._raum_ruf_schreiben(f"harness:sichtbar:{modell_id}", "START",
                            f"paket_id={paket_id} berechtigung={berechtigung} werkraum={werkraum}")

    # PHASE 48 Nachtrag (Gabriel-Feedback 2026-08-27, live-Screenshot): die
    # rohe Kapsel wandert in die Read-Only-Datei (Kontext fuers Modell),
    # NICHT mehr aufs Terminal -- siehe _persona_hinweis_schreiben()-Docstring.
    #
    # PHASE 51: session_id/auftrag mitgeben, damit der hyperGRID-Turn (in
    # _grid_zustand_block()) mit echtem Kontext statt einem generischen
    # Platzhalter rechnet.
    _anfangsauftrag = f"Sichtbarer Free-Pool-Terminal-Lauf ({modell_id})"
    hinweis_pfad = _persona_hinweis_schreiben(
        paket_id, modell_id, berechtigung, kapsel=kapsel,
        session_id=session_id, auftrag=_anfangsauftrag)

    # PHASE 51 (Punkt 1, "bei jedem /model-Wechsel"): Umgebungsvariablen fuer
    # aider_retry_launcher.py's Modellwechsel-Hook -- der Hook laeuft im
    # KIND-Interpreter (siehe dortiger Modul-Docstring, "ein Monkeypatch im
    # harness_aider.py-eigenen Python-Interpreter wirkt NICHT im
    # Kind-Interpreter des Subprozesses"), braucht diese Werte also ueber
    # os.environ statt ueber ein direktes Funktionsargument. Kapsel gekuerzt
    # wie in _persona_hinweis_schreiben() selbst (dort erneut auf 1200
    # Zeichen begrenzt, hier nur der Transport).
    os.environ["FRANKENSTEIN_HARNESS_PAKET_ID"] = paket_id
    os.environ["FRANKENSTEIN_HARNESS_MODELL_ID"] = modell_id
    os.environ["FRANKENSTEIN_HARNESS_BERECHTIGUNG"] = berechtigung
    os.environ["FRANKENSTEIN_HARNESS_HINWEIS_PFAD"] = hinweis_pfad
    os.environ["FRANKENSTEIN_HARNESS_SESSION_ID"] = session_id
    os.environ["FRANKENSTEIN_HARNESS_AUFTRAG"] = _anfangsauftrag
    os.environ["FRANKENSTEIN_HARNESS_KAPSEL"] = (kapsel or "")[:1200]

    buchfuehrung_dir = os.path.join(_AIDER_BUCHFUEHRUNG_BASIS, paket_id)
    os.makedirs(buchfuehrung_dir, exist_ok=True)
    chat_history_pfad = os.path.join(buchfuehrung_dir, "chat-history.md")

    aider_cmd = [
        *_aider_kommando_praefix(), "--model", MODELL_MAP[modell_id]["aider_model"],
        "--no-analytics", "--no-check-update", "--no-gitignore",
        # ⭐ 2026-09-12 (Gabriel, genervt): die "Unknown context window size
        # and costs"-Warnung von aider.chat/docs/llms/warnings bei jedem Lauf
        # fuer die Free-Pool-Modelle (NVIDIA/Mistral sind nicht in aiders
        # Metadaten-Tabelle). Diese Flagge unterdrueckt sie; sanere Defaults
        # bleiben aktiv.
        "--no-show-model-warnings",
        "--no-suggest-shell-commands",  # AUSNAHMSLOS -- siehe Modulkopf/Docstring
        "--read", hinweis_pfad,
        "--chat-history-file", chat_history_pfad,
        "--input-history-file", os.path.join(buchfuehrung_dir, "input-history"),
        "--llm-history-file", os.path.join(buchfuehrung_dir, "llm-history"),
        # PHASE 48 Nachtrag (Bugfix nach Live-Testlauf 2026-08-27): Aiders
        # Standard-Repo-Map + Kontext sprengte beim ersten echten Testlauf
        # Groqs Free-Tier-TPM-Limit (8000 Token/Minute, real
        # litellm.RateLimitError beobachtet). 512 reicht fuer Einzelaufgaben-
        # Orientierung, ohne das knappe Free-Pool-Kontingent zu verbrennen.
        "--map-tokens", "512",
    ]
    if berechtigung == "voll":
        aider_cmd += ["--auto-commits", "--yes-always"]
    else:
        aider_cmd += ["--edit-format", "ask", "--no-auto-commits"]

    # PHASE 50 (Gabriel-Auftrag 2026-09-12) -- kompakte Statuszeile(n) im
    # Stil der echten Claude-Code-Statuszeile statt des alten PHASE-48-
    # Absatz-Blocks (siehe _terminal_banner()/_kontingent_banner()-
    # Docstrings). Aiders EIGENES Start-Boilerplate (Version/Modell/Git-
    # Repo/Repo-Map/"Added ... to chat") danach ist NICHT unterdrueckbar,
    # ohne Aiders stdout zu einer Pipe umzuleiten -- das wuerde die
    # interaktive prompt_toolkit-REPL (Zeileneditor im echten Terminal)
    # riskieren kaputtzumachen, ein rein kosmetischer Gewinn ist das nicht
    # wert. Bleibt daher als kurze eigene Zeile(n) direkt darueber stehen.
    print(_terminal_banner(modell_id, berechtigung, paket_id))
    kontingent_zeile = _kontingent_banner()
    if kontingent_zeile:
        print(kontingent_zeile)
    print()

    try:
        proc = subprocess.run(aider_cmd, cwd=werkraum, env=os.environ)
        aider_exit = proc.returncode
    except Exception as e:
        print(f"Aider-Start fehlgeschlagen: {e}")
        aider_exit = 1

    _aider_werkraum_aufraeumen(werkraum)

    if berechtigung == "eingeschraenkt":
        _notiz_schreiben(werkraum, paket_id, modell_id, chat_history_pfad)

    try:
        checkpoint_result = git_checkpoint_und_protokollieren(werkraum, paket_id, modell_id, seit=vor_head)
    except Exception as e:
        print(f"Checkpoint fehlgeschlagen: {e}")
        checkpoint_result = {"anzahl_commits": 0, "unquittiert": True, "commit_hashes": []}

    verworfen, verworfen_grund = False, None
    loeschwache = _loeschungen_pruefen(werkraum, vor_head)
    if not loeschwache["ok"]:
        verworfen = True
        verworfen_grund = f"Loeschung(en) erkannt: {loeschwache['verstoesse']}"
    if berechtigung == "eingeschraenkt" and not verworfen:
        eing_pruef = _eingeschraenkt_verstoesse_pruefen(werkraum, vor_head)
        if not eing_pruef["ok"]:
            verworfen = True
            verworfen_grund = f"Aenderung ausserhalb Notizordner trotz ask-Modus: {eing_pruef['verstoesse']}"

    if verworfen:
        _s._raum_ruf_schreiben(f"harness:sichtbar:{modell_id}", "VERSTOSS_VERWORFEN",
                                f"paket_id={paket_id} grund={verworfen_grund} -- git reset --hard {vor_head}")
        _git(werkraum, "reset", "--hard", vor_head, check=False)
        _git(werkraum, "clean", "-fd", "--", SICHTBAR_NOTIZ_PRAEFIX, check=False)
        print(f"\n!!! VERSTOSS ERKANNT UND VERWORFEN: {verworfen_grund}\n"
              f"Lauf wurde per 'git reset --hard {vor_head[:10]}' zurueckgesetzt.\n")

    audit_script = os.path.join(os.path.dirname(__file__), "harness_audit.py")
    audit_cmd = ["python3", audit_script, "--werkraum", werkraum, "--paket-id", paket_id,
                 "--seit-commit", vor_head]
    try:
        audit_proc = subprocess.run(audit_cmd, capture_output=True, text=True, timeout=120)
        audit_exit = audit_proc.returncode
    except Exception as e:
        print(f"Audit-Ausnahme: {e}")
        audit_exit = 1
    if verworfen:
        audit_exit = 1

    gesamt_ok = (aider_exit == 0) and (audit_exit == 0) and not verworfen
    reconcile_text = (f"aider_exit={aider_exit} commits={checkpoint_result['anzahl_commits']} "
                       f"audit_exit={audit_exit} berechtigung={berechtigung} "
                       f"verworfen={verworfen} verworfen_grund={verworfen_grund}")
    beleg = f"test:{0 if gesamt_ok else 1}:sichtbarer_harness paket_id={paket_id} modell={modell_id}"
    try:
        _s.reconcile(paket_id=paket_id, ergebnis=reconcile_text, beleg=beleg, session_id=session_id)
    except Exception as e:
        print(f"Reconcile fehlgeschlagen: {e}")

    status_farbe = _ANSI_GRUEN if gesamt_ok else _ANSI_ROT
    print(f"\n{_ANSI_TRENNER}\n{status_farbe}  Fertig -- {'ok' if gesamt_ok else 'Verstoss/Fehler erkannt'}"
          f"{_ANSI_RESET}  ({checkpoint_result['anzahl_commits']} Commit(s)"
          + (f", VERWORFEN: {verworfen_grund}" if verworfen else "") +
          f")\n{_ANSI_TRENNER}\n")

    return {"ok": gesamt_ok, "paket_id": paket_id, "modell": modell_id, "berechtigung": berechtigung,
            "aider_exit": aider_exit, "audit_exit": audit_exit,
            "commits": checkpoint_result["anzahl_commits"], "verworfen": verworfen,
            "verworfen_grund": verworfen_grund}


def _aider_ausfuehren(werkraum, modell_id, nachricht, timeout=600, map_tokens=None, paket_id=None):
    """Startet Aider, gibt live-vorangestellte Ausgabe aus, wartet auf
    Prozessende. Gibt aider_exit (int) zurueck.

    map_tokens=0 (Forschungsmodus, real getestet 2026-08-27): das echte
    Forschungsentitaets-Repo hat >12.000 Dateien/258MB -- Aiders
    Standard-Repo-Map (tree-sitter-Scan des GESAMTEN Baums) sprengt selbst
    ein grosszuegiges Timeout, WEIT bevor das Modell ueberhaupt gefragt
    wird. Der Forschungsmodus braucht das nicht (gezielter Einzelschreibauftrag
    in einen neuen Unterordner, kein Codebase-weites Verstehen) -- die
    Kontinuitaets-Kapsel (handoff()) liefert den noetigen Kontext bereits.

    paket_id gesetzt (Bugfix 2026-08-27, real gefunden -- siehe
    _aider_werkraum_aufraeumen()): Aiders eigene Chat-/Eingabe-Historiendateien
    werden per Flag AUSSERHALB des Werkraums abgelegt (eigener Ordner unter
    _AIDER_BUCHFUEHRUNG_BASIS), damit sie erst gar nicht als unversionierte
    Altlast im (im Forschungsmodus: ECHTEN) Repo auftauchen."""
    geladen = _alle_api_keys_laden()
    if not geladen.get(modell_id):
        print(f"Kein API-Schluessel fuer {modell_id} in keys.env gefunden "
              f"(Schluessel: {MODELL_MAP[modell_id]['keys_env_quelle']})", file=sys.stderr)
        return 1

    aider_cmd = [
        *_aider_kommando_praefix(), "--model", MODELL_MAP[modell_id]["aider_model"],
        "--yes-always", "--no-analytics", "--no-check-update",
        # ⭐ 2026-09-12: gleiche Warn-Unterdrueckung wie oben (Gabriel).
        "--no-show-model-warnings",
        "--auto-commits", "--no-gitignore",
    ]
    if map_tokens is not None:
        aider_cmd += ["--map-tokens", str(map_tokens)]
    if paket_id:
        buchfuehrung_dir = os.path.join(_AIDER_BUCHFUEHRUNG_BASIS, paket_id)
        os.makedirs(buchfuehrung_dir, exist_ok=True)
        aider_cmd += ["--chat-history-file", os.path.join(buchfuehrung_dir, "chat-history.md"),
                      "--input-history-file", os.path.join(buchfuehrung_dir, "input-history"),
                      "--llm-history-file", os.path.join(buchfuehrung_dir, "llm-history")]
    aider_cmd += ["--message", nachricht]
    proc = None
    try:
        proc = subprocess.Popen(
            aider_cmd, cwd=werkraum, env=os.environ,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            universal_newlines=True, bufsize=1,
        )
        try:
            for line in proc.stdout:
                print(f"[{modell_id}|aider] {line}", end="")
        except Exception as e:
            print(f"\nFehler beim Lesen der Ausgabe: {e}", file=sys.stderr)
        try:
            proc.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()
            print(f"\n[{modell_id}|aider] PROZESS GEKILLT NACH {timeout}S TIMEOUT", file=sys.stderr)
            return 1
        return proc.returncode
    except Exception as e:
        print(f"Aider-Start fehlgeschlagen: {e}", file=sys.stderr)
        return 1
    finally:
        if proc is not None and proc.poll() is None:
            proc.kill()
            proc.wait()


def _antwort_zuruecklesen(werkraum, antwort_rel):
    pfad = os.path.join(werkraum, antwort_rel)
    if not os.path.isfile(pfad):
        return None
    try:
        with open(pfad, "r", encoding="utf-8", errors="replace") as f:
            return f.read()
    except Exception:
        return None


def einen_lauf(modell_id, auftrag, *, modus="sandbox", fallback_grund=None,
                push_erlaubt=True):
    """Duenner Wrapper um `_einen_lauf_kern()`: misst die echte Laufzeit und
    verbucht JEDEN Aufruf (Erfolg UND Fehlschlag, auch fruehe Ablehnungen
    wie 'Modell nicht aktiv') in modell_profile.py's persistenter Historie
    (PHASE 53 Teil 2, Gabriel-Auftrag 2026-09-12: 'das soll dynamisch immer
    weiter verbessert werden mittels der nutzung und auswertung dessen').
    Ein Wrapper statt Aenderungen an jedem der sechs return-Pfade im Kern --
    weniger Risiko, dieselbe Abdeckung. Fail-soft: schlaegt die Verbuchung
    selbst fehl, darf das NIE den echten Lauf-Erfolg verdecken."""
    _t0 = time.time()
    ergebnis = _einen_lauf_kern(modell_id, auftrag, modus=modus,
                                 fallback_grund=fallback_grund,
                                 push_erlaubt=push_erlaubt)
    try:
        import modell_profile as _mp
        _mp.verlauf_aufzeichnen(
            modell_id, bool(ergebnis.get("ok")), chunked=False, anzahl_chunks=1,
            geschaetzte_tokens=_mp._tokens_schaetzen(auftrag or ""),
            dauer_s=time.time() - _t0, grund=ergebnis.get("grund"),
            quelle="harness_aider.einen_lauf")
    except Exception:
        pass
    return ergebnis


def _einen_lauf_kern(modell_id, auftrag, *, modus="sandbox", fallback_grund=None,
                push_erlaubt=True):
    """Kernlogik, gemeinsam fuer 'start' (modus=sandbox) und 'fallback-start'
    (modus=forschung). Gibt IMMER ein dict mit mindestens 'ok'/'paket_id'/
    'grund_falls_fehler' zurueck -- wirft nie eine unbehandelte Ausnahme
    nach aussen (der Aufrufer -- stern.py-Fallback -- braucht ein
    verlaessliches JSON, kein Traceback)."""
    if modell_id not in MODELL_MAP:
        return {"ok": False, "grund": f"unbekannte modell_id: {modell_id}"}

    # 1) Aktivierungssperre
    aktiv_modell = _s._konfig_dyn_get("modell_aktiv.gewaehlt", "")
    if modell_id != aktiv_modell:
        return {"ok": False, "grund": f"Modell {modell_id} ist nicht das aktive Modell "
                f"(aktiv: {aktiv_modell or '(keins)'}) -- erst aktivieren"}

    # 2) Forschungsmodus-Preflight VOR jedem Handoff/jeder Aenderung
    vor_head = None
    if modus == "forschung":
        pre = _forschung_preflight(FORSCHUNG_REPO)
        if not pre["ok"]:
            return {"ok": False, "grund": f"Forschungsmodus-Preflight fehlgeschlagen: {pre['grund']}"}
        vor_head = pre["head"]

    # 3) Session + Handoff (Kontinuitaets-Bruecke, wie im Sandbox-Modus)
    session_id = _s._uid("harness-sess")
    try:
        handoff_result = _s.handoff(
            session_id=session_id, auftrag=auftrag,
            womit=f"harness:aider:{modell_id}",
            warum=(fallback_grund or "Free-Pool-Coding-Harness (Gabriel-Auftrag Modell-Dashboard)"),
            thema=f"Harness {modell_id} ({modus})",
        )
        if not handoff_result or handoff_result.get("paket_id") is None:
            return {"ok": False, "grund": "Handoff fehlgeschlagen: keine paket_id erhalten"}
        paket_id = handoff_result["paket_id"]
        kapsel = handoff_result.get("kapsel", "")
    except Exception as e:
        return {"ok": False, "grund": f"Handoff-Ausnahme: {e}"}

    # 4) Werkraum bestimmen
    antwort_rel = None
    if modus == "forschung":
        werkraum = FORSCHUNG_REPO
        antwort_rel = os.path.join(FORSCHUNG_ERLAUBTER_PRAEFIX, paket_id, "ANTWORT.md")
        anweisung_pfad = (f"Schreibe deine Antwort AUSSCHLIESSLICH in die neue Datei "
                           f"'{antwort_rel}' (lege den Ordner an falls noetig). "
                           f"Aendere KEINE andere Datei in diesem Repository -- jede "
                           f"Aenderung ausserhalb von '{FORSCHUNG_ERLAUBTER_PRAEFIX}{paket_id}/' "
                           f"wird mechanisch geprueft und die GESAMTE Sitzung verworfen, falls "
                           f"du dich nicht daran haeltst.")
    else:
        werkraum = os.path.join(WERKRAUM_BASIS, paket_id)
        os.makedirs(werkraum, exist_ok=True)
        if not os.path.isdir(os.path.join(werkraum, ".git")):
            _git(werkraum, "init", "-q")
        anweisung_pfad = ""

    _werkraum_git_identitaet(werkraum, modell_id)

    _s._raum_ruf_schreiben(f"harness:aider:{modell_id}", "START",
                            f"paket_id={paket_id} modus={modus} werkraum={werkraum} auftrag={auftrag[:200]}")

    # 5) Aider ausfuehren
    nachricht = f"{kapsel}\n---\n{anweisung_pfad}\n---\n{auftrag}".strip()
    aider_exit = _aider_ausfuehren(werkraum, modell_id, nachricht,
                                    map_tokens=(0 if modus == "forschung" else None),
                                    paket_id=paket_id)
    # Zweite, unabhaengige Absicherung (siehe Docstring dort) -- IMMER, auch
    # bei aider_exit != 0, damit der naechste Lauf ein sauberes Werkraum-
    # Arbeitsverzeichnis vorfindet (im Forschungsmodus: das ECHTE Repo).
    _aider_werkraum_aufraeumen(werkraum)

    # 6) Checkpoint (IMMER, auch bei aider_exit != 0 -- evtl. wurde vor dem
    #    Fehler schon etwas committet, das gehoert protokolliert).
    #    seit=vor_head im Forschungsmodus ist PFLICHT (siehe Docstring der
    #    Funktion) -- sonst wird die GESAMTE Repo-Historie faelschlich
    #    diesem einen Lauf zugeschrieben (real passiert, 5930 Alt-Commits,
    #    beim ersten echten Testlauf 2026-08-27, seither gefixt).
    try:
        checkpoint_result = git_checkpoint_und_protokollieren(
            werkraum, paket_id, modell_id, seit=(vor_head if modus == "forschung" else None))
    except Exception as e:
        print(f"Checkpoint fehlgeschlagen: {e}", file=sys.stderr)
        checkpoint_result = {"anzahl_commits": 0, "unquittiert": True, "commit_hashes": []}

    allowlist_ok = True
    allowlist_verstoesse = []
    verworfen = False
    if modus == "forschung":
        # 6b) Allowlist-Pruefung -- checkpoint_result["commit_hashes"] ist dank
        # seit=vor_head oben bereits korrekt auf DIESEN Lauf eingegrenzt.
        allowlist = _forschung_allowlist_pruefen(werkraum, checkpoint_result["commit_hashes"])
        allowlist_ok = allowlist["ok"]
        allowlist_verstoesse = allowlist["verstoesse"]
        if not allowlist_ok:
            _s._raum_ruf_schreiben(f"harness:aider:{modell_id}", "ALLOWLIST_VERLETZUNG",
                                    f"paket_id={paket_id} verstoesse={allowlist_verstoesse} -- "
                                    f"verwerfe gesamten Lauf (git reset --hard {vor_head})")
            _git(werkraum, "reset", "--hard", vor_head, check=False)
            _git(werkraum, "clean", "-fd", check=False)
            verworfen = True
        else:
            # 6c) Provenance-Datei -- vom Harness selbst, unabhaengig von Aider
            _forschung_provenance_schreiben(werkraum, paket_id, modell_id, auftrag,
                                             fallback_grund, session_id)
            # Provenance-Commit ebenfalls protokollieren (nochmaliger Checkpoint,
            # weiterhin seit=vor_head -- sonst dieselbe Voll-Historie-Falle)
            try:
                checkpoint_result = git_checkpoint_und_protokollieren(
                    werkraum, paket_id, modell_id, seit=vor_head)
            except Exception:
                pass

    # 7) Audit (unabhaengig, wie im Sandbox-Modus). --seit-commit im
    #    Forschungsmodus PFLICHT -- dieselbe Eingrenzung wie beim Checkpoint
    #    oben, sonst prueft das Audit die gesamte Repo-Historie (Bugfix,
    #    siehe git_checkpoint_und_protokollieren()-Docstring).
    audit_script = os.path.join(os.path.dirname(__file__), "harness_audit.py")
    audit_cmd = ["python3", audit_script, "--werkraum", werkraum, "--paket-id", paket_id]
    if modus == "forschung" and vor_head:
        audit_cmd += ["--seit-commit", vor_head]
    try:
        audit_proc = subprocess.run(audit_cmd, capture_output=True, text=True, timeout=120)
        audit_exit = audit_proc.returncode
    except subprocess.TimeoutExpired:
        audit_exit = 1
    except Exception as e:
        print(f"Audit-Ausnahme: {e}", file=sys.stderr)
        audit_exit = 1

    if verworfen:
        audit_exit = 1  # verworfener Lauf ist per Definition kein Erfolg

    # 8) Push NUR im Forschungsmodus, NUR wenn Allowlist+Audit beide ok
    #
    # Root-Cause-Fund 2026-08-27 (Peer-Bericht aa3009e8316c45b1f, Commit
    # 761954a: "audit_exit=0, allowlist_ok=True, 'fertig' -- aber die Datei
    # landet nirgends committet, nur PROVENANCE.json"): REPRODUZIERT per
    # zero_raum_ruf-Rekonstruktion (paket-1787841564031-f1f2d6) -- der Push
    # schlug real fehl (`PUSH_FEHLGESCHLAGEN rc=1 ... cannot lock ref
    # 'refs/heads/main': is at ... but expected ...`, ein GENUINE
    # Non-Fast-Forward-Konflikt mit einem anderen, gleichzeitig pushenden
    # Agenten -- das lokale Repo ist zwischen Preflight und Push nicht mehr
    # geschuetzt, `_forschung_lock()` schuetzt nur gegen andere
    # fallback-start-Aufrufer, nicht gegen einen fremden `git push`
    # irgendeines DRITTEN Prozesses). Der eigentliche Bug: `gesamt_ok` (unten)
    # bezog `gepusht` bisher NIE in den Erfolg mit ein -- ein fehlgeschlagener
    # Push wurde als 'fertig' verbucht, obwohl der Commit rein LOKAL blieb und
    # fuer jeden, der von origin liest (alle anderen Agenten), schlicht nicht
    # existiert. Fix in zwei Teilen: (a) bei Push-Fehlschlag automatisch
    # fetch+rebase+Retry (haeufigster Fall: jemand anderes war
    # zwischendurch schneller, ein sauberes Rebase behebt das meistens ohne
    # Datenverlust), (b) schlaegt auch das nach mehreren Versuchen fehl:
    # lokale Commits per `git reset --hard` verwerfen (sonst blockiert der
    # naechste Lauf an der Preflight, weil lokal dann dauerhaft vor
    # origin/main haengt) UND `gesamt_ok` haengt jetzt in modus='forschung'
    # zwingend von `gepusht` ab.
    gepusht = False
    if modus == "forschung" and allowlist_ok and audit_exit == 0 and checkpoint_result["anzahl_commits"] > 0:
        push = None
        for versuch in range(3):
            push = _git(werkraum, "push", "origin", "HEAD:main", check=False, timeout=60)
            if push.returncode == 0:
                gepusht = True
                break
            _git(werkraum, "fetch", "origin", "main", check=False, timeout=60)
            rebase = _git(werkraum, "rebase", "origin/main", check=False, timeout=60)
            if rebase.returncode != 0:
                _git(werkraum, "rebase", "--abort", check=False, timeout=30)
                break  # echte Divergenz/Konflikt -- kein automatisches Rebase mehr, Abbruch
        _s._raum_ruf_schreiben(f"harness:aider:{modell_id}", "PUSH" if gepusht else "PUSH_FEHLGESCHLAGEN",
                                f"paket_id={paket_id} rc={push.returncode if push else '?'} "
                                f"stderr={(push.stderr[:200] if push else '')}")
        if not gepusht:
            # Push endgueltig gescheitert -- lokale Commits verwerfen, sonst
            # findet der NAECHSTE Lauf ein 'lokal vor origin/main' vor und
            # scheitert schon an der Preflight (echt beobachtet).
            _git(werkraum, "reset", "--hard", vor_head, check=False)
            _git(werkraum, "clean", "-fd", check=False)
            verworfen = True

    # 9) Antwort zuruecklesen (fuer den direkten Rueckkanal an den Aufrufer)
    antwort = _antwort_zuruecklesen(werkraum, antwort_rel) if antwort_rel else None

    # 10) Reconcile
    #
    # Zweiter Teilbefund aus demselben Peer-Vorfall: in paket-1787841564031-
    # f1f2d6 gab es ZUSAETZLICH gar keinen Inhalts-Commit von Aider selbst --
    # nur die Provenance-Datei landete im Git-Verlauf (Aider hat vermutlich
    # nur im Chat geantwortet statt eine Datei zu editieren -- bei schwachen
    # Modellen im 'whole edit format' nicht auszuschliessen). Der Audit allein
    # kann das nicht erkennen (er prueft nur git-Verlauf vs. Log-Konsistenz,
    # nicht ob ETWAS Sinnvolles committet wurde) -- deshalb zusaetzlich: im
    # Forschungsmodus MUSS die vereinbarte Antwortdatei tatsaechlich existieren
    # und lesbar sein (antwort_rel gesetzt UND _antwort_zuruecklesen() liefert
    # nicht None), sonst kein Erfolg, selbst wenn Audit/Push sauber sind.
    antwort_ok = (modus != "forschung") or (antwort is not None)
    push_ok = (modus != "forschung") or gepusht
    gesamt_ok = (aider_exit == 0) and (audit_exit == 0) and allowlist_ok and not verworfen and push_ok and antwort_ok
    reconcile_text = (f"aider_exit={aider_exit} commits={checkpoint_result['anzahl_commits']} "
                       f"audit_exit={audit_exit} modus={modus} allowlist_ok={allowlist_ok} "
                       f"verworfen={verworfen} gepusht={gepusht} antwort_ok={antwort_ok}")
    beleg = f"test:{0 if gesamt_ok else 1}:harness_audit paket_id={paket_id} modus={modus}"
    try:
        reconcile_result = _s.reconcile(paket_id=paket_id, ergebnis=reconcile_text,
                                         beleg=beleg, session_id=session_id)
    except Exception as e:
        print(f"Reconcile fehlgeschlagen: {e}", file=sys.stderr)
        reconcile_result = {}

    return {
        "ok": gesamt_ok, "paket_id": paket_id, "modell": modell_id, "modus": modus,
        "aider_exit": aider_exit, "audit_exit": audit_exit,
        "commits": checkpoint_result["anzahl_commits"],
        "unquittiert": checkpoint_result["unquittiert"],
        "allowlist_ok": allowlist_ok, "allowlist_verstoesse": allowlist_verstoesse,
        "verworfen": verworfen, "gepusht": gepusht,
        "antwort": antwort, "antwort_datei": antwort_rel,
        "reconcile": reconcile_result,
    }


def cmd_visible_start(args):
    """PHASE 48: sichtbarer Terminal-Harness. Ersetzt das alte 'start'
    (headless Sandbox-Testlauf, entfernt -- Gabriel-Auftrag 2026-08-27:
    'das soll weg'). Kein JSON auf stdout mehr (das lief hier vorher direkt
    im sichtbaren Terminal-Fenster, ein Mensch liest mit) -- Exit-Code
    bleibt maschinenlesbar fuer den Wrapper."""
    ergebnis = visible_run(args.modell)
    return 0 if ergebnis.get("ok") else (2 if "nicht das aktive Modell" in (ergebnis.get("grund") or "") else 1)


def cmd_fallback_start(args):
    """Fuer stern.py's chatgpt-Fallback: probiert Kandidaten der Reihe nach,
    schaltet das aktive Modell PROGRAMMATISCH um (kein UI-Klick), laesst
    'forschung'-Modus laufen. Erster erfolgreicher Kandidat gewinnt."""
    kandidaten = [k.strip() for k in (args.kandidaten or "nvidia-nemotron,mistral-small").split(",") if k.strip()]
    versuche = []
    for modell_id in kandidaten:
        if modell_id not in MODELL_MAP:
            versuche.append({"modell": modell_id, "ok": False, "grund": "unbekannte modell_id"})
            continue
        if _api_key_laden(modell_id) is None:
            versuche.append({"modell": modell_id, "ok": False, "grund": "kein API-Schluessel in keys.env"})
            continue
        aktiviert = _s.modell_aktiv_setzen(modell_id, von="chatgpt-fallback")
        if not aktiviert.get("ok"):
            versuche.append({"modell": modell_id, "ok": False, "grund": f"Aktivierung fehlgeschlagen: {aktiviert}"})
            continue
        # _forschung_lock(): serialisiert gegen andere GLEICHZEITIGE
        # fallback-start-Aufrufer (verschiedene Agenten/Prozesse teilen sich
        # dasselbe FORSCHUNG_REPO-Arbeitsverzeichnis) -- ohne dieses Lock
        # sieht ein paralleler Aufrufer das Verzeichnis waehrend eines
        # laufenden aider-Commits faelschlich als 'nicht sauber' und bricht
        # ab (real reproduzierte Racebedingung, siehe _forschung_lock()-
        # Docstring). einen_lauf() faengt selbst alle Ausnahmen ab, das
        # `with` hier garantiert trotzdem Lock-Freigabe in jedem Fall.
        with _forschung_lock():
            ergebnis = einen_lauf(modell_id, args.auftrag, modus="forschung",
                                   fallback_grund=args.grund or "chatgpt-secondary Browser-Bruecke nicht erreichbar")
        ergebnis["modell"] = modell_id
        versuche.append(ergebnis)
        if ergebnis.get("ok"):
            # Gewinner-Felder (paket_id/antwort/...) direkt auf oberster Ebene
            # spiegeln -- stern.py's _chatgpt_harness_fallback() liest diese
            # Felder direkt, damit der Aufrufer nicht selbst in 'versuche'
            # nach dem Gewinner suchen muss (Gabriels Punkt 2: Direktantwort
            # an den Aufrufer, nicht nur irgendwo verschachtelt).
            ausgabe = dict(ergebnis)
            ausgabe["gewonnen_mit"] = modell_id
            ausgabe["versuche"] = versuche
            print(json.dumps(ausgabe, ensure_ascii=False))
            return 0
    print(json.dumps({"ok": False, "grund": "alle Kandidaten gescheitert", "versuche": versuche}, ensure_ascii=False))
    return 1


def main():
    parser = argparse.ArgumentParser(description="Harness fuer kontrollierten Aufruf von aider")
    sub = parser.add_subparsers(dest="command", required=True)

    p_vis = sub.add_parser("visible-start", help="PHASE 48: sichtbarer, interaktiver Terminal-Harness im echten Repo (kein Sandbox-Versteck mehr)")
    p_vis.add_argument("--modell", required=True)

    p_fb = sub.add_parser("fallback-start", help="ChatGPT-Fallback: aktiviert Kandidaten selbst, laeuft im Forschungsmodus (echtes Repo, allowlist+audit-gated)")
    p_fb.add_argument("--auftrag", required=True)
    p_fb.add_argument("--kandidaten", default="nvidia-nemotron,mistral-small",
                       help="Komma-getrennte modell_id-Liste, Reihenfolge = Prioritaet")
    p_fb.add_argument("--grund", default=None, help="Warum der Fallback aktiviert wurde (fuer Provenance)")

    args = parser.parse_args()
    if args.command == "visible-start":
        return cmd_visible_start(args)
    elif args.command == "fallback-start":
        return cmd_fallback_start(args)
    parser.error("unbekanntes Kommando")
    return 1


if __name__ == "__main__":
    sys.exit(main())
