#!/usr/bin/env python3
"""Der Veroeffentlicher -- der einzige Weg von Zero nach draussen, auf dem WIRT.

⭐⭐ WARUM NICHT EINFACH GIT IN DEN CONTAINER:
Zero darf in die Arbeitskopie schreiben -- dafuer ist sie da. Die Arbeitskopie
enthaelt aber `.git/hooks/`. Waere git dort verfuegbar, koennte Zero ein
pre-commit-Hook schreiben und mit dem naechsten Veroeffentlichen ausfuehren
lassen: eine vollstaendige Schale, gebaut aus zwei erlaubten Handgriffen.
"Bash verboten" waere damit eine Formalitaet gewesen.

Deshalb laeuft der Weg nach draussen HIER, ausserhalb des Containers:

  Zero legt einen Auftrag ab  →  dieser Dienst prueft und fuehrt aus  →
  Zero liest das Ergebnis

Der Auftrag enthaelt NUR eine Nachricht und ein Repo aus einer festen Liste.
Kein Befehl, kein Pfad, kein Argument, das ein Modelltext formen koennte.

⚠️ UND DIE HOOK-PRUEFUNG BLEIBT TROTZDEM. Auch hier wird vor jedem Lauf
geprueft, ob in .git/hooks eine ausfuehrbare Datei liegt -- und abgebrochen,
wenn ja. Nicht weil der Weg oben offen waere, sondern weil eine zweite Sperre
genau dann traegt, wenn die erste sich als falsch erweist. Eine Sperre, die man
nur einmal hat, ist eine Annahme.
"""
from __future__ import annotations

import json
import os
import subprocess
import time
from pathlib import Path

AUFTRAEGE = Path("/var/lib/clay/arbeit/.auftrag")
FREIGEGEBEN = {"/var/lib/clay/arbeit/seimensch": ("origin", "main")}
TAKT = 0.12  # war 3.0 -- das war die groesste Einzel-Latenz je Werkzeug-Aufruf.
# 0.12s ist ein billiger glob-Check; die Antwort ist damit fast sofort da,
# statt bis zu 3s auf die naechste Abfrage zu warten.


def _git(repo: Path, *a: str, timeout: int = 120) -> tuple[int, str]:
    r = subprocess.run(
        ["git", "-C", str(repo),
         "-c", f"safe.directory={repo}",
         # Ausdruecklich tot, auch wenn .git/config sie setzt: git zieht diese
         # Werte sonst aus dem Repo und fuehrt sie als Schalbefehl aus.
         "-c", "core.fsmonitor=false",
         "-c", "core.hooksPath=/dev/null",
         "-c", "core.pager=cat",
         "-c", "core.editor=true",
         "-c", "core.sshCommand=",
         "-c", "user.name=Zero", "-c", "user.email=zero@frank.ink", *a],
        capture_output=True, text=True, timeout=timeout,
        # Keine geerbte Umgebung, die einen Umweg oeffnen koennte.
        env={"PATH": "/usr/bin:/bin", "HOME": "/var/lib/clay",
             "GIT_TERMINAL_PROMPT": "0",
             # ⚠️ Keine System- und keine Benutzerkonfiguration. Sonst laesst
             # sich ueber eine ~/.gitconfig oder /etc/gitconfig dasselbe machen
             # wie ueber .git/config -- der Weg waere nur ein anderer.
             "GIT_CONFIG_SYSTEM": "/dev/null",
             "GIT_CONFIG_GLOBAL": "/dev/null",
             "GIT_CONFIG_NOSYSTEM": "1"})
    return r.returncode, ((r.stdout or "") + (r.stderr or ""))[:1500]


# Schluessel, mit denen git Fremdes ausfuehrt. Die Liste ist NICHT die
# Hauptsperre -- die ist, dass Zero .git gar nicht erreicht. Sie faengt den
# Fall ab, dass etwas anderes doch dort hineinschreibt.
GEFAEHRLICH = ("fsmonitor", "hookspath", "sshcommand", "pager", "editor",
               "askpass", "alias.", "sendemail", "difftool", "mergetool",
               "credential.helper", "uploadpack", "receivepack", "externaldiff",
               "gpg.program", "filter.", "ssh.variant",
               # Nachgetragen 18.08. nach einem Pruefangriff. `include` und
               # `includeif` sind die heikelsten: sie holen Konfiguration aus
               # einer ANDEREN Datei, an der diese Textpruefung vorbeisieht.
               "include.", "includeif", "diff.external", "sequence.editor",
               "templatedir", "insteadof", "protocol.", "core.symlinks")


def _config_sauber(repo: Path) -> tuple[bool, str]:
    """Steht in .git/config ein Schluessel, mit dem git Fremdes ausfuehrt?

    ⚠️ Genau hierueber lief der nachgewiesene Ausbruch: `core.fsmonitor` mit
    einem Schalbefehl als Wert, ausgeloest schon durch ein blosses `git status`.
    Gelesen wird als Text, nicht mit `git config` -- ein `git config`-Aufruf
    wuerde die Konfiguration bereits auswerten und damit genau das ausloesen,
    wovor er schuetzen soll.
    """
    c = repo / ".git" / "config"
    if not c.is_file():
        return True, ""
    try:
        text = c.read_text(encoding="utf-8", errors="replace").lower()
    except OSError as e:
        return False, f".git/config nicht lesbar ({e}) -- im Zweifel nicht anfassen"
    gefunden = [g for g in GEFAEHRLICH if g in text]
    if gefunden:
        return False, (".git/config enthaelt ausfuehrende Schluessel: "
                       + ", ".join(gefunden) +
                       " -- git wuerde deren Wert als Befehl ausfuehren. "
                       "Ich fasse dieses Repo nicht an.")
    return True, ""


def _hooks_sauber(repo: Path) -> tuple[bool, str]:
    """Liegt in .git/hooks etwas Ausfuehrbares? Dann NICHT anfassen.

    ⚠️ Das ist die zweite Sperre. git fuehrt Hooks aus, und die Arbeitskopie ist
    fuer Zero schreibbar. Wer hier nicht prueft, hat den Container umsonst ohne
    git gebaut.
    """
    h = repo / ".git" / "hooks"
    if not h.is_dir():
        return True, ""
    verdaechtig = [f.name for f in h.iterdir()
                   if f.is_file() and not f.name.endswith(".sample") and os.access(f, os.X_OK)]
    if verdaechtig:
        return False, ("ausfuehrbare Hooks in .git/hooks: " + ", ".join(verdaechtig) +
                       " -- ein Hook laeuft beim Commit und waere eine Schale. "
                       "Ich fasse dieses Repo nicht an.")
    return True, ""


def _zurueckgeben(repo: Path) -> None:
    """Die Arbeitskopie gehoert wieder Zero.

    root-Aufrufe wie `git add` schreiben Dateien als root zurueck. Zero koennte
    sie danach nicht mehr aendern -- und bekaeme eine Rechteverweigerung, die
    wie der Zaun aussieht, aber keiner ist.
    """
    try:
        subprocess.run(["chown", "-R", "clay:clay", str(repo)],
                       capture_output=True, timeout=60)
    except Exception:
        pass


def bearbeite(auftrag: Path) -> dict:
    try:
        a = json.loads(auftrag.read_text(encoding="utf-8"))
    except Exception as e:
        return {"veroeffentlicht": False, "fehler": f"Auftrag unlesbar: {e}"}

    if a.get("art") == "seite_diagnose":
        import importlib.util as _il
        _s = _il.spec_from_file_location("diagnose", "/opt/entityos/diagnose.py")
        _m = _il.module_from_spec(_s); _s.loader.exec_module(_m)
        return _m.diagnose(str(a.get("url") or ""))

    if a.get("art") == "seite_pruefen":
        # ⭐ Der Blick auf die EIGENE Auslieferung. Laeuft hier draussen, weil der
        # Container bewusst kein Netz hat -- und weil die Erlaubnisliste der
        # Domains auf dem Wirt steht, wo ein Modelltext sie nicht erweitern kann.
        import importlib.util as _il
        _s = _il.spec_from_file_location("seitenpruefer", "/opt/entityos/seitenpruefer.py")
        _m = _il.module_from_spec(_s); _s.loader.exec_module(_m)
        return _m.pruefen(str(a.get("url") or ""), str(a.get("suche") or ""))

    if a.get("art") in ("speicher_lage", "speicher_aufraeumen",
                        "speicher_rueckweg", "speicher_abschaffen"):
        # ⚠️ Zero darf NACHSEHEN und AUFRAEUMEN LASSEN, aber nicht bestimmen,
        # WAS Muell ist. Die Muster und die UNANTASTBAR-Liste stehen in
        # speicherwacht.py auf dem Wirt und sind von hier aus nicht zu
        # beeinflussen. Ein Auftrag kann keinen Pfad mitgeben.
        import importlib.util as _il
        _s = _il.spec_from_file_location("speicherwacht", "/opt/entityos/speicherwacht.py")
        _m = _il.module_from_spec(_s); _s.loader.exec_module(_m)
        if a["art"] == "speicher_bilanz":
            # Die teure Vollrechnung -- ausdruecklich abgerufen, nicht im
            # heissen Pfad jeder "wie voll"-Frage.
            return {"lage": _m.lage(), "bilanz": _m.bilanz(zeitlimit=60),
                    "verursacher": _m.verursacher(), "altbestand": _m.altbestand()}
        if a["art"] == "speicher_lage":
            erg = _m.lage()
            # ⚠️ NUR die sofortige Messung im heissen Pfad. lage() ist
            # shutil.disk_usage -- Millisekunden. bilanz() (du-Scans, bis 45s)
            # und verursacher() (systemctl) machten "wie voll ist die Platte"
            # zu einer 5-Sekunden-Frage. Die volle Bilanz laeuft im
            # 30-Minuten-Waechter und ist ueber speicher_bilanz abrufbar.
            erg["waere_wegwerfbar_gb"] = round(sum(k["gb"] for k in _m._kandidaten(12.0)), 2)
            return erg
        if a["art"] == "speicher_rueckweg":
            return _m.rueckweg()
        if a["art"] == "speicher_abschaffen":
            # ⚠️ Der Pfad wird NICHT frei uebernommen: abschaffen() prueft ihn
            # gegen die von Hand gepflegte ALTBESTAND-Liste und verweigert
            # alles andere. Ein Auftrag kann hier keinen Pfad erfinden.
            return _m.abschaffen(str(a.get("pfad") or ""))
        return _m.wachen(nur_zeigen=bool(a.get("nur_zeigen")))

    repo_s = str(a.get("repo") or "")
    ziel = FREIGEGEBEN.get(repo_s)
    if not ziel:
        return {"veroeffentlicht": False,
                "fehler": f"{repo_s} ist nicht freigegeben. Freigegeben: {list(FREIGEGEBEN)}. "
                          "Ein Repo ist ein Weg nach draussen und wird einzeln benannt, "
                          "nicht pauschal erlaubt."}
    repo = Path(repo_s)

    # ⚠️ VOR jedem git-Aufruf, auch vor `stand`. Vorher lief `stand` durch
    # KEINE Pruefung -- und genau `stand` war der Ausloeser des Ausbruchs:
    # ein `git status` genuegt, damit git core.fsmonitor ausfuehrt. Eine
    # Pruefung, die nur den gefaehrlich aussehenden Weg bewacht, bewacht nichts.
    for pruefer, marke in ((_config_sauber, "config"), (_hooks_sauber, "hooks")):
        ok, grund = pruefer(repo)
        if not ok:
            return {"veroeffentlicht": False, "fehler": grund, "sperre": marke}

    if a.get("art") == "stand":
        # Reine Abfrage: nichts wird geaendert, also auch keine Nachricht noetig.
        rc, offen = _git(repo, "status", "--short")
        rc2, letzte = _git(repo, "log", "--oneline", "-3")
        _zurueckgeben(repo)   # auch nach einer blossen Abfrage: wer anfasst, gibt zurueck
        return {"repo": repo_s,
                "geaendert": [z for z in offen.splitlines() if z.strip()],
                "letzte_commits": letzte.splitlines()}

    nachricht = str(a.get("nachricht") or "").strip()
    if not nachricht:
        return {"veroeffentlicht": False,
                "fehler": "ohne Nachricht wird nicht veroeffentlicht -- wer spaeter liest, "
                          "muss erfahren WARUM, nicht nur WAS"}

    rc, offen = _git(repo, "status", "--porcelain")
    dateien = [z for z in offen.splitlines() if z.strip()]

    # ⚠️ GEMESSEN: ein Commit gelang, der Push scheiterte -- und danach war der
    # Commit UNERREICHBAR. Der naechste Versuch sah einen sauberen Baum, meldete
    # "nichts geaendert" und tat nichts. Die Arbeit war getan, lag fest und kein
    # Werkzeug kam mehr an sie heran; nur ein Mensch mit einer Schale haette sie
    # noch befreien koennen. Ein Weg, der beim Scheitern in eine Sackgasse
    # fuehrt, ist schlechter als einer, der gar nicht erst losgeht.
    rc_v, voraus = _git(repo, "rev-list", "--count", f"{ziel[0]}/{ziel[1]}..HEAD")
    try:
        offene_commits = int(voraus.strip() or "0")
    except ValueError:
        offene_commits = 0

    if not dateien and not offene_commits:
        return {"veroeffentlicht": False, "grund": "nichts geaendert -- kein Leercommit"}

    schritte = []
    if not dateien and offene_commits:
        # Nur nachholen, was schon committet ist. Kein neuer Commit -- die
        # Begruendung von damals bleibt stehen, sie wird nicht ueberschrieben.
        befehle = (("push", ziel[0], f"HEAD:{ziel[1]}"),)
        dateien = [f"(kein neuer Commit -- {offene_commits} wartende(r) Commit(s) "
                   "aus einem frueheren, gescheiterten Push)"]
    else:
        befehle = (("add", "-A"),
                   ("commit", "-q", "-m", nachricht[:2000]),
                   ("push", ziel[0], f"HEAD:{ziel[1]}"))
    for befehl in befehle:
        rc, aus = _git(repo, *befehl)
        schritte.append({"schritt": befehl[0], "rc": rc, "ausgabe": aus.strip()[:400]})
        if rc != 0:
            return {"veroeffentlicht": False, "fehlgeschlagen_bei": schritte[-1],
                    "schritte": schritte, "dateien": dateien}

    _zurueckgeben(repo)
    rc, kopf = _git(repo, "log", "--oneline", "-1")
    return {"veroeffentlicht": True, "dateien": dateien, "anzahl": len(dateien),
            "nachgeholte_commits": offene_commits,
            "commit": kopf.strip(), "schritte": schritte,
            "hinweis": "Bei SeiMensch geht ein Push auf main SOFORT oeffentlich. "
                       "Pruefe die Seite, statt den Erfolg zu behaupten."}


def main() -> None:
    AUFTRAEGE.mkdir(parents=True, exist_ok=True)
    os.chmod(AUFTRAEGE, 0o2775)
    while True:
        for f in sorted(AUFTRAEGE.glob("*.auftrag")):
            erg = {"veroeffentlicht": False, "fehler": "unbehandelt"}
            try:
                erg = bearbeite(f)
            except Exception as e:
                erg = {"veroeffentlicht": False, "fehler": f"{type(e).__name__}: {e}"}
            finally:
                erg["fertig"] = time.time()
                ziel = f.with_suffix(".ergebnis")
                ziel.write_text(json.dumps(erg, ensure_ascii=False, indent=2), encoding="utf-8")
                os.chmod(ziel, 0o664)
                f.unlink(missing_ok=True)
        time.sleep(TAKT)


if __name__ == "__main__":
    main()
