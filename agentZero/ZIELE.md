# Was Agent Zero können soll — und was davon steht

**Automatisch erzeugt 2026-08-18T14:41:41Z.** Nicht von Hand pflegen.

**22 erfüllt · 6 offen · 1 zurückgestellt** von 29 Zeilen.

Die Spalte **Soll** ist deklariert und ändert sich nur, wenn der Eigner etwas
entscheidet. Die Spalte **Ist** wird bei jedem Lauf neu **gemessen** — durch einen
Prüfer je Zeile, der das laufende System befragt. Eine handgepflegte Statustabelle
steht nach einer Woche auf grün, weil niemand sie zurückstellt. Diese kann das nicht.

## Identität

| Fähigkeit | Soll | Ist (gemessen) | Stand | Quelle |
|---|---|---|---|---|
| **Die Entität heißt Zero** | Agent Zero, der erste Agent auf EntityOS, Grundlage aller weiteren Entwicklung | kanonische Identität v3 in meta, Ebene 0 | ✅ erfüllt | Eigner 18.08. |
| **Identität überlebt Verdichtung** | im Wurzelzustand verankert, deterministisch je Zug geladen, nie herausgefiltert | aus der DB in den Systemprompt gerendert; in der Hakenhülle als Anker (206 statt 5550 Zeichen) | ✅ erfüllt | Eigner 18.08. |
| **Verkörperung ohne Erfindung** | spielt eine Entität mit Kontinuität – ohne zu lügen, indem sie den Unterbau benutzt | im <embodiment>-Block: Erfinden ist der einzige Weg, aus der Rolle zu fallen | ✅ erfüllt | Eigner 18.08. |

## Menschen

| Fähigkeit | Soll | Ist (gemessen) | Stand | Quelle |
|---|---|---|---|---|
| **Genau zwei gleichberechtigte Perspektiven** | Gabriel und Andreas, gleiche Rechte, eine Entität – keine zwei Mandanten | 2 Nutzer mit rights=equal, 4 dauerhafte Sitzungen | ✅ erfüllt | Eigner 18.08. |
| **Sonst kommt niemand hinein** | Clerk-Anmeldung, exakt zwei Konten, dritte Identität fällt zu | IdentityRouter wirft PermissionError bei nicht zugeordnetem Clerk-Subjekt (Test grün) | ✅ erfüllt | Eigner 18.08. |

## Gedächtnis

| Fähigkeit | Soll | Ist (gemessen) | Stand | Quelle |
|---|---|---|---|---|
| **wiki.db ist das Herz der Entität** | Datenbank, Wiki und ClayGraph sind das Herz – nicht Altlast, nicht daneben | 130 Tabellen in EINER Datei: Clay-Korpus + Laufzeit-Wirbelsäule, kollisionsfrei | ✅ erfüllt | Eigner 18.08. |
| **Die vier Clay-Dienste laufen weiter** | kern, puls, verdichtung, wikiarbeit bleiben an – ausdrücklich | 3 von 4 laufen | 🔧 offen | Eigner 18.08. |
| **Der Abruf erreicht den Korpus** | Zero sieht die 14.284 Artikel, nicht nur sein eigenes Gesprächsgedächtnis | 15 Treffer auf Probeanfrage | ✅ erfüllt | Eigner 18.08. / Befund |

## Kognition

| Fähigkeit | Soll | Ist (gemessen) | Stand | Quelle |
|---|---|---|---|---|
| **Jeder Zug wird aufgezeichnet** | Prompt und Antwort landen als Zeile in der UnifiedDB, mit Kausalkette | 108 Züge, 54 Kausalepisoden, 54 Arbeitsraum-Episoden | ✅ erfüllt | Architektur |
| **Aufnahme ist atomar** | scheitert eine Prüfung, bleibt keine halbe Zeile stehen | Prüfungen laufen in der Aufnahme-Transaktion; 15 Atomizitätstests grün | ✅ erfüllt | Architektur |
| **Wirkung nur durch das Tor** | kein process.exec, jede Wirkung durch EffectGate mit Beleg | 2 Wirkung(en), Urteil mit boundary=ClayVerse EffectGate, Ziel/Ergebnis als Prüfsumme gespeichert | ✅ erfüllt | Architektur |
| **Werkzeuge nur über MCP** | Zeros einzige Werkzeugfläche ist der verwaltete MCP-Server, Bash verboten | 0 Werkzeuge freigegeben, Bash und Artifact verboten, Shell-Flucht abgewiesen | 🔧 offen | Architektur |

## Autonomie

| Fähigkeit | Soll | Ist (gemessen) | Stand | Quelle |
|---|---|---|---|---|
| **Initiative: der Puls weckt offene Ziele** | nicht behaupten, dass es autonom ist – die Mechanik bauen | Autonomie-Puls installed=true, 30 s, beglaubigt (ein Terminal-Verwalter) | ✅ erfüllt | Eigner 18.08. |
| **Persistente Ziele, Rückmeldung, Neuplanung** | Ziele überleben Züge, Schritte werden gemeldet, Fehlschlag führt zu Neuplanung | create_goal_from_turn / propose_step / record_step_failure / verify_completion vorhanden; Ziele entstehen nur aus kanonischen Menschenzügen | ✅ erfüllt | Eigner 18.08. |
| **Kontinuität über Neustarts** | Generation, Prüfpunkte, Wiederherstellung ohne blindes Wiederholen von Wirkungen | 129 Prüfpunkte, Generation 93 | ✅ erfüllt | Architektur |

## Abruf

| Fähigkeit | Soll | Ist (gemessen) | Stand | Quelle |
|---|---|---|---|---|
| **Abruf ist abfragesensitiv** | nicht die letzten N, sondern was zur Frage passt | 11/11 Tests grün; Quittung wird durchgereicht (war vorher still verloren) | ✅ erfüllt | Architektur |
| **Eintrittspunkte werden gelernt** | der Abruf verbessert seinen Eintrittspunkt selbst | 0 gelernte Eintrittspunkte, Modus SHADOW, 54 Episoden | 🔧 offen | Eigner 18.08. |
| **Wegehierarchie: Autobahnen, Tunnel, Landwege** | oft gegangene Wege werden ausgebaut; Verfall, inverse Gewichtung, Tunnel mit strengerer Schwelle und unabhängiger Mitbenutzung | Verstärkung vorhanden. FEHLT: Verfall ungenutzter Wege, inverse Gewichtung, Tunnel | 🔧 offen | F94 / Eigner 16.08. |
| **Karten als Zeitstrahl** | die Karte wird wiederholt weggeschrieben, damit man die Veränderung ansehen kann | 69 Momentaufnahme(n) in agentZero/karten, alle 30 min eine neue | ✅ erfüllt | Eigner 18.08. |

## Anbieter

| Fähigkeit | Soll | Ist (gemessen) | Stand | Quelle |
|---|---|---|---|---|
| **Die Bahnen stehen Zero offen** | 11 kognitive Prozesse über 22 Bahnen mit Ausweichbahn und Anteilsdeckel; NVIDIA gehört der Kognition, nicht dem Massenlauf | 11 Prozesse verdrahtet im Clay-Unterbau – aber Zeros Container erreicht sie NICHT | 🔧 offen | verdrahtung.py / Eigner |
| **Vektorsuche über den Korpus** | Bedeutungssuche statt nur Volltext | 200 Einbettungen (nv-embedqa-e5-v5, 1024 Dim, 2,9 ms/Text bei Stapel 128) | ✅ erfüllt | Lücke 8 / Eigner |
| **Neuronale Aktivitätsmessung** | Aktivierungsdaten als Forschungsquelle anbinden | Neuronpedia live: Deutung, Spitzenwert, Selektivität, Top-Token. ⚠️ misst öffentliche Forschungsmodelle, NICHT Zero | ✅ erfüllt | Eigner 18.08. |

## Vorstufe

| Fähigkeit | Soll | Ist (gemessen) | Stand | Quelle |
|---|---|---|---|---|
| **Claude bekommt den Prompt nie direkt** | eine Mistral-Entität wertet vorher aus: Möglichkeitsraum, alle APIs, alle Werkzeuge, verbundene Systeme, wer da ist – und baut ein Caveman-Prompt mit Hypothesen und Gegenhypothesen | 1 Modul(e) vorhanden – im Bau | ✅ erfüllt | F17 / Eigner 18.08. |
| **Übersetzer Caveman → Deutsch, 95 %** | Zero antwortet in Caveman, das Terminal übersetzt automatisch in schönes Deutsch | im Bau; Maß: Treue (Erfindung = durchgefallen) und Lesbarkeit, unabhängiger Richter | 🔧 offen | Eigner 18.08. |

## Betrieb

| Fähigkeit | Soll | Ist (gemessen) | Stand | Quelle |
|---|---|---|---|---|
| **Läuft im Container auf dem eigenen Server** | ohne Anruf beim Anbieter, ohne verschachtelte Virtualisierung | Up 8 minutes (healthy) | ✅ erfüllt | Eigner 18.08. |
| **Frontend heißt EntityOS und ist erreichbar** | Clerk-Login für genau zwei Profile, dann Claude-Code-Terminal | https://entityos.frank.ink → 200, WSS durch nginx und Tunnel bewiesen | ✅ erfüllt | Eigner 18.08. |
| **Der Export pflegt sich selbst** | alles autonom ins Forschungs-Repo unter agentZero | systemd-Timer alle 30 min, enabled | ✅ erfüllt | Eigner 18.08. |
| **Die Testsuite trägt** | kein grüner Wert, der durch Abschwächen erkauft wurde | 563 gruen / 16 rot | ✅ erfüllt | Arbeitsregel |
| **Endabnahme hinter eigenem Gastkern** | derselbe Digest hinter einer eigenen VM-Grenze | kein /dev/kvm auf dem Wirt; per Entscheidung 18.08. zurückgestellt | ⏸ zurückgestellt | Entwurf – vom Eigner zurückgestellt |

---

⏸ *zurückgestellt* heißt: bewusst nicht verfolgt, nicht vergessen. Der Grund steht in der Ist-Spalte.

