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
reconnections. Find the device by name and, when available, its Bluetooth address
from evdev `uniq`. Remotes with identical names must be distinguished by this
address; ambiguous matches must never select an arbitrary device. Never persist
the event number.

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

For the blueprint's HAVUOpenWebif connection, document the verified version,
exact commit and actual verification scope in both languages. Do not describe
source review and simulated tests as receiver testing. Mention possible
incompatibility with other/newer versions; when changing the verification baseline,
update blueprint descriptions and the test reference together as well.

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

## Branches, approval and releases

- Implement changes on `develop` first, or on a new working branch when needed;
  do not make changes or commits directly on `main`.
- Merge changes into `main` exclusively through a pull request and only after
  explicit approval from the user.
- Create a new release only when explicitly instructed by the user.
  Approval of changes or a pull request does not authorize a release.
- The versioning rules below do not authorize automatic publication.

## Versioning

- When making changes on `develop` or a working branch, automatically increase
  the version without a separate request, based on the entire unpublished scope
  since the last stable version: patch for fixes, internal changes and
  documentation-only changes, minor for backward-compatible new features,
  major for incompatible changes.
- Development builds use `X.Y.Z-dev.N`, starting with `dev.1`, for example
  `1.1.0-dev.1`. Increment the counter for further completed changes to the same
  target version; restart at `dev.1` when the target version increases.
  Do not assign a new version for every individual file edit.
- `version` in `manifest.json`, `INTEGRATION_VERSION` and the newest entry in
  both changelogs must match, including the development suffix. Explicitly label
  the changelog entry as an unpublished development version and update it for
  further changes to the same target version.
- Immediately before each pull request into `main`, fetch the current remote
  state of `main`, tags and published releases. Recalculate the next appropriate
  version from the latest stable release and the entire proposed scope of changes.
  Account for intervening version increases from other branches or commits;
  do not reuse a published version or one already assigned on `main`, and do not
  decrease the version.
- On the working branch, remove the entire `-dev.N` suffix and synchronize the
  manifest, `INTEGRATION_VERSION`, both changelogs and their tables of contents.
  Keep the entry labelled unpublished until publication, but no longer label it
  as a development version. Then rerun the checks. This preparation is incomplete
  without an up-to-date comparison against the remote state.
- If `main` or the release baseline changes while a pull request is open, repeat
  the version comparison before merging and make any adjustments on the source
  branch. Merge only after user approval. A version without a development suffix
  or a merge does not authorize automatic tags or releases; an explicit release
  instruction is still required.

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
