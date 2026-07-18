"""Coordinator/client wrapper for iPixel Color."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable, Callable
from typing import Any, TypeVar

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError

from pypixelcolor.client import AsyncClient

from .const import (
    CONF_ADDRESS,
    MAX_RECONNECT_ATTEMPTS,
    RECONNECT_DELAY,
)

_LOGGER = logging.getLogger(__name__)

_T = TypeVar("_T")


class IPixelConnectionError(HomeAssistantError):
    """Raised when the iPixel device cannot be reached."""


class IPixelCoordinator:
    """Connection manager for an iPixel Color matrix.

    Handles:
    - Initial BLE connect
    - Automatic reconnect on command failure
    - Serialized command execution
    - Basic cached state
    """

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize coordinator."""
        self.hass = hass
        self.entry = entry
        self.address: str = entry.data[CONF_ADDRESS]

        self.client = AsyncClient(self.address)

        self._lock = asyncio.Lock()
        self._connected = False

        self.is_on = False
        self.brightness = 255

    @property
    def connected(self) -> bool:
        """Return current connection state."""
        return self._connected

    async def async_connect(self) -> None:
        """Connect to the matrix."""
        async with self._lock:
            await self._async_connect_locked()

    async def _async_connect_locked(self) -> None:
        """Connect while lock is already held."""
        if self._connected:
            return

        _LOGGER.debug("Connecting to iPixel Color device %s", self.address)

        try:
            await self.client.connect()
        except Exception as err:  # noqa: BLE library can raise several types
            self._connected = False
            _LOGGER.warning("Failed to connect to iPixel Color %s: %s", self.address, err)
            raise IPixelConnectionError(f"Could not connect to iPixel Color {self.address}") from err

        self._connected = True
        _LOGGER.info("Connected to iPixel Color device %s", self.address)

    async def async_disconnect(self) -> None:
        """Disconnect from the matrix."""
        async with self._lock:
            if not self._connected:
                return

            try:
                await self.client.disconnect()
            except Exception as err:  # noqa
                _LOGGER.debug("Error while disconnecting iPixel Color: %s", err)
            finally:
                self._connected = False

    async def _async_reconnect_locked(self) -> None:
        """Reconnect while lock is already held."""
        self._connected = False

        try:
            await self.client.disconnect()
        except Exception:
            pass

        self.client = AsyncClient(self.address)

        last_error: Exception | None = None

        for attempt in range(1, MAX_RECONNECT_ATTEMPTS + 1):
            try:
                _LOGGER.debug(
                    "Reconnect attempt %s/%s for iPixel Color %s",
                    attempt,
                    MAX_RECONNECT_ATTEMPTS,
                    self.address,
                )
                await self.client.connect()
            except Exception as err:  # noqa
                last_error = err
                await asyncio.sleep(RECONNECT_DELAY)
            else:
                self._connected = True
                _LOGGER.info("Reconnected to iPixel Color %s", self.address)
                return

        raise IPixelConnectionError(
            f"Could not reconnect to iPixel Color {self.address}"
        ) from last_error

    async def async_call(
        self,
        func: Callable[[AsyncClient], Awaitable[_T]],
        *,
        reconnect: bool = True,
    ) -> _T:
        """Call a pypixelcolor command with reconnect handling."""
        async with self._lock:
            if not self._connected:
                await self._async_connect_locked()

            try:
                return await func(self.client)
            except Exception as first_err:  # noqa
                _LOGGER.warning(
                    "iPixel Color command failed, reconnect=%s: %s",
                    reconnect,
                    first_err,
                )

                self._connected = False

                if not reconnect:
                    raise IPixelConnectionError("iPixel Color command failed") from first_err

                await self._async_reconnect_locked()

                try:
                    return await func(self.client)
                except Exception as second_err:  # noqa
                    self._connected = False
                    raise IPixelConnectionError(
                        "iPixel Color command failed after reconnect"
                    ) from second_err

    async def async_set_power(self, on: bool) -> None:
        """Set display power."""
        await self.async_call(lambda client: client.set_power(on))
        self.is_on = on

    async def async_set_brightness(self, brightness: int) -> None:
        """Set brightness, Home Assistant scale 0-255."""
        brightness = max(0, min(255, brightness))

        # pypixelcolor expects a level; most devices use 0-100.
        level = round((brightness / 255) * 100)

        await self.async_call(lambda client: client.set_brightness(level))

        self.brightness = brightness
        if brightness > 0:
            self.is_on = True

    async def async_send_text(
        self,
        text: str,
        *,
        color: str = "ffffff",
        bg_color: str | None = None,
        rainbow_mode: int = 0,
        animation: int = 0,
        save_slot: int = 0,
        speed: int = 80,
        font: str = "CUSONG",
    ) -> None:
        """Send text to the matrix."""
        await self.async_call(
            lambda client: client.send_text(
                text=text,
                rainbow_mode=rainbow_mode,
                animation=animation,
                save_slot=save_slot,
                speed=speed,
                color=color,
                bg_color=bg_color,
                font=font,
            )
        )
        self.is_on = True

    async def async_set_clock(
        self,
        *,
        style: int = 1,
        show_date: bool = True,
        format_24: bool = True,
    ) -> None:
        """Show clock mode."""
        await self.async_call(
            lambda client: client.set_clock_mode(
                style=style,
                show_date=show_date,
                format_24=format_24,
            )
        )
        self.is_on = True

    async def async_show_slot(self, number: int) -> None:
        """Show saved slot."""
        await self.async_call(lambda client: client.show_slot(number))
        self.is_on = True

    async def async_set_orientation(self, orientation: int) -> None:
        """Set orientation."""
        await self.async_call(lambda client: client.set_orientation(orientation))

    async def async_clear(self) -> None:
        """Clear EEPROM/screens."""
        await self.async_call(lambda client: client.clear())

    @callback
    def async_device_info(self) -> dict[str, Any]:
        """Return HA device info."""
        return {
            "identifiers": {("ipixel_color", self.address)},
            "name": self.entry.title,
            "manufacturer": "iPixel Color",
            "model": "LED Matrix",
            "connections": {("bluetooth", self.address)},
        }