"""Service handlers for ipixel_color.

Provides two services:
  - ipixel_color.send_text  — display a text message on the matrix
  - ipixel_color.send_image — display an image from a file path
"""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import HomeAssistantError

from .const import DOMAIN
from .coordinator import IPixelDevice

_LOGGER = logging.getLogger(__name__)

# Maps HA brightness (0-255) → device brightness (0-100)
def _ha_to_device_brightness(value: int | None) -> int | None:
    if value is None:
        return None
    return round(value / 255.0 * 100)


async def _get_device(hass: HomeAssistant, entity_id: str) -> IPixelDevice:
    """Resolve entity_id → IPixelDevice, raising if unavailable."""
    state = hass.states.get(entity_id)
    if state is None:
        raise HomeAssistantError(f"Entity {entity_id} not found")
    entry_id = state.context.as_dict().get("entry_id")
    if entry_id is None:
        raise HomeAssistantError(f"Entity {entity_id} is not a tracked iPixel device")
    device = hass.data[DOMAIN].get(entry_id)
    if device is None:
        raise HomeAssistantError(f"Device for {entity_id} is not loaded")
    return device


async def _send_text(hass: HomeAssistant, call: ServiceCall) -> None:
    data = call.data
    entity_id: str = data["entity_id"]
    device = await _get_device(hass, entity_id)

    brightness = data.get("brightness")
    if brightness is not None:
        await device.set_brightness(_ha_to_device_brightness(brightness))

    await device.send_text(
        text=data["message"],
        color=data.get("color", "ffffff"),
        bg_color=data.get("bg_color"),
        animation=int(data.get("animation", 0)),
        speed=int(data.get("speed", 80)),
        rainbow_mode=int(data.get("rainbow_mode", 0)),
        font=data.get("font", "CUSONG"),
    )
    _LOGGER.info("[%s] send_text: %s", device.address, data["message"])


async def _send_image(hass: HomeAssistant, call: ServiceCall) -> None:
    data = call.data
    entity_id: str = data["entity_id"]
    path: str = data["path"]
    device = await _get_device(hass, entity_id)

    resize_method = data.get("resize_method", "crop")
    await device.send_image(path)
    _LOGGER.info("[%s] send_image: %s (resize=%s)", device.address, path, resize_method)


def register_services(hass: HomeAssistant) -> None:
    """Register ipixel_color services with Home Assistant."""
    async def handle_send_text(call: ServiceCall) -> None:
        try:
            await _send_text(hass, call)
        except Exception as ex:
            _LOGGER.exception("send_text service failed: %s", ex)
            raise HomeAssistantError(str(ex)) from ex

    async def handle_send_image(call: ServiceCall) -> None:
        try:
            await _send_image(hass, call)
        except Exception as ex:
            _LOGGER.exception("send_image service failed: %s", ex)
            raise HomeAssistantError(str(ex)) from ex

    hass.services.async_register(
        DOMAIN, "send_text", handle_send_text,
        schema={
            "entity_id": str,
            "message": str,
            "color": str,
            "bg_color": str | None,
            "animation": int,
            "speed": int,
            "rainbow_mode": int,
            "font": str,
            "brightness": int | None,
        },
    )

    hass.services.async_register(
        DOMAIN, "send_image", handle_send_image,
        schema={
            "entity_id": str,
            "path": str,
            "resize_method": str,
        },
    )
