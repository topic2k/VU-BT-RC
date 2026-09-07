# AGENTS.md

## Projekt

Dies ist eine Home-Assistant-Custom-Integration zur Anbindung der VU+ Bluetooth-Fernbedienung VUPLUS-BLE-RCU über Linux evdev.

## Zielplattform

- Home Assistant 2026.9.x
- Home Assistant OS
- Python 3.14
- Raspberry Pi / aarch64
- lokale Linux-evdev-Eingabegeräte

## Automationsschnittstelle

Die Event-Entity ist die einzige Automationsschnittstelle. Es gibt weder das
Bus-Event `vuplus_remote_command` noch integrationsspezifische Device Triggers.

## Eingabegerät

Das relevante evdev-Gerät heißt normalerweise `VUPLUS-BLE-RCU Keyboard`.
Nicht dauerhaft von einem festen `/dev/input/eventX` ausgehen. Die Event-Nummer kann sich nach Bluetooth-Reconnects ändern.
Das Gerät wird anhand seines Namens gesucht. Die Event-Nummer darf nicht gespeichert
werden.

## Async-Regeln

Home Assistant darf nicht durch blockierende I/O-Operationen im Event-Loop blockiert werden. Insbesondere evdev.list_devices(), das Öffnen von InputDevice und vergleichbare blockierende Operationen müssen entsprechend der Home-Assistant-Async-Konvention behandelt werden.

## Fernbedienung

Die Integration unterscheidet `press`, `repeat`, `long_press`, `short_release` und `long_release`. Die Schwelle für Long Press ist konfigurierbar.

## Home-Assistant-Integration

Die Integration soll sich möglichst vollständig in Home Assistant integrieren:
- Config Flow
- Device Registry
- Event-Entity als alleinige Automationsschnittstelle
- auswählbare Ereignistypen und Attributfilter in der Automation UI

## Bekannte Einschränkungen

TV Power und AV erzeugen auf der aktuell verwendeten Linux-evdev-Schnittstelle kein Event. Diese Tasten dürfen daher nicht einfach als funktionierend implementiert oder dokumentiert werden.

## Dokumentation

README.md enthält ausschließlich die aktuelle technische Dokumentation.
CHANGELOG.md enthält ausschließlich die Versionshistorie.
Der Changelog wird nicht in README.md dupliziert.

CHANGELOG.md:
- beginnt mit einem Inhaltsverzeichnis
- führt die neueste Version zuerst
- erhält bei jeder relevanten Änderung einen neuen Eintrag

README.md:
- beginnt mit einem Inhaltsverzeichnis
- enthält nur aktuelle Informationen
- erledigte Punkte werden aus "Weiterentwicklung" entfernt
- enthält keine historische Versionsliste

## Versionierung

Bei einer nutzerrelevanten Änderung Version in manifest.json erhöhen und CHANGELOG.md ergänzen. Keine künstlichen Release-Versionen für reine interne Kleinständerungen erzeugen.
Reine Dokumentationsänderungen erhöhen ausschließlich die Patch-Version der Integration.

## Entwicklungsregeln

Vor Änderungen:
1. Bestehenden Code analysieren.
2. Bestehende Funktionalität nachvollziehen.
3. Einen kurzen Implementierungsplan erstellen.

Nach Änderungen:
1. Tests ausführen.
2. Python-Syntax prüfen.
3. Home-Assistant-Kompatibilität prüfen, soweit lokal möglich.
4. README.md und CHANGELOG.md aktualisieren.
5. Keine ZIP-Datei erzeugen, sofern nicht ausdrücklich verlangt.
