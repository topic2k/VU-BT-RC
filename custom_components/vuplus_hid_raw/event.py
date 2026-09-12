"""Event entities for VU+ remote buttons."""
from __future__ import annotations

from homeassistant.components.event import (
    ButtonEventType,
    EventDeviceClass,
    EventEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.entity import DeviceInfo

from . import COMMAND_LABELS, DOMAIN, INTEGRATION_VERSION, _device_translation, _register_callback

EVENT_TYPE_BY_ACTION = {
    "press": ButtonEventType.PRESS_START,
    "short_release": ButtonEventType.PRESS_END,
    "long_press": ButtonEventType.LONG_PRESS_START,
    "long_release": ButtonEventType.LONG_PRESS_END,
    "repeat": "repeat",
}


class VuplusRemoteButtonEvent(EventEntity):
    """Represent the events emitted by one physical remote button."""

    _attr_has_entity_name = True
    _attr_device_class = EventDeviceClass.BUTTON
    _attr_event_types = [
        ButtonEventType.PRESS_START,
        ButtonEventType.PRESS_END,
        ButtonEventType.LONG_PRESS_START,
        ButtonEventType.LONG_PRESS_END,
        "repeat",
    ]
    _attr_icon = "mdi:remote"

    def __init__(self, state, command: str) -> None:
        """Initialize a button event entity."""
        self._state = state
        self._command = command
        self._attr_unique_id = f"{state['entry'].entry_id}_{command}_button_events"
        self._attr_translation_key = command
        self._attr_device_info = DeviceInfo(
            identifiers={
                (DOMAIN, state["entry"].unique_id or state["entry"].entry_id)
            },
            **_device_translation(state),
            manufacturer="VU+",
            model="VUPLUS-BLE-RCU",
            model_id="VUPLUS-BLE-RCU",
            sw_version=f"Integration {INTEGRATION_VERSION}",
        )
        self._remove = None

    async def async_added_to_hass(self) -> None:
        """Register the remote event callback."""
        self._remove = _register_callback(self._state, self._handle)

    async def async_will_remove_from_hass(self) -> None:
        """Unregister the remote event callback."""
        if self._remove:
            self._remove()

    @callback
    def _handle(self, data) -> None:
        """Handle an event for this button."""
        if data["command"] != self._command:
            return

        if event_type := EVENT_TYPE_BY_ACTION.get(data["action"]):
            event_data = {
                **data,
                "command_label": self.name or data.get("command_label", self._command),
            }
            self._trigger_event(event_type, event_data)
            self.async_write_ha_state()


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities
) -> None:
    """Set up one event entity for every supported remote button."""
    entity_registry = er.async_get(hass)
    old_entity_id = entity_registry.async_get_entity_id(
        "event", DOMAIN, f"{entry.entry_id}_button_events"
    )
    if old_entity_id is not None:
        entity_registry.async_remove(old_entity_id)

    state = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        VuplusRemoteButtonEvent(state, command) for command in COMMAND_LABELS
    )
