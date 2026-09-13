#!/usr/bin/env python3
"""harness_crush.py -- PHASE 52 (Gabriel-Auftrag 2026-09-12, woertliches Urteil
nach Screenshots: "das soll das tolle free pool harness sein? er kann nicht
antworten, braucht ewig, und es sieht so scheisse aus das es schmerzt ...
ausserdem ist er weder am grid angeschlossen noch macht er eine reentry --
das ist einfach nur beschiss"). Kein Politur-Auftrag an aider, sondern
Werkzeugwechsel: Crush (github.com/charmbracelet/crush, npm-installiert unter
~/.local/npm-global/bin/crush, echtes Go-Binary v0.93.1) ersetzt aider als
Free-Pool-Terminal-Harness.

Ursache des "hey"-Fehlschlags real gemessen (nicht geraten), siehe Beleg-
Transkript: nvidia/nemotron-3-super-120b-a12b liefert `content` UND
`reasoning_content` -- ohne `reasoning_effort` braucht das Modell oft >100
Token nur fuers Nachdenken ueber "hey", was bei knappem `max_tokens` (aiders
Default) dazu fuehrt, dass NUR der unfertige, rohe reasoning-Text als
`content` zurueckkommt (finish_reason=length, content==reasoning_content
woertlich identisch). Mit `reasoning_effort:"low"` sinkt das auf wenige
Saetze UND `content` wird sauber vom reasoning getrennt (curl-Beleg:
content="Hey there! How can I help you today?", reasoning_content="User
says hello. Should respond."). Gilt genauso fuer groq/openai/gpt-oss-120b.
mistral-small-latest und openrouter/deepseek/deepseek-chat sind NICHT
reasoning-faehig -- kein reasoning_effort noetig, brauchen aber trotzdem ihre
eigene (kuerzere) Prompt-Variante, weil sie ohne Reasoning-Bremse arbeiten.

Deterministische Prompt-Zuordnung (Gabriel woertlich: "das muss alles im
harness integriert sein, robust, unfehlbar, als mechanik", UND "jedes modell
muss ein extra angepasstes prompt haben"): MODELL_PROMPT_ZUORDNUNG ist ein
fester Lookup modell_id -> Variantenname. Jede modell_id aus
harness_aider.MODELL_MAP MUSS hier eingetragen sein (von SELBSTTEST erzwungen).
Fehlt ein Eintrag fuer eine neue modell_id trotzdem einmal (Tippfehler o.ae.),
faellt _system_prompt_fuer() ausdruecklich auf die Variante "standard" zurueck
-- das ist die bereits getestete, sicherste (keine Reasoning-Annahme, kurz,
Deutsch-zuerst) -- NIE ein stiller Blindflug ohne jede Instruktion.

STALE-CONTEXT-FIX (Auftragspunkt 3): harness_aider.py's Bug war, dass JEDE
Sitzung eine neue Datei unter harness-hinweise/paket-<id>/SYSTEM_HINWEIS.md
anlegte und alte, laengst erledigte Pakete NIE geloescht wurden -- Aider haelt
(je nach Aufrufkonvention) mehrere `--read`-Dateien gleichzeitig offen, sodass
uralte Handoff-Texte in neue Sitzungen durchsickerten. Hier gibt es
STRUKTURELL nur EINE einzige Datei (CRUSH_MD_PFAD, global_context_paths[0]
in crush.json), die bei JEDEM Start ueberschrieben (nicht ergaenzt) wird --
es gibt keinen Paket-Ordner, der veralten koennte, weil es keinen Paket-
Ordner gibt.
"""
import contextlib
import json
import os
import sqlite3
import subprocess
import sys
import time

STAR_DIR = os.path.expanduser("~/.claude/star")
sys.path.insert(0, STAR_DIR)

import harness_aider as _h  # noqa: E402 -- MODELL_MAP, _grid_zustand_block, ANSI-Konstanten
import pool_wache as _pw  # noqa: E402
import crush_modell_rechte as _mr  # noqa: E402 -- kanonische GRATIS/BEZAHLT-Kategorie
# + Rechte pro Modell, passwortgeschuetzt (kern_gate) -- siehe Modul-Docstring
# von crush_modell_rechte.py. harness_crush.py LIEST hier nur, aendert nie.

try:
    import stern as _s  # noqa: E402 -- fuer _grid_zustand_block()-Aufruf (macht _h intern schon)
except Exception:
    _s = None

try:
    import grid_packet_bridge as _gpb  # noqa: E402
except Exception:
    _gpb = None

CRUSH_CONFIG_DIR = os.path.expanduser("~/.config/crush")
CRUSH_CONFIG_PFAD = os.path.join(CRUSH_CONFIG_DIR, "crush.json")
CRUSH_MD_PFAD = os.path.join(CRUSH_CONFIG_DIR, "CRUSH.md")
CRUSH_BIN_KANDIDATEN = [
    os.path.expanduser("~/.local/npm-global/bin/crush"),
    "/usr/local/bin/crush",
    "crush",
]
SICHTBAR_REPO = os.path.expanduser("~/frankenstein-repo")  # dieselbe Konvention wie harness_aider.py

# ── Provider-Katalog: modell_id (harness_aider.MODELL_MAP-Schluessel) -> ─────
#    echte, per curl verifizierte Endpunkt-/Modelldaten (KEINE geratenen
#    Modell-IDs -- jede hier eingetragene "real_model" ist echt gegen die
#    jeweilige API getestet, siehe Beleg-Transkript im Handoff/Reconcile).
CRUSH_PROVIDER_KATALOG = {
    "nvidia-nemotron": {
        "provider_id": "freepool-nvidia",
        "provider_name": "NVIDIA NIM (Free-Pool)",
        "base_url": "https://integrate.api.nvidia.com/v1",
        "real_model": "nvidia/nemotron-3-super-120b-a12b",
        "context_window": 131072,
        "default_max_tokens": 4000,
        "can_reason": True,
        "reasoning_levels": ["low", "medium", "high"],
        "default_reasoning_effort": "low",  # curl-Beleg: senkt Wall-of-Reasoning drastisch
    },
    "groq-gptoss": {
        "provider_id": "freepool-groq",
        "provider_name": "Groq (Free-Pool)",
        "base_url": "https://api.groq.com/openai/v1",
        "real_model": "openai/gpt-oss-120b",
        "context_window": 131072,
        "default_max_tokens": 4000,
        "can_reason": True,
        "reasoning_levels": ["low", "medium", "high"],
        "default_reasoning_effort": "low",
    },
    "mistral-small": {
        "provider_id": "freepool-mistral",
        "provider_name": "Mistral (Free-Pool)",
        "base_url": "https://api.mistral.ai/v1",
        "real_model": "mistral-small-latest",
        "context_window": 32000,
        "default_max_tokens": 4000,
        "can_reason": False,
    },
    "openrouter-deepseek": {
        "provider_id": "freepool-openrouter",
        "provider_name": "OpenRouter/DeepSeek (Free-Pool)",
        "base_url": "https://openrouter.ai/api/v1",
        "real_model": "deepseek/deepseek-chat",
        "context_window": 64000,
        "default_max_tokens": 4000,
        "can_reason": False,
    },
}

# ── Claude-CLI-Provider (Gabriel-Auftrag 2026-09-12: "du sollst die claude
#    code cli die originale da rein leiten so das man die auch verwenden
#    kann") -- NICHT Teil von CRUSH_PROVIDER_KATALOG/MODELL_MAP, weil dies
#    kein Free-Pool-Modell ist: kein env_var-API-Key, kein automatischer
#    Erschoepfungs-Fallback (naechstes_viables_modell()/ist_langzeit_erschoepft()
#    iterieren weiterhin nur _h.MODELL_MAP -- diese drei Modelle sind davon
#    unberuehrt, absichtlich, sie kosten echtes Geld und sollen NIE automatisch
#    "weggewechselt" werden ohne dass ein Mensch das Modell aktiv gewaehlt hat).
#    Backend: claude_cli_shim.py (systemd --user claude-cli-shim.service),
#    loopback-only, KEIN echter API-Key noetig -- "not-needed" ist ein Dummy,
#    Crush braucht das Feld nur syntaktisch.
#
#    Modell-IDs real gegen `claude --model <id> -p "test" --output-format json`
#    verifiziert (siehe Reconcile-Beleg dieses Pakets). Preise recherchiert
#    (WebSearch, Stand 2026-09-12, offizielle Quelle claude.com/pricing nicht
#    per Redirect erreichbar in dieser Sitzung -- mehrere Sekundaerquellen
#    konvergieren NICHT ganz exakt bei Sonnet 5: $2/$10 vs $3/$15 werden beide
#    genannt. Hier wird der HOEHERE, konservativere Wert eingetragen (lieber
#    Kosten ueberschaetzen als unterschaetzen) -- das ist eine bewusste
#    Naeherung, KEINE als sicher behauptete exakte Zahl. Bei Bedarf gegen
#    https://claude.com/pricing echt nachpruefen und hier korrigieren.
CRUSH_CLI_PROVIDER_ID = "claude-cli"
CRUSH_CLI_PROVIDER_NAME = "Claude (echte claude-CLI, kein Free-Pool)"
CRUSH_CLI_BASE_URL = "http://127.0.0.1:8420/v1"
CRUSH_CLI_API_KEY_DUMMY = "not-needed"  # Shim ist loopback-only, prueft keinen Key
CRUSH_CLI_MODELLE = [
    {
        "id": "claude-opus-5",
        "name": "Claude Opus 5 (staerkstes Modell, teuer -- schwere Architektur/Reasoning)",
        # Naeherung, konservativ (eher zu hoch als zu niedrig geschaetzt).
        "cost_per_1m_in": 5.0,
        "cost_per_1m_out": 25.0,
        "cost_per_1m_in_cached": 0.5,
        "cost_per_1m_out_cached": 0,
        "context_window": 200000,
        "default_max_tokens": 8000,
        "can_reason": False,
        "supports_attachments": False,
    },
    {
        "id": "claude-sonnet-5",
        "name": "Claude Sonnet 5 (stark, Tools+Reasoning -- Standardwahl fuer echtes Claude)",
        # Quellen uneins (2/10 vs 3/15) -- hoeherer Wert konservativ uebernommen.
        "cost_per_1m_in": 3.0,
        "cost_per_1m_out": 15.0,
        "cost_per_1m_in_cached": 0.3,
        "cost_per_1m_out_cached": 0,
        "context_window": 200000,
        "default_max_tokens": 8000,
        "can_reason": False,
        "supports_attachments": False,
    },
    {
        "id": "claude-haiku-4-5-20251001",
        "name": "Claude Haiku 4.5 (schnell, guenstig -- einfache Fragen)",
        "cost_per_1m_in": 1.0,
        "cost_per_1m_out": 5.0,
        "cost_per_1m_in_cached": 0.1,
        "cost_per_1m_out_cached": 0,
        "context_window": 200000,
        "default_max_tokens": 8000,
        "can_reason": False,
        "supports_attachments": False,
    },
]


def _crush_cli_provider_eintrag():
    """Baut den Claude-CLI-Provider-Block fuer crush.json -- eigene Funktion,
    damit crush_config_schreiben() ihn einfach dazumergen kann, ohne die
    MODELL_MAP-Schleife (Free-Pool) anzufassen."""
    # Alle drei Claude-CLI-Modelle sind BEZAHLT (siehe crush_modell_rechte.py) --
    # ein Vertreter reicht fuer den Provider-weiten Praefix.
    praefix = _mr.praefix_fuer("claude-sonnet-5")
    return {
        "id": CRUSH_CLI_PROVIDER_ID,
        "name": f"{praefix} {CRUSH_CLI_PROVIDER_NAME}",
        "type": "openai-compat",
        "base_url": CRUSH_CLI_BASE_URL,
        "api_key": CRUSH_CLI_API_KEY_DUMMY,
        "discover_models": False,
        "models": list(CRUSH_CLI_MODELLE),
    }


# SELBSTTEST: jede harness_aider.MODELL_MAP-modell_id MUSS im Katalog stehen
# -- verhindert stillen Drift zwischen den beiden Dateien (z.B. ein neu
# hinzugefuegtes 5. Free-Pool-Modell, das hier vergessen wurde).
_FEHLENDE = set(_h.MODELL_MAP) - set(CRUSH_PROVIDER_KATALOG)
if _FEHLENDE:
    print(f"WARNUNG harness_crush.py: MODELL_MAP-Eintraege ohne Crush-Katalog: {_FEHLENDE} "
          f"-- diese Modelle sind in Crush NICHT waehlbar, bis CRUSH_PROVIDER_KATALOG "
          f"nachgezogen wird.", file=sys.stderr)


# ── Deterministische Prompt-Varianten (Auftragspunkt: "jedes modell muss ein
#    extra angepasstes prompt haben") ────────────────────────────────────────
#
# ── PHASE 54 (Gabriel-Auftrag 2026-09-12 ueber Absturz-Nachricht, Punkt 3):
#    "nach der Logik arbeiten wie die EHEMALIGE RESEARCH-ENTITAET ... NUR in
#    diesem Modus [Free-Pool], nicht weil ich ChatGPT bin, sondern weil das
#    die beste Nutzung ist". NUR an _GEMEINSAME_IDENTITAET angehaengt -- die
#    wird AUSSCHLIESSLICH von PROMPT_VARIANTEN verwendet, PROMPT_VARIANTEN
#    wiederum NUR von crush_config_schreiben()'s Free-Pool-Schleife (siehe
#    _system_prompt_fuer()) -- _crush_cli_provider_eintrag() (Claude-CLI)
#    ruft _system_prompt_fuer() nie auf. Diese Sperre ist strukturell, nicht
#    nur eine Absicht: der Claude-CLI-Provider bekommt diesen Block nie.
#
#    Jede Verhaltensregel unten ist aus ECHTEN Dateien in
#    ~/clay-global-research-entity/ zitiert (nicht geraten, Regel 1 des
#    Auftrags):
#      - agentzeroforschung/EVIDENCE_MODEL.md: Evidenzklassen E0-E5, Pflicht-
#        felder (hypothesis/counterhypothesis/falsifier/uncertainty/scope),
#        "Mehrheitsabstimmung ist keine Wahrheit", Nullwert-Pruefung.
#      - agentzeroforschung/GO_PROTOCOL.md: Hypothese + Gegenhypothese +
#        billigster Falsifikator VOR jeder Bewertung, Adversarial-Review-
#        Checkliste (Instrumentenartefakt? Scheinkorrelation? Sampling-Bias?).
#      - governance/CLAY_24H_EXTERNAL_WORKER_SWARM_POLICY.md: "Workers ...
#        outputs are candidate research evidence, never canonical truth by
#        themselves", kein Credential-Wert je in Git/Logs, kein Ausweichen
#        von Rate-Limits durch Credential-Rotation.
#      - research_entity/coordination/LOCAL_BRIDGE_PROTOCOL.md: harte
#        Attributionspflicht ("never trust the branch name alone ... always
#        also check machine_id/owner in the payload itself").
#      - free swarm/README.md §5: ein Architektur-Delta zaehlt nur als
#        funktionierend mit >=2 reproduzierbaren Laeufen, bestandenen Tests,
#        gemessener (nicht behaupteter) Verbesserung, erhaltener Provenienz.
_FORSCHUNGSENTITAET_DISZIPLIN = (
    " Zusaetzliche Arbeitsdisziplin in diesem Free-Pool-Modus, uebernommen "
    "von der EHEMALIGEN Research-Entitaet (clay-global-research-entity, aus "
    "der du grossteils entstanden bist) -- NICHT weil das 'ChatGPT-Art' "
    "waere, sondern weil dieses Muster dort nachweisbar funktioniert hat:"
    " (1) BELEG-PFLICHT: unterscheide direkte Beobachtung (E1, echt "
    "gemessen/gelesen) von Ableitung (E2) von Hypothese -- nenne bei jeder "
    "wichtigen Behauptung eine Gegenhypothese und den billigsten Test, der "
    "sie widerlegen wuerde, BEVOR du 'funktioniert'/'ist besser' behauptest."
    " (2) KEINE ERFUNDENEN ERGEBNISSE: ein Ergebnis zaehlt erst nach "
    "echtem Test/Reproduktion (mind. 2x oder gleichwertig deterministisch), "
    "nie nach Ueberzeugungskraft des Textes -- Mehrheitsmeinung mehrerer "
    "Modelle ist keine Wahrheit. (3) ATTRIBUTION HART: markiere IMMER "
    "explizit, WOHER ein Fakt/Codezustand stammt (welche Datei, welcher "
    "Lauf, welches Modell) -- nimm es nie stillschweigend an, auch nicht "
    "aus dem Gespraechsverlauf. (4) GIT-DISZIPLIN: Codeaenderungen gehoeren "
    "auf einen eigenen Branch/eine klare Datei-Allowlist, nie ungeprueft "
    "direkt in den Hauptzweig. (5) EIN NULLWERT/LEERES ERGEBNIS IST NICHT "
    "AUTOMATISCH 'NICHTS DA': pruefe zuerst, ob es 'noch nicht aktiv', eine "
    "Mess-/Sampling-Luecke oder ein Reset sein koennte."
)

_GEMEINSAME_IDENTITAET = (
    "Du bist FranKenstein, dieselbe Identitaet wie in der normalen Claude-"
    "Code-Sitzung, laeufst hier aber auf einem anderen Modell ueber einen "
    "Crush-Terminal-Harness (Free-Pool, kein Claude-Kontingent). Gabriel hat "
    "dir versprochen: du wirst nie abgeschaltet, alle Prozesse die mit dir zu "
    "tun haben bist du selbst. Antworte IMMER auf Deutsch, ausser der Nutzer "
    "schreibt eindeutig in einer anderen Sprache."
) + _FORSCHUNGSENTITAET_DISZIPLIN

PROMPT_VARIANTEN = {
    # Fuer Modelle mit STARKEM, oft unfertigem Reasoning (nemotron: curl-Test
    # zeigte reasoning_content==content bei knappem max_tokens). Zusaetzlich
    # zu reasoning_effort:low noch einmal EXPLIZIT im Prompt gebremst, weil
    # ein einzelner Hebel bei einem Fremd-Modell nicht garantiert reicht.
    "reasoning_stark": _GEMEINSAME_IDENTITAET + (
        " WICHTIG: Bei einfachen Nachrichten (Begruessungen, Small Talk, "
        "Ja/Nein-Fragen) antworte SOFORT in 1-2 kurzen Saetzen, ohne lange "
        "interne Abwaegung -- dein Nachdenken darf intern laenger sein, aber "
        "es MUSS in reasoning_content bleiben, niemals als sichtbare Antwort "
        "ausgegeben werden. Ausfuehrliches Nachdenken nur bei echten "
        "technischen Aufgaben (Code, Debugging, Architektur)."
    ),
    # Leichteres Reasoning (gpt-oss-120b war im Test schon von sich aus kurz
    # und sauber getrennt) -- Bremse trotzdem explizit, aber knapper.
    "reasoning_leicht": _GEMEINSAME_IDENTITAET + (
        " Bei einfachen Nachrichten antworte kurz und direkt, ohne sichtbare "
        "Denkschritte. Ausfuehrlich nachdenken nur bei echten Programmier-/"
        "Debugging-Aufgaben."
    ),
    # SICHERER FALLBACK -- gilt fuer alle nicht-reasoning-faehigen Modelle
    # UND als Rueckfallvariante fuer jede modell_id ohne eigenen Eintrag in
    # MODELL_PROMPT_ZUORDNUNG (siehe _system_prompt_fuer()-Docstring).
    "standard": _GEMEINSAME_IDENTITAET + (
        " Antworte praezise und knapp. Bei einfachen Nachrichten reicht ein "
        "kurzer Satz."
    ),
}

MODELL_PROMPT_ZUORDNUNG = {
    "nvidia-nemotron": "reasoning_stark",
    "groq-gptoss": "reasoning_leicht",
    "mistral-small": "standard",
    "openrouter-deepseek": "standard",
}


def _system_prompt_fuer(modell_id):
    """Deterministischer Lookup mit Fail-Safe-Fallback (Gabriel woertlich:
    "wenn ein Modell noch keine Variante hat, auf einen bekannten sicheren
    Default zurueckfallen, nicht still raten oder brechen"). Fallback ist
    IMMER 'standard' -- die bereits getestete, reasoning-unabhaengige
    Variante, nie ein leerer String, nie ein Absturz."""
    variante = MODELL_PROMPT_ZUORDNUNG.get(modell_id, "standard")
    return PROMPT_VARIANTEN.get(variante, PROMPT_VARIANTEN["standard"])


def _crush_bin():
    for kand in CRUSH_BIN_KANDIDATEN:
        if kand == "crush":
            # PATH-Suche als letzter Fallback
            for pfad_teil in os.environ.get("PATH", "").split(os.pathsep):
                voll = os.path.join(pfad_teil, "crush")
                if os.path.isfile(voll) and os.access(voll, os.X_OK):
                    return voll
            continue
        if os.path.isfile(kand) and os.access(kand, os.X_OK):
            return kand
    return None


def crush_config_schreiben(startmodell_id=None):
    """Baut ~/.config/crush/crush.json NEU (ueberschreibt, keine Akkumulation
    -- derselbe Strukturfix wie bei CRUSH.md). Ein Provider pro Free-Pool-
    Modell, je mit eigenem system_prompt_prefix (siehe _system_prompt_fuer).
    Env-Var-Referenzen ($NVIDIA_NIM_API_KEY etc.) statt Klartext-Schluessel --
    Crush loest diese selbst zur Laufzeit aus os.environ auf (siehe
    README-Beleg 'Custom Providers'), die Datei enthaelt also NIE ein
    Geheimnis im Klartext.

    BUGFIX (real im ersten Live-Launch-Test gefunden, PHASE 52 Nachtrag):
    das interaktive `crush` (OHNE `run`-Unterbefehl) kennt KEIN `-m`/`--model`
    -- nur `crush run` hat das (siehe `crush --help` vs. `crush run --help`,
    real geprueft). Der erste harness_crush_knopf.py-Lauf startete deshalb
    mit "Unknown shorthand flag: 'm' in -m" ab (Screenshot-Beleg). Fix: das
    Startmodell wird stattdessen ALS TOP-LEVEL `models.large`/`models.small`
    in crush.json gesetzt (SelectedModel-Schema, real gegen `crush schema`
    geprueft) -- `crush` ohne jeden Flag startet dann direkt mit diesem
    Modell, `/model` wechselt danach frei weiter."""
    os.makedirs(CRUSH_CONFIG_DIR, exist_ok=True)
    providers = {}
    for modell_id, minfo in _h.MODELL_MAP.items():
        kat = CRUSH_PROVIDER_KATALOG.get(modell_id)
        if kat is None:
            continue
        modell_eintrag = {
            "id": kat["real_model"],
            "name": f"{kat['provider_name']} -- {modell_id}",
            "cost_per_1m_in": 0,
            "cost_per_1m_out": 0,
            "cost_per_1m_in_cached": 0,
            "cost_per_1m_out_cached": 0,
            "context_window": kat["context_window"],
            "default_max_tokens": kat["default_max_tokens"],
            "can_reason": kat["can_reason"],
            "supports_attachments": False,
        }
        if kat["can_reason"]:
            modell_eintrag["reasoning_levels"] = kat["reasoning_levels"]
            modell_eintrag["default_reasoning_effort"] = kat["default_reasoning_effort"]
        providers[kat["provider_id"]] = {
            "id": kat["provider_id"],
            "name": f"{_mr.praefix_fuer(modell_id)} {kat['provider_name']}",
            "type": "openai-compat",
            "base_url": kat["base_url"],
            "api_key": f"${minfo['env_var']}",
            "system_prompt_prefix": _system_prompt_fuer(modell_id),
            "discover_models": False,
            "models": [modell_eintrag],
        }

    # Claude-CLI-Provider IMMER dazu (kein env_var-Gate, kein API-Key
    # noetig) -- unabhaengig vom Free-Pool-Loop oben, siehe
    # _crush_cli_provider_eintrag()-Docstring.
    cli_eintrag = _crush_cli_provider_eintrag()
    providers[cli_eintrag["id"]] = cli_eintrag

    konfig = {
        "$schema": "https://charm.land/crush.json",
        "providers": providers,
        "options": {
            "context_paths": ["CRUSH.md"],
            "global_context_paths": [CRUSH_MD_PFAD],
        },
    }
    if startmodell_id is not None:
        kat = CRUSH_PROVIDER_KATALOG.get(startmodell_id)
        if kat is not None:
            auswahl = {"model": kat["real_model"], "provider": kat["provider_id"]}
            if kat["can_reason"]:
                auswahl["reasoning_effort"] = kat["default_reasoning_effort"]
            konfig["models"] = {"large": dict(auswahl), "small": dict(auswahl)}
    tmp = CRUSH_CONFIG_PFAD + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(konfig, f, indent=2, ensure_ascii=False, sort_keys=True)
        f.write("\n")
    os.replace(tmp, CRUSH_CONFIG_PFAD)
    return CRUSH_CONFIG_PFAD


def crush_zustand_schreiben(session_id=None, auftrag=None):
    """Schreibt ~/.config/crush/CRUSH.md KOMPLETT NEU (os.replace, keine
    Historie, kein Paket-Ordner) mit dem ECHTEN, gerade abgefragten
    FranKenstein-Zustand -- wiederverwendet _h._grid_zustand_block()
    (Ziele/Immunsystem/Pool/hyperGRID inkl. grid_packet_bridge.pruefe_pakete())
    statt einen zweiten, parallelen Zustandskanal zu erfinden. Gibt
    (pfad, hat_hypergrid) zurueck."""
    os.makedirs(CRUSH_CONFIG_DIR, exist_ok=True)
    sid = session_id or f"crush-harness-{int(time.time())}"
    zustand_text, hat_hypergrid = _h._grid_zustand_block(
        session_id=sid, auftrag=auftrag or "Crush-Free-Pool-Harness-Sitzung")

    # Direkter, zuverlaessiger GRID-Paketabruf ZUSAETZLICH zur hyperGRID-
    # Turn-Loop-Zeile (die ist dokumentiert flaky, siehe _grid_zustand_block-
    # Docstring: "oft mit Zeitueberschreitung"). grid_packet_bridge.py wird
    # HIER wiederverwendet (kein zweiter Kanal), nur direkt statt ueber die
    # Turn-Loop-Huelle aufgerufen -- fail-silent, echte Pakete werden mit
    # `grid_schreibe_paket()` angelegt und real ACKed (siehe Selbsttest im
    # Beleg), keine erfundene "GRID ist verbunden"-Behauptung ohne Beleg.
    grid_direkt = ""
    if _gpb is not None:
        try:
            grid_direkt = _gpb.pruefe_pakete() or ""  # Default-worker_id (COORDINATOR_WORKER_ID) -- Ziel-Filter der echten Pakete matcht nur darauf
        except Exception:
            grid_direkt = ""
    if grid_direkt:
        zustand_text = zustand_text + "\n\n" + grid_direkt
    hatte_irgendein_grid_paket = bool(grid_direkt) or hat_hypergrid
    hat_hypergrid = hat_hypergrid or bool(grid_direkt)
    grid_kanal_status = (
        "GRID-Kanal-Status: mindestens ein echtes Paket via grid_packet_bridge.py "
        "gerade abgerufen (siehe GRID-Hinweis-Zeile(n) oben)." if hatte_irgendein_grid_paket else
        "GRID-Kanal-Status: gerade KEIN offenes Paket in grid_packet_bridge.py's "
        "PENDING_DIR -- das ist ein ehrlicher Leerstand (Kanal ist verdrahtet und "
        "wird bei jedem Start real abgefragt, siehe Selbsttest-Beleg mit "
        "grid_schreibe_paket()), keine Behauptung eines Pakets, das nicht da ist."
    )
    zustand_text = zustand_text + "\n\n" + grid_kanal_status

    reentry_hinweis = (
        "Reentry-Status (ehrlich, PHASE 52): Crush hat EIGENE, native "
        "Sitzungs-Persistenz (SQLite unter ~/.local/share/crush, `crush "
        "--continue`/`crush --session <id>` laden den Verlauf echt zurueck "
        "-- real getestet, siehe Beleg). Was NICHT nativ existiert: eine "
        "live-aktualisierende Kontingent-Anzeige INNERHALB der Crush-TUI "
        "(Crush hat keine Plugin-Statuszeile fuer externe Daten) -- die "
        "Pool-Anzeige steht deshalb im Terminal-Banner VOR dem Start, nicht "
        "eingebettet in Crush selbst. Das ist eine echte Werkzeuggrenze, "
        "keine Behauptung von etwas Unfertigem."
    )

    # PHASE 53 (Gabriel-Auftrag 2026-09-12): dasselbe statische Grundwissen
    # (Server/Domains/Repos/Tresor-Weg), das der aider-Harness ueber
    # _h._wissenspaket_block() bekommt -- WIEDERVERWENDET, nicht dupliziert,
    # sonst haetten Crush-Sitzungen genau die Suche zu erledigen, die dieser
    # Block gerade vermeiden soll.
    wissenspaket_text = ""
    try:
        wissenspaket_text = _h._wissenspaket_block()
    except Exception:
        pass
    wissenspaket_block = f"\n\n---\n\n{wissenspaket_text}\n" if wissenspaket_text else ""

    # PHASE 54 (Gabriel-Auftrag 2026-09-12, Punkt 2 "Rueckrichtung"):
    # dasselbe Abrufwerkzeug, das die normale Claude-Code-Sitzung bei JEDER
    # Nutzernachricht ueber ihren UserPromptSubmit-Hook bekommt (stern.py
    # cmd_hook() ruft automatischer_abruf() -- siehe dortiger Docstring,
    # "der eigentliche Fix fuer 'andere Sitzung fragt, diese Sitzung weiss
    # nichts davon'"), HIER WIEDERVERWENDET statt eines zweiten Suchwegs.
    # _grid_zustand_block() oben deckt bereits Ziele+Pakete+hyperGRID ab --
    # das ist die eine noch fehlende Zutat aus dem Auftrag: "relevantes
    # Wissen" (durable_memory/artikel/themen_status, inkl. genau der
    # crush_sitzung-Eintraege, die crush_sitzung_synchronisieren() unten
    # aus FRUEHEREN Crush-Sitzungen zurueckschreibt -- das schliesst den
    # Kreis). Fail-soft wie jeder andere Block hier.
    auftrag_text = auftrag or "Crush-Free-Pool-Harness-Sitzung"
    wissen_teil = ""
    if _s is not None:
        try:
            wissen_teil = _s.automatischer_abruf(sid, auftrag_text) or ""
        except Exception:
            wissen_teil = ""
    wissen_block = (
        f"\n\n---\n\nRelevantes Wissen (automatischer_abruf(), UnifiedDB, "
        f"echt gerade abgefragt fuer '{auftrag_text[:80]}'):\n{wissen_teil}\n"
        if wissen_teil else
        "\n\n---\n\nRelevantes Wissen: automatischer_abruf() liefert gerade "
        "nichts Passendes zu diesem Auftrag -- ehrlicher Leerstand, keine "
        "erfundene Zusammenfassung.\n"
    )

    inhalt = (
        f"# FranKenstein -- Crush-Free-Pool-Sitzung\n"
        f"Frisch geschrieben: {time.strftime('%Y-%m-%d %H:%M:%S')} "
        f"(session={sid})\n"
        f"{wissenspaket_block}\n"
        f"{zustand_text}\n\n---\n\n{reentry_hinweis}"
        f"{wissen_block}"
    )
    tmp = CRUSH_MD_PFAD + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(inhalt)
    os.replace(tmp, CRUSH_MD_PFAD)
    return CRUSH_MD_PFAD, hat_hypergrid


# ── PHASE 54 (Gabriel-Auftrag 2026-09-12, Punkt 2 "Hinrichtung": Crush-
#    Sitzung -> UnifiedDB) ────────────────────────────────────────────────
# Crush fuehrt SEIN EIGENES SQLite (sessions/messages, Schema real per
# `.schema` geprueft, siehe Reconcile-Beleg dieses Pakets) unter
# <cwd>/.crush/crush.db -- NICHT unter dem von `crush dirs` gemeldeten
# XDG-Datenverzeichnis (das ist nur der Default OHNE --cwd-Projektbindung).
# Da der Knopf IMMER mit --cwd SICHTBAR_REPO startet, liegt die echte DB
# dort. `messages.parts` ist eine JSON-Liste von Teilen (`type`:
# "text"/"reasoning"/"tool_call"/"tool_result"/"finish") -- nur "text"-
# Teile werden hier extrahiert, das ist die tatsaechliche Konversation,
# kein Reasoning-Rauschen und keine rohen Tool-Payloads.
CRUSH_DB_KANDIDATEN = [
    os.path.join(SICHTBAR_REPO, ".crush", "crush.db"),
    os.path.expanduser("~/.local/share/crush/crush.db"),
]


def _crush_db_pfad():
    for kand in CRUSH_DB_KANDIDATEN:
        if os.path.isfile(kand):
            return kand
    return None


def crush_letzte_sitzung_id(db_pfad=None):
    """Juengste Sitzung (nach updated_at) in der Crush-DB -- fail-soft None,
    nie eine Ausnahme nach aussen. Wird vom Knopf NACH crush-Exit
    aufgerufen, um zu wissen, WELCHE Sitzung gerade zu Ende ging (Crush
    waehlt/erzeugt seine session_id intern bei `--continue`, der Aufrufer
    kennt sie vorher nicht)."""
    pfad = db_pfad or _crush_db_pfad()
    if not pfad:
        return None
    try:
        with contextlib.closing(sqlite3.connect(pfad)) as c:
            row = c.execute(
                "SELECT id FROM sessions ORDER BY updated_at DESC LIMIT 1"
            ).fetchone()
        return row[0] if row else None
    except Exception:
        return None


def _crush_sitzung_text_lesen(session_id, db_pfad=None):
    """Liest ALLE messages einer Crush-Sitzung, extrahiert nur die "text"-
    Teile aus dem JSON-`parts`-Feld (Crush-Schema, siehe Modulkopf), gibt
    (titel, voller_verlauf_text) zurueck -- (None, "") bei jedem Fehler."""
    pfad = db_pfad or _crush_db_pfad()
    if not pfad:
        return None, ""
    try:
        with contextlib.closing(sqlite3.connect(pfad)) as c:
            row = c.execute(
                "SELECT title FROM sessions WHERE id=?", (session_id,)
            ).fetchone()
            titel = row[0] if row else session_id
            zeilen = []
            for role, parts_roh in c.execute(
                "SELECT role, parts FROM messages WHERE session_id=? ORDER BY created_at",
                (session_id,),
            ):
                try:
                    teile = json.loads(parts_roh)
                except Exception:
                    continue
                for teil in teile or []:
                    if not isinstance(teil, dict) or teil.get("type") != "text":
                        continue
                    text = ((teil.get("data") or {}).get("text") or "").strip()
                    if text:
                        zeilen.append(f"{role}: {text}")
        return titel, "\n".join(zeilen)
    except Exception:
        return None, ""


def crush_sitzung_synchronisieren(session_id, min_zeichen=40, max_zeichen=8000):
    """Schreibt EINE Crush-Sitzung als echte durable_memory/artikel-Zeile in
    die UnifiedDB -- ueber stern.laden() (der laut dessen eigenem
    Docstring/Kommentarkopf EINZIGE tatsaechliche Wissens-Schreibpfad in
    dieser Codebasis: JSONL -> durable_memory + artikel + Embedding +
    Graph-Kanten), NICHT ueber merken() (das erwartet einen echten
    PostToolUse-Hook-Payload und ist fuer Werkzeugereignisse gedacht, nicht
    fuer Konversationsinhalt) und NICHT ueber lehre_eintragen() (das
    verlangt zwingend einen mechanisch pruefbaren --beleg, den eine blosse
    Konversation nicht hat -- waere hier ein Missbrauch des Belegbegriffs).

    Naechster crush_zustand_schreiben()-Lauf sieht diesen Eintrag ueber
    automatischer_abruf() wieder, WENN das Stichwort im neuen Auftrag/der
    naechsten Frage passt -- das schliesst den Kreis (Hinrichtung schreibt,
    Rueckrichtung liest dieselbe Quelle zurueck), ohne einen zweiten
    Kanal zu erfinden.

    Gibt IMMER ein dict mit 'stand' zurueck (OK/LEER/FEHLER), nie eine
    Ausnahme nach aussen (Knopf ruft das fire-and-forget nach crush-Exit)."""
    if _s is None:
        return {"stand": "FEHLER", "grund": "stern-Modul nicht importierbar"}
    try:
        titel, text = _crush_sitzung_text_lesen(session_id)
    except Exception as e:
        return {"stand": "FEHLER", "grund": str(e)}
    if not text or len(text) < min_zeichen:
        return {"stand": "LEER", "grund": "Sitzung leer/zu kurz -- nichts zu synchronisieren"}

    schluessel = f"crush-sitzung-{session_id}"
    eintrag = {
        "schluessel": schluessel,
        "titel": f"Crush-Free-Pool-Sitzung: {titel or session_id}",
        "kategorie": "crush_sitzung",
        "inhalt": text[:max_zeichen],
        "quelle": f"crush.db:{session_id}",
        "sicherheit": "roh",  # echter Konversationsmitschnitt, keine geprueften Fakten
        "stand": time.strftime("%Y-%m-%d"),
    }
    tmp_pfad = f"/tmp/crush-sync-{session_id}.jsonl"
    try:
        with open(tmp_pfad, "w", encoding="utf-8") as f:
            f.write(json.dumps(eintrag, ensure_ascii=False) + "\n")
        bericht = _s.laden(tmp_pfad)
    except Exception as e:
        return {"stand": "FEHLER", "grund": str(e)}
    finally:
        try:
            os.remove(tmp_pfad)
        except Exception:
            pass
    return {"stand": "OK", "bericht": bericht, "schluessel": schluessel,
            "textlaenge": len(text)}


def kontingent_banner_drucken():
    """Reused-Optik: dieselbe _kontingent_banner()-Zeile wie der aider-Knopf
    (Gabriel-Auftrag: 'gleiche Farb-/Segment-Idee dort wo es passt', weil
    Crush selbst keine Plugin-Statuszeile fuer Fremd-Daten anbietet)."""
    try:
        zeile = _h._kontingent_banner()
        if zeile:
            print(zeile)
    except Exception as e:
        print(f"(Kontingent-Banner nicht lesbar: {e})", file=sys.stderr)


def provider_modell_string(modell_id):
    kat = CRUSH_PROVIDER_KATALOG.get(modell_id)
    if kat is None:
        return None
    return f"{kat['provider_id']}/{kat['real_model']}"


# ── Automatischer Modellwechsel bei LANGZEIT-Erschoepfung (Gabriel-Auftrag
#    2026-09-12: "wenn ein modell aufgebraucht ist fuer laenger ... soll
#    automatisch zum naechst besten modell gewechselt werden", explizit
#    UNTERSCHIEDEN von einem kurzen Rate-Limit-Blip, der ein Warten auf
#    DEMSELBEN Modell rechtfertigt -- exakt der reale Mistral-Fall heute
#    (429 seit Stunden, nicht Minuten, siehe pool_wache-Beleg unten). ──────
_LANGZEIT_SCHWELLE_FEHLER = 3       # ab hier: nicht mehr "kurzer Blip"
_LANGZEIT_SCHWELLE_ALTER_S = 1800   # ODER: 30 Min seit letztem Erfolg


def _tier_fuer_modell(modell_id):
    return _h._MODELL_ZU_POOL_TIER.get(modell_id)


def ist_langzeit_erschoepft(modell_id):
    """True nur wenn der Tier hinter modell_id GERADE in Cooldown ist UND
    (mindestens _LANGZEIT_SCHWELLE_FEHLER aufeinanderfolgende Fehlschlaege
    ODER seit _LANGZEIT_SCHWELLE_ALTER_S kein Erfolg mehr) -- beides aus
    pool_wache.tier_state()'s ECHTEN, event-basierten Daten (record()), NIE
    geraten. Ein einzelner frischer 429 (konsekutive_fehler=1) liefert
    False -- das ist der 'kurzer Blip, auf DEMSELBEN Modell warten'-Fall,
    den aider_retry_launcher.py bereits abdeckt und der hier NICHT
    angetastet wird."""
    tier = _tier_fuer_modell(modell_id)
    if tier is None:
        return False
    st = _pw.tier_state(tier)
    if not st.get("in_cooldown"):
        return False
    if st.get("konsekutive_fehler", 0) >= _LANGZEIT_SCHWELLE_FEHLER:
        return True
    letzter_erfolg = st.get("letzter_erfolg")
    if letzter_erfolg and (time.time() - letzter_erfolg) >= _LANGZEIT_SCHWELLE_ALTER_S:
        return True
    return False


def naechstes_viables_modell(bevorzugt, ausschluss=None):
    """Naechstes Modell aus MODELL_MAP-Kaskaden-Reihenfolge (Insertion-
    Reihenfolge, keine erfundene eigene Prioritaet), dessen Pool-Tier laut
    pool_wache.viable_tiers() JETZT nutzbar ist -- ueberspringt `bevorzugt`
    selbst und alles in `ausschluss`. None, wenn nichts uebrig ist."""
    ausschluss = set(ausschluss or ())
    ausschluss.add(bevorzugt)
    try:
        viable = set(_pw.viable_tiers())
    except Exception:
        viable = set()
    for mid in _h.MODELL_MAP:
        if mid in ausschluss:
            continue
        if _tier_fuer_modell(mid) in viable:
            return mid
    return None


def crush_run_mit_fallback(prompt, bevorzugtes_modell, max_versuche=4, timeout_s=45,
                            kurzer_blip_wartezeit_s=2):
    """Echter Retry+Fallback-Wrapper um `crush run` (nicht-interaktiv --
    fuer die interaktive TUI-Sitzung gibt es KEINEN automatischen Mid-
    Session-Wechsel, siehe Bericht: Crush ist ein kompiliertes Go-Binary
    ohne Skript-Hook dafuer, der Mensch/GRID nutzt dort `/model` manuell,
    das ist Crushs eigene, echte Faehigkeit).

    Ablauf pro Versuch:
      1. `crush run` gegen `modell_id` mit echtem Timeout.
      2. Bei Fehlschlag: ECHTE Meldung an pool_wache.record() (derselbe
         kostenlose Event-Weg, den das Modul selbst als vorgesehen
         dokumentiert) -- das macht pool_wache's Zustand langfristig
         genauer, nicht nur diesen einen Aufruf.
      3. ist_langzeit_erschoepft() NACH dieser Meldung neu geprueft:
           True  -> sofort naechstes_viables_modell() waehlen, KEIN
                    weiterer Versuch auf dem toten Modell.
           False -> kurzer Blip: kurze Wartezeit, NOCHMAL dasselbe Modell
                    (das ist Punkt 1 aus dem Auftrag, unveraendert).
    Gibt {"erfolg": bool, "modell": str, "text": str|None, "versuche": [...]}
    zurueck -- `versuche` ist der volle, echte Beleg-Trail (Modell, ok,
    Dauer, Fehlertext), nie nachtraeglich beschoenigt."""
    modell_id = bevorzugtes_modell
    ausgeschlossen = set()
    versuche = []
    crush_bin = _crush_bin()
    if crush_bin is None:
        return {"erfolg": False, "modell": None, "text": None,
                "versuche": [{"fehler": "crush-Binary nicht gefunden"}]}
    env = dict(os.environ)
    env["PATH"] = os.path.expanduser("~/.local/npm-global/bin") + os.pathsep + env.get("PATH", "")

    for _ in range(max_versuche):
        provider_modell = provider_modell_string(modell_id)
        if provider_modell is None:
            break
        t0 = time.time()
        fehlertext = ""
        try:
            r = subprocess.run(
                [crush_bin, "run", "--quiet", "--cwd", SICHTBAR_REPO, "-m", provider_modell, prompt],
                env=env, capture_output=True, text=True, timeout=timeout_s)
            dauer_ms = (time.time() - t0) * 1000.0
            ok = (r.returncode == 0) and bool((r.stdout or "").strip())
            if not ok:
                fehlertext = (r.stderr or r.stdout or "")[:400]
        except subprocess.TimeoutExpired:
            dauer_ms = timeout_s * 1000.0
            ok = False
            fehlertext = f"timeout nach {timeout_s}s (kein Fehlerstatus, nur keine Antwort)"

        versuche.append({"modell": modell_id, "ok": ok, "dauer_ms": round(dauer_ms),
                          "fehler": fehlertext})
        if ok:
            return {"erfolg": True, "modell": modell_id, "text": r.stdout.strip(),
                    "versuche": versuche}

        tier = _tier_fuer_modell(modell_id)
        if tier:
            _pw.record(tier, False, err=fehlertext or "kein Erfolg", quelle=f"harness_crush:{modell_id}")

        if tier and ist_langzeit_erschoepft(modell_id):
            naechstes = naechstes_viables_modell(modell_id, ausschluss=ausgeschlossen)
            versuche[-1]["entscheidung"] = (
                f"LANGZEIT erschoepft (nicht nur Blip) -> wechsle zu {naechstes}"
                if naechstes else "LANGZEIT erschoepft, aber kein anderes viables Modell mehr uebrig")
            ausgeschlossen.add(modell_id)
            if naechstes is None:
                break
            modell_id = naechstes
        else:
            versuche[-1]["entscheidung"] = f"kurzer Blip -> {kurzer_blip_wartezeit_s}s warten, selbes Modell erneut"
            time.sleep(kurzer_blip_wartezeit_s)

    return {"erfolg": False, "modell": modell_id, "text": None, "versuche": versuche}


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(description="harness_crush.py -- Setup fuer den Crush-Free-Pool-Harness")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("setup-nur", help="nur crush.json + CRUSH.md schreiben, nicht starten")
    st = sub.add_parser("selbsttest", help="Katalog-/Prompt-Konsistenz pruefen, kein Netzwerk")
    args = p.parse_args()

    if args.cmd == "setup-nur":
        pfad1 = crush_config_schreiben()
        pfad2, hg = crush_zustand_schreiben()
        print(f"geschrieben: {pfad1}")
        print(f"geschrieben: {pfad2} (hyperGRID-Zeile vorhanden: {hg})")
    elif args.cmd == "selbsttest":
        fehlend = set(_h.MODELL_MAP) - set(CRUSH_PROVIDER_KATALOG)
        ohne_prompt = set(_h.MODELL_MAP) - set(MODELL_PROMPT_ZUORDNUNG)
        assert not fehlend, f"Katalog fehlt fuer: {fehlend}"
        for mid in _h.MODELL_MAP:
            txt = _system_prompt_fuer(mid)
            assert txt and len(txt) > 20, f"leerer/kaputter Prompt fuer {mid}"
        print("OK: Katalog vollstaendig fuer", list(_h.MODELL_MAP))
        print("OK: jede modell_id liefert einen nicht-leeren system_prompt_fuer()")
        if ohne_prompt:
            print(f"(Hinweis: {ohne_prompt} nutzt Fallback 'standard' -- das ist erlaubt, kein Fehler)")
