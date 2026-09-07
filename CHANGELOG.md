# Changelog

## Inhaltsverzeichnis

- [1.0.1](#101)
- [1.0.0](#100)

[Deutsch](CHANGELOG.md) | [English](CHANGELOG.en.md)

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
