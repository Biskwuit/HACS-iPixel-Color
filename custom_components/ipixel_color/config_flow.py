"""Config flow for iPixel Color LED Matrix."""

import asyncio
import logging
from typing import Any

import bluetooth
from homeassistant.components import bluetooth
from homeassistant.config_entries import ConfigFlow, ConfigEntry, OptionsFlow
from homeassistant.core import callback
from homeassistant.helpers.selector import selector

from .const import CONF_ADDRESS, DOMAIN

_LOGGER = logging.getLogger(__name__)


class IPixelColorConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for iPixel Color LED Matrix."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._address: str | None = None
        self._devices: dict[str, bluetooth.BLEDevice] = {}

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Handle the user step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            address = user_input[CONF_ADDRESS]
            await self.async_set_unique_id(address)
            self._abort_if_unique_id_configured()

            # Validate connection
            try:
                import pypixelcolor
                client = pypixelcolor.AsyncClient(address)
                await client.connect()
                await client.disconnect()
            except Exception as err:
                _LOGGER.warning("Connection validation failed: %s", err)
                errors["base"] = "cannot_connect"

            if not errors:
                return self.async_create_entry(
                    title=f"iPixel Color LED Matrix ({address})",
                    data={CONF_ADDRESS: address},
                )

        # Discover devices
        discovered = bluetooth.async_discovered_service_info(self.hass)
        self._devices = {}
        devices_dict = {}

        for discovery in discovered:
            if discovery.name and "iPixel" in discovery.name:
                address = discovery.address
                self._devices[address] = discovery
                devices_dict[address] = f"{discovery.name} ({address})"

        if not devices_dict:
            # If no auto-discovered, show any discovered BLE devices as fallback
            for discovery in discovered:
                address = discovery.address
                self._devices[address] = discovery
                devices_dict[address] = f"{discovery.name or 'Unknown'} ({address})"

        return self.async_show_form(
            step_id="user",
            data_schema=selector({
                CONF_ADDRESS: selector({
                    "select": {
                        "options": [
                            {"label": name, "value": addr}
                            for addr, name in devices_dict.items()
                        ]
                    }
                })
            }),
            errors=errors,
        )

    async def async_step_bluetooth(
        self, discovery_info: bluetooth.BluetoothServiceInfoBleak
    ) -> dict[str, Any]:
        """Handle the bluetooth discovery step."""
        address = discovery_info.address
        await self.async_set_unique_id(address)
        self._abort_if_unique_id_configured()

        self._address = address
        self.context["title_placeholders"] = {"address": address}

        return self.async_show_form(
            step_id="bluetooth_confirm",
            description_placeholders={CONF_ADDRESS: address},
        )

    async def async_step_bluetooth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Confirm the bluetooth discovery."""
        if user_input is None:
            return self.async_show_form(step_id="bluetooth_confirm")

        address = self._address or self.context.get("title_placeholders", {}).get("address")
        return self.async_create_entry(
            title=f"iPixel Color LED Matrix ({address})",
            data={CONF_ADDRESS: address},
        )

    @staticmethod
    @callback
    def async_get_options_flow(entry: ConfigEntry) -> OptionsFlow:
        """Get the options flow."""
        return IPixelColorOptionsFlow(entry)


class IPixelColorOptionsFlow(OptionsFlow):
    """Handle options for iPixel Color."""

    def __init__(self, entry: ConfigEntry) -> None:
        """Initialize options flow."""
        self._entry = entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Manage options."""
        return self.async_show_form(step_id="init")
