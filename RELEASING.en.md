[Deutsch](RELEASING.md) | [English](RELEASING.en.md)

# Publishing

## Contents

- [Repository](#repository)
- [Development versions](#development-versions)
- [Version before the pull request](#version-before-the-pull-request)
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

## Development versions

Make changes on `develop` or a working branch. Automatically increase the version
based on all changes since the last stable version: patch for fixes, internal
changes and documentation, minor for backward-compatible new features, major
for incompatible changes. Development builds use the `-dev.N` suffix, for example
`1.1.0-dev.1`. Further completed changes to the same target version increment
the counter; restart at 1 when the target version increases.

The manifest, `INTEGRATION_VERSION` and both changelogs use the same full version.
Label it as unpublished in the changelogs. This format uses SemVer with a
prerelease identifier, supported by the
[Home Assistant manifest rules](https://developers.home-assistant.io/docs/creating_integration_manifest/#version).

Merge changes into `main` only through a pull request after user approval.
Remove the development suffix immediately before the pull request.
Merge approval does not authorize a release.

## Version before the pull request

1. Immediately before a pull request into `main`, refresh remote branches and
   tags and check published releases on GitHub. Local versions or tags alone
   are not sufficient for this comparison.
2. Determine the next appropriate patch, minor or major version from the latest
   stable release and the entire proposed scope of changes. Account for version
   increases from other branches or commits since work began. The target version
   must not have been published or assigned on `main` already, and must not
   cause a version decrease.
3. On the source branch, set the chosen version without `-dev.N` in the manifest,
   `INTEGRATION_VERSION` and both changelogs. Update the tables of contents and
   label the entry as unpublished; remove only its development-version label.
   Preserve published history.
4. Rerun the [checks](#checks) and include the version adjustment in the pull
   request. Preparation is incomplete without a current remote comparison.
5. If `main` or the release baseline changes while the pull request is open,
   repeat the comparison before merging and make any necessary changes on the
   source branch. Merge only after user approval.

This process creates neither a tag nor a release. A version without a development
suffix remains unpublished until an explicit release instruction is given.

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

An explicit release instruction from the user is required. This also applies
to release drafts and release tags.

1. Check the version to be released and its commit on `main`. For any pending
   changes, follow [Version before the pull request](#version-before-the-pull-request).
2. As part of the requested publication, remove the unpublished label from both
   changelogs. Prepare this change on a working branch too and merge it through
   a pull request after user approval, repeating the version comparison.

3. Wait for the GitHub Actions checks to pass for the commit being released.
   Complete the hardware tests under [Checks](#checks) and update the pending-test
   notes in both README versions based on the actual results.
4. Tag the checked commit on `main` and push the tag:

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
