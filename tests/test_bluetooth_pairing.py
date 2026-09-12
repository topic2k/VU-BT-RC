"""Hardware-free BlueZ tests using real dbus-fast messages and agent metadata.

Install manifest's dbus-fast and voluptuous dependencies before running.
Home Assistant and the Linux D-Bus transport are replaced by small test doubles.
"""

import asyncio
import importlib
import sys
import types
import unittest
from unittest.mock import AsyncMock, patch

import test_event_entity_source  # Installs the existing Home Assistant doubles.
from dbus_fast import Message, Variant
from dbus_fast.errors import DBusError
from dbus_fast.service import ServiceInterface

if sys.platform == "win32":
    # dbus-fast's Linux transport uses ancillary Unix socket operations.
    # Keep its real messages/service decorators, replacing only the transport.
    aio = types.ModuleType("dbus_fast.aio")
    aio.MessageBus = object
    sys.modules["dbus_fast.aio"] = aio

pairing = importlib.import_module("custom_components.vuplus_hid_raw.bluetooth_pairing")
PATH = "/org/bluez/hci0/dev_AA_BB_CC_DD_EE_FF"
REMOTE = pairing.Remote(PATH, "AA:BB:CC:DD:EE:FF", "VUPLUS-BLE-RCU")
IDENTITY = {"address": REMOTE.address, "adapter_address": "11:22:33:44:55:66"}


def properties(**overrides):
    values = {"Name": ("s", "VUPLUS-BLE-RCU"), "Address": ("s", REMOTE.address),
              "Adapter": ("o", "/org/bluez/hci0"), "Paired": ("b", False)}
    values.update(overrides)
    return {key: Variant(signature, value) for key, (signature, value) in values.items()}


class FakeBus:
    def __init__(self):
        self.objects = {"/org/bluez/hci0": {pairing.ADAPTER: {
                            "Powered": Variant("b", True),
                            "Address": Variant("s", IDENTITY["adapter_address"])}},
                        PATH: {pairing.DEVICE: properties()}}
        self.calls = []
        self.failures = {}
        self.disconnected = False
        self.exported = None
        self.unexported = False

    async def connect(self):
        return self

    async def call(self, message):
        self.calls.append(message)
        if message.member in self.failures:
            failure = self.failures[message.member]
            if callable(failure):
                return await failure(message)
            raise failure
        message.serial = len(self.calls)
        if message.member == "GetManagedObjects":
            return Message.new_method_return(message, "a{oa{sa{sv}}}", [self.objects])
        return Message.new_method_return(message)

    def export(self, path, agent):
        self.exported = agent

    def unexport(self, path):
        self.unexported = True

    def disconnect(self):
        self.disconnected = True

    @property
    def members(self):
        return [message.member for message in self.calls]


class BluetoothTest(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.bus = FakeBus()
        patcher = patch.object(pairing, "MessageBus", return_value=self.bus)
        patcher.start()
        self.addCleanup(patcher.stop)

    async def test_pair_trust_connect_and_cleanup(self):
        identity = await pairing.async_pair_remote(REMOTE)
        self.assertEqual(identity, IDENTITY)
        self.assertEqual(self.bus.members, ["GetManagedObjects", "RegisterAgent", "Pair",
                                          "Set", "Connect", "GetManagedObjects", "UnregisterAgent"])
        trust = self.bus.calls[3]
        self.assertEqual(trust.body, [pairing.DEVICE, "Trusted", Variant("b", True)])
        self.assertTrue(self.bus.disconnected)
        self.assertTrue(self.bus.unexported)

    async def test_existing_bond_is_preserved_and_connected(self):
        self.bus.objects[PATH][pairing.DEVICE]["Paired"] = Variant("b", True)
        self.bus.failures["Connect"] = DBusError("org.bluez.Error.AlreadyConnected", "Connected")
        await pairing.async_pair_remote(REMOTE)
        self.assertEqual(self.bus.members, ["GetManagedObjects", "Set", "Connect", "GetManagedObjects"])

    async def test_live_status_uses_the_stored_remote_and_adapter_identity(self):
        props = self.bus.objects[PATH][pairing.DEVICE]
        props["Paired"] = Variant("b", True)
        props["Connected"] = Variant("b", True)
        props["Trusted"] = Variant("b", True)
        self.assertEqual(
            await pairing.async_get_remote_status(IDENTITY),
            {"paired": True, "connected": True, "trusted": True},
        )

    async def test_live_status_reports_removed_remote_as_not_paired(self):
        del self.bus.objects[PATH]
        self.assertEqual(
            await pairing.async_get_remote_status(IDENTITY),
            {"paired": False, "connected": False, "trusted": False},
        )

    async def test_selection_revalidated_before_pairing(self):
        self.bus.objects[PATH][pairing.DEVICE]["Address"] = Variant("s", "00:00:00:00:00:00")
        with self.assertRaises(pairing.PairingError) as error:
            await pairing.async_pair_remote(REMOTE)
        self.assertEqual(error.exception.key, "bluetooth_device_gone")
        self.assertNotIn("Pair", self.bus.members)

    async def test_pair_timeout_cancels_and_unregisters(self):
        self.bus.failures["Pair"] = TimeoutError()
        with self.assertRaises(pairing.PairingError) as error:
            await pairing.async_pair_remote(REMOTE)
        self.assertEqual(error.exception.key, "bluetooth_timeout")
        self.assertEqual(self.bus.members[-2:], ["CancelPairing", "UnregisterAgent"])
        self.assertNotIn("Set", self.bus.members)
        self.assertTrue(self.bus.disconnected)

    async def test_cancellation_cancels_pairing_and_closes_bus(self):
        entered = asyncio.Event()

        async def block(message):
            entered.set()
            await asyncio.Future()

        self.bus.failures["Pair"] = block
        task = asyncio.create_task(pairing.async_pair_remote(REMOTE))
        await entered.wait()
        task.cancel()
        with self.assertRaises(asyncio.CancelledError):
            await task
        self.assertEqual(self.bus.members[-2:], ["CancelPairing", "UnregisterAgent"])
        self.assertTrue(self.bus.disconnected)

    async def test_trust_permission_failure_preserves_pairing(self):
        self.bus.failures["Set"] = DBusError("org.freedesktop.DBus.Error.AccessDenied", "Denied")
        with self.assertRaises(pairing.PairingError) as error:
            await pairing.async_pair_remote(REMOTE)
        self.assertEqual(error.exception.key, "bluetooth_permission")
        self.assertNotIn("Connect", self.bus.members)
        self.assertNotIn("RemoveDevice", self.bus.members)
        self.assertTrue(self.bus.unexported)

    async def test_authentication_error(self):
        self.bus.failures["Pair"] = DBusError("org.bluez.Error.AuthenticationFailed", "Failed")
        with self.assertRaises(pairing.PairingError) as error:
            await pairing.async_pair_remote(REMOTE)
        self.assertEqual(error.exception.key, "bluetooth_authentication")
        self.assertTrue(self.bus.unexported)

    async def test_pin_request_is_explained(self):
        async def request_pin(message):
            self.bus.exported._reject_pin(PATH)

        self.bus.failures["Pair"] = request_pin
        with self.assertRaises(pairing.PairingError) as error:
            await pairing.async_pair_remote(REMOTE)
        self.assertEqual(error.exception.key, "bluetooth_pin_required")

    async def test_scan_filters_devices_and_releases_own_session(self):
        self.bus.objects["/org/bluez/hci0/dev_00_00_00_00_00_00"] = {
            pairing.DEVICE: properties(Name=("s", "Other keyboard"))}
        with patch.object(pairing, "SCAN_SECONDS", 0):
            results = await pairing.async_discover_remotes()
        self.assertEqual(results, [REMOTE])
        self.assertEqual(self.bus.members, ["GetManagedObjects", "StartDiscovery",
                                          "GetManagedObjects", "StopDiscovery"])
        self.assertTrue(self.bus.disconnected)

    async def test_scan_cancellation_stops_discovery(self):
        with patch.object(pairing.asyncio, "sleep", side_effect=asyncio.CancelledError):
            with self.assertRaises(asyncio.CancelledError):
                await pairing.async_discover_remotes()
        self.assertEqual(self.bus.members[-1], "StopDiscovery")
        self.assertTrue(self.bus.disconnected)

    async def test_scan_excludes_paired_bonded_and_connected_remotes(self):
        for state in ("Paired", "Bonded", "Connected"):
            with self.subTest(state=state):
                self.bus.objects[PATH][pairing.DEVICE] = properties(
                    **{state: ("b", True)})
                with patch.object(pairing, "SCAN_SECONDS", 0):
                    self.assertEqual(await pairing.async_discover_remotes(), [])
        self.assertNotIn("RemoveDevice", self.bus.members)
        self.assertNotIn("Disconnect", self.bus.members)

    async def test_scan_excludes_known_address_on_other_adapter(self):
        # The bond remains relevant even if its adapter is powered off.
        self.bus.objects["/org/bluez/hci1"] = {
            pairing.ADAPTER: {"Powered": Variant("b", False)}}
        self.bus.objects[PATH.replace("hci0", "hci1")] = {
            pairing.DEVICE: properties(
                Adapter=("o", "/org/bluez/hci1"),
                Address=("s", REMOTE.address.lower()), Paired=("b", True))}
        new_path = "/org/bluez/hci0/dev_00_11_22_33_44_55"
        self.bus.objects[new_path] = {
            pairing.DEVICE: properties(Address=("s", "00:11:22:33:44:55"))}
        with patch.object(pairing, "SCAN_SECONDS", 0):
            self.assertEqual(await pairing.async_discover_remotes(), [
                pairing.Remote(new_path, "00:11:22:33:44:55", "VUPLUS-BLE-RCU")])

    async def test_scan_uses_state_after_discovery(self):
        async def paired_during_scan(_seconds):
            self.bus.objects[PATH][pairing.DEVICE]["Paired"] = Variant("b", True)

        with patch.object(pairing.asyncio, "sleep", side_effect=paired_during_scan):
            self.assertEqual(await pairing.async_discover_remotes(), [])

    async def test_no_local_adapter_and_powered_off(self):
        for objects, expected in [({}, "bluetooth_no_adapter"),
            ({"/org/bluez/hci0": {pairing.ADAPTER: {"Powered": Variant("b", False)}}},
             "bluetooth_adapter_off")]:
            with self.subTest(expected=expected):
                self.bus.objects = objects
                with self.assertRaises(pairing.PairingError) as error:
                    await pairing.async_discover_remotes()
                self.assertEqual(error.exception.key, expected)

    async def test_partial_multi_adapter_scan_is_cleaned_up(self):
        self.bus.objects["/org/bluez/hci1"] = {pairing.ADAPTER: {"Powered": Variant("b", True)}}

        async def start(message):
            if message.path.endswith("hci1"):
                raise DBusError("org.bluez.Error.NotReady", "Not ready")
            message.serial = len(self.bus.calls)
            return Message.new_method_return(message)

        self.bus.failures["StartDiscovery"] = start
        with self.assertRaises(pairing.PairingError):
            await pairing.async_discover_remotes()
        stopped = [msg.path for msg in self.bus.calls if msg.member == "StopDiscovery"]
        self.assertEqual(stopped, ["/org/bluez/hci0"])

    async def test_bus_error_response_is_translated(self):
        async def fail(message):
            message.serial = len(self.bus.calls)
            return Message.new_error(message, "org.freedesktop.DBus.Error.ServiceUnknown", "No BlueZ")

        self.bus.failures["GetManagedObjects"] = fail
        with self.assertRaises(pairing.PairingError) as error:
            await pairing.async_discover_remotes()
        self.assertEqual(error.exception.key, "bluetooth_unavailable")

    def test_real_agent_signatures_and_device_scope(self):
        agent = pairing._PairingAgent(PATH)
        methods = {item.name: item for item in ServiceInterface._get_methods(agent)}
        self.assertEqual(methods["RequestPasskey"].out_signature, "u")
        self.assertEqual(methods["DisplayPasskey"].in_signature, "ouq")
        methods["RequestAuthorization"].fn(agent, PATH)
        with self.assertRaises(DBusError):
            methods["RequestAuthorization"].fn(agent, "/other")
        with self.assertRaises(DBusError):
            methods["AuthorizeService"].fn(agent, PATH, "unknown-service")


class FlowBase:
    def __init_subclass__(cls, **kwargs):
        pass

    def async_show_form(self, **kwargs):
        return {"type": "form", **kwargs}

    def async_show_menu(self, **kwargs):
        return {"type": "menu", **kwargs}

    def async_show_progress(self, **kwargs):
        return {"type": "progress", **kwargs}

    def async_show_progress_done(self, **kwargs):
        return {"type": "progress_done", **kwargs}

    async def async_set_unique_id(self, value):
        self.unique_id = value

    def _abort_if_unique_id_configured(self):
        if getattr(self, "duplicate", False):
            raise RuntimeError("already_configured")

    def _async_current_entries(self):
        return getattr(self, "current_entries", [])

    def async_abort(self, **kwargs):
        return {"type": "abort", **kwargs}

    def async_update_and_abort(self, entry, *, data_updates, options):
        # HA 2026.9 accepts a complete options mapping, not options_updates.
        entry.data = {**entry.data, **data_updates}
        entry.options = options
        return self.async_abort(reason="reconfigure_successful")

    def async_update_reload_and_abort(self, entry, *, data_updates, options):
        return self.async_update_and_abort(entry, data_updates=data_updates, options=options)

    def async_create_entry(self, **kwargs):
        return {"type": "create_entry", **kwargs}


class OptionsBase(FlowBase):
    @property
    def config_entry(self):
        return self.hass.config_entries.async_get_known_entry(self.handler)


class FlowTest(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        entries = sys.modules["homeassistant.config_entries"]
        entries.ConfigFlow = FlowBase
        entries.OptionsFlow = OptionsBase
        selectors = types.ModuleType("homeassistant.helpers.selector")
        for kind in ("Select", "Number"):
            setattr(selectors, f"{kind}SelectorConfig", lambda **kwargs: kwargs)
            setattr(selectors, f"{kind}Selector", lambda config: lambda value: value)
            setattr(selectors, f"{kind}SelectorMode", types.SimpleNamespace(DROPDOWN="dropdown", BOX="box"))
        sys.modules["homeassistant.helpers"].selector = selectors
        self.module = importlib.import_module("custom_components.vuplus_hid_raw.config_flow")
        self.flow = self.module.ConfigFlow()
        self.flow.hass = types.SimpleNamespace(
            async_create_background_task=lambda coro, name: asyncio.create_task(coro),
            async_add_executor_job=AsyncMock(side_effect=lambda func, *args: func(*args)),
        )
        evdev = types.ModuleType("evdev")
        evdev.InputDevice = lambda path: types.SimpleNamespace(name="VUPLUS-BLE-RCU Keyboard", path=path, close=lambda: None)
        evdev.list_devices = lambda: ["/dev/input/event7"]
        patcher = patch.dict(sys.modules, {"evdev": evdev})
        patcher.start()
        self.addCleanup(patcher.stop)

    async def test_existing_setup_does_not_call_bluetooth(self):
        menu = await self.flow.async_step_user()
        self.assertEqual(menu["menu_options"], ["device", "bluetooth"])
        data = {"device_name": "VUPLUS-BLE-RCU Keyboard", "long_press_ms": 500}
        with patch.object(self.module, "async_pair_remote") as pair:
            result = await self.flow.async_step_device(data)
        pair.assert_not_called()
        self.assertEqual(result["data"], data)
        self.assertEqual(self.flow.unique_id, "name:VUPLUS-BLE-RCU Keyboard")
        self.assertNotIn("/dev/input", str(result["data"]))

    async def test_complete_pairing_flow(self):
        with patch.object(self.module, "async_discover_remotes", AsyncMock(return_value=[REMOTE])):
            result = await self.flow.async_step_bluetooth({})
            self.assertEqual(result["type"], "progress")
            await result["progress_task"]
            result = await self.flow.async_step_scan()
        self.assertEqual(result["next_step_id"], "select_remote")
        with patch.object(self.module, "async_pair_remote", AsyncMock(return_value=IDENTITY)) as pair, \
             patch.object(self.module, "_find_device", return_value="/dev/input/event7"):
            result = await self.flow.async_step_select_remote({"remote": PATH})
            await result["progress_task"]
            result = await self.flow.async_step_pair()
        self.assertEqual(result["next_step_id"], "device")
        pair.assert_awaited_once_with(REMOTE)
        self.flow.hass.async_add_executor_job.assert_awaited()

    async def test_discovery_failure_and_retry(self):
        with patch.object(self.module, "async_discover_remotes", AsyncMock(side_effect=pairing.PairingError("bluetooth_permission"))):
            result = await self.flow.async_step_bluetooth({})
            with self.assertRaises(pairing.PairingError):
                await result["progress_task"]
            result = await self.flow.async_step_scan()
        self.assertEqual(result["next_step_id"], "bluetooth")
        self.assertEqual((await self.flow.async_step_bluetooth())["errors"], {"base": "bluetooth_permission"})
        with patch.object(self.module, "async_discover_remotes", AsyncMock(return_value=[])):
            result = await self.flow.async_step_bluetooth({})
            await result["progress_task"]
            await self.flow.async_step_scan()
        self.assertEqual(self.flow._bluetooth_error, "bluetooth_no_devices")

    async def test_duplicate_is_not_swallowed(self):
        self.flow.duplicate = True
        with self.assertRaisesRegex(RuntimeError, "already_configured"):
            await self.flow.async_step_device({"device_name": "VUPLUS-BLE-RCU Keyboard", "long_press_ms": 500})

    async def test_scan_filters_configured_addresses_including_legacy_metadata(self):
        new_remote = pairing.Remote(
            "/org/bluez/hci0/dev_00_11_22_33_44_55", "00:11:22:33:44:55",
            "VUPLUS-BLE-RCU")
        for data in (
            {"device_address": REMOTE.address.lower()},
            {"bluetooth_device": {"address": REMOTE.address.lower()}},
        ):
            with self.subTest(data=data):
                self.flow.current_entries = [types.SimpleNamespace(data=data)]
                with patch.object(self.module, "async_discover_remotes",
                                  AsyncMock(return_value=[REMOTE, new_remote])):
                    result = await self.flow.async_step_bluetooth({})
                    await result["progress_task"]
                    result = await self.flow.async_step_scan()
                self.assertEqual(result["next_step_id"], "select_remote")
                self.assertEqual(self.flow._remotes, {new_remote.path: new_remote})

    async def test_scan_with_only_configured_remote_offers_retry(self):
        self.flow.current_entries = [types.SimpleNamespace(
            data={"device_address": REMOTE.address})]
        with patch.object(self.module, "async_discover_remotes",
                          AsyncMock(return_value=[REMOTE])):
            result = await self.flow.async_step_bluetooth({})
            await result["progress_task"]
            result = await self.flow.async_step_scan()
        self.assertEqual(result["next_step_id"], "bluetooth")
        self.assertEqual(self.flow._bluetooth_error, "bluetooth_no_devices")
        self.assertEqual(self.flow._remotes, {})

    async def test_pairing_failure_returns_to_retry(self):
        self.flow._selected_remote = REMOTE
        with patch.object(self.module, "async_pair_remote", AsyncMock(side_effect=pairing.PairingError("bluetooth_timeout"))):
            result = await self.flow.async_step_pair()
            with self.assertRaises(pairing.PairingError):
                await result["progress_task"]
            result = await self.flow.async_step_pair()
        self.assertEqual(result["next_step_id"], "bluetooth")
        self.assertEqual(self.flow._bluetooth_error, "bluetooth_timeout")

    async def test_empty_evdev_list_can_be_refreshed(self):
        with patch.object(sys.modules["evdev"], "list_devices", return_value=[]):
            result = await self.flow.async_step_device()
        self.assertEqual(result["step_id"], "device_missing")
        self.assertEqual(result["data_schema"]({}), {})
        result = await self.flow.async_step_device_missing({})
        self.assertEqual(result["step_id"], "device")

    async def test_options_use_home_assistant_entry_and_save_threshold(self):
        entry = types.SimpleNamespace(options={"long_press_ms": 750}, data={})
        flow = self.module.ConfigFlow.async_get_options_flow(entry)
        flow.hass = types.SimpleNamespace(config_entries=types.SimpleNamespace(
            async_get_known_entry=lambda handler: entry))
        flow.handler = "entry-id"
        result = await flow.async_step_init()
        self.assertEqual(result["data_schema"]({}), {"long_press_ms": 750})
        result = await flow.async_step_init({"long_press_ms": 1000})
        self.assertEqual(result["data"], {"long_press_ms": 1000})
