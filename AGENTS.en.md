[Deutsch](AGENTS.md) | [English](AGENTS.en.md)

# Project instructions

## Project

This is a Home Assistant custom integration for the VU+ Bluetooth remote
`VUPLUS-BLE-RCU`, using Linux evdev.

## Target platform

- Home Assistant 2026.9.x
- Home Assistant OS
- Python 3.14
- Raspberry Pi / aarch64
- Local Linux evdev input devices

## Automation interface

Event entities are the only automation interface. There is no
`vuplus_remote_command` bus event and no integration-specific device triggers.

## Input device

The relevant evdev device is normally named `VUPLUS-BLE-RCU Keyboard`.
Never assume a fixed `/dev/input/eventX`: its number can change after Bluetooth
reconnections. Find the device by name and never persist its event number.

## Async rules

Do not block the Home Assistant event loop with I/O. In particular,
`evdev.list_devices()`, opening `InputDevice` and comparable blocking operations
must follow Home Assistant async conventions.

## Remote

The integration distinguishes `press`, `repeat`, `long_press`, `short_release`
and `long_release`. The long-press threshold is configurable.

## Home Assistant integration

Integrate as fully as possible with Home Assistant:

- Config flow
- Device registry
- Event entities as the only automation interface
- Selectable event types and attribute filters in the automation UI

## Known limitations

TV Power and AV do not generate events through the Linux evdev interface in use.
Do not implement or document these buttons as working.

## Language

- Always maintain the entire integration and documentation in German and English.
- `strings.json` contains English source strings. `translations/en.json` and
  `translations/de.json` must have identical keys and placeholders.
- UI text, device names, entity names and fixed selection options use Home
  Assistant translation mechanisms. Technical identifiers remain language-neutral;
  do not hardcode German UI text in Python.
- German documents use `*.md`; their English counterparts use `*.en.md`. Each
  pair links to the other language and is updated together, including changelogs,
  release guides and project instructions.
- `LICENSE` contains the authoritative English MIT text. `LICENSE.de.md` contains
  a clearly identified German translation.
- A feature is complete only when both languages and their checks are updated.

## Documentation

`README.md` contains the current, concise user documentation for GitHub and HACS.
Detailed setup and reference information belongs in `DOKUMENTATION.md`.
`CHANGELOG.md` contains only version history. Do not duplicate the changelog in
the README. The same rules apply to their English counterparts.

The changelog:

- Starts with a table of contents.
- Lists the newest version first.
- Gets a new entry for every relevant change.

The README:

- Starts with a table of contents.
- Contains current user-facing information: purpose, features, installation,
  setup, use, limitations and links to further documentation.
- Stays easy to scan and links to `DOKUMENTATION.md` for technical background.
- Removes completed items from future-development lists.
- Does not contain a historical version list.

## Versioning

Until the first publication, additions remain part of version 1.0.0; update the
initial release entry in both changelogs. After the first publication:

User-visible changes require a manifest version increase and changelog update.
Do not create artificial releases for tiny internal changes. Documentation-only
changes increase only the integration's patch version.

## Development rules

Before changes:

1. Analyze the existing code.
2. Understand the existing functionality.
3. Write a short implementation plan.

After changes:

1. Run tests.
2. Check Python syntax.
3. Check Home Assistant compatibility as far as locally possible.
4. Update affected documentation and changelogs in both languages.
5. Do not create ZIP files unless explicitly requested.
