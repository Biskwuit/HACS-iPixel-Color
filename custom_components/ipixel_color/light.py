"""Light entity for iPixel Color LED Matrix."""

import logging
from typing import Any, Optional

from homeassistant.components.bluetooth import CONNECTIONS_DOMAIN
from homeassistant.components.light import ColorMode, LightEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CONF_ADDRESS, DOMAIN
from .coordinator import IPixelColorCoordinator

_LOGGER = logging.getLogger(__name__)


class IPixelColorLight(LightEntity):
    """Light entity for controlling power and brightness."""

    _attr_color_mode = ColorMode.BRIGHTNESS
    _attr_supported_color_modes = {ColorMode.BRIGHTNESS}
    _attr_has_entity_name = True
    _attr_translation_key = "light"

    def __init__(
        self,
        coordinator: IPixelColorCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the light entity."""
        super().__init__(coordinator)
        self._entry = entry
        self._address = entry.data[CONF_ADDRESS]
        self._attr_unique_id = f"{self._address}_light"
        self._attr_device_info = self._get_device_info()

        self._cached_brightness: Optional[int] = None

    def _get_device_info(self) -> dict[str, Any]:
        """Build device info."""
        device_info = self.coordinator.device_info
        connections = {(CONNECTIONS_DOMAIN, self._address)}

        name = "iPixel Color LED Matrix"
        if device_info:
            model = getattr(device_info, "model", None) or "iPixel Color"
            firmware = getattr(device_info, "firmware", None) or "Unknown"
            name = f"iPixel Color {model}"

            identifiers: set[tuple[str, str]] = set()
            for conn in connections:
                identifiers.add(conn)

            return {
                "identifiers": identifiers,
                "name": name,
                "manufacturer": "iPixel",
                "model": model,
                "sw_version": firmware,
            }

        return {
            "identifiers": connections,
            "name": name,
            "manufacturer": "iPixel",
            "model": "iPixel Color LED Matrix",
        }

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on the light."""
        await self.coordinator.set_power(True)
        if (brightness := kwargs.get("brightness")) is not None:
            level = int(brightness / 2.55)  # HA uses 0-255, device uses 0-100
            await self.coordinator.set_brightness(level)
            self._cached_brightness = level
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off the light."""
        await self.coordinator.set_power(False)
        self.async_write_ha_state()

    async def async_update_brightness(self, brightness: int) -> None:
        """Update brightness."""
        if self._attr_is_on:
            level = int(brightness / 2.55)
            await self.coordinator.set_brightness(level)
            self._cached_brightness = level
            self.async_write_ha_state()

    @property
    def is_on(self) -> bool:
        """Return True if the device is on."""
        return self.coordinator.available

    @property
    def brightness(self) -> Optional[int]:
        """Return the brightness (0-255 scale)."""
        return self._cached_brightness * 2.55 if self._cached_brightness else 255

    @property
    def available(self) -> bool:
        """Return True if the device is available."""
        return self.coordinator.available