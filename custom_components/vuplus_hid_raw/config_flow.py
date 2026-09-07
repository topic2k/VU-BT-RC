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

_LOGGER = logging.getLogger(__name__)


def _list_evdev_device_names(list_devices, InputDevice) -> list[dict[str, str]]:
    """Return unique evdev device names with their current event path as label."""
    devices: list[tuple[str, str]] = []
    seen: set[str] = set()
    for path in list_devices():
        try:
            device = InputDevice(path)
            try:
                name = (device.name or "").strip()
                if name and name not in seen:
                    seen.add(name)
                    devices.append((name, path))
            finally:
                device.close()
        except OSError:
            continue

    devices.sort(key=lambda item: (item[0].lower(), item[1]))
    return [
        {"value": name, "label": f"{name} ({path})"}
        for name, path in devices
    ]


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    def __init__(self):
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
        self._remotes = {remote.path: remote for remote in remotes or []}
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
                _find_device, DEFAULT_DEVICE_NAME, list_devices, InputDevice
            ):
                return
            await asyncio.sleep(1)

    async def async_step_device_missing(self, user_input=None):
        """Allow refreshing even when an empty dropdown cannot be submitted."""
        return await self.async_step_device()

    async def async_step_device(self, user_input: dict[str, Any] | None = None):
        errors = {}

        try:
            from evdev import InputDevice, list_devices
            device_options = await self.hass.async_add_executor_job(
                _list_evdev_device_names, list_devices, InputDevice
            )
        except ImportError:
            device_options = []
            errors["base"] = "evdev_missing"
        except Exception:
            device_options = []
            errors["base"] = "unknown"

        if user_input is not None:
            try:
                from evdev import InputDevice, list_devices
                path = await self.hass.async_add_executor_job(
                    _find_device,
                    user_input["device_name"],
                    list_devices,
                    InputDevice,
                )
            except ImportError:
                errors["base"] = "evdev_missing"
            except Exception:
                errors["base"] = "unknown"
            else:
                if not path:
                    errors["base"] = "device_not_found"
                else:
                    await self.async_set_unique_id(
                        f"name:{user_input['device_name']}"
                    )
                    self._abort_if_unique_id_configured()
                    data = dict(user_input)
                    identity = await _async_get_bluetooth_device(
                        self.hass, user_input["device_name"]
                    )
                    if (identity is None and self._paired_identity
                            and user_input["device_name"] == DEFAULT_DEVICE_NAME):
                        # The user explicitly selected this remote in our pairing wizard.
                        identity = self._paired_identity
                    if identity:
                        data[CONF_BLUETOOTH_DEVICE] = identity
                    return self.async_create_entry(
                        title="VU+ Bluetooth Fernbedienung", data=data
                    )

        if not device_options:
            return self.async_show_form(
                step_id="device_missing", data_schema=vol.Schema({}),
                errors=errors or {"base": "device_not_found"},
            )

        schema = vol.Schema(
            {
                vol.Required(
                    "device_name", default=(
                        DEFAULT_DEVICE_NAME
                        if any(option["value"] == DEFAULT_DEVICE_NAME for option in device_options)
                        else device_options[0]["value"] if device_options else DEFAULT_DEVICE_NAME
                    )
                ): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=device_options,
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    )
                ),
                vol.Required(
                    "long_press_ms", default=DEFAULT_LONG_PRESS_MS
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=100,
                        max=5000,
                        step=50,
                        mode=selector.NumberSelectorMode.BOX,
                    )
                ),
            }
        )
        return self.async_show_form(step_id="device", data_schema=schema, errors=errors)

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
