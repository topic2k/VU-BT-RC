"""Removal lifecycle and exact Bluetooth bond ownership regression tests."""

import asyncio
import importlib
import json
import sys
import types
import unittest
from unittest.mock import AsyncMock, Mock, patch

import test_bluetooth_pairing as bluetooth_tests
from test_bluetooth_pairing import FakeBus, IDENTITY, PATH, REMOTE, pairing, properties
from dbus_fast import Variant
from dbus_fast.errors import DBusError
from test_event_entity_source import integration


class UnpairTest(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.bus = FakeBus()
        patcher = patch.object(pairing, "MessageBus", return_value=self.bus)
        patcher.start()
        self.addCleanup(patcher.stop)

    async def test_remove_only_exact_device_on_renumbered_adapter(self):
        adapter = self.bus.objects.pop("/org/bluez/hci0")
        self.bus.objects["/org/bluez/hci3"] = adapter
        props = self.bus.objects.pop(PATH)[pairing.DEVICE]
        props["Adapter"] = Variant("o", "/org/bluez/hci3")
        new_path = PATH.replace("hci0", "hci3")
        self.bus.objects[new_path] = {pairing.DEVICE: props}
        self.bus.objects["/org/bluez/hci0"] = {pairing.ADAPTER: {
            "Address": Variant("s", "00:00:00:00:00:01")}}
        self.bus.objects[PATH] = {pairing.DEVICE: properties()}
        other = PATH.replace("AA_BB", "00_00").replace("hci0", "hci3")
        self.bus.objects[other] = {pairing.DEVICE: properties(
            Address=("s", "00:00:CC:DD:EE:FF"), Adapter=("o", "/org/bluez/hci3"))}
        await pairing.async_unpair_remote(IDENTITY)
        removal = self.bus.calls[-1]
        self.assertEqual((removal.member, removal.path, removal.body),
                         ("RemoveDevice", "/org/bluez/hci3", [new_path]))
        self.assertTrue(self.bus.disconnected)

    async def test_missing_device_is_already_unpaired(self):
        del self.bus.objects[PATH]
        await pairing.async_unpair_remote(IDENTITY)
        self.assertEqual(self.bus.members, ["GetManagedObjects"])

    async def test_missing_adapter_does_not_report_success(self):
        del self.bus.objects["/org/bluez/hci0"]
        with self.assertRaises(pairing.PairingError) as error:
            await pairing.async_unpair_remote(IDENTITY)
        self.assertEqual(str(error.exception), "bluetooth_no_adapter")
        self.assertNotIn("RemoveDevice", self.bus.members)

    async def test_invalid_identity_never_deletes(self):
        for identity in [{}, {"address": REMOTE.address},
                         {**IDENTITY, "address": "VUPLUS-BLE-RCU"}]:
            with self.subTest(identity=identity), self.assertRaises(pairing.PairingError):
                await pairing.async_unpair_remote(identity)
        self.assertEqual(self.bus.members, [])

    async def test_remove_failure_is_propagated_and_bus_closed(self):
        self.bus.failures["RemoveDevice"] = DBusError("org.freedesktop.DBus.Error.AccessDenied", "Denied")
        with self.assertRaises(pairing.PairingError) as error:
            await pairing.async_unpair_remote(IDENTITY)
        self.assertEqual(str(error.exception), "bluetooth_permission")
        self.assertTrue(self.bus.disconnected)

    async def test_concurrent_removal_is_idempotent(self):
        self.bus.failures["RemoveDevice"] = DBusError("org.bluez.Error.DoesNotExist", "Gone")
        await pairing.async_unpair_remote(IDENTITY)

    async def test_resolve_existing_manual_pairing(self):
        self.bus.objects[PATH][pairing.DEVICE]["Paired"] = Variant("b", True)
        self.assertEqual(await pairing.async_resolve_pairing(REMOTE.address.lower()), IDENTITY)

    async def test_ambiguous_adapter_requires_exact_adapter_address(self):
        self.bus.objects[PATH][pairing.DEVICE]["Paired"] = Variant("b", True)
        self.bus.objects["/org/bluez/hci1"] = {pairing.ADAPTER: {
            "Address": Variant("s", "00:00:00:00:00:01")}}
        self.bus.objects[PATH.replace("hci0", "hci1")] = {pairing.DEVICE: properties(
            Paired=("b", True), Adapter=("o", "/org/bluez/hci1"))}
        self.assertIsNone(await pairing.async_resolve_pairing(REMOTE.address))
        self.assertEqual(await pairing.async_resolve_pairing(
            REMOTE.address, IDENTITY["adapter_address"]), IDENTITY)


class RemovalLifecycleTest(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.entry = types.SimpleNamespace(entry_id="remote-1", data={
            "device_name": integration.DEFAULT_DEVICE_NAME,
            integration.CONF_BLUETOOTH_DEVICE: IDENTITY}, options={})
        self.hass = types.SimpleNamespace(data={}, config_entries=types.SimpleNamespace(
            async_entries=Mock(return_value=[]), async_reload=AsyncMock(),
            async_unload_platforms=AsyncMock(return_value=True)))
        self.issue = Mock()
        registry = types.SimpleNamespace(async_create_issue=self.issue,
            IssueSeverity=types.SimpleNamespace(WARNING="warning"))
        patcher = patch.object(sys.modules["homeassistant.helpers"],
            "issue_registry", registry, create=True)
        patcher.start()
        self.addCleanup(patcher.stop)

    async def test_delete_only_creates_persistent_confirmation(self):
        with patch.object(pairing, "async_unpair_remote", AsyncMock()) as remove:
            await integration.async_remove_entry(self.hass, self.entry)
        remove.assert_not_called()
        issue = self.issue.call_args.kwargs
        self.assertTrue(issue["is_persistent"])
        self.assertTrue(issue["is_fixable"])
        self.assertEqual(issue["translation_key"], "confirm_unpair")
        self.assertEqual(issue["data"], {**IDENTITY, "device_name": integration.DEFAULT_DEVICE_NAME})
        self.assertEqual(json.loads(json.dumps(issue["data"])), issue["data"])

    async def test_reload_and_disable_do_not_unpair(self):
        self.hass.data[integration.DOMAIN] = {self.entry.entry_id: {
            "stop": asyncio.Event(), "task": None}}
        with patch.object(pairing, "async_unpair_remote", AsyncMock()) as remove:
            await integration.async_reload_entry(self.hass, self.entry)
            await integration.async_unload_entry(self.hass, self.entry)
        remove.assert_not_called()
        self.hass.config_entries.async_reload.assert_awaited_once_with(self.entry.entry_id)
        self.hass.config_entries.async_unload_platforms.assert_awaited()

    async def test_legacy_entry_resolves_identity_without_unpairing(self):
        del self.entry.data[integration.CONF_BLUETOOTH_DEVICE]
        with patch.object(integration, "_async_get_bluetooth_device", AsyncMock(return_value=IDENTITY)), \
             patch.object(pairing, "async_unpair_remote", AsyncMock()) as remove:
            await integration.async_remove_entry(self.hass, self.entry)
        remove.assert_not_called()
        self.assertEqual(self.issue.call_args.kwargs["data"]["address"], REMOTE.address)

    async def test_missing_mapping_still_allows_user_to_keep_pairing(self):
        del self.entry.data[integration.CONF_BLUETOOTH_DEVICE]
        with patch.object(integration, "_async_get_bluetooth_device", AsyncMock(return_value=None)), \
             patch.object(pairing, "async_unpair_remote", AsyncMock()) as remove:
            await integration.async_remove_entry(self.hass, self.entry)
        remove.assert_not_called()
        self.assertIsNone(self.issue.call_args.kwargs["data"]["address"])

    async def test_setup_saves_legacy_mapping_without_changing_reader_name(self):
        del self.entry.data[integration.CONF_BLUETOOTH_DEVICE]
        self.entry.async_on_unload = Mock()
        self.entry.add_update_listener = Mock()
        self.hass.config_entries.async_update_entry = Mock()
        self.hass.config_entries.async_forward_entry_setups = AsyncMock()
        self.hass.async_create_background_task = lambda coro, name: asyncio.create_task(coro)
        fake_evdev = types.SimpleNamespace(InputDevice=object, list_devices=lambda: [])
        with patch.dict(sys.modules, {"evdev": fake_evdev}), \
             patch.object(integration, "_async_get_bluetooth_device", AsyncMock(return_value=IDENTITY)), \
             patch.object(integration, "_reader_supervisor", AsyncMock()):
            self.assertTrue(await integration.async_setup_entry(self.hass, self.entry))
            await self.hass.data[integration.DOMAIN][self.entry.entry_id]["task"]
        data = self.hass.config_entries.async_update_entry.call_args.kwargs["data"]
        self.assertEqual(data[integration.CONF_BLUETOOTH_DEVICE], IDENTITY)
        self.assertEqual(data["device_name"], integration.DEFAULT_DEVICE_NAME)
        self.assertNotIn("/dev/input", str(data))

    def test_evdev_metadata_is_optional_and_devices_are_closed(self):
        closed = []
        def device(path):
            return types.SimpleNamespace(name=integration.DEFAULT_DEVICE_NAME,
                uniq=REMOTE.address, phys=f"{IDENTITY['adapter_address']}/input0",
                close=lambda: closed.append(path))
        self.assertEqual(integration._read_bluetooth_addresses(
            integration.DEFAULT_DEVICE_NAME, lambda: ["/dev/input/event7"], device),
            (REMOTE.address, IDENTITY["adapter_address"]))
        self.assertEqual(closed, ["/dev/input/event7"])
        def missing(path):
            result = device(path)
            del result.uniq
            return result
        self.assertIsNone(integration._read_bluetooth_addresses(
            integration.DEFAULT_DEVICE_NAME, lambda: ["/dev/input/event8"], missing))
        self.assertEqual(closed[-1], "/dev/input/event8")


class PairingFlowPersistenceTest(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        bluetooth_tests.FlowTest.setUp(self)

    async def test_pairing_wizard_persists_addresses_only(self):
        self.flow._selected_remote = REMOTE
        with patch.object(self.module, "async_pair_remote", AsyncMock(return_value=IDENTITY)):
            await self.flow._async_pair_and_wait()
        result = await self.flow.async_step_device({
            "device_name": integration.DEFAULT_DEVICE_NAME, "long_press_ms": 500})
        self.assertEqual(result["data"][integration.CONF_BLUETOOTH_DEVICE], IDENTITY)
        self.assertNotIn("hci0", str(result["data"]))
        self.assertNotIn("/dev/input", str(result["data"]))

    async def test_manual_setup_saves_verified_mapping(self):
        with patch.object(self.module, "_async_get_bluetooth_device", AsyncMock(return_value=IDENTITY)):
            result = await self.flow.async_step_device({
                "device_name": integration.DEFAULT_DEVICE_NAME, "long_press_ms": 500})
        self.assertEqual(result["data"][integration.CONF_BLUETOOTH_DEVICE], IDENTITY)


class ConfirmUnpairTest(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        bluetooth_tests.FlowTest.setUp(self)
        repairs_base = types.ModuleType("homeassistant.components.repairs")
        repairs_base.RepairsFlow = bluetooth_tests.FlowBase
        self.patch_modules = patch.dict(sys.modules, {"homeassistant.components.repairs": repairs_base})
        self.patch_modules.start()
        self.addCleanup(self.patch_modules.stop)
        self.repairs = importlib.import_module("custom_components.vuplus_hid_raw.repairs")
        self.flow = self.repairs.UnpairRepairFlow()
        self.flow.data = json.loads(json.dumps({**IDENTITY, "device_name": integration.DEFAULT_DEVICE_NAME}))
        self.flow.hass = types.SimpleNamespace(
            async_create_background_task=lambda coro, name: asyncio.create_task(coro),
            config_entries=types.SimpleNamespace(async_entries=Mock(return_value=[])))
        self.remove = AsyncMock()
        patcher = patch.object(self.repairs, "async_unpair_remote", self.remove)
        patcher.start()
        self.addCleanup(patcher.stop)

    async def test_repair_options_are_translatable_and_missing_addresses_are_neutral(self):
        captured = []

        def select_config(**kwargs):
            captured.append(kwargs)
            return kwargs

        self.flow.data = {}
        with patch.object(self.repairs.selector, "SelectSelectorConfig", select_config):
            result = await self.flow.async_step_confirm()
        self.assertEqual(result["data_schema"]({}), {"action": "keep"})
        self.assertEqual(result["description_placeholders"], {"address": "—", "adapter": "—"})
        self.assertEqual(captured[0]["translation_key"], "unpair_action")
        self.assertEqual(captured[0]["options"], ["keep", "delete"])
        from test_localization import catalog
        for language in ("de", "en"):
            options = catalog(language)["selector"][captured[0]["translation_key"]]["options"]
            self.assertEqual(set(options), set(captured[0]["options"]))
            self.assertTrue(all(options.values()))
        self.remove.assert_not_called()

    async def test_initial_dialog_and_keep_do_not_unpair(self):
        result = await self.flow.async_step_init()
        self.assertEqual(result["data_schema"]({}), {"action": "keep"})
        self.remove.assert_not_called()
        result = await self.flow.async_step_confirm({"action": "keep"})
        self.assertEqual(result["type"], "create_entry")
        self.remove.assert_not_called()

    async def test_empty_or_unknown_choice_is_not_confirmation(self):
        for user_input in [{}, {"action": "unknown"}]:
            result = await self.flow.async_step_confirm(user_input)
            self.assertEqual(result["type"], "form")
        self.remove.assert_not_called()

    async def test_progress_step_cannot_start_without_confirmation(self):
        result = await self.flow.async_step_unpair()
        self.assertEqual(result["step_id"], "confirm")
        self.remove.assert_not_called()

    async def test_init_input_cannot_bypass_displaying_question(self):
        result = await self.flow.async_step_init({"action": "delete"})
        self.assertEqual(result["step_id"], "confirm")
        self.remove.assert_not_called()

    async def test_only_explicit_delete_unpairs_persisted_identity(self):
        result = await self.flow.async_step_confirm({"action": "delete"})
        self.assertEqual(result["type"], "progress")
        await result["progress_task"]
        result = await self.flow.async_step_unpair()
        self.assertEqual(result["next_step_id"], "done")
        self.remove.assert_awaited_once_with(IDENTITY)
        result = await self.flow.async_step_done()
        self.assertEqual(result["type"], "create_entry")

    async def test_failure_needs_fresh_confirmation_and_can_be_kept(self):
        self.remove.side_effect = pairing.PairingError("bluetooth_permission")
        result = await self.flow.async_step_confirm({"action": "delete"})
        with self.assertRaises(pairing.PairingError):
            await result["progress_task"]
        result = await self.flow.async_step_unpair()
        self.assertEqual(result["next_step_id"], "confirm")
        form = await self.flow.async_step_confirm()
        self.assertEqual(form["errors"], {"base": "bluetooth_permission"})
        self.assertEqual(form["data_schema"]({}), {"action": "keep"})
        await self.flow.async_step_unpair()
        self.assertEqual(self.remove.await_count, 1)
        await self.flow.async_step_confirm({"action": "keep"})
        self.assertEqual(self.remove.await_count, 1)

    async def test_new_or_shared_entry_blocks_old_confirmation(self):
        for data in [{integration.CONF_BLUETOOTH_DEVICE: IDENTITY},
                     {"device_name": integration.DEFAULT_DEVICE_NAME}]:
            self.flow.hass.config_entries.async_entries.return_value = [types.SimpleNamespace(data=data)]
            result = await self.flow.async_step_confirm({"action": "delete"})
            with self.assertRaises(pairing.PairingError):
                await result["progress_task"]
            await self.flow.async_step_unpair()
            self.assertEqual(self.flow._error, "bluetooth_still_in_use")
        self.remove.assert_not_called()

    async def test_missing_identity_cannot_delete(self):
        self.flow.data = None
        result = await self.flow.async_step_confirm({"action": "delete"})
        with self.assertRaises(pairing.PairingError):
            await result["progress_task"]
        await self.flow.async_step_unpair()
        self.assertEqual(self.flow._error, "bluetooth_identity_missing")
        self.remove.assert_not_called()

    async def test_factory_leaves_issue_data_to_home_assistant(self):
        flow = await self.repairs.async_create_fix_flow(None, "unpair_remote-1", self.flow.data)
        self.assertIsInstance(flow, self.repairs.UnpairRepairFlow)
        self.assertFalse(flow._confirmed)
        with self.assertRaises(ValueError):
            await self.repairs.async_create_fix_flow(None, "unrelated", None)
