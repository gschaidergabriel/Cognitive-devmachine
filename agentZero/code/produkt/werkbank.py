"""Die Werkbank -- Zero wird handlungsfaehig, ohne eine Schale zu bekommen.

Gabriel: "agent zero muss handlungsfaehig sein ... er muss genau so
handlungsfaehig sein wie du." Und zugleich gilt die Architekturregel:
"Zeros einzige Werkzeugflaeche ist der verwaltete MCP-Server, Bash verboten."

⭐ BEIDES GEHT, UND ZWAR SO: nicht Bash geben, sondern GENAU DIE FAEHIGKEITEN,
die ich zum Arbeiten wirklich brauche -- lesen, suchen, schreiben,
veroeffentlichen -- jede als eigenes Werkzeug mit eigenem Zaun. Eine Schale
gaebe alles auf einmal und liesse sich nicht einzaeunen; vier benannte
Faehigkeiten schon.

Was damit MOEGLICH wird: eine Telefonnummer in einer Seite finden, sie in allen
Fundstellen sehen, eine davon aendern und die Aenderung veroeffentlichen.
Was damit UNMOEGLICH bleibt: curl, ssh, systemctl, Pakete nachladen,
Rechte aendern, andere Dienste anfassen, aus dem Zaun heraustreten.

═══ DER ZAUN ═══

WURZELN ist eine Erlaubnisliste. Alles ausserhalb wird abgewiesen, und zwar
NACH Aufloesung aller Symlinks und "..": eine Pruefung auf der Zeichenkette
liesse sich mit ../.. umgehen, eine auf dem aufgeloesten Pfad nicht.

⚠️ Die Live-Wurzeln der Seiten sind NUR LESBAR eingetragen. Sie werden vom
Deploy-Hook befuellt; wer dort schreibt, verliert seine Aenderung beim naechsten
Push und haelt sie fuer erledigt. Geschrieben wird in der Arbeitskopie, und
veroeffentlicht wird ueber `veroeffentlichen()`.

⚠️ Und `veroeffentlichen()` ist der einzige Weg nach draussen. Es macht genau
zwei Dinge -- committen und pushen -- mit festen Argumenten, ohne Schale. Ein
Modelltext kann daraus keinen anderen Befehl formen.
"""
from __future__ import annotations

import json
import os
import re
import time
from pathlib import Path

# Erlaubnisliste. (Pfad, schreibbar)
WURZELN: list[tuple[Path, bool]] = [
    (Path("/var/lib/clay/arbeit"), True),          # Arbeitskopien -- hier wird gearbeitet
    (Path("/var/lib/agentforge/projects"), False),  # ausgelieferte Seiten -- nur lesen
]
MAX_LESEN = 200_000
MAX_SCHREIBEN = 400_000
MAX_TREFFER = 60
AUFTRAEGE = Path("/var/lib/clay/arbeit/.auftrag")
WARTEN_MAX = 120.0

# Repos, in denen veroeffentlicht werden darf. Nicht "jedes Git unter der
# Wurzel": ein Repo ist ein Weg nach draussen und gehoert einzeln benannt.
VEROEFFENTLICHBAR = {"/var/lib/clay/arbeit/seimensch": "origin main"}


class ZaunFehler(PermissionError):
    pass


def _pruefe(pfad: str, *, schreiben: bool = False) -> Path:
    """Aufloesen und gegen die Erlaubnisliste pruefen. Wirft, statt zu kuerzen.

    ⭐ NACH der Aufloesung geprueft: eine Pruefung auf der Zeichenkette liesse
    sich mit ../.. oder einem Symlink umgehen. `resolve()` macht daraus einen
    echten Pfad, und erst der wird verglichen.
    """
    p = Path(pfad).expanduser()
    if not p.is_absolute():
        p = WURZELN[0][0] / p
    p = p.resolve()
    # ⚠️⚠️ .git ist fuer Zero unsichtbar -- lesen UND schreiben.
    # Ein beschreibbares .git/config ist ein Weg, dem Wirt Befehle
    # unterzuschieben (core.fsmonitor, core.pager, core.sshCommand, alias.*).
    # Nachgewiesen: damit lief Fremdcode als root. Eine Liste der gefaehrlichen
    # Schluessel zu pflegen hiesse, sich auf die eigene Vollstaendigkeit zu
    # verlassen -- der ganze Ordner ist die ehrlichere Sperre. Zero arbeitet an
    # der Arbeitskopie, nicht an ihrer Verwaltung.
    # ⚠️ Kleinschreibung vergleichen, nicht woertlich. Auf ext4 ist `.GIT` ein
    # anderer, nicht existierender Ordner -- aber sich darauf zu verlassen heisst,
    # eine Sicherheitseigenschaft an eine Dateisystem-Einstellung zu haengen.
    # Auf einem Dateisystem ohne Gross-/Kleinschreibung waere derselbe Zaun offen.
    teile = {t.lower() for t in p.parts}
    if ".git" in teile:
        raise ZaunFehler(
            f"{p} liegt in .git -- die Verwaltung der Arbeitskopie ist nicht dein "
            "Arbeitsplatz. Ein beschreibbares .git/config koennte dem Wirt Befehle "
            "unterschieben. Aendere Dateien, nicht das Repo.")
    # ⚠️ Diese zwei liegen im Arbeitsbaum, steuern aber, WIE git Dateien
    # verarbeitet -- .gitattributes kann Filter und Zeilenenden umstellen und
    # damit aus einer Ein-Zeilen-Aenderung einen Commit machen, der JEDE Datei
    # anfasst. Das ist keine Codeausfuehrung, aber ein Weg, unbemerkt viel zu
    # veroeffentlichen. .gitmodules zieht fremde Repos herein.
    # .gitignore bleibt erlaubt: das ist eine gewoehnliche Projektdatei.
    if p.name.lower() in (".gitattributes", ".gitmodules"):
        raise ZaunFehler(
            f"{p.name} steuert, WIE git Dateien verarbeitet -- damit liesse sich aus einer "
            "kleinen Aenderung ein Commit ueber den ganzen Baum machen. Nicht dein "
            "Arbeitsplatz. (.gitignore darfst du anfassen.)")

    for wurzel, schreibbar in WURZELN:
        try:
            p.relative_to(wurzel.resolve())
        except ValueError:
            continue
        if schreiben and not schreibbar:
            raise ZaunFehler(
                f"{wurzel} ist nur lesbar. Das ist die ausgelieferte Fassung -- sie wird "
                f"vom Deploy-Hook befuellt, und eine Aenderung dort waere beim naechsten "
                f"Push weg. Arbeite in /var/lib/clay/arbeit und veroeffentliche dann.")
        return p
    raise ZaunFehler(
        f"{p} liegt ausserhalb der erlaubten Wurzeln "
        f"({', '.join(str(w) for w, _ in WURZELN)}). Das ist kein Versehen, sondern der Zaun.")


def liste(pfad: str = "/var/lib/clay/arbeit", tiefe: int = 1) -> dict:
    """Was liegt hier? Ohne Schale, ohne Umwege."""
    p = _pruefe(pfad)
    if not p.is_dir():
        return {"pfad": str(p), "fehler": "kein Verzeichnis"}
    alle = sorted(p.iterdir())
    eintraege = [{"name": k.name, "art": "ordner" if k.is_dir() else "datei",
                  "bytes": k.stat().st_size if k.is_file() else None}
                 for k in alle[:200]]
    erg = {"pfad": str(p), "eintraege": eintraege,
           "anzahl_geliefert": len(eintraege), "anzahl_gesamt": len(alle)}
    if len(alle) > len(eintraege):
        erg["abgeschnitten"] = True
        erg["hinweis"] = (f"{len(alle)} Einträge insgesamt, {len(eintraege)} aufgeführt. "
                          "Wer 200 sieht und 234 hat, hält 200 für alles.")
    return erg


def lesen(pfad: str, von: int = 1, zeilen: int = 400) -> dict:
    """Datei lesen, mit Zeilennummern -- damit ein Beleg praezise sein kann."""
    p = _pruefe(pfad)
    if not p.is_file():
        return {"pfad": str(p), "fehler": "keine Datei"}
    if p.stat().st_size > MAX_LESEN:
        return {"pfad": str(p), "fehler": f"groesser als {MAX_LESEN} Bytes -- "
                                          "nutze suchen(), um die Stelle zu finden"}
    alle = p.read_text(encoding="utf-8", errors="replace").splitlines()
    von = max(1, int(von))
    teil = alle[von - 1: von - 1 + max(1, min(int(zeilen), 800))]
    return {"pfad": str(p), "zeilen_gesamt": len(alle), "ab": von,
            "text": "\n".join(f"{von+i:>5}  {z}" for i, z in enumerate(teil))}


def suchen(muster: str, pfad: str = "/var/lib/clay/arbeit", nur: str = "") -> dict:
    """Wie grep -rn. Findet ALLE Fundstellen -- nicht nur die erste.

    ⚠️ Das ist der Grund, warum es dieses Werkzeug gibt: Zero hat bei der
    Telefonnummer selbst gewarnt, dass sie ausser in der Kontaktseite auch in
    Fussbereich und Impressum stehen duerfte. Wer nur die erste Stelle sieht,
    haelt die Sache fuer erledigt und laesst sie anderswo oeffentlich stehen.
    """
    p = _pruefe(pfad)
    try:
        r = re.compile(muster, re.IGNORECASE)
    except re.error as e:
        return {"fehler": f"ungueltiges Muster: {e}"}
    treffer, geprueft, gesamt = [], 0, 0
    je_datei: dict[str, int] = {}
    dateien = [p] if p.is_file() else sorted(p.rglob(nur or "*"))
    for f in dateien:
        if not f.is_file() or ".git" in f.parts:
            continue
        try:
            if f.stat().st_size > MAX_LESEN:
                continue
            text = f.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        geprueft += 1
        for nr, zeile in enumerate(text.splitlines(), 1):
            if r.search(zeile):
                gesamt += 1
                je_datei[str(f)] = je_datei.get(str(f), 0) + 1
                # Weitergezaehlt wird IMMER, ausgeliefert nur bis zur Kappung.
                if len(treffer) < MAX_TREFFER:
                    treffer.append({"datei": str(f), "zeile": nr,
                                    "text": zeile.strip()[:220]})

    erg = {"muster": muster, "treffer": treffer, "anzahl_geliefert": len(treffer),
           "anzahl_gesamt": gesamt, "dateien_mit_treffern": len(je_datei),
           "je_datei": dict(sorted(je_datei.items(), key=lambda x: -x[1])[:120]),
           "dateien_geprueft": geprueft}
    if gesamt > len(treffer):
        erg["abgeschnitten"] = True
        erg["hinweis"] = (
            f"{gesamt} Fundstellen insgesamt, {len(treffer)} davon einzeln aufgefuehrt. "
            "Die ZAHL ist vollstaendig, die Liste nicht -- `je_datei` nennt jede "
            "betroffene Datei mit ihrer Trefferzahl. Fuer die Einzelzeilen einer "
            "Datei nimm `pfad=<die Datei>`.")
    else:
        erg["hinweis"] = ("Alle Fundstellen im erlaubten Bereich. Steht hier nichts, "
                          "gibt es dort nichts -- das ist ein Befund.")
    return erg


def schreiben(pfad: str, alt: str, neu: str) -> dict:
    """Ersetzt EINE eindeutige Stelle. Kein Ueberschreiben ganzer Dateien.

    ⭐ `alt` muss genau einmal vorkommen. Kommt es mehrfach vor, wird
    abgewiesen statt zu raten, welche Stelle gemeint war -- und kommt es gar
    nicht vor, ist die Annahme ueber den Dateiinhalt falsch, was man wissen
    will, bevor man schreibt.
    """
    p = _pruefe(pfad, schreiben=True)
    if not p.is_file():
        return {"pfad": str(p), "fehler": "keine Datei"}
    if p.stat().st_size > MAX_SCHREIBEN:
        return {"pfad": str(p), "fehler": "zu gross"}
    text = p.read_text(encoding="utf-8")
    n = text.count(alt)
    if n == 0:
        return {"pfad": str(p), "fehler": "die zu ersetzende Stelle kommt nicht vor -- "
                                          "deine Annahme ueber den Inhalt stimmt nicht. "
                                          "Erst lesen()."}
    if n > 1:
        return {"pfad": str(p), "fehler": f"die Stelle kommt {n}-mal vor. Nimm mehr Umgebung "
                                          "dazu, damit sie eindeutig ist -- ich rate nicht, "
                                          "welche gemeint war."}
    p.write_text(text.replace(alt, neu), encoding="utf-8")
    return {"pfad": str(p), "ersetzt": 1, "bytes_neu": p.stat().st_size,
            "beleg": f"{p}: '{alt[:60]}' -> '{neu[:60]}'"}


def _auftrag(art: str, **daten) -> dict:
    """Einen Auftrag an den Veroeffentlicher auf dem Wirt legen und warten.

    ⭐⭐ WARUM NICHT EINFACH GIT HIER AUFRUFEN: Im Container gibt es kein git --
    absichtlich. Zero darf in die Arbeitskopie schreiben, und die enthaelt
    `.git/hooks/`. Waere git hier verfuegbar, koennte Zero ein pre-commit-Hook
    schreiben und beim naechsten Veroeffentlichen ausfuehren lassen: eine
    vollstaendige Schale, gebaut aus zwei erlaubten Handgriffen. "Bash verboten"
    waere eine Formalitaet gewesen.

    Der Auftrag traegt nur eine Nachricht und ein Repo aus einer festen Liste.
    Kein Befehl, kein Pfad, kein Argument, das ein Modelltext formen koennte.
    """
    AUFTRAEGE.mkdir(parents=True, exist_ok=True)
    kennung = f"{int(time.time()*1000)}-{os.getpid()}"
    ziel = AUFTRAEGE / f"{kennung}.auftrag"
    ergebnis = AUFTRAEGE / f"{kennung}.ergebnis"
    ziel.write_text(json.dumps({"art": art, **daten}, ensure_ascii=False), encoding="utf-8")
    frist = time.time() + WARTEN_MAX
    while time.time() < frist:
        if ergebnis.exists():
            try:
                erg = json.loads(ergebnis.read_text(encoding="utf-8"))
            except Exception as e:
                erg = {"veroeffentlicht": False, "fehler": f"Ergebnis unlesbar: {e}"}
            ergebnis.unlink(missing_ok=True)
            return erg
        time.sleep(0.4)
    return {"veroeffentlicht": False,
            "fehler": f"der Veroeffentlicher hat in {WARTEN_MAX}s nicht geantwortet. "
                      "Das heisst NICHT, dass nichts passiert ist -- pruefe mit "
                      "werkbank_stand, bevor du es erneut versuchst."}


def _git(repo: Path, *args: str, timeout: int = 90) -> tuple[int, str]:
    r = subprocess.run(["git", "-C", str(repo), *args],
                       capture_output=True, text=True, timeout=timeout)
    return r.returncode, ((r.stdout or "") + (r.stderr or ""))[:1200]


def stand(repo: str = "/var/lib/clay/arbeit/seimensch") -> dict:
    """Was ist in der Arbeitskopie geaendert, aber noch nicht veroeffentlicht?

    Laeuft ueber den Veroeffentlicher, weil im Container kein git liegt.
    """
    p = _pruefe(repo)
    return _auftrag("stand", repo=str(p))


def veroeffentlichen(nachricht: str, repo: str = "/var/lib/clay/arbeit/seimensch") -> dict:
    """Committen und pushen -- der EINZIGE Weg nach draussen.

    Ausgefuehrt wird das auf dem WIRT, nicht hier: siehe _auftrag(). Der
    Veroeffentlicher prueft ausserdem vor jedem Lauf, ob in .git/hooks etwas
    Ausfuehrbares liegt, und bricht dann ab. Zwei Sperren, weil eine Sperre,
    die man nur einmal hat, eine Annahme ist.

    ⚠️ Ein Push auf main geht bei SeiMensch SOFORT oeffentlich. Deshalb nennt
    das Ergebnis die Zahl der geaenderten Dateien: wer mehr aendert als
    gedacht, soll es im Beleg sehen und nicht auf der Live-Seite.
    """
    p = _pruefe(repo)
    if str(p) not in VEROEFFENTLICHBAR:
        return {"fehler": f"{p} ist nicht zum Veroeffentlichen freigegeben. "
                          f"Freigegeben: {list(VEROEFFENTLICHBAR)}"}
    if not str(nachricht or "").strip():
        return {"fehler": "ohne Nachricht wird nicht veroeffentlicht -- wer spaeter liest, "
                          "muss erfahren WARUM, nicht nur WAS"}
    return _auftrag("veroeffentlichen", repo=str(p), nachricht=str(nachricht).strip())


def speicher_lage() -> dict:
    """Wie voll ist die Platte des Wirts, und was waere wegwerfbar?"""
    return _auftrag("speicher_lage")


def speicher_aufraeumen(nur_zeigen: bool = True) -> dict:
    """Aufraeumen lassen. Vorgabe ist ZEIGEN, nicht loeschen.

    ⭐ Die Vorgabe steht bewusst auf `nur_zeigen=True`. Wer aufraeumt, soll
    vorher gesehen haben, was verschwindet -- und Loeschen ist der eine
    Handgriff, den man nicht zurueckholt.

    ⚠️ Du bestimmst NICHT, was Muell ist. Muster, Mindestalter und die
    namentliche Liste des Unantastbaren stehen auf dem Wirt. wiki.db,
    /opt/unifieddb, /etc/entityos, die Repos und die ausgelieferten Seiten
    stehen darauf -- an die kommt dieser Weg nicht heran, auch nicht auf
    deine Anweisung.
    """
    return _auftrag("speicher_aufraeumen", nur_zeigen=bool(nur_zeigen))


def speicher_rueckweg() -> dict:
    """Verzeichnis des Altbestands schreiben -- WAS da liegt, damit es zurueckkommen kann.

    ⭐ Gewichte sind nachladbar, die Liste war es nicht. Diese Funktion schreibt
    jedes Modell mit Namen, Fassung und Nachladebefehl ins Wiki. Erst danach
    darf ein Posten ueberhaupt entfernt werden -- ohne Verzeichnis waere das
    Loeschen unumkehrbar, und genau das ist ausgeschlossen.
    """
    return _auftrag("speicher_rueckweg")


def speicher_abschaffen(pfad: str) -> dict:
    """Einen Altbestandsposten entfernen. Nur nach geschriebenem Rueckweg.

    ⚠️ Du kannst hier keinen beliebigen Pfad nennen: er muss woertlich in der
    von Hand gepflegten ALTBESTAND-Liste auf dem Wirt stehen. Alles andere wird
    abgewiesen -- auch wenn es nach Muell aussieht.
    """
    return _auftrag("speicher_abschaffen", pfad=str(pfad))


def seite_pruefen(url: str, suche: str = "") -> dict:
    """Nachsehen, was auf einer EIGENEN Seite wirklich steht.

    ⭐ Nutze das nach jedem Veroeffentlichen. Vorher stand in deiner Anleitung
    "pruefe die Seite, statt den Erfolg zu behaupten" -- ohne dass es ein
    Mittel dazu gab. Eine Pflicht ohne Werkzeug erzieht nicht zur Sorgfalt.

    ⚠️⚠️ UND SIE IST NOETIG: `/srv/git/seimensch.git` auf diesem Wirt ist ein
    SPIEGEL. Ein Push dorthin durchlaeuft den vollstaendigen Deploy-Haken --
    Sicherung, Integritaetspruefung, Spiegelung, chown -- und meldet Erfolg,
    waehrend seimensch.net von 72.61.19.188 ausgeliefert wird. Das ist die
    gefaehrlichste Sorte Erfolg: einer mit vollstaendigem Beleg.
    """
    return _auftrag("seite_pruefen", url=str(url), suche=str(suche or ""))
