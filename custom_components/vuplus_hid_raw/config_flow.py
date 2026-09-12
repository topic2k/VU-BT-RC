"""Config flow for the VU+ HID Raw Remote."""
from __future__ import annotations

import asyncio
import logging
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import selector

from . import (
    DOMAIN, DEFAULT_DEVICE_NAME, DEFAULT_LONG_PRESS_MS, CONF_BLUETOOTH_DEVICE,
    _async_get_bluetooth_device, _find_device,
)
from .bluetooth_pairing import (
    PairingError, Remote, async_discover_remotes, async_pair_remote,
)

from .input_device import (
    CONF_DEVICE_ADDRESS, entry_address, list_input_choices, normalize_address,
)

_LOGGER = logging.getLogger(__name__)


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    def __init__(self):
        self._reconfigure_entry = None
        self._bluetooth_task: asyncio.Task | None = None
        self._remotes: dict[str, Remote] = {}
        self._selected_remote: Remote | None = None
        self._bluetooth_error: str | None = None
        self._paired_identity: dict[str, str] | None = None

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        return self.async_show_menu(
            step_id="user", menu_options=["device", "bluetooth"]
        )

    async def async_step_bluetooth(self, user_input=None):
        """Explain the pairing action before starting local discovery."""
        if user_input is not None:
            self._bluetooth_error = None
            self._paired_identity = None
            return await self.async_step_scan()
        return self.async_show_form(
            step_id="bluetooth", data_schema=vol.Schema({}),
            errors={"base": self._bluetooth_error} if self._bluetooth_error else {},
        )

    async def async_step_scan(self, user_input=None):
        if self._bluetooth_task is None:
            self._bluetooth_task = self.hass.async_create_background_task(
                async_discover_remotes(), f"{DOMAIN}_scan"
            )
        if not self._bluetooth_task.done():
            return self.async_show_progress(
                step_id="scan", progress_action="scan",
                progress_task=self._bluetooth_task,
            )
        remotes = self._bluetooth_result()
        configured_addresses = {
            entry_address(entry) for entry in self._async_current_entries()
        }
        self._remotes = {
            remote.path: remote for remote in remotes or []
            if normalize_address(remote.address) not in configured_addresses
        }
        if not self._remotes and not self._bluetooth_error:
            self._bluetooth_error = "bluetooth_no_devices"
        return self.async_show_progress_done(
            next_step_id="bluetooth" if self._bluetooth_error else "select_remote"
        )

    def _bluetooth_result(self):
        """Consume the task result so the form can offer a retry."""
        task, self._bluetooth_task = self._bluetooth_task, None
        assert task is not None
        try:
            return task.result()
        except PairingError as exc:
            self._bluetooth_error = exc.key
            _LOGGER.debug("Bluetooth setup failed: %s", exc.key, exc_info=True)
        except Exception:
            _LOGGER.exception("Bluetooth setup failed")
            self._bluetooth_error = "bluetooth_failed"
        return None

    async def async_step_select_remote(self, user_input=None):
        errors = {}
        if user_input is not None:
            self._selected_remote = self._remotes.get(user_input["remote"])
            if self._selected_remote is not None:
                return await self.async_step_pair()
            errors["base"] = "bluetooth_device_gone"
        return self.async_show_form(
            step_id="select_remote", errors=errors,
            data_schema=vol.Schema({
                vol.Required("remote"): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=[{"value": remote.path, "label": remote.label}
                                 for remote in self._remotes.values()],
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    )
                ),
            }),
        )

    async def async_step_pair(self, user_input=None):
        if self._bluetooth_task is None:
            self._bluetooth_task = self.hass.async_create_background_task(
                self._async_pair_and_wait(), f"{DOMAIN}_pair"
            )
        if not self._bluetooth_task.done():
            return self.async_show_progress(
                step_id="pair", progress_action="pair",
                progress_task=self._bluetooth_task,
            )
        self._bluetooth_result()
        return self.async_show_progress_done(
            next_step_id="bluetooth" if self._bluetooth_error else "device"
        )

    async def _async_pair_and_wait(self):
        assert self._selected_remote is not None
        self._paired_identity = await async_pair_remote(self._selected_remote)
        # Linux may need a moment to publish the HID input device after pairing.
        try:
            from evdev import InputDevice, list_devices
        except ImportError as exc:
            raise PairingError("evdev_missing") from exc
        for _ in range(10):
            if await self.hass.async_add_executor_job(
                _find_device, DEFAULT_DEVICE_NAME, list_devices, InputDevice,
                self._selected_remote.address,
            ):
                return
            await asyncio.sleep(1)

    async def async_step_reconfigure(self, user_input=None):
        """Bind a legacy entry without replacing its registry or entity IDs."""
        self._reconfigure_entry = self._get_reconfigure_entry()
        return await self.async_step_device(user_input)

    async def async_step_device_missing(self, user_input=None):
        """Allow refreshing even when an empty dropdown cannot be submitted."""
        return await self.async_step_device()

    async def async_step_device(self, user_input: dict[str, Any] | None = None):
        errors = {}
        choices = []
        entry = self._reconfigure_entry
        try:
            from evdev import InputDevice, list_devices
            choices = await self.hass.async_add_executor_job(
                list_input_choices, list_devices, InputDevice
            )
            if self._paired_identity:
                choices = [choice for choice in choices
                           if choice.address == self._paired_identity["address"]]
            if entry:
                choices = [choice for choice in choices
                           if choice.name == entry.data["device_name"]
                           and (not entry_address(entry)
                                or choice.address == entry_address(entry))]
        except ImportError:
            errors["base"] = "evdev_missing"
        except Exception:
            errors["base"] = "unknown"

        if user_input is not None and not errors:
            choice = next((choice for choice in choices
                           if choice.value == user_input["device_name"]), None)
            if choice is None:
                errors["base"] = "device_not_found"
            else:
                try:
                    path = await self.hass.async_add_executor_job(
                        _find_device, choice.name, list_devices, InputDevice,
                        choice.address,
                    )
                except OSError:
                    path = None
                if not path:
                    errors["base"] = "device_not_found"
                else:
                    return await self._async_save_device(choice, user_input, entry)

        if not choices:
            return self.async_show_form(
                step_id="device_missing", data_schema=vol.Schema({}),
                errors=errors or {"base": "device_not_found"},
            )

        default = next((choice.value for choice in choices
                        if choice.name == DEFAULT_DEVICE_NAME), choices[0].value)
        threshold = (entry.options.get("long_press_ms", entry.data.get(
            "long_press_ms", DEFAULT_LONG_PRESS_MS)) if entry else DEFAULT_LONG_PRESS_MS)
        schema = vol.Schema({
            vol.Required("device_name", default=default): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=[choice.option for choice in choices],
                    mode=selector.SelectSelectorMode.DROPDOWN,
                )
            ),
            vol.Required("long_press_ms", default=threshold): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=100, max=5000, step=50, mode=selector.NumberSelectorMode.BOX,
                )
            ),
        })
        return self.async_show_form(
            step_id="reconfigure" if entry else "device",
            data_schema=schema, errors=errors,
        )

    async def _async_save_device(self, choice, user_input, entry):
        """Prevent both new duplicates and collisions with legacy name entries."""
        for configured in self._async_current_entries():
            if entry and configured.entry_id == entry.entry_id:
                continue
            if configured.data.get("device_name") != choice.name:
                continue
            address = entry_address(configured)
            if not address:
                return self.async_abort(reason="legacy_entry_needs_address")
            if not choice.address or address == choice.address:
                return self.async_abort(reason="already_configured")

        unique_id = (f"bluetooth:{choice.address}:{choice.name}" if choice.address
                     else f"name:{choice.name}")
        if entry is None:
            await self.async_set_unique_id(unique_id)
            self._abort_if_unique_id_configured()
        data = {"device_name": choice.name, "long_press_ms": user_input["long_press_ms"]}
        if choice.address:
            data[CONF_DEVICE_ADDRESS] = choice.address
        identity = await _async_get_bluetooth_device(self.hass, choice.name, choice.address)
        if identity is None and self._paired_identity:
            identity = self._paired_identity
        if identity:
            data[CONF_BLUETOOTH_DEVICE] = identity
        if entry:
            # Keep the original unique ID so HA keeps its device and entity registry.
            update = (self.async_update_and_abort if entry.update_listeners
                      else self.async_update_reload_and_abort)
            return update(
                entry, data_updates=data,
                options={**entry.options, "long_press_ms": user_input["long_press_ms"]},
            )
        return self.async_create_entry(
            title=f"VUPLUS-BLE-RCU ({choice.address})" if choice.address else "VUPLUS-BLE-RCU",
            data=data,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return OptionsFlow()


class OptionsFlow(config_entries.OptionsFlow):
    async def async_step_init(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        "long_press_ms",
                        default=self.config_entry.options.get(
                            "long_press_ms",
                            self.config_entry.data.get(
                                "long_press_ms", DEFAULT_LONG_PRESS_MS
                            ),
                        ),
                    ): selector.NumberSelector(
                        selector.NumberSelectorConfig(
                            min=100,
                            max=5000,
                            step=50,
                            mode=selector.NumberSelectorMode.BOX,
                        )
                    ),
                }
            ),
        )
