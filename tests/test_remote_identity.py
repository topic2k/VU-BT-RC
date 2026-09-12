"""Two identical remotes must stay separate across discovery and reconnects."""

import asyncio
import json
import sys
import types
import unittest
from unittest.mock import AsyncMock, Mock, patch

import test_bluetooth_pairing as bluetooth_tests
from test_event_entity_source import integration, event_platform, binary_sensor_platform
from custom_components.vuplus_hid_raw import input_device as inputs

NAME = integration.DEFAULT_DEVICE_NAME
FIRST = "68:96:6A:35:53:86"
SECOND = "68:96:6A:15:BA:3F"


class Devices:
    def __init__(self, values=None):
        self.values = values if values is not None else {
            "/dev/input/event7": (NAME, FIRST.lower()),
            "/dev/input/event9": (NAME, SECOND),
        }
        self.opened = []

    def paths(self):
        return list(self.values)

    def open(self, path):
        name, address = self.values[path]
        device = types.SimpleNamespace(
            name=name, uniq=address, path=path,
            phys="11:22:33:44:55:66/input0", close=Mock(),
        )
        self.opened.append(device)
        return device


class IdentityTest(unittest.TestCase):
    def test_dropdown_keeps_same_name_with_distinct_addresses(self):
        devices = Devices()
        choices = inputs.list_input_choices(devices.paths, devices.open)
        self.assertEqual({FIRST, SECOND}, {choice.address for choice in choices})
        self.assertEqual(2, len({choice.value for choice in choices}))
        for choice in choices:
            self.assertIn(choice.address, choice.option["label"])
            self.assertIn(choice.path, choice.option["label"])
            self.assertNotIn("/dev/input", choice.value)
        for device in devices.opened:
            device.close.assert_called_once()

    def test_reported_host_metadata_matches_both_remotes(self):
        # User supplied /proc/bus/input/devices on 2026-09-12: same phys, distinct uniq.
        devices = Devices({"/dev/input/event7": (NAME, SECOND.lower()),
                           "/dev/input/event5": (NAME, FIRST.lower())})
        def open_device(path):
            device = devices.open(path)
            device.phys = "88:a2:9e:e3:76:a5"
            return device
        for address, path in [(FIRST, "/dev/input/event5"), (SECOND, "/dev/input/event7")]:
            self.assertEqual(path, integration._find_device(NAME, devices.paths, open_device, address))
            self.assertEqual((address, "88:A2:9E:E3:76:A5"), integration._read_bluetooth_addresses(
                NAME, devices.paths, open_device, address))

    def test_reader_uses_exact_address_and_keeps_verified_handle(self):
        devices = Devices()
        selected = inputs.open_input_device(NAME, devices.paths, devices.open, SECOND.lower())
        self.assertIs(selected, devices.opened[1])
        self.assertEqual(selected.uniq, SECOND)
        devices.opened[0].close.assert_called_once()
        selected.close.assert_not_called()
        selected.close()

    def test_reconnect_follows_address_when_paths_are_reused(self):
        devices = Devices()
        self.assertEqual("/dev/input/event7", integration._find_device(
            NAME, devices.paths, devices.open, FIRST))
        devices.values = {
            "/dev/input/event7": (NAME, SECOND),
            "/dev/input/event12": (NAME, FIRST),
        }
        self.assertEqual("/dev/input/event12", integration._find_device(
            NAME, devices.paths, devices.open, FIRST))

    def test_missing_selected_remote_never_falls_back_to_other(self):
        devices = Devices({"/dev/input/event7": (NAME, SECOND)})
        self.assertIsNone(inputs.open_input_device(NAME, devices.paths, devices.open, FIRST))
        devices.opened[0].close.assert_called_once()

    def test_name_only_ambiguity_closes_all_handles(self):
        devices = Devices()
        self.assertIsNone(inputs.open_input_device(NAME, devices.paths, devices.open))
        for device in devices.opened:
            device.close.assert_called_once()

    def test_name_and_address_must_both_match(self):
        devices = Devices({"/dev/input/event7": ("VUPLUS-BLE-RCU Mouse", FIRST)})
        self.assertIsNone(inputs.open_input_device(NAME, devices.paths, devices.open, FIRST))

    def test_missing_or_duplicate_identity_cannot_be_selected_ambiguously(self):
        for addresses in [(None, None), (FIRST, FIRST)]:
            devices = Devices({f"/dev/input/event{i}": (NAME, address)
                               for i, address in enumerate(addresses)})
            self.assertEqual([], inputs.list_input_choices(devices.paths, devices.open))
            self.assertIsNone(inputs.open_input_device(
                NAME, devices.paths, devices.open, addresses[0]))

    def test_single_device_without_metadata_still_works(self):
        devices = Devices({"/dev/input/event7": (NAME, None)})
        choices = inputs.list_input_choices(devices.paths, devices.open)
        self.assertEqual(NAME, choices[0].value)
        self.assertEqual("/dev/input/event7", integration._find_device(
            NAME, devices.paths, devices.open))

    def test_invalid_address_does_not_enable_name_fallback(self):
        devices = Devices({"/dev/input/event7": (NAME, None)})
        self.assertIsNone(inputs.open_input_device(NAME, devices.paths, devices.open, "bad"))

    def test_cleanup_metadata_resolves_only_selected_remote(self):
        devices = Devices()
        self.assertIsNone(integration._read_bluetooth_addresses(NAME, devices.paths, devices.open))
        self.assertEqual((FIRST, "11:22:33:44:55:66"), integration._read_bluetooth_addresses(
            NAME, devices.paths, devices.open, FIRST))

    def test_legacy_pairing_address_is_reader_identity(self):
        entry = types.SimpleNamespace(data={"bluetooth_device": {"address": FIRST.lower()}})
        self.assertEqual(FIRST, inputs.entry_address(entry))

    def test_device_names_and_serial_numbers_distinguish_remotes(self):
        for address in (FIRST, SECOND):
            state = {"entry": types.SimpleNamespace(entry_id=address, unique_id=address),
                     "device_address": address}
            for entity in (event_platform.VuplusRemoteButtonEvent(state, "ok"),
                           binary_sensor_platform.VuplusRemoteDiagnostic(state, "paired")):
                info = entity._attr_device_info
                self.assertEqual("remote_with_address", info["translation_key"])
                self.assertEqual({"address": address}, info["translation_placeholders"])
                self.assertEqual(address, info["serial_number"])


class MultiRemoteFlowTest(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        bluetooth_tests.FlowTest.setUp(self)
        self.devices = Devices()
        sys.modules["evdev"].InputDevice = self.devices.open
        sys.modules["evdev"].list_devices = self.devices.paths
        patcher = patch.object(self.module, "_async_get_bluetooth_device", AsyncMock(return_value=None))
        patcher.start()
        self.addCleanup(patcher.stop)

    def data(self, address):
        return {"device_name": json.dumps([NAME, address]), "long_press_ms": 500}

    async def test_create_two_entries_and_reject_duplicate(self):
        first = await self.flow.async_step_device(self.data(FIRST))
        first_id = self.flow.unique_id
        self.flow.current_entries = [types.SimpleNamespace(entry_id="first", data=first["data"])]
        second = await self.flow.async_step_device(self.data(SECOND))
        self.assertNotEqual(first_id, self.flow.unique_id)
        self.assertEqual(FIRST, first["data"]["device_address"])
        self.assertEqual(SECOND, second["data"]["device_address"])
        for result in (first, second):
            self.assertEqual(NAME, result["data"]["device_name"])
            self.assertNotIn("/dev/input", str(result["data"]))
        duplicate = await self.flow.async_step_device(self.data(FIRST))
        self.assertEqual("already_configured", duplicate["reason"])

    async def test_unbound_legacy_entry_must_be_bound_before_second_setup(self):
        self.flow.current_entries = [types.SimpleNamespace(entry_id="old", data={"device_name": NAME})]
        result = await self.flow.async_step_device(self.data(FIRST))
        self.assertEqual("legacy_entry_needs_address", result["reason"])

    async def test_legacy_pairing_metadata_prevents_duplicate(self):
        self.flow.current_entries = [types.SimpleNamespace(entry_id="old", data={
            "device_name": NAME, "bluetooth_device": {"address": FIRST.lower()}})]
        result = await self.flow.async_step_device(self.data(FIRST))
        self.assertEqual("already_configured", result["reason"])

    async def test_reconfigure_binds_legacy_and_preserves_ids_and_options(self):
        entry = types.SimpleNamespace(entry_id="old", unique_id=f"name:{NAME}",
                                     data={"device_name": NAME}, options={"long_press_ms": 750},
                                     update_listeners=[object()])
        self.flow._get_reconfigure_entry = lambda: entry
        self.flow.current_entries = [entry]
        before = event_platform.VuplusRemoteButtonEvent({"entry": entry}, "ok")
        result = await self.flow.async_step_reconfigure(self.data(FIRST))
        self.assertEqual("reconfigure_successful", result["reason"])
        self.assertEqual(FIRST, entry.data["device_address"])
        self.assertEqual(500, entry.options["long_press_ms"])
        after = event_platform.VuplusRemoteButtonEvent({"entry": entry}, "ok")
        self.assertEqual(before._attr_unique_id, after._attr_unique_id)
        self.assertEqual(before._attr_device_info["identifiers"], after._attr_device_info["identifiers"])

    async def test_reconfigure_unloaded_entry_schedules_reload(self):
        entry = types.SimpleNamespace(entry_id="old", unique_id=f"name:{NAME}",
                                     data={"device_name": NAME}, options={}, update_listeners=[])
        self.flow._get_reconfigure_entry = lambda: entry
        with patch.object(self.flow, "async_update_reload_and_abort",
                          wraps=self.flow.async_update_reload_and_abort) as reload_entry:
            await self.flow.async_step_reconfigure(self.data(FIRST))
        reload_entry.assert_called_once()

    async def test_reconfigure_cannot_silently_replace_bound_remote(self):
        entry = types.SimpleNamespace(entry_id="old", unique_id="old", options={}, data={
            "device_name": NAME, "device_address": FIRST})
        self.flow._get_reconfigure_entry = lambda: entry
        result = await self.flow.async_step_reconfigure(self.data(SECOND))
        self.assertEqual("device_not_found", result["errors"]["base"])
        self.assertEqual(FIRST, entry.data["device_address"])

    async def test_pairing_flow_does_not_offer_other_connected_remote(self):
        self.flow._paired_identity = {"address": FIRST, "adapter_address": "11:22:33:44:55:66"}
        self.devices.values = {"/dev/input/event7": (NAME, SECOND)}
        result = await self.flow.async_step_device(self.data(SECOND))
        self.assertEqual("device_missing", result["step_id"])
        self.assertEqual("device_not_found", result["errors"]["base"])

    async def test_selection_disappears_before_validation(self):
        with patch.object(self.module, "_find_device", return_value=None):
            result = await self.flow.async_step_device(self.data(FIRST))
        self.assertEqual("device_not_found", result["errors"]["base"])


class SeparateReadersTest(unittest.IsolatedAsyncioTestCase):
    async def test_legacy_reader_pins_address_without_bluez(self):
        devices = Devices({"/dev/input/event7": (NAME, FIRST.lower())})
        entry = types.SimpleNamespace(entry_id="old", data={"device_name": NAME})
        state = {
            "entry": entry, "device_name": NAME, "long_press_ms": 500,
            "callbacks": [], "diagnostic_callbacks": [], "diagnostics": {},
            "stop": asyncio.Event(), "list_devices": devices.paths,
        }

        def open_device(path):
            device = devices.open(path)

            async def events():
                state["stop"].set()
                if False:
                    yield

            device.async_read_loop = events
            return device

        state["InputDevice"] = open_device
        update = Mock()
        hass = types.SimpleNamespace(
            async_add_executor_job=AsyncMock(side_effect=lambda func, *args: func(*args)),
            config_entries=types.SimpleNamespace(async_update_entry=update),
        )
        await integration._reader_supervisor(hass, state)
        self.assertEqual(FIRST, state["device_address"])
        update.assert_called_once_with(entry, data={"device_name": NAME, "device_address": FIRST})
        self.assertNotIn("/dev/input", str(update.call_args))
        devices.opened[0].close.assert_called_once()

    async def test_ambiguous_legacy_reader_stays_inactive(self):
        devices = Devices()
        received = []
        state = {
            "entry": types.SimpleNamespace(entry_id="old"), "device_name": NAME,
            "long_press_ms": 500, "callbacks": [received.append],
            "diagnostic_callbacks": [], "diagnostics": {}, "stop": asyncio.Event(),
            "list_devices": devices.paths, "InputDevice": devices.open,
        }
        hass = types.SimpleNamespace(
            async_add_executor_job=AsyncMock(side_effect=lambda func, *args: func(*args)),
        )
        with patch.object(integration.asyncio, "sleep", AsyncMock(side_effect=lambda _: state["stop"].set())):
            await integration._reader_supervisor(hass, state)
        self.assertEqual([], received)
        self.assertFalse(state["diagnostics"]["input_device"])
        self.assertFalse(state["diagnostics"]["reader_active"])

    async def test_each_reader_publishes_only_its_own_remote(self):
        devices = Devices()
        received = {FIRST: [], SECOND: []}
        states = {}
        for address in received:
            states[address] = {
                "entry": types.SimpleNamespace(entry_id=address), "device_name": NAME,
                "device_address": address, "long_press_ms": 500,
                "callbacks": [received[address].append], "diagnostic_callbacks": [],
                "diagnostics": {}, "stop": asyncio.Event(), "list_devices": devices.paths,
            }

        def open_device(path):
            device = devices.open(path)
            address = inputs.device_address(device)

            async def events():
                # Different buttons on physically different remotes.
                code = 28 if address == FIRST else 139
                yield types.SimpleNamespace(type=1, code=code, value=1)
                yield types.SimpleNamespace(type=1, code=code, value=0)
                states[address]["stop"].set()

            device.async_read_loop = events
            return device

        hass = types.SimpleNamespace(
            async_add_executor_job=AsyncMock(side_effect=lambda func, *args: func(*args)),
            async_create_background_task=lambda coro, name: asyncio.create_task(coro),
        )
        for state in states.values():
            state["InputDevice"] = open_device
        await asyncio.gather(*(integration._reader_supervisor(hass, state) for state in states.values()))
        self.assertEqual(["ok", "ok"], [event["command"] for event in received[FIRST]])
        self.assertEqual(["menu", "menu"], [event["command"] for event in received[SECOND]])
        for device in devices.opened:
            device.close.assert_called_once()
