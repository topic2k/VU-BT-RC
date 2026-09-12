"""Diagnostic entities for the VU+ Bluetooth remote."""
from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorDeviceClass, BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import DeviceInfo

from . import DOMAIN, INTEGRATION_VERSION, _device_translation, _register_diagnostic_callback

DIAGNOSTICS = ("paired", "connected", "trusted", "input_device", "reader_active")


class VuplusRemoteDiagnostic(BinarySensorEntity):
    """Represent one live diagnostic condition of the remote."""

    _attr_has_entity_name = True
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY

    def __init__(self, state, key: str) -> None:
        self._state = state
        self._key = key
        self._remove = None
        self._attr_unique_id = f"{state['entry'].entry_id}_{key}_diagnostic"
        self._attr_translation_key = key
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, state["entry"].unique_id or state["entry"].entry_id)},
            **_device_translation(state),
            manufacturer="VU+",
            model="VUPLUS-BLE-RCU",
            model_id="VUPLUS-BLE-RCU",
            sw_version=f"Integration {INTEGRATION_VERSION}",
        )

    @property
    def available(self) -> bool:
        """BlueZ values require both a known pairing and BlueZ access."""
        return self._key not in {"paired", "connected", "trusted"} or self.is_on is not None

    @property
    def is_on(self) -> bool | None:
        return self._state["diagnostics"][self._key]

    async def async_added_to_hass(self) -> None:
        self._remove = _register_diagnostic_callback(self._state, self._handle_update)

    async def async_will_remove_from_hass(self) -> None:
        if self._remove:
            self._remove()

    @callback
    def _handle_update(self) -> None:
        self.async_write_ha_state()


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities) -> None:
    """Set up remote diagnostic binary sensors."""
    state = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(VuplusRemoteDiagnostic(state, key) for key in DIAGNOSTICS)
