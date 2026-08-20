import sys, time, signal, json
sys.path.append("/opt/unifieddb")
from udb.abruf.paket import paket

class Zeit(Exception): pass
def wecker(*a): raise Zeit()
signal.signal(signal.SIGALRM, wecker)

FRAGEN = [
    "warum haben herzrad.at und leihmich.org eigene wurzeln im webserver?",
    "warum muss der browser-daemon nach einem seimensch-test gestoppt werden?",
    "in welchem verzeichnis liegt die arbeitskopie von seimensch?",
    "wo muss ein neuer leihmich-slug eingetragen werden?",
]
for f in FRAGEN:
    t0 = time.time(); signal.alarm(90)
    try:
        r = paket(f, budget=6, wirt="latenzmessung")
        signal.alarm(0)
        print(f"  {time.time()-t0:7.1f}s  {len(r.get('treffer') or [])} Treffer  {f[:52]}", flush=True)
    except Zeit:
        signal.alarm(0)
        print(f"  >90.0s  ABBRUCH                {f[:52]}", flush=True)
    except Exception as e:
        signal.alarm(0)
        print(f"  {time.time()-t0:7.1f}s  FEHLER {type(e).__name__}  {f[:44]}", flush=True)
