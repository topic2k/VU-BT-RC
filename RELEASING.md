[Deutsch](RELEASING.md) | [English](RELEASING.en.md)

# Veröffentlichung

## Inhaltsverzeichnis

- [Repository](#repository)
- [Entwicklerversionen](#entwicklerversionen)
- [Version vor dem Pull Request](#version-vor-dem-pull-request)
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

## Entwicklerversionen

Änderungen entstehen auf `develop` oder einem Arbeitsbranch. Die Version wird
dabei automatisch anhand aller Änderungen seit der letzten stabilen Version
erhöht: Patch für Korrekturen, interne Änderungen und Dokumentation, Minor für
rückwärtskompatible neue Funktionen, Major für inkompatible Änderungen.
Entwicklungsstände tragen das Suffix `-dev.N`, zum Beispiel `1.1.0-dev.1`.
Weitere abgeschlossene Änderungen derselben Zielversion erhöhen den Zähler;
bei einer höheren Zielversion beginnt er wieder bei 1.

Manifest, `INTEGRATION_VERSION` und beide Changelogs verwenden dieselbe vollständige
Version. Die Changelogs kennzeichnen sie als unveröffentlicht. Das Format verwendet
SemVer mit einer Vorabversionskennung, wie von den
[Home-Assistant-Manifestregeln](https://developers.home-assistant.io/docs/creating_integration_manifest/#version)
unterstützt.

Änderungen gelangen ausschließlich nach Nutzerfreigabe per Pull Request nach
`main`. Das Entwicklungssuffix wird unmittelbar vor dem Pull Request entfernt.
Eine Merge-Freigabe erlaubt kein Release.

## Version vor dem Pull Request

1. Unmittelbar vor einem Pull Request nach `main` Remote-Branches und Tags
   aktualisieren sowie die veröffentlichten Releases auf GitHub prüfen. Lokale
   Versionsangaben oder Tags allein reichen für diesen Abgleich nicht aus.
2. Ausgehend vom letzten stabilen Release und dem gesamten vorgesehenen
   Änderungsumfang die nächste passende Patch-, Minor- oder Major-Version
   bestimmen. Versionsanhebungen durch andere Branches oder Commits seit Beginn
   der Arbeit berücksichtigen. Die Zielversion darf weder bereits veröffentlicht
   noch auf `main` vergeben sein und darf keine Versionsabsenkung verursachen.
3. Auf dem Quellbranch die ermittelte Version ohne `-dev.N` in Manifest,
   `INTEGRATION_VERSION` und beiden Changelogs setzen. Inhaltsverzeichnisse
   anpassen und den Eintrag als unveröffentlicht kennzeichnen; nur die
   Kennzeichnung als Entwicklerversion entfällt. Veröffentlichte Historie erhalten.
4. Die [Prüfungen](#prüfungen) erneut ausführen und die Versionsanpassung im
   Pull Request mitführen. Ohne aktuellen Remote-Abgleich ist die Vorbereitung
   nicht abgeschlossen.
5. Ändert sich `main` oder die Release-Basis während des offenen Pull Requests,
   den Abgleich vor dem Merge wiederholen und nötige Änderungen im Quellbranch
   vornehmen. Erst nach Nutzerfreigabe mergen.

Dieser Ablauf erstellt weder einen Tag noch ein Release. Auch eine Version ohne
Entwicklungssuffix bleibt bis zur ausdrücklichen Release-Anweisung unveröffentlicht.

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

Voraussetzung ist eine ausdrückliche Release-Anweisung des Nutzers. Dies gilt
auch für Release-Entwürfe und Release-Tags.

1. Die zu veröffentlichende Version und ihren Commit auf `main` prüfen. Bei
   noch ausstehenden Änderungen den Ablauf unter
   [Version vor dem Pull Request](#version-vor-dem-pull-request) durchlaufen.
2. Im Rahmen der beauftragten Veröffentlichung die Kennzeichnung als
   unveröffentlicht in beiden Changelogs entfernen. Auch diese Änderung auf einem
   Arbeitsbranch vorbereiten und nach Nutzerfreigabe per Pull Request übernehmen;
   dabei den Versionsabgleich erneut durchführen.

3. Die GitHub-Actions-Prüfungen für den zu veröffentlichenden Commit erfolgreich
   abschließen lassen. Den Hardwaretest aus dem Abschnitt [Prüfungen](#prüfungen)
   durchführen und ausstehende Testhinweise in beiden README-Fassungen anhand
   des tatsächlichen Ergebnisses aktualisieren.
4. Den geprüften Commit auf `main` markieren und den Tag übertragen:

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

Blueprint-Updates verwenden die feste `source_url` auf `main`. Blueprint-Änderungen
erst übernehmen, wenn sie verteilt werden sollen: Updater können sie sofort nach
dem Merge erkennen, ohne auf ein GitHub-Release zu warten. Dateinamen und
Quelladressen stabil halten. Bei Blueprint-Änderungen die sichtbare Version in
beiden Beschreibungen auf die Release-Version setzen (Entwicklungssuffix vor dem
PR entfernen). Bei Releases ohne Blueprint-Änderungen die Blueprint-Version
beibehalten, um unnötige Update-Hinweise zu vermeiden. Die HAVUOpenWebif-Prüfbasis
separat pflegen.
Import, Update-Erkennung und Installation nach Möglichkeit in Home Assistant mit
Blueprints Updater testen; tatsächliche Ergebnisse dokumentieren und lokale
Metadatentests nicht als vollständigen Integrationstest ausgeben. Der Updater
bleibt optional.

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
