[Deutsch](CHANGELOG.md) | [English](CHANGELOG.en.md)

# Changelog

## Contents

- [1.0.3](#103)
- [1.0.2](#102)
- [1.0.1](#101)
- [1.0.0](#100)

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
