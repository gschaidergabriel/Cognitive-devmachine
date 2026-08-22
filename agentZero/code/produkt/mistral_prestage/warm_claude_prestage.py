"""STANDING warm Claude-Sonnet Vorstufen-Notweg -- Gabriels Umbau 2026-08-22
(ersetzt den ersten Entwurf: ein `claude -p`-Einzelaufruf JE Mistral-Ausfall.
Dieser Entwurf ist es NICHT mehr -- siehe unten).

⭐⭐⭐ NUR der LETZTE Ausweg. Solange Mistral (transport.
mistral_chat_json_rotating, alle rotierenden Schluessel) liefert, ruft
NIEMAND dieses Modul -- prestage.py/innenraum.py greifen nur im
except-Zweig hierher. Im Leerlauf macht dieser Weg NULL Aufrufe, NULL
Kosten -- er WARTET nur (siehe unten, warum das trotzdem nicht "nichts
tun" bedeutet).

⭐⭐ STEHEND, NICHT EPHEMER. Der erste Entwurf spawnte pro Mistral-Ausfall
einen frischen `claude -p <prompt>`-Prozess (spawn -> Antwort -> Prozess
weg) -- korrekt ephemer, aber JEDER Ausfall zahlte den vollen Node-/MCP-Boot
neu (gemessen an Zero selbst, siehe warm_zero.py-Kopf: ~2,4s allein Boot).
Gabriels Umbau: EIN laufender Prozess je Vorstufen-Modus (aussen/chat,
innen/autonom) bleibt zwischen Zuegen OFFEN (stdin bleibt offen, anders als
warm_zero.WarmPool, das absichtlich NACH einem Zug schliesst, weil Zeros
Gesetz Zustandslosigkeit VERLANGT -- die Vorstufen-Rolle hat kein solches
Gesetz, im Gegenteil: Gabriels Vorgabe ist genau die Wiederverwendung ueber
Zuege hinweg, fuer Boot- UND Cache-Vorteil). Der Prozess wird beim ERSTEN
Bedarf gebootet (lazy) und bleibt danach warm, solange er lebt und unter dem
Token-Deckel bleibt -- der ZWEITE und jeder weitere Ausfall in Folge trifft
dann sofort einen bereits laufenden Prozess, kein Boot mehr.

⭐⭐ SELBST-REZYKLIERUNG BEI 350.000 TOKEN. Ein stehender Prozess akkumuliert
Kontext ueber seine Zuege (jeder weitere Zug traegt den gewachsenen
Gespraechsverlauf im naechsten `usage.input_tokens`, dieselbe Form wie jede
mehrzuegige Chat-API) -- ohne Deckel wuerde er irgendwann sein Kontextfenster
sprengen. `_StandingProcess.zug()` liest die ECHTE Nutzung nach jedem Zug
(headless_zero.nutzung_aus_envelope(), wiederverwendet, nicht neu gebaut) und
haelt die zuletzt gemeldete Kontextgroesse fest. Ueberschreitet sie
TOKEN_RECYCLE_SCHWELLE, schliesst der Manager den Prozess NACH der Antwort
und bootet beim naechsten Zug einen frischen -- "es gibt immer einen
warmen bereit" (der alte antwortet noch normal zu Ende, der naechste Zug
trifft den neuen).

⭐ CACHE-OPTIMIERT, DIESELBEN ZWEI GRIFFE WIE warm_zero.WarmPool (siehe
dessen `_argv`-Kommentar "TOKEN-KETTE 2026-08-22", hier wiederverwendet, nicht
neu gemessen): `--append-system-prompt-file` (eine STABILE Datei statt
Kommandozeilentext -- der Systemprompt-Praefix bleibt ueber Prozess-/
Aufrufgrenzen hinweg byte-identisch) und `--exclude-dynamic-system-prompt-
sections` (nimmt Claude Codes eigene pro-Maschine-Abschnitte aus dem
Cache-Praefix heraus, damit sie den dahinter angehaengten stabilen
Vorstufen-Systemprompt nicht mitreissen).

⭐ WIEDERVERWENDET, NICHT NEU GEBAUT: das stream-json-Sende-/Lese-Protokoll
(Popen mit stdin/stdout-Pipes, `select`-basiertes Warten, `type:"result"`-
Ereignis) ist dasselbe Muster wie warm_zero.WarmPool.answer() -- nur dass
hier stdin NACH dem Zug offen bleibt statt zu schliessen, und der Prozess
NICHT nach jedem Zug getoetet wird. `headless_zero.nutzung_aus_envelope()`
wird woertlich wiederverwendet fuer die Tokenzahlen.

⚠️ Voller End-to-End-Beweis (echter `claude`-Prozess, echte OAuth-Credential,
echtes Mehrzug-Verhalten von `--input-format stream-json` UEBER mehrere
gesendete Nachrichten auf DEMSELBEN offenen stdin) ist NICHT Teil dieses
Baus -- das braucht die echte VPS-Umgebung (Credential unter
/var/lib/clay/.claude/.credentials.json) und eine bewusste Messung, wie
warm_zero.py selbst sie hat (siehe dessen Kopf: "gemessen bewiesen"). Diese
Datei ist dafuer gebaut, GETESTET mit einem gefakten `popen_fn` (Messgeraet-
vor-Glauben gilt auch hier: kein echter Prozessstart in einem Unit-Test) --
der Mechanismus (Boot, Wiederverwendung, Rezyklierung bei 350k, Envelope-
Parsing, Fehlerpfad) ist bewiesen, das Verhalten des ECHTEN `claude`-Binaries
bei mehreren stdin-Nachrichten in einem Prozess ist es an dieser Stelle
NICHT -- das gehoert in eine Live-Probe auf dem VPS, bevor dieser Weg im
Ernstfall vertraut wird.

⭐ NICHT AN EINEN STARTUP-HAKEN VERDRAHTET. `warm_up()` bootet beide
Prozesse VORAB (bevor der erste Ausfall eintritt) -- das ist, was Gabriels
"steht + wartet, auch im Leerlauf" fordert. Ob/wo ein Dienst-Start (service.py
o.ae.) das aufruft, ist eine Betriebs-Entscheidung ausserhalb dieses
Feature-Branches (kein Anfassen von service.py/systemd hier) -- ohne
expliziten Aufruf bleibt der Weg beim bewiesenen Fallback: lazy beim ersten
Bedarf gebootet, danach warm.
"""
from __future__ import annotations

import json
import re
import select
import subprocess
import threading
import time
from pathlib import Path
from typing import Any, Callable

from . import headless_zero as hz

TOKEN_RECYCLE_SCHWELLE = 350_000
ANTWORT_TIMEOUT_S = 180.0
BOOT_WARTE_S = 0.0  # kein Vorwaerm-Boot-Vorteil noetig -- der Prozess wartet ohnehin

_FENCE_RE = re.compile(r"```(?:json)?\s*\n?(.*?)\n?```", re.DOTALL)


class WarmClaudeFallbackError(RuntimeError):
    """Weder Mistral noch der stehende Claude-Notweg haben diesen Zug
    geliefert -- der Aufrufer (prestage.py/innenraum.py) hat dann keinen
    dritten Weg mehr."""


def _envelope_aus_text(text: str) -> dict[str, Any]:
    """Der Mistral-Weg erzwingt JSON-Modus serverseitig; `claude -p` hat das
    nicht -- robust parsen: erst der ganze Text, sonst ein ```json-Codeblock,
    den das Modell trotz Anweisung ("NUR das JSON-Objekt") manchmal
    drumherum baut."""
    for kandidat in (text, *_FENCE_RE.findall(text)):
        kandidat = (kandidat or "").strip()
        if not kandidat:
            continue
        try:
            geparst = json.loads(kandidat)
        except (json.JSONDecodeError, TypeError):
            continue
        if isinstance(geparst, dict):
            return geparst
    raise WarmClaudeFallbackError(f"claude-Antwort ist kein JSON-Envelope: {text[:300]!r}")


class _StandingProcess:
    """EIN laufender `claude -p --input-format stream-json`-Prozess, der
    ueber mehrere Vorstufen-Zuege hinweg WARM bleibt -- stdin bleibt offen
    (siehe Modul-Kopf fuer den Unterschied zu warm_zero.WarmPool)."""

    def __init__(self, proc, sysdatei: str, *, select_fn: Callable = select.select):
        self.proc = proc
        self.sysdatei = sysdatei
        self.geboren = time.time()
        self.letzte_kontextgroesse = 0
        self.zuege = 0
        self._lock = threading.Lock()
        # ⭐ Injizierbar, damit ein Test einen Fake-Prozess (kein echtes
        # Dateideskriptor-Objekt, select.select() braucht sonst fileno())
        # ohne echtes OS-Pipe durchspielen kann -- dieselbe "kein echter
        # Prozess in einem Unit-Test"-Konvention wie ueberall sonst im Paket.
        self._select_fn = select_fn

    def lebt(self) -> bool:
        return self.proc.poll() is None

    def ueber_dem_deckel(self) -> bool:
        return self.letzte_kontextgroesse >= TOKEN_RECYCLE_SCHWELLE

    def schliessen(self) -> None:
        try:
            if self.proc.stdin and not self.proc.stdin.closed:
                self.proc.stdin.close()
        except Exception:
            pass
        try:
            self.proc.terminate()
        except Exception:
            pass

    def zug(self, *, system: str, user: str, timeout: float = ANTWORT_TIMEOUT_S) -> dict[str, Any]:
        """EIN Vorstufen-Zug auf diesem laufenden Prozess. `system` wird nur
        beim ALLERERSTEN Zug ueber die Datei wirksam (--append-system-prompt-
        file wird beim Boot gelesen) -- innerhalb der Prozesslebensdauer ist
        er ohnehin konstant (derselbe Modus bootet mit demselben System), der
        Parameter steht hier nur fuer die Signatur-Symmetrie mit dem
        Mistral-Weg (system, user)."""
        if not self.lebt():
            raise WarmClaudeFallbackError("Prozess bereits tot")
        msg = json.dumps({"type": "user", "message": {
            "role": "user", "content": [{"type": "text", "text": user}]}})
        with self._lock:
            try:
                self.proc.stdin.write(msg + "\n")
                self.proc.stdin.flush()
            except Exception as exc:
                raise WarmClaudeFallbackError(f"stdin-Schreibfehler: {exc}") from exc

            result_ev = None
            frist = time.time() + timeout
            while True:
                rest = frist - time.time()
                if rest <= 0:
                    raise WarmClaudeFallbackError(f"keine Antwort in {timeout}s")
                bereit, _, _ = self._select_fn([self.proc.stdout], [], [], min(rest, 1.0))
                if not bereit:
                    continue
                line = self.proc.stdout.readline()
                if not line:
                    raise WarmClaudeFallbackError("Prozess hat stdout geschlossen (tot)")
                try:
                    ev = json.loads(line)
                except Exception:
                    continue
                if ev.get("type") == "result":
                    result_ev = ev
                    break

        if not isinstance(result_ev, dict) or result_ev.get("is_error"):
            raise WarmClaudeFallbackError(
                f"Fehlerergebnis: {str((result_ev or {}).get('result',''))[:300]}")
        text = result_ev.get("result")
        if not isinstance(text, str) or not text.strip():
            raise WarmClaudeFallbackError("kein Ergebnistext")

        nutzung = hz.nutzung_aus_envelope(result_ev) or {}
        kontextgroesse = int(nutzung.get("input_tokens") or 0) + int(nutzung.get("output_tokens") or 0)
        self.letzte_kontextgroesse = kontextgroesse
        self.zuege += 1

        payload = _envelope_aus_text(text)
        receipt = {
            "engine": "claude-fallback-warm",
            "modell": "sonnet",
            "cost_usd": result_ev.get("total_cost_usd"),
            "kontextgroesse_tokens": kontextgroesse,
            "zuege_auf_diesem_prozess": self.zuege,
            "prozess_alter_s": round(time.time() - self.geboren, 1),
            "usage": nutzung,
        }
        return {"payload": payload, "receipt": receipt}


class WarmClaudeFallbackManager:
    """Haelt GENAU EINEN warmen `claude -p`-Prozess fuer EINEN Vorstufen-
    Modus am Leben. Lazy gebootet (kein Aufruf, keine Kosten, bis der erste
    Mistral-Ausfall -- oder bis `warm_up()` explizit gerufen wird), danach
    wiederverwendet ueber Zuege hinweg, rezykliert bei Tod oder ueber dem
    Token-Deckel."""

    def __init__(self, *, modus: str, popen_fn: Callable = subprocess.Popen,
                 sysdatei_verzeichnis: str = "/tmp", select_fn: Callable = select.select):
        self.modus = modus
        self._popen_fn = popen_fn
        self._sysdatei_verzeichnis = sysdatei_verzeichnis
        self._select_fn = select_fn
        self._proc: _StandingProcess | None = None
        self._letztes_system: str | None = None
        self._lock = threading.Lock()

    def _sysdatei(self, system: str) -> str:
        # Stabiler Dateiname je Modus, INHALT nur neu geschrieben, wenn er
        # sich aendert -- --append-system-prompt-file haelt den Cache-Praefix
        # ueber Prozess-/Kommandozeilengrenzen hinweg identisch (derselbe
        # Trick wie warm_zero.WarmPool._sysdatei).
        p = Path(self._sysdatei_verzeichnis) / f"claude-fallback-warm-sys-{self.modus}.md"
        if not p.is_file() or p.read_text(encoding="utf-8") != system:
            p.write_text(system, encoding="utf-8")
        return str(p)

    def _argv(self, sysdatei: str) -> list[str]:
        return [
            "claude", "-p",
            "--model", "sonnet",
            "--tools", "", "--setting-sources", "", "--permission-mode", "dontAsk",
            "--append-system-prompt-file", sysdatei,
            "--exclude-dynamic-system-prompt-sections",
            "--input-format", "stream-json", "--output-format", "stream-json", "--verbose",
            "--no-session-persistence",
        ]

    def _env(self) -> dict:
        return {
            "HOME": "/var/lib/clay", "PATH": "/usr/local/bin:/usr/bin:/bin", "LANG": "C.UTF-8",
            "DISABLE_UPDATES": "1",
            "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC": "1",
            "CLAUDE_CODE_DISABLE_BACKGROUND_TASKS": "1",
            "CLAUDE_CODE_DISABLE_AUTO_MEMORY": "1",
            "CLAUDE_CODE_DISABLE_CLAUDE_MDS": "1",
            "CLAUDE_CODE_SKIP_PROMPT_HISTORY": "1",
            # ⭐ derselbe Schalter wie ueberall sonst in diesem Paket:
            # unterdrueckt den verwalteten UserPromptSubmit-Hook -- dieser
            # Prozess darf NIE als Zero-Gespraechszug in turns/active_turns
            # auftauchen.
            "CLAYVERSE_PIPELINE_MANAGED": "1",
        }

    def _boot(self, system: str) -> _StandingProcess:
        sysdatei = self._sysdatei(system)
        proc = self._popen_fn(
            self._argv(sysdatei), stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, env=self._env(), text=True, bufsize=1)
        self._letztes_system = system
        return _StandingProcess(proc, sysdatei, select_fn=self._select_fn)

    def warm_up(self) -> None:
        """Bootet den Prozess VORAB, im Hintergrund -- damit er schon steht
        und wartet, BEVOR der erste Mistral-Ausfall eintritt (Gabriels
        "im Leerlauf einfach warm warten"). Nicht an einen Dienst-Start
        verdrahtet -- siehe Modul-Kopf."""
        def _hintergrund():
            with self._lock:
                if self._proc is None or not self._proc.lebt():
                    try:
                        self._proc = self._boot(self._letztes_system or "")
                    except Exception:
                        pass  # warm_up darf nie werfen -- der Kaltweg (lazy Boot) traegt so oder so
        threading.Thread(target=_hintergrund, daemon=True).start()

    def zug(self, *, system: str, user: str) -> dict[str, Any]:
        """EIN Vorstufen-Zug ueber den stehenden Fallback. Bootet bei Bedarf
        (kein Prozess, toter Prozess, oder ueber dem Token-Deckel), sonst
        wird der laufende Prozess wiederverwendet -- "es gibt immer einen
        warmen bereit"."""
        with self._lock:
            muss_booten = (
                self._proc is None or not self._proc.lebt()
                or self._proc.ueber_dem_deckel()
                or self._letztes_system != system
            )
            if muss_booten:
                if self._proc is not None:
                    self._proc.schliessen()
                self._proc = self._boot(system)
            proc = self._proc
        try:
            return proc.zug(system=system, user=user)
        except WarmClaudeFallbackError:
            # Ein gescheiterter Zug toetet den Prozess -- der NAECHSTE Aufruf
            # bootet frisch, statt denselben (vielleicht kaputten) Prozess
            # erneut zu versuchen. Dieser Zug selbst wird nicht wiederholt --
            # das ist Sache des Aufrufers (kein Schleifen-Retry hier).
            with self._lock:
                proc.schliessen()
                if self._proc is proc:
                    self._proc = None
            raise


# ── ZWEI stehende Prozesse, EINER je Vorstufen-Modus ────────────────────
# Getrennt, damit jeder seinen EIGENEN byte-identischen Systemprompt-Praefix
# behaelt (prestage._BASE_RULES+... vs. innenraum._INNEN_DENKRAUM sind
# komplett verschiedene Texte -- ein gemeinsamer Prozess wuerde bei jedem
# Modus-Wechsel neu booten muessen, also gaebe es nie einen wirklich
# "stehenden" Vorteil).
_AUSSEN = WarmClaudeFallbackManager(modus="aussen")
_INNEN = WarmClaudeFallbackManager(modus="innen")


def aussen_zug(*, system: str, user: str) -> dict[str, Any]:
    """Der Notweg fuer die AEUSSERE (Chat-)Vorstufe -- prestage.run_prestage
    ruft dies NUR im except-Zweig um transport.mistral_chat_json_rotating."""
    return _AUSSEN.zug(system=system, user=user)


def innen_zug(*, system: str, user: str) -> dict[str, Any]:
    """Der Notweg fuer die INNERE (autonome) Vorstufe -- innenraum.
    run_innere_vorstufe ruft dies NUR im except-Zweig um denselben Mistral-Ruf."""
    return _INNEN.zug(system=system, user=user)


def warm_up_beide() -> None:
    """Beide stehenden Prozesse vorab booten (Hintergrund, nie werfend) --
    der Griff, den ein spaeterer Dienst-Start ziehen kann, um "steht schon,
    bevor der erste Ausfall kommt" zu bekommen. Siehe Modul-Kopf: hier NICHT
    automatisch aufgerufen."""
    _AUSSEN.warm_up()
    _INNEN.warm_up()
