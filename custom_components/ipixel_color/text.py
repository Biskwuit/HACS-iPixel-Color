"""Text entity for iPixel Color LED Matrix."""

import logging
from typing import Any

from homeassistant.components.bluetooth import CONNECTIONS_DOMAIN
from homeassistant.components.text import TextEntity, TextMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CONF_ADDRESS, DOMAIN
from .coordinator import IPixelColorCoordinator

_LOGGER = logging.getLogger(__name__)


class IPixelColorText(TextEntity):
    """Text entity for sending messages to the LED matrix."""

    _attr_has_entity_name = True
    _attr_translation_key = "text"
    _attr_mode = TextMode.TEXT
    _attr_max = 200
    _attr_min = 1

    def __init__(
        self,
        coordinator: IPixelColorCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the text entity."""
        super().__init__(coordinator)
        self._entry = entry
        self._address = entry.data[CONF_ADDRESS]
        self._attr_unique_id = f"{self._address}_text"
        self._attr_device_info = self._get_device_info()

    def _get_device_info(self) -> dict[str, Any]:
        """Build device info."""
        device_info = self.coordinator.device_info

        name = "iPixel Color LED Matrix"
        if device_info:
            model = getattr(device_info, "model", None) or "iPixel Color"
            firmware = getattr(device_info, "firmware", None) or "Unknown"
            name = f"iPixel Color {model}"

            return {
                "identifiers": {(CONNECTIONS_DOMAIN, self._address)},
                "name": name,
                "manufacturer": "iPixel",
                "model": model,
                "sw_version": firmware,
            }

        return {
            "identifiers": {(CONNECTIONS_DOMAIN, self._address)},
            "name": name,
            "manufacturer": "iPixel",
            "model": "iPixel Color LED Matrix",
        }

    async def async_set_value(self, value: str) -> None:
        """Set the text value and send to the device."""
        if not value:
            return

        success = await self.coordinator.send_text(
            text=value,
            animation=0,
            speed=80,
            color="ffffff",
            font="CUSONG",
        )

        if not success:
            _LOGGER.warning("Failed to send text to device")

        self.async_write_ha_state()

    @property
    def native_value(self) -> str | None:
        """Return the current text value."""
        return getattr(self, "_last_sent_text", None)

    @property
    def available(self) -> bool:
        """Return True if the device is available."""
        return self.coordinator.available