"""Light platform for iPixel Color."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ColorMode,
    LightEntity,
    LightEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.entity_platform import AddEntitiesCallback, async_get_current_platform

from .const import (
    DOMAIN,
    SERVICE_CLEAR,
    SERVICE_SEND_IMAGE,
    SERVICE_SEND_TEXT,
    SERVICE_SET_CLOCK,
    SERVICE_SET_ORIENTATION,
    SERVICE_SHOW_SLOT,
)
from .coordinator import IPixelCoordinator

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up light entity."""
    coordinator: IPixelCoordinator = hass.data[DOMAIN][entry.entry_id]

    entity = IPixelColorLight(coordinator)
    async_add_entities([entity])

    platform = async_get_current_platform()

    platform.async_register_entity_service(
        SERVICE_SEND_TEXT,
        {
            vol.Required("text"): cv.string,
            vol.Optional("color", default="ffffff"): cv.string,
            vol.Optional("bg_color"): cv.string,
            vol.Optional("rainbow_mode", default=0): vol.Coerce(int),
            vol.Optional("animation", default=0): vol.Coerce(int),
            vol.Optional("save_slot", default=0): vol.Coerce(int),
            vol.Optional("speed", default=80): vol.Coerce(int),
            vol.Optional("font", default="CUSONG"): cv.string,
        },
        "async_send_text",
    )

    platform.async_register_entity_service(
        SERVICE_SEND_IMAGE,
        {
            vol.Optional("path"): cv.string,
            vol.Optional("hex_string"): cv.string,
            vol.Optional("file_extension", default=".png"): cv.string,
            vol.Optional("resize_method", default="crop"): vol.In(["crop", "fit"]),
            vol.Optional("save_slot", default=0): vol.Coerce(int),
        },
        "async_send_image",
    )

    platform.async_register_entity_service(
        SERVICE_SET_CLOCK,
        {
            vol.Optional("style", default=1): vol.Coerce(int),
            vol.Optional("show_date", default=True): cv.boolean,
            vol.Optional("format_24", default=True): cv.boolean,
        },
        "async_set_clock",
    )

    platform.async_register_entity_service(
        SERVICE_SHOW_SLOT,
        {
            vol.Required("number"): vol.Coerce(int),
        },
        "async_show_slot",
    )

    platform.async_register_entity_service(
        SERVICE_SET_ORIENTATION,
        {
            vol.Required("orientation"): vol.Coerce(int),
        },
        "async_set_orientation",
    )

    platform.async_register_entity_service(
        SERVICE_CLEAR,
        {},
        "async_clear",
    )

class IPixelColorLight(LightEntity):
    """Representation of an iPixel Color matrix as a light."""

    _attr_has_entity_name = True
    _attr_name = None
    _attr_supported_color_modes = {ColorMode.BRIGHTNESS}
    _attr_color_mode = ColorMode.BRIGHTNESS
    _attr_supported_features = LightEntityFeature.EFFECT

    def __init__(self, coordinator: IPixelCoordinator) -> None:
        """Initialize entity."""
        self.coordinator = coordinator
        self._attr_unique_id = coordinator.address
        self._attr_device_info = coordinator.async_device_info()

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        # We keep it available so service calls can trigger reconnect.
        return True

    @property
    def is_on(self) -> bool:
        """Return if display is on."""
        return self.coordinator.is_on

    @property
    def brightness(self) -> int:
        """Return brightness."""
        return self.coordinator.brightness

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on display."""
        brightness = kwargs.get(ATTR_BRIGHTNESS)

        if brightness is not None:
            await self.coordinator.async_set_brightness(brightness)
        else:
            await self.coordinator.async_set_power(True)

        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off display."""
        await self.coordinator.async_set_power(False)
        self.async_write_ha_state()

    async def async_send_text(
        self,
        text: str,
        color: str = "ffffff",
        bg_color: str | None = None,
        rainbow_mode: int = 0,
        animation: int = 0,
        save_slot: int = 0,
        speed: int = 80,
        font: str = "CUSONG",
    ) -> None:
        """Send text service."""
        await self.coordinator.async_send_text(
            text,
            color=color,
            bg_color=bg_color,
            rainbow_mode=rainbow_mode,
            animation=animation,
            save_slot=save_slot,
            speed=speed,
            font=font,
        )
        self.async_write_ha_state()

    async def async_send_image(
        self,
        path: str | None = None,
        hex_string: str | None = None,
        file_extension: str = ".png",
        resize_method: str = "crop",
        save_slot: int = 0,
    ) -> None:
        """Send image service."""
        if path is not None:
            await self.coordinator.async_send_image(
                path,
                resize_method=resize_method,
                save_slot=save_slot,
            )
        elif hex_string is not None:
            await self.coordinator.async_send_image_hex(
                hex_string,
                file_extension=file_extension,
                resize_method=resize_method,
                save_slot=save_slot,
            )
        else:
            raise ValueError("Either path or hex_string must be provided")
        self.async_write_ha_state()

    async def async_set_clock(
        self,
        style: int = 1,
        show_date: bool = True,
        format_24: bool = True,
    ) -> None:
        """Set clock mode service."""
        await self.coordinator.async_set_clock(
            style=style,
            show_date=show_date,
            format_24=format_24,
        )
        self.async_write_ha_state()

    async def async_show_slot(self, number: int) -> None:
        """Show saved slot service."""
        await self.coordinator.async_show_slot(number)
        self.async_write_ha_state()

    async def async_set_orientation(self, orientation: int) -> None:
        """Set orientation service."""
        await self.coordinator.async_set_orientation(orientation)
        self.async_write_ha_state()

    async def async_clear(self) -> None:
        """Clear device service."""
        await self.coordinator.async_clear()
        self.async_write_ha_state()