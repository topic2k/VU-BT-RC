[Deutsch](RELEASING.md) | [English](RELEASING.en.md)

# Veröffentlichung

## Inhaltsverzeichnis

- [Repository](#repository)
- [Prüfungen](#prüfungen)
- [Release veröffentlichen](#release-veröffentlichen)
- [HACS](#hacs)

## Repository

Das öffentliche Repository [topic2k/VU-BT-RC](https://github.com/topic2k/VU-BT-RC)
verwendet den Hauptzweig `main`. Die Installation ist in der
[README](README.md) beschrieben; die Release-Inhalte stehen im
[Changelog](CHANGELOG.md).

Repository-Einstellungen für HACS:

- Öffentliches Repository mit aktivierten Issues.
- Beschreibung: „Home Assistant integration for the VU+ Bluetooth remote via
  local Linux evdev.“
- Topics: `home-assistant`, `hacs`, `custom-integration`, `bluetooth`, `vuplus`,
  `evdev`.

Das Projekt steht unter der [MIT-Lizenz](LICENSE).

`documentation`, `issue_tracker` und `codeowners` im Integrationsmanifest
verweisen auf dieses Repository und `@topic2k`.

## Prüfungen

Mit Python 3.14 im Projektverzeichnis ausführen:

```sh
python -m pip install --group test
python -m unittest discover -s tests -v
python -m compileall -q custom_components tests
git diff --check
```

Vor einem Release müssen `version` in
`custom_components/vuplus_hid_raw/manifest.json`, `INTEGRATION_VERSION` in
`custom_components/vuplus_hid_raw/__init__.py`, der neueste Changelog-Eintrag
und der Git-Tag übereinstimmen. Der Tag erhält das Präfix `v`, zum Beispiel
`v1.0.2` für die Version `1.0.2`.

Der Workflow `.github/workflows/validate.yml` prüft auf GitHub die Tests,
Python-Syntax, Home-Assistant-Metadaten mit Hassfest und HACS-Anforderungen.
Die Tests prüfen außerdem identische Übersetzungsschlüssel und Platzhalter,
übersetzbare Entitäts- und Auswahlnamen sowie die Dokumentationsverweise.
Alle Dokumentationsänderungen werden gleichzeitig in Deutsch und Englisch gepflegt.
Die vollständige HACS-Prüfung benötigt das öffentliche GitHub-Repository samt
Beschreibung, Topics und aktivierten Issues.

Für das erste Release sind Installation über HACS sowie Hinzufügen,
Bluetooth-Kopplung und bestätigtes Entkoppeln mit der Fernbedienung geprüft.
Für spätere Funktionsänderungen auf der Zielplattform Home Assistant OS /
Raspberry Pi / aarch64 zusätzlich Tasten, Kurz- und Langdruck,
Wiederverbindung, Diagnoseanzeigen und beide Sprachen prüfen. Automatisierte
Tests mit simuliertem Home Assistant und BlueZ ersetzen diese Hardwaretests nicht.

## Release veröffentlichen

1. Den geprüften Projektstand lokal committen, sofern noch Änderungen offen sind.
2. `main` zum eingerichteten Remote `origin` übertragen:

   ```sh
   git push -u origin main
   ```

3. Die GitHub-Actions-Prüfungen für den zu veröffentlichenden Commit erfolgreich
   abschließen lassen. Den Hardwaretest aus dem Abschnitt [Prüfungen](#prüfungen)
   durchführen und ausstehende Testhinweise in beiden README-Fassungen anhand
   des tatsächlichen Ergebnisses aktualisieren.
4. Den geprüften Commit markieren und den Tag übertragen:

   ```sh
   git tag -a vX.Y.Z -m "Release X.Y.Z"
   git push origin vX.Y.Z
   ```

5. Auf GitHub ein Release zum Tag `vX.Y.Z` mit dem Titel `X.Y.Z` erstellen.
   Die Abschnitte `X.Y.Z` aus `CHANGELOG.md` und `CHANGELOG.en.md` als
   zweisprachige Beschreibung verwenden und als
   reguläres Release veröffentlichen.

Es ist kein zusätzliches ZIP-Release-Asset erforderlich. HACS verwendet den
Integrationsordner aus dem Repository am gewählten Release-Tag.

Ein Release kann vorab als **Entwurf** mit dem vorgesehenen Tag `vX.Y.Z` und
als Ziel dem geprüften Commit vorbereitet werden. Den Entwurf erst nach den
Prüfungen veröffentlichen. Bei weiteren Änderungen Ziel-Commit und zweisprachige
Release-Beschreibung aktualisieren. Ein Entwurf wird HACS-Nutzern nicht als
veröffentlichte Version angeboten.

## HACS

`hacs.json` setzt Home Assistant **2026.9.0** als Mindestversion. Die Dateien der
Integration liegen vollständig in `custom_components/vuplus_hid_raw`; die lokalen
Brand-Dateien befinden sich in dessen Unterordner `brand`.

Nach der Veröffentlichung kann das Repository in HACS als benutzerdefiniertes
Repository vom Typ **Integration** hinzugefügt werden. Ein Eintrag im
HACS-Standardkatalog ist ein separater Schritt und für diese Installation
nicht erforderlich. Für die Anzeige einer Release-Version in HACS ist ein
veröffentlichtes GitHub-Release erforderlich; ein Git-Tag allein reicht nicht.

Referenzen: [HACS-Anforderungen](https://www.hacs.xyz/docs/publish/start/),
[Integrationsstruktur](https://www.hacs.xyz/docs/publish/integration/),
[HACS-Validierung](https://www.hacs.xyz/docs/publish/action/).
