# Veröffentlichung

## Inhaltsverzeichnis

- [Repository](#repository)
- [Prüfungen](#prüfungen)
- [Release veröffentlichen](#release-veröffentlichen)
- [HACS](#hacs)

[Deutsch](RELEASING.md) | [English](RELEASING.en.md)

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
python -m pip install -r requirements-test.txt
python -m unittest discover -s tests -v
python -m compileall -q custom_components tests
git diff --check
```

Vor einem Release müssen `version` in
`custom_components/vuplus_hid_raw/manifest.json`, `INTEGRATION_VERSION` in
`custom_components/vuplus_hid_raw/__init__.py`, der neueste Changelog-Eintrag
und der Git-Tag übereinstimmen. Für die Erstveröffentlichung lautet die Version
`1.0.0`, der Tag `v1.0.0`.

Der Workflow `.github/workflows/validate.yml` prüft auf GitHub die Tests,
Python-Syntax, Home-Assistant-Metadaten mit Hassfest und HACS-Anforderungen.
Die Tests prüfen außerdem identische Übersetzungsschlüssel und Platzhalter,
übersetzbare Entitäts- und Auswahlnamen sowie die Dokumentationsverweise.
Alle Dokumentationsänderungen werden gleichzeitig in Deutsch und Englisch gepflegt.
Die vollständige HACS-Prüfung benötigt das öffentliche GitHub-Repository samt
Beschreibung, Topics und aktivierten Issues.

Zusätzlich auf der Zielplattform Home Assistant OS / Raspberry Pi / aarch64
prüfen: frische Installation, Bluetooth-Kopplung, alle unterstützten Tasten,
Kurz- und Langdruck, Wiederverbindung, Diagnoseanzeigen und beide Entscheidungen
im Reparaturdialog nach dem Löschen, jeweils mit deutscher und englischer Spracheinstellung. Automatisierte Tests mit simuliertem
Home Assistant und BlueZ ersetzen diesen Hardwaretest nicht.

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
   git tag -a v1.0.0 -m "Release 1.0.0"
   git push origin v1.0.0
   ```

5. Auf GitHub ein Release zum Tag `v1.0.0` mit dem Titel `1.0.0` erstellen.
   Die Abschnitte `1.0.0` aus `CHANGELOG.md` und `CHANGELOG.en.md` als
   zweisprachige Beschreibung verwenden und als
   reguläres Release veröffentlichen.

Es ist kein zusätzliches ZIP-Release-Asset erforderlich. HACS verwendet den
Integrationsordner aus dem Repository am gewählten Release-Tag.

Ein Release kann vorab als **Entwurf** mit dem vorgesehenen Tag `v1.0.0` und
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
