#!/usr/bin/env python3
"""ratgeber_hook.py — UserPromptSubmit. Haengt an JEDEN Prompt zwei Dinge:

  1. die Zeitzeile aus /var/lib/clay/jetzt.txt -- die DATEI wird gelesen.
     Der Puls schreibt sie alle 4 s. Es wird nicht der Puls gerufen und die
     Zeit nicht selbst gerechnet. ⚠️ Ist die Datei aelter als 60 s, schweigt
     der Puls -- dann wird das GESAGT, statt eine alte Zeit als jetzt
     auszugeben.
  2. den Vorschlag des Ratgebers.

DIE EINE REGEL, die ueber allem steht: DER PROMPT GEHT IMMER DURCH.
Fehlende Datei, veraltete Datei, toter Ratgeber, kein Netz, kaputtes JSON auf
stdin -- in jedem dieser Faelle endet dieser Haken mit 0 und ohne Schaden.
Ein Haken, der den Prompt kaputt machen kann, ist schlechter als gar keiner.
Deshalb liegt der GANZE Rumpf in einem try/except, und das except gibt nichts
aus. Ausgabe auf stdout wird von Claude Code an den Prompt angehaengt --
darum darf dort nie eine Ausnahme landen.

⚠️ GEMESSEN 2026-08-15, und das ist der Grund fuer die Nachreichung:
mistral-small-latest braucht p50 2332 ms, p95 2804 ms. Die vom Eigner
gesetzte harte Frist ist 2,5 s. Es fehlen also regelmaessig ein paar hundert
Millisekunden. Statt die Token wegzuwerfen, rechnet ein ABGEKOPPELTES Kind
zu Ende und legt das Ergebnis in den Ablagekorb; der naechste Prompt reicht
es NACH -- ausdruecklich mit seiner urspruenglichen Frage und seinem Alter
beschriftet, damit niemand es fuer eine Antwort auf die neue Frage haelt.

⚠️ DATENSCHUTZ: der Ratgeber liest die letzten Nachrichten der Sitzung und
schickt sie an MISTRAL. Siehe Kopf von ratgeber.py. Abschaltbar mit
CLAY_RATGEBER_VERLAUF=0.
"""
import json
import os
import subprocess
import sys
import time

WERKZEUG = "/opt/clayverse/werkzeug"
RATGEBER = os.path.join(WERKZEUG, "ratgeber.py")
JETZT = os.environ.get("CLAY_JETZT_DATEI", "/var/lib/clay/jetzt.txt")
KORB = os.environ.get("CLAY_RATGEBER_KORB", "/var/lib/clay/ratgeber")
PYTHON = os.environ.get("CLAY_RATGEBER_PYTHON", "/usr/bin/python3")

FRIST_S = float(os.environ.get("CLAY_RATGEBER_FRIST", "2.5"))
JETZT_ALT_S = 60.0            # darueber schweigt der Puls
NACHREICHUNG_MAX_S = 900.0    # aelteres wird weggeworfen, nicht nachgereicht
TAKT_S = 0.05                 # wie oft im Ablagekorb nachgesehen wird


def zeitzeile():
    """Die Pulszeile, plus ehrliche Aussage ueber ihr Alter."""
    try:
        alt = time.time() - os.path.getmtime(JETZT)
        with open(JETZT, encoding="utf-8") as f:
            z = f.read().strip().splitlines()[0].strip()
        if not z:
            return "ZEIT: die Pulsdatei ist leer — keine Zeit verfuegbar."
        if alt > JETZT_ALT_S:
            # Die alte Zeit wird gezeigt, aber NICHT als jetzt ausgegeben.
            return ("ZEIT: ⚠️ der Puls schweigt seit %.0f s. Letzte "
                    "geschriebene Zeile (VERALTET, nicht jetzt): %s" % (alt, z))
        return "ZEIT: " + z
    except FileNotFoundError:
        return "ZEIT: Pulsdatei %s fehlt — keine Zeit verfuegbar." % JETZT
    except Exception as e:
        return "ZEIT: Pulsdatei nicht lesbar (%s) — keine Zeit verfuegbar." % (
            str(e)[:80])


def _text(spool):
    """Ergebnisdatei -> Text. Nie eine Ausnahme nach draussen."""
    try:
        with open(spool, encoding="utf-8") as f:
            e = json.load(f)
        sys.path.insert(0, WERKZEUG)
        import ratgeber
        return ratgeber.als_text(e), e
    except Exception:
        return None, None


def nachreichung(korb, sitzung):
    """Ein Ergebnis, das die letzte Frist verpasst hat, aber inzwischen
    fertig wurde. Wird mit SEINER Frage und seinem Alter beschriftet --
    sonst liest es sich wie eine Antwort auf die neue Frage."""
    zeilen = []
    try:
        for name in sorted(os.listdir(korb)):
            if not name.startswith(sitzung + ".") or not name.endswith(".json"):
                continue
            p = os.path.join(korb, name)
            alt = time.time() - os.path.getmtime(p)
            t, e = (None, None) if alt > NACHREICHUNG_MAX_S else _text(p)
            for weg in (p, p + ".frage"):
                try:
                    os.unlink(weg)    # genau einmal nachreichen
                except OSError:
                    pass
            if t is None:
                continue
            zeilen.append(
                "NACHGEREICHT (dieser Vorschlag gehoert zur FRUEHEREN Frage "
                "»%s«, %.0f s alt — nicht zur jetzigen):\n%s"
                % ((e.get("frage") or "")[:90], alt, t))
    except Exception:
        pass
    return zeilen


def main():
    try:
        roh = sys.stdin.read()
        d = json.loads(roh) if roh.strip() else {}
    except Exception:
        d = {}                        # unlesbar: der Prompt geht trotzdem durch

    stuecke = [zeitzeile()]

    try:
        frage = (d.get("prompt") or "").strip()
        sitzung = (d.get("session_id") or "ohne")[:40]
        transkript = d.get("transcript_path") or ""

        os.makedirs(KORB, exist_ok=True)
        # Erst nachreichen, was seit dem letzten Prompt fertig wurde.
        stuecke += nachreichung(KORB, sitzung)

        if frage:
            spool = os.path.join(KORB, "%s.%d.json" % (sitzung, int(time.time() * 1000)))
            # Die Frage geht ueber eine DATEI, nicht ueber die Kommandozeile:
            # verschachtelte Anfuehrungszeichen haben in diesem Haus heute
            # schon zweimal einen Aufruf zerlegt.
            fragedatei = spool + ".frage"
            with open(fragedatei, "w", encoding="utf-8") as f:
                f.write(frage)
            kind = subprocess.Popen(
                # ⚠️ Zwei verschiedene Fristen, mit Absicht:
                # der HAKEN wartet hoechstens FRIST_S (2,5 s) -- das ist die
                # Zusicherung "der Prompt wartet nie". Das KIND darf laenger
                # rechnen (MODELLFRIST), weil sein Ergebnis sonst samt der
                # schon bezahlten Token weggeworfen wuerde; es wird beim
                # naechsten Prompt nachgereicht.
                [PYTHON, RATGEBER, "--frage-datei", fragedatei,
                 "--transkript", transkript, "--spool", spool, "--still",
                 "--frist", os.environ.get("CLAY_RATGEBER_MODELLFRIST", "8.0")],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                stdin=subprocess.DEVNULL, start_new_session=True)

            # Warten -- aber nie laenger als die Frist.
            ende = time.time() + FRIST_S
            t = None
            while time.time() < ende:
                if os.path.exists(spool):
                    t, _e = _text(spool)
                    if t is not None:
                        break
                if kind.poll() is not None and not os.path.exists(spool):
                    break             # Kind ist tot und hat nichts abgelegt
                time.sleep(TAKT_S)

            if t is not None:
                try:
                    os.unlink(spool)
                    os.unlink(fragedatei)
                except OSError:
                    pass
                stuecke.append(t)
            else:
                # Das Kind rechnet abgekoppelt weiter; das Ergebnis kommt
                # beim naechsten Prompt als Nachreichung.
                stuecke.append(
                    "RATGEBER: Frist %.1fs verstrichen, kein Vorschlag "
                    "rechtzeitig. Er wird nachgereicht. Der Prompt wartet "
                    "nicht." % FRIST_S)
    except Exception:
        # Ein Haken darf nie der Grund sein, dass eine Sitzung bricht.
        pass

    try:
        sys.stdout.write("\n".join(stuecke) + "\n")
    except Exception:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
