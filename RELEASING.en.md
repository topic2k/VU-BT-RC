[Deutsch](RELEASING.md) | [English](RELEASING.en.md)

# Publishing

## Contents

- [Repository](#repository)
- [Checks](#checks)
- [Publish a release](#publish-a-release)
- [HACS](#hacs)

## Repository

The public repository [topic2k/VU-BT-RC](https://github.com/topic2k/VU-BT-RC)
uses `main` as its default branch. Installation is documented in the
[README](README.en.md); release contents are in the [changelog](CHANGELOG.en.md).

Repository settings for HACS:

- Public repository with issues enabled.
- Description: “Home Assistant integration for the VU+ Bluetooth remote via
  local Linux evdev.”
- Topics: `home-assistant`, `hacs`, `custom-integration`, `bluetooth`, `vuplus`,
  `evdev`.

The project uses the [MIT License](LICENSE).

The integration manifest's `documentation`, `issue_tracker` and `codeowners`
refer to this repository and `@topic2k`.

## Checks

Run from the project directory with Python 3.14:

```sh
python -m pip install --group test
python -m unittest discover -s tests -v
python -m compileall -q custom_components tests
git diff --check
```

Before a release, `version` in `custom_components/vuplus_hid_raw/manifest.json`,
`INTEGRATION_VERSION` in `custom_components/vuplus_hid_raw/__init__.py`, the newest
changelog entry and the Git tag must agree. Tags use the `v` prefix, for example
`v1.0.2` for version `1.0.2`.

The `.github/workflows/validate.yml` workflow runs tests, Python syntax checks,
Home Assistant metadata validation with Hassfest and HACS validation on GitHub.
Tests also check matching translation keys and placeholders, translatable entity
and option names, and documentation links. Update all documentation in German
and English together.

Full HACS validation requires the public GitHub repository with a description,
topics and enabled issues.

For the first release, installation through HACS, adding the integration,
Bluetooth pairing and explicitly confirmed unpairing have been tested with the
remote. For later feature changes, also test buttons, short and long presses,
reconnection, diagnostics and both languages on Home Assistant OS / Raspberry Pi /
aarch64. Tests with simulated Home Assistant and BlueZ do not replace hardware
testing.

## Publish a release

1. Commit the checked project state locally if changes are still pending.
2. Push `main` to the configured remote `origin`:

   ```sh
   git push -u origin main
   ```

3. Wait for the GitHub Actions checks to pass for the commit being released.
   Complete the hardware tests under [Checks](#checks) and update the pending-test
   notes in both README versions based on the actual results.
4. Tag the checked commit and push the tag:

   ```sh
   git tag -a vX.Y.Z -m "Release X.Y.Z"
   git push origin vX.Y.Z
   ```

5. Create a GitHub release for tag `vX.Y.Z`, titled `X.Y.Z`. Use the `X.Y.Z`
   sections from `CHANGELOG.md` and `CHANGELOG.en.md` as a bilingual description
   and publish it as a regular release.

No additional ZIP release asset is required. HACS uses the integration directory
from the repository at the selected release tag.

A release can be prepared as a **draft** using the intended tag `vX.Y.Z` and
the checked commit as its target. Publish the draft only after completing the
checks. If further changes are made, update its target commit and bilingual
release description. A draft is not offered to HACS users as a published version.

## HACS

`hacs.json` sets **2026.9.0** as the minimum Home Assistant version. All integration
files are in `custom_components/vuplus_hid_raw`, with local brand images in its
`brand` subdirectory.

After publication, the repository can be added to HACS as a custom repository
of type **Integration**. Inclusion in the HACS default catalog is a separate
step and is not required for this installation method. HACS needs a published
GitHub release to display a release version; a Git tag alone is not sufficient.

References: [HACS requirements](https://www.hacs.xyz/docs/publish/start/),
[integration structure](https://www.hacs.xyz/docs/publish/integration/),
[HACS validation](https://www.hacs.xyz/docs/publish/action/).
