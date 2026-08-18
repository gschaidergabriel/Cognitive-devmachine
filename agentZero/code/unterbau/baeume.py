#!/usr/bin/env python3
"""baeume.py — das GitHub-Konto als Bäume ins Zentralrepo ziehen.

Ein Unterordner je eigenem Repo, wie bei Chronik. Auf dem Server liegt alles
zusammen, ist aber einzeln auslesbar: `git log -- baeume/<name>/`.

Drei Regeln, die hier eingebaut sind:

  1. **Fremde Upstreams kommen nicht hinein.** Ein Fork von KDE/krita ist
     9 GB Fremdcode; er wird als Verweis vermerkt, nicht gespiegelt. Sonst
     schleppt jeder Klon ihn mit.
  2. **Kein .git im .git.** Die Bäume sind Dateibestände, keine verschachtelten
     Repos — sonst sieht git im Zentralrepo nur einen leeren Ordner.
  3. **Jeder Lauf erzeugt ein Ereignis** mit wirt/instanz/organ. Was nicht im
     Strom steht, ist nicht passiert.

    baeume.py holen      alle eigenen Repos spiegeln
    baeume.py stand      was liegt da, wie alt
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

REPO = Path("/opt/clayverse")
BAEUME = REPO / "baeume"
STROM = Path("/var/lib/clay/ereignisse.jsonl")
ZWISCHEN = Path("/var/lib/clay/klone")

# Fremde Upstreams: nur vermerken, nie spiegeln.
FREMD = {"krita"}


def ereignis(art: str, **rest) -> None:
    e = {"zeit": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "wirt": "clayverse",
         "instanz": "baeume", "organ": "zentralrepo", "art": art, **rest}
    try:
        STROM.parent.mkdir(parents=True, exist_ok=True)
        with STROM.open("a", encoding="utf-8") as f:
            f.write(json.dumps(e, ensure_ascii=False) + "\n")
    except Exception:
        pass


def _lauf(*args, cwd=None, still=True):
    return subprocess.run(args, cwd=cwd, capture_output=still, text=True)


def repos() -> list[dict]:
    p = _lauf("gh", "repo", "list", "--limit", "200", "--json",
              "name,visibility,isFork,parent,pushedAt,diskUsage")
    if p.returncode != 0:
        sys.exit(f"gh: {p.stderr.strip()[:200]}")
    return json.loads(p.stdout)


def holen() -> None:
    BAEUME.mkdir(parents=True, exist_ok=True)
    ZWISCHEN.mkdir(parents=True, exist_ok=True)
    alle = repos()
    verweise, geholt, unveraendert, fehler = [], [], [], []

    for r in alle:
        name = r["name"]
        if name in FREMD or r.get("isFork"):
            verweise.append({
                "name": name,
                "upstream": (r.get("parent") or {}).get("nameWithOwner", "unbekannt"),
                "groesse_mb": round((r.get("diskUsage") or 0) / 1024, 1),
                "grund": "fremder Upstream — Verweis statt Kopie",
            })
            continue

        klon = ZWISCHEN / name
        try:
            if klon.exists():
                p = _lauf("git", "-C", str(klon), "pull", "--ff-only", "-q")
                if p.returncode != 0:
                    _lauf("git", "-C", str(klon), "fetch", "--all", "-q")
                    _lauf("git", "-C", str(klon), "reset", "--hard", "-q", "origin/HEAD")
            else:
                p = _lauf("gh", "repo", "clone", f"gschaidergabriel/{name}",
                          str(klon), "--", "--depth", "1", "-q")
                if p.returncode != 0:
                    fehler.append((name, p.stderr.strip()[:120]))
                    continue

            ziel = BAEUME / name
            neu = not ziel.exists()
            # Dateibestand spiegeln, .git bleibt draußen (Regel 2)
            p = _lauf("rsync", "-a", "--delete", "--exclude", ".git",
                      f"{klon}/", f"{ziel}/")
            if p.returncode != 0:
                fehler.append((name, "rsync fehlgeschlagen"))
                continue
            (geholt if neu else unveraendert).append(name)
        except Exception as e:
            fehler.append((name, str(e)[:120]))

    (BAEUME / "VERWEISE.json").write_text(
        json.dumps({"erzeugt": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
                    "hinweis": "Fremde Upstreams werden nicht gespiegelt.",
                    "verweise": verweise}, ensure_ascii=False, indent=2),
        encoding="utf-8")

    _lauf("git", "-C", str(REPO), "add", "-A")
    p = _lauf("git", "-C", str(REPO), "commit", "-q", "-m",
              f"Bäume: {len(geholt)} neu, {len(unveraendert)} aktualisiert, "
              f"{len(verweise)} als Verweis")
    _lauf("git", "-C", str(REPO), "push", "-q", "origin", "HEAD")

    ereignis("gespiegelt", neu=len(geholt), aktualisiert=len(unveraendert),
             verweise=len(verweise), fehler=len(fehler))

    print(f"  neu:          {len(geholt)}  {' '.join(geholt[:6])}")
    print(f"  aktualisiert: {len(unveraendert)}")
    print(f"  als Verweis:  {len(verweise)}  " +
          " ".join(f"{v['name']}({v['groesse_mb']}MB)" for v in verweise))
    for n, g in fehler:
        print(f"  FEHLER {n}: {g}")
    groesse = sum(f.stat().st_size for f in BAEUME.rglob("*") if f.is_file())
    print(f"  Baumbestand:  {groesse/1024/1024:.0f} MB")


def stand() -> None:
    if not BAEUME.exists():
        print("Noch keine Bäume."); return
    print(f"\n{'BAUM':<38} {'MB':>8}  {'DATEIEN':>8}")
    print("-" * 60)
    for d in sorted(p for p in BAEUME.iterdir() if p.is_dir()):
        dateien = [f for f in d.rglob("*") if f.is_file()]
        mb = sum(f.stat().st_size for f in dateien) / 1024 / 1024
        print(f"{d.name:<38} {mb:>8.1f}  {len(dateien):>8}")
    v = BAEUME / "VERWEISE.json"
    if v.exists():
        d = json.loads(v.read_text(encoding="utf-8"))
        for x in d.get("verweise", []):
            print(f"{x['name']:<38} {'—':>8}  Verweis auf {x['upstream']} ({x['groesse_mb']} MB)")
    print()


if __name__ == "__main__":
    {"holen": holen, "stand": stand}.get(
        sys.argv[1] if len(sys.argv) > 1 else "stand", stand)()
