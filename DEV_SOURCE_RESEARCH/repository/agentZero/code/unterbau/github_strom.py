#!/usr/bin/env python3
"""github_strom.py — GitHub-Ereignisse laufend in den Strom ziehen.

Kein Einmal-Spiegel wie bei baeume.py: jeder Lauf holt, was seit dem letzten
Mal neu war, und haengt genau diese Zeilen an. Zwei Quellen:

  1. Konto-Ereignisse (`gh api /users/<konto>/events`) — push/pr/issue/release/
     neu/geloescht, absteigend nach id. Die hoechste gesehene id ist der
     Wasserstand, kein Ereignis darunter wird zweimal geschrieben.
  2. Repo-Liste (`gh repo list ... pushedAt`) — Netz fuer Pushes, die aus dem
     Ereignisfenster schon rausgefallen sind (GitHub deckelt bei ~300
     Ereignissen / 90 Tagen, egal wie oft man blaettert).

Ohne GH_TOKEN kein Lauf. Kein gh-auth-Login auf diesem Host vorgesehen — das
Zeichen kommt von aussen, ueber die Umgebungsvariable oder eine
EnvironmentFile beim systemd-Service.

    github_strom.py abgleich     neue Ereignisse holen und anhaengen
    github_strom.py stand        letzter Stand je Repo, wie alt
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

KONTO = "gschaidergabriel"
STROM = Path("/var/lib/clay/ereignisse.jsonl")
STAND = Path("/var/lib/clay/github-stand.json")

# GitHub-Ereignistyp -> unser art-Feld. Was nicht hier drinsteht (Watch,
# Fork, Member, Comment, ...), wird beim Wasserstand mitgezaehlt, aber nicht
# als Zeile geschrieben — kein art-Wert dafuer vorgesehen, nichts erfinden.
ART = {
    "PushEvent": "push",
    "PullRequestEvent": "pr",
    "IssuesEvent": "issue",
    "ReleaseEvent": "release",
    "CreateEvent": "neu",
    "DeleteEvent": "geloescht",
}


def ereignis(instanz: str, art: str, **rest) -> None:
    e = {"zeit": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "wirt": "github",
         "instanz": instanz, "organ": "github", "art": art, **rest}
    STROM.parent.mkdir(parents=True, exist_ok=True)
    with STROM.open("a", encoding="utf-8") as f:
        f.write(json.dumps(e, ensure_ascii=False) + "\n")


def _gh(*args: str) -> str:
    p = subprocess.run(["gh", *args], capture_output=True, text=True)
    if p.returncode != 0:
        sys.exit(f"gh {' '.join(args)}: {p.stderr.strip()[:300]}")
    return p.stdout


def _pruefe_zugang() -> None:
    if os.environ.get("GH_TOKEN"):
        return
    p = subprocess.run(["gh", "auth", "status"], capture_output=True, text=True)
    if p.returncode != 0:
        sys.exit("Kein Zugang: GH_TOKEN ist nicht gesetzt und gh ist nicht "
                  "eingeloggt. export GH_TOKEN=<token> und erneut versuchen.")


def _lade_stand() -> dict:
    if STAND.exists():
        return json.loads(STAND.read_text(encoding="utf-8"))
    return {"letzte_event_id": "0", "repos": {}}


def _schreibe_stand(stand: dict) -> None:
    STAND.parent.mkdir(parents=True, exist_ok=True)
    STAND.write_text(json.dumps(stand, ensure_ascii=False, indent=2), encoding="utf-8")


def _repo_liste() -> list[dict]:
    out = _gh("repo", "list", KONTO, "--limit", "200", "--json", "name,pushedAt")
    return json.loads(out)


def _konto_ereignisse() -> list[dict]:
    # GitHub deckelt selbst: max ~300 Ereignisse / 90 Tage, egal wie viele Seiten.
    out = _gh("api", "--paginate", f"/users/{KONTO}/events?per_page=100")
    text = out.strip()
    if not text:
        return []
    # gh haengt bei --paginate mehrere JSON-Arrays direkt aneinander (]["),
    # wenn es mehr als eine Seite gab. Trennen, dann jedes Array einzeln laden.
    stuecke = text.replace("][", "]\x00[").split("\x00")
    alle: list[dict] = []
    for stueck in stuecke:
        alle.extend(json.loads(stueck))
    return alle


def _feld(payload: dict, *pfad, standard=None):
    d = payload
    for p in pfad:
        if not isinstance(d, dict) or p not in d:
            return standard
        d = d[p]
    return d


def abgleich(_argv: list[str]) -> None:
    _pruefe_zugang()
    stand = _lade_stand()
    letzte_id = int(stand.get("letzte_event_id", "0"))

    alle = _konto_ereignisse()
    # GitHub liefert neueste zuerst — fuer die richtige Reihenfolge im Strom
    # aufsteigend nach id verarbeiten.
    neu_events = sorted(
        (e for e in alle if int(e["id"]) > letzte_id),
        key=lambda e: int(e["id"]),
    )

    geschrieben = 0
    push_gesehen: set[str] = set()
    hoechste_id = letzte_id

    for e in neu_events:
        hoechste_id = max(hoechste_id, int(e["id"]))
        typ = e.get("type", "")
        repo_pfad = _feld(e, "repo", "name")
        if not repo_pfad:
            continue
        repo = repo_pfad.split("/")[-1]
        art = ART.get(typ)
        if art is None:
            continue  # WatchEvent, ForkEvent & co. — kein art-Wert vorgesehen

        payload = e.get("payload", {})
        rest: dict = {"repo": repo}

        if typ == "PushEvent":
            sha = _feld(payload, "head")
            if sha:
                rest["sha"] = sha[:12]
            commits = payload.get("commits") or []
            if commits:
                zeile = (commits[-1].get("message") or "").splitlines()
                if zeile:
                    rest["titel"] = zeile[0][:200]
            push_gesehen.add(repo)
        elif typ == "PullRequestEvent":
            nummer = _feld(payload, "number")
            if nummer is not None:
                rest["nummer"] = nummer
            titel = _feld(payload, "pull_request", "title")
            if titel:
                rest["titel"] = titel
        elif typ == "IssuesEvent":
            nummer = _feld(payload, "issue", "number")
            if nummer is not None:
                rest["nummer"] = nummer
            titel = _feld(payload, "issue", "title")
            if titel:
                rest["titel"] = titel
        elif typ == "ReleaseEvent":
            titel = _feld(payload, "release", "name") or _feld(payload, "release", "tag_name")
            if titel:
                rest["titel"] = titel
        elif typ in ("CreateEvent", "DeleteEvent"):
            ref_typ = payload.get("ref_type")
            ref = payload.get("ref")
            if ref_typ:
                rest["ref_typ"] = ref_typ
            if ref:
                rest["titel"] = ref

        ereignis(repo, art, **rest)
        geschrieben += 1

    # Netz: Pushes ausserhalb des Ereignisfensters ueber pushedAt nachziehen.
    for r in _repo_liste():
        name = r["name"]
        gepusht = r.get("pushedAt")
        bekannt = stand["repos"].get(name, {})
        alt_gepusht = bekannt.get("pushed_at")
        if gepusht and gepusht != alt_gepusht and name not in push_gesehen:
            ereignis(name, "push", repo=name)
            geschrieben += 1
        eintrag = dict(bekannt)
        eintrag["zuletzt_geprueft"] = time.strftime("%Y-%m-%dT%H:%M:%S%z")
        if gepusht:
            eintrag["pushed_at"] = gepusht
        stand["repos"][name] = eintrag

    stand["letzte_event_id"] = str(hoechste_id)
    _schreibe_stand(stand)
    print(f"neu: {geschrieben}  (Konto-Ereignisse geprueft: {len(neu_events)}, "
          f"Wasserstand jetzt {hoechste_id})")


def stand_zeigen(_argv: list[str]) -> None:
    s = _lade_stand()
    if not s["repos"]:
        print("Noch kein Abgleich gelaufen.")
        return
    jetzt = datetime.now(timezone.utc)
    print(f"\n{'REPO':<40} {'LETZTER PUSH':<22} {'ALTER':>8}")
    print("-" * 72)
    for name in sorted(s["repos"]):
        r = s["repos"][name]
        gepusht = r.get("pushed_at")
        if gepusht:
            try:
                t = datetime.fromisoformat(gepusht.replace("Z", "+00:00"))
                alter = f"{(jetzt - t).days}d"
            except ValueError:
                alter = "?"
        else:
            gepusht, alter = "—", "?"
        print(f"{name:<40} {gepusht:<22} {alter:>8}")
    print(f"\nWasserstand Konto-Ereignisse: id {s.get('letzte_event_id', '0')}\n")


if __name__ == "__main__":
    befehl = sys.argv[1] if len(sys.argv) > 1 else "stand"
    {"abgleich": abgleich, "stand": stand_zeigen}.get(
        befehl, lambda _a: sys.exit(f"Unbekannt: {befehl}"))(sys.argv[2:])
