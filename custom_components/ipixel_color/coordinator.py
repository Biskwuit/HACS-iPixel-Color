"""Coordinator / device wrapper for iPixel Color LED Matrix.

Wraps pypixelcolor.AsyncClient and implements:
  - Exponential-backoff automatic reconnection
  - Transparent reconnection-on-command-failure for entity callers
  - Connection state tracking via an async coordinator DataUpdateCoordinator
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Callable, Coroutine, Optional

from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import (
    RECONNECT_BACKOFF_FACTOR,
    RECONNECT_BASE_DELAY,
    RECONNECT_MAX_DELAY,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


def _extract_bleak_exceptions() -> tuple[type[Exception], ...]:
    """Return a tuple of Bleak exception types, falling back to Exception.

    In bleak >= 2.0, BleakDBusError lives in bleak.exc, not at the top level.
    BleakBlueZDBusError was removed in bleak 3.x (merged into BleakDBusError).
    """
    try:
        import bleak
        from bleak.exc import BleakDBusError, BleakError
        return (BleakError, BleakDBusError, Exception)
    except ImportError:
        return (Exception,)


BLEAK_EXCEPTIONS = _extract_bleak_exceptions()


class IPixelDevice:
    """Wraps pypixelcolor.AsyncClient with automatic reconnection.

    Callers (entities, services) call methods on this object directly.
    If the underlying BLE session is disconnected, all public async methods
    will:
      1. Mark the coordinator as unavailable so HA reflects the state.
      2. Attempt reconnection with exponential backoff.
      3. Retry the original command once reconnected.
      4. Propagate the exception only if reconnect also fails.

    The disconnect detection is handled via the coordinator's
    _on_device_disconnected callback, which is called whenever the
    DataUpdateCoordinator refresh detects a disconnect.
    """

    def __init__(
        self,
        hass: HomeAssistant,
        address: str,
        entry_id: str,
        name: str | None = None,
    ) -> None:
        self._hass = hass
        self._address = address
        self._entry_id = entry_id
        self._name = name or address
        self._client: Any = None  # pypixelcolor.AsyncClient; type declared as Any to avoid hard dep at import time
        self._connected = False
        self._connect_lock = asyncio.Lock()
        self._reconnect_task: asyncio.Task[None] | None = None
        self._should_reconnect = True
        self._reconnect_delay = RECONNECT_BASE_DELAY

        # Coordinator that will manage entity state and drive refresh cycles
        self._coordinator = DataUpdateCoordinator[dict[str, Any]](
            hass,
            _LOGGER,
            name=DOMAIN,
            update_method=self._async_update,
            update_interval=None,  # No polling; updates are command-driven
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @property
    def coordinator(self) -> DataUpdateCoordinator[dict[str, Any]]:
        return self._coordinator

    @property
    def address(self) -> str:
        return self._address

    @property
    def display_name(self) -> str:
        return self._name

    @property
    def is_connected(self) -> bool:
        return self._connected

    @callback
    def _set_connected(self, connected: bool) -> None:
        """Thread-safe update of connection state."""
        was_connected = self._connected
        self._connected = connected
        if not connected and was_connected:
            _LOGGER.warning("[%s] BLE device disconnected", self._address)
            # Mark data as stale so entities show Unavailable
            self._coordinator.async_set_updated_data({"available": False})
            # Kick off background reconnect loop
            self._schedule_reconnect()
        elif connected and not was_connected:
            _LOGGER.info("[%s] BLE device reconnected", self._address)
            self._reconnect_delay = RECONNECT_BASE_DELAY  # reset backoff

    async def _async_update(self) -> dict[str, Any]:
        """Called by the coordinator when an entity requests a refresh."""
        if not self._connected:
            raise RuntimeError("Device not connected")
        try:
            # Retrieve cached device info (synchronous, fast)
            info = self._client.get_device_info()
            return {"available": True, "device_info": info}
        except Exception as ex:
            _LOGGER.debug("[%s] Refresh failed: %s", self._address, ex)
            raise

    # ------------------------------------------------------------------
    # Connection lifecycle
    # ------------------------------------------------------------------

    async def connect(self) -> None:
        """Connect to the BLE device (blocking, no retry). Used at startup."""
        async with self._connect_lock:
            if self._connected:
                return
            import pypixelcolor

            self._client = pypixelcolor.AsyncClient(self._address)
            try:
                await self._client.connect()
                self._set_connected(True)
                _LOGGER.info("[%s] Connected successfully", self._address)
            except Exception as ex:
                _LOGGER.error("[%s] Initial connect failed: %s", self._address, ex)
                self._client = None
                raise

    async def disconnect(self) -> None:
        """Gracefully disconnect and cancel background reconnect loop."""
        self._should_reconnect = False
        if self._reconnect_task:
            self._reconnect_task.cancel()
            self._reconnect_task = None
        async with self._connect_lock:
            if self._client is not None:
                try:
                    await self._client.disconnect()
                except Exception as ex:
                    _LOGGER.debug("[%s] Disconnect error: %s", self._address, ex)
                self._client = None
            self._set_connected(False)

    # ------------------------------------------------------------------
    # Background reconnect loop
    # ------------------------------------------------------------------

    def _schedule_reconnect(self) -> None:
        """Schedule the background reconnect task if not already running."""
        if self._reconnect_task is None or self._reconnect_task.done():
            self._should_reconnect = True
            self._reconnect_task = asyncio.create_task(self._reconnect_loop())

    async def _reconnect_loop(self) -> None:
        """Exponential-backoff reconnect loop, runs until successful or unloaded."""
        import pypixelcolor

        delay = self._reconnect_delay
        attempt = 0
        while self._should_reconnect:
            attempt += 1
            _LOGGER.info(
                "[%s] Reconnect attempt %d in %.0fs",
                self._address,
                attempt,
                delay,
            )
            await asyncio.sleep(delay)

            if not self._should_reconnect:
                break

            # Create a fresh client for each attempt
            new_client = pypixelcolor.AsyncClient(self._address)
            try:
                await new_client.connect()
                # Success – swap in the new client
                old_client = self._client
                self._client = new_client
                self._set_connected(True)
                _LOGGER.info(
                    "[%s] Reconnected on attempt %d",
                    self._address,
                    attempt,
                )
                return
            except Exception as ex:
                _LOGGER.warning(
                    "[%s] Reconnect attempt %d failed: %s",
                    self._address,
                    attempt,
                    ex,
                )
                delay = min(delay * RECONNECT_BACKOFF_FACTOR, RECONNECT_MAX_DELAY)

        _LOGGER.debug("[%s] Reconnect loop stopped (should_reconnect=False)", self._address)

    # ------------------------------------------------------------------
    # Wrapper for client commands with transparent reconnect-on-failure
    # ------------------------------------------------------------------

    async def _wrapped_command(
        self,
        coro: Coroutine,
        reconnect_callback: Callable[[], None],
    ) -> Any:
        """Execute an async command, reconnecting once if it fails.

        Args:
            coro:        A coroutine that calls a pypixelcolor method
                         (e.g., self._client.set_brightness(50)).
            reconnect_callback: Called synchronously before the reconnect
                         task is scheduled (to mark the device unavailable
                         immediately so HA reflects the correct state).
        """
        try:
            return await coro
        except BLEAK_EXCEPTIONS as ex:
            _LOGGER.warning(
                "[%s] Command failed due to BLE error, will reconnect: %s",
                self._address,
                ex,
            )
        except RuntimeError as ex:
            # pypixelcolor raises RuntimeError when not connected
            if "not connected" in str(ex).lower():
                _LOGGER.warning("[%s] Not connected: %s", self._address, ex)
            else:
                raise
        except Exception as ex:
            # BleakDBusError and BleakBlueZDBusError inherit from Exception
            _LOGGER.warning("[%s] Unexpected error: %s", self._address, ex)

        # Mark unavailable and schedule reconnect
        reconnect_callback()
        # Retry once reconnected
        await self._wait_until_connected(timeout=30.0)
        _LOGGER.info("[%s] Retrying command after reconnect", self._address)
        return await coro

    async def _wait_until_connected(self, timeout: float) -> None:
        """Block until _connected becomes True or timeout fires."""
        step = 0.5
        elapsed = 0.0
        while not self._connected and elapsed < timeout:
            await asyncio.sleep(step)
            elapsed += step
        if not self._connected:
            raise TimeoutError(f"Timeout waiting for reconnect within {timeout}s")

    # ------------------------------------------------------------------
    # Public device command API (used by entities and services)
    # ------------------------------------------------------------------

    async def set_power(self, on: bool) -> None:
        """Turn the device on or off."""

        async def _cmd() -> None:
            await self._client.set_power(on)

        await self._wrapped_command(_cmd(), lambda: self._set_connected(False))

    async def set_brightness(self, level: int) -> None:
        """Set brightness level (0-100)."""

        async def _cmd() -> None:
            await self._client.set_brightness(level)

        await self._wrapped_command(_cmd(), lambda: self._set_connected(False))

    async def set_orientation(self, orientation: int) -> None:
        """Set display orientation (0-3)."""

        async def _cmd() -> None:
            await self._client.set_orientation(orientation)

        await self._wrapped_command(_cmd(), lambda: self._set_connected(False))

    async def send_text(
        self,
        text: str,
        color: str = "ffffff",
        bg_color: str | None = None,
        animation: int = 0,
        speed: int = 80,
        rainbow_mode: int = 0,
        font: str = "CUSONG",
    ) -> None:
        """Send a text message to the device."""

        async def _cmd() -> None:
            await self._client.send_text(
                text,
                color=color,
                bg_color=bg_color,
                animation=animation,
                speed=speed,
                rainbow_mode=rainbow_mode,
                font=font,
            )

        await self._wrapped_command(_cmd(), lambda: self._set_connected(False))

    async def send_image(self, path: str) -> None:
        """Send an image file to the device."""

        async def _cmd() -> None:
            await self._client.send_image(path)

        await self._wrapped_command(_cmd(), lambda: self._set_connected(False))

    async def clear(self) -> None:
        """Clear the display."""

        async def _cmd() -> None:
            await self._client.clear()

        await self._wrapped_command(_cmd(), lambda: self._set_connected(False))
