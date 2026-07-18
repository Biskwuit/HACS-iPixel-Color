"""iPixel Color LED Matrix custom integration for Home Assistant."""

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN

__version__ = "0.2.0"


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up iPixel Color from a config entry."""
    await hass.config_entries.async_forward_entry_setups(entry, ["light"])
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload iPixel Color config entry."""
    return await hass.config_entries.async_unload_platforms(entry, ["light"])
