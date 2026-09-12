[Deutsch](CHANGELOG.md) | [English](CHANGELOG.en.md)

# Changelog

## Contents

- [1.2.0](#120)
- [1.1.1](#111)
- [1.1.0](#110)
- [1.0.3](#103)
- [1.0.2](#102)
- [1.0.1](#101)
- [1.0.0](#100)

## 1.2.0

- Bluetooth pairing discovery hides remotes already paired, bonded, connected
  or configured in the integration by address, including across adapters.
  Updated dialogs and documentation; tested filtering and empty results with
  simulated devices. Successful filtering confirmed by the user in a hardware
  test on 2026-09-12.

- Set up multiple VU+ remotes with identical names separately using the Bluetooth
  address in evdev `uniq`. Selection, device names and reconnection use the fixed
  address; changing event paths are still never stored.
- Legacy entries can be assigned through **Reconfigure** while retaining device,
  entity and automation associations. Existing Bluetooth identities are reused.
  Ambiguous selection never reads an arbitrary device.
- Pairing, diagnostics and confirmed unpairing respect the selected remote.
  Added tests for two identical devices, separate button events, path changes,
  missing devices and legacy assignment. Verified locally with simulated devices;
  a host listing from 2026-09-12 confirms distinct `uniq` addresses for two devices.
  Actual parallel operation and reconnects remain untested.

## 1.1.1

- Added stable blueprint source URLs, visible versions and language-specific import links. Documented optional update notices with Blueprints Updater and migration of existing local files.

- Fixed blueprint template failure caused by the unavailable `has_service`
  function. Removed the incorrect test helper so template tests reproduce
  this error. Home Assistant reports unregistered actions when invoked.

## 1.1.0

- Added German and English blueprints to map short key presses in one
  automation. HAVUOpenWebif receivers are mapped automatically using Enigma2
  keycodes; target prefixes and explicit mappings are also supported.
  Ambiguous matches require an explicit target.
- Conditions can redirect individual keys or switch the entire target profile.
  Alternative targets support buttons, media players, switches, scripts,
  scenes, lights, fans, covers and helpers.
- Added entity type filtering and text search with a shared action list in
  the same dialog. Action data and disabling individual keys are configurable.
  Users check support on their particular device.
- Missing, unavailable and action-domain-mismatched targets are skipped.
  Added setup documentation and automated blueprint tests.
- Reference: HAVUOpenWebif 1.1.0, commit
  `f20b23d74b6b63f343dd42d2177dec22df068d76`. Verified through source review
  and local simulation; no confirmed receiver test. Other or newer
  HAVUOpenWebif versions may break the mapping.
- Documented development versioning, version checks before pull requests,
  authorized merges into main and explicitly requested releases in both
  languages.

## 1.0.3

- Added distinct default names for the Volume up/down and Channel up/down event
  entities so Home Assistant does not need to add numeric suffixes such as `_2`.

## 1.0.2

- Moved the language selector to the beginning of every bilingual document.
- Tested installation through HACS, adding the integration, Bluetooth pairing and
  explicitly confirmed unpairing with the remote.

## 1.0.1

- Added a compact logo variant and use it in the README and documentation.

## 1.0.0

Initial release of the **VU+ HID Raw Remote** Home Assistant integration.

- Connects the VU+ Bluetooth remote `VUPLUS-BLE-RCU` through local Linux evdev
  devices, for Home Assistant 2026.9.0 or newer.
- UI setup with optional Bluetooth discovery, pairing, trusting and connection
  through BlueZ.
- Device discovery by Linux device name and automatic reconnection when
  `/dev/input/eventX` paths change.
- A separate event entity for every supported button as the automation interface,
  including special buttons identified through `MSC_SCAN`.
- Short and long presses, releases and repeats, with a configurable long-press
  threshold and event types `press_start`, `press_end`, `long_press_start`,
  `long_press_end` and `repeat`.
- Device information with icon and logo, plus five diagnostic binary sensors
  for pairing, Bluetooth connection, trust, input device and reader status.
- Optional unpairing through an explicitly confirmed repair dialog after
  deletion of the integration entry.
- German and English UI, including device and entity names, repair choices,
  and complete documentation in both languages.
- HACS repository structure, installation and remote guides, and automated
  Python, Home Assistant and HACS checks.
- GitHub project logo and configuration for additional development tools.
- Concise README for GitHub and HACS; detailed setup and reference information
  moved to separate documentation.

`TV Power` and `AV` do not generate events through the evdev interface used here
and are not available as automation triggers.
