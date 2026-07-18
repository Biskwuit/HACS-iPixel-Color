"""iPixel Color LED matrix light entity."""
from homeassistant.components.light import CoordinatorEntity, ColorMode

import logging
from typing import Any, Optional

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv, entity_platform
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    DOMAIN,
    SERVICE_SEND_IMAGE,
    SERVICE_SEND_IMAGE_HEX,
    SERVICE_SEND_TEXT,
)
from .coordinator import IPixelColorCoordinator

_LOGGER = logging.getLogger(__name__)


# ── Service schemas ────────────────────────────────────────────────────────────

SEND_TEXT_SCHEMA = cv.make_entity_service_schema(
    {
        vol.Required("text"): cv.string,
        vol.Optional("color", default="ffffff"): cv.string,
        vol.Optional("rainbow_mode", default=0): vol.All(vol.Coerce(int), vol.Range(min=0, max=9)),
        vol.Optional("animation", default=1): vol.All(vol.Coerce(int), vol.Range(min=1, max=4)),
        vol.Optional("speed", default=80): vol.All(vol.Coerce(int), vol.Range(min=0, max=100)),
        vol.Optional("save_slot", default=0): vol.All(vol.Coerce(int), vol.Range(min=0, max=10)),
    }
)

SEND_IMAGE_SCHEMA = cv.make_entity_service_schema(
    {
        vol.Required("image"): cv.string,
        vol.Optional("save_slot", default=0): vol.All(vol.Coerce(int), vol.Range(min=0, max=10)),
        vol.Optional("animation", default=0): vol.All(vol.Coerce(int), vol.Range(min=0, max=10)),
        vol.Optional("speed", default=80): vol.All(vol.Coerce(int), vol.Range(min=0, max=100)),
        vol.Optional("resize_method", default="crop"): vol.In(["crop", "fit"]),
    }
)

SEND_IMAGE_HEX_SCHEMA = cv.make_entity_service_schema(
    {
        vol.Required("hex_string"): cv.string,
        vol.Required("file_extension", default=".png"): cv.string,
        vol.Optional("save_slot", default=0): vol.All(vol.Coerce(int), vol.Range(min=0, max=10)),
        vol.Optional("resize_method", default="crop"): vol.In(["crop", "fit"]),
    }
)


# ── Entity ─────────────────────────────────────────────────────────────────────

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the iPixel Color light entity from a config entry."""
    coordinator: IPixelColorCoordinator = hass.data[DOMAIN][config_entry.entry_id]

    async_add_entities([IPixelColorLight(coordinator, config_entry.data.get("name", ""))])

    # Register entity-level services
    platform = entity_platform.async_get_current_platform()

    platform.async_register_entity_service(
        SERVICE_SEND_TEXT,
        SEND_TEXT_SCHEMA,
        "async_send_text",
    )
    platform.async_register_entity_service(
        SERVICE_SEND_IMAGE,
        SEND_IMAGE_SCHEMA,
        "async_send_image",
    )
    platform.async_register_entity_service(
        SERVICE_SEND_IMAGE_HEX,
        SEND_IMAGE_HEX_SCHEMA,
        "async_send_image_hex",
    )


class IPixelColorLight(CoordinatorEntity):
    """Home Assistant Light entity wrapping an IPixelColorCoordinator."""

    _attr_max_color_temp_kelvin = 10000
    _attr_min_color_temp_kelvin = 1000
    _attr_max_mireds = 500
    _attr_min_mireds = 50
    _attr_supported_features = 0
    _attr_color_mode = ColorMode.BRIGHTNESS
    _attr_supported_color_modes = {ColorMode.BRIGHTNESS}
    _attr_effect = None
    _attr_effect_list: list[str] | None = None

    def __init__(self, coordinator: IPixelColorCoordinator, name: str) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = coordinator.address.replace(":", "-")
        self._attr_device_info = {
            "identifiers": {(DOMAIN, coordinator.address)},
            "name": name or coordinator.name,
            "manufacturer": "iPixel Color",
            "sw_version": "0.2.0",
        }
        self._attr_name = name or "iPixel Color"
        self._attr_brightness = coordinator.brightness

    # ── Entity state ───────────────────────────────────────────────────────────

    @property
    def is_on(self) -> bool:
        return self.coordinator.is_on

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self.coordinator.async_set_power(True)
        if (brightness := kwargs.get("brightness")) is not None:
            await self.coordinator.async_set_brightness(brightness)
        await self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self.coordinator.async_set_power(False)
        await self.async_write_ha_state()

    async def async_update(self) -> None:
        # State is driven by coordinator; nothing to poll.
        pass

    # ── Service handlers ───────────────────────────────────────────────────────

    async def async_send_text(
        self,
        text: str,
        color: str = "ffffff",
        rainbow_mode: int = 0,
        animation: int = 1,
        speed: int = 80,
        save_slot: int = 0,
    ) -> None:
        """Display text on the LED matrix."""
        await self.coordinator.async_send_text(
            text=text,
            color=color,
            rainbow_mode=rainbow_mode,
            animation=animation,
            speed=speed,
            save_slot=save_slot,
        )
        await self.async_write_ha_state()

    async def async_send_image(
        self,
        image: str,
        save_slot: int = 0,
        animation: int = 0,
        speed: int = 80,
        resize_method: str = "crop",
    ) -> None:
        """Display a static image or animated GIF on the LED matrix.
        
        Args:
            image:          Full path to a local image file.
            save_slot:      Save slot (1-10). 0=transient.
            animation:      Reserved.
            speed:          Reserved.
            resize_method:  'crop' (fill, crop edges) or 'fit' (fit with padding).
        """
        await self.coordinator.async_send_image(
            image=image,
            save_slot=save_slot,
            animation=animation,
            speed=speed,
            resize_method=resize_method,
        )
        await self.async_write_ha_state()

    async def async_send_image_hex(
        self,
        hex_string: str,
        file_extension: str = ".png",
        save_slot: int = 0,
        resize_method: str = "crop",
    ) -> None:
        """Display an image from a hexadecimal string on the LED matrix.
        
        Args:
            hex_string:     Hexadecimal string of image data.
            file_extension: File extension identifying the image type.
            save_slot:      Save slot (1-10). 0=transient.
            resize_method:  'crop' or 'fit'.
        """
        await self.coordinator.async_send_image_hex(
            hex_string=hex_string,
            file_extension=file_extension,
            save_slot=save_slot,
            resize_method=resize_method,
        )
        await self.async_write_ha_state()
