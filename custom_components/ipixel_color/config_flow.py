"""Config flow for iPixel Color integration."""

from typing import Any

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.config_entries import ConfigFlow, OptionsFlow
from homeassistant.const import CONF_ADDRESS, CONF_NAME
from homeassistant.data_entry_flow import FlowResult

from .const import DOMAIN, IPIXEL_ADVERTISEMENT_NAME_PREFIX, SCAN_TIMEOUT
from .coordinator import IPixelColorCoordinator

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_ADDRESS): cv.string,
        vol.Optional(CONF_NAME, default=""): cv.string,
    }
)


class IPixelColorConfigFlow(ConfigFlow, domain=DOMAIN):
    """Config flow for iPixel Color."""

    VERSION = 1
    MINOR_VERSION = 1

    def __init__(self) -> None:
        self._discovered_devices: list[dict[str, str]] = []

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            address = user_input.get(CONF_ADDRESS, "").strip()
            name = user_input.get(CONF_NAME, "").strip()
            if not address:
                errors["base"] = "missing_address"
            else:
                await self.async_set_unique_id(address)
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=name or f"iPixel Color {address}",
                    data={CONF_ADDRESS: address, CONF_NAME: name},
                )

        # Run BLE scan if no devices yet
        if not self._discovered_devices:
            self._discovered_devices = IPixelColorCoordinator.discover()

        devices = {
            d["address"]: d["name"] or f"{IPIXEL_ADVERTISEMENT_NAME_PREFIX} {d['address']}"
            for d in self._discovered_devices
        }

        if not devices:
            return self.async_show_form(
                step_id="user",
                data_schema=STEP_USER_DATA_SCHEMA,
                errors=errors,
                description_placeholders={
                    "scan_timeout": str(SCAN_TIMEOUT),
                    "hint": (
                        "No devices found. Enter the BLE address manually "
                        "(e.g. AA:BB:CC:DD:EE:FF) or check that your device is powered on."
                    ),
                },
            )

        # Offer discovered devices
        addresses = list(devices.keys())
        select_schema = vol.Schema(
            {
                vol.Required("selected_address"): cv.select_with_default(
                    options=addresses,
                    default=addresses[0],
                ),
                vol.Optional(CONF_NAME, default=""): cv.string,
            }
        )

        if user_input is not None and "selected_address" in user_input:
            address = user_input["selected_address"]
            name = user_input.get(CONF_NAME, "").strip()
            await self.async_set_unique_id(address)
            self._abort_if_unique_id_configured()
            return self.async_create_entry(
                title=name or devices[address],
                data={CONF_ADDRESS: address, CONF_NAME: name},
            )

        return self.async_show_form(
            step_id="user",
            data_schema=select_schema,
            errors=errors,
            description_placeholders={
                "hint": f"Found {len(devices)} device(s). Select one or enter manually below.",
            },
        )
