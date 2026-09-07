"""Local BlueZ pairing for the VU+ remote (no GATT/proxy connection)."""

import asyncio
import re
from contextlib import asynccontextmanager, suppress
from dataclasses import dataclass

from dbus_fast import BusType, Message, MessageType, Variant
from dbus_fast.aio import MessageBus
from dbus_fast.errors import DBusError
from dbus_fast.service import ServiceInterface, method

BLUEZ = "org.bluez"
ADAPTER = "org.bluez.Adapter1"
DEVICE = "org.bluez.Device1"
PROPERTIES = "org.freedesktop.DBus.Properties"
AGENT_MANAGER = "org.bluez.AgentManager1"
AGENT_PATH = "/vuplus_hid_raw/pairing_agent"
CALL_TIMEOUT = 10
SCAN_SECONDS = 10
PAIR_TIMEOUT = 60
REMOTE_NAME = "VUPLUS-BLE-RCU"
HID_UUIDS = {
    "00001812-0000-1000-8000-00805f9b34fb",
    "00001124-0000-1000-8000-00805f9b34fb",
}


def normalize_address(value) -> str | None:
    """Accept only a complete Bluetooth address, never a name or event path."""
    if isinstance(value, str) and re.fullmatch(r"[0-9a-fA-F]{2}(?::[0-9a-fA-F]{2}){5}", value):
        return value.upper()
    return None


def _pairing_identity(objects, properties) -> dict[str, str] | None:
    adapter = objects.get(_value(properties, "Adapter"), {}).get(ADAPTER, {})
    address = normalize_address(_value(properties, "Address"))
    adapter_address = normalize_address(_value(adapter, "Address"))
    if address and adapter_address:
        return {"address": address, "adapter_address": adapter_address}
    return None


async def async_resolve_pairing(address: str, adapter_address: str | None = None):
    """Resolve evdev's Bluetooth addresses to one local BlueZ pairing."""
    address = normalize_address(address)
    if not address:
        return None
    async with _connection() as bus:
        objects = await _objects(bus)
        matches = []
        for interfaces in objects.values():
            props = interfaces.get(DEVICE, {})
            if not _is_remote(props) or not _value(props, "Paired", False):
                continue
            identity = _pairing_identity(objects, props)
            if (identity and identity["address"] == address
                    and (adapter_address is None or identity["adapter_address"] == adapter_address)):
                matches.append(identity)
        return matches[0] if len(matches) == 1 else None


async def async_get_remote_status(identity: dict[str, str] | None) -> dict[str, bool] | None:
    """Return the live BlueZ state for one previously identified remote."""
    identity = identity if isinstance(identity, dict) else {}
    address = normalize_address(identity.get("address"))
    adapter_address = normalize_address(identity.get("adapter_address"))
    if not address or not adapter_address:
        return None
    async with _connection() as bus:
        objects = await _objects(bus)
        matches = [
            props for interfaces in objects.values()
            if (props := interfaces.get(DEVICE)) is not None
            and normalize_address(_value(props, "Address")) == address
            and _pairing_identity(objects, props) == {
                "address": address, "adapter_address": adapter_address
            }
        ]
        if len(matches) != 1:
            return {"paired": False, "connected": False, "trusted": False}
        props = matches[0]
        return {
            "paired": bool(_value(props, "Paired", False)),
            "connected": bool(_value(props, "Connected", False)),
            "trusted": bool(_value(props, "Trusted", False)),
        }


async def async_unpair_remote(identity: dict[str, str]) -> None:
    """Forget only the exact remote on its original physical adapter."""
    address = normalize_address(identity.get("address"))
    adapter_address = normalize_address(identity.get("adapter_address"))
    if not address or not adapter_address:
        raise PairingError("bluetooth_identity_missing")
    async with _connection() as bus:
        objects = await _objects(bus)
        adapters = [path for path, interfaces in objects.items()
                    if normalize_address(_value(interfaces.get(ADAPTER, {}), "Address")) == adapter_address]
        if len(adapters) != 1:
            raise PairingError("bluetooth_no_adapter")
        adapter_path = adapters[0]
        matches = [path for path, interfaces in objects.items()
                   if (props := interfaces.get(DEVICE)) is not None
                   and _value(props, "Adapter") == adapter_path
                   and normalize_address(_value(props, "Address")) == address]
        if not matches:
            return  # Already forgotten on this adapter.
        if len(matches) != 1:
            raise PairingError("bluetooth_identity_missing")
        try:
            await _call(bus, adapter_path, ADAPTER, "RemoveDevice", "o", [matches[0]])
        except DBusError as exc:
            if exc.type != "org.bluez.Error.DoesNotExist":
                raise


class PairingError(Exception):
    """A translated configuration error."""

    def __init__(self, key: str) -> None:
        super().__init__(key)
        self.key = key


@dataclass(frozen=True)
class Remote:
    """A temporary discovery result; never stored in the config entry."""

    path: str
    address: str
    name: str

    @property
    def label(self) -> str:
        adapter = self.path.split("/")[-2]
        return f"{self.name} ({self.address}, {adapter})"


def _value(properties, key, default=None):
    value = properties.get(key)
    return value.value if value is not None else default


def _is_remote(properties) -> bool:
    name = _value(properties, "Name", "")
    return name == REMOTE_NAME or name.startswith(f"{REMOTE_NAME} ")


async def _call(bus, path, interface, member, signature="", body=None,
                timeout=CALL_TIMEOUT):
    async with asyncio.timeout(timeout):
        reply = await bus.call(Message(
            destination=BLUEZ, path=path, interface=interface,
            member=member, signature=signature, body=body or [],
        ))
    if reply is None:
        raise PairingError("bluetooth_unavailable")
    if reply.message_type == MessageType.ERROR:
        raise DBusError(reply.error_name, str(reply.body[0]) if reply.body else "")
    return reply.body


async def _objects(bus):
    return (await _call(bus, "/", "org.freedesktop.DBus.ObjectManager",
                        "GetManagedObjects"))[0]


@asynccontextmanager
async def _connection():
    bus = None
    try:
        bus = MessageBus(bus_type=BusType.SYSTEM)
        async with asyncio.timeout(CALL_TIMEOUT):
            await bus.connect()
        yield bus
    except TimeoutError as exc:
        raise PairingError("bluetooth_timeout") from exc
    except PermissionError as exc:
        raise PairingError("bluetooth_permission") from exc
    except DBusError as exc:
        if exc.type in ("org.freedesktop.DBus.Error.AccessDenied",
                        "org.bluez.Error.NotAuthorized"):
            key = "bluetooth_permission"
        elif exc.type.startswith("org.bluez.Error.Authentication"):
            key = "bluetooth_authentication"
        elif exc.type == "org.bluez.Error.NotReady":
            key = "bluetooth_adapter_off"
        elif exc.type in ("org.freedesktop.DBus.Error.ServiceUnknown",
                          "org.freedesktop.DBus.Error.NameHasNoOwner"):
            key = "bluetooth_unavailable"
        else:
            key = "bluetooth_failed"
        raise PairingError(key) from exc
    except (OSError, EOFError) as exc:
        raise PairingError("bluetooth_unavailable") from exc
    finally:
        if bus is not None:
            bus.disconnect()


async def async_discover_remotes() -> list[Remote]:
    """Scan powered local adapters, releasing only our discovery sessions."""
    async with _connection() as bus:
        objects = await _objects(bus)
        adapters = [path for path, interfaces in objects.items() if ADAPTER in interfaces]
        if not adapters:
            raise PairingError("bluetooth_no_adapter")
        powered = [path for path in adapters if _value(objects[path][ADAPTER], "Powered", False)]
        if not powered:
            raise PairingError("bluetooth_adapter_off")
        started = []
        try:
            for path in powered:
                await _call(bus, path, ADAPTER, "StartDiscovery")
                started.append(path)
            await asyncio.sleep(SCAN_SECONDS)
            objects = await _objects(bus)
            return sorted(
                [Remote(path, _value(props, "Address", ""),
                        _value(props, "Alias", REMOTE_NAME))
                 for path, interfaces in objects.items()
                 if (props := interfaces.get(DEVICE)) is not None
                 and _is_remote(props)
                 and _value(props, "Adapter") in powered],
                key=lambda remote: (remote.address, remote.path),
            )
        finally:
            for path in started:
                with suppress(DBusError, PairingError, OSError, TimeoutError):
                    await _call(bus, path, ADAPTER, "StopDiscovery", timeout=2)


class _PairingAgent(ServiceInterface):
    """Authorize only the selected remote; never become the default agent."""

    def __init__(self, device_path: str) -> None:
        super().__init__("org.bluez.Agent1")
        self.device_path = device_path
        self.requires_pin = False

    def _check(self, device):
        if device != self.device_path:
            raise DBusError("org.bluez.Error.Rejected", "Device not selected")

    def _reject_pin(self, device):
        self._check(device)
        self.requires_pin = True
        raise DBusError("org.bluez.Error.Rejected", "PIN pairing is not supported")

    @method()
    def Release(self):
        pass

    @method()
    def Cancel(self):
        pass

    @method()
    def RequestAuthorization(self, device: "o"):
        self._check(device)

    @method()
    def AuthorizeService(self, device: "o", uuid: "s"):
        self._check(device)
        if uuid.lower() not in HID_UUIDS:
            raise DBusError("org.bluez.Error.Rejected", "Not a HID service")

    @method()
    def RequestPinCode(self, device: "o") -> "s":
        self._reject_pin(device)

    @method()
    def RequestPasskey(self, device: "o") -> "u":
        self._reject_pin(device)

    @method()
    def DisplayPinCode(self, device: "o", pincode: "s"):
        self._reject_pin(device)

    @method()
    def DisplayPasskey(self, device: "o", passkey: "u", entered: "q"):
        self._reject_pin(device)

    @method()
    def RequestConfirmation(self, device: "o", passkey: "u"):
        self._reject_pin(device)


async def async_pair_remote(remote: Remote) -> dict[str, str] | None:
    """Pair, trust and connect a selected local remote, preserving existing bonds."""
    async with _connection() as bus:
        objects = await _objects(bus)
        props = objects.get(remote.path, {}).get(DEVICE, {})
        if not _is_remote(props) or _value(props, "Address") != remote.address:
            raise PairingError("bluetooth_device_gone")
        agent = _PairingAgent(remote.path)
        registered = False
        bus.export(AGENT_PATH, agent)
        try:
            if not _value(props, "Paired", False):
                await _call(bus, "/org/bluez", AGENT_MANAGER, "RegisterAgent",
                            "os", [AGENT_PATH, "NoInputNoOutput"])
                registered = True
                try:
                    await _call(bus, remote.path, DEVICE, "Pair", timeout=PAIR_TIMEOUT)
                except (TimeoutError, asyncio.CancelledError):
                    with suppress(DBusError, PairingError, OSError, TimeoutError):
                        await _call(bus, remote.path, DEVICE, "CancelPairing", timeout=2)
                    raise
                except DBusError as exc:
                    if agent.requires_pin:
                        raise PairingError("bluetooth_pin_required") from exc
                    if exc.type != "org.bluez.Error.AlreadyExists":
                        raise
            await _call(bus, remote.path, PROPERTIES, "Set", "ssv",
                        [DEVICE, "Trusted", Variant("b", True)])
            try:
                await _call(bus, remote.path, DEVICE, "Connect", timeout=20)
            except DBusError as exc:
                if exc.type != "org.bluez.Error.AlreadyConnected":
                    raise
            # Pairing can resolve a private address to its permanent identity.
            objects = await _objects(bus)
            return _pairing_identity(objects, objects.get(remote.path, {}).get(DEVICE, {}))
        finally:
            if registered:
                with suppress(DBusError, PairingError, OSError, TimeoutError):
                    await _call(bus, "/org/bluez", AGENT_MANAGER, "UnregisterAgent",
                                "o", [AGENT_PATH], timeout=2)
            bus.unexport(AGENT_PATH)
