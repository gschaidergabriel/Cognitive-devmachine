#!/usr/bin/env python3
"""udb/cli.py — CLI-Zugang zu UnifiedDB: Zustand, Neuronpedia, NVIDIA-Embeddings, Memory.

Kein Modellaufruf in zustand(); neuropedia/embeddings rufen echte externe
APIs auf (Kontingente beachten). Alle Schreibpfade gehen ueber neue Tabellen
(udb_nvidia_embedding, forschung_neuropedia, memory_tabelle) -- keine
bestehende Tabelle dieses Hauses wird hier veraendert.
"""
import argparse
import json
import sys
from pathlib import Path

repo_root = Path(__file__).parent.parent
sys.path.insert(0, str(repo_root))

from udb.abruf.zustand import zustand, zustand_json, zustand_text, verbindung, schreib_verbindung
from udb.abruf.neuropedia import (
    aktivierung_abrufen,
    clayverse_forschung_analyse,
    in_unifieddb_speichern as neuropedia_speichern,
    forschung_neuropedia_anzeigen,
    fehlt_schluessel as neuropedia_fehlt_schluessel,
)
from udb.abruf.nvidia_embedding import (
    embed_text,
    in_unifieddb_speichern as embedding_speichern,
    embedding_abrufen,
    vektor_suche,
)
from udb.abruf.memory_entitaet import MemoryEntitaet


def cmd_zustand(args):
    try:
        if args.format == "json":
            ergebnis = zustand_json(args.pfad)
        elif args.format == "text":
            ergebnis = zustand_text(args.pfad)
        else:
            ergebnis = json.dumps(zustand(args.pfad, voll=args.voll), indent=2, default=str, ensure_ascii=False)
        print(ergebnis)
        return 0
    except Exception as e:
        print(f"FEHLER: {e}", file=sys.stderr)
        return 1


def cmd_neuropedia(args):
    try:
        if neuropedia_fehlt_schluessel() and args.action != "anzeigen":
            print(json.dumps({"error": "NEUROPEDIA_API_KEY fehlt in der Tresordatei"}, ensure_ascii=False))
            return 1

        if args.action == "abrufen":
            a = aktivierung_abrufen(args.modell, args.source, args.index)
            print(json.dumps({
                "modell": a.model_id, "source": a.layer, "index": a.index,
                "tokens": a.tokens, "aktivierungen": a.activations,
                "max_aktivierung": a.max_value, "max_token_index": a.max_value_token_index,
                "max_token": a.tokens[a.max_value_token_index] if a.tokens else None,
                "was_gemessen": f"oeffentliches Forschungsmodell {a.model_id}, nicht Zero",
            }, indent=2, default=str, ensure_ascii=False))

        elif args.action == "speichern":
            a = aktivierung_abrufen(args.modell, args.source, args.index)
            c = schreib_verbindung(args.pfad)
            neuropedia_speichern(a, c, args.projekt)
            c.close()
            print(f"Aktivierung gespeichert: {a.model_id}/{a.layer}/{a.index}")

        elif args.action == "analysieren":
            indices = args.indices.split(",") if args.indices else [args.index]
            analyse = clayverse_forschung_analyse(args.modell, args.source, indices)
            print(json.dumps(analyse, indent=2, default=str, ensure_ascii=False))

        elif args.action == "anzeigen":
            c = verbindung(args.pfad)
            ergebnisse = forschung_neuropedia_anzeigen(c, args.limit)
            c.close()
            print(json.dumps(ergebnisse, indent=2, default=str, ensure_ascii=False))

        return 0
    except Exception as e:
        print(f"FEHLER: {e}", file=sys.stderr)
        return 1


def cmd_embeddings(args):
    try:
        if args.action == "erstellen":
            emb = embed_text(args.text, input_type="query")
            print(json.dumps({"text": args.text, "dimension": len(emb), "embedding_preview": emb[:5]},
                              indent=2, default=str, ensure_ascii=False))

        elif args.action == "speichern":
            emb = embed_text(args.text, input_type="passage")
            c = schreib_verbindung(args.pfad)
            embedding_speichern(args.artikel_id, emb, c)
            c.close()
            print(f"Embedding gespeichert: {args.artikel_id} ({len(emb)} dimensions)")

        elif args.action == "abrufen":
            c = verbindung(args.pfad)
            emb = embedding_abrufen(args.artikel_id, c)
            c.close()
            if emb:
                print(json.dumps({"artikel_id": args.artikel_id, "dimension": len(emb), "embedding_preview": emb[:5]},
                                  indent=2, default=str, ensure_ascii=False))
            else:
                print(json.dumps({"error": "Kein Embedding gefunden"}, ensure_ascii=False))

        elif args.action == "suche":
            c = verbindung(args.pfad)
            ergebnisse = vektor_suche(args.text, c, limit=args.limit)
            c.close()
            print(json.dumps({"query": args.text, "ergebnisse": ergebnisse}, indent=2, default=str, ensure_ascii=False))

        return 0
    except Exception as e:
        print(f"FEHLER: {e}", file=sys.stderr)
        return 1


def cmd_memory(args):
    try:
        me = MemoryEntitaet(args.pfad)
        if args.action == "hinzufuegen":
            ok = me.memory_hinzufuegen(args.artikel_id, args.text, quelle=args.quelle,
                                        priority=args.priority, tag=args.tag)
            print(f"Memory hinzugefuegt: {args.artikel_id} ({args.tag})" if ok else "FEHLER: nicht hinzugefuegt")
        elif args.action == "abrufen":
            print(json.dumps(me.memory_abrufen(args.artikel_id or None, args.tag or None, args.limit),
                              indent=2, default=str, ensure_ascii=False))
        elif args.action == "suche":
            print(json.dumps(me.memory_suche(args.suchbegriff, args.limit), indent=2, default=str, ensure_ascii=False))
        elif args.action == "statistik":
            print(json.dumps(me.memory_statistik(), indent=2, default=str, ensure_ascii=False))
        elif args.action == "loeschen":
            ok = me.memory_loeschen(args.memory_id)
            print(f"Memory geloescht: ID {args.memory_id}" if ok else "FEHLER: nicht geloescht")
        return 0
    except Exception as e:
        print(f"FEHLER: {e}", file=sys.stderr)
        return 1


def main():
    parser = argparse.ArgumentParser(description="UnifiedDB CLI")
    parser.add_argument("--pfad", default="/var/lib/clay/wiki.db")
    sub = parser.add_subparsers(dest="befehl")

    zp = sub.add_parser("zustand")
    zp.add_argument("--format", choices=["json", "dict", "text"], default="dict")
    zp.add_argument("--voll", action="store_true")
    zp.set_defaults(func=cmd_zustand)

    npp = sub.add_parser("neuropedia")
    npp.add_argument("action", choices=["abrufen", "speichern", "analysieren", "anzeigen"])
    npp.add_argument("--modell", default="gpt2-small")
    npp.add_argument("--source", default="9-res-jb")
    npp.add_argument("--index", default="200")
    npp.add_argument("--indices", default="")
    npp.add_argument("--projekt", default="clayverse")
    npp.add_argument("--limit", type=int, default=10)
    npp.set_defaults(func=cmd_neuropedia)

    ep = sub.add_parser("embeddings")
    ep.add_argument("action", choices=["erstellen", "speichern", "abrufen", "suche"])
    ep.add_argument("--text", default="")
    ep.add_argument("--artikel-id", dest="artikel_id", default="")
    ep.add_argument("--limit", type=int, default=5)
    ep.set_defaults(func=cmd_embeddings)

    mp = sub.add_parser("memory")
    mp.add_argument("action", choices=["hinzufuegen", "abrufen", "suche", "statistik", "loeschen"])
    mp.add_argument("--artikel-id", dest="artikel_id", default="")
    mp.add_argument("--text", default="")
    mp.add_argument("--quelle", default="")
    mp.add_argument("--priority", type=float, default=1.0)
    mp.add_argument("--tag", default="")
    mp.add_argument("--suchbegriff", default="")
    mp.add_argument("--limit", type=int, default=10)
    mp.add_argument("--memory-id", dest="memory_id", type=int, default=0)
    mp.set_defaults(func=cmd_memory)

    args = parser.parse_args()
    if not args.befehl:
        parser.print_help()
        return 1
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
