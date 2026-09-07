"""Ask explicitly before removing a deleted remote's Bluetooth pairing."""

from __future__ import annotations

import asyncio
import logging

import voluptuous as vol

from homeassistant.components.repairs import RepairsFlow
from homeassistant.helpers import selector

from . import CONF_BLUETOOTH_DEVICE, DOMAIN
from .bluetooth_pairing import PairingError, async_unpair_remote, normalize_address

_LOGGER = logging.getLogger(__name__)
_ERROR_KEYS = {
    "bluetooth_identity_missing", "bluetooth_still_in_use", "bluetooth_no_adapter",
    "bluetooth_permission", "bluetooth_timeout", "bluetooth_unavailable",
    "bluetooth_adapter_off", "bluetooth_failed",
}


class UnpairRepairFlow(RepairsFlow):
    """Keep the bond unless the user chooses and submits 'delete'."""

    def __init__(self):
        self._task: asyncio.Task | None = None
        self._error: str | None = None
        self._confirmed = False

    async def async_step_init(self, user_input=None):
        return await self.async_step_confirm()

    async def async_step_confirm(self, user_input=None):
        if user_input is not None:
            if user_input.get("action") == "keep":
                return self.async_create_entry(data={})
            if user_input.get("action") == "delete":
                self._error = None
                self._confirmed = True
                return await self.async_step_unpair()
        data = self.data or {}
        return self.async_show_form(
            step_id="confirm",
            data_schema=vol.Schema({
                vol.Required("action", default="keep"): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=["keep", "delete"],
                        translation_key="unpair_action",
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    )
                ),
            }),
            errors={"base": self._error} if self._error else {},
            description_placeholders={
                "address": normalize_address(data.get("address")) or "—",
                "adapter": normalize_address(data.get("adapter_address")) or "—",
            },
        )

    async def _async_unpair(self):
        data = self.data or {}
        identity = {
            "address": normalize_address(data.get("address")),
            "adapter_address": normalize_address(data.get("adapter_address")),
        }
        if not all(identity.values()):
            raise PairingError("bluetooth_identity_missing")
        # Recheck at confirmation time: the remote may have been added again.
        if any(entry.data.get(CONF_BLUETOOTH_DEVICE) == identity
               or (data.get("device_name")
                   and entry.data.get("device_name") == data["device_name"])
               for entry in self.hass.config_entries.async_entries(DOMAIN)):
            raise PairingError("bluetooth_still_in_use")
        await async_unpair_remote(identity)

    async def async_step_unpair(self, user_input=None):
        if self._task is None:
            if not self._confirmed:
                return await self.async_step_confirm()
            self._task = self.hass.async_create_background_task(
                self._async_unpair(), f"{DOMAIN}_confirmed_unpair"
            )
        if not self._task.done():
            return self.async_show_progress(
                step_id="unpair", progress_action="unpair", progress_task=self._task
            )
        task, self._task = self._task, None
        self._confirmed = False
        try:
            task.result()
        except PairingError as exc:
            self._error = exc.key if exc.key in _ERROR_KEYS else "bluetooth_failed"
        except Exception:
            _LOGGER.exception("Confirmed Bluetooth unpairing failed")
            self._error = "bluetooth_failed"
        return self.async_show_progress_done(
            next_step_id="confirm" if self._error else "done"
        )

    async def async_step_done(self, user_input=None):
        return self.async_create_entry(data={})


async def async_create_fix_flow(hass, issue_id, data):
    """HA supplies persisted issue data after constructing the flow."""
    if not issue_id.startswith("unpair_"):
        raise ValueError(f"Unknown repair issue: {issue_id}")
    return UnpairRepairFlow()
