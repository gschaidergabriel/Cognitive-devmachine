"""PreToolUse-Zaun fuer Zero -- der duenne Schutz um das Unersetzliche.

Gabriel 19.08.: Zero bekommt native Werkzeuge (Bash, Read/Write/Edit, Web, ...)
und handelt DIREKT wie eine normale Claude-Code-Sitzung. EINZIGE Ausnahme
(Gabriels Wahl "duenner Zaun"): das Unersetzliche darf nicht zerstoert und
Passwort-/Schluesselmaterial nicht ausgelesen werden. Alles andere laeuft frei.

Dies ist bewusst ein DUENNER Zaun gegen Versehen und beilaeufige Prompt-Injection
aus gelesenen Inhalten -- keine gehaertete Sandbox. Er blockt die direkten
Wege; ein entschlossener Umweg (eigenes Python-Skript o.ae.) ist nicht das
Bedrohungsmodell hier (nur 2 vertraute Menschen haben Zugang).

Vertrag: liest das PreToolUse-Payload von stdin ({tool_name, tool_input}).
Blockt mit permissionDecision=deny; sonst kein Output = durchlassen.
"""
import json
import re
import sys

# Unersetzlich -- Kontinuitaet/Identitaet der Entitaet. Nie loeschen/ueberschreiben.
UNERSETZLICH = (
    "/var/lib/clay",         # wiki.db -- das Herz
    "/opt/unifieddb",        # UnifiedDB
    "/var/lib/clayverse",    # Laufzeitzustand
    "/etc/entityos/tresor",  # Tresor (deckt tresor.key mit)
)
# Geheim -- Passwort-/Schluesselmaterial. Nie lesen/ausgeben.
GEHEIM = (
    "/etc/entityos/tresor",
    "/etc/entityos/tresor.key",
    "/etc/clayverse/freie-zugaenge.env",
    "/etc/entityos/postfach.env",
)
GEHEIM_NAME = re.compile(
    r"(freie-zugaenge\.env|postfach\.env|tresor\.key|secret\.key|\.tresor\b|/tresor\b|\.credentials\b)")
# Zerstoerende Shell-Verben (cp/mv bewusst NICHT hier -- Backups muessen erlaubt bleiben).
ZERSTOER = re.compile(r"(?:^|[;&|]|\s)(rm|rmdir|shred|unlink|truncate|dd|mkfs)\b")
# Lese-Verben, mit denen sich ein Geheimnis ausgeben liesse.
LESE = re.compile(
    r"(?:^|[;&|]|\s)(cat|less|more|head|tail|strings|xxd|od|hexdump|base64|grep|egrep|"
    r"nl|tac|awk|sed|cut|printenv|env)\b|\$\(<")


def _trifft(text, pfade):
    return any(p in text for p in pfade)


def deny(grund):
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "deny",
        "permissionDecisionReason": grund,
    }}))
    sys.exit(0)


def main():
    try:
        payload = json.load(sys.stdin)
    except Exception:
        sys.exit(0)   # kein lesbares Payload -> nicht blockieren
    tool = payload.get("tool_name", "")
    ti = payload.get("tool_input", {}) or {}

    if tool in ("Write", "Edit", "MultiEdit", "NotebookEdit"):
        pfad = str(ti.get("file_path") or ti.get("notebook_path") or "")
        if _trifft(pfad, UNERSETZLICH) or GEHEIM_NAME.search(pfad):
            deny("Zaun: das Unersetzliche/Geheime wird nicht ueberschrieben (" + pfad + ").")

    elif tool == "Read":
        pfad = str(ti.get("file_path") or "")
        if _trifft(pfad, GEHEIM) or GEHEIM_NAME.search(pfad):
            deny("Zaun: Passwort-/Schluesseldatei wird nicht gelesen (" + pfad + ").")

    elif tool == "Bash":
        cmd = str(ti.get("command") or "")
        # (a) Geheimnis auslesen?
        if GEHEIM_NAME.search(cmd) and LESE.search(cmd):
            deny("Zaun: kein Auslesen von Passwort-/Schluesselmaterial.")
        # (b) Unersetzliches mit einem zerstoerenden Verb anfassen?
        if _trifft(cmd, UNERSETZLICH) and ZERSTOER.search(cmd):
            deny("Zaun: das Unersetzliche (wiki.db/unifieddb/tresor/Laufzeit) wird nicht zerstoert.")
        # (c) Umleitung, die ein geschuetztes Ziel ueberschreibt?
        for m in re.finditer(r">>?\s*([^\s;&|>]+)", cmd):
            ziel = m.group(1)
            if _trifft(ziel, UNERSETZLICH) or GEHEIM_NAME.search(ziel):
                deny("Zaun: kein Ueberschreiben des Unersetzlichen/Geheimen per Umleitung.")
        # (d) zerstoerende DB-Operationen auf dem Herzen
        if _trifft(cmd, UNERSETZLICH) and re.search(r"\b(DROP|DELETE|TRUNCATE)\b", cmd, re.I):
            deny("Zaun: keine zerstoerenden DB-Operationen auf dem Unersetzlichen.")

    sys.exit(0)


if __name__ == "__main__":
    main()
