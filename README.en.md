[Deutsch](README.md) | [English](README.en.md)

# VU+ HID Raw Remote

## Contents

- [What is it?](#what-is-it)
- [What it can do](#what-it-can-do)
- [Requirements](#requirements)
- [Installation](#installation)
- [Setup and use](#setup-and-use)
- [Automations](#automations)
- [Important notes](#important-notes)
- [Learn more](#learn-more)
- [License](#license)

![VU+ HID Raw Remote](logo.docs.png)

## What is it?

**VU+ HID Raw Remote** connects the VU+ BT/IR remote (Type V), Bluetooth name
`VUPLUS-BLE-RCU`, directly to Home Assistant. Every supported button becomes its
own event entity and can trigger automations.

For example, pressing **OK**, **Menu**, a colour button or a playback button can
directly control scenes, lights or scripts.

## What it can do

- Set up the remote in the Home Assistant UI and pair it through Bluetooth when
  needed.
- Distinguish short presses, long presses and button repeats.
- Provide a clearly selectable automation trigger for every supported button.
- Reconnect automatically after Bluetooth disconnections.
- Show pairing, connection and input-device status on the device page.
- Remove the Bluetooth pairing after deleting the integration only when explicitly
  confirmed.

The UI and documentation are available in German and English.

## Requirements

- Home Assistant **2026.9.0** or newer, preferably Home Assistant OS on a
  Raspberry Pi / aarch64.
- A VU+ BT/IR Type V remote and a local Bluetooth adapter.
- The remote must appear on the Home Assistant host as
  `VUPLUS-BLE-RCU Keyboard`.

Home Assistant Container needs additional access to `/dev/input` and the system
D-Bus. Details are in the [detailed documentation](DOKUMENTATION.en.md#requirements-and-permissions).

## Installation

### Through HACS

1. In HACS, open **Custom repositories** from the top-right menu.
2. Enter `https://github.com/topic2k/VU-BT-RC` and choose **Integration**.
3. Download **VU+ HID Raw Remote** and restart Home Assistant.
4. Go to **Settings → Devices & services → Add integration** and search for
   **VU+ HID Raw Remote**.

### Manually

Copy `custom_components/vuplus_hid_raw` to
`/config/custom_components/vuplus_hid_raw` and restart Home Assistant. No
`configuration.yaml` entry is needed.

## Setup and use

When adding the integration, choose one of two paths:

- **Select an already connected input device** if the remote is already paired
  with the host.
- **Pair a Bluetooth remote** to discover, pair and connect it directly in Home
  Assistant. Discovery hides remotes already paired, connected or configured
  in the integration.

Wake the remote during setup. Then choose a long-press threshold; the default is
500 ms. The device page subsequently lists button event entities and five
diagnostic indicators.

For multiple VU+ remotes, create one integration entry per remote and select its
**Bluetooth address** in the dropdown. Device names include the address; you can
rename them to “Living room” or “Bedroom”. First use **Reconfigure** to assign an
existing entry without a fixed identity to its remote. Existing automations are
retained. See [multiple remotes](DOKUMENTATION.en.md#multiple-remotes) for details.

## Automations

[Import English blueprint into Home Assistant](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2Ftopic2k%2FVU-BT-RC%2Fblob%2Fmain%2Fblueprints%2Fautomation%2Fvuplus_hid_raw%2Fshort_press_buttons.en.yaml)

For optional update notices, configure [Blueprints Updater](https://github.com/luuquangvu/blueprints-updater).
See [blueprint updates](DOKUMENTATION.en.md#blueprint-updates). Updating the integration through HACS does not update imported blueprints.

To forward presses to a satellite receiver's `button.*` entities, use the
[blueprint for the entire remote](DOKUMENTATION.en.md#blueprint-short-presses-to-receiver-buttons).
It maps short presses using a shared naming rule, supports exceptions, and can
redirect individual keys or all targets depending on conditions.
For **HAVUOpenWebif**, selecting the receiver enables detection by keycode;
ambiguous keys such as TV and teletext use explicit targets.
Verified baseline: **HAVUOpenWebif 1.1.0**, commit `f20b23d74b6b` (source review
and local blueprint tests; not yet tested on a receiver). Mapping may stop working
with other or newer versions. See the
[documentation](DOKUMENTATION.en.md#automatic-detection-for-havuopenwebif) for the verification scope.
Alternative targets can be configured with key, entity and action selectors,
including media players, switches, scripts, scenes, lights and other controllable
entities. Individual keys can also be disabled.
Target selection can be narrowed by entity type and searched by text in the
entity field. Entity and unfiltered action list share the same dialog.
Users choose an action matching the target and check support on their device.

In a new automation, choose the **Event received** trigger, select the desired
button entity and choose an event type:

| Event type | Meaning |
| --- | --- |
| `press_start` | Button pressed |
| `press_end` | Released after a short press |
| `long_press_start` | Long press detected |
| `long_press_end` | Released after a long press |
| `repeat` | Held button is repeating |

No additional button-name filter is needed because the button is already selected
through its own entity. See the [automation reference](DOKUMENTATION.en.md#automations)
for a complete example and event data.

## Important notes

- **TV Power** and **AV** do not produce Linux evdev events, so they cannot
  trigger Home Assistant automations.
- Bluetooth proxies are insufficient because the remote must be available as a
  local Linux input device.
- Multiple remotes with identical names require distinct Bluetooth addresses in
  their Linux input devices (`uniq`). Ambiguous matches do not select a device.

## Learn more

- [Detailed documentation](DOKUMENTATION.en.md): setup details, Bluetooth,
  unpairing, event attributes and diagnostics.
- [VU+ BT/IR remote button combinations](VU_BT_FERNBEDIENUNG_TASTENKOMBINATIONEN.en.md):
  pairing mode, factory reset, system codes and TV functions.
- [Report problems or ask a question](https://github.com/topic2k/VU-BT-RC/issues).

## License

The project uses the [MIT License](LICENSE). A
[German translation](LICENSE.de.md) is provided for reference.
