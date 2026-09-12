"""Stable evdev identity and blocking discovery helpers (executor only)."""

from collections import Counter
from contextlib import suppress
from dataclasses import dataclass
import json
import re

CONF_DEVICE_ADDRESS = "device_address"


def normalize_address(value) -> str | None:
    """Accept only a complete Bluetooth address, never a name or event path."""
    if isinstance(value, str) and re.fullmatch(
        r"[0-9a-fA-F]{2}(?::[0-9a-fA-F]{2}){5}", value
    ):
        return value.upper()
    return None


def entry_address(entry) -> str | None:
    """Use explicit reader identity, falling back to legacy pairing metadata."""
    return normalize_address(entry.data.get(CONF_DEVICE_ADDRESS)) or normalize_address(
        (entry.data.get("bluetooth_device") or {}).get("address")
    )


def device_address(device) -> str | None:
    """Linux Bluetooth HID exposes the remote address in uniq, not phys."""
    with suppress(OSError, AttributeError):
        return normalize_address(device.uniq)
    return None


@dataclass(frozen=True)
class InputChoice:
    name: str
    address: str | None
    path: str

    @property
    def value(self) -> str:
        return json.dumps([self.name, self.address]) if self.address else self.name

    @property
    def option(self) -> dict[str, str]:
        identity = f"{self.address}, " if self.address else ""
        return {"value": self.value, "label": f"{self.name} ({identity}{self.path})"}


def list_input_choices(list_devices, InputDevice) -> list[InputChoice]:
    """List distinct interfaces; omit identities which cannot be selected safely."""
    choices = []
    for path in list_devices():
        try:
            device = InputDevice(path)
            try:
                if name := device.name:
                    choices.append(InputChoice(name, device_address(device), path))
            finally:
                device.close()
        except OSError:
            continue
    names = Counter(choice.name for choice in choices)
    identities = Counter((choice.name, choice.address) for choice in choices)
    return sorted(
        (choice for choice in choices
         if identities[choice.name, choice.address] == 1
         and (choice.address or names[choice.name] == 1)),
        key=lambda choice: (choice.name.lower(), choice.address or "", choice.path),
    )


def open_input_device(device_name, list_devices, InputDevice, address=None):
    """Return the verified open handle only when exactly one interface matches."""
    if address is not None:
        address = normalize_address(address)
        if address is None:
            return None
    selected = None
    try:
        for path in list_devices():
            try:
                device = InputDevice(path)
            except OSError:
                continue
            try:
                if device.name != device_name:
                    continue
                if address is not None and device_address(device) != address:
                    continue
                if selected is not None:
                    return None
                selected, device = device, None
            finally:
                if device is not None:
                    device.close()
        result, selected = selected, None
        return result
    finally:
        if selected is not None:
            selected.close()
