[Deutsch](VU_BT_FERNBEDIENUNG_TASTENKOMBINATIONEN.md) | [English](VU_BT_FERNBEDIENUNG_TASTENKOMBINATIONEN.en.md)

# VU+ BT/IR-Fernbedienung: Tastenkombinationen

## Inhaltsverzeichnis

- [Geltungsbereich und Schreibweise](#geltungsbereich-und-schreibweise)
- [Schnellübersicht](#schnellübersicht)
- [Bluetooth-Kopplung](#bluetooth-kopplung)
- [Werkseinstellungen der Fernbedienung](#werkseinstellungen-der-fernbedienung)
- [Receiver-Systemcode](#receiver-systemcode)
- [TV-Funktionen einrichten](#tv-funktionen-einrichten)
- [TV-Herstellercodes](#tv-herstellercodes)
- [Hinweise zur Home-Assistant-Integration](#hinweise-zur-home-assistant-integration)
- [Quellen](#quellen)

## Geltungsbereich und Schreibweise

Diese Anleitung gilt für die VU+ **BT/IR-Fernbedienung** (Typ V) mit dem
Bluetooth-Namen `VUPLUS-BLE-RCU`, nicht für ältere reine IR-Fernbedienungen.

`[A] + [B] halten` bedeutet: beide Tasten gleichzeitig gedrückt halten, bis die
beschriebene LED-Rückmeldung erscheint. Ziffernfolgen und einzeln aufgeführte
Tasten werden anschließend kurz gedrückt.

> Achtung: Ein Werksreset betrifft die **Fernbedienung**, nicht den VU+-Receiver.
> Dabei werden laut Handbuch sowohl die Bluetooth-Kopplung als auch die
> IR-/TV-Programmierung gelöscht.

## Schnellübersicht

| Zweck | Tastenkombination | Erfolgsanzeige |
| --- | --- | --- |
| Bluetooth-Kopplungsmodus | `[MENU] + [AUDIO]` halten | Rote LED leuchtet |
| Fernbedienung zurücksetzen | `[PVR] + [EXIT]` etwa 5 Sekunden halten | Rote LED blinkt dreimal |
| Receiver-Systemcode ändern | `[STB POWER] + [OK]` halten, `0000x`, `[OK]` | LED blinkt beim Speichern zweimal |
| TV-Herstellercode eingeben | `[TV POWER] + [OK]` halten, fünfstelligen Code, `[OK]` | LED blinkt beim Speichern zweimal |
| TV-Code automatisch suchen | `[TV POWER] + [OK]` halten, `[CH+]` oder `[CH-]`, `[OK]` | TV schaltet aus; anschließend mit OK speichern |
| Lautstärke TV oder Receiver zuordnen | `[TV POWER] + [OK]` halten, `[TV POWER]` oder `[STB POWER]` | LED blinkt zweimal |

## Bluetooth-Kopplung

1. Auf einem VU+-Receiver das Bluetooth-Setup öffnen und Bluetooth aktivieren.
   Für die Home-Assistant-Integration stattdessen im Config Flow
   **Bluetooth-Fernbedienung koppeln** wählen und die Suche starten.
2. `[MENU]` und `[AUDIO]` gleichzeitig gedrückt halten, bis die rote LED leuchtet.
3. Die Fernbedienung in der Suche auswählen und die Kopplung abschließen.

Die Fernbedienung funktioniert grundsätzlich auch per IR. Sobald die
Bluetooth-Verbindung aktiv ist, wird die normale IR-Übertragung laut Handbuch
automatisch deaktiviert; die Lautstärke-Weitergabe (Volume Punch) ist davon
ausgenommen.

## Werkseinstellungen der Fernbedienung

1. `[PVR]` und `[EXIT]` gleichzeitig etwa fünf Sekunden gedrückt halten.
2. Erst loslassen, nachdem die rote LED dreimal geblinkt hat.
3. Die Fernbedienung befindet sich wieder im Auslieferungszustand: gespeicherte
   Bluetooth-Kopplungen und die TV-/IR-Programmierung sind gelöscht.
4. Danach bei Bedarf neu koppeln und TV-Funktionen erneut einrichten.

Das Entfernen der Batterien ist **kein** Werksreset. Die gespeicherten Bluetooth-
und IR-Einstellungen bleiben dabei erhalten.

## Receiver-Systemcode

Der Systemcode muss nur geändert werden, wenn Fernbedienung und VU+-Receiver auf
unterschiedliche Codes eingestellt sind. Standard ist Modus 2. Vor dem Wechsel
eine vorhandene Bluetooth-Verbindung trennen.

1. `[STB POWER]` und `[OK]` etwa drei Sekunden gedrückt halten, bis die LED leuchtet.
2. Einen fünfstelligen Code eingeben:

   | Code | Modus | Vorgesehene Geräte |
   | --- | --- | --- |
   | `00001` | 1 | Duo, Solo |
   | `00002` | 2 (Standard) | Aktuelle VU+-Modelle, z. B. Ultimo 4K, Uno 4K, Duo², Solo 4K, Solo², Solo SE und Zero |
   | `00003` | 3 | Reserviert bzw. nur bei passend umgestelltem Receiver |
   | `00004` | 4 | Reserviert bzw. nur bei passend umgestelltem Receiver |

3. Mit `[OK]` speichern. Die rote LED blinkt zur Bestätigung zweimal.

Der Receiver muss denselben Systemcode verwenden. Den Receiver-Code stellt man
über dessen Erweiterung **Code der Fernbedienung** ein und startet anschließend
die Benutzeroberfläche neu.

## TV-Funktionen einrichten

Diese Einstellungen betreffen die Universalfernbedienungsfunktionen für TV
(TV Power, AV, Lautstärke und Stummschaltung). Die Automationskonfiguration in
Home Assistant bleibt dabei erhalten; die Lautstärke-Zuordnung kann jedoch
beeinflussen, ob diese Tasten per IR an den TV gesendet werden.

### Hersteller-Code manuell eingeben

1. TV einschalten.
2. `[TV POWER] + [OK]` etwa drei Sekunden halten, bis die LED leuchtet.
3. Den fünfstelligen Hersteller-Code eingeben.
4. `[OK]` drücken, um zu speichern.

Nach erfolgreicher Einrichtung steuern `[VOL+]`, `[VOL-]` und `[MUTE]` den TV.

### Hersteller-Code automatisch suchen

1. TV einschalten und `[TV POWER] + [OK]` halten, bis die LED leuchtet.
2. `[CH+]` oder `[CH-]` wiederholt drücken. Mit jedem Tastendruck wird ein
   Ausschaltcode an den TV gesendet.
3. Sobald der TV ausgeht, `[OK]` drücken, um den gefundenen Code zu speichern.

### Lautstärke wieder dem Receiver zuordnen

1. `[TV POWER] + [OK]` halten, bis die LED leuchtet.
2. `[TV POWER]` drücken, damit Lautstärke und Stummschaltung den TV steuern,
   oder `[STB POWER]`, damit sie wieder den Receiver steuern.

## TV-Herstellercodes

Die Datenbank enthält je nach Baureihe mehrere passende Codes für dieselbe Marke.
Die folgenden Codes sind ein Auszug für gängige Hersteller. Sie sind genau in der
angegebenen Reihenfolge zu testen: Einstellungen mit `[TV POWER] + [OK]` öffnen,
einen Code eingeben und anschließend mit `[OK]` speichern.

| Hersteller | Fünfstellige TV-Codes |
| --- | --- |
| Acer | `10746`, `10640` |
| AOC | `10016` |
| Beko | `10691`, `10690`, `10510`, `10296`, `10263`, `10255`, `10250`, `10225`, `10195`, `10130`, `10117`, `10108`, `10090`, `10086`, `10085`, `10049` |
| Hisense | `10772`, `10753`, `10752`, `10551`, `10302` |
| LG | `10708`, `10707`, `10634`, `10592`, `10553`, `10512`, `10511`, `10509`, `10504`, `10503`, `10502`, `10501`, `10446`, `10440`, `10439`, `10437`, `10288`, `10286`, `10283`, `10263`, `10250`, `10181`, `10110`, `10108`, `10090`, `10069`, `10038`, `10015`, `10014`, `10013` |
| Panasonic | `10740`, `10639`, `10595`, `10508`, `10254`, `10168`, `10167` |
| Samsung | `10743`, `10738`, `10712`, `10693`, `10692`, `10607`, `10601`, `10550`, `10514`, `10506`, `10505`, `10284`, `10268`, `10257`, `10237`, `10220`, `10171`, `10126`, `10108`, `10086`, `10045` |
| Sharp | `10749`, `10748`, `10714`, `10646`, `10644`, `10568`, `10567`, `10558`, `10557`, `10556`, `10432`, `10423`, `10224`, `10171`, `10084`, `10083`, `10082`, `10081`, `10073` |
| Sony | `10213`, `10212`, `10211` |
| TCL | `10716`, `10668`, `10565`, `10564`, `10563`, `10562`, `10561`, `10152` |
| Technisat | `10248`, `10118`, `10108` |
| Telefunken | `10688`, `10679`, `10530`, `10270`, `10261`, `10225`, `10195`, `10193` |
| Thomson | `10716`, `10668`, `10565`, `10564`, `10563`, `10562`, `10561`, `10270`, `10261`, `10195`, `10193` |

Die [vollständige TV-Code-Liste im VU+-Handbuch](https://www.tvdigitalne.cz/user/related_files/vu_plus_bt_ir_english.pdf)
umfasst zahlreiche weitere Marken. Falls kein Code funktioniert, die automatische
Codesuche verwenden statt weitere Codes anderer Hersteller auszuprobieren.

## Hinweise zur Home-Assistant-Integration

- Der Werksreset entfernt die Kopplung aus der Fernbedienung. Falls der
  Home-Assistant-Host danach noch einen veralteten BlueZ-Eintrag führt, diesen
  vor einer erneuten Kopplung dort entfernen.
- Für die Integration muss nach der Kopplung das lokale evdev-Gerät
  `VUPLUS-BLE-RCU Keyboard` erscheinen. Die wechselnde Nummer von
  `/dev/input/eventX` ist unerheblich.
- `TV POWER` und `AV` lösen auf der verwendeten Linux-evdev-Schnittstelle keine
  Ereignisse aus. Sie stehen deshalb nicht als Home-Assistant-Trigger bereit.

## Quellen

- [VU+ WIKI: Fernbedienung – Programmierung Typ V](https://wiki.vuplus-support.org/index.php?title=Fernbedienung#Programmierung_(Typ_V)) – Kopplung, Werksreset, TV- und Systemcode-Einstellungen.
- [VU+ Bluetooth Remote Manual (Ultimo 4K BLE RCU)](https://www.tvdigitalne.cz/user/related_files/vu_plus_bt_ir_english.pdf) – Haltezeiten, LED-Rückmeldungen sowie Umfang des Werksresets.
- [TV-Code-Liste im VU+ Bluetooth Remote Manual](https://www.tvdigitalne.cz/user/related_files/vu_plus_bt_ir_english.pdf) – vollständige Hersteller- und Code-Datenbank.

Die Einrichtung und Nutzung in Home Assistant beschreibt die [README](README.md).
