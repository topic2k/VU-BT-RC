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
Das Gerät wird anhand seines Namens und, sofern vorhanden, der Bluetooth-Adresse
aus evdev `uniq` gesucht. Gleichnamige Fernbedienungen müssen über diese Adresse
unterschieden werden; bei Mehrdeutigkeit darf kein beliebiges Gerät gewählt werden.
Die Event-Nummer darf nicht gespeichert werden.

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

Für die HAVUOpenWebif-Anbindung des Blueprints müssen geprüfte Version, genauer
Commit und tatsächlicher Prüfumfang in beiden Sprachfassungen dokumentiert sein.
Quellcodeprüfung und simulierte Tests nicht als Test am Receiver bezeichnen.
Auf mögliche Inkompatibilität anderer/neuerer Versionen hinweisen; bei einer neuen
Prüfbasis auch Blueprint-Beschreibungen und Testreferenz gemeinsam aktualisieren.

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

## Branches, Freigabe und Releases

- Änderungen zuerst auf `develop` oder bei Bedarf auf einem neuen Arbeitsbranch
  umsetzen; keine direkten Änderungen oder Commits auf `main`.
- Änderungen erst nach ausdrücklicher Freigabe durch den Nutzer und ausschließlich
  per Pull Request nach `main` übernehmen.
- Ein neues Release nur auf ausdrückliche Anweisung des Nutzers erstellen.
  Die Freigabe von Änderungen oder eines Pull Requests ist keine Release-Freigabe.
- Die folgenden Versionierungsregeln erlauben keine automatische Veröffentlichung.

## Versionierung

- Bei Änderungen auf `develop` oder einem Arbeitsbranch die Version automatisch
  und ohne gesonderte Aufforderung passend zum gesamten unveröffentlichten Umfang
  gegenüber der letzten stabilen Version erhöhen: Patch für Fehlerkorrekturen,
  interne Änderungen und reine Dokumentation, Minor für rückwärtskompatible neue
  Funktionen, Major für inkompatible Änderungen.
- Entwicklungsstände verwenden `X.Y.Z-dev.N`, beginnend mit `dev.1`, zum Beispiel
  `1.1.0-dev.1`. Bei weiteren abgeschlossenen Änderungen an derselben Zielversion
  den Zähler erhöhen; bei einer höheren Zielversion wieder mit `dev.1` beginnen.
  Nicht für jeden einzelnen Dateiedit eine neue Version vergeben.
- `version` in `manifest.json`, `INTEGRATION_VERSION` und der neueste Eintrag in
  beiden Changelogs müssen einschließlich Entwicklungssuffix übereinstimmen.
  Den Changelog-Eintrag ausdrücklich als unveröffentlichte Entwicklerversion
  kennzeichnen und bei weiteren Änderungen derselben Zielversion fortschreiben.
- Unmittelbar vor jedem Pull Request nach `main` den aktuellen Remote-Stand von
  `main`, die Tags und die veröffentlichten Releases abrufen. Die nächste passende
  Version anhand des letzten stabilen Releases und des gesamten vorgesehenen
  Änderungsumfangs neu bestimmen. Zwischenzeitliche Versionsanhebungen durch
  andere Branches oder Commits berücksichtigen; keine bereits veröffentlichte
  oder auf `main` vergebene Version erneut verwenden und keine Version absenken.
- Noch auf dem Arbeitsbranch das vollständige Suffix `-dev.N` entfernen und
  Manifest, `INTEGRATION_VERSION`, beide Changelogs und deren Inhaltsverzeichnisse
  synchronisieren. Den Eintrag bis zur Veröffentlichung als unveröffentlicht,
  aber nicht mehr als Entwicklerversion kennzeichnen. Danach die Prüfungen erneut
  ausführen. Ohne aktuellen Remote-Abgleich ist diese Vorbereitung unvollständig.
- Wenn sich `main` oder die Release-Basis während eines offenen Pull Requests
  ändert, den Versionsabgleich vor dem Merge wiederholen und nötige Anpassungen
  im Quellbranch vornehmen. Die Übernahme erfolgt erst nach Nutzerfreigabe.
  Eine Version ohne Entwicklungssuffix oder ein Merge erlaubt keine automatischen
  Tags oder Releases; dafür bleibt eine ausdrückliche Release-Anweisung nötig.

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
