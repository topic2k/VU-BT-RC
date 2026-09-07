"""Regression tests for the event-entity source data."""
from __future__ import annotations

import asyncio
import importlib
import json
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import patch


def _install_home_assistant_stubs() -> None:
    homeassistant = types.ModuleType("homeassistant")
    components = types.ModuleType("homeassistant.components")
    event_component = types.ModuleType("homeassistant.components.event")
    binary_sensor_component = types.ModuleType("homeassistant.components.binary_sensor")

    class EventEntity:
        @property
        def name(self):
            # Home Assistant resolves entity translations; tests can supply that result.
            return getattr(self, "_test_name", None)

        def _trigger_event(self, event_type, data) -> None:
            self.triggered = (event_type, data)

        def async_write_ha_state(self) -> None:
            self.written = True

    event_component.ButtonEventType = types.SimpleNamespace(
        PRESS_START="press_start",
        PRESS_END="press_end",
        LONG_PRESS_START="long_press_start",
        LONG_PRESS_END="long_press_end",
    )
    event_component.EventDeviceClass = types.SimpleNamespace(BUTTON="button")
    event_component.EventEntity = EventEntity
    class BinarySensorEntity:
        def async_write_ha_state(self) -> None:
            self.written = True

    binary_sensor_component.BinarySensorDeviceClass = types.SimpleNamespace(
        CONNECTIVITY="connectivity"
    )
    binary_sensor_component.BinarySensorEntity = BinarySensorEntity
    config_entries = types.ModuleType("homeassistant.config_entries")
    config_entries.ConfigEntry = object
    const = types.ModuleType("homeassistant.const")
    const.Platform = types.SimpleNamespace(EVENT="event", BINARY_SENSOR="binary_sensor")
    const.EntityCategory = types.SimpleNamespace(DIAGNOSTIC="diagnostic")
    core = types.ModuleType("homeassistant.core")
    core.HomeAssistant = object
    core.callback = lambda function: function
    helpers = types.ModuleType("homeassistant.helpers")
    entity = types.ModuleType("homeassistant.helpers.entity")
    entity.DeviceInfo = lambda **kwargs: kwargs
    entity_registry = types.ModuleType("homeassistant.helpers.entity_registry")
    entity_registry.async_get = lambda hass: None
    helpers.entity_registry = entity_registry
    sys.modules.update(
        {
            "homeassistant": homeassistant,
            "homeassistant.components": components,
            "homeassistant.components.event": event_component,
            "homeassistant.components.binary_sensor": binary_sensor_component,
            "homeassistant.config_entries": config_entries,
            "homeassistant.const": const,
            "homeassistant.core": core,
            "homeassistant.helpers": helpers,
            "homeassistant.helpers.entity": entity,
            "homeassistant.helpers.entity_registry": entity_registry,
        }
    )


_install_home_assistant_stubs()
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
integration = importlib.import_module("custom_components.vuplus_hid_raw")
event_platform = importlib.import_module("custom_components.vuplus_hid_raw.event")
binary_sensor_platform = importlib.import_module("custom_components.vuplus_hid_raw.binary_sensor")


class EventEntitySourceTest(unittest.TestCase):
    """Validate the data supplied exclusively to the event entity."""

    def test_keycode_and_unknown_usage_mapping(self) -> None:
        self.assertEqual("ok", integration._command_for_key(28, None))
        self.assertEqual("epg", integration._command_for_key(240, 0x16B))
        self.assertIsNone(integration._command_for_key(240, None))

    def test_device_lookup_uses_name_not_event_path(self) -> None:
        closed: list[str] = []

        class InputDevice:
            def __init__(self, path) -> None:
                self.path = path
                self.name = "VUPLUS-BLE-RCU Keyboard"

            def close(self) -> None:
                closed.append(self.path)

        self.assertEqual(
            "/dev/input/event7",
            integration._find_device(
                "VUPLUS-BLE-RCU Keyboard",
                lambda: ["/dev/input/event7", "/dev/input/event9"],
                InputDevice,
            ),
        )
        self.assertEqual(["/dev/input/event7"], closed)

    def test_published_action_data_matches_evdev_values(self) -> None:
        expected_values = {
            "press": 1,
            "long_press": 1,
            "repeat": 2,
            "short_release": 0,
            "long_release": 0,
        }
        for action, value in expected_values.items():
            with self.subTest(action=action):
                received: list[dict] = []
                integration._publish_event(
                    {"callbacks": [received.append]},
                    command="ok",
                    action=action,
                    key_code=28,
                    scan_code=None,
                    usage=None,
                    duration_ms=10,
                )
                self.assertEqual(value, received[0]["value"])
                self.assertNotIn("device_id", received[0])

    def test_diagnostic_entities_report_live_values(self) -> None:
        state = {
            "entry": types.SimpleNamespace(entry_id="entry-123", unique_id=None),
            "diagnostics": {
                "paired": True, "connected": False, "trusted": True,
                "input_device": True, "reader_active": False,
            },
            "diagnostic_callbacks": [],
        }
        entity = binary_sensor_platform.VuplusRemoteDiagnostic(state, "connected")
        self.assertEqual("entry-123_connected_diagnostic", entity._attr_unique_id)
        self.assertFalse(entity.is_on)
        self.assertTrue(entity.available)

        unknown = binary_sensor_platform.VuplusRemoteDiagnostic(state, "paired")
        state["diagnostics"]["paired"] = None
        self.assertFalse(unknown.available)

    def test_each_supported_command_has_its_own_event_entity(self) -> None:
        commands = set(integration.KEY_COMMANDS.values()) | set(
            integration.USAGE_COMMANDS.values()
        )
        self.assertEqual(commands, set(integration.COMMAND_LABELS))

        state = {
            "entry": types.SimpleNamespace(entry_id="entry-123", unique_id=None)
        }
        entity = event_platform.VuplusRemoteButtonEvent(state, "ok")

        self.assertEqual("entry-123_ok_button_events", entity._attr_unique_id)
        self.assertEqual("ok", entity._attr_translation_key)
        self.assertEqual(
            {
                "identifiers": {(integration.DOMAIN, "entry-123")},
                "translation_key": "remote",
                "manufacturer": "VU+",
                "model": "VUPLUS-BLE-RCU",
                "model_id": "VUPLUS-BLE-RCU",
                "sw_version": "Integration " + json.loads(
                    (Path(__file__).resolve().parents[1]
                     / "custom_components/vuplus_hid_raw/manifest.json").read_text(encoding="utf-8")
                )["version"],
            },
            entity._attr_device_info,
        )

        entity._handle({"command": "menu", "action": "short_release"})
        self.assertFalse(hasattr(entity, "triggered"))

        data = {"command": "ok", "command_label": "OK", "action": "short_release"}
        entity._handle(data)
        self.assertEqual(("press_end", data), entity.triggered)
        self.assertTrue(entity.written)

    def test_brand_images_are_packaged_for_the_home_assistant_ui(self) -> None:
        """Ensure local UI branding is shipped alongside the integration."""
        brand_dir = (
            Path(__file__).resolve().parents[1]
            / "custom_components"
            / "vuplus_hid_raw"
            / "brand"
        )
        for filename in ("icon.png", "logo.png"):
            with self.subTest(filename=filename):
                self.assertEqual(
                    b"\x89PNG\r\n\x1a\n", (brand_dir / filename).read_bytes()[:8]
                )


class EventPlatformSetupTest(unittest.IsolatedAsyncioTestCase):
    """Validate creation and migration of the per-button entities."""

    async def test_setup_creates_all_buttons_and_removes_aggregate_entity(self) -> None:
        removed: list[str] = []

        class Registry:
            def async_get_entity_id(self, domain, platform, unique_id):
                self.lookup = (domain, platform, unique_id)
                return "event.old_button_events"

            def async_remove(self, entity_id) -> None:
                removed.append(entity_id)

        registry = Registry()
        entry = types.SimpleNamespace(entry_id="entry-123", unique_id="remote-1")
        state = {"entry": entry}
        hass = types.SimpleNamespace(
            data={integration.DOMAIN: {entry.entry_id: state}}
        )
        added: list = []

        with patch.object(event_platform.er, "async_get", return_value=registry):
            await event_platform.async_setup_entry(hass, entry, added.extend)

        self.assertEqual(
            ("event", integration.DOMAIN, "entry-123_button_events"),
            registry.lookup,
        )
        self.assertEqual(["event.old_button_events"], removed)
        self.assertEqual(len(integration.COMMAND_LABELS), len(added))
        self.assertEqual(
            set(integration.COMMAND_LABELS), {item._command for item in added}
        )


class ReaderTest(unittest.IsolatedAsyncioTestCase):
    """Exercise long press timing and scan association with fake evdev."""

    async def test_unknown_key_and_long_press_without_repeat(self) -> None:
        received: list[dict] = []
        state = {
            "device_name": "VUPLUS-BLE-RCU Keyboard",
            "long_press_ms": 10,
            "callbacks": [received.append],
            "diagnostic_callbacks": [],
            "diagnostics": {
                "paired": None, "connected": None, "trusted": None,
                "input_device": False, "reader_active": False,
            },
            "stop": asyncio.Event(),
            "entry": types.SimpleNamespace(entry_id="entry-123"),
            "list_devices": lambda: [],
        }

        class Device:
            def close(self):
                pass

            async def async_read_loop(self):
                yield types.SimpleNamespace(type=4, code=4, value=0x0C016B)
                yield types.SimpleNamespace(type=1, code=240, value=1)
                yield types.SimpleNamespace(type=1, code=240, value=2)
                await asyncio.sleep(0.03)
                yield types.SimpleNamespace(type=1, code=240, value=0)
                state["stop"].set()

        class Hass:
            async def async_add_executor_job(self, function, *args):
                return function(*args)

            def async_create_background_task(self, coroutine, name):
                return asyncio.create_task(coroutine, name=name)

        state["InputDevice"] = lambda path: Device()
        with patch.object(integration, "_find_device", return_value="/dev/input/event7"):
            await integration._reader_supervisor(Hass(), state)

        self.assertEqual(
            ["press", "repeat", "long_press", "long_release"],
            [event["action"] for event in received],
        )
        self.assertEqual("epg", received[0]["command"])
        self.assertEqual(0x16B, received[0]["usage"])
