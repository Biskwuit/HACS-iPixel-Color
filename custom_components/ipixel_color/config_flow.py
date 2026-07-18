"""Config flow for iPixel Color."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from bleak import BleakScanner

from homeassistant import config_entries
from homeassistant.components import bluetooth
from homeassistant.const import CONF_ADDRESS, CONF_NAME
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult

from .const import DEFAULT_NAME, DOMAIN

_LOGGER = logging.getLogger(__name__)


class IPixelColorConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle an iPixel Color config flow."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize flow."""
        self._discovered: dict[str, str] = {}

    async def async_step_bluetooth(
        self,
        discovery_info: bluetooth.BluetoothServiceInfoBleak,
    ) -> FlowResult:
        """Handle Bluetooth discovery."""
        address = discovery_info.address
        name = discovery_info.name or DEFAULT_NAME

        await self.async_set_unique_id(address)
        self._abort_if_unique_id_configured()

        self.context["title_placeholders"] = {"name": name}

        return await self.async_step_bluetooth_confirm(
            {
                CONF_ADDRESS: address,
                CONF_NAME: name,
            }
        )

    async def async_step_bluetooth_confirm(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> FlowResult:
        """Confirm Bluetooth discovery."""
        if user_input is not None:
            address = user_input[CONF_ADDRESS]
            name = user_input.get(CONF_NAME, DEFAULT_NAME)

            await self.async_set_unique_id(address)
            self._abort_if_unique_id_configured()

            return self.async_create_entry(
                title=name,
                data={
                    CONF_ADDRESS: address,
                    CONF_NAME: name,
                },
            )

        return self.async_show_form(
            step_id="bluetooth_confirm",
            data_schema=vol.Schema({}),
            description_placeholders={
                "name": self.context.get("title_placeholders", {}).get("name", DEFAULT_NAME)
            },
        )

    async def async_step_user(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> FlowResult:
        """Manual setup."""
        errors: dict[str, str] = {}

        if user_input is not None:
            address = user_input[CONF_ADDRESS]
            name = user_input.get(CONF_NAME, DEFAULT_NAME)

            await self.async_set_unique_id(address)
            self._abort_if_unique_id_configured()

            return self.async_create_entry(
                title=name,
                data={
                    CONF_ADDRESS: address,
                    CONF_NAME: name,
                },
            )

        discovered = await self._async_discover_ipixel_devices()

        if discovered:
            self._discovered = discovered
            return await self.async_step_pick_device()

        schema = vol.Schema(
            {
                vol.Required(CONF_ADDRESS): str,
                vol.Optional(CONF_NAME, default=DEFAULT_NAME): str,
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors,
            description_placeholders={
                "hint": "No iPixel device was auto-discovered. Enter the BLE MAC/address manually."
            },
        )

    async def async_step_pick_device(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> FlowResult:
        """Pick from manually scanned devices."""
        if user_input is not None:
            address = user_input[CONF_ADDRESS]
            name = self._discovered.get(address, DEFAULT_NAME)

            await self.async_set_unique_id(address)
            self._abort_if_unique_id_configured()

            return self.async_create_entry(
                title=name,
                data={
                    CONF_ADDRESS: address,
                    CONF_NAME: name,
                },
            )

        return self.async_show_form(
            step_id="pick_device",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_ADDRESS): vol.In(self._discovered),
                }
            ),
        )

    async def _async_discover_ipixel_devices(self) -> dict[str, str]:
        """Actively scan for likely iPixel devices."""
        devices: dict[str, str] = {}

        try:
            found = await BleakScanner.discover(timeout=8.0)
        except Exception as err:  # noqa
            _LOGGER.warning("BLE scan failed: %s", err)
            return devices

        for device in found:
            name = device.name or ""

            if "ipixel" in name.lower():
                devices[device.address] = name

        return devices

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Return options flow."""
        return IPixelColorOptionsFlow(config_entry)


class IPixelColorOptionsFlow(config_entries.OptionsFlow):
    """Options flow placeholder."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> FlowResult:
        """Manage options."""
        return self.async_create_entry(title="", data={})