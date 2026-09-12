[Deutsch](DOKUMENTATION.md) | [English](DOKUMENTATION.en.md)

# VU+ HID Raw Remote – ausführliche Dokumentation

## Inhaltsverzeichnis

- [Überblick](#überblick)
- [Voraussetzungen und Berechtigungen](#voraussetzungen-und-berechtigungen)
- [Sprachen](#sprachen)
- [Installation](#installation)
- [Funktionsumfang](#funktionsumfang)
- [Geräteinformationen](#geräteinformationen)
- [Diagnose-Entitäten](#diagnose-entitäten)
- [Einrichtung](#einrichtung)
- [Mehrere Fernbedienungen](#mehrere-fernbedienungen)
- [Bluetooth-Kopplung](#bluetooth-kopplung)
- [Entkoppeln beim Löschen](#entkoppeln-beim-löschen)
- [Events](#events)
- [Automationen](#automationen)
- [Blueprint: kurze Tastendrücke an Receiver-Buttons](#blueprint-kurze-tastendrücke-an-receiver-buttons)
- [Kurz- und Langdruck](#kurz--und-langdruck)
- [Reconnect](#reconnect)
- [Tastenbelegung](#tastenbelegung)
- [Tastenkombinationen der BT/IR-Fernbedienung](#tastenkombinationen-der-btir-fernbedienung)
- [Bekannte Einschränkungen](#bekannte-einschränkungen)
- [Entwicklung](#entwicklung)
- [Lizenz](#lizenz)

Diese Referenz ergänzt das kompakte [README](README.md) für GitHub und HACS.
Sie beschreibt die technischen Hintergründe, alle Einrichtungswege, Event-Daten
und die Fehlerdiagnose.

## Überblick

![VU+ HID Raw Remote](logo.docs.png)

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
- Auswahl über Linux-Gerätename und Bluetooth-Adresse; das Dropdown zeigt zusätzlich den aktuellen Pfad.
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
- **Eingabegerät verfügbar** zeigt, ob das konfigurierte Gerät anhand von Name und
  gespeicherter Adresse eindeutig als evdev-Gerät vorhanden ist.
- **Eingabe wird gelesen** zeigt, ob der evdev-Reader das Gerät geöffnet hat.

Die Bluetooth-Zustände werden beim Laden und anschließend alle 30 Sekunden
aktualisiert. Kann die gespeicherte Bluetooth-Zuordnung nicht bestimmt werden oder
ist BlueZ nicht erreichbar, sind diese drei Entitäten vorübergehend nicht verfügbar,
statt einen falschen Aus-Zustand zu zeigen.

## Einrichtung

Die Integration wird über die UI hinzugefügt. Zu Beginn stehen **Bereits verbundenes
Eingabegerät auswählen** und **Bluetooth-Fernbedienung koppeln** zur Auswahl.
Für die Tastenerkennung werden der Linux-Gerätename, standardmäßig
`VUPLUS-BLE-RCU Keyboard`, und die Bluetooth-Adresse aus evdev `uniq` gespeichert.
`/dev/input/eventX` wird nie gespeichert. Sofern eindeutig zugeordnet, wird auch
die Adresse des lokalen Adapters für Diagnose und späteres Entkoppeln hinterlegt.
Die Fernbedienung muss zum Einrichten aufgeweckt und verbunden sein, damit Linux ihr
evdev-Gerät bereitstellt und sie im Dropdown erscheint.

Die Langdruck-Schwelle beträgt standardmäßig **500 ms**. Sie lässt sich beim
Einrichten und anschließend unter den Integrationsoptionen zwischen **100 und
5000 ms** in Schritten von **50 ms** einstellen.

## Mehrere Fernbedienungen

Jede Fernbedienung erhält einen eigenen Integrationseintrag mit eigenen
Tasten-Event-Entitäten und Diagnoseanzeigen. Im Dropdown erscheinen gleichnamige
Geräte getrennt mit ihrer Bluetooth-Adresse. Wähle jeweils die passende Adresse
und `VUPLUS-BLE-RCU Keyboard`. Die übersetzten Gerätenamen enthalten die Adresse;
du kannst ihnen anschließend eigene Namen geben. Im Blueprint wählst du für jede
Automation das zugehörige Fernbedienungsgerät aus.

**Bestehenden Eintrag übernehmen:** Eine bereits gespeicherte Bluetooth-Zuordnung
wird als feste Leseradresse übernommen. Fehlt sie, wird ein eindeutig gefundenes
Einzelgerät bei Verfügbarkeit an seine Adresse gebunden. Sind mehrere gleichnamige
Geräte vorhanden, bleibt der Leser ohne feste Zuordnung inaktiv. Öffne dann beim
vorhandenen Eintrag unter **Einstellungen → Geräte & Dienste → VU+ HID Raw Remote**
das Menü **Neu konfigurieren** und wähle seine Fernbedienung anhand der Adresse.
Geräte- und Entitätskennungen sowie bestehende Automationen bleiben erhalten.
Danach über **Eintrag hinzufügen** die zweite Fernbedienung einrichten. Solange
ein unzugeordneter gleichnamiger Eintrag existiert, verhindert die Einrichtung
eines weiteren Eintrags eine doppelte Nutzung derselben Fernbedienung.
Eine bereits fest zugeordnete Fernbedienung kann über **Neu konfigurieren** nicht
durch eine andere ersetzt werden.

Die feste Adresse stammt aus dem evdev-Feld `uniq`, unabhängig vom BlueZ-Zugang.
Das Feld `phys` dient nur zur zusätzlichen Zuordnung des lokalen Bluetooth-Adapters.
Prüfung auf dem Linux-Host, während beide Fernbedienungen verbunden sind:

```sh
grep -A 7 -B 1 'Name="VUPLUS-BLE-RCU Keyboard"' /proc/bus/input/devices
```

Die Zeilen `U: Uniq=` sollten die unterschiedlichen Bluetooth-Adressen enthalten.
Bei fehlendem `uniq` bleibt ein einzelnes eindeutig benanntes Eingabegerät nutzbar;
mehrere gleichnamige Geräte ohne unterscheidbare Adresse werden nicht angeboten.
Am 12.09.2026 bestätigte eine vom Nutzer bereitgestellte Host-Ausgabe zwei
gleichnamige Keyboard-Geräte mit unterschiedlichen Bluetooth-Adressen in `uniq`
und identischem Adapter in `phys`. Diese Metadaten werden auch im Test nachgebildet.
Die Funktion ist lokal mit simulierten evdev-Geräten geprüft; der tatsächliche
Parallelbetrieb und Reconnects mit zwei Fernbedienungen auf HA OS stehen noch aus.

## Bluetooth-Kopplung

Home Assistants allgemeine Bluetooth-Einrichtung bietet keinen universellen
Pair-/Trust-Dialog für HID-Fernbedienungen. Diese Integration ergänzt dafür einen
eigenen optionalen Ablauf:

1. **Bluetooth-Fernbedienung koppeln** wählen und die Fernbedienung gemäß ihrer
   Anleitung in den Kopplungsmodus versetzen.
2. Die Suche starten. Sie dauert etwa zehn Sekunden und verwendet eingeschaltete
   lokale Bluetooth-Adapter. Angeboten werden Geräte mit dem Bluetooth-Namen
   `VUPLUS-BLE-RCU` (gegebenenfalls mit einem durch Leerzeichen getrennten Zusatz).
   Bereits gekoppelte, dauerhaft gebundene oder verbundene Geräte werden über
   alle lokalen Adapter hinweg anhand ihrer Bluetooth-Adresse ausgeblendet,
   ebenso bereits in der Integration eingerichtete Adressen. Schlafende
   gekoppelte Fernbedienungen werden dadurch nicht erneut angeboten.
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

Für bereits gekoppelte Fernbedienungen den Weg **Bereits verbundenes Eingabegerät
auswählen** verwenden und die Fernbedienung aufwecken. Die Suche führt keine
Historie gelöschter Kopplungen: Nach dem Entfernen der Kopplung und des
Integrationseintrags kann eine Fernbedienung wieder angeboten werden.
Der Filter wurde lokal mit simulierten BlueZ-Geräten und Konfigurationseinträgen
geprüft. Der Nutzer hat die erfolgreiche Filterung am 12.09.2026 im Praxistest
bestätigt; daraus folgt keine Bestätigung der übrigen noch offenen Hardwaretests.

Kopplung und Vertrauen bleiben
bei einem späteren Fehler oder beim Abbrechen der Einrichtung in BlueZ erhalten.
Beim Löschen eines fertigen Integrationseintrags bleibt die Kopplung zunächst
erhalten; das zusätzliche Entkoppeln muss ausdrücklich bestätigt werden (siehe unten). Ein laufender Koppelversuch wird beim Abbruch
beendet; der temporäre Pairing-Agent und eigene Suchsitzungen werden freigegeben.
Die Integration ersetzt keinen globalen Bluetooth-Agenten und ändert keine
Adaptereinstellungen. Bluetooth-Adressen dienen zusätzlich zum Entkoppeln;
BlueZ-Gerätepfade, `hciX`-Nummern und evdev-Pfade werden nicht gespeichert.
Der Reader prüft Linux-Gerätename und die gespeicherte Bluetooth-Adresse.
Nach dem Koppeln bietet die Eingabegeräteauswahl nur die gewählte Fernbedienung an.

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
neu laden, damit die Zuordnung gespeichert werden kann. Für gespeicherte
Fernbedienungsadressen wird ausschließlich die passende evdev-Schnittstelle
berücksichtigt. Ein anderer Eintrag mit abweichender fester Adresse verhindert
das bestätigte Entkoppeln nicht; ein unzugeordneter gleichnamiger Eintrag schützt
die Kopplung weiterhin vor einer unsicheren Entfernung.

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

Bei einer deutschen Einrichtung erhalten Lautstärke und Kanal eindeutige,
automatisch erzeugte Namen wie `..._lautstarke_plus`, `..._lautstarke_minus`,
`..._kanal_plus` und `..._kanal_minus`. Bereits vorhandene Entitäten behalten
ihre Entity-ID; diese können bei Bedarf in den Entitätseinstellungen umbenannt
werden.

## Blueprint: kurze Tastendrücke an Receiver-Buttons

Mit dem [deutschen Blueprint](blueprints/automation/vuplus_hid_raw/short_press_buttons.yaml)
ersetzt eine Automation die bisherigen Einzelautomationen für kurze Tastendrücke.
Die [englische Fassung](blueprints/automation/vuplus_hid_raw/short_press_buttons.en.yaml)
hat dieselbe Funktion. Beide benötigen Home Assistant ab 2026.9.0.

### Einrichtung

1. Den Import-Link in der README nutzen oder den [deutschen Blueprint](https://github.com/topic2k/VU-BT-RC/blob/main/blueprints/automation/vuplus_hid_raw/short_press_buttons.yaml)
   unter **Einstellungen → Automationen & Szenen → Blueprints → Blueprint importieren**
   importieren. Alternativ die YAML-Datei nach `/config/blueprints/automation/vuplus_hid_raw/`
   kopieren. HACS installiert diese Blueprint-Dateien nicht mit der Integration.
2. Unter **Einstellungen → Automationen & Szenen → Blueprints** den Blueprint
   öffnen und eine Automation erstellen; bei einer aktualisierten Datei den
   Blueprint neu laden.
3. Das Gerät unserer Fernbedienung auswählen. Damit sind dessen Event-Entitäten
   gemeinsam erfasst; ihre Entity-IDs dürfen beliebig benannt sein.
4. Für HAVUOpenWebif unter **HAVUOpenWebif-Receiver** den Receiver auswählen;
   das Präfix kann leer bleiben. Die automatische Erkennung ist unten beschrieben.
   Für andere Integrationen das **Standard-Zielpräfix** eintragen, beispielsweise
   `button.receiver_`. Daraus entstehen `button.receiver_ok`, `button.receiver_up` usw.
5. Abweichungen unter **Abweichende Tastennamen** oder **Explizite Standard-Ziele**
   ergänzen. Speichern und zunächst mit einer Taste testen. Die bisherigen
   Automationen für kurze Tastendrücke deaktivieren, damit keine Doppelaktionen
   entstehen.

Die Zuordnung verwendet das sprachunabhängige Attribut `command`, nicht den
Anzeigenamen oder die Entity-ID der Fernbedienung. Bei der Präfix-Zuordnung werden
ähnlich aussehende Namen nicht unscharf gesucht: Es zählt die genaue Entity-ID des
Ziel-Buttons. Folgende Präfix- und Einzelziel-Beispiele sind Platzhalter.

### Blueprint-Updates

Jede Sprachfassung besitzt eine feste `source_url` auf `main` und eine sichtbare
Blueprint-Version in der Beschreibung. Beim Aktualisieren den bisherigen lokalen
Dateipfad beibehalten: Automationen verweisen auf diese Datei. Die angegebene
HAVUOpenWebif-Prüfversion ist davon unabhängig.

Für ein manuelles Update im Menü des Blueprints **Blueprint erneut importieren**
wählen. Home Assistant ersetzt die importierte Vorlage; erforderliche Anpassungen
an Eingaben stehen im [Changelog](CHANGELOG.md). Siehe die
[Home-Assistant-Anleitung](https://www.home-assistant.io/docs/automation/using_blueprints/#re-importing-a-blueprint).
Ein HACS-Update unserer Integration aktualisiert den separaten Blueprint nicht.

Für optionale Update-Hinweise:

1. [Blueprints Updater](https://github.com/luuquangvu/blueprints-updater) über HACS
   installieren und unter **Einstellungen → Geräte & Dienste** einrichten.
2. Über dessen Whitelist die installierte Sprachfassung unseres Blueprints auswählen.
3. Automatische Installation zunächst ausgeschaltet lassen. Verfügbare Änderungen
   erscheinen über eine `update`-Entität; prüfen und manuell mit aktivierter
   Sicherung installieren.
4. Nach dem Hinzufügen eines Blueprints die Updater-Integration neu laden,
   damit sie ihre Liste aktualisiert.

Der Updater erkennt Inhaltsänderungen unabhängig von unserer Versionsnummer.
Die Quelle folgt `main`: Änderungen stehen bereits nach dem Merge bereit, auch
vor dem GitHub-Release. Entwicklungsänderungen auf `develop` werden nicht angeboten.
Der Updater ist optional; unsere Fernbedienungsintegration benötigt ihn nicht.

Bei einem bisher manuell kopierten Blueprint die Datei einmal am bisherigen Pfad
durch die aktuelle Sprachfassung inklusive `source_url` ersetzen. Danach die
Automationen und den Updater neu laden. Ein zweiter Import unter einem anderen
Pfad aktualisiert keine Automationen, die noch auf die bisherige Datei verweisen.

Import, Update-Erkennung und Installation mit Blueprints Updater sind noch nicht
in einer laufenden Home-Assistant-Installation geprüft. Lokale Tests prüfen
Quellmetadaten, Sprachlinks und Template-Ausführung, nicht den externen Updater.

### Automatische Erkennung für HAVUOpenWebif

**Geprüfte Basis: HAVUOpenWebif 1.1.0**, laut
[Manifest](https://github.com/howeydium/HAVUOpenWebif/blob/f20b23d74b6b63f343dd42d2177dec22df068d76/custom_components/havuopenwebif/manifest.json)
im Commit `f20b23d74b6b63f343dd42d2177dec22df068d76`.
Geprüft wurden die Tasten- und Attributdefinitionen im Quellcode sowie unsere
Blueprint-Zuordnung mit lokalen YAML-/Jinja-Tests und simulierten Entitäten.
Ein Import und ein Funktionstest mit dieser Integration am echten Receiver
stehen noch aus; dieser Stand ist keine Bestätigung einer vollständig getesteten
Gerätekombination.

**Mit anderen oder neueren HAVUOpenWebif-Versionen kann die Zuordnung teilweise
oder vollständig nicht mehr funktionieren.** Insbesondere Änderungen an Keycodes,
Attributen oder Gerätezuordnungen können sie beeinträchtigen. Es gibt keine
automatische Versionssperre oder Zusage für andere Versionen. Nach einem Update
die Zuordnung erneut prüfen. Der Hinweis betrifft die HAVUOpenWebif-Anbindung
des Blueprints; das Einlesen der Bluetooth-Fernbedienung ist davon unabhängig.

Nach Auswahl des Receiver-Geräts werden dessen `button.*`-Entitäten anhand ihres
`keycode`-Attributs erkannt. Dadurch sind Sprache, Gerätename und umbenannte
Entity-IDs unerheblich. Nur Buttons von HAVUOpenWebif auf dem ausgewählten Gerät
kommen infrage. Ein Präfix oder übersetzte Tastennamen sind dafür nicht nötig.
**Explizite Standard-Ziele** haben weiterhin Vorrang, auch zum Deaktivieren einer Taste.

Der Blueprint enthält eine Zuordnung der Tastenfunktionen zu den Enigma2-Codes
von [HAVUOpenWebif](https://github.com/howeydium/HAVUOpenWebif/blob/f20b23d74b6b63f343dd42d2177dec22df068d76/custom_components/havuopenwebif/const.py).
Er reicht unsere lokalen evdev-Codes nicht direkt weiter: Beispielsweise verwendet
OK dort `352`, Exit `174`, Stop `128` und PVR `366`. Die Buttons selbst senden diese
Codes über [OpenWebIf](https://github.com/howeydium/HAVUOpenWebif/blob/f20b23d74b6b63f343dd42d2177dec22df068d76/custom_components/havuopenwebif/button.py).

Im geprüften Stand gibt es für `tv`/`tvradio` denselben Code `377` und für
`text`/`text_teletext` denselben Code `388`. Bei mehreren passenden Buttons wird
die Taste übersprungen. Dafür unter **Explizite Standard-Ziele** die gewünschte
eigene Entität angeben, beispielsweise:

```yaml
tv: button.mein_receiver_tv
teletext: button.mein_receiver_videotext
```

Diese beiden Entity-IDs durch die tatsächlichen IDs ersetzen. Die Codes und
die Erkennung sind geprüft; die konkrete Funktion auf dem Receiver bleibt von
dessen Firmware abhängig, insbesondere bei PVR, das HAVUOpenWebif als Best Effort
kennzeichnet. Für `speak`, `left_0` und `right_0` gibt es keine eindeutige
Entsprechung im geprüften Tastenangebot. Diese bleiben ohne explizites Ziel unbelegt.
Ein fehlender oder mehrdeutiger Treffer fällt nicht auf die Präfix-Regel zurück.

### Zuordnung über Namen und Einzelziele

**Abweichende Tastennamen** ändern nur das Suffix nach dem Präfix:

```yaml
volume_up: lautstarke_plus
volume_down: lautstarke_minus
stb_power: power
"1": digit_1
```

**Explizite Standard-Ziele** haben Vorrang vor Präfix und Suffix:

```yaml
ok: button.receiver_enter
mute: button.verstarker_mute
speak: ""
```

Ein leerer Wert `""` deaktiviert diese Taste. Ohne Receiver-Auswahl schaltet ein
leeres Präfix die automatische Namensregel aus; dann gelten nur explizite Ziele. Für Zifferntasten
die Schlüssel immer in Anführungszeichen setzen (`"0"` bis `"9"`).

Die verfügbaren `command`-Werte sind:

```text
ok, up, down, left, right, volume_up, volume_down, channel_up, channel_down,
menu, pvr, mute, rewind, forward, play, pause, record, stop, radio, help,
stb_power, red, green, yellow, blue, 0–9, epg, audio, teletext, subtitle,
speak, tv, exit, left_0, right_0
```

### Bedingte Ziele

**Alternative Zuordnung aktivieren** einschalten und im Bedingungseditor zum
Beispiel `input_boolean.kinomodus` auf `on` prüfen. Alle Bedingungen müssen erfüllt
sein; ODER-Gruppen sind möglich. Eine leere Bedingungsliste gilt immer, solange die
alternative Zuordnung aktiviert ist.

Für **nur andere Lautstärkeziele** den alternativen Receiver und das alternative
Präfix leer lassen. Unter **Explizite alternative Ziele** Einträge hinzufügen und
jeweils **Taste**, unter **Ziel nach Typ auswählen** den Entitätstyp und das Ziel,
und bei Bedarf **Aktion** auswählen:

1. Beispielsweise **Media Player**, **Schalter** oder **Skript** als Typ wählen.
2. Im darunterliegenden Entitätsfeld einen Namen oder eine Entity-ID eingeben,
   etwa `wohnzimmer` oder `media_player.verstarker`. Die eingebaute Freitextsuche
   grenzt die Liste innerhalb des gewählten Typs weiter ein.
3. Den gewünschten Treffer auswählen. Der Suchtext ist nur eine Auswahlhilfe;
   gespeichert wird die konkrete Ziel-Entität, kein Suchmuster für spätere Aufrufe.

Die Freitextsuche stammt aus Home Assistants
[Entitätsauswahl](https://github.com/home-assistant/frontend/blob/dev/src/data/entity/entity_picker.ts).
Ein separates Freitextfeld ist dafür nicht nötig. Es gibt genau eine Zielauswahl
pro Eintrag. Bei einem Typwechsel werden gespeicherte Ziele anderer, gerade
nicht ausgewählter Typen nicht ausgeführt. Ein Eintrag ohne vollständige
Zielauswahl und ohne aktivierte Deaktivierung ändert die Standard-Zuordnung nicht.

| Taste | Ziel-Entität (Beispiel) | Aktion |
| --- | --- | --- |
| Lautstärke Plus | `media_player.verstarker` | Media Player: Lautstärke erhöhen |
| Lautstärke Minus | `media_player.verstarker` | Media Player: Lautstärke verringern |
| Rot | `switch.steckdose` | Schalter: umschalten |
| Grün | `script.kinomodus` | Skript starten |
| Blau | `scene.kino` | Szene aktivieren |

Die Auswahl umfasst `button`, `input_button`, `media_player`, `switch`,
`input_boolean`, `script`, `scene`, `light`, `fan` und `cover`, auch von anderen
Integrationen. Ohne ausgewählte Aktion gilt: Buttons werden gedrückt, Skripte
gestartet, Szenen aktiviert und bei Media Playern Wiedergabe/Pause umgeschaltet.
Schalter, Schalt-Helfer, Lichter, Ventilatoren und Rollläden werden umgeschaltet.
Für Lautstärke, Ein-/Ausschalten oder eine andere Funktion die passende Aktion
ausdrücklich auswählen. Entitätsauswahl und Aktion stehen im selben Dialog, ohne
zusätzlichen Unterdialog. Die Entitätsauswahl bleibt nach Typ gefiltert; die
gemeinsame Aktionsliste zeigt alle angebotenen Aktionen. Eine zum Zieltyp passende
Aktion selbst auswählen und nach einem Typwechsel gegebenenfalls anpassen.
Nicht zum Zieltyp passende Aktionen werden bei der Ausführung übersprungen.
Die Fähigkeiten des konkreten Geräts werden nicht geprüft; Benutzer müssen selbst
prüfen oder ausprobieren, welche Aktionen es unterstützt. Gerätefehler erscheinen
in der Automationsspur.

Unter **Aktionsdaten (optional, YAML)** lassen sich feste Parameter angeben:
bei `media_player.volume_mute` beispielsweise `is_volume_muted: true`, für
`light.turn_on` etwa `brightness_pct: 30` und für `media_player.select_source`
etwa `source: HDMI 1`. Bei `script.turn_on` werden Skriptparameter unter
`variables` angegeben. Für komplexe Abläufe ein Skript auswählen. Skripte starten
ohne auf ihr Ende zu warten; ihre weitere Ausführung folgt ihrem eigenen Modus.

**Taste deaktivieren** unterdrückt die ausgewählte Taste, solange
die Alternativbedingungen gelten; dafür ist keine Ziel-Entität nötig. Der Schalter
hat Vorrang vor einem gleichzeitig ausgewählten Ziel. Ein Eintrag ohne Ziel und
ohne aktivierte Deaktivierung ändert nichts. Entfernen eines Eintrags hebt seine
Überschreibung auf.

Bei mehrfacher Auswahl derselben Taste gilt der letzte vollständige Eintrag.

Alle anderen Tasten behalten ihre Standard-Zuordnung. Für **einen anderen
HAVUOpenWebif-Receiver für alle Tasten** den **Alternativen HAVUOpenWebif-Receiver**
auswählen. Damit wird das gesamte Zielprofil gewechselt; explizite Standard-Ziele
werden nicht übernommen. Videotext/TV-Ausnahmen deshalb bei Bedarf auch unter
**Explizite alternative Ziele** eintragen. Für andere Integrationen beispielsweise `button.receiver_schlafzimmer_`
als alternatives Präfix eintragen. Dann gelten nur dieses Präfix, die gemeinsamen
abweichenden Tastennamen und die expliziten alternativen Ziele. Explizite
Standard-Ziele werden in diesem Fall nicht übernommen.

Auch Bedingungen pro Taste sind möglich. Eine Template-Bedingung kann etwa
`{{ command | string in ['volume_up', 'volume_down', 'mute'] }}` verwenden und
mit einer Zustandsbedingung kombiniert werden. Ein Blueprint bietet ein
Standardprofil und ein bedingtes Alternativprofil. Für weitere Profile lassen sich
mehrere Automationen ohne Standard-Receiver, mit leerem Standardpräfix und ohne Standard-Einzelziele
anlegen. Ihre Alternativbedingungen müssen sich gegenseitig ausschließen, damit
ein Tastendruck nur eine Automation zur Weiterleitung bringt.

### Verhalten und Prüfung

- Nur `press_end` löst die gewählte Aktion einmal aus. Automatisch erkannte
  Receiver-Buttons und explizite Standard-Buttons verwenden `button.press`. Langer Druck,
  Drücken und Wiederholungen werden nicht weitergeleitet.
- Nicht vorhandene, nicht verfügbare oder explizit deaktivierte Ziele werden
  übersprungen. Ein vorhandener Button im Zustand `unknown` darf gedrückt werden;
  dieser Zustand ist vor seiner ersten Betätigung normal. Ein alternatives Ziel
  fällt bei Ausfall nicht auf den Standard-Receiver zurück.
- Tastendrücke werden in Reihenfolge abgearbeitet (`queued`, höchstens 50
  laufende/wartende Durchläufe). Bedingungen werden bei der Verarbeitung geprüft.
- In der Automationsspur zeigen `command`, `target_receiver`, `target_prefix`, `target_buttons` und
  `target_button` die ermittelte Zuordnung. `target_entity`, `target_action` und
  `target_data` zeigen den endgültigen Aufruf. Zum Testen die physische Taste kurz
  drücken; **Aktionen ausführen** stellt keine `trigger`-Daten bereit.
- Nicht zum Zieltyp passende Aktionen werden übersprungen. Nicht registrierte
  Aktionen werden beim Aufruf von Home Assistant als Fehler in der Automationsspur
  gemeldet; eine Service-Abfrage im Template findet nicht statt.
  Präfixe und explizite Standard-Ziele sind Button-Zuordnungen;
  andere Entitätstypen werden über die neuen Auswahlfelder eingerichtet.
- **TV Power** und **AV** bleiben ohne Funktion über evdev.

Die Vorlagen sind mit YAML- und Jinja-Tests geprüft; ein Import und Funktionstest
mit der konkreten Receiver-Integration steht noch aus. Der Auslöser entspricht
dem [Event-Trigger in Home Assistant 2026.9](https://github.com/home-assistant/core/blob/2026.9.0/homeassistant/components/event/trigger.py),
die Eingabefelder verwenden die dokumentierten
[Blueprint-Selektoren](https://www.home-assistant.io/docs/blueprint/selectors/).

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

Der Reader sucht das Gerät anhand des Linux-Gerätenamens und der gespeicherten
Bluetooth-Adresse aus `uniq`. Fehlt diese Fernbedienung, wird kein anderes
gleichnamiges Gerät gelesen. Bei einer Trennung wird
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
- Mehrere gleichnamige Fernbedienungen benötigen unterschiedliche Bluetooth-Adressen
  in evdev `uniq`. Fehlende oder doppelte Identitäten lassen sich nicht zuverlässig
  unterscheiden. Der Betrieb mit zwei echten Fernbedienungen ist noch nicht bestätigt;
  die Zuordnung und Ereignistrennung sind mit simulierten evdev-Geräten geprüft.
- Installation über HACS sowie Hinzufügen, Bluetooth-Kopplung und bestätigtes
  Entkoppeln sind mit der Fernbedienung getestet. Die automatisierten Tests
  simulieren weiterhin Home Assistant und den BlueZ-Transport; Tasten, Langdruck
  und Wiederverbindung sollten vor einem späteren Funktionsausbau zusätzlich auf
  der eigenen Zielhardware geprüft werden.

## Entwicklung

Entwicklungsregeln und dauerhafte Projektvorgaben stehen in [AGENTS.md](AGENTS.md).

Für die lokalen Prüfungen Python 3.14 verwenden:

```sh
python -m pip install --group test
python -m unittest discover -s tests -v
python -m compileall -q custom_components tests
```

Die Tests ersetzen Home Assistant, evdev und den Linux-D-Bus-Transport durch
Testdoubles. Unter GitHub Actions laufen außerdem Hassfest und die HACS-Validierung.
Die Einstellungen für zusätzliche Entwicklungswerkzeuge stehen in
[pyproject.toml](pyproject.toml); sie ersetzen nicht die oben genannten
Release-Prüfungen. Der Ablauf für die Veröffentlichung steht in
[RELEASING.md](RELEASING.md).

Die Versionshistorie steht ausschließlich in [CHANGELOG.md](CHANGELOG.md).

## Lizenz

Das Projekt steht unter der [MIT-Lizenz](LICENSE). Eine
[deutsche Übersetzung](LICENSE.de.md) ist zur Orientierung verfügbar.
