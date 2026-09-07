"""VU+ BLE remote raw HID integration."""
from __future__ import annotations

import asyncio
from contextlib import suppress
import logging
import time
from typing import Any, Callable

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)
DOMAIN = "vuplus_hid_raw"
INTEGRATION_VERSION = "1.0.2"
PLATFORMS = [Platform.EVENT, Platform.BINARY_SENSOR]
DEFAULT_DEVICE_NAME = "VUPLUS-BLE-RCU Keyboard"
DEFAULT_LONG_PRESS_MS = 500
RECONNECT_DELAY = 2
CONF_BLUETOOTH_DEVICE = "bluetooth_device"
DIAGNOSTIC_REFRESH_SECONDS = 30

KEY_COMMANDS = {
    28:"ok",103:"up",108:"down",105:"left",106:"right",115:"volume_up",114:"volume_down",
    402:"channel_up",403:"channel_down",139:"menu",378:"pvr",113:"mute",168:"rewind",
    208:"forward",207:"play",119:"pause",167:"record",166:"stop",217:"radio",138:"help",
    116:"stb_power",398:"red",399:"green",400:"yellow",401:"blue",2:"1",3:"2",4:"3",5:"4",
    6:"5",7:"6",8:"7",9:"8",10:"9",11:"0",
}
USAGE_COMMANDS = {0x16B:"epg",0x07:"audio",0x0A:"teletext",0x0B:"subtitle",0x04:"speak",0x16D:"tv",0x16C:"exit",0x08:"left_0",0x09:"right_0"}
COMMAND_LABELS = {
    "ok": "OK",
    "up": "Up",
    "down": "Down",
    "left": "Left",
    "right": "Right",
    "volume_up": "Volume +",
    "volume_down": "Volume -",
    "channel_up": "Channel +",
    "channel_down": "Channel -",
    "menu": "Menu",
    "pvr": "PVR",
    "mute": "Mute",
    "rewind": "Rewind",
    "forward": "Fast forward",
    "play": "Play",
    "pause": "Pause",
    "record": "Record",
    "stop": "Stop",
    "radio": "Radio",
    "help": "Help",
    "stb_power": "STB Power",
    "red": "Red",
    "green": "Green",
    "yellow": "Yellow",
    "blue": "Blue",
    "0": "0",
    "1": "1",
    "2": "2",
    "3": "3",
    "4": "4",
    "5": "5",
    "6": "6",
    "7": "7",
    "8": "8",
    "9": "9",
    "epg": "EPG",
    "audio": "Audio",
    "teletext": "Teletext",
    "subtitle": "Subtitles",
    "speak": "Speak",
    "tv": "TV",
    "exit": "Exit",
    "left_0": "Left of 0",
    "right_0": "Right of 0"
}
async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up a configured VU+ remote."""
    hass.data.setdefault(DOMAIN, {})
    try:
        from evdev import InputDevice, list_devices
    except ImportError:
        _LOGGER.error("python-evdev is not available")
        return False

    device_name = entry.data.get("device_name", DEFAULT_DEVICE_NAME)
    if CONF_BLUETOOTH_DEVICE not in entry.data:
        identity = await _async_get_bluetooth_device(hass, device_name)
        if identity:
            hass.config_entries.async_update_entry(
                entry, data={**entry.data, CONF_BLUETOOTH_DEVICE: identity}
            )
    long_press_ms = int(entry.options.get("long_press_ms", entry.data.get("long_press_ms", DEFAULT_LONG_PRESS_MS)))

    state = {
        "entry": entry, "device_name": device_name, "long_press_ms": long_press_ms,
        "callbacks": [], "diagnostic_callbacks": [], "stop": asyncio.Event(),
        "task": None, "diagnostic_task": None,
        "diagnostics": {
            "paired": None, "connected": None, "trusted": None,
            "input_device": False, "reader_active": False,
        },
        "bluetooth_identity": entry.data.get(CONF_BLUETOOTH_DEVICE),
        "InputDevice": InputDevice, "list_devices": list_devices,
    }
    hass.data[DOMAIN][entry.entry_id] = state
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    state["task"] = hass.async_create_background_task(
        _reader_supervisor(hass, state), f"{DOMAIN}_{entry.entry_id}"
    )
    state["diagnostic_task"] = hass.async_create_background_task(
        _diagnostic_supervisor(hass, state), f"{DOMAIN}_{entry.entry_id}_diagnostics"
    )
    return True


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload the reader after an options update."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a configured remote."""
    state = hass.data.get(DOMAIN, {}).pop(entry.entry_id, None)
    if not state:
        return True
    state["stop"].set()
    for task_name in ("task", "diagnostic_task"):
        if task := state.get(task_name):
            task.cancel()
            with suppress(asyncio.CancelledError):
                await task
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


def _read_bluetooth_addresses(device_name, list_devices, InputDevice):
    """Read optional cleanup metadata; never use it for reader discovery."""
    from .bluetooth_pairing import normalize_address

    candidates = set()
    for path in list_devices():
        try:
            device = InputDevice(path)
            try:
                if device.name != device_name:
                    continue
                address = normalize_address(device.uniq)
                if not address:
                    return None
                try:
                    adapter = normalize_address((device.phys or "").split("/")[0])
                except (OSError, AttributeError):
                    adapter = None
                candidates.add((address, adapter))
            finally:
                device.close()
        except (OSError, AttributeError):
            # A matching interface with unreadable identity is not safe to infer.
            return None
    return next(iter(candidates)) if len(candidates) == 1 else None


async def _async_get_bluetooth_device(hass, device_name):
    """Best-effort mapping for configuration entries without a Bluetooth identity."""
    from .bluetooth_pairing import async_resolve_pairing

    try:
        from evdev import InputDevice, list_devices
        addresses = await hass.async_add_executor_job(
            _read_bluetooth_addresses, device_name, list_devices, InputDevice
        )
        if addresses:
            return await async_resolve_pairing(*addresses)
    except Exception:
        _LOGGER.debug("Could not identify the Bluetooth pairing for %s", device_name, exc_info=True)
    return None


async def async_remove_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Offer a persistent choice; deletion itself never removes a Bluetooth bond."""
    from homeassistant.helpers import issue_registry as ir
    from .bluetooth_pairing import normalize_address

    identity = entry.data.get(CONF_BLUETOOTH_DEVICE)
    if not identity:
        identity = await _async_get_bluetooth_device(
            hass, entry.data.get("device_name", DEFAULT_DEVICE_NAME)
        )
    identity = identity if isinstance(identity, dict) else {}
    ir.async_create_issue(
        hass, DOMAIN, f"unpair_{entry.entry_id}",
        is_fixable=True,
        is_persistent=True,
        severity=ir.IssueSeverity.WARNING,
        translation_key="confirm_unpair",
        data={
            "address": normalize_address(identity.get("address")),
            "adapter_address": normalize_address(identity.get("adapter_address")),
            "device_name": entry.data.get("device_name", DEFAULT_DEVICE_NAME),
        },
    )


def _find_device(device_name: str, list_devices, InputDevice):
    for path in list_devices():
        try:
            device = InputDevice(path)
            try:
                if device.name == device_name:
                    return path
            finally:
                device.close()
        except OSError:
            continue
    return None


def _set_diagnostics(state: dict[str, Any], **changes: bool | None) -> None:
    """Store changed diagnostic values and notify their entities."""
    diagnostics = state["diagnostics"]
    if not any(diagnostics.get(key) != value for key, value in changes.items()):
        return
    diagnostics.update(changes)
    for callback in tuple(state["diagnostic_callbacks"]):
        callback()


def _register_diagnostic_callback(state, callback: Callable[[], None]) -> Callable[[], None]:
    """Register a diagnostic entity state listener."""
    state["diagnostic_callbacks"].append(callback)

    def remove() -> None:
        if callback in state["diagnostic_callbacks"]:
            state["diagnostic_callbacks"].remove(callback)

    return remove


async def _diagnostic_supervisor(hass: HomeAssistant, state: dict[str, Any]) -> None:
    """Refresh BlueZ state without blocking the Home Assistant event loop."""
    from .bluetooth_pairing import PairingError, async_get_remote_status

    while not state["stop"].is_set():
        identity = state.get("bluetooth_identity")
        try:
            status = await async_get_remote_status(identity) if identity else None
        except PairingError:
            _LOGGER.debug("Could not refresh VU+ Bluetooth diagnostics", exc_info=True)
            status = None
        if status is None:
            _set_diagnostics(state, paired=None, connected=None, trusted=None)
        else:
            _set_diagnostics(state, **status)
        try:
            await asyncio.wait_for(state["stop"].wait(), DIAGNOSTIC_REFRESH_SECONDS)
        except TimeoutError:
            pass

def _command_for_key(key_code: int, usage: int | None) -> str | None:
    if key_code == 240 and usage is not None:
        return USAGE_COMMANDS.get(usage)
    return KEY_COMMANDS.get(key_code)

def _publish_event(state: dict[str, Any], *, command: str, action: str,
                   key_code: int, scan_code: int | None, usage: int | None, duration_ms: int | None) -> None:
    """Publish a remote event to the event entity callback."""
    data = {
        "command": command, "command_label": COMMAND_LABELS.get(command, command),
        "action": action,
        "key_code": key_code,
        "value": 2 if action == "repeat" else 0 if action in ("short_release", "long_release") else 1,
        "scan_code": scan_code, "usage": usage, "duration_ms": duration_ms,
    }
    for callback in tuple(state["callbacks"]):
        callback(data)

def _register_callback(state, callback: Callable[[dict[str, Any]], None]) -> Callable[[], None]:
    state["callbacks"].append(callback)
    def remove():
        if callback in state["callbacks"]:
            state["callbacks"].remove(callback)
    return remove

async def _reader_supervisor(hass: HomeAssistant, state: dict[str, Any]) -> None:
    """Keep the evdev reader alive and reconnect after Bluetooth loss."""
    pressed: dict[str, dict[str, Any]] = {}
    pending_scan = None

    def _cancel_long_press_timer(press: dict[str, Any]) -> None:
        """Cancel the timer associated with a pressed key."""
        task = press.get("long_press_task")
        if task is not None and not task.done():
            task.cancel()

    def _clear_pressed() -> None:
        """Cancel every active long-press timer and forget pressed keys."""
        for press in pressed.values():
            _cancel_long_press_timer(press)
        pressed.clear()

    def _active_command_for_key_code(key_code: int) -> str | None:
        """Resolve a scan-less repeat or release for one active key only."""
        matches = [
            command
            for command, press in pressed.items()
            if press["key_code"] == key_code
        ]
        return matches[0] if len(matches) == 1 else None

    async def _async_fire_long_press(
        command: str, press: dict[str, Any]
    ) -> None:
        """Fire long press at the configured threshold without evdev repeats."""
        try:
            await asyncio.sleep(state["long_press_ms"] / 1000)
        except asyncio.CancelledError:
            return

        if (
            state["stop"].is_set()
            or pressed.get(command) is not press
            or press["long_sent"]
        ):
            return

        press["long_sent"] = True
        _publish_event(
            state,
            command=command,
            action="long_press",
            key_code=press["key_code"],
            scan_code=press["scan_code"],
            usage=press["usage"],
            duration_ms=int((time.monotonic() - press["started"]) * 1000),
        )

    while not state["stop"].is_set():
        device = None
        pending_scan = None
        try:
            path = await hass.async_add_executor_job(_find_device, state["device_name"], state["list_devices"], state["InputDevice"])
            _set_diagnostics(state, input_device=bool(path))
            if not path:
                await asyncio.sleep(RECONNECT_DELAY)
                continue
            device = await hass.async_add_executor_job(state["InputDevice"], path)
            _set_diagnostics(state, reader_active=True)
            _LOGGER.info("VU+ raw HID connected to %s", path)
            async for event in device.async_read_loop():
                if state["stop"].is_set(): break
                if event.type == 4 and event.code == 4:  # EV_MSC / MSC_SCAN
                    pending_scan = int(event.value)
                    continue
                if event.type != 1:  # EV_KEY
                    continue
                key_code, value = int(event.code), int(event.value)
                scan_code = pending_scan
                pending_scan = None
                usage = (scan_code & 0xFFFF) if scan_code is not None else None
                command = _command_for_key(key_code, usage)
                if command is None and value in (0, 2):
                    command = _active_command_for_key_code(key_code)
                if command is None:
                    continue
                now = time.monotonic()
                if value == 1:
                    if previous_press := pressed.pop(command, None):
                        _cancel_long_press_timer(previous_press)
                    press = {
                        "started": now,
                        "key_code": key_code,
                        "scan_code": scan_code,
                        "usage": usage,
                        "long_sent": False,
                    }
                    pressed[command] = press
                    press["long_press_task"] = hass.async_create_background_task(
                        _async_fire_long_press(command, press),
                        f"{DOMAIN}_{state['entry'].entry_id}_{command}_long_press",
                    )
                    _publish_event(state,command=command,action="press",key_code=key_code,scan_code=scan_code,usage=usage,duration_ms=0)
                elif value == 2:
                    p=pressed.get(command)
                    if not p: continue
                    duration_ms=int((now-p["started"])*1000)
                    _publish_event(state,command=command,action="repeat",key_code=p["key_code"],scan_code=p["scan_code"],usage=p["usage"],duration_ms=duration_ms)
                elif value == 0:
                    p=pressed.pop(command,None)
                    if not p: continue
                    duration_ms=int((now-p["started"])*1000)
                    _cancel_long_press_timer(p)
                    if not p["long_sent"] and duration_ms >= state["long_press_ms"]:
                        p["long_sent"] = True
                        _publish_event(state,command=command,action="long_press",key_code=p["key_code"],scan_code=p["scan_code"],usage=p["usage"],duration_ms=duration_ms)
                    action="long_release" if duration_ms >= state["long_press_ms"] else "short_release"
                    _publish_event(state,command=command,action=action,key_code=p["key_code"],scan_code=p["scan_code"],usage=p["usage"],duration_ms=duration_ms)
        except asyncio.CancelledError:
            raise
        except OSError as err:
            _LOGGER.info("VU+ HID disconnected: %s", err)
            _clear_pressed()
        except Exception:
            _LOGGER.exception("Unexpected VU+ HID reader error")
            _clear_pressed()
        finally:
            _clear_pressed()
            _set_diagnostics(state, reader_active=False)
            if device is not None:
                with suppress(OSError):
                    await hass.async_add_executor_job(device.close)
        if not state["stop"].is_set():
            await asyncio.sleep(RECONNECT_DELAY)
