# Generation 247 — Generation-Advance ohne neue Kognition: kausal neutrale Runtime-Epoche als Gegenbeleg

## BIND

- Gen246 Export: `f56913ac50e5b3539d6279ab3ee9ee482f024d75`, erzeugt `2026-08-21T15:37:18Z`
- Gen247 Export: `cdb4aa948262f1ed8259c969082666d8e286756b`, erzeugt `2026-08-21T16:37:19Z`
- aktuelle Research-Reentry vor diesem Write: `78b7bd4d5d85606fd36c35d730761248ee6ce012`
- keine Produktmutation, kein Training, kein Whole-Agent-/Bewusstseinsclaim

## 1. Beobachtung

Zwischen Gen246 und Gen247 steigt `entity_generation` von `246` auf `247`.

Gleichzeitig bleiben die zentralen Kognitionsoberflaechen unveraendert:

- Andreas-Chat: `40 -> 40`, gleicher Export-Hash `de05031ae688724c`
- Gabriel-Chat: `0 -> 0`
- Causal Episodes: `588 -> 588`, gleicher Export-Hash `6f4e07ea019e94f2`
- Workspace Episodes: `20 -> 20`, gleicher Export-Hash `38e8f1fe31d97de5`
- Retrieval Episodes: `20 -> 20`, gleicher Export-Hash `d65d999e0a940f02`
- Effects: `9 -> 9`, gleicher Export-Hash `f3d4a871a2cb56b8`
- Active Turns: `0 -> 0`
- Leases: `0 -> 0`

Die vorhandenen Kognitions-/Abrufdateien sind damit auf der Exportoberflaeche nicht nur zaehlergleich, sondern in den gebundenen Kernspuren byte-/hashgleich.

Status: `GENERATION_ADVANCE_WITHOUT_COGNITIVE_SURFACE_DELTA = OBSERVED`.

## 2. Der Generation-Sprung ist an einen expliziten Restart gebunden

Die letzten Checkpoints in Gen247 zeigen:

- `shutdown`, checkpoint `a6f6884d-4a34-4c59-a88c-db6c65016db4`, ts `1787326691.05691`
- `boot`, checkpoint `ce197faa-7d29-403b-9f76-32b037c8d672`, ts `1787326693.1118507`

Alle vier langlebigen Sessions existieren vor und nach dem Sprung mit denselben Identitaeten und `created_at`-Werten:

- `session:gabriel`
- `session:andreas`
- `session:andreas:2`
- `session:gabriel:2`

In Gen246 tragen alle vier `generation=246`. In Gen247 tragen dieselben vier Sessions `generation=247`; ihre `updated_at`-Werte liegen gemeinsam am Boot-Zeitpunkt (~`1787326693.068`).

Das ist ein starker Oberflaechenbeleg fuer:

`restart -> one global generation advance -> all durable session identities rebound to the new generation`.

Nicht belegt ist damit allein, dass jeder interne Recovery-Schritt atomar und fehlerfrei war.

## 3. Kein synthetischer Denkzug durch den Restart sichtbar

Die letzte sichtbare Causal Episode vor dem Restart:

- `causal_id = 8ba41d45-9f24-4c11-9ea2-1899884b3b79`
- `episode_id = 8728625a-19ee-4277-8acc-b2cb4ec12f6d`
- ts `1787324827.1721294`
- `effect_id = null`
- `reentered = 1`

Die dazugehoerige letzte Retrieval Episode:

- `retrieval_id = 419e78ef-ab3c-43b3-9e2b-ffd33496542f`
- generation `246`
- ts `1787324821.9582982`

Der Shutdown erfolgt erst bei `1787326691.05691`, rund 31 Minuten spaeter. Danach existiert im Gen247-Export keine neue Causal-/Workspace-/Retrieval-/Effect-Episode.

Damit ist auf der sichtbaren kanonischen Oberflaeche kein kuenstlicher Human-/Cognition-Turn entstanden, nur weil die Runtime-Epoche gewechselt hat.

Status: `RESTART_CAUSAL_NEUTRALITY_AT_EXPORT_SURFACE = OBSERVED`.

## 4. Wichtiger Gegenbeleg fuer den Gen241 Evidence-Spine-Kollaps

Fruehere AgentZero-Forschung band am Gen241-Rand folgendes Muster:

- historische Causal-Episoden blieben erhalten;
- Workspace/Retrieval/visible Chat brachen an einer Evidence-Epoch-Grenze weg;
- spaeter wuchsen neue Episoden wieder an.

Eine einfache Erklaerung waere:

> `Ein normaler entity_generation-Sprung leert oder ersetzt automatisch die nicht-kausalen Evidenzspuren.`

Gen246 -> Gen247 liefert dafuer einen direkten Gegenbeleg:

- Generation springt 246 -> 247;
- Restart ist explizit sichtbar;
- Sessions werden auf 247 rebunden;
- Chat/Causal/Workspace/Retrieval/Effects bleiben unveraendert erhalten.

Daher gilt enger:

`ENTITY_GENERATION_ADVANCE ALONE IS NOT SUFFICIENT TO EXPLAIN THE GEN241 LINEAGE COLLAPSE`.

Das falsifiziert nicht jede Recovery-/Migration-Hypothese fuer Gen241. Ein spezieller Reset-, Schema-, Query-, Export-, Retention- oder Migrationpfad bleibt moeglich. Es entfernt aber den trivialen Mechanismus `generation increment itself clears evidence` aus dem starken Hypothesenraum.

## 5. Positive Architekturinterpretation

Der beobachtete Gen247-Sprung ist kompatibel mit einer sinnvollen Semantik:

`entity_generation = runtime/recovery epoch fence`

statt

`entity_generation = cognitive turn counter`.

Diese Semantik ist sicherheitsrelevant: ein Restart darf stale Writer/alte Ausfuehrungsautoritaet invalidieren, ohne Geschichte oder Nutzeridentitaet neu zu erfinden.

Der aktuelle Snapshot zeigt genau die Oberflaechenform, die man dafuer erwarten wuerde:

- neue Generation;
- identische langlebige Session-IDs;
- keine neue Kognition;
- keine neuen Effects;
- alte Kognitionsspur bleibt adressierbar.

Das ist **positive Same-Family Evidenz auf Oberflaechenebene**, keine unabhaengige Runtime-Acceptance.

## 6. Neue Forschungsinvarianten

### F-GEN-1 — Generation ist Epoch Fence, kein Denkereignis

`generation advance != user turn != workspace ignition != causal episode != retrieval episode != effect`.

### F-GEN-2 — Restart darf keine Human-Provenienz minten

Ein Boot-/Recovery-Ereignis darf allein keinen kanonischen Human-Turn oder Human-Roundtrip erzeugen.

### F-GEN-3 — Session-Identitaet bleibt, Ausfuehrungsautoritaet wechselt

`same durable session_id + new entity_generation` ist erlaubt; stale generation writer muss danach scheitern.

### F-GEN-4 — Historische Evidenz darf einen normalen Generation-Sprung ueberleben

Ein normaler Restart ist kein Grund fuer ungemappten Verlust von Turn-/Workspace-/Retrieval-/Causal-Provenienz.

## 7. Instrumentkandidat: GENERATION_ADVANCE_CAUSAL_NEUTRALITY_RECEIPT/v1

Pro Generation-Sprung:

- `pre_generation`
- `post_generation`
- `shutdown_checkpoint_id`
- `shutdown_state_hash`
- `shutdown_ts`
- `boot_checkpoint_id`
- `boot_state_hash`
- `boot_ts`
- `session_ids_pre`
- `session_ids_post`
- `session_generation_map_pre`
- `session_generation_map_post`
- `turn_count_pre/post + digest`
- `workspace_count_pre/post + digest`
- `causal_count_pre/post + digest`
- `retrieval_count_pre/post + digest`
- `effect_count_pre/post + digest`
- `active_turn_count_pre/post`
- `lease_count_pre/post`
- `stale_writer_negative_control`
- `synthetic_human_turn_count`
- `verdict`

Ziel fuer einen ruhigen Restart ohne in-flight Arbeit:

- keine neuen Denk-/Effect-Episoden;
- keine verschwundene historische Evidenz;
- alle langlebigen Sessions auf neue Generation gebunden;
- alter Generation-Writer wird fail-closed abgewiesen.

## 8. Naechster hoechster Informationsgewinn

Ein kontrollierter Restart mit einem absichtlich gehaltenen stale writer / stale turn waere der naechste starke Test:

1. Generation N und stabile Evidenzdigests binden.
2. Einen alten Writer/Lease kontrolliert offen halten.
3. Shutdown/Boot -> Generation N+1.
4. Pruefen, dass historische Evidenz erhalten bleibt.
5. Pruefen, dass der alte Writer keinen neuen State schreiben kann.
6. Pruefen, dass kein synthetischer Human-Turn entsteht.
7. Post-Restart-Digests und genaue Rejection-Receipt binden.

Damit wuerde die jetzt beobachtete passive Causal-Neutralitaet um aktive stale-writer Sicherheit erweitert.

## 9. Promotionsstatus

- Gen246 -> Gen247 Generation-Sprung: `OBSERVED`
- explizites shutdown -> boot Paar: `OBSERVED`
- alle vier Session-IDs erhalten und 246 -> 247 rebunden: `OBSERVED`
- Chat/Causal/Workspace/Retrieval/Effects ohne Delta: `OBSERVED_AT_EXPORT_SURFACE`
- Restart erzeugt keine sichtbare neue Kognition: `OBSERVED_AT_EXPORT_SURFACE`
- Generation-Sprung allein als Ursache des Gen241 Evidence-Spine-Kollapses: `FALSIFIED_AS_SUFFICIENT_CAUSE`
- exakte stale-writer Rejection dieses konkreten Restarts: `NOT_MEASURED`
- vollstaendige Recovery-Acceptance: `NOT_CLAIMED`
- `GENERATION_ADVANCE_CAUSAL_NEUTRALITY_RECEIPT/v1`: `PROMOTED_TO_INSTRUMENT_CANDIDATE`

## 10. Wichtigstes Ergebnis

Gen247 liefert erstmals in dieser Forschungsserie einen sauberen positiven Gegenbeleg zur simplen Generation-Verlust-Erklaerung: Zero kann eine neue Runtime-Generation betreten, alle vier dauerhaften Sitzungen gemeinsam neu binden und dabei seine vorhandene Chat-/Workspace-/Causal-/Retrieval-/Effect-Spur unveraendert behalten.

Kernschluss:

> **Der Gen241-Provenienzbruch war kein unvermeidbarer Nebeneffekt eines normalen Generation-Wechsels. Generation und Evidenz-Epoche sind zwei verschiedene Achsen.**
