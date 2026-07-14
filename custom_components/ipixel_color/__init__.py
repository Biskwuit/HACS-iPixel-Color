"""iPixel Color LED Matrix Home Assistant integration."""

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .coordinator import IPixelDevice
from . import services  # noqa: F401 — registers services at import time

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["light"]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up iPixel Color LED Matrix from a config entry."""
    address: str = entry.data["address"]
    name: str = entry.data.get("name") or address

    device = IPixelDevice(
        hass=hass,
        address=address,
        entry_id=entry.entry_id,
        name=name,
    )

    if DOMAIN not in hass.data:
        hass.data[DOMAIN] = {}
        services.register_services(hass)

    hass.data[DOMAIN][entry.entry_id] = device

    try:
        await device.connect()
    except Exception as ex:
        _LOGGER.warning(
            "[%s] Initial connection failed; background reconnect will keep trying: %s",
            address,
            ex,
        )

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload and disconnect the integration."""
    device: IPixelDevice = hass.data[DOMAIN].pop(entry.entry_id, None)
    if device is None:
        return True

    await device.disconnect()

    if not hass.data[DOMAIN]:
        del hass.data[DOMAIN]

    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    return unload_ok
