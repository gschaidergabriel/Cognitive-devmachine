# EntityOS -- Architekturskizze

**Automatisch abgeleitet, nicht gepflegt.** Erzeugt 2026-08-20T04:11:13Z aus dem gemessenen
Zustand auf `frank-api`. Eine handgepflegte Skizze weicht nach zwei Wochen vom Code
ab und luegt dann still; diese kann das nicht, weil sie bei jedem Lauf neu aus Code,
Datenbank und laufenden Diensten entsteht.

## Die vier Namen

| Name | Was es ist |
|---|---|
| **EntityOS** | das Betriebssystem, der Container, das Produkt, das Frontend |
| **Zero** | die Entitaet selbst. Agent Zero. Wer im Terminal antwortet |
| **ClayCode** | Zeros Werkzeug, unveraendert |
| **Clay** | der Unterbau: Korpus, Graph, die vier Dienste |

## Der Weg eines Satzes

```mermaid
flowchart TD
    M[Mensch im Browser] -->|Clerk-Anmeldung| N[nginx TLS auf 72.61.19.188]
    N -->|WebSocket + SSH-Tunnel| S[EntityOS-Container auf frank-api]
    S -->|UserPromptSubmit-Haken| T[TurnLifecycle: Zug aufnehmen]
    T --> W[WorldAssembler]
    W --> A[Abruf-Entitaet MicroClay]
    W --> K[(Clay-Korpus: Artikel, Kanten, Lesarten)]
    W --> I[Kanonische Identitaet Ebene 0]
    T --> C[Zero = Claude Code in tmux]
    C -->|MCP| E{EffectGate}
    E -->|Urteil| J[(EffectJournal)]
    C -->|Stop-Haken| T
    T --> D[(UnifiedDB = wiki.db)]
    P[Autonomie-Puls 30s] -->|next_runnable| T
```

## Gemessener Bestand

| | |
|---|---|
| Produktmodule | 56 Dateien, 16135 Zeilen |
| Testdateien | 125 |
| Tabellen in der UnifiedDB | 132 |
| Artikel im Korpus | 18019 |
| Kanten | 117793 |
| Lesarten | 22567 |
| Zuege von Zero | 180 |
| Wirkungen durch das Tor | 3 |
| Abrufepisoden | 90 |
| gelernte Eintrittspunkte | 27 |
| Entitaetsgeneration | 182 |

## Laufende Clay-Dienste

```
clayverse-kern.service
clayverse-puls.service
clayverse-wikiarbeit.service
```

## Container

```
entityos:latest | user 5001:5001 | {"3000/tcp":[{"HostIp":"127.0.0.1","HostPort":"3000"}]}
```

## Werkzeuge, die Zero erreichen kann

```
(keine ermittelt)
```

## Ein Gefaess, zwei Schichten

Die Laufzeit-Wirbelsaeule (Zuege, Sitzungen, Wirkungen, Kausalitaet,
Abruf-Lernen) liegt in **derselben Datei** wie der Clay-Korpus. Keine
Namenskollision, gemessen. Die vier Clay-Dienste schreiben unveraendert weiter,
die Entitaet schreibt daneben -- eine Wahrheit, kein zweites Gedaechtnis.
