"""Config flow for iPixel Color LED Matrix."""

import logging
from typing import Any

import voluptuous as vol

from homeassistant.components import bluetooth
from homeassistant.components.bluetooth import BluetoothServiceInfoBleak
from homeassistant.config_entries import ConfigFlow, ConfigEntry, OptionsFlow
from homeassistant.core import callback
from homeassistant.helpers.selector import (
    SelectSelector,
    SelectSelectorConfig,
    SelectOptionDict,
    SelectSelectorMode,
)

from .const import CONF_ADDRESS, DOMAIN

_LOGGER = logging.getLogger(__name__)


class IPixelColorConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for iPixel Color LED Matrix."""

    VERSION = 1

    def __init__(self) -> None:
        self._address: str | None = None
        self._devices: dict[str, Any] = {}

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        errors: dict[str, str] = {}

        if user_input is not None:
            address = user_input[CONF_ADDRESS]
            await self.async_set_unique_id(address)
            self._abort_if_unique_id_configured()

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
        devices_dict: dict[str, str] = {}

        for discovery in discovered:
            if discovery.name and "iPixel" in discovery.name:
                devices_dict[discovery.address] = f"{discovery.name} ({discovery.address})"

        if not devices_dict:
            for discovery in discovered:
                devices_dict[discovery.address] = (
                    f"{discovery.name or 'Unknown'} ({discovery.address})"
                )

        # No devices found at all -> let the user type a MAC manually
        if not devices_dict:
            schema = vol.Schema({vol.Required(CONF_ADDRESS): str})
        else:
            schema = vol.Schema(
                {
                    vol.Required(CONF_ADDRESS): SelectSelector(
                        SelectSelectorConfig(
                            options=[
                                SelectOptionDict(value=addr, label=name)
                                for addr, name in devices_dict.items()
                            ],
                            mode=SelectSelectorMode.DROPDOWN,
                            custom_value=True,
                        )
                    )
                }
            )

        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors,
        )

    async def async_step_bluetooth(
        self, discovery_info: BluetoothServiceInfoBleak
    ) -> dict[str, Any]:
        address = discovery_info.address
        await self.async_set_unique_id(address)
        self._abort_if_unique_id_configured()

        self._address = address
        self.context["title_placeholders"] = {"address": address}

        return await self.async_step_bluetooth_confirm()

    async def async_step_bluetooth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        if user_input is None:
            return self.async_show_form(
                step_id="bluetooth_confirm",
                description_placeholders={CONF_ADDRESS: self._address},
            )

        return self.async_create_entry(
            title=f"iPixel Color LED Matrix ({self._address})",
            data={CONF_ADDRESS: self._address},
        )

    @staticmethod
    @callback
    def async_get_options_flow(entry: ConfigEntry) -> OptionsFlow:
        return IPixelColorOptionsFlow(entry)


class IPixelColorOptionsFlow(OptionsFlow):
    """Handle options for iPixel Color."""

    def __init__(self, entry: ConfigEntry) -> None:
        self._entry = entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)
        return self.async_show_form(step_id="init")