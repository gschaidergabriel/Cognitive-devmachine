"""Der dauerhafte Zero-Prozess -- vorgewaermte Prozesse ohne Kaltstart je Zug.

⭐ GABRIEL 19.08.: "mach den dauerhaften zero-prozess." Gemessen: ein frisches
`claude -p` braucht ~2,4s allein fuer den Boot (Node, MCP, Konfiguration), bevor
ueberhaupt gedacht wird. Ein Zug dauert dadurch ewig.

⭐⭐ DER TRICK, gemessen bewiesen: `claude -p --input-format stream-json` bootet
im LEERLAUF (waehrend es auf stdin wartet). Sende ich sofort -> send->result
4,7s. Sende ich nach 5s Leerlauf -> send->result 2,5s. Der Boot ist also
vorziehbar. Also halte ich pro Mensch ein paar Prozesse WARM (gebootet, wartend)
bereit; kommt ein Zug, bekommt er einen warmen -- der Boot ist schon bezahlt.

⚠️⚠️ ZUSTANDSLOSIGKEIT BLEIBT. Zeros Gesetz: kein eigenes Gedaechtnis, UnifiedDB
ist die einzige Kontinuitaet. Ein Prozess, der mehrere Zuege sieht, wuerde das
brechen. Deshalb: JEDER warme Prozess nimmt GENAU EINEN Prompt, dann stirbt er.
Der Hintergrund fuellt nach. So ist jeder Zug frisch -- nur der Boot ist
vorgezogen, nicht der Zustand.

⚠️ RUeCKFALL: ist kein warmer Prozess bereit (Pool leer, Prozess tot), gibt
answer() None zurueck und der Aufrufer nimmt den bewaehrten Kaltweg. Der
dauerhafte Prozess darf nie eine Verschlechterung sein -- nur eine Abkuerzung,
wenn sie da ist.
"""
from __future__ import annotations

import collections
import json
import os
import select
import subprocess
import threading
import time
from pathlib import Path

from . import headless_zero as hz

POOL_SIZE = int(os.environ.get("CLAYVERSE_WARM_POOL", "2"))

# ⭐⭐⭐ GEMESSENER PRODUKTIONSAUSFALL, 2026-08-20. Die Antwortschleife unten
# lautete:
#     frist = time.time() + timeout
#     while time.time() < frist:
#         line = warm.proc.stdout.readline()
# `readline()` auf einer Roehre blockiert OHNE Zeitgrenze. Die Frist wurde nur
# ZWISCHEN zwei Zeilen geprueft -- kommt keine einzige, wird sie nie erreicht.
# Die Zeitgrenze war Zierrat.
# Gemessen: ein Abnahmezug auf "hallo" stand 13 Minuten, vier warme Prozesse
# lagen daneben und schwiegen. Fuer einen Menschen im Browser heisst das: der
# Chat antwortet nie, ohne Fehler, ohne Meldung. Aufgefallen ist es nur, weil
# alle Messreihen des Tages den Warmpool ausdruecklich abgeschaltet hatten --
# der Kaltweg funktionierte die ganze Zeit.
ERSTE_ZEILE_S = float(os.environ.get("CLAYVERSE_WARM_ERSTE_ZEILE", "25"))
# Ein warmer Prozess, der den Auftrag hat, meldet sich binnen Sekunden mit
# seinem ersten Ereignis. Bleibt das aus, ist der Prozess kaputt und nicht
# beschaeftigt -- dann sofort auf den Kaltweg, statt die volle Frist zu warten.
AUSFAELLE_BIS_SPERRE = 3
SPERRE_S = 600.0
WARMUP_S = 5.5           # so lange braucht der Boot im Leerlauf (gemessen ~5s)
MAX_ALTER_S = 900        # ein warmer Prozess, der 15 min nie drankam, wird ersetzt
_KANONISCH = (("gabriel", "session:gabriel"), ("andreas", "session:andreas"))


class _Warm:
    __slots__ = ("proc", "sysdatei", "geboren", "bereit_ab")

    def __init__(self, proc, sysdatei):
        self.proc = proc
        self.sysdatei = sysdatei
        self.geboren = time.time()
        self.bereit_ab = self.geboren + WARMUP_S

    def lebt(self) -> bool:
        return self.proc.poll() is None

    def bereit(self) -> bool:
        return self.lebt() and time.time() >= self.bereit_ab

    def zu_alt(self) -> bool:
        return time.time() - self.geboren > MAX_ALTER_S


class WarmPool:
    def __init__(self, db_path="/var/lib/clay/wiki.db", state_root="/var/lib/clayverse"):
        self.db_path = db_path
        self.state_root = state_root
        self._pools: dict[tuple, collections.deque] = {k: collections.deque() for k in _KANONISCH}
        self._sysdateien: dict[tuple, str] = {}
        self._lock = threading.Lock()
        self._an = False

    # ── Start/Stopp ────────────────────────────────────────────────────────
    def starten(self) -> None:
        with self._lock:
            if self._an:
                return
            self._an = True
        threading.Thread(target=self._nachfuell_schleife, daemon=True).start()

    # ── Die per-Mensch stabile Systemprompt-Datei ─────────────────────────
    def _sysdatei(self, user, session) -> str:
        key = (user, session)
        pfad = self._sysdateien.get(key)
        if pfad and Path(pfad).is_file():
            return pfad
        text = hz._systemanweisung(self.db_path, user, session)
        p = Path(f"/tmp/zero-warm-sys-{user}.md")
        p.write_text(text, encoding="utf-8")
        self._sysdateien[key] = str(p)
        return str(p)

    def _argv(self, user, session, sysdatei) -> list[str]:
        # ⚠️ Der warme Prozess hat feste Werkzeuge (bei Boot gesetzt, nicht je
        # Zug waehlbar). Also die volle erlaubte Liste -- die Sicherheitsgrenze
        # ist ohnehin managed-settings (Bash/Artifact verboten), nicht diese
        # Auswahl; die Vorstufe lenkt die Werkzeugwahl im caveman_prompt.
        return [
            "claude", "-p",
            "--model", "sonnet",
            "--settings", hz.MANAGED_SETTINGS, "--setting-sources", "",
            # native Werkzeuge EXPLIZIT inkl. WebSearch/WebFetch (Default lud sie nicht)
            "--tools", "Bash,BashOutput,KillShell,Read,Write,Edit,MultiEdit,NotebookEdit,Glob,Grep,WebSearch,WebFetch,TodoWrite,Task",
            "--permission-mode", "dontAsk",
            "--append-system-prompt-file", sysdatei,
            "--input-format", "stream-json", "--output-format", "stream-json", "--verbose",
            "--no-session-persistence", "--max-turns", "8",
        ]

    def _env(self, user, session) -> dict:
        return {
            "HOME": "/var/lib/clay", "PATH": "/usr/local/bin:/usr/bin:/bin", "LANG": "C.UTF-8",
            "PYTHONPATH": "/opt/clayverse", "CLAYVERSE_STATE_ROOT": self.state_root,
            "CLAYVERSE_DB_PATH": self.db_path, "CLAYVERSE_USER_ID": user,
            "CLAYVERSE_SESSION_ID": session, "DISABLE_UPDATES": "1",
            "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC": "1", "CLAUDE_CODE_SKIP_PROMPT_HISTORY": "1",
            "CLAUDE_CODE_DISABLE_AUTO_MEMORY": "1", "CLAUDE_CODE_DISABLE_CLAUDE_MDS": "1",
            "CLAUDE_CODE_DISABLE_BACKGROUND_TASKS": "1", "CLAYVERSE_PIPELINE_MANAGED": "1",
        }

    def _boote_einen(self, user, session) -> _Warm | None:
        try:
            sysdatei = self._sysdatei(user, session)
            proc = subprocess.Popen(
                self._argv(user, session, sysdatei), stdin=subprocess.PIPE,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                env=self._env(user, session), text=True, bufsize=1)
            return _Warm(proc, sysdatei)
        except Exception:
            return None

    def _nachfuell_schleife(self) -> None:
        while True:
            for key in _KANONISCH:
                pool = self._pools[key]
                with self._lock:
                    # tote/alte raus
                    lebende = collections.deque(w for w in pool if w.lebt() and not w.zu_alt())
                    for w in pool:
                        if w not in lebende:
                            try: w.proc.terminate()
                            except Exception: pass
                    self._pools[key] = lebende
                    fehlend = POOL_SIZE - len(lebende)
                if fehlend > 0:
                    for _ in range(fehlend):
                        w = self._boote_einen(*key)
                        if w:
                            with self._lock:
                                self._pools[key].append(w)
            time.sleep(1.0)

    # ── Der Zug: einen warmen Prozess nehmen, EINEN Prompt, dann sterben ──
    def answer(self, caveman_prompt: str, *, user_id: str, session_id: str,
               timeout: int = 240) -> dict | None:
        # ⭐ Sicherung: haben die letzten Versuche nur geschwiegen, ist der Pool
        # kaputt und nicht langsam. Dann gar nicht erst hineingehen -- sonst
        # kostet jeder Zug die volle Frist, bevor er den Kaltweg findet.
        if time.time() < getattr(self, "_gesperrt_bis", 0.0):
            return None
        key = (user_id, session_id)
        if key not in self._pools:
            return None
        with self._lock:
            pool = self._pools[key]
            warm = None
            while pool:
                kandidat = pool.popleft()
                if kandidat.bereit():
                    warm = kandidat
                    break
                elif kandidat.lebt() and not kandidat.zu_alt():
                    pool.append(kandidat)  # noch nicht warm -- hinten anstellen
                    break                   # nichts Bereites gefunden
                else:
                    try: kandidat.proc.terminate()
                    except Exception: pass
            if warm is None:
                return None
        # Ab hier ausserhalb des Locks -- der Prozess ist unser allein.
        started = time.perf_counter()
        try:
            msg = json.dumps({"type": "user", "message": {"role": "user",
                              "content": [{"type": "text", "text": caveman_prompt}]}})
            warm.proc.stdin.write(msg + "\n")
            warm.proc.stdin.flush()
            warm.proc.stdin.close()
        except Exception:
            self._toete(warm)
            return None

        result_ev = None
        frist = time.time() + timeout
        erste_frist = time.time() + ERSTE_ZEILE_S
        stumm = False
        try:
            while True:
                # Die Frist gilt fuer das WARTEN, nicht nur fuer die Pausen
                # zwischen zwei Zeilen -- das war der Fehler.
                rest = min(frist, erste_frist) - time.time()
                if rest <= 0:
                    stumm = True
                    break
                bereit, _, _ = select.select([warm.proc.stdout], [], [], min(rest, 1.0))
                if not bereit:
                    continue
                line = warm.proc.stdout.readline()
                if not line:
                    break
                erste_frist = frist      # er lebt -- ab jetzt gilt die volle Frist
                try:
                    ev = json.loads(line)
                except Exception:
                    continue
                if ev.get("type") == "result":
                    result_ev = ev
                    break
        finally:
            self._toete(warm)

        if stumm:
            self._ausfaelle = getattr(self, "_ausfaelle", 0) + 1
            if self._ausfaelle >= AUSFAELLE_BIS_SPERRE:
                self._gesperrt_bis = time.time() + SPERRE_S
                print(f"warm_zero: {self._ausfaelle} stumme Prozesse hintereinander -- "
                      f"Pool fuer {int(SPERRE_S)}s gesperrt, es geht ueber den Kaltweg",
                      file=__import__("sys").stderr)
            return None
        self._ausfaelle = 0

        if not isinstance(result_ev, dict):
            return None
        if result_ev.get("is_error"):
            return None
        text = result_ev.get("result")
        if not isinstance(text, str) or not text:
            return None
        if text.startswith(hz._BLOCKED_PREFIX):
            return None
        return {
            "caveman_answer": text,
            "num_turns": result_ev.get("num_turns"),
            "duration_ms_claude_code": result_ev.get("duration_ms"),
            "duration_ms_api": result_ev.get("duration_api_ms"),
            "cost_usd": result_ev.get("total_cost_usd"),
            "wall_ms": (time.perf_counter() - started) * 1000.0,
            "claude_session_id": result_ev.get("session_id"),
            "warm": True,
        }

    def _toete(self, warm: _Warm) -> None:
        try:
            warm.proc.terminate()
        except Exception:
            pass


# Ein Prozess-weiter Pool, faul gestartet.
POOL = WarmPool()
