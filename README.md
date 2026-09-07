# VU+ HID Raw Remote

## Inhaltsverzeichnis

- [Überblick](#überblick)
- [Voraussetzungen und Berechtigungen](#voraussetzungen-und-berechtigungen)
- [Sprachen](#sprachen)
- [Installation](#installation)
- [Funktionsumfang](#funktionsumfang)
- [Geräteinformationen](#geräteinformationen)
- [Diagnose-Entitäten](#diagnose-entitäten)
- [Einrichtung](#einrichtung)
- [Bluetooth-Kopplung](#bluetooth-kopplung)
- [Entkoppeln beim Löschen](#entkoppeln-beim-löschen)
- [Events](#events)
- [Automationen](#automationen)
- [Kurz- und Langdruck](#kurz--und-langdruck)
- [Reconnect](#reconnect)
- [Tastenbelegung](#tastenbelegung)
- [Tastenkombinationen der BT/IR-Fernbedienung](#tastenkombinationen-der-btir-fernbedienung)
- [Bekannte Einschränkungen](#bekannte-einschränkungen)
- [Entwicklung](#entwicklung)
- [Lizenz](#lizenz)

[Deutsch](README.md) | [English](README.en.md)

## Überblick

![VU+ HID Raw Remote](custom_components/vuplus_hid_raw/brand/logo.png)

Die Integration liest die VU+ BLE-Fernbedienung direkt über Linux `evdev` und stellt sie als Home-Assistant-Gerät bereit.

Mehrere VU+-Sondertasten werden von Linux als `KEY_UNKNOWN = 240` gemeldet. Der zugrunde liegende `MSC_SCAN`-Wert unterscheidet diese Tasten trotzdem. Die Integration verwendet deshalb normale Linux-Keycodes für reguläre Tasten und `MSC_SCAN`/HID-Usage für die als `KEY_UNKNOWN` gemeldeten Consumer-Tasten.

## Voraussetzungen und Berechtigungen

- Home Assistant ab **2026.9.0**; Zielplattform ist Home Assistant OS auf
  Raspberry Pi / aarch64 mit Python 3.14.
- VU+ BT/IR-Fernbedienung (Typ V) mit Bluetooth-Namen `VUPLUS-BLE-RCU`.
- Lokaler Bluetooth-Adapter und das lesbare Linux-Eingabegerät
  `VUPLUS-BLE-RCU Keyboard`.
- Für die Installation über HACS: eine eingerichtete HACS-Integration.

Die Integration benötigt Linux `evdev`. Die Abhängigkeit `evdev==1.9.3` ist im
Manifest hinterlegt und wird von Home Assistant bei der Einrichtung der Custom
Integration installiert; eine manuelle `pip`-Installation ist nicht erforderlich.

Der Home-Assistant-Prozess benötigt Lesezugriff auf die Geräte unter `/dev/input`.
Home Assistant OS stellt die lokalen evdev-Geräte für die Core-Integration bereit.
Bei Home Assistant Container muss `/dev/input` in die
Laufzeitumgebung durchgereicht sein und der Prozess die entsprechenden
Leseberechtigungen besitzen, typischerweise über die Gruppe `input` oder eine
passende udev-Regel. Fehlt der Zugriff, ist das Gerät im Config-Flow-Dropdown nicht
sichtbar oder kann nach der Einrichtung nicht geöffnet werden.

## Sprachen

Einrichtung, Optionen, Reparaturdialoge sowie Geräte-, Tasten- und Diagnosenamen
stehen auf Deutsch und Englisch zur Verfügung. Home Assistant wählt die
Übersetzungen anhand seiner Spracheinstellungen; vom Backend erzeugte Namen
richten sich nach der Systemsprache. Selbst vergebene Namen bleiben erhalten.
Bereits erzeugte Entity-IDs ändern sich durch einen Sprachwechsel nicht automatisch.
Der Integrationseintrag verwendet die sprachneutrale Modellkennung `VUPLUS-BLE-RCU`.

Technische Werte wie `command`, `action` und `event_type` sind in beiden Sprachen
identisch. `command_label` enthält den von Home Assistant ermittelten Namen der
Tasten-Entität. Für Filter und Vergleiche die technischen Werte verwenden.

Alle Anleitungen sind über die Sprachlinks in Deutsch und Englisch erreichbar.

## Installation

### Über HACS

1. In HACS das Menü oben rechts öffnen und **Benutzerdefinierte Repositories**
   wählen.
2. `https://github.com/topic2k/VU-BT-RC` eintragen und den Typ **Integration** wählen.
3. **VU+ HID Raw Remote** in HACS öffnen und herunterladen.
4. Home Assistant neu starten.
5. Unter **Einstellungen → Geräte & Dienste → Integration hinzufügen** nach
   **VU+ HID Raw Remote** suchen und die [Einrichtung](#einrichtung) abschließen.

Die Installation als benutzerdefiniertes Repository setzt ein öffentliches
GitHub-Repository voraus. Eine Aufnahme in den HACS-Standardkatalog ist dafür
nicht erforderlich. Siehe auch die
[HACS-Anleitung für benutzerdefinierte Repositories](https://www.hacs.xyz/docs/faq/custom_repositories/).

### Manuell

1. Den Ordner `custom_components/vuplus_hid_raw` aus diesem Repository vollständig
   nach `/config/custom_components/vuplus_hid_raw` kopieren, einschließlich
   `translations` und `brand`.
2. Home Assistant neu starten und die Integration wie oben hinzufügen.

Der Integrationsordner muss direkt `manifest.json` und `__init__.py` enthalten.
Ein Eintrag in `configuration.yaml` ist nicht erforderlich.

## Funktionsumfang

- Konfiguration über **Einstellungen → Geräte & Dienste**.
- Optionales Suchen, Koppeln, Vertrauen und Verbinden der Fernbedienung im Config Flow.
- Zusätzliche Benutzerbestätigung zum Entkoppeln nach dem Löschen des Integrationseintrags.
- Auswahl der Fernbedienung über ihren Linux-Gerätenamen; das Dropdown zeigt zusätzlich den aktuellen Pfad.
- Device Registry für die Fernbedienung.
- Diagnose-Entitäten für Bluetooth-Kopplung, Verbindung und Reader-Zustand.
- Eigene Event-Entität für jede unterstützte Taste.
- Standardisierte Button-Events: `press_start`, `press_end`, `long_press_start`, `long_press_end` und `repeat`.
- Automatische Wiederverbindung bei Bluetooth-/evdev-Trennung.
- Wechselnde `/dev/input/eventX`-Nummern werden unterstützt.

## Geräteinformationen

In der Home-Assistant-Geräteansicht erscheint die Fernbedienung mit dem Namen
**VU+ Bluetooth-Fernbedienung**, dem Hersteller **VU+** und dem Modell
`VUPLUS-BLE-RCU`. Als Softwareversion wird die Version der Integration angezeigt.
Eine Firmware-Version der Fernbedienung liefert die Linux-evdev-Schnittstelle nicht
und wird daher nicht angezeigt.

Das Integrations-Icon und -Logo liegen in `custom_components/vuplus_hid_raw/brand/`
vor und werden von Home Assistant in der Oberfläche verwendet.

## Diagnose-Entitäten

In der Geräteansicht stehen fünf aktivierte Diagnose-Binärsensoren bereit:

- **Gekoppelt**, **Bluetooth verbunden** und **Vertrauenswürdig** lesen die
  entsprechenden Zustände der zugeordneten BlueZ-Fernbedienung aus.
- **Eingabegerät verfügbar** zeigt, ob der konfigurierte Linux-Gerätename aktuell
  als evdev-Gerät vorhanden ist.
- **Eingabe wird gelesen** zeigt, ob der evdev-Reader das Gerät geöffnet hat.

Die Bluetooth-Zustände werden beim Laden und anschließend alle 30 Sekunden
aktualisiert. Kann die gespeicherte Bluetooth-Zuordnung nicht bestimmt werden oder
ist BlueZ nicht erreichbar, sind diese drei Entitäten vorübergehend nicht verfügbar,
statt einen falschen Aus-Zustand zu zeigen.

## Einrichtung

Die Integration wird über die UI hinzugefügt. Zu Beginn stehen **Bereits verbundenes
Eingabegerät auswählen** und **Bluetooth-Fernbedienung koppeln** zur Auswahl.
Für die Tastenerkennung gespeichert wird der Linux-Gerätename,
standardmäßig `VUPLUS-BLE-RCU Keyboard`; `/dev/input/eventX` wird nie gespeichert.
Zusätzlich werden, sofern eindeutig zugeordnet, die Bluetooth-Adressen der
Fernbedienung und des lokalen Adapters für das spätere Entkoppeln hinterlegt.
Die Fernbedienung muss zum Einrichten aufgeweckt und verbunden sein, damit Linux ihr
evdev-Gerät bereitstellt und sie im Dropdown erscheint.

Die Langdruck-Schwelle beträgt standardmäßig **500 ms**. Sie lässt sich beim
Einrichten und anschließend unter den Integrationsoptionen zwischen **100 und
5000 ms** in Schritten von **50 ms** einstellen.

## Bluetooth-Kopplung

Home Assistants allgemeine Bluetooth-Einrichtung bietet keinen universellen
Pair-/Trust-Dialog für HID-Fernbedienungen. Diese Integration ergänzt dafür einen
eigenen optionalen Ablauf:

1. **Bluetooth-Fernbedienung koppeln** wählen und die Fernbedienung gemäß ihrer
   Anleitung in den Kopplungsmodus versetzen.
2. Die Suche starten. Sie dauert etwa zehn Sekunden und verwendet eingeschaltete
   lokale Bluetooth-Adapter. Angeboten werden Geräte mit dem Bluetooth-Namen
   `VUPLUS-BLE-RCU` (gegebenenfalls mit einem durch Leerzeichen getrennten Zusatz).
3. Die Fernbedienung anhand ihrer Bluetooth-Adresse und des Adapters auswählen.
   Mit dem Absenden wird sie gekoppelt (`Pair`), als vertrauenswürdig markiert
   (`Trusted = true`) und verbunden (`Connect`).
4. Anschließend das Linux-Gerät `VUPLUS-BLE-RCU Keyboard` und die Langdruck-Schwelle
   auswählen. Falls Linux das Gerät noch nicht anzeigt, die Fernbedienung aufwecken
   und das Formular erneut absenden, um die Liste zu aktualisieren. Bei einer
   vollständig leeren Geräteliste erscheint dafür ein eigener Wiederholen-Dialog.

Der Ablauf verwendet BlueZ über den System-D-Bus; `bluetoothctl` wird nicht
benötigt. `dbus-fast==5.0.22` wird über das Manifest installiert. HA OS stellt
BlueZ und den D-Bus-Zugang bereit. Bei Container-Installationen muss zusätzlich
zum Zugriff auf `/dev/input` auch der System-D-Bus des Hosts erreichbar sein.
Der Prozess benötigt die Berechtigung zum Koppeln und Ändern von `Trusted`.
Bei fehlendem Adapter, ausgeschaltetem Bluetooth, fehlenden Berechtigungen oder
Zeitüberschreitungen zeigt der Dialog einen Fehler und ermöglicht einen neuen Versuch.

Bluetooth-Proxies eignen sich für diesen Ablauf nicht: Das HID-Gerät muss vom
Linux-System des Home-Assistant-Hosts als lokales evdev-Gerät bereitgestellt werden.
Unterstützt wird Kopplung ohne PIN-Eingabe (Just Works). Falls die Fernbedienung
eine PIN oder einen Zahlenvergleich verlangt, meldet der Dialog dies; diese
Kopplung muss weiterhin mit `bluetoothctl` erfolgen.

Bestehende Kopplungen werden wiederverwendet. Kopplung und Vertrauen bleiben
bei einem späteren Fehler oder beim Abbrechen der Einrichtung in BlueZ erhalten.
Beim Löschen eines fertigen Integrationseintrags bleibt die Kopplung zunächst
erhalten; das zusätzliche Entkoppeln muss ausdrücklich bestätigt werden (siehe unten). Ein laufender Koppelversuch wird beim Abbruch
beendet; der temporäre Pairing-Agent und eigene Suchsitzungen werden freigegeben.
Die Integration ersetzt keinen globalen Bluetooth-Agenten und ändert keine
Adaptereinstellungen. Bluetooth-Adressen dienen zusätzlich zum Entkoppeln;
BlueZ-Gerätepfade, `hciX`-Nummern und evdev-Pfade werden nicht gespeichert.
Der Reader sucht weiterhin ausschließlich nach dem Linux-Gerätenamen.

## Entkoppeln beim Löschen

Beim Löschen des Integrationseintrags unter **Einstellungen → Geräte & Dienste**
bleibt die Bluetooth-Kopplung zunächst erhalten. Anschließend erscheint unter
**Einstellungen → System → Reparaturen** die Rückfrage **Auch die Bluetooth-Kopplung
löschen?**. Home Assistants normaler Löschdialog lässt sich durch eine Custom
Integration nicht um eine zusätzliche Auswahl erweitern; die Rückfrage erfolgt
deshalb separat nach dem Löschen des HA-Eintrags, aber vor dem Entkoppeln.

Im Dialog gibt es zwei Möglichkeiten:

- **Nur Gerät/Integration löschen – Kopplung behalten** (Vorauswahl): Die Rückfrage
  wird abgeschlossen. Kopplung und Vertrauen bleiben auf dem HA-Host erhalten.
- **Auch die Bluetooth-Kopplung löschen**: Erst beim ausdrücklichen Bestätigen
  dieser Auswahl entfernt die Integration das Gerät aus BlueZ. Verbindung,
  Kopplung und Vertrauen werden auf dem angegebenen Adapter entfernt.

**Schließen oder Ignorieren der Rückfrage, Neuladen, Deaktivieren und Neustarten
lösen kein Entkoppeln aus.** Die offene Rückfrage mit den zugehörigen Adressen
bleibt über HA-Neustarts erhalten. Für die automatische Rückfrage muss der
Integrationscode weiterhin installiert sein.

Nach bestätigtem Entkoppeln muss die Fernbedienung für eine erneute Einrichtung
wieder gekoppelt werden. Ihre internen Kopplungsdaten werden dadurch nicht
zurückgesetzt; sie muss gegebenenfalls erneut in den Kopplungsmodus. Ein bereits
auf dem ursprünglichen Adapter aus BlueZ entferntes Gerät gilt als entkoppelt.
Verwendet ein anderer oder neu angelegter Integrationseintrag die Fernbedienung,
verweigert der Dialog das Entkoppeln.

Der Koppelassistent merkt sich die Bluetooth-Adressen von Fernbedienung und
Adapter. Bei manuell gekoppelten Fernbedienungen und Einträgen ohne Zuordnung
versucht die Integration, die Zuordnung aus den optionalen evdev-Metadaten
`uniq` und `phys` sowie den BlueZ-Geräten eindeutig zu ermitteln. Dies geschieht
beim Einrichten, beim Laden eines Eintrags ohne Zuordnung und nötigenfalls beim
Löschen. Falls die Zuordnung fehlt, die Fernbedienung aufwecken und die Integration
neu laden, damit die Zuordnung gespeichert werden kann. Der Reader verwendet
für die Gerätesuche und den Reconnect ausschließlich den Linux-Gerätenamen.

Bei fehlender Zuordnung, fehlendem Adapter oder einem Fehler beim bestätigten
Entkoppeln bleibt die Rückfrage offen und zeigt den Grund. Die Auswahl wird wieder
auf **Kopplung behalten** gesetzt. Es gibt keinen automatischen Wiederholungsversuch;
ein neuer Löschversuch benötigt eine erneute ausdrückliche Auswahl und Bestätigung.
Alternativ lässt sich die Kopplung bei Bedarf auf dem HA-Host mit `bluetoothctl`
nach Auswahl des richtigen Adapters manuell entfernen.

## Events

Jede unterstützte Taste wird als eigene Event-Entität mit der Geräteklasse
`button` bereitgestellt. Dadurch kann die Taste in der Automations-UI direkt über
ihre Entität ausgewählt werden. Die Entitäten nutzen die HA-Standardtypen
`press_start`, `press_end`, `long_press_start`, `long_press_end` sowie `repeat`.
Ihre Event-Attribute enthalten `command`, `command_label`, `action`, `key_code`,
`value`, `scan_code`, `usage` und `duration_ms`.

| Ereignistyp in Home Assistant | Attribut `action` | Bedeutung |
| --- | --- | --- |
| `press_start` | `press` | Taste gedrückt |
| `press_end` | `short_release` | Nach kurzem Druck losgelassen |
| `long_press_start` | `long_press` | Langdruck-Schwelle erreicht |
| `long_press_end` | `long_release` | Nach langem Druck losgelassen |
| `repeat` | `repeat` | Linux meldet eine Tastenwiederholung |

Der Zustand einer Event-Entität ist der Zeitpunkt ihres letzten Ereignisses;
`event_type` enthält dessen Typ. `duration_ms` beschreibt die bisherige
Tastendruckdauer in Millisekunden. `scan_code` und `usage` können fehlen
(`null`), wenn Linux keinen Scan-Wert geliefert hat.

## Automationen

Die Event-Entitäten sind die Schnittstelle für Automationen. In der
Automations-UI wird zuerst die gewünschte Tasten-Entität über den Trigger
**Ereignis empfangen** ausgewählt. Der Event-Typ legt anschließend die
Tastenaktion fest. Ein zusätzlicher Attribut- oder Template-Filter für den
Tastennamen ist nicht erforderlich.

Es gibt keine integrationsspezifischen Device Triggers und kein separates
Bus-Event. Dadurch ist die Event-Entity die einzige Automationsschnittstelle.

### Beispiel: OK-Taste losgelassen

Die folgende Automation erzeugt nach einem kurzen Druck mit anschließendem
Loslassen der OK-Taste eine dauerhafte Home-Assistant-Benachrichtigung. Der
Event-Typ `press_end` entspricht dem Loslassen nach einem kurzen Tastendruck.

```yaml
alias: "VU+: OK-Taste losgelassen"
triggers:
  - trigger: event.received
    target:
      entity_id: event.vu_bluetooth_fernbedienung_ok
    options:
      event_type:
        - press_end
actions:
  - action: persistent_notification.create
    data:
      title: "VU+-Fernbedienung"
      message: >-
        Taste losgelassen: {{ trigger.to_state.attributes.command_label }}
mode: single
```

Die Entity-ID kann je nach Systemsprache bei der Einrichtung und eigener
Benennung abweichen. In diesem Fall im Beispiel `event.vu_bluetooth_fernbedienung_ok` durch die
Entity-ID der eigenen Entität **OK** ersetzen.

## Kurz- und Langdruck

Die Dauer wird mit einer monotonen Uhr zwischen `EV_KEY` Down und Up gemessen. Nach
Erreichen der Schwelle erzeugt ein unabhängiger Timer sofort `long_press`; dies ist
nicht von Linux-Repeat-Ereignissen abhängig. Beim Loslassen, bei einer Trennung und
beim Entladen der Integration wird der zugehörige Timer abgebrochen.

Ein kurzer Tastendruck erzeugt `press` und anschließend `short_release`. Ein langer
Tastendruck erzeugt `press`, nach Ablauf der Schwelle `long_press` und beim
Loslassen `long_release`. Linux-Repeat-Ereignisse erzeugen zusätzlich `repeat`,
haben aber keinen Einfluss darauf, ob und wann Long Press erkannt wird.

Standard-Schwelle:

```text
500 ms
```

`value` verwendet die Wertebelegung von Linux evdev:

```text
0 = release
1 = press
2 = repeat
```

Das vom Timer erzeugte `long_press` enthält `value: 1`. `value: 2` bezeichnet
ausschließlich Wiederholungen. Long Press wird aus der tatsächlichen Dauer bestimmt.

## Reconnect

Der Reader sucht das Gerät anhand des Linux-Gerätenamens. Bei einer Trennung wird
alle zwei Sekunden erneut gesucht. Dadurch sind wechselnde `/dev/input/eventX`-Pfade
unproblematisch. `MSC_SCAN` wird jeweils nur dem unmittelbar folgenden Key-Event
zugeordnet und bei einer Wiederverbindung verworfen.

## Tastenbelegung

### Navigation

`ok`, `up`, `down`, `left`, `right`

### Lautstärke / Kanal

`volume_up`, `volume_down`, `channel_up`, `channel_down`, `mute`

### Menüs / Sonderfunktionen

`menu`, `pvr`, `radio`, `help`, `stb_power`, `epg`, `audio`, `teletext`, `subtitle`, `speak`, `tv`, `exit`, `left_0`, `right_0`

### Wiedergabe

`rewind`, `forward`, `play`, `pause`, `record`, `stop`

### Farbtasten

`red`, `green`, `yellow`, `blue`

### Ziffern

`0` bis `9`

## Tastenkombinationen der BT/IR-Fernbedienung

Die Anleitung zu Bluetooth-Kopplung, Werksreset, Systemcode sowie TV- und
Lautstärke-Programmierung steht in
[`VU_BT_FERNBEDIENUNG_TASTENKOMBINATIONEN.md`](VU_BT_FERNBEDIENUNG_TASTENKOMBINATIONEN.md).

## Bekannte Einschränkungen

- `TV Power` und `AV` erzeugen auf der verwendeten Linux-HID/evdev-Schicht kein
  Ereignis und stehen nicht als Trigger zur Verfügung.
- Bluetooth-Proxies ersetzen kein lokales evdev-Gerät.
- Mehrere Fernbedienungen mit identischem Linux-Gerätenamen lassen sich nicht
  getrennt konfigurieren; die Geräteauswahl und der Reader unterscheiden sie
  ausschließlich anhand ihres Namens.
- Die automatisierten Tests simulieren Home Assistant und den BlueZ-Transport.
  Ein vollständiger Test von Kopplung, Reparaturdialog und Entkopplung mit echter
  Fernbedienung unter HA OS auf Raspberry Pi/aarch64 ist noch ausstehend.

## Entwicklung

Entwicklungsregeln und dauerhafte Projektvorgaben stehen in [AGENTS.md](AGENTS.md).

Für die lokalen Prüfungen Python 3.14 verwenden:

```sh
python -m pip install -r requirements-test.txt
python -m unittest discover -s tests -v
python -m compileall -q custom_components tests
```

Die Tests ersetzen Home Assistant, evdev und den Linux-D-Bus-Transport durch
Testdoubles. Unter GitHub Actions laufen außerdem Hassfest und die HACS-Validierung.
Der Ablauf für die Veröffentlichung steht in [RELEASING.md](RELEASING.md).

Die Versionshistorie steht ausschließlich in [CHANGELOG.md](CHANGELOG.md).

## Lizenz

Das Projekt steht unter der [MIT-Lizenz](LICENSE). Eine
[deutsche Übersetzung](LICENSE.de.md) ist zur Orientierung verfügbar.
