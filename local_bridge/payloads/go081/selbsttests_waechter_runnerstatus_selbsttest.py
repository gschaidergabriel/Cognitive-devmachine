#!/usr/bin/env python3
"""GO081: Runner-only rc changes must be persisted and reported by the watcher."""
from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

W = Path(__file__).resolve().parent
WAECHTER = W / "selbsttests-waechter.py"

bestanden = 0
gefallen = 0


def pruefe(cond: bool, text: str) -> None:
    global bestanden, gefallen
    if cond:
        bestanden += 1
        print(f"  ok    {text}")
    else:
        gefallen += 1
        print(f"  FEHLER  {text}")


def runner(path: Path, rc: int) -> Path:
    path.write_text(
        "#!/usr/bin/env bash\n"
        "printf '#ERG\\teins\\t0\\n'\n"
        "printf '#ERG\\tzwei\\t0\\n'\n"
        "printf '#SATZ\\t2/2\\n'\n"
        f"exit {rc}\n",
        encoding="utf-8",
    )
    path.chmod(0o755)
    return path


def run(laeufer: Path, verlauf: Path, meldung: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(WAECHTER), "--laeufer", str(laeufer),
         "--verlauf", str(verlauf), "--meldung", str(meldung),
         "--zeitgrenze", "10"],
        capture_output=True, text=True, timeout=30,
    )


print("Selbsttest Runnerstatus im Selbsttest-Waechter -- GO081\n")
with tempfile.TemporaryDirectory(prefix="go081-runnerstatus-") as td:
    t = Path(td)
    v = t / "verlauf.tsv"
    m = t / "meldung.txt"
    okr = runner(t / "ok.sh", 0)
    badr = runner(t / "rc5.sh", 5)

    r1 = run(okr, v, m)
    pruefe(r1.returncode == 0, f"R1 Grundlinie rc=0 (war {r1.returncode})")
    header = v.read_text(encoding="utf-8").splitlines()[0].split("\t")
    pruefe("laeufer" in header, "R2 Verlauf hat stabile Spalte 'laeufer'")

    r2 = run(badr, v, m)
    text = m.read_text(encoding="utf-8") if m.exists() else ""
    pruefe(r2.returncode == 2, f"R3 runner rc5 bleibt BEFUND rc=2 (war {r2.returncode})")
    pruefe("laeufer: ok -> rc5" in text,
           "R4 rc0->rc5 wird als AENDERUNG gemeldet")

    before = len(text)
    r3 = run(badr, v, m)
    text2 = m.read_text(encoding="utf-8") if m.exists() else ""
    pruefe(r3.returncode == 2, "R5 gleicher rc5 bleibt rot")
    pruefe(len(text2) == before,
           "R6 unveraenderter rc5 erzeugt keine doppelte Meldung")

    r4 = run(okr, v, m)
    text3 = m.read_text(encoding="utf-8") if m.exists() else ""
    pruefe(r4.returncode == 0, f"R7 Erholung auf runner rc0 wird wieder gruen (war {r4.returncode})")
    pruefe("laeufer: rc5 -> ok" in text3,
           "R8 Erholung rc5->ok wird als AENDERUNG gemeldet")

print(f"\n{bestanden} bestanden, {gefallen} gefallen")
sys.exit(1 if gefallen else 0)
