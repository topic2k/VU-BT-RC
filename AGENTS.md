[Deutsch](AGENTS.md) | [English](AGENTS.en.md)

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

## Sprache / Language

- Integration und Dokumentation werden immer vollständig auf Deutsch und Englisch gepflegt.
- `strings.json` enthält die englischen Quelltexte. `translations/en.json` und
  `translations/de.json` enthalten dieselben Schlüssel und Platzhalter.
- Alle Oberflächentexte, Geräte- und Entitätsnamen sowie feste Auswahloptionen
  verwenden Home Assistants Übersetzungsmechanismus. Technische Kennungen bleiben
  sprachunabhängig; keine fest eingebauten deutschen Oberflächentexte im Python-Code.
- Deutsche Dokumentation liegt in `*.md`, die zugehörige englische Fassung in
  `*.en.md`. Beide Fassungen verlinken einander und werden im selben Arbeitsschritt
  aktualisiert. Dies gilt auch für Changelog, Release-Anleitung und Projektvorgaben.
- `LICENSE` enthält den maßgeblichen englischen MIT-Lizenztext;
  `LICENSE.de.md` enthält eine als solche gekennzeichnete deutsche Übersetzung.
- Neue Funktionen sind erst vollständig, wenn beide Sprachen und ihre Prüfungen
  aktualisiert sind.

## Dokumentation

README.md enthält die aktuelle, kompakte Nutzerdokumentation für GitHub und HACS.
Ausführliche Einrichtungs- und Referenzinformationen stehen in DOKUMENTATION.md.
CHANGELOG.md enthält ausschließlich die Versionshistorie.
Der Changelog wird nicht in README.md dupliziert.

CHANGELOG.md:
- beginnt mit einem Inhaltsverzeichnis
- führt die neueste Version zuerst
- erhält bei jeder relevanten Änderung einen neuen Eintrag

README.md:
- beginnt mit einem Inhaltsverzeichnis
- enthält nur aktuelle Informationen aus Sicht von Anwendern: Zweck, Funktionen,
  Installation, Einrichtung, Nutzung, Grenzen und weiterführende Links
- bleibt übersichtlich und verweist für technische Hintergründe auf
  DOKUMENTATION.md
- erledigte Punkte werden aus "Weiterentwicklung" entfernt
- enthält keine historische Versionsliste

## Versionierung

Bis zur ersten Veröffentlichung gehören Ergänzungen zur Version 1.0.0; der
Erstveröffentlichungseintrag wird in beiden Changelog-Fassungen aktualisiert.
Nach der ersten Veröffentlichung gilt:

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
4. Betroffene Dokumentationen und Changelogs in beiden Sprachen aktualisieren.
5. Keine ZIP-Datei erzeugen, sofern nicht ausdrücklich verlangt.
