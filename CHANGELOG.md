[Deutsch](CHANGELOG.md) | [English](CHANGELOG.en.md)

# Changelog

## Inhaltsverzeichnis

- [1.2.0](#120)
- [1.1.1](#111)
- [1.1.0](#110)
- [1.0.3](#103)
- [1.0.2](#102)
- [1.0.1](#101)
- [1.0.0](#100)

## 1.2.0

- Die Bluetooth-Kopplungssuche blendet bereits gekoppelte, gebundene, verbundene
  und in der Integration eingerichtete Fernbedienungen anhand ihrer Adresse aus,
  auch über mehrere Adapter hinweg. Dialogtexte und Dokumentation angepasst;
  Filterung und leere Ergebnislisten mit simulierten Geräten getestet.
  Erfolgreiche Filterung vom Nutzer am 12.09.2026 im Praxistest bestätigt.

- Mehrere gleichnamige VU+ Fernbedienungen über die Bluetooth-Adresse in evdev
  `uniq` getrennt einrichten. Auswahl, Gerätenamen und Reconnect berücksichtigen
  die feste Adresse; wechselnde Event-Pfade werden weiterhin nicht gespeichert.
- Bestehende Einträge können über **Neu konfigurieren** eindeutig zugeordnet
  werden, ohne Geräte-, Entitäts- oder Automationszuordnungen zu ersetzen.
  Vorhandene Bluetooth-Zuordnungen werden übernommen. Ohne eindeutige Auswahl
  wird kein beliebiges Gerät gelesen.
- Koppelassistent, Diagnose und bestätigtes Entkoppeln berücksichtigen die
  ausgewählte Fernbedienung. Tests für zwei gleichnamige Geräte, getrennte
  Tastenereignisse, Pfadwechsel, fehlende Geräte und Bestandszuordnung ergänzt.
  Lokal mit simulierten Geräten geprüft. Host-Ausgabe vom 12.09.2026 bestätigt
  unterschiedliche `uniq`-Adressen bei zwei Geräten; deren tatsächlicher
  Parallelbetrieb und Reconnects sind noch nicht getestet.

## 1.1.1

- Feste Blueprint-Quelladressen, sichtbare Versionen und sprachspezifische Import-Links ergänzt. Optionale Update-Hinweise mit Blueprints Updater und Umstellung vorhandener lokaler Dateien dokumentiert.

- Template-Abbruch im Blueprint durch die nicht verfügbare Funktion
  `has_service` behoben. Fehlerhafte Test-Nachbildung entfernt, damit die
  Template-Tests diesen Fehler erkennen. Nicht registrierte Aktionen werden
  beim Aufruf von Home Assistant gemeldet.

## 1.1.0

- Deutschen und englischen Blueprint ergänzt: Eine Automation ordnet kurze
  Tastendrücke den Zielen zu. HAVUOpenWebif-Receiver werden anhand von Enigma2-
  Keycodes automatisch zugeordnet; alternativ sind Zielpräfixe und explizite
  Zuordnungen möglich. Mehrdeutige Treffer benötigen ein explizites Ziel.
- Bedingungen können einzelne Tasten umleiten oder das gesamte Zielprofil
  wechseln. Alternative Ziele unterstützen Buttons, Media Player, Schalter,
  Skripte, Szenen, Lichter, Ventilatoren, Rollläden und Helfer.
- Entitätsauswahl mit Typfilter und Freitextsuche sowie eine gemeinsame
  Aktionsliste im selben Dialog ergänzt. Aktionsdaten und das Deaktivieren
  einzelner Tasten sind konfigurierbar. Benutzer prüfen die Geräteunterstützung.
- Fehlende, nicht verfügbare und nicht zum Aktionstyp passende Ziele werden
  übersprungen. Anleitung und automatisierte Blueprint-Prüfungen ergänzt.
- Referenz: HAVUOpenWebif 1.1.0, Commit
  `f20b23d74b6b63f343dd42d2177dec22df068d76`. Geprüft durch Quellcodeprüfung
  und lokale Simulation; kein bestätigter Receiver-Test. Andere oder neuere
  HAVUOpenWebif-Versionen können die Zuordnung beeinträchtigen.
- Projekt- und Release-Vorgaben für Entwicklungsversionsnummern, Versionsabgleich
  vor Pull Requests, freigegebene Übernahme nach main und beauftragte Releases
  in beiden Sprachen dokumentiert.

## 1.0.3

- Eindeutige Standardnamen für die Event-Entitäten Lautstärke Plus/Minus und
  Kanal Plus/Minus ergänzt, damit Home Assistant keine numerischen Suffixe wie
  `_2` erzeugen muss.

## 1.0.2

- Sprachumschalter in allen zweisprachigen Dokumentationen an den Anfang verschoben.
- Installation über HACS sowie Hinzufügen, Bluetooth-Kopplung und bestätigtes
  Entkoppeln mit der Fernbedienung getestet.

## 1.0.1

- Kompakte Logo-Variante für README und Dokumentation ergänzt und dort verwendet.

## 1.0.0

Erstveröffentlichung der Home-Assistant-Integration **VU+ HID Raw Remote**.

- Anbindung der VU+ Bluetooth-Fernbedienung `VUPLUS-BLE-RCU` über lokale
  Linux-evdev-Geräte für Home Assistant ab 2026.9.0.
- Einrichtung über die Oberfläche mit optionaler Bluetooth-Suche, Kopplung,
  Vertrauenseinstellung und Verbindung über BlueZ.
- Geräteerkennung anhand des Linux-Gerätenamens und automatische Wiederverbindung
  bei wechselnden `/dev/input/eventX`-Pfaden.
- Eigene Event-Entität für jede unterstützte Taste als Automationsschnittstelle,
  einschließlich der über `MSC_SCAN` unterscheidbaren Sondertasten.
- Kurz- und Langdruck, Loslassen und Wiederholung mit konfigurierbarer
  Langdruck-Schwelle; Ereignistypen `press_start`, `press_end`, `long_press_start`,
  `long_press_end` und `repeat`.
- Geräteinformationen mit Icon und Logo sowie fünf Diagnose-Binärsensoren für
  Kopplung, Bluetooth-Verbindung, Vertrauen, Eingabegerät und Reader-Zustand.
- Optionale Entkopplung über einen bestätigten Reparaturdialog nach dem Löschen
  des Integrationseintrags.
- Deutsche und englische Oberfläche einschließlich Geräte- und Entitätsnamen,
  Reparaturauswahl und vollständig zweisprachiger Dokumentation.
- HACS-Repositorystruktur, Installationsanleitung, Fernbedienungsanleitung und
  automatische Prüfungen für Python, Home Assistant und HACS.
- GitHub-Projektlogo und Konfiguration für zusätzliche Entwicklungswerkzeuge.
- Kompaktes README für GitHub und HACS; ausführliche Einrichtungs- und
  Referenzinformationen sind in die separate Dokumentation ausgelagert.

`TV Power` und `AV` liefern über die verwendete evdev-Schnittstelle keine
Ereignisse und stehen nicht als Automationsauslöser zur Verfügung.
