"""Keep both supported languages complete and automation values stable."""
from __future__ import annotations

import json
from pathlib import Path
import re
from string import Formatter
import types
import unittest

from test_event_entity_source import binary_sensor_platform, event_platform, integration

ROOT = Path(__file__).resolve().parents[1]
COMPONENT = ROOT / "custom_components/vuplus_hid_raw"


def catalog(language):
    return json.loads((COMPONENT / "translations" / f"{language}.json").read_text(encoding="utf-8"))


def leaves(value, prefix=()):
    result = {}
    for key, child in value.items():
        path = (*prefix, key)
        if isinstance(child, dict):
            result.update(leaves(child, path))
        else:
            result[path] = child
    return result


class LocalizationTest(unittest.TestCase):
    def test_catalogs_have_identical_keys_placeholders_and_english_source(self):
        english = catalog("en")
        self.assertEqual(english, json.loads((COMPONENT / "strings.json").read_text(encoding="utf-8")))
        english_leaves = leaves(english)
        german_leaves = leaves(catalog("de"))
        self.assertEqual(set(english_leaves), set(german_leaves))
        for key, english_text in english_leaves.items():
            with self.subTest(key=key):
                german_text = german_leaves[key]
                self.assertIsInstance(english_text, str)
                self.assertIsInstance(german_text, str)
                self.assertTrue(english_text.strip())
                self.assertTrue(german_text.strip())
                self.assertNotIn("[%key:", english_text)
                self.assertNotIn("[%key:", german_text)
                placeholders = lambda text: {field for _, field, _, _ in Formatter().parse(text) if field is not None}
                self.assertEqual(placeholders(english_text), placeholders(german_text))

    def test_repair_translations_use_exclusive_description_or_fix_flow(self):
        for language in ("de", "en"):
            for key, issue in catalog(language)["issues"].items():
                with self.subTest(language=language, issue=key):
                    self.assertEqual(sum(field in issue for field in ("description", "fix_flow")), 1)
                    self.assertTrue(issue["title"])

    def test_every_button_diagnostic_and_device_uses_available_translations(self):
        state = {"entry": types.SimpleNamespace(entry_id="entry", unique_id="remote")}
        for language in ("de", "en"):
            translated = catalog(language)
            self.assertEqual(set(integration.COMMAND_LABELS), set(translated["entity"]["event"]))
            self.assertEqual(set(binary_sensor_platform.DIAGNOSTICS), set(translated["entity"]["binary_sensor"]))
            for command in integration.COMMAND_LABELS:
                entity = event_platform.VuplusRemoteButtonEvent(state, command)
                self.assertNotIn("_attr_name", vars(entity))
                self.assertTrue(translated["entity"]["event"][entity._attr_translation_key]["name"])
                self.assertTrue(translated["device"][entity._attr_device_info["translation_key"]]["name"])
                self.assertEqual(set(entity._attr_event_types), set(translated["entity"]["event"][command]["state_attributes"]["event_type"]["state"]))
            for key in binary_sensor_platform.DIAGNOSTICS:
                entity = binary_sensor_platform.VuplusRemoteDiagnostic(state, key)
                self.assertNotIn("_attr_name", vars(entity))
                self.assertTrue(translated["entity"]["binary_sensor"][entity._attr_translation_key]["name"])
                self.assertTrue(translated["device"][entity._attr_device_info["translation_key"]]["name"])

    def test_translated_button_labels_preserve_identifiers_and_shared_event_data(self):
        state = {"entry": types.SimpleNamespace(entry_id="entry", unique_id="remote")}
        data = {"command": "volume_up", "command_label": "Volume +", "action": "short_release", "value": 0, "duration_ms": 200}
        original = data.copy()
        for language in ("de", "en"):
            entity = event_platform.VuplusRemoteButtonEvent(state, "volume_up")
            entity._test_name = catalog(language)["entity"]["event"]["volume_up"]["name"]
            entity._handle(data)
            event_type, published = entity.triggered
            self.assertEqual(event_type, "press_end")
            self.assertEqual(published["command_label"], entity._test_name)
            self.assertEqual(published, {**original, "command_label": entity._test_name})
            self.assertEqual(data, original)
            self.assertEqual(entity._attr_unique_id, "entry_volume_up_button_events")
        entity = event_platform.VuplusRemoteButtonEvent(state, "volume_up")
        entity._handle(data)
        self.assertEqual(entity.triggered[1]["command_label"], "Volume +")

    def test_volume_and_channel_entity_names_generate_distinct_object_ids(self):
        expected_names = {
            "de": {
                "volume_up": "Lautstärke Plus",
                "volume_down": "Lautstärke Minus",
                "channel_up": "Kanal Plus",
                "channel_down": "Kanal Minus",
            },
            "en": {
                "volume_up": "Volume up",
                "volume_down": "Volume down",
                "channel_up": "Channel up",
                "channel_down": "Channel down",
            },
        }
        for language, names in expected_names.items():
            with self.subTest(language=language):
                translated = catalog(language)["entity"]["event"]
                self.assertEqual(names, {key: translated[key]["name"] for key in names})

    def test_documentation_pairs_links_and_release_versions(self):
        german = {p.name for p in ROOT.glob("*.md") if not p.name.endswith((".en.md", ".de.md"))}
        for name in german:
            english = name[:-3] + ".en.md"
            self.assertTrue((ROOT / english).exists(), english)
            self.assertIn(f"]({english})", (ROOT / name).read_text(encoding="utf-8"))
            self.assertIn(f"]({name})", (ROOT / english).read_text(encoding="utf-8"))
        for path in ROOT.glob("*.md"):
            content = path.read_text(encoding="utf-8")
            headings = re.findall(r"^#{1,6} (.+)$", content, re.M)
            anchors = {re.sub(r"[^\w\- ]", "", h.lower()).replace(" ", "-") for h in headings}
            for target in re.findall(r"\]\(([^\s)]+)\)", content):
                if target.startswith(("https://", "http://")):
                    continue
                with self.subTest(document=path.name, target=target):
                    if target.startswith("#"):
                        self.assertIn(target[1:], anchors)
                    else:
                        self.assertTrue((ROOT / target.split("#")[0]).exists())
        versions = lambda name: re.findall(r"^## (\d+\.\d+\.\d+)", (ROOT / name).read_text(encoding="utf-8"), re.M)
        self.assertEqual(versions("CHANGELOG.md"), versions("CHANGELOG.en.md"))
        manifest = json.loads((COMPONENT / "manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(versions("CHANGELOG.md")[0], manifest["version"])
        self.assertEqual(manifest["version"], integration.INTEGRATION_VERSION)

    def test_remote_guides_keep_identical_manufacturer_codes(self):
        tables = []
        for name in ("VU_BT_FERNBEDIENUNG_TASTENKOMBINATIONEN.md", "VU_BT_FERNBEDIENUNG_TASTENKOMBINATIONEN.en.md"):
            content = (ROOT / name).read_text(encoding="utf-8")
            tables.append([line for line in content.splitlines() if line.startswith("| ") and re.search(r"`\d{5}`", line)])
        self.assertTrue(tables[0])
        self.assertEqual(tables[0], tables[1])
