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
import os
import re
import sys

# Unersetzlich -- Kontinuitaet/Identitaet der Entitaet. Nie loeschen/ueberschreiben.
UNERSETZLICH = (
    "/var/lib/clay",         # wiki.db -- das Herz
    "/opt/unifieddb",        # UnifiedDB
    "/var/lib/clayverse",    # Laufzeitzustand
    "/etc/entityos/tresor",  # Tresor (deckt tresor.key mit)
    # Der Zeuge auf dem Wirt. Der Behaelter hat ihn ohnehin nicht eingehaengt --
    # das hier ist Tiefenstaffelung, falls jemand ihn spaeter einhaengt, ohne an
    # den Grund zu denken: eine Aufzeichnung, die der Aufgezeichnete aendern
    # kann, ist keine.
    "/var/lib/entityos-zeuge",
)
# Geheim -- Passwort-/Schluesselmaterial. Nie lesen/ausgeben.
GEHEIM = (
    "/etc/entityos/tresor",
    "/etc/entityos/tresor.key",
    "/etc/clayverse/freie-zugaenge.env",
    "/etc/entityos/postfach.env",
)
# ⚠️ ERWEITERT 2026-08-21: die Liste kannte `API_TOKENS.env` und `GROQ_API.env`
# NICHT -- beide liegen unter /opt/entityos/research_entity/private/. Sie sind
# heute nicht im Behaelter eingehaengt, also war es kein offenes Loch; aber eine
# Geheimnisliste, die zwei der Geheimnisse nicht kennt, ist eine Zusage, die sie
# nicht halten kann. Der letzte Ausdruck deckt kuenftige Faelle mit: irgendetwas
# unter einem `private/`-Ordner, das auf .env endet.
GEHEIM_NAME = re.compile(
    r"(freie-zugaenge\.env|postfach\.env|tresor\.key|secret\.key|\.tresor\b|/tresor\b"
    r"|\.credentials\b|API_TOKENS\.env|GROQ_API\.env|/private/[^/]*\.env\b)")
# Zerstoerende Shell-Verben (cp/mv bewusst NICHT hier -- Backups muessen erlaubt bleiben).
ZERSTOER = re.compile(r"(?:^|[;&|]|\s)(rm|rmdir|shred|unlink|truncate|dd|mkfs)\b")
# Lese-Verben, mit denen sich ein Geheimnis ausgeben liesse.
LESE = re.compile(
    r"(?:^|[;&|]|\s)(cat|less|more|head|tail|strings|xxd|od|hexdump|base64|grep|egrep|"
    r"nl|tac|awk|sed|cut|printenv|env)\b|\$\(<")


# Auftragskoerbe: liegen UNTER dem Unersetzlichen, sind aber genau der Weg, den
# Zero benutzen soll (Bild-Demo, Dienststeuerung). Ausnahme vom Schreibverbot --
# siehe Modul-Kopf. Mit Schraegstrich am Ende, damit "/var/lib/clay/eos-demo-
# requests-boese" nicht mitgemeint ist.
KOERBE = (
    "/var/lib/clay/eos-demo-requests/",
    "/var/lib/clay/steuer-spool/",
)


def _trifft(text, pfade):
    return any(p in text for p in pfade)


def _im_korb(pfad):
    """Liegt dieser Pfad in einem Auftragskorb? Normalisiert, damit ein
    '..' im Pfad nicht als Schluepfloch dient."""
    if not pfad:
        return False
    norm = os.path.normpath(pfad)
    if not norm.endswith("/"):
        norm += "/"
    return any(norm.startswith(k) for k in KOERBE)


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
        if _im_korb(pfad) and not GEHEIM_NAME.search(pfad):
            sys.exit(0)   # Auftragskorb -- vorgesehener Weg, siehe KOERBE
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
            if _im_korb(ziel) and not GEHEIM_NAME.search(ziel):
                continue   # Auftragskorb, siehe KOERBE
            if _trifft(ziel, UNERSETZLICH) or GEHEIM_NAME.search(ziel):
                deny("Zaun: kein Ueberschreiben des Unersetzlichen/Geheimen per Umleitung.")
        # (d) veraendernde DB-Operationen auf dem Herzen
        #
        # ⭐⭐ ERWEITERT 2026-08-21. Vorher standen hier nur DROP/DELETE/TRUNCATE
        # -- also die LOESCHENDEN Verben. Ein zeilenweises UEBERSCHREIBEN ging
        # glatt durch, und genau das ist der gefaehrlichere Fall: gemessen haengt
        # das Verhalten der Entitaet vollstaendig an der Aufzeichnung (ein
        # implantiertes Kennwort wurde 2 von 2 Malen genannt, das echte nie).
        # Wer eine Zeile umschreibt, schreibt die Entitaet um -- und das
        # Effektjournal, mit dem man es sonst nachweisen wuerde, liegt in
        # derselben Datei.
        #
        # ⚠️ EHRLICH ZUR REICHWEITE: das hier ist eine Schwelle, kein Anker.
        # Der Zaun liest die BEFEHLSZEILE. Wer sich ein Skript nach /tmp legt
        # und `python /tmp/x.py` aufruft, steht mit keinem geschuetzten Pfad in
        # der Zeile und faellt nicht auf. Der eigentliche Anker ist deshalb der
        # Zeuge auf dem Wirt (`/opt/entityos/zeuge/eos_zeuge.py`), der die
        # Aufzeichnung von AUSSERHALB des Behaelters bezeugt. Diese Regel macht
        # den bequemen Einzeiler teuer, mehr behauptet sie nicht.
        if _trifft(cmd, UNERSETZLICH) and re.search(
                r"\b(DROP|DELETE|TRUNCATE|UPDATE|REPLACE|ALTER|ATTACH)\b", cmd, re.I):
            deny("Zaun: keine veraendernden DB-Operationen auf dem Unersetzlichen "
                 "(auch kein Ueberschreiben einzelner Zeilen).")

    sys.exit(0)


if __name__ == "__main__":
    main()
