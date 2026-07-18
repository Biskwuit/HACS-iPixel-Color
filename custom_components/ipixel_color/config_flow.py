"""Config flow for iPixel Color."""

from typing import Any

from bleak import BleakScanner
from bleak.backends.device import BLEDevice
import voluptuous as vol

from homeassistant.config_entries import ConfigEntry, ConfigFlow, OptionsFlow
from homeassistant.const import CONF_ADDRESS, CONF_NAME
from homeassistant.data_entry_flow import FlowResult

from .const import DEFAULT_NAME, DOMAIN

class IPixelColorConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle config flow for iPixel Color."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Handle user step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            address = user_input[CONF_ADDRESS]
            name = user_input.get(CONF_NAME, DEFAULT_NAME)

            await self.async_set_unique_id(address)
            self._abort_if_unique_id_configured()

            return self.async_create_entry(
                title=name,
                data={CONF_ADDRESS: address, CONF_NAME: name},
            )

        devices = await BleakScanner.discover(return_adv=True)

        # Filter for iPixel Color devices by name pattern
        ipixel_devices: dict[str, BLEDevice] = {}
        for dev in devices.values():
            if dev and dev.name and "ipixel" in dev.name.lower():
                if dev.address not in ipixel_devices:
                    ipixel_devices[dev.address] = dev

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_ADDRESS): vol.In(
                        {addr: f"{dev.name} ({addr})" for addr, dev in ipixel_devices.items()}
                        if ipixel_devices
                        else {None: "No iPixel Color devices found"}
                    ),
                    vol.Optional(CONF_NAME, default=DEFAULT_NAME): str,
                }
            ),
            errors=errors,
        )