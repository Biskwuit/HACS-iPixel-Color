"""Light entity for iPixel Color LED Matrix.

Represents the matrix power state and brightness.
State is derived from the coordinator; when disconnected after
exhausted reconnect attempts the entity shows Unavailable while
the background reconnect loop continues.
"""

from __future__ import annotations

import logging
from typing import Any, Optional

from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ColorMode,
    LightEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import IPixelDevice

_LOGGER = logging.getLogger(__name__)


def _ha_brightness_to_percent(value: int) -> int:
    """Convert 0-255 HA brightness to 0-100 device level."""
    return round(value / 255.0 * 100)


def _device_brightness_to_ha(value: int) -> int:
    """Convert 0-100 device brightness to 0-255 HA brightness."""
    return round(value / 100.0 * 255.0)


class IPixelLight(LightEntity):
    """Light entity wrapping the IPixelDevice power + brightness."""

    _attr_color_mode = ColorMode.BRIGHTNESS
    _attr_supported_color_modes = {ColorMode.BRIGHTNESS}
    _attr_has_entity_name = True
    _attr_name = None  # Use device name from ConfigEntry

    def __init__(self, device: IPixelDevice, entry: ConfigEntry) -> None:
        self._device = device
        self._entry = entry
        self._attr_unique_id = f"{DOMAIN}_{device.address}_light"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, device.address)},
            name=device.display_name,
            manufacturer="iPixel",
            model="iPixel Color LED Matrix",
        )

    @property
    def available(self) -> bool:
        """Return False when the device is disconnected."""
        return self._device.is_connected

    @property
    def is_on(self) -> bool:
        """Power state is tracked via coordinator data."""
        data = self._device.coordinator.data or {}
        return data.get("power_on", True)

    @property
    def brightness(self) -> int | None:
        """Current brightness 0-255 or None if unknown."""
        data = self._device.coordinator.data or {}
        level = data.get("brightness")
        if level is None:
            return None
        return _device_brightness_to_ha(level)

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on the device, optionally setting brightness."""
        brightness_arg = kwargs.get(ATTR_BRIGHTNESS)
        if brightness_arg is not None:
            level = _ha_brightness_to_percent(brightness_arg)
            await self._device.set_brightness(level)

        await self._device.set_power(True)
        await self._device.coordinator.async_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off the device."""
        await self._device.set_power(False)
        await self._device.coordinator.async_refresh()

    async def async_update(self) -> None:
        """Refresh state from the coordinator.

        The coordinator will raise if the device is disconnected,
        which Home Assistant will catch and handle by marking the
        entity unavailable.
        """
        await self._device.coordinator.async_refresh()


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the iPixel light entity from a config entry."""
    device: IPixelDevice = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([IPixelLight(device, entry)], True)
