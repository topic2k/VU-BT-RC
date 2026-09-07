[Deutsch](VU_BT_FERNBEDIENUNG_TASTENKOMBINATIONEN.md) | [English](VU_BT_FERNBEDIENUNG_TASTENKOMBINATIONEN.en.md)

# VU+ BT/IR remote: button combinations

## Contents

- [Scope and notation](#scope-and-notation)
- [Quick reference](#quick-reference)
- [Bluetooth pairing](#bluetooth-pairing)
- [Factory reset](#factory-reset)
- [Receiver system code](#receiver-system-code)
- [TV functions](#tv-functions)
- [TV manufacturer codes](#tv-manufacturer-codes)
- [Home Assistant integration notes](#home-assistant-integration-notes)
- [Sources](#sources)

## Scope and notation

This guide covers the VU+ **BT/IR remote** (Type V), Bluetooth name
`VUPLUS-BLE-RCU`, rather than older IR-only remotes.

“Hold `[A] + [B]`” means pressing both buttons together until the indicated LED
response. Press subsequent digit sequences and individually listed buttons briefly.

> A factory reset affects the **remote**, not the VU+ receiver. According to the
> manual, it clears both Bluetooth pairing and IR/TV programming.

## Quick reference

| Purpose | Button combination | Confirmation |
| --- | --- | --- |
| Bluetooth pairing mode | Hold `[MENU] + [AUDIO]` | Red LED lights up |
| Reset the remote | Hold `[PVR] + [EXIT]` for about 5 seconds | Red LED flashes three times |
| Change receiver system code | Hold `[STB POWER] + [OK]`, enter `0000x`, press `[OK]` | LED flashes twice when saved |
| Enter TV manufacturer code | Hold `[TV POWER] + [OK]`, enter five-digit code, press `[OK]` | LED flashes twice when saved |
| Search TV code automatically | Hold `[TV POWER] + [OK]`, press `[CH+]` or `[CH-]`, then `[OK]` | TV switches off; save with OK |
| Assign volume to TV or receiver | Hold `[TV POWER] + [OK]`, press `[TV POWER]` or `[STB POWER]` | LED flashes twice |

## Bluetooth pairing

1. On a VU+ receiver, open Bluetooth setup and enable Bluetooth. For Home
   Assistant, instead select **Pair a Bluetooth remote** in the integration's
   config flow and start discovery.
2. Hold `[MENU]` and `[AUDIO]` together until the red LED lights up.
3. Select the remote in discovery and complete pairing.

The remote also supports IR operation. According to the manual, normal IR
transmission is automatically disabled while Bluetooth is connected, except for
volume forwarding (Volume Punch).

## Factory reset

1. Hold `[PVR]` and `[EXIT]` together for about five seconds.
2. Release them after the red LED has flashed three times.
3. The remote is back to factory settings: stored Bluetooth pairings and TV/IR
   programming have been cleared.
4. Pair it again and reconfigure TV functions as needed.

Removing the batteries is **not** a factory reset. Stored Bluetooth and IR
settings are retained.

## Receiver system code

Only change the system code if the remote and VU+ receiver are configured to use
different codes. The default is mode 2. Disconnect Bluetooth before changing it.

1. Hold `[STB POWER]` and `[OK]` for about three seconds until the LED lights up.
2. Enter a five-digit code:

   | Code | Mode | Intended devices |
   | --- | --- | --- |
   | `00001` | 1 | Duo, Solo |
   | `00002` | 2 (default) | Current VU+ models, e.g. Ultimo 4K, Uno 4K, Duo², Solo 4K, Solo², Solo SE and Zero |
   | `00003` | 3 | Reserved, or only for a receiver configured accordingly |
   | `00004` | 4 | Reserved, or only for a receiver configured accordingly |

3. Press `[OK]` to save. The red LED flashes twice.

The receiver must use the same system code. Set its code through the **Remote
control code** extension and then restart the receiver's user interface.

## TV functions

These settings control the universal remote's TV functions (TV Power, AV, volume
and mute). They do not change your Home Assistant automation configuration, but
volume assignment can affect whether those buttons are sent to the TV over IR.

### Enter a manufacturer code manually

1. Switch on the TV.
2. Hold `[TV POWER] + [OK]` for about three seconds until the LED lights up.
3. Enter the five-digit manufacturer code.
4. Press `[OK]` to save.

After successful setup, `[VOL+]`, `[VOL-]` and `[MUTE]` control the TV.

### Search for a manufacturer code automatically

1. Switch on the TV and hold `[TV POWER] + [OK]` until the LED lights up.
2. Press `[CH+]` or `[CH-]` repeatedly. Each press sends a power-off code to the TV.
3. When the TV switches off, press `[OK]` to save the code.

### Assign volume to the receiver again

1. Hold `[TV POWER] + [OK]` until the LED lights up.
2. Press `[TV POWER]` to assign volume and mute to the TV, or `[STB POWER]` to
   assign them to the receiver again.

## TV manufacturer codes

Depending on the model range, the database may contain several suitable codes
for one brand. The following selection covers common manufacturers. Test codes
in the order shown: enter setup with `[TV POWER] + [OK]`, enter a code and press
`[OK]` to save.

| Manufacturer | Five-digit TV codes |
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

The [complete TV code list in the VU+ manual](https://www.tvdigitalne.cz/user/related_files/vu_plus_bt_ir_english.pdf)
contains many additional brands. If none of a brand's codes work, use automatic
code search rather than trying codes for other manufacturers.

## Home Assistant integration notes

- A factory reset removes pairing from the remote. If the Home Assistant host
  still has an obsolete BlueZ entry, remove it there before pairing again.
- After pairing, the local evdev device `VUPLUS-BLE-RCU Keyboard` must appear.
  The changing number in `/dev/input/eventX` does not matter.
- `TV POWER` and `AV` do not produce events on the Linux evdev interface used
  here. They are not available as Home Assistant triggers.

## Sources

- [VU+ WIKI: remote control – Type V programming](https://wiki.vuplus-support.org/index.php?title=Fernbedienung#Programmierung_(Typ_V)) (German): pairing, factory reset, TV settings and system codes.
- [VU+ Bluetooth Remote Manual (Ultimo 4K BLE RCU)](https://www.tvdigitalne.cz/user/related_files/vu_plus_bt_ir_english.pdf): hold times, LED responses and the scope of a factory reset.
- [TV code list in the VU+ Bluetooth Remote Manual](https://www.tvdigitalne.cz/user/related_files/vu_plus_bt_ir_english.pdf): the full manufacturer and code database.

See the [README](README.en.md) for setup and usage in Home Assistant.
