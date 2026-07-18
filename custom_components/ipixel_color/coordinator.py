"""Data coordinator for iPixel Color LED Matrix."""

import asyncio
import logging
from datetime import timedelta
from typing import Optional

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import (
    CONF_ADDRESS,
    DOMAIN,
    RECONNECT_DELAY,
    RECONNECT_MAX_DELAY,
)

_LOGGER = logging.getLogger(__name__)


class IPixelColorCoordinator(DataUpdateCoordinator):
    """Manages the connection to an iPixel Color LED Matrix device."""

    def __init__(
        self,
        hass: HomeAssistant,
        address: str,
    ) -> None:
        """Initialize the coordinator."""
        self._address = address
        self._client: Optional["pypixelcolor.AsyncClient"] = None
        self._reconnect_task: Optional[asyncio.Task] = None
        self._should_reconnect = False
        self._reconnect_delay = RECONNECT_DELAY

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=30),
            always_update=False,
        )

    @property
    def device_info(self) -> Optional["DeviceInfo"]:
        """Return cached device info."""
        if self._client is not None:
            try:
                return self._client.get_device_info()
            except RuntimeError:
                return None
        return None

    @property
    def available(self) -> bool:
        """Return True if connected."""
        return self._client is not None and self._client._connected  # noqa: SLF001

    async def _async_update_data(self):
        """Update data. Called by the coordinator."""
        # The device info is cached; we just need to maintain connection.
        if not self.available:
            _LOGGER.debug("Client not available, will reconnect")
        return {"available": self.available}

    async def async_connect(self) -> bool:
        """Connect to the device."""
        try:
            import pypixelcolor

            _LOGGER.info("Connecting to iPixel Color device at %s", self._address)
            self._client = pypixelcolor.AsyncClient(self._address)
            await self._client.connect()
            _LOGGER.info("Successfully connected to iPixel Color device at %s", self._address)
            self._should_reconnect = True
            self._reconnect_delay = RECONNECT_DELAY
            self.async_set_updated_data({"available": True})
            return True
        except Exception as err:
            _LOGGER.warning("Failed to connect to iPixel Color device: %s", err)
            self._client = None
            return False

    async def async_disconnect(self) -> None:
        """Disconnect from the device."""
        self._should_reconnect = False
        if self._reconnect_task:
            self._reconnect_task.cancel()
            self._reconnect_task = None

        if self._client is not None:
            try:
                await self._client.disconnect()
            except Exception as err:
                _LOGGER.debug("Error disconnecting: %s", err)
            self._client = None
            self.async_set_updated_data({"available": False})

    async def _async_reconnect_loop(self) -> None:
        """Background reconnect loop."""
        _LOGGER.debug("Starting reconnect loop for %s", self._address)
        while self._should_reconnect:
            if not self.available:
                _LOGGER.info("Attempting to reconnect to %s in %ds", self._address, self._reconnect_delay)
                connected = await self.async_connect()
                if not connected:
                    # Exponential backoff
                    self._reconnect_delay = min(self._reconnect_delay * 2, RECONNECT_MAX_DELAY)
                else:
                    self._reconnect_delay = RECONNECT_DELAY
            await asyncio.sleep(self._reconnect_delay)

    def start_reconnect_loop(self) -> None:
        """Start the automatic reconnect background task."""
        if self._reconnect_task is None or self._reconnect_task.done():
            self._should_reconnect = True
            self._reconnect_task = asyncio.create_task(self._async_reconnect_loop())
            _LOGGER.debug("Reconnect loop started for %s", self._address)

    async def send_text(
        self,
        text: str,
        animation: int = 0,
        speed: int = 80,
        color: str = "ffffff",
        font: str = "CUSONG",
    ) -> bool:
        """Send text to the device."""
        if not self.available:
            _LOGGER.warning("Cannot send text: not connected")
            return False

        try:
            await self._client.send_text(
                text=text,
                animation=animation,
                speed=speed,
                color=color,
                font=font,
            )
            return True
        except Exception as err:
            _LOGGER.warning("Failed to send text: %s", err)
            # Connection might be broken; trigger reconnect
            if self._should_reconnect and not self._reconnect_task.done():
                # The reconnect loop will handle it
                pass
            return False

    async def set_power(self, on: bool) -> bool:
        """Set the power state of the device."""
        if not self.available:
            _LOGGER.warning("Cannot set power: not connected")
            return False

        try:
            await self._client.set_power(on=on)
            return True
        except Exception as err:
            _LOGGER.warning("Failed to set power: %s", err)
            return False

    async def set_brightness(self, level: int) -> bool:
        """Set the brightness of the device (0-100)."""
        if not self.available:
            _LOGGER.warning("Cannot set brightness: not connected")
            return False

        try:
            await self._client.set_brightness(level=level)
            return True
        except Exception as err:
            _LOGGER.warning("Failed to set brightness: %s", err)
            return False

    async def clear(self) -> bool:
        """Clear the device display."""
        if not self.available:
            return False

        try:
            await self._client.clear()
            return True
        except Exception as err:
            _LOGGER.warning("Failed to clear display: %s", err)
            return False