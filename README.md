# VU+ HID Raw Remote

## Inhaltsverzeichnis

- [Worum geht es?](#worum-geht-es)
- [Das kann die Integration](#das-kann-die-integration)
- [Voraussetzungen](#voraussetzungen)
- [Installation](#installation)
- [Einrichtung und Nutzung](#einrichtung-und-nutzung)
- [Automationen](#automationen)
- [Wichtige Hinweise](#wichtige-hinweise)
- [Mehr erfahren](#mehr-erfahren)
- [Lizenz](#lizenz)

[Deutsch](README.md) | [English](README.en.md)

![VU+ HID Raw Remote](logo.docs.png)

## Worum geht es?

**VU+ HID Raw Remote** bindet die VU+ BT/IR-Fernbedienung (Typ V) mit dem
Bluetooth-Namen `VUPLUS-BLE-RCU` direkt in Home Assistant ein. Jede unterstützte
Taste wird dort zu einer eigenen Event-Entität und kann Automationen auslösen.

So kann beispielsweise ein Druck auf **OK**, **Menü**, eine Farbtaste oder eine
Wiedergabetaste direkt Szenen, Lichter oder Skripte steuern.

## Das kann die Integration

- Fernbedienung über die Home-Assistant-Oberfläche einrichten und bei Bedarf
  direkt per Bluetooth koppeln.
- Kurze und lange Tastendrücke sowie Tastenwiederholungen unterscheiden.
- Für jede unterstützte Taste einen klar auswählbaren Automationsauslöser bieten.
- Nach Bluetooth-Trennungen automatisch wieder verbinden.
- Den Zustand von Kopplung, Verbindung und Eingabegerät in der Geräteansicht
  anzeigen.
- Beim Löschen der Integration die Bluetooth-Kopplung nur nach ausdrücklicher
  Bestätigung entfernen.

Die Oberfläche und die Dokumentation stehen auf Deutsch und Englisch zur Verfügung.

## Voraussetzungen

- Home Assistant **2026.9.0** oder neuer, vorzugsweise Home Assistant OS auf
  Raspberry Pi / aarch64.
- VU+ BT/IR-Fernbedienung Typ V und ein lokaler Bluetooth-Adapter.
- Die Fernbedienung muss auf dem Home-Assistant-Host als
  `VUPLUS-BLE-RCU Keyboard` erscheinen.

Bei Home Assistant Container sind zusätzliche Zugriffsrechte auf `/dev/input`
und den System-D-Bus nötig. Die Details stehen in der
[ausführlichen Dokumentation](DOKUMENTATION.md#voraussetzungen-und-berechtigungen).

## Installation

### Über HACS

1. In HACS oben rechts **Benutzerdefinierte Repositories** öffnen.
2. `https://github.com/topic2k/VU-BT-RC` eintragen und den Typ **Integration**
   auswählen.
3. **VU+ HID Raw Remote** herunterladen und Home Assistant neu starten.
4. Unter **Einstellungen → Geräte & Dienste → Integration hinzufügen** nach
   **VU+ HID Raw Remote** suchen.

### Manuell

Den Ordner `custom_components/vuplus_hid_raw` in
`/config/custom_components/vuplus_hid_raw` kopieren und Home Assistant neu
starten. Ein Eintrag in `configuration.yaml` ist nicht nötig.

## Einrichtung und Nutzung

Beim Hinzufügen der Integration gibt es zwei Wege:

- **Bereits verbundenes Eingabegerät auswählen**, wenn die Fernbedienung schon
  mit dem Host gekoppelt ist.
- **Bluetooth-Fernbedienung koppeln**, um sie direkt in Home Assistant zu suchen,
  zu koppeln und zu verbinden.

Die Fernbedienung zum Einrichten aufwecken. Danach die gewünschte Langdruck-Schwelle
wählen; standardmäßig sind es 500 ms. In der Geräteansicht erscheinen anschließend
die Tasten als Event-Entitäten und fünf Diagnoseanzeigen.

## Automationen

In einer neuen Automation den Auslöser **Ereignis empfangen** wählen, die gewünschte
Tasten-Entität auswählen und dann den Ereignistyp festlegen:

| Ereignistyp | Bedeutung |
| --- | --- |
| `press_start` | Taste gedrückt |
| `press_end` | Nach kurzem Druck losgelassen |
| `long_press_start` | Langdruck erkannt |
| `long_press_end` | Nach langem Druck losgelassen |
| `repeat` | Taste wird gehalten und wiederholt |

Ein zusätzlicher Filter für den Tastennamen ist nicht nötig: Die Taste wird bereits
über ihre eigene Entität ausgewählt. Ein vollständiges Beispiel und die Event-Daten
stehen in der [Automationsreferenz](DOKUMENTATION.md#automationen).

## Wichtige Hinweise

- **TV Power** und **AV** liefern über Linux evdev kein Ereignis und können daher
  keine Home-Assistant-Automation auslösen.
- Bluetooth-Proxies genügen nicht, weil die Fernbedienung als lokales
  Linux-Eingabegerät verfügbar sein muss.
- Mehrere Fernbedienungen mit demselben Linux-Gerätenamen lassen sich nicht
  getrennt einrichten.

## Mehr erfahren

- [Ausführliche Dokumentation](DOKUMENTATION.md): Einrichtungsdetails,
  Bluetooth, Entkoppeln, Event-Attribute und Diagnose.
- [Tastenkombinationen der VU+ BT/IR-Fernbedienung](VU_BT_FERNBEDIENUNG_TASTENKOMBINATIONEN.md):
  Kopplungsmodus, Werksreset, Systemcode und TV-Funktionen.
- [Probleme oder Fragen melden](https://github.com/topic2k/VU-BT-RC/issues).

## Lizenz

Das Projekt steht unter der [MIT-Lizenz](LICENSE). Eine
[deutsche Übersetzung](LICENSE.de.md) dient zur Orientierung.
